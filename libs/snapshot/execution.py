from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport

from .queries import proposals, votes

transport = AIOHTTPTransport(url="https://hub.snapshot.org/graphql")


async def get_proposals(space_id: str, limit: int) -> dict[str, list[dict]]:

    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        query = proposals(space_id, limit)

        result = await session.execute(query)
        return result


async def get_votes(proposal_id: str) -> dict[str, list[dict]]:
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        query = votes(proposal_id)

        result = await session.execute(query)
        return result
