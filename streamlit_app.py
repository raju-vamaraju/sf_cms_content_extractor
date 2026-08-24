import os
import subprocess
import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Salesforce CMS Migration",
    layout="wide"
)

st.title("Salesforce CMS Migration Dashboard")

# ==========================================
# CONFIG
# ==========================================

ASSET_CSV = "cms_asset_inventory.csv"
MISSING_CSV = "cms_missing_inventory.csv"
LOG_FILE = "salesforce_cms_export/cms_export.log"
MEDIA_ROOT = "_media"

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.header("Environment")

env = st.sidebar.selectbox(
    "Environment",
    ["uat", "prd"]
)

# ==========================================
# ACTION BUTTONS
# ==========================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Build Inventory"):
        subprocess.Popen(
            ["python", "build_inventory.py", env]
        )
        st.success(
            "Inventory build started"
        )

with col2:
    if st.button("Find Missing Content"):
        subprocess.Popen(
            ["python", "build_missing_inventory.py", env]
        )
        st.success(
            "Missing content analysis started"
        )

with col3:
    if st.button("Download Assets"):
        subprocess.Popen(
            ["python", "download_assets.py"]
        )
        st.success(
            "Asset download started"
        )

with col4:
    if st.button("Retry Failed"):
        subprocess.Popen(
            ["python", "retry_failed.py"]
        )
        st.success(
            "Retry job started"
        )

st.divider()

# ==========================================
# DASHBOARD
# ==========================================

asset_count = 0
missing_count = 0
success_count = 0
failed_count = 0
pending_count = 0

if os.path.exists(ASSET_CSV):

    asset_df = pd.read_csv(
        ASSET_CSV
    )

    asset_count = len(asset_df)

    if "Status" in asset_df.columns:

        success_count = len(
            asset_df[
                asset_df["Status"] == "SUCCESS"
            ]
        )

        failed_count = len(
            asset_df[
                asset_df["Status"] == "FAILED"
            ]
        )

        pending_count = len(
            asset_df[
                asset_df["Status"] == "PENDING"
            ]
        )

if os.path.exists(MISSING_CSV):

    missing_df = pd.read_csv(
        MISSING_CSV
    )

    missing_count = len(
        missing_df
    )

# ==========================================
# METRICS
# ==========================================

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric(
    "Asset Records",
    asset_count
)

m2.metric(
    "Missing Content",
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

# ==========================================
# PROGRESS BAR
# ==========================================

if asset_count > 0:

    completed = (
        success_count +
        failed_count
    )

    progress = completed / asset_count

    st.subheader(
        "Download Progress"
    )

    st.progress(progress)

    st.write(
        f"{completed} / {asset_count}"
    )

st.divider()

# ==========================================
# TABS
# ==========================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Asset Inventory",
    "Missing Content",
    "Media Explorer",
    "Logs"
])

# ==========================================
# ASSET INVENTORY
# ==========================================

with tab1:

    st.header(
        "Asset Inventory"
    )

    if os.path.exists(ASSET_CSV):

        asset_df = pd.read_csv(
            ASSET_CSV
        )

        search = st.text_input(
            "Search Assets"
        )

        if search:
            asset_df = asset_df[
                asset_df.astype(str)
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
            asset_df,
            use_container_width=True
        )

    else:
        st.info(
            "Asset inventory not found."
        )

# ==========================================
# MISSING CONTENT
# ==========================================

with tab2:

    st.header(
        "Missing Content"
    )

    if os.path.exists(MISSING_CSV):

        missing_df = pd.read_csv(
            MISSING_CSV
        )

        search = st.text_input(
            "Search Missing Content"
        )

        if search:
            missing_df = missing_df[
                missing_df.astype(str)
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
            missing_df,
            use_container_width=True
        )

    else:
        st.info(
            "Missing content CSV not found."
        )

# ==========================================
# MEDIA EXPLORER
# ==========================================

with tab3:

    st.header(
        "Downloaded Media"
    )

    if os.path.exists(MEDIA_ROOT):

        for root, dirs, files in os.walk(
            MEDIA_ROOT
        ):

            level = root.replace(
                MEDIA_ROOT,
                ""
            ).count(os.sep)

            indent = "  " * level

            st.write(
                f"{indent}📁 "
                f"{os.path.basename(root)}"
            )

            for file in files:

                st.write(
                    f"{indent}    📄 {file}"
                )

    else:

        st.info(
            "No media downloaded yet."
        )

# ==========================================
# LOGS
# ==========================================

with tab4:

    st.header(
        "Execution Log"
    )

    if os.path.exists(LOG_FILE):

        with open(
            LOG_FILE,
            "r"
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