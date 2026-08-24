import csv
import os
import requests

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

CSV_FILE = "cms_asset_inventory.csv"
MEDIA_ROOT = "_media"

# ==========================================
# LOAD CSV
# ==========================================

with open(
    CSV_FILE,
    newline="",
    encoding="utf-8"
) as f:

    rows = list(
        csv.DictReader(f)
    )

# ==========================================
# DOWNLOAD FUNCTION
# ==========================================

def download_file(row):

    status = row["Status"]

    if status in (
        "SUCCESS",
        "ALREADY_EXISTS"
    ):
        return row

    folder = row["Folder"]

    path = os.path.join(
        MEDIA_ROOT,
        folder
    )

    os.makedirs(
        path,
        exist_ok=True
    )

    file_path = os.path.join(
        path,
        row["FileName"]
    )

    if os.path.exists(file_path):

        row["Status"] = (
            "ALREADY_EXISTS"
        )

        return row

    try:

        print(
            f"Downloading "
            f"{row['FileName']}"
        )

        response = requests.get(
            row["DownloadUrl"],
            stream=True,
            timeout=120
        )

        response.raise_for_status()

        with open(
            file_path,
            "wb"
        ) as f:

            for chunk in response.iter_content(
                8192
            ):
                if chunk:
                    f.write(chunk)

        row["Status"] = "SUCCESS"

        row["DownloadedDate"] = (
            datetime.now()
            .isoformat()
        )

        row["ErrorMessage"] = ""

    except Exception as ex:

        row["Status"] = "FAILED"

        row["RetryCount"] = str(
            int(
                row.get(
                    "RetryCount",
                    0
                )
            ) + 1
        )

        row["ErrorMessage"] = str(ex)

    return row

# ==========================================
# MULTI-THREAD DOWNLOAD
# ==========================================

pending_rows = [

    row

    for row in rows

    if row["Status"] not in (
        "SUCCESS",
        "ALREADY_EXISTS"
    )
]

print(
    f"Pending downloads: {len(pending_rows)}"
)

with ThreadPoolExecutor(
    max_workers=20
) as executor:

    updated_rows = list(
        executor.map(
            download_file,
            pending_rows
        )
    )

# ==========================================
# MERGE RESULTS
# ==========================================

updated_lookup = {

    row["ManagedContentId"]: row

    for row in updated_rows
}

final_rows = []

for row in rows:

    key = row["ManagedContentId"]

    if key in updated_lookup:

        final_rows.append(
            updated_lookup[key]
        )

    else:

        final_rows.append(row)

# ==========================================
# SAVE CSV ONCE
# ==========================================

with open(
    CSV_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=final_rows[0].keys()
    )

    writer.writeheader()

    writer.writerows(
        final_rows
    )

# ==========================================
# SUMMARY
# ==========================================

success = len([
    r for r in final_rows
    if r["Status"] == "SUCCESS"
])

failed = len([
    r for r in final_rows
    if r["Status"] == "FAILED"
])

exists = len([
    r for r in final_rows
    if r["Status"] == "ALREADY_EXISTS"
])

pending = len([
    r for r in final_rows
    if r["Status"] == "PENDING"
])

print()
print("=========================")
print("DOWNLOAD COMPLETE")
print("=========================")
print(f"SUCCESS        : {success}")
print(f"FAILED         : {failed}")
print(f"ALREADY EXISTS : {exists}")
print(f"PENDING        : {pending}")
print("=========================")