from asyncio import run as asyncio_run
from typing import Any
from datetime import datetime, timedelta
from pprint import PrettyPrinter

import pandas as pd

from libs.coingecko.queries import (
    get_raw_historical_price_range,
)
from libs.deepdao.adapters import (
    get_snapshot_id,
)
from libs.deepdao.queries import (
    get_raw_dao_data,
    get_raw_dao_list,
    get_raw_token_metadata,
)

from libs.snapshot.execution import get_proposals, get_votes


pp = PrettyPrinter(2)


def get_historical_prices_per_date(
    token_address: str, chain_name: str, start: int, end: int
) -> dict[float, float]:
    raw_historical_price_range = get_raw_historical_price_range(
        token_address, chain_name, start, end
    )
    price_map = dict()

    for price in raw_historical_price_range:
        timestamp = datetime.fromtimestamp(price[0] / 1e3).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        price_map[timestamp.timestamp()] = price[1]
    return price_map


async def get_dao_snapshot_data(raw_dao: dict, proposal_limit: int) -> dict[str, dict]:
    raw_dao_id = raw_dao.get("organizationId")
    raw_dao_token_metadata = await get_raw_token_metadata(raw_dao_id)
    raw_dao_data = get_raw_dao_data(raw_dao_id)
    dao_snapshot_id = get_snapshot_id(raw_dao_data)
    if not dao_snapshot_id:
        return None

    raw_dao_proposals: list[dict] = (
        await get_proposals(dao_snapshot_id, proposal_limit)
    )["proposals"]
    dao_proposals: dict[str, dict] = dict()

    for proposal in raw_dao_proposals:
        proposal_id = proposal["id"]
        dao_proposals[proposal_id] = dict()

        proposal["space_name"] = proposal["space"]["name"]
        proposal["space_id"] = proposal["space"]["id"]
        del proposal["space"]
        dao_proposals[proposal_id]["proposal"] = proposal

        votes = await get_votes(proposal_id)
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
            raw_dao_token_metadata["tokenAddress"],
            raw_dao_token_metadata["chainName"].lower(),
            start,
            end,
        )
        for vote in votes["votes"]:
            vote_time = datetime.fromtimestamp(vote["created"]).replace(
                hour=0, minute=0, second=0
            )
            vote_price = price_map.get(vote_time.timestamp())

            vote["proposal_id"] = vote["proposal"]["id"]
            vote["proposal_scores_total"] = vote["proposal"]["scores_total"]
            vote["proposal_state"] = vote["proposal"]["state"]
            vote["proposal_space_name"] = vote["proposal"]["space"]["name"]
            vote["proposal_space_id"] = vote["proposal"]["space"]["id"]
            vote["cost"] = vote["vp"] * vote_price if vote_price else 0
            vote["cost_per_vote"] = vote_price if vote_price else 0
            del vote["proposal"]
        dao_proposals[proposal_id].update(votes)

    return dao_proposals


async def get_all_dao_snapshot_data(
    proposal_limit: int, list_size: int, max_number_of_daos: int
) -> list[dict]:
    raw_daos: list[dict] = get_raw_dao_list(list_size)
    daos: list[dict[str, Any]] = []

    dao_counter = 0
    i = 0

    while dao_counter < max_number_of_daos:
        dao = await get_dao_snapshot_data(raw_daos[i], proposal_limit)
        if dao:
            daos.append(dao)
            dao_counter += 1
        i += 1

    return daos


def get_snapshot_dataframe(dao_snapshot_vote_data: list[dict]) -> pd.DataFrame:
    index = pd.Index(
        [vote["voter"] for vote in dao_snapshot_vote_data],
        "str",
        name="Voter Address",
        tupleize_cols=False,
    )

    return pd.DataFrame(
        dao_snapshot_vote_data,
        index=index,
    ).drop(["voter", "id"], axis=1)


def get_all_snapshot_dataframes_for_dao(
    dao_snapshot_datas: list[dict],
) -> list[pd.DataFrame]:
    dao_snapshot_dfs = []
    for snapshot_data in dao_snapshot_datas:
        for proposal in snapshot_data.values():
            try:
                dao_snapshot_dfs.append(get_snapshot_dataframe(proposal["votes"]))
            except KeyError:
                pp.pprint(snapshot_data)
                raise

    return dao_snapshot_dfs


snapshot_datas = asyncio_run(get_all_dao_snapshot_data(5, 20, 5))
snapshot_dataframes = get_all_snapshot_dataframes_for_dao(snapshot_datas)


pd.set_option("display.width", 4000)
pd.set_option("display.max_columns", 1000)
[print(df, end="\n\n") for df in snapshot_dataframes]

# pp.pprint(run(get_votes("Qma8KF8jTV3kwBFdjfwE9jvLpPYVMdY6RVS9pJZ6QGEur6")))
# run(get_proposals("uniswap", 1))
