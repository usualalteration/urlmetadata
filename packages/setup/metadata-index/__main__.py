#--kind python:default
#--web false
# Note: this timeout is 5 minutes - 10 minutes is max allowed
#--timeout 300000
import types, os, metadata_index

builder = []
## build-context ##
#--param MONGODB_URI "$MONGODB_URI"
from pymongo import MongoClient
def init_mongodb(args, ctx):
  uri = args.get("MONGODB_URI", os.getenv("MONGODB_URI"))
  if not uri:
    raise RuntimeError("MONGODB_URI is not configured for this action")
  ctx.MONGODB_CLIENT = MongoClient(uri)
  ctx.MONGODB = ctx.MONGODB_CLIENT.get_default_database()
builder.append(init_mongodb)

def main(args):
  try:
    ctx = types.SimpleNamespace()
    for fn in builder: fn(args, ctx)
    return { "body": metadata_index.main(args, ctx=ctx) }
  except Exception as e:
    import traceback
    traceback.print_exc()
    return {
      "body": {"error": str(e) },
      "statusCode": 500
    }
