import json

with open("salesforce_cms_export/content.json") as f:
    data = json.load(f)

for item in data["items"]:
    if item.get("type") == "cms_image":
        print(json.dumps(item, indent=2))
        break