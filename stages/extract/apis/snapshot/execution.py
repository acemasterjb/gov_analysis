from asyncio import sleep
from os import getenv

from dotenv import load_dotenv
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError
from graphql import DocumentNode

from .queries import proposals, votes


load_dotenv()


async def try_result(query: DocumentNode, retry_attempt: int = 0) -> dict[str, list[dict]]:
    if retry_attempt > 5:
        print("\t---\n\tERROR: Failed attempt to connect to Snapshot.\n\t---\n")
        return dict()

    api_key = getenv("SNAPSHOT_API")
    headers = {"accept": "application/json", "x-api-key": api_key} if api_key else None
    transport = AIOHTTPTransport(
        url="https://hub.snapshot.org/graphql", headers=headers
    )
    client = Client(transport=transport)
    session = await client.connect_async(reconnecting=True)

    try:
        result = await session.execute(query)
    except TransportServerError:
        await client.close_async()
        await sleep(21)
        return await try_result(client, query, retry_attempt+1)
    finally:
        await client.close_async()

    return result


async def get_proposals(
    organization_id: str, upper_limit: int = None, skip: int = 0
) -> dict[str, list[dict]]:
    query = proposals(organization_id, upper_limit, skip=skip)
    result = await try_result(query)

    if not result["proposals"]:
        return {"proposals": []}
    return result


async def get_votes(proposal_id: str, skip: int = 0) -> dict[str, list[dict]]:
    query = votes(proposal_id, skip)
    result = await try_result(query)

    if not result["votes"]:
        return {"votes": []}
    if skip < 4999:
        if skip == 4000:
            skip -= 1
        result["votes"].extend(
            (await get_votes(proposal_id, skip + 1000))["votes"].copy()
        )
    return result
