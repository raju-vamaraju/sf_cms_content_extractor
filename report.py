import pandas as pd

df = pd.read_csv(
    "cms_inventory.csv"
)

print()

print(
    "Total:",
    len(df)
)

print(
    "SUCCESS:",
    len(df[
        df.Status == "SUCCESS"
    ])
)

print(
    "FAILED:",
    len(df[
        df.Status == "FAILED"
    ])
)

print(
    "PENDING:",
    len(df[
        df.Status == "PENDING"
    ])
)

print(
    "ALREADY_EXISTS:",
    len(df[
        df.Status ==
        "ALREADY_EXISTS"
    ])
)