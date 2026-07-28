"""
extract_metadata action.

Receives a JSON body/query with an `url`, extracts the page metadata
(title, description, favicon, Open Graph image/title/description) using
`requests` + `BeautifulSoup`, caches the result in MongoDB (collection
`metadata`) and returns the extracted data to the frontend.

Flow:
  1. Validate the incoming URL.
  2. If a document for this URL already exists in MongoDB, return it (cache hit).
  3. Otherwise download the HTML (with a sane timeout and User-Agent).
  4. Parse the HTML and extract the relevant metadata.
  5. Persist the document in MongoDB with an `inserted_at` timestamp.
  6. Return the metadata dict.
"""

import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# Collection name used to persist the extracted metadata.
COLLECTION = "metadata"

# HTTP fetch parameters.
USER_AGENT = (
    "Mozilla/5.0 (compatible; URLMetadataCollector/1.0; +https://example.com/bot)"
)
HTTP_TIMEOUT = 12  # seconds, covers both connect and read
MAX_HTML_BYTES = 5 * 1024 * 1024  # 5 MB safety cap to avoid huge payloads


def request_data(args):
    """Merge body and top-level request fields into a single dict.

    OpenServerless web actions can deliver JSON fields either at the top level
    of `args` or nested under `args["body"]` (as a dict or JSON string).
    Top-level fields win over body fields.
    """
    data = dict(args) if isinstance(args, dict) else {}
    body = data.get("body")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            body = {}
    merged = dict(body) if isinstance(body, dict) else {}
    ignored = {"body", "__ow_method", "__ow_headers", "__ow_path", "__ow_body"}
    merged.update({k: v for k, v in data.items() if k not in ignored})
    return merged


def normalize_url(url):
    """Strip whitespace and return a canonical URL, or "" if invalid."""
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if not url:
        return ""
    # Add a scheme if the user pasted "example.com/path".
    if "://" not in url:
        url = "http://" + url
    parsed = urlparse(url)
    # A valid URL needs a netloc and an http(s) scheme.
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return url


def get_collection(ctx):
    """Return the `metadata` MongoDB collection from the generated context."""
    if not ctx or not hasattr(ctx, "MONGODB"):
        return None
    return ctx.MONGODB[COLLECTION]


def find_cached(coll, url):
    """Return a cached metadata document for the URL, or None."""
    try:
        doc = coll.find_one({"url": url})
    except Exception:
        return None
    if not doc:
        return None
    # Normalize the stored document into a JSON-friendly dict.
    doc.pop("_id", None)
    if isinstance(doc.get("inserted_at"), datetime):
        doc["inserted_at"] = doc["inserted_at"].isoformat()
    doc["cached"] = True
    return doc


def fetch_html(url):
    """Download the HTML at `url`. Raises requests exceptions on failure."""
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    resp = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    # Cap the size to avoid parsing enormous payloads.
    if len(resp.content) > MAX_HTML_BYTES:
        raise ValueError("Page too large to parse")
    # Warn (but allow) when the content type is not HTML-ish.
    if "html" not in content_type and "xml" not in content_type:
        raise ValueError("URL does not return an HTML page")
    return resp.text


def extract_meta(soup):
    """Extract Open Graph and standard meta tags from a parsed soup."""
    og = {}

    def og_prop(prop):
        tag = soup.find("meta", property=prop)
        return tag.get("content").strip() if tag and tag.get("content") else ""

    def meta_name(name):
        tag = soup.find("meta", attrs={"name": name})
        return tag.get("content").strip() if tag and tag.get("content") else ""

    og["title"] = og_prop("og:title")
    og["description"] = og_prop("og:description")
    og["image"] = og_prop("og:image")
    og["site_name"] = og_prop("og:site_name")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    description = og["description"] or meta_name("description") or meta_name("Description")

    return {
        "title": title,
        "description": description,
        "og": og,
    }


def extract_favicon(soup, base_url):
    """Find the best favicon URL, resolved against the page base URL."""
    icon_links = soup.find_all("link", rel=lambda r: r and "icon" in " ".join(r).lower())
    for link in icon_links:
        href = (link.get("href") or "").strip()
        if href:
            return urljoin(base_url, href)
    # Fallback to /favicon.ico at the site root.
    parsed = urlparse(base_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    return ""


def extract_metadata_from_html(html, url):
    """Parse HTML and return a clean metadata dict."""
    soup = BeautifulSoup(html, "html.parser")
    meta = extract_meta(soup)
    favicon = extract_favicon(soup, url)

    title = meta["og"]["title"] or meta["title"] or urlparse(url).netloc
    description = meta["og"]["description"] or meta["description"]
    image = meta["og"]["image"]
    site_name = meta["og"]["site_name"]

    # Resolve relative og:image URLs against the page URL.
    if image:
        image = urljoin(url, image)

    return {
        "url": url,
        "title": title,
        "description": description,
        "favicon": favicon,
        "image": image,
        "site_name": site_name,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }


def main(args, ctx=None):
    """Entry point invoked by the generated wrapper."""
    data = request_data(args)
    url = normalize_url(data.get("url"))

    if not url:
        return {"ok": False, "error": "URL non valido o mancante"}

    coll = get_collection(ctx)
    if coll is None:
        return {"ok": False, "error": "MongoDB non configurato"}

    # 1. Cache lookup by URL.
    cached = find_cached(coll, url)
    if cached:
        return {"ok": True, "data": cached}

    # 2. Fetch and parse the page.
    try:
        html = fetch_html(url)
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Timeout durante il download della pagina"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "Impossibile connettersi all'URL specificato"}
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": f"Errore HTTP: {exc}"}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        metadata = extract_metadata_from_html(html, url)
    except Exception as exc:
        return {"ok": False, "error": f"Errore di parsing: {exc}"}

    # 3. Persist in MongoDB with an insertion timestamp for ordering.
    document = dict(metadata)
    document["url"] = url
    document["inserted_at"] = datetime.now(timezone.utc)
    try:
        coll.insert_one(document)
    except Exception as exc:
        # Even if persistence fails, return what we extracted to the user.
        return {"ok": True, "data": metadata, "warning": f"Salvataggio fallito: {exc}"}

    # Strip the MongoDB-specific fields before returning.
    document.pop("_id", None)
    # Convert datetime to ISO string for JSON serialization.
    if isinstance(document.get("inserted_at"), datetime):
        document["inserted_at"] = document["inserted_at"].isoformat()
    return {"ok": True, "data": document}