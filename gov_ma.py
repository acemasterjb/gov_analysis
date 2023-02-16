from asyncio import gather, run as asyncio_run
from typing import Any

import pandas as pd

from libs.apis.coingecko.adapters import (
    get_circulating_supply,
    get_market_cap,
    get_token_price,
    get_total_supply,
)
from libs.apis.coingecko.queries import (
    get_raw_market_data,
    get_raw_market_data_by_symbol,
)
from libs.apis.deepdao.adapters import (
    get_governance_participants,
    get_native_token_address,
    get_native_token_symbol,
    get_organization_aum,
    get_token_holders_count,
)
from libs.apis.deepdao.queries import (
    get_raw_dao_list,
    get_raw_organization_data,
    get_raw_token_metadata,
)


def get_treasury_v_market_cap(
    raw_organization_data: dict[str, Any], raw_market_data: dict[str, Any]
) -> float:
    if not raw_market_data or not raw_organization_data:
        return None
    treasury = get_organization_aum(raw_organization_data)
    market_cap = get_market_cap(raw_market_data)

    try:
        return treasury / market_cap
    except ZeroDivisionError:
        return None


async def get_dao(raw_dao: dict) -> dict[str, Any] | None:
    raw_dao_id = raw_dao["organizationId"]
    raw_dao_chain_name = raw_dao["mainTreasuryTitle"].lower()
    if raw_dao_chain_name not in ["ethereum", "solana", "substrate"]:
        return None
    raw_token_metadata, raw_organization_data = await gather(
        get_raw_token_metadata(raw_dao_id), get_raw_organization_data(raw_dao_id)
    )

    subtrate_translator = {
        "polkadot": "polkadot",
        "phala": "pha",
        "kusama": "kusama",
    }

    native_token_address = get_native_token_address(raw_token_metadata)
    if raw_dao_chain_name == "substrate":
        try:
            raw_market_data = await get_raw_market_data_by_symbol(
                subtrate_translator[native_token_address]
            )
        except KeyError:
            return None
    else:
        raw_market_data = await get_raw_market_data(
            native_token_address, raw_dao_chain_name
        )

    dao = {
        "token_symbol": get_native_token_symbol(raw_token_metadata),
        "token_price": get_token_price(raw_market_data),
        "total_supply": get_total_supply(raw_market_data),
        "circulating_supply": get_circulating_supply(raw_market_data),
        "market_cap": get_market_cap(raw_market_data),
        "treasury": get_organization_aum(raw_organization_data),
        "treasury_vs_market_cap": get_treasury_v_market_cap(
            raw_organization_data, raw_market_data
        ),
        "token_holders": get_token_holders_count(raw_organization_data),
        "governance_participants": get_governance_participants(raw_organization_data),
        "dao_name": raw_dao["daoName"],
        "chain": raw_dao_chain_name,
    }
    return dao


async def get_daos(max_number_of_daos: int, list_size: int) -> list[dict[str, Any]]:
    print("Getting DAO data from APIs...")
    raw_daos: list[dict] = get_raw_dao_list(list_size)
    daos: list[dict[str, Any]] = []

    dao_counter = 0
    i = 0

    while dao_counter < max_number_of_daos:
        dao = await get_dao(raw_daos[i])
        if dao:
            daos.append(dao)
            dao_counter += 1
        i += 1

    return daos


def get_dao_dataframe(dao_objects: list[dict]) -> pd.DataFrame:
    index = pd.Index(
        [dao["dao_name"] for dao in dao_objects],
        "str",
        name="DAO Name",
        tupleize_cols=False,
    )
    return pd.DataFrame(dao_objects, index=index).drop(["dao_name"], axis=1)


def export_excel_sheet(dao_dataframe: pd.DataFrame):
    dao_dataframe.to_excel(
        "./dao_market_analysis.xls", "DAO Stats", "N/A", engine="openpyxl"
    )


daos = asyncio_run(get_daos(60, 100))

print("Done getting DAO data")
print("Exporting to Excel Spreadsheet...")
export_excel_sheet(get_dao_dataframe(daos))
print("Excel Spreadsheet generated")
