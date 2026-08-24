# describe_variant.py

from login import get_sf
import sys

ENVIRONMENT = sys.argv[1]

sf = get_sf(ENVIRONMENT)

describe = sf.ManagedContentVariant.describe()

for field in describe["fields"]:
    print(field["name"])