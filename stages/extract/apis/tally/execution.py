from os import getenv

from gql import dsl, Client
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv

from .queries import organizations, proposals, votes


load_dotenv()
headers = {"Api-key": getenv("TALLY_API")}
transport = AIOHTTPTransport(
    url="https://api.tally.xyz/query", headers=headers, timeout=120
)

client = Client(transport=transport, fetch_schema_from_transport=True)


def get_governances_in_next_page(tally_result: dict[str, dict]) -> dict[str, dict]:
    proposals_with_more_pages = dict()
    for proposal_id, proposal in tally_result.items():
        if proposal["votes"]:
            proposals_with_more_pages[str(proposal_id)] = proposal

    return proposals_with_more_pages


async def get_votes(
    chain_id: str,
    proposal_ids: list[str],
    governance_ids: list[str] = [],
    upper_limit: int = 200,
    skip: int = 0,
) -> dict[str, dict]:
    session = await client.connect_async(reconnecting=True)
    query = votes(chain_id, proposal_ids, governance_ids, upper_limit, skip)
    result = dict()

    try:
        response = await session.execute(query)
    except Exception:
        await client.close_async()
        print(chain_id, proposal_ids)
        raise
    await client.close_async()

    for proposal in response["proposals"]:
        result[proposal["id"]] = proposal

    maybe_next_page = get_governances_in_next_page(result)
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

        del next_page
        del maybe_next_page

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
