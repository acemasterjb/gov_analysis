from asyncio import run as asyncio_run
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any
from pprint import PrettyPrinter

import pandas as pd

from libs.apis.coingecko.queries import (
    get_raw_historical_price_range,
)
from libs.apis.deepdao.adapters import (
    get_snapshot_id,
)
from libs.apis.deepdao.queries import (
    get_raw_dao_data,
    get_raw_dao_list,
    get_raw_token_metadata,
)
from libs.apis.snapshot.execution import get_proposals, get_votes
from libs.data_processing.reaggregation import (
    reaggregate_votes_approval,
    reaggregate_votes_single_choice_or_basic,
    reaggregate_votes_weighted,
)
from libs.data_processing.filters import get_quartile_by_vp


pp = PrettyPrinter(2)


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

    proposal_id = proposal["id"]
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


async def get_dao_snapshot_data(
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


async def get_all_dao_snapshot_data(
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
    )


def get_all_snapshot_dataframes_for_dao(
    dao_snapshot_datas: list[dict],
) -> list[pd.DataFrame]:
    print("Generating DFs for dao snapshot data")
    dao_snapshot_dfs = []
    for snapshot_data in dao_snapshot_datas:
        for proposal in snapshot_data.values():
            dao_snapshot_dfs.append(get_snapshot_dataframe(proposal["votes"]))

    return dao_snapshot_dfs


snapshot_datas = asyncio_run(get_all_dao_snapshot_data(50, 20, 50))
snapshot_dataframes = get_all_snapshot_dataframes_for_dao(snapshot_datas)


def filter_top_shareholders_from_df(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    def reaggregate_votes(
        unfiltered_proposal: pd.DataFrame, top_shareholders: pd.Series
    ) -> pd.DataFrame:
        proposal_type_map = {
            "single-choice": reaggregate_votes_single_choice_or_basic,
            "basic": reaggregate_votes_single_choice_or_basic,
            "approval": reaggregate_votes_approval,
            "weighted": reaggregate_votes_weighted,
        }
        proposal_type: str = unfiltered_proposal.iloc[0]["proposal_type"]

        result: pd.DataFrame = proposal_type_map[proposal_type](
            unfiltered_proposal, top_shareholders
        )

        return result

    top_shareholders_df = get_quartile_by_vp(snapshot_df, 0.95)
    top_shareholder_addresses = top_shareholders_df["voter"]
    reaggregated_snapshot_df = reaggregate_votes(snapshot_df, top_shareholder_addresses)
    if not reaggregated_snapshot_df.empty:
        snapshot_df = reaggregated_snapshot_df
    return (
        snapshot_df.loc[
            lambda df: [voter not in top_shareholder_addresses for voter in df["voter"]]
        ]
    ).drop(["voter", "id"], axis=1)


def filter_top_shareholders_from_all_dfs(
    snapshot_dfs: list[pd.DataFrame],
) -> list[pd.DataFrame]:
    print("Filtereing out top 10 holders for each dao")
    filtered_dfs = []
    for snapshot_df in snapshot_dfs:
        snapshot_df_copy = snapshot_df.copy()
        try:
            snapshot_df_copy["proposal_scores"] = deepcopy(
                snapshot_df["proposal_scores"].values
            )
        except KeyError:
            pp.pprint(snapshot_df)
            raise
        filtered_dfs.append(filter_top_shareholders_from_df(snapshot_df_copy))
    return filtered_dfs


filtered_snapshot_dfs = filter_top_shareholders_from_all_dfs(snapshot_dataframes)


def merge_organization_dataframes(
    filtered_snapshot_dfs: list[pd.DataFrame],
) -> list[pd.DataFrame]:
    organization_map: dict[str, list[pd.DataFrame]] = dict()
    for snapshot_df in filtered_snapshot_dfs:
        if snapshot_df.empty:
            continue
        organization_name: str = snapshot_df.iloc[0]["proposal_space_name"]
        if organization_name not in organization_map.keys():
            organization_map[organization_name] = []
        organization_map[organization_name].append(snapshot_df)

    organization_dfs = []
    for organization in organization_map.keys():
        organization_df = pd.concat(organization_map[organization])
        organization_dfs.append(organization_df)

    return organization_dfs


organization_dataframes = merge_organization_dataframes(filtered_snapshot_dfs)


def export_organization_dataframes_to_xls(
    organization_dataframes: list[pd.DataFrame], file_name: str
):
    print("Generating Spreadsheet...")
    with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
        for organization_dataframe in organization_dataframes:
            organization_name: str = organization_dataframe.iloc[0][
                "proposal_space_name"
            ]
            if "/" in organization_name:
                organization_name = organization_name.replace("/", "_")
            organization_dataframe.to_excel(writer, organization_name, "N/A")

    print("Done")


# pd.set_option("display.width", 4000)
# pd.set_option("display.max_columns", 1000)
# [print(df, end="\n\n") for df in organization_dataframes]

export_organization_dataframes_to_xls(
    merge_organization_dataframes(snapshot_dataframes), "./plutocracy_report.xlsx"
)
export_organization_dataframes_to_xls(
    organization_dataframes, "./plutocracy_report_filtered.xlsx"
)
