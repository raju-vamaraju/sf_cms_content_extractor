import pandas as pd

df = pd.read_csv(
    "cms_inventory.csv"
)

failed = df[
    df["Status"] == "FAILED"
]

failed.to_csv(
    "failed_downloads.csv",
    index=False
)

print(
    f"Failed files: {len(failed)}"
)