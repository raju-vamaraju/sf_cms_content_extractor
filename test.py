import requests
from simple_salesforce import Salesforce

# ==========================================
# SALESFORCE LOGIN
# ==========================================

sf = Salesforce(
    username="raju.vamaraju@insigniafinancial.com.au",
    password="Doitraju001",
    security_token="BduNkV5ZK7apF19bzmQLerDi",
    domain="test"  # sandbox
)

print("Connected to Salesforce")
print("Instance:", sf.sf_instance)

# ==========================================
# AUTH HEADER
# ==========================================

headers = {
    "Authorization": f"Bearer {sf.session_id}"
}

instance_url = f"https://{sf.sf_instance}"

# ==========================================
# TEST IMAGE DOWNLOAD
# ==========================================

url = (
    f"{instance_url}"
    "/services/data/v61.0/connect/cms/delivery/channels/"
    "0ap6F0000008OU2/media/"
    "MCG6LK6FVTBNEBFNAOM6D2WSBQPA/content"
)

print("\nURL:")
print(url)

response = requests.get(
    url,
    headers=headers,
    stream=True,
    timeout=60
)

print("\nStatus Code:", response.status_code)
print("Content Type:", response.headers.get("Content-Type"))

if response.status_code == 200:

    output_file = "Mercer_Logo.png"

    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"\nSUCCESS - Saved to {output_file}")

else:

    print("\nFAILED")
    print(response.text)