from typing import Any

from httpx import AsyncClient, Client, Timeout

from .deep_dao_headers import headers


TIMEOUT = Timeout(10.0, connect=30.0, read=30.0)


def get_raw_dao_list(limit: int) -> list[dict]:
    url = f"https://deepdao-server.deepdao.io/dashboard/ksdf3ksa-937slj3?limit={limit}&offset=0&orderBy=totalValueUSD&order=DESC"

    with Client(headers=headers, timeout=TIMEOUT) as client:
        resp = client.get(url)
        return resp.json()["daosSummary"]


async def get_raw_token_metadata(organization_id: str) -> dict[str, str]:
    url = f"https://deepdao-server.deepdao.io/discussion/{organization_id}/projectToken"

    async with AsyncClient(headers=headers, timeout=TIMEOUT) as client:
        resp = await client.get(url)
        resp_json: dict[str, str] = resp.json()
        return resp_json.get("data")


def get_raw_dao_data(organization_id: str) -> list[dict]:
    url = f"https://deepdao-server.deepdao.io/organization/ksdf3ksa-937slj3/{organization_id}/dao"

    with Client(headers=headers, timeout=TIMEOUT) as client:
        resp = client.get(url)
        resp_json = resp.json()["data"]

        return resp_json
