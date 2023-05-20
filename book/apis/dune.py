from os import getenv

from dotenv import load_dotenv
from httpx import Client, Timeout


load_dotenv()

DUNE_API = getenv("DUNE_API")
HEADERS = {"x-dune-api-key": DUNE_API}
TIMEOUT = Timeout(10.0, connect=30.0, read=30.0)


def run_query(query: str) -> dict:
     with Client(headers=HEADERS, timeout=TIMEOUT) as client:
        resp = client.get(query)
        return resp.json()


def get_top_uniswap_proposals(limit: int = 10) -> list[dict] | None:
    dune_top_proposal_query = f"https://api.dune.com/api/v1/query/2488751/results"
    resp_json = run_query(dune_top_proposal_query)
    result: dict | None = resp_json.get("result")
    if result:
        return result.get("rows")
    return None
