"""
list_metadata action.

Connects to MongoDB, returns the last 50 extracted URLs ordered by the most
recent insertion time (descending). The `metadata` collection is populated by
the `extract_metadata` action.
"""

import json
from datetime import datetime

COLLECTION = "metadata"
LIMIT = 50


def get_collection(ctx):
    """Return the `metadata` MongoDB collection from the generated context."""
    if not ctx or not hasattr(ctx, "MONGODB"):
        return None
    return ctx.MONGODB[COLLECTION]


def serialize_doc(doc):
    """Convert a BSON document into a JSON-friendly dict."""
    if not doc:
        return None
    doc.pop("_id", None)
    if isinstance(doc.get("inserted_at"), datetime):
        doc["inserted_at"] = doc["inserted_at"].isoformat()
    if isinstance(doc.get("extracted_at"), datetime):
        doc["extracted_at"] = doc["extracted_at"].isoformat()
    return doc


def main(args, ctx=None):
    """Entry point invoked by the generated wrapper."""
    coll = get_collection(ctx)
    if coll is None:
        return {"ok": False, "error": "MongoDB non configurato"}

    try:
        cursor = coll.find({}).sort("inserted_at", -1).limit(LIMIT)
        docs = [serialize_doc(doc) for doc in cursor]
    except Exception as exc:
        return {"ok": False, "error": f"Errore lettura MongoDB: {exc}"}

    # Filter out any None values defensively.
    docs = [d for d in docs if d is not None]
    return {"ok": True, "data": docs}