from datetime import datetime, timedelta
from typing import Any
from apis.coingecko.queries import (
    get_raw_historical_price_range,
)
from apis.deepdao.adapters import (
    get_snapshot_id,
)
from apis.deepdao.queries import (
    get_raw_dao_data,
    get_raw_dao_list,
    get_raw_token_metadata,
)
from apis.snapshot.execution import get_proposals, get_votes


def sanitize_vote(vote: dict, price_map: dict[float, float], dao_id: str):
    vote_time = datetime.fromtimestamp(vote["created"]).replace(
        hour=0, minute=0, second=0
    )
    vote_price = price_map.get(vote_time.timestamp())

    vote["proposal_id"] = vote["proposal"]["id"]
    vote["proposal_scores_total"] = vote["proposal"]["scores_total"]
    vote["proposal_state"] = vote["proposal"]["state"]
    vote["proposal_space_name"] = vote["proposal"]["space"]["name"]
    vote["proposal_type"] = vote["proposal"]["type"]
    vote["proposal_scores"] = vote["proposal"]["scores"]
    vote["proposal_choices"] = vote["proposal"]["choices"]
    vote["organization_id"] = dao_id
    vote["proposal_space_id"] = vote["proposal"]["space"]["id"]
    vote["cost"] = vote["vp"] * vote_price if vote_price else 0
    vote["cost_per_vote"] = vote_price if vote_price else 0
    del vote["proposal"]


def get_historical_prices_per_date(
    token_address: str, chain_name: str, start: int, end: int
) -> dict[float, float]:
    raw_historical_price_range = get_raw_historical_price_range(
        token_address, chain_name, start, end
    )
    if not raw_historical_price_range:
        return None
    price_map = dict()

    for price in raw_historical_price_range:
        timestamp = datetime.fromtimestamp(price[0] / 1e3).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        price_map[timestamp.timestamp()] = price[1]
    return price_map


def get_price_map(votes: dict, token_metadata: dict) -> dict[float, float]:
    start = (
        datetime.fromtimestamp(votes["votes"][-1]["created"])
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    end = (
        datetime.fromtimestamp(votes["votes"][0]["created"]).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        + timedelta(1)
    ).timestamp()

    price_map = get_historical_prices_per_date(
        token_metadata["tokenAddress"],
        token_metadata["chainName"].lower(),
        start,
        end,
    )
    return price_map


async def get_proposal_payload(proposal: dict, dao_metadata: dict) -> dict | None:
    print(f"\tprocessing proposal {proposal['id']}")
    dao_id, token_metadata, _ = dao_metadata.values()

    proposal_id: str = proposal["id"]
    payload = {proposal_id: dict()}

    proposal["space_name"] = proposal["space"]["name"]
    proposal["space_id"] = proposal["space"]["id"]
    del proposal["space"]

    votes = await get_votes(proposal_id)
    if not votes["votes"] or votes["votes"][0]["proposal"]["type"] in [
        "quadratic",
        "ranked-choice",
    ]:
        return None

    payload[proposal_id]["proposal"] = proposal
    price_map = get_price_map(votes, token_metadata)
    if not price_map:
        return None

    for vote in votes["votes"]:
        sanitize_vote(vote, price_map, dao_id)

    payload[proposal_id].update(votes)
    return payload


async def get_dao_metadata(raw_dao: dict) -> dict[str, Any]:
    raw_dao_id = raw_dao.get("organizationId")
    raw_dao_token_metadata = await get_raw_token_metadata(raw_dao_id)
    raw_dao_data = get_raw_dao_data(raw_dao_id)
    dao_snapshot_id = get_snapshot_id(raw_dao_data)

    return {
        "id": raw_dao_id,
        "token_metadata": raw_dao_token_metadata,
        "snapshot_id": dao_snapshot_id,
    }


async def get_single_dao_snapshot(
    raw_dao: dict, proposal_limit: int = None
) -> dict[str, dict] | None:
    print(f"Getting raw snapshot data for {raw_dao['daoName']}")
    dao_metadata = await get_dao_metadata(raw_dao)
    _, _, dao_snapshot_id = dao_metadata.values()
    if not dao_snapshot_id:
        return None

    raw_dao_proposals: list[dict] = (
        await get_proposals(dao_snapshot_id, proposal_limit)
    )["proposals"]
    print("\tDone getting proposals")
    if not raw_dao_proposals:
        return None
    dao_proposals: dict[str, dict] = dict()

    for proposal in raw_dao_proposals:
        payload = await get_proposal_payload(proposal, dao_metadata)
        if payload:
            dao_proposals.update(payload)
    return dao_proposals


async def dao_snapshot_data(
    list_size: int,
    max_number_of_daos: int,
    proposal_limit: int = None,
) -> list[dict]:
    blacklist = [
        "Wonderland",
        "Fei",
        "OlympusDAO",
        "BitDAO",
        "Compound",
        "Illuvium",
        "Synthetix",
    ]
    raw_daos: list[dict] = get_raw_dao_list(list_size)
    daos = []

    dao_counter = 0
    i = 0

    while dao_counter < max_number_of_daos and i < len(raw_daos):
        if raw_daos[i]["daoName"] not in blacklist:
            dao = await get_single_dao_snapshot(raw_daos[i], proposal_limit)
            if dao:
                daos.append(dao)
                dao_counter += 1
        i += 1

    return daos
