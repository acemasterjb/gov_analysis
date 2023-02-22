from time import sleep
from typing import Any

from httpx import AsyncClient, Client, Timeout
from tenacity import *

COINGECKO_HEADERS = {"accept": "application/json"}
TIMEOUT = Timeout(10.0, connect=30.0, read=30.0)


@retry(stop=stop_after_attempt(5), wait=wait_incrementing(10, 10))
async def get_raw_market_data(token_address: str, chain_name: str) -> dict[str, Any]:
    if chain_name == "polygon":
        chain_name = "polygon-pos"
    url = (
        f"https://api.coingecko.com/api/v3/coins/{chain_name}/contract/{token_address}"
    )

    async with AsyncClient(headers=COINGECKO_HEADERS, timeout=TIMEOUT) as client:
        resp = await client.get(url)
        resp_json: dict[str, Any] = resp.json()
        return resp_json if resp_json.get("error") is None else {}


@retry(stop=stop_after_attempt(5), wait=wait_incrementing(10, 10))
async def get_raw_market_data_by_symbol(token_symbol: str):
    url = f"https://api.coingecko.com/api/v3/coins/{token_symbol}"
    params = {"tickers": True, "market_data": True, "sparkline": True}

    async with AsyncClient(
        headers=COINGECKO_HEADERS, timeout=TIMEOUT, params=params
    ) as client:
        resp = await client.get(url)
        resp_json: dict[str, Any] = resp.json()
        return resp_json if resp_json.get("error") is None else {}


@retry(stop=stop_after_attempt(5), wait=wait_incrementing(10, 10))
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
        try:
            return resp_json["prices"] if resp_json.get("error") is None else {}
        except KeyError:
            sleep(60)
            return get_raw_historical_price_range(token_address, chain_name, start, end)
