import os
import csv
import json
import logging
import requests

from datetime import datetime
from simple_salesforce import Salesforce

# =====================================================
# CONFIGURATION
# =====================================================



USERNAME = "raju.vamaraju@insigniafinancial.com.au"
PASSWORD = "Doitraju001"
SECURITY_TOKEN = "BduNkV5ZK7apF19bzmQLerDi"

DOMAIN = "test"  # test=sandbox, login=production

NETWORK_ID = "0DB6F000000PIPZWA4"
API_VERSION = "67.0"

OUTPUT_DIR = "salesforce_cms_export"
MEDIA_DIR = os.path.join(OUTPUT_DIR, "_media")

os.makedirs(MEDIA_DIR, exist_ok=True)

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    filename=os.path.join(OUTPUT_DIR, "cms_export.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# =====================================================
# LOGIN
# =====================================================

print("Connecting to Salesforce...")

sf = Salesforce(
    username=USERNAME,
    password=PASSWORD,
    security_token=SECURITY_TOKEN,
    domain=DOMAIN
)

instance_url = f"https://{sf.sf_instance}"

headers = {
    "Authorization": f"Bearer {sf.session_id}"
}

print(f"Connected to {sf.sf_instance}")

# =====================================================
# BUILD FOLDER LOOKUP
# =====================================================

print("Loading CMS folder mappings...")

folder_lookup = {}

query = """
SELECT Id,
       Name,
       AuthoredManagedContentSpace.Name
FROM ManagedContent
"""

result = sf.query_all(query)

for rec in result["records"]:

    folder_name = "Unknown"

    authored_space = rec.get("AuthoredManagedContentSpace")

    if authored_space:
        folder_name = authored_space.get(
            "Name",
            "Unknown"
        )

    folder_lookup[rec["Id"]] = folder_name

print(
    f"Loaded {len(folder_lookup)} CMS folder mappings"
)

# =====================================================
# INVENTORY CSV
# =====================================================

csv_path = os.path.join(
    OUTPUT_DIR,
    "inventory.csv"
)

inventory_file = open(
    csv_path,
    "w",
    newline="",
    encoding="utf-8"
)

inventory_writer = csv.DictWriter(
    inventory_file,
    fieldnames=[
        "ManagedContentId",
        "ContentKey",
        "Folder",
        "Title",
        "Type",
        "FileName",
        "DownloadUrl",
        "LocalPath",
        "Status",
        "ErrorMessage",
        "DownloadedDate"
    ]
)

inventory_writer.writeheader()

# =====================================================
# FETCH ALL CMS CONTENT
# =====================================================

all_items = []

page = 0
page_size = 100

print("Loading CMS content...")

while True:

    url = (
        f"{instance_url}"
        f"/services/data/v{API_VERSION}"
        f"/connect/communities/{NETWORK_ID}"
        f"/managed-content/delivery"
    )

    params = {
        "page": page,
        "pageSize": page_size,
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

    all_items.extend(items)

    print(
        f"Loaded page {page} "
        f"({len(items)} records)"
    )

    if len(items) < page_size:
        break

    page += 1

print(f"Total CMS items: {len(all_items)}")

# =====================================================
# SAVE RAW CONTENT
# =====================================================

json_path = os.path.join(
    OUTPUT_DIR,
    "content.json"
)

with open(
    json_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "count": len(all_items),
            "items": all_items
        },
        f,
        indent=2
    )

# =====================================================
# DOWNLOAD MEDIA
# =====================================================

success_count = 0
failed_count = 0
exists_count = 0

for item in all_items:

    managed_content_id = item.get(
        "managedContentId"
    )

    content_key = item.get(
        "contentKey"
    )

    title = item.get(
        "title",
        ""
    )

    content_type = item.get(
        "type",
        ""
    )

    nodes = item.get(
        "contentNodes",
        {}
    )

    source = nodes.get("source")

    if not source:
        continue

    resource_url = source.get(
        "resourceUrl"
    )

    static_url = source.get(
        "url"
    )

    file_name = source.get(
        "fileName"
    )

    if not file_name and static_url:
        file_name = static_url.split("/")[-1]

    if not file_name:
        file_name = f"{managed_content_id}.bin"

    download_url = None

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

    if not download_url:
        continue

    folder_name = folder_lookup.get(
        managed_content_id,
        "Unknown"
    )

    safe_folder = (
        folder_name
        .replace("/", "-")
        .replace("\\", "-")
    )

    folder_path = os.path.join(
        MEDIA_DIR,
        safe_folder
    )

    os.makedirs(
        folder_path,
        exist_ok=True
    )

    local_path = os.path.join(
        folder_path,
        file_name
    )

    # ==========================================
    # ALREADY EXISTS
    # ==========================================

    if os.path.exists(local_path):

        exists_count += 1

        inventory_writer.writerow({
            "ManagedContentId": managed_content_id,
            "ContentKey": content_key,
            "Folder": folder_name,
            "Title": title,
            "Type": content_type,
            "FileName": file_name,
            "DownloadUrl": download_url,
            "LocalPath": local_path,
            "Status": "ALREADY_EXISTS",
            "ErrorMessage": "",
            "DownloadedDate": ""
        })

        continue

    # ==========================================
    # DOWNLOAD
    # ==========================================

    try:

        print(
            f"Downloading: "
            f"{folder_name}/{file_name}"
        )

        response = requests.get(
            download_url,
            headers=headers,
            stream=True,
            timeout=120
        )

        response.raise_for_status()

        with open(
            local_path,
            "wb"
        ) as f:

            for chunk in response.iter_content(
                chunk_size=8192
            ):
                if chunk:
                    f.write(chunk)

        success_count += 1

        inventory_writer.writerow({
            "ManagedContentId": managed_content_id,
            "ContentKey": content_key,
            "Folder": folder_name,
            "Title": title,
            "Type": content_type,
            "FileName": file_name,
            "DownloadUrl": download_url,
            "LocalPath": local_path,
            "Status": "SUCCESS",
            "ErrorMessage": "",
            "DownloadedDate":
                datetime.now().isoformat()
        })

        logging.info(
            f"SUCCESS - {file_name}"
        )

    except Exception as ex:

        failed_count += 1

        error_message = str(ex)

        inventory_writer.writerow({
            "ManagedContentId": managed_content_id,
            "ContentKey": content_key,
            "Folder": folder_name,
            "Title": title,
            "Type": content_type,
            "FileName": file_name,
            "DownloadUrl": download_url,
            "LocalPath": local_path,
            "Status": "FAILED",
            "ErrorMessage": error_message,
            "DownloadedDate": ""
        })

        logging.error(
            f"FAILED - {file_name} - {error_message}"
        )

inventory_file.close()

# =====================================================
# SUMMARY
# =====================================================

print()
print("====================================")
print("EXPORT COMPLETE")
print("====================================")
print(f"Success        : {success_count}")
print(f"Failed         : {failed_count}")
print(f"Already Exists : {exists_count}")
print(f"Inventory CSV  : {csv_path}")
print(f"Media Folder   : {MEDIA_DIR}")
print(f"Log File       : {OUTPUT_DIR}/cms_export.log")
print("====================================")