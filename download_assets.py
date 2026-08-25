import csv
import json
import os
import requests

import sys

from logger import get_logger
from login import get_sf

logger = get_logger(
    "cms_download"
)

logger.info(
    "DOWNLOAD JOB STARTED"
)



from datetime import datetime
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)



CSV_FILE = "cms_asset_inventory.csv"
MEDIA_ROOT = "_media"
STATUS_FILE = "status.json"
ENVIRONMENT = sys.argv[1] if len(sys.argv) > 1 else "uat"

sf = get_sf(
    ENVIRONMENT
)

headers = {
    "Authorization":
        f"Bearer {sf.session_id}"
}

# ==================================================
# STATUS
# ==================================================

def update_status(
    completed,
    failed,
    total,
    status="RUNNING"
):

    percent = 0

    if total > 0:

        percent = round(
            (completed / total) * 100,
            2
        )

    with open(
        STATUS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "job": "DOWNLOAD_ASSETS",
                "status": status,
                "completed": completed,
                "failed": failed,
                "total": total,
                "percent": percent
            },
            f,
            indent=2
        )

# ==================================================
# LOAD CSV
# ==================================================
print(
    f"Connecting to Salesforce [{ENVIRONMENT}]..."
)


with open(
    CSV_FILE,
    newline="",
    encoding="utf-8"
) as f:

    rows = list(
        csv.DictReader(f)
    )

# ==================================================
# DOWNLOAD FUNCTION
# ==================================================

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

    file_name = row.get(
        "UniqueFileName"
    )

    if not file_name:

        file_name = row["FileName"]

    file_path = os.path.join(
        path,
        file_name
    )

    if os.path.exists(file_path):

        logger.info(
            f"ALREADY_EXISTS - {row['FileName']}"
        )
        
        row["Status"] = (
            "ALREADY_EXISTS"
        )

        return row

    try:

        response = requests.get(
            row["DownloadUrl"],
            stream=True,
            headers=headers,
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

        row["Status"] = (
            "SUCCESS"
        )

        row["DownloadedDate"] = (
            datetime.now()
            .isoformat()
        )

        row["FileSize"] = str(
            os.path.getsize(
                file_path
            )
        )

        row["ContentType"] = (
            response.headers.get(
                "Content-Type",
                ""
            )
        )

        row["ErrorMessage"] = ""
        logger.info(
            f"SUCCESS - {row['FileName']}"
        )

    except Exception as ex:

        print(
            f"FAILED: {row['FileName']}"
        )

        print(
            f"ERROR: {str(ex)}"
        )

        logger.error(
            f"{row['FileName']} - {str(ex)}"
        )

        row["Status"] = "FAILED"

        retry_count = int(
            row.get(
                "RetryCount",
                0
            )
        )

        row["RetryCount"] = str(
            retry_count + 1
        )

        row["ErrorMessage"] = str(ex)

    return row

# ==================================================
# PENDING ROWS
# ==================================================

pending_rows = [

    row

    for row in rows

    if row["Status"] not in (
        "SUCCESS",
        "ALREADY_EXISTS"
    )
]

# TEST MODE
#pending_rows = [
 #   r
  #  for r in pending_rows
   # if not os.path.exists(
    #    os.path.join(
     #       MEDIA_ROOT,
      #      r["Folder"],
       #     r["FileName"]
        #)
    #)
#]

total = len(
    pending_rows
)

print(
    f"Pending downloads: {total}"
)

update_status(
    0,
    0,
    total,
    "STARTING"
)

# ==================================================
# DOWNLOADS
# ==================================================

updated_rows = []

completed = 0
failed = 0

with ThreadPoolExecutor(
    max_workers=20
) as executor:

    futures = [

        executor.submit(
            download_file,
            row
        )

        for row in pending_rows
    ]

    for future in as_completed(
        futures
    ):

        row = future.result()

        updated_rows.append(
            row
        )

        completed += 1

        if row["Status"] == "FAILED":

            failed += 1

        update_status(
            completed,
            failed,
            total
        )

# ==================================================
# MERGE RESULTS
# ==================================================

updated_lookup = {

    row["ManagedContentId"]: row

    for row in updated_rows
}

final_rows = []

for row in rows:

    key = row[
        "ManagedContentId"
    ]

    if key in updated_lookup:

        final_rows.append(
            updated_lookup[key]
        )

    else:

        final_rows.append(
            row
        )


print(
    f"updated_rows = {len(updated_rows)}"
)

print(
    f"updated_lookup = {len(updated_lookup)}"
)

statuses = {}

for row in final_rows:

    status = row["Status"]

    statuses[status] = (
        statuses.get(status, 0) + 1
    )

print(
    "STATUS COUNTS:"
)

print(
    statuses
)



# ==================================================
# SAVE CSV
# ==================================================

print("REACHED CSV SAVE")

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

print("CSV SAVED")

# ==================================================
# FINAL STATUS COUNTS
# ==================================================

success_count = len([
    r for r in final_rows
    if r["Status"] == "SUCCESS"
])

failed_count = len([
    r for r in final_rows
    if r["Status"] == "FAILED"
])

already_exists_count = len([
    r for r in final_rows
    if r["Status"] == "ALREADY_EXISTS"
])

pending_count = len([
    r for r in final_rows
    if r["Status"] == "PENDING"
])

# ==================================================
# FINAL STATUS FILE
# ==================================================

update_status(
    success_count + failed_count + already_exists_count,
    failed_count,
    len(final_rows),
    "COMPLETE"
)

# ==================================================
# SUMMARY
# ==================================================

print()
print("===================================")
print("DOWNLOAD COMPLETE")
print("===================================")
print(f"SUCCESS        : {success_count}")
print(f"FAILED         : {failed_count}")
print(f"ALREADY EXISTS : {already_exists_count}")
print(f"PENDING        : {pending_count}")
print("===================================")

logger.info(
    f"DOWNLOAD COMPLETE - "
    f"SUCCESS={success_count} "
    f"FAILED={failed_count} "
    f"ALREADY_EXISTS={already_exists_count} "
    f"PENDING={pending_count}"
)