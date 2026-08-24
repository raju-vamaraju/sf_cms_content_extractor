import os
import re
import json
import requests
from simple_salesforce import Salesforce
from urllib.parse import urljoin

# ==================================================
# CONFIGURATION
# ==================================================

SOURCE_USERNAME = "raju.vamaraju@insigniafinancial.com.au"
SOURCE_PASSWORD = "Doitraju001"
SOURCE_SECURITY_TOKEN = "BduNkV5ZK7apF19bzmQLerDi"

# Sandbox
SOURCE_DOMAIN = "test"

# Your Network ID
NETWORK_ID = "0DB6F000000PIPZWA4"

# API version
API_VERSION = "61.0"

OUTPUT_DIR = "salesforce_cms_export"
MEDIA_DIR = os.path.join(OUTPUT_DIR, "_media")

os.makedirs(MEDIA_DIR, exist_ok=True)

# ==================================================
# LOGIN
# ==================================================

print("Connecting to Salesforce...")

sf = Salesforce(
    username=SOURCE_USERNAME,
    password=SOURCE_PASSWORD,
    security_token=SOURCE_SECURITY_TOKEN,
    domain=SOURCE_DOMAIN,
)

headers = {
    "Authorization": f"Bearer {sf.session_id}",
    "Content-Type": "application/json"
}

instance_url = f"https://{sf.sf_instance}"

print("Connected successfully")

# ==================================================
# FETCH CMS CONTENT
# ==================================================

cms_items = []

page = 0
page_size = 100

while True:

    endpoint = (
        f"{instance_url}/services/data/v{API_VERSION}"
        f"/connect/communities/{NETWORK_ID}/managed-content/delivery"
    )

    params = {
        "page": page,
        "pageSize": page_size,
        "language": "en_US"
    }

    print(f"Loading page {page}...")

    response = requests.get(
        endpoint,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    with open("raw_response.json", "w") as f:
        json.dump(data, f, indent=2)

    print("Saved raw_response.json")

    items = data.get("items", [])

    if not items:
        break

    cms_items.extend(items)

    if len(items) < page_size:
        break

    page += 1

print(f"\nFound {len(cms_items)} CMS item(s)")

# ==================================================
# PROCESS CONTENT
# ==================================================

export_items = []

for item in cms_items:

    title = item.get("title", "Untitled")

    print(f"\nProcessing: {title}")

    content_id = item.get("managedContentId")

    slug = item.get(
        "contentUrlName",
        re.sub(r"[^a-zA-Z0-9]+", "-", title.lower())
    )

    nodes = item.get("contentNodes", {})

    record = {
        "id": content_id,
        "type": item.get("type"),
        "title": title,
        "slug": slug,
        "body": "",
        "excerpt": ""
    }

    # ==========================================
    # Extract text fields
    # ==========================================

    for node_name, node in nodes.items():

        if not isinstance(node, dict):
            continue

        value = node.get("value")

        if not value:
            continue

        if node_name.lower() == "body":
            record["body"] = value

        elif node_name.lower() == "excerpt":
            record["excerpt"] = value

        else:
            if isinstance(value, str):
                record[node_name] = value

    # ==========================================
    # Download images
    # ==========================================

    for node_name, node in nodes.items():

        if not isinstance(node, dict):
            continue

        image_url = (
            node.get("resourceUrl")
            or node.get("url")
        )

        if not image_url:
            continue

        if not any(
            ext in str(image_url).lower()
            for ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".webp"
            ]
        ):
            continue

        try:

            file_name = (
                node.get("fileName")
                or f"{content_id}_{node_name}.jpg"
            )

            safe_name = (
                f"{content_id}_{file_name}"
            )

            file_path = os.path.join(
                MEDIA_DIR,
                safe_name
            )

            full_url = (
                image_url
                if image_url.startswith("http")
                else urljoin(instance_url, image_url)
            )

            img_response = requests.get(
                full_url,
                headers=headers,
                stream=True,
                timeout=60
            )

            if img_response.status_code == 200:

                with open(file_path, "wb") as f:
                    for chunk in img_response.iter_content(8192):
                        f.write(chunk)

                record[node_name] = (
                    f"_media/{safe_name}"
                )

                print(
                    f"  Downloaded: {safe_name}"
                )

        except Exception as ex:
            print(
                f"  Failed image download: {ex}"
            )

    export_items.append(record)

# ==================================================
# WRITE EXPORT FILE
# ==================================================

output_json = os.path.join(
    OUTPUT_DIR,
    "content.json"
)

with open(
    output_json,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "count": len(export_items),
            "items": export_items
        },
        f,
        indent=4,
        ensure_ascii=False
    )

print("\n===================================")
print("Export Complete")
print("===================================")
print(f"Content Items : {len(export_items)}")
print(f"JSON File     : {output_json}")
print(f"Media Folder  : {MEDIA_DIR}")