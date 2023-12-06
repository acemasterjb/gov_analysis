from typing import Any, Callable

from eth_utils.address import to_checksum_address

from .apis.deepdao.adapters import (
    get_snapshot_id,
)
from .apis.deepdao.queries import (
    get_raw_dao_data,
    get_raw_dao_list,
    get_raw_token_metadata,
)
from .apis.snapshot.execution import get_proposals as get_snapshot_proposals
from .apis.tally.execution import (
    get_organizations,
    get_proposals as get_tally_proposals,
    get_votes,
)
from .datatypes import Request
from .data_processing.filters import find_dao, get_valid_organizations
from .data_processing.tally import (
    get_proposal_payload as get_tally_proposal_payload,
)
from .data_processing.snapshot import get_proposal_payload as get_snapshot_payload


async def get_dao_metadata(raw_dao: dict) -> dict[str, Any]:
    raw_dao_id: str = raw_dao.get("organizationId")
    raw_dao_data = get_raw_dao_data(raw_dao_id)
    dao_snapshot_id = get_snapshot_id(raw_dao_data)

    return {
        "id": raw_dao_id,
        "snapshot_id": dao_snapshot_id,
    }


async def get_valid_proposal_payloads(
    payload_function: Callable[[dict, dict], dict | None],
    raw_proposals: list[dict],
    dao_metadata: dict,
):
    for proposal in raw_proposals.copy():
        yield (await payload_function(proposal, dao_metadata))


async def get_single_dao_snapshot(
    raw_dao: dict, proposal_limit: int = None
) -> dict[str, dict]:
    print(f"Getting raw snapshot data for {raw_dao['daoName']}")
    dao_metadata = await get_dao_metadata(raw_dao)
    _, dao_snapshot_id = dao_metadata.values()
    if not dao_snapshot_id:
        return {}

    raw_proposals: list[dict] = (
        await get_snapshot_proposals(dao_snapshot_id, proposal_limit)
    )["proposals"]
    print("\tDone getting proposals")
    dao_proposals: dict[str, dict] = dict()

    async for maybe_payload in get_valid_proposal_payloads(
        get_snapshot_payload, raw_proposals, dao_metadata
    ):
        if maybe_payload:
            dao_proposals.update(maybe_payload.copy())
    return dao_proposals


async def sanitize_tally_proposals(
    raw_proposals: list[dict], governance_metadata: dict[str, str]
) -> dict[str, dict]:
    if not governance_metadata:
        return {}
    dao_tally_id, _, _ = governance_metadata.values()
    if not dao_tally_id:
        return {}

    dao_proposals: dict[str, dict] = dict()

    async for maybe_proposal in get_valid_proposal_payloads(
        get_tally_proposal_payload, raw_proposals, governance_metadata
    ):
        if maybe_proposal:
            dao_proposals.update(maybe_proposal)
    return dao_proposals


async def get_tally_organizations(raw_daos: list[dict]) -> list[dict[str, str]]:
    organization_names = []
    [
        organization_names.extend(raw_dao["daoName"].split(" ") + [raw_dao["daoName"]])
        for raw_dao in raw_daos
    ]

    return (await get_organizations(organization_names))["organizations"]


async def get_all_daos_tally(raw_daos: list[dict]) -> list[dict[str, dict]]:
    organizations = await get_tally_organizations(raw_daos)
    token_addresses = []
    for raw_dao in raw_daos:
        raw_dao_id = raw_dao.get("organizationId")
        maybe_token_metadata = await get_raw_token_metadata(raw_dao_id)
        if maybe_token_metadata:
            maybe_token_address = maybe_token_metadata.get("tokenAddress")
            if maybe_token_address:
                try:
                    token_addresses.append(to_checksum_address(maybe_token_address))
                except ValueError:
                    print(f"[warning] Converting {maybe_token_address} to checksum")

    organizations = get_valid_organizations(token_addresses, organizations)

    governances = await get_tally_proposals(
        [organization["id"] for organization in organizations]
    )
    governance_metadatas: list[dict] = []
    proposals_payload: list[list] = []

    for governance in governances["governances"]:
        proposals: list[dict] = governance["proposals"]
        try:
            print(f"getting votes for {governance['organization']['name']}")
            votes = await get_votes(
                governance["chainId"],
                [str(proposal["id"]) for proposal in proposals],
                [governance["id"]],
            )

        except Exception:
            print(f"issue with {governance['organization']['name']}\n\n")
            continue
        for proposal in proposals:
            proposal["votes"] = votes[proposal["id"]]["votes"].copy()

        proposals_payload.append(proposals)
        governance_metadatas.append(
            {k: v for k, v in governance.items() if type(v) is str}
        )

    return [
        await sanitize_tally_proposals(proposals, governance_metadata)
        for proposals, governance_metadata in zip(
            proposals_payload,
            governance_metadatas,
        )
    ]


async def select_dimension(
    raw_dao: dict | list[dict], proposal_limit: int = None, from_onchain: bool = False
) -> list[dict] | dict[str, dict]:
    if from_onchain:
        assert type(raw_dao) == list, "`raw_dao` needs to be a list for tally"
        return await get_all_daos_tally(raw_dao)
    else:
        return await get_single_dao_snapshot(raw_dao, proposal_limit)


async def dao_snapshot_data(request: Request) -> list[dict]:
    raw_daos: list[dict] = get_raw_dao_list(request.limit)
    whitelisted_raw_daos = [
        raw_dao for raw_dao in raw_daos if raw_dao["daoName"] not in request.blacklist
    ]
    daos: list[dict] = []
    valid_daos = 0

    if request.use_tally:
        daos = await select_dimension(
            whitelisted_raw_daos[: request.max_number_of_daos],
            request.proposal_limit,
            True,
        )
    else:
        for raw_dao in whitelisted_raw_daos:
            maybe_dao_data: dict[str, dict] = await select_dimension(
                raw_dao, request.proposal_limit, request.use_tally
            )
            if maybe_dao_data:
                daos.append(maybe_dao_data)
                valid_daos += 1
                if valid_daos == request.max_number_of_daos:
                    break

    return daos


async def dao_snapshot_data_for(request: Request) -> dict[str, dict]:
    raw_daos = get_raw_dao_list(request.limit)
    raw_dao: dict = find_dao(request.dao_name, raw_daos)

    if not raw_dao:
        return {}

    return await get_single_dao_snapshot(raw_dao, request.proposal_limit)
