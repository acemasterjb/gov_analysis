from asyncio import sleep
from asyncio.exceptions import TimeoutError

from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError
from graphql import DocumentNode

from .queries import proposals, votes

transport = AIOHTTPTransport(url="https://hub.snapshot.org/graphql")

client = Client(transport=transport)


async def try_result(client: Client, query: DocumentNode) -> dict[str, list[dict]]:
    session = await client.connect_async(reconnecting=True)

    try:
        result = await session.execute(query)
    except (TransportServerError, TimeoutError):
        await client.close_async()
        await sleep(21)
        return await try_result(client, query)
    finally:
        await client.close_async()

    return result


async def get_proposals(
    organization_id: str, upper_limit: int = 0, skip: int = 0
) -> dict[str, list[dict]]:
    query = proposals(organization_id, upper_limit, skip=skip)
    result = await try_result(client, query)

    if not result["proposals"]:
        return {"proposals": []}
    return result


async def get_votes(proposal_id: str, skip: int = 0) -> dict[str, list[dict]]:
    query = votes(proposal_id, skip)
    result = await try_result(client, query)

    if not result["votes"]:
        return {"votes": []}
    if skip < 4999:
        if skip == 4000:
            skip -= 1
        result["votes"].extend(
            (await get_votes(proposal_id, skip + 1000))["votes"].copy()
        )
    return result
