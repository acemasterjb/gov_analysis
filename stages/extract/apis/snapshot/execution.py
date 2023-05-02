from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError

from .queries import proposals, votes

transport = AIOHTTPTransport(url="https://hub.snapshot.org/graphql")

client = Client(transport=transport)


async def get_proposals(
    organization_id: str, upper_limit: int = None, skip: int = 0
) -> dict[str, list[dict]]:
    session = await client.connect_async(reconnecting=True)
    query = proposals(organization_id, upper_limit, skip=skip)

    result = await session.execute(query)

    await client.close_async()

    if not result["proposals"]:
        return {"proposals": []}
    return result


async def get_votes(proposal_id: str, skip: int = 0) -> dict[str, list[dict]]:
    default = {"votes": []}

    session = await client.connect_async(reconnecting=True)
    query = votes(proposal_id, skip)

    try:
        result = await session.execute(query)
    except TransportServerError:
        return default

    await client.close_async()

    if not result["votes"]:
        return default
    if skip < 4999:
        if skip == 4000:
            skip -= 1
        result["votes"].extend((await get_votes(proposal_id, skip + 1000))["votes"])
    return result
