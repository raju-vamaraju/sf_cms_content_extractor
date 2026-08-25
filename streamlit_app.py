import os
import sys
import json
import subprocess

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ==================================================
# AUTO REFRESH
# ==================================================

st_autorefresh(
    interval=2000,
    key="autorefresh"
)

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Salesforce CMS Migration",
    layout="wide"
)

st.title("Salesforce CMS Migration Dashboard")

# ==================================================
# CONFIG
# ==================================================

ASSET_CSV = "cms_asset_inventory.csv"
MISSING_CSV = "cms_missing_inventory.csv"
STATUS_FILE = "status.json"
LOG_FILE = "salesforce_cms_export/cms_export.log"
MEDIA_ROOT = "_media"

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.header("Environment")

env = st.sidebar.selectbox(
    "Environment",
    ["uat", "prd"]
)

st.sidebar.write("Python")

st.sidebar.code(
    sys.executable
)

# ==================================================
# ACTION BUTTONS
# ==================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    if st.button("Build Inventory"):

        subprocess.Popen(
            [sys.executable,
             "build_inventory.py",
             env]
        )

        st.success(
            "Inventory job started"
        )

with col2:

    if st.button(
        "Find Missing Content"
    ):

        subprocess.Popen(
            [sys.executable,
             "build_missing_inventory.py",
             env]
        )

        st.success(
            "Missing content job started"
        )

with col3:

    if st.button(
        "Download Assets"
    ):

        subprocess.Popen(
            [sys.executable,
             "download_assets.py"]
        )

        st.success(
            "Download job started"
        )

with col4:

    if st.button(
        "Retry Failed"
    ):

        subprocess.Popen(
            [sys.executable,
             "retry_failed.py"]
        )

        st.success(
            "Retry job started"
        )

st.divider()

# ==================================================
# STATUS
# ==================================================

if os.path.exists(
    STATUS_FILE
):

    try:

        with open(
            STATUS_FILE,
            "r"
        ) as f:

            status = json.load(f)

        st.subheader(
            "Current Job"
        )

        st.write(
            f"Job: {status.get('job','IDLE')}"
        )

        st.write(
            f"Status: {status.get('status','UNKNOWN')}"
        )

        percent = (
            status.get(
                "percent",
                0
            ) / 100
        )

        st.progress(percent)

        st.write(
            f"{status.get('percent',0)}%"
        )

        if "current_page" in status:

            st.write(
                f"Page: "
                f"{status['current_page']}"
            )

        if "asset_records" in status:

            st.write(
                f"Records: "
                f"{status['asset_records']}"
            )

    except Exception as ex:

        st.warning(
            str(ex)
        )

st.divider()

# ==================================================
# LOAD CSV DATA
# ==================================================

asset_count = 0
missing_count = 0

success_count = 0
failed_count = 0
pending_count = 0

asset_df = pd.DataFrame()
missing_df = pd.DataFrame()

if os.path.exists(
    ASSET_CSV
):

    asset_df = pd.read_csv(
        ASSET_CSV
    )

    asset_count = len(
        asset_df
    )

    if "Status" in asset_df.columns:

        success_count = len(
            asset_df[
                asset_df["Status"]
                == "SUCCESS"
            ]
        )

        failed_count = len(
            asset_df[
                asset_df["Status"]
                == "FAILED"
            ]
        )

        pending_count = len(
            asset_df[
                asset_df["Status"]
                == "PENDING"
            ]
        )

if os.path.exists(
    MISSING_CSV
):

    missing_df = pd.read_csv(
        MISSING_CSV
    )

    missing_count = len(
        missing_df
    )

# ==================================================
# METRICS
# ==================================================

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric(
    "Assets",
    asset_count
)

m2.metric(
    "Missing",
    missing_count
)

m3.metric(
    "Downloaded",
    success_count
)

m4.metric(
    "Failed",
    failed_count
)

m5.metric(
    "Pending",
    pending_count
)

# ==================================================
# PROGRESS
# ==================================================

if asset_count > 0:

    completed = (
        success_count +
        failed_count
    )

    download_pct = (
        completed /
        asset_count
    )

    st.subheader(
        "Download Progress"
    )

    st.progress(
        download_pct
    )

    st.write(
        f"{completed} "
        f"/ "
        f"{asset_count}"
    )

st.divider()

# ==================================================
# DOWNLOAD BUTTONS
# ==================================================

c1, c2 = st.columns(2)

with c1:

    if os.path.exists(
        ASSET_CSV
    ):

        with open(
            ASSET_CSV,
            "rb"
        ) as f:

            st.download_button(
                "Download Asset CSV",
                data=f,
                file_name=ASSET_CSV
            )

with c2:

    if os.path.exists(
        MISSING_CSV
    ):

        with open(
            MISSING_CSV,
            "rb"
        ) as f:

            st.download_button(
                "Download Missing CSV",
                data=f,
                file_name=MISSING_CSV
            )

# ==================================================
# TABS
# ==================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Asset Inventory",
        "Missing Content",
        "Media Explorer",
        "Logs"
    ]
)

# ==================================================
# ASSET INVENTORY
# ==================================================

with tab1:

    st.subheader(
        "Asset Inventory"
    )

    if len(asset_df):

        search = st.text_input(
            "Search Assets"
        )

        df = asset_df.copy()

        if search:

            df = df[
                df.astype(str)
                .apply(
                    lambda x:
                    x.str.contains(
                        search,
                        case=False
                    )
                )
                .any(axis=1)
            ]

        st.dataframe(
            df,
            width="stretch"
        )

    else:

        st.info(
            "Asset inventory not found."
        )

# ==================================================
# MISSING CONTENT
# ==================================================

with tab2:

    st.subheader(
        "Missing Content"
    )

    if len(missing_df):

        search = st.text_input(
            "Search Missing"
        )

        df = missing_df.copy()

        if search:

            df = df[
                df.astype(str)
                .apply(
                    lambda x:
                    x.str.contains(
                        search,
                        case=False
                    )
                )
                .any(axis=1)
            ]

        st.dataframe(
            df,
            width="stretch"
        )

    else:

        st.info(
            "No missing content file."
        )

# ==================================================
# MEDIA EXPLORER
# ==================================================

with tab3:

    st.subheader(
        "Downloaded Media"
    )

    if os.path.exists(
        MEDIA_ROOT
    ):

        for root, dirs, files in os.walk(
            MEDIA_ROOT
        ):

            level = (
                root.replace(
                    MEDIA_ROOT,
                    ""
                )
                .count(os.sep)
            )

            indent = (
                "  " * level
            )

            st.write(
                f"{indent}📁 "
                f"{os.path.basename(root)}"
            )

            for file in files:

                st.write(
                    f"{indent}📄 {file}"
                )

    else:

        st.info(
            "No media downloaded."
        )

# ==================================================
# LOGS
# ==================================================

with tab4:

    st.subheader(
        "Logs"
    )

    if os.path.exists(
        LOG_FILE
    ):

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            content = f.read()

        st.text_area(
            "Log Output",
            content,
            height=500
        )

    else:

        st.info(
            "Log file not found."
        )