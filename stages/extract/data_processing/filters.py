from typing import Any


def find_dao(user_dao_name: str, dao_metadata_list: list[dict[str, dict]]) -> dict:
    return next(
        (
            dao_metadata
            for dao_metadata in dao_metadata_list
            if user_dao_name in get_positive_cases_for(dao_metadata)
        ),
        {},
    )


def get_positive_cases_for(dao_metadata: dict[str, Any]) -> list[str]:
    api_dao_name: str = dao_metadata["daoName"]
    return [
        api_dao_name,
        api_dao_name.lower(),
        api_dao_name.upper(),
    ]


def get_valid_organizations(
    actual_token_addresses: list[str], organizations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        organization
        for organization in organizations
        if any(
            contract["address"] in actual_token_addresses
            for governance in organization["governances"]
            for contract in governance["contracts"]["tokens"]
        )
    ]
