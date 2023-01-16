from typing import Any


def get_token_price(raw_market_data: dict[str, Any]) -> float:
    if not raw_market_data:
        return None
    return raw_market_data["market_data"]["current_price"]["usd"]


def get_total_supply(raw_market_data: dict[str, Any]) -> int:
    if not raw_market_data:
        return None
    return raw_market_data["market_data"]["total_supply"]


def get_circulating_supply(raw_market_data: dict[str, Any]) -> int:
    if not raw_market_data:
        return None
    return raw_market_data["market_data"]["circulating_supply"]


def get_market_cap(raw_market_data: dict[str, Any]) -> float:
    if not raw_market_data:
        return None
    return raw_market_data["market_data"]["market_cap"]["usd"]
