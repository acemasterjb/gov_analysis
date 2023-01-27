from typing import Any


def get_native_token_address(raw_token_metadata: dict[str, str]) -> str:
    if not raw_token_metadata:
        return None
    return raw_token_metadata.get("tokenAddress")


def get_native_token_symbol(raw_token_metadata: dict[str, str]) -> str:
    if not raw_token_metadata:
        return None
    return raw_token_metadata.get("tokenSymbol")


def get_organization_aum(raw_organization_data: dict[str, Any]) -> float:
    if not raw_organization_data:
        return None
    return raw_organization_data.get("aum")


def get_token_holders_count(raw_organization_data: dict[str, Any]) -> int:
    if not raw_organization_data:
        return None
    return raw_organization_data.get("membersCount")


def get_governance_participants(raw_organization_data: dict[str, Any]) -> int:
    if not raw_organization_data:
        return None
    return raw_organization_data.get("votesCount")


def get_snapshot_id(raw_dao_data: list[dict]) -> str | None:
    try:
        snapshot_object: dict = raw_dao_data[0]
    except KeyError:
        print(raw_dao_data)
        raise
    if snapshot_object.get("platformTitle") != "Snapshot":
        return None
    return (
        snapshot_object["website"].split("/")[-1]
        if snapshot_object["website"]
        else None
    )
