from time import sleep

from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError

from .queries import proposals, votes

transport = AIOHTTPTransport(url="https://hub.snapshot.org/graphql")


async def get_proposals(space_id: str, upper_limit: int) -> dict[str, list[dict]]:

    try:
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = proposals(space_id, upper_limit)

            result = await session.execute(query)
    except TransportServerError:
        print("\tWaiting a minute to try a Snapshot again")
        sleep(60)
        result = await get_proposals(space_id, upper_limit)
    return result


async def get_votes(proposal_id: str) -> dict[str, list[dict]]:
    try:
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = votes(proposal_id)

            result = await session.execute(query)
    except TransportServerError:
        print("\tWaiting a minute to try a Snapshot again")
        sleep(60)
        result = await get_votes(proposal_id)
    return result
