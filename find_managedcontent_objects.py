from login import get_sf
import sys

ENVIRONMENT = sys.argv[1]

sf = get_sf(ENVIRONMENT)

objects = sf.describe()["sobjects"]

for obj in sorted(objects, key=lambda x: x["name"]):

    if "ManagedContent" in obj["name"]:
        print(obj["name"])