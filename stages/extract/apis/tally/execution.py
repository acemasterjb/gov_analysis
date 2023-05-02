from os import getenv

from gql import dsl, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError
from dotenv import load_dotenv

from .queries import organizations, proposals, votes


load_dotenv()
headers = {"Api-key": getenv("TALLY_API")}
transport = AIOHTTPTransport(
    url="https://api.tally.xyz/query", headers=headers, timeout=120
)

client = Client(transport=transport, fetch_schema_from_transport=True)


async def get_votes(
    chain_id: str,
    proposal_ids: list[str],
    governance_ids: list[str] = [],
    upper_limit: int = 200,
    skip: int = 0,
) -> dict[str, dict]:
    session = await client.connect_async(reconnecting=True)
    query = votes(chain_id, proposal_ids, governance_ids, upper_limit, skip)

    try:
        response = await session.execute(query)
    except TransportServerError:
        await client.close_async()
        raise
    await client.close_async()

    result = {proposal["id"]: proposal for proposal in response["proposals"]}

    maybe_next_page = {
        id: proposal for id, proposal in result.items() if proposal["votes"]
    }

    if maybe_next_page:
        maybe_next_page_proposal_ids = list(maybe_next_page.keys())
        next_page = await get_votes(
            chain_id,
            maybe_next_page_proposal_ids,
            governance_ids,
            upper_limit,
            skip + 200,
        )

        for proposal_id, proposal in next_page.copy().items():
            if proposal["votes"]:
                votes_in_next_page = maybe_next_page[proposal_id]["votes"].copy()

                votes_in_next_page.extend(proposal["votes"])
                result[proposal_id]["votes"].extend(votes_in_next_page)

    return result


async def get_proposals(
    organization_ids: list[str],
    upper_limit: int = 150,
    skip: int = 0,
) -> dict[str, list[dict]]:
    session = await client.connect_async(reconnecting=True)
    ds = dsl.DSLSchema(client.schema)
    query = proposals(ds, organization_ids[:10], upper_limit, skip)
    temp_organization_ids = organization_ids
    del temp_organization_ids[:10]

    response = await session.execute(query)

    await client.close_async()

    if temp_organization_ids:
        response["governances"].extend(
            (await get_proposals(temp_organization_ids))["governances"]
        )

    if not response.get("governances"):
        return {"governances": []}
    return response


async def get_organizations(
    organization_names: list[str], upper_limit: int = None, skip: int = 0
) -> dict[str, list[dict]]:
    session = await client.connect_async(reconnecting=True)
    ds = dsl.DSLSchema(client.schema)
    query = organizations(ds, organization_names, upper_limit, skip)

    response = await session.execute(query)

    await client.close_async()

    if not response.get("organizations"):
        return {"organizations": []}
    return response
