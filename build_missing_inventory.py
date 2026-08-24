import csv
import sys

from login import get_sf

ENVIRONMENT = sys.argv[1]

INPUT_CSV = "cms_asset_inventory.csv"
OUTPUT_CSV = "cms_missing_inventory.csv"

# ==========================================
# LOGIN
# ==========================================

sf = get_sf(ENVIRONMENT)

print("Connected")

# ==========================================
# LOAD ASSET IDS
# ==========================================

asset_ids = set()

with open(
    INPUT_CSV,
    newline="",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:
        asset_ids.add(
            row["ManagedContentId"]
        )

print(
    f"Asset inventory contains {len(asset_ids)} records"
)

# ==========================================
# QUERY ALL MANAGEDCONTENT
# ==========================================

query = """
SELECT Id,
       Name,
       ContentKey,
       CreatedDate,
       LastModifiedDate,
       AuthoredManagedContentSpace.Name
FROM ManagedContent
"""

results = sf.query_all(query)

all_records = results["records"]

print(
    f"ManagedContent contains {len(all_records)} records"
)

# ==========================================
# FIND MISSING RECORDS
# ==========================================

missing_records = []

for rec in all_records:

    managed_content_id = rec["Id"]

    if managed_content_id in asset_ids:
        continue

    folder_name = "Unknown"

    authored_space = rec.get(
        "AuthoredManagedContentSpace"
    )

    if authored_space:
        folder_name = authored_space.get(
            "Name",
            "Unknown"
        )

    # --------------------------------------
    # GET VARIANT STATUS
    # --------------------------------------

    variant_status = ""
    is_published = ""

    try:

        variant_query = f"""
        SELECT ManagedContentVariantStatus,
               IsPublished
        FROM ManagedContentVariant
        WHERE ManagedContentId = '{managed_content_id}'
        """

        variant_results = sf.query(
            variant_query
        )

        if variant_results["totalSize"] > 0:

            variant = (
                variant_results["records"][0]
            )

            variant_status = variant.get(
                "ManagedContentVariantStatus",
                ""
            )

            is_published = variant.get(
                "IsPublished",
                ""
            )

    except Exception as ex:

        variant_status = (
            f"ERROR: {str(ex)}"
        )

    missing_records.append({

        "ManagedContentId":
            managed_content_id,

        "ContentKey":
            rec.get(
                "ContentKey",
                ""
            ),

        "Title":
            rec.get(
                "Name",
                ""
            ),

        "Folder":
            folder_name,

        "ManagedContentVariantStatus":
            variant_status,

        "IsPublished":
            is_published,

        "VisibilityStatus":
            "NOT_VISIBLE_IN_CHANNEL",

        "CreatedDate":
            rec.get(
                "CreatedDate",
                ""
            ),

        "LastModifiedDate":
            rec.get(
                "LastModifiedDate",
                ""
            )
    })

print(
    f"Missing records found: "
    f"{len(missing_records)}"
)

# ==========================================
# WRITE CSV
# ==========================================

with open(
    OUTPUT_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "ManagedContentId",
            "ContentKey",
            "Title",
            "Folder",
            "ManagedContentVariantStatus",
            "IsPublished",
            "VisibilityStatus",
            "CreatedDate",
            "LastModifiedDate"
        ]
    )

    writer.writeheader()

    writer.writerows(
        missing_records
    )

print()
print(
    f"Created: {OUTPUT_CSV}"
)

print(
    f"Records: {len(missing_records)}"
)