# Salesforce CMS Migration Tool

## Overview

This project exports Salesforce CMS content and media assets from an Experience Cloud site.

Features:

- Build a CMS asset inventory
- Download CMS media assets
- Preserve CMS folder/workspace structure
- Track download status
- Retry failed downloads
- Generate missing content reports
- Streamlit dashboard for monitoring and execution
- Multi-threaded asset downloads
- Resume capability for interrupted downloads

---

# Project Structure

```text
adviserhub_cms/
│
├── config.json
├── login.py
│
├── build_inventory.py
├── build_missing_inventory.py
├── download_assets.py
├── retry_failed.py
├── report.py
│
├── streamlit_app.py
│
├── cms_asset_inventory.csv
├── cms_missing_inventory.csv
│
├── salesforce_cms_export/
│   ├── content.json
│   ├── cms_export.log
│   └── _media/
│
└── venv/
```

---

# Prerequisites

## Python

Recommended:

```bash
python3 --version
```

```text
Python 3.10+
```

## Create Virtual Environment

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate - mac/linux
.\venv\Scripts\Activate.ps1 - windows

```

Upgrade pip:

```bash
python -m pip install --upgrade pip setuptools wheel
```

## Install Dependencies

```bash
pip install simple-salesforce requests pandas streamlit
```

---

# Configuration

Create a file named:

```text
config.json
```

Example:

```json
{
	"uat": {
		"username": "user@company.com",
		"password": "password",
		"security_token": "token"
	},
	"prd": {
		"username": "user@company.com",
		"password": "password",
		"security_token": "token"
	}
}
```

---

# Environment Mapping

The login utility automatically selects the correct Salesforce endpoint:

| Environment | Endpoint |
|-------------|----------|
| prd | login.salesforce.com |
| uat | test.salesforce.com |
| dev | test.salesforce.com |
| sit | test.salesforce.com |

Usage:

```python
from login import get_sf

sf = get_sf("uat")
```

---

# Step 1 - Build Asset Inventory

Generates a CSV containing all downloadable CMS assets.

Run:

```bash
python build_inventory.py uat
```

Output:

```text
cms_asset_inventory.csv
```

Example:

```csv
ManagedContentId,
ContentKey,
Folder,
Title,
Type,
FileName,
DownloadUrl,
Status
```

Fields:

```text
ManagedContentId
ContentKey
Folder
Title
Type
FileName
DownloadUrl
Status
RetryCount
FileSize
ContentType
ErrorMessage
DownloadedDate
```

---

# Step 2 - Identify Missing Content

Creates a report of records that exist in Salesforce CMS but are not exposed through the CMS Delivery API.

Run:

```bash
python build_missing_inventory.py uat
```

Output:

```text
cms_missing_inventory.csv
```

Example:

```csv
ManagedContentId,
ContentKey,
Title,
Folder,
ManagedContentVariantStatus,
IsPublished,
VisibilityStatus
```

Typical statuses:

```text
Draft
Archived
Published
```

Visibility values:

```text
VISIBLE_IN_CHANNEL
NOT_VISIBLE_IN_CHANNEL
```

---

# Step 3 - Download Assets

Downloads assets listed in the asset inventory.

Run:

```bash
python download_assets.py
```

The downloader:

- Uses multiple threads
- Skips existing files
- Updates inventory status
- Supports retries
- Preserves CMS folder structure

Example output structure:

```text
_media/
├── Systems-Logos/
│   ├── Mercer Logo.png
│   ├── FASEA Logo.png
│
├── Practice Support/
│   ├── WealthSolver Guide.pdf
│
├── Professional Standards/
│   ├── Platform Support Pack.xlsx
│
└── AdviserONE for Shadforth/
```

---

# Download Status Values

The inventory tracks:

```text
PENDING
SUCCESS
FAILED
ALREADY_EXISTS
```

Example:

```csv
Status
-------
SUCCESS
FAILED
PENDING
ALREADY_EXISTS
```

---

# Step 4 - Retry Failed Downloads

Retries only failed records.

Run:

```bash
python retry_failed.py
```

Uses:

```text
Status = FAILED
```

records only.

---

# Step 5 - Generate Reports

Produce migration statistics.

Run:

```bash
python report.py
```

Example:

```text
Assets          : 6214
Downloaded      : 6200
Failed          : 14
Pending         : 0
Already Exists  : 0
```

---

# Streamlit Dashboard

Launch the UI:

```bash
streamlit run streamlit_app.py
```

Open:

```text
http://localhost:8501
```

Features:

- Environment selector
- Build Inventory
- Download Assets
- Retry Failed
- View Asset Inventory
- View Missing Content
- View Download Logs
- Browse Downloaded Files
- Progress Dashboard

---

# CSV Definitions

## Asset Inventory

File:

```text
cms_asset_inventory.csv
```

Columns:

```text
ManagedContentId
ContentKey
Folder
Title
Type
FileName
DownloadUrl
Status
RetryCount
FileSize
ContentType
ErrorMessage
DownloadedDate
```

---

## Missing Content Inventory

File:

```text
cms_missing_inventory.csv
```

Columns:

```text
ManagedContentId
ContentKey
Title
Folder
ManagedContentVariantStatus
IsPublished
VisibilityStatus
CreatedDate
LastModifiedDate
```

---

# Logging

The downloader maintains:

```text
salesforce_cms_export/cms_export.log
```

Example:

```text
2026-08-23 14:16:05 INFO SUCCESS - Xtools+ Revisited Release Notes.pdf
2026-08-23 14:16:08 INFO SUCCESS - WealthSolver User Guide.pdf
2026-08-23 14:16:10 ERROR FAILED - SomeFile.pdf
```

---

# Multi-threaded Downloads

Downloads use:

```python
ThreadPoolExecutor(
		max_workers=20
)
```

Benefits:

- Faster export
- Better utilization of network bandwidth
- Reduced overall migration time

---

# Common Commands

Build Inventory:

```bash
python build_inventory.py uat
```

Build Missing Content Report:

```bash
python build_missing_inventory.py uat
```

Download Assets:

```bash
python download_assets.py
```

Retry Failures:

```bash
python retry_failed.py
```

Generate Report:

```bash
python report.py
```

Launch Dashboard:

```bash
streamlit run streamlit_app.py
```

---

# Current Migration Flow

```text
1. Build Asset Inventory
						│
						▼
2. Build Missing Content Report
						│
						▼
3. Business Review Missing Content
						│
						▼
4. Download Assets
						│
						▼
5. Retry Failures
						│
						▼
6. Generate Migration Reports
```

---

# Notes

- CMS Delivery API returns only content available to the configured Experience Cloud channel.
- Archived or unpublished content may appear in the Missing Content report.
- Existing files are skipped automatically.
- Asset downloads are resumable.
- Folder structure is derived from:

```text
AuthoredManagedContentSpace.Name
```

- Missing content records can be reviewed with business users to determine whether they should be:
	- Migrated
	- Archived
	- Ignored
	- Rebuilt manually

---

# Future Enhancements

- Pause / Resume downloads
- Live progress refresh
- Automatic retry policy
- Download checkpoints
- Salesforce record hyperlinks
- File checksum validation
- SharePoint migration output
- HTML export for CMS pages and articles
- Folder size analytics
- Migration summary dashboard
- Parallel inventory generation

---

# Author

Salesforce CMS Migration Utility for Experience Cloud content extraction, inventory management, migration analysis, and asset export.
