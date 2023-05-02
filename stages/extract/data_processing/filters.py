from typing import Any


def find_dao(
    user_dao_name: str, dao_metadata_list: list[dict[str, dict]]
) -> dict | None:
    for dao_metadata in dao_metadata_list:
        api_dao_name = dao_metadata["daoName"]
        positive_cases: list[str] = [
            api_dao_name,
            api_dao_name.lower(),
            api_dao_name.upper(),
        ]

        if user_dao_name in positive_cases:
            return dao_metadata
    return None


def get_valid_organizations(
    actual_token_addresses: list[str], organizations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    actual_organizations = []

    for organization in organizations:
        governances: list[dict[str, str]] = organization["governances"]
        for governance in governances:
            contracts = governance["contracts"]
            for contract in contracts["tokens"]:
                if contract["address"] in actual_token_addresses:
                    actual_organizations.append(organization)
                    continue

    return actual_organizations


def get_governor_from_deepdao_assets(
    deepdao_assets_response: list[dict[str, Any]]
) -> str | None:
    for asset in deepdao_assets_response:
        if asset["description"] == "Governor":
            return asset["address"]
