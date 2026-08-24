import json
from pathlib import Path

from simple_salesforce import Salesforce


CONFIG_FILE = "config.json"


def get_config(environment):
    """
    Returns configuration for an environment.
    """

    config_path = Path(CONFIG_FILE)

    with open(config_path, "r") as f:
        config = json.load(f)

    environment = environment.lower()

    if environment not in config:
        raise ValueError(
            f"Environment '{environment}' not found in config.json"
        )

    return config[environment]


def get_sf(environment):
    """
    Returns authenticated Salesforce object.

    prd   -> login
    other -> test
    """

    cfg = get_config(environment)

    sf_domain = (
        "login"
        if environment.lower() == "prd"
        else "test"
    )

    print(
        f"Connecting to Salesforce [{environment}] "
        f"using domain [{sf_domain}]..."
    )

    sf = Salesforce(
        username=cfg["username"],
        password=cfg["password"],
        security_token=cfg["security_token"],
        domain=sf_domain
    )

    return sf


def get_instance_url(sf):
    return f"https://{sf.sf_instance}"


if __name__ == "__main__":

    env = "uat"

    sf = get_sf(env)

    print("Connected")
    print(sf.sf_instance)