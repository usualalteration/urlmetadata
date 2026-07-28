"""
setup/metadata-index action (private).

Idempotently creates the indexes used by the URL Metadata Collector on the
`metadata` MongoDB collection:

  - unique index on `url` (fast cache lookup, prevents duplicate documents)
  - descending index on `inserted_at` (fast "last 50" listing)

`create_index` is idempotent: re-running this setup action is safe and will
not duplicate or drop existing indexes.
"""

COLLECTION = "metadata"


def main(args, ctx=None):
    if not ctx or not hasattr(ctx, "MONGODB"):
        return {"ok": False, "error": "MongoDB non configurato"}

    coll = ctx.MONGODB[COLLECTION]
    created = []

    try:
        # Unique index on url so cache lookups are fast and duplicates are
        # prevented. If a document already exists for a url, re-extraction
        # will be served from the cache.
        coll.create_index("url", unique=True, name="idx_url_unique")
        created.append("idx_url_unique")

        # Descending index on inserted_at to support list_metadata ordering.
        coll.create_index([("inserted_at", -1)], name="idx_inserted_at_desc")
        created.append("idx_inserted_at_desc")
    except Exception as exc:
        return {"ok": False, "error": f"Errore creazione indici: {exc}"}

    try:
        existing = coll.index_information().keys()
    except Exception:
        existing = []

    return {
        "ok": True,
        "collection": COLLECTION,
        "created": created,
        "indexes": list(existing),
    }