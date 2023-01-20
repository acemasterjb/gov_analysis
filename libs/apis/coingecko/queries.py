from time import sleep
from typing import Any

from httpx import AsyncClient, Client, Timeout

COINGECKO_HEADERS = {"accept": "application/json"}
TIMEOUT = Timeout(10.0, connect=30.0, read=30.0)


async def get_raw_market_data(token_address: str, chain_name: str) -> dict[str, Any]:
    if chain_name == "polygon":
        chain_name = "polygon-pos"
    url = (
        f"https://api.coingecko.com/api/v3/coins/{chain_name}/contract/{token_address}"
    )

    async with AsyncClient(headers=COINGECKO_HEADERS, timeout=TIMEOUT) as client:
        resp = await client.get(url)
        resp_json: dict[str, Any] = resp.json()
        status: dict = resp_json.get("status")
        if status:
            if status.get("error_code") >= 400:
                print("\twaiting a minute for CG...")
                sleep(60)
                return await get_raw_market_data(token_address, chain_name)
        return resp_json if resp_json.get("error") is None else {}


async def get_raw_market_data_by_symbol(token_symbol: str):
    url = f"https://api.coingecko.com/api/v3/coins/{token_symbol}"
    params = {"tickers": True, "market_data": True, "sparkline": True}

    async with AsyncClient(
        headers=COINGECKO_HEADERS, timeout=TIMEOUT, params=params
    ) as client:
        resp = await client.get(url)
        resp_json: dict[str, Any] = resp.json()
        status: dict = resp_json.get("status")
        if status:
            if status.get("error_code") >= 400:
                print("\twaiting a minute for CG...")
                sleep(60)
                return await get_raw_market_data_by_symbol(token_symbol)
        return resp_json if resp_json.get("error") is None else {}




def get_raw_historical_price_range(
    token_address: str, chain_name: str, start: int, end: int
):
    if chain_name == "polygon":
        chain_name = "polygon-pos"
    url = f"https://api.coingecko.com/api/v3/coins/{chain_name}/contract/{token_address}/market_chart/range/"

    params = {
        "vs_currency": "usd",
        "from": start,
        "to": end,
    }

    with Client(headers=COINGECKO_HEADERS, timeout=TIMEOUT, params=params) as client:
        resp = client.get(url)
        resp_json: dict[str, Any] = resp.json()
        # print(resp.url)
        status: dict = resp_json.get("status")
        if status:
            if status.get("error_code") >= 400:
                print("\twaiting a minute for CG...")
                sleep(60)
                return get_raw_historical_price_range(
                    token_address, chain_name, start, end
                )
        return resp_json["prices"] if resp_json.get("error") is None else {}
