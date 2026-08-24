from login import get_sf
import sys
import json

ENVIRONMENT = sys.argv[1]

sf = get_sf(ENVIRONMENT)

record_id = "20Y6F000000GuuZUAS"

mc = sf.ManagedContent.get(record_id)

print(json.dumps(mc, indent=2))