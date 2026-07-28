// API helpers for the URL Metadata Collector.
//
// Frontend code calls the public Nuvolaris/OpenServerless web actions through
// the relative "/api/my/<package>/<action>" proxy so the browser keeps its
// own origin. The generated wrapper nests the module return value under a
// `body` field, so we unwrap that before reading the application payload.

export interface MetadataItem {
  url: string;
  title: string;
  description?: string;
  favicon?: string;
  image?: string;
  site_name?: string;
  extracted_at?: string;
  inserted_at?: string;
  cached?: boolean;
}

interface ApiPayload {
  ok: boolean;
  data?: MetadataItem | MetadataItem[];
  error?: string;
  warning?: string;
}

// Unwrap the OpenServerless wrapper envelope and return the application JSON.
async function parsePayload(response: Response): Promise<ApiPayload> {
  const raw = await response.json();
  const data =
    raw && typeof raw === "object" && "body" in raw ? raw.body : raw;
  return (data ?? {}) as ApiPayload;
}

export async function extractMetadata(
  url: string
): Promise<MetadataItem & { warning?: string }> {
  const res = await fetch("/api/my/v1/extract-metadata", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  const payload = await parsePayload(res);

  if (!payload.ok || payload.error) {
    throw new Error(payload.error || `Errore: ${res.status}`);
  }

  const data = payload.data as MetadataItem;
  if (!data) {
    throw new Error("Nessun dato ricevuto dal server");
  }
  return { ...data, warning: payload.warning };
}

export async function listMetadata(): Promise<MetadataItem[]> {
  const res = await fetch("/api/my/v1/list-metadata", {
    method: "GET",
  });

  const payload = await parsePayload(res);

  if (!payload.ok || payload.error) {
    throw new Error(payload.error || `Errore: ${res.status}`);
  }

  const data = payload.data;
  return Array.isArray(data) ? data : [];
}