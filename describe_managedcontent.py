import sys
from login import get_sf

ENVIRONMENT = sys.argv[1]

sf = get_sf(ENVIRONMENT)

describe = sf.ManagedContent.describe()

for field in describe["fields"]:
    print(field["name"])