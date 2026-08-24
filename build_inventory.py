import csv
import requests
import sys

from login import get_sf
from login import get_instance_url

# ===================================================
# PARAMETERS
# ===================================================

ENVIRONMENT = sys.argv[1]

NETWORK_ID = "0DB6F000000PIPZWA4"
API_VERSION = "67.0"

ASSET_CSV = "cms_asset_inventory.csv"
CONTENT_CSV = "cms_content_inventory.csv"

# ===================================================
# LOGIN
# ===================================================

sf = get_sf(ENVIRONMENT)

instance_url = get_instance_url(sf)

headers = {
    "Authorization": f"Bearer {sf.session_id}"
}

print(f"Connected to {sf.sf_instance}")

# ===================================================
# FOLDER LOOKUP
# ===================================================

folder_lookup = {}

query = """
SELECT Id,
       Name,
       AuthoredManagedContentSpace.Name
FROM ManagedContent
"""

results = sf.query_all(query)

for rec in results["records"]:

    folder_name = "Unknown"

    authored_space = rec.get(
        "AuthoredManagedContentSpace"
    )

    if authored_space:
        folder_name = authored_space.get(
            "Name",
            "Unknown"
        )

    folder_lookup[rec["Id"]] = folder_name

print(
    f"Loaded {len(folder_lookup)} ManagedContent records"
)

# ===================================================
# ASSET CSV
# ===================================================

asset_file = open(
    ASSET_CSV,
    "w",
    newline="",
    encoding="utf-8"
)

asset_writer = csv.DictWriter(
    asset_file,
    fieldnames=[
        "ManagedContentId",
        "ContentKey",
        "Folder",
        "Title",
        "Type",
        "FileName",
        "DownloadUrl",
        "Status",
        "RetryCount",
        "ErrorMessage",
        "DownloadedDate"
    ]
)

asset_writer.writeheader()

# ===================================================
# CONTENT CSV
# ===================================================

content_file = open(
    CONTENT_CSV,
    "w",
    newline="",
    encoding="utf-8"
)

content_writer = csv.DictWriter(
    content_file,
    fieldnames=[
        "ManagedContentId",
        "ContentKey",
        "Folder",
        "Title",
        "Type",
        "ContentUrlName",
        "PublishedDate",
        "Reason"
    ]
)

content_writer.writeheader()

# ===================================================
# PROCESS CMS CONTENT
# ===================================================

page = 0

asset_count = 0
content_count = 0

while True:

    url = (
        f"{instance_url}"
        f"/services/data/v{API_VERSION}"
        f"/connect/communities/{NETWORK_ID}"
        f"/managed-content/delivery"
    )

    params = {
        "page": page,
        "pageSize": 100,
        "language": "en_US"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    items = data.get("items", [])

    if not items:
        break

    print(
        f"Page {page}: {len(items)} records"
    )

    for item in items:

        managed_content_id = item.get(
            "managedContentId"
        )

        folder_name = folder_lookup.get(
            managed_content_id,
            "Unknown"
        )

        content_nodes = item.get(
            "contentNodes",
            {}
        )

        source = content_nodes.get(
            "source"
        )

        # ==========================================
        # DOWNLOADABLE ASSET
        # ==========================================

        if source:

            file_name = source.get(
                "fileName"
            )

            resource_url = source.get(
                "resourceUrl"
            )

            static_url = source.get(
                "url"
            )

            if (
                not file_name
                and static_url
            ):
                file_name = (
                    static_url.split("/")[-1]
                )

            download_url = ""

            if resource_url:

                download_url = (
                    f"{instance_url}"
                    f"{resource_url}"
                )

            elif static_url:

                download_url = (
                    f"{instance_url}"
                    f"{static_url}"
                )

            asset_writer.writerow({

                "ManagedContentId":
                    managed_content_id,

                "ContentKey":
                    item.get(
                        "contentKey"
                    ),

                "Folder":
                    folder_name,

                "Title":
                    item.get(
                        "title"
                    ),

                "Type":
                    item.get(
                        "type"
                    ),

                "FileName":
                    file_name,

                "DownloadUrl":
                    download_url,

                "Status":
                    "PENDING",

                "RetryCount":
                    0,

                "ErrorMessage":
                    "",

                "DownloadedDate":
                    ""
            })

            asset_count += 1

        # ==========================================
        # NON-DOWNLOADABLE CONTENT
        # ==========================================

        else:

            content_writer.writerow({

                "ManagedContentId":
                    managed_content_id,

                "ContentKey":
                    item.get(
                        "contentKey"
                    ),

                "Folder":
                    folder_name,

                "Title":
                    item.get(
                        "title"
                    ),

                "Type":
                    item.get(
                        "type"
                    ),

                "ContentUrlName":
                    item.get(
                        "contentUrlName"
                    ),

                "PublishedDate":
                    item.get(
                        "publishedDate"
                    ),

                "Reason":
                    "No source node"
            })

            content_count += 1

    page += 1

# ===================================================
# CLOSE FILES
# ===================================================

asset_file.close()
content_file.close()

# ===================================================
# SUMMARY
# ===================================================

print()
print("===================================")
print("Inventory Build Complete")
print("===================================")
print(
    f"Asset Records   : {asset_count}"
)
print(
    f"Content Records : {content_count}"
)
print(
    f"Total Records   : {asset_count + content_count}"
)
print()
print(
    f"Asset CSV   : {ASSET_CSV}"
)
print(
    f"Content CSV : {CONTENT_CSV}"
)
print("===================================")