from typing import Any

from eth_utils import to_checksum_address

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
    raw_dao_id = raw_dao.get("organizationId")
    raw_dao_data = get_raw_dao_data(raw_dao_id)
    dao_snapshot_id = get_snapshot_id(raw_dao_data)

    return {
        "id": raw_dao_id,
        "snapshot_id": dao_snapshot_id,
    }


async def get_single_dao_snapshot(
    raw_dao: dict, proposal_limit: int = None
) -> dict[str, dict] | None:
    print(f"Getting raw snapshot data for {raw_dao['daoName']}")
    dao_metadata = await get_dao_metadata(raw_dao)
    _, dao_snapshot_id = dao_metadata.values()
    if not dao_snapshot_id:
        return None

    raw_dao_proposals: list[dict] = (
        await get_snapshot_proposals(dao_snapshot_id, proposal_limit)
    )["proposals"]
    print("\tDone getting proposals")
    if not raw_dao_proposals:
        return None
    dao_proposals: dict[str, dict] = dict()

    for proposal in raw_dao_proposals:
        payload = await get_snapshot_payload(proposal, dao_metadata)
        if payload:
            dao_proposals.update(payload)
    return dao_proposals


async def sanitize_tally_proposals(
    proposals: list[dict], governance_metadata: dict[str, str] | None
) -> dict[str, dict] | None:
    if not governance_metadata:
        return None
    dao_tally_id, _, _ = governance_metadata.values()
    if not dao_tally_id:
        return None

    dao_proposals: dict[str, dict] = dict()

    for proposal in proposals:
        payload = await get_tally_proposal_payload(proposal, governance_metadata)
        if payload:
            dao_proposals.update(payload)
    return dao_proposals


async def get_tally_organizations(raw_daos: list[dict]) -> list[dict[str, str]]:
    organization_names = []
    [organization_names.extend(raw_dao["daoName"].split(" ")) for raw_dao in raw_daos]

    return (await get_organizations(organization_names))["organizations"]


async def get_all_daos_tally(raw_daos: list[dict]) -> dict[str, dict] | None:
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
                except Exception:
                    continue

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
            return None
        print(
            f"number of votes in {governance['organization']['name']}: {sum([len(proposal['votes']) for proposal in votes.values()])}"
        )
        for proposal in proposals:
            proposal["votes"] = votes[proposal["id"]]["votes"].copy()
        del votes

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
) -> dict[str, dict] | list[dict] | None:
    if from_onchain:
        assert type(raw_dao) == list, "`raw_dao` needs to be a list for tally"
        return await get_all_daos_tally(raw_dao)
    else:
        return await get_single_dao_snapshot(raw_dao, proposal_limit)


async def dao_snapshot_data(request: Request) -> list[dict]:
    raw_daos: list[dict] = get_raw_dao_list(request.limit)
    daos = []

    dao_counter = 0
    i = 0

    while dao_counter < request.max_number_of_daos and i < len(raw_daos):
        if request.use_tally:
            daos: list[dict] = await select_dimension(
                [
                    raw_dao
                    for raw_dao in raw_daos
                    if raw_dao["daoName"] not in request.blacklist
                ][: request.max_number_of_daos],
                request.proposal_limit,
                request.use_tally,
            )
            break
        if raw_daos[i]["daoName"] not in request.blacklist:
            dao = await select_dimension(
                raw_daos[i], request.proposal_limit, request.use_tally
            )
            if dao:
                daos.append(dao)
                dao_counter += 1
        i += 1

    return daos


async def dao_snapshot_data_for(request: Request) -> dict[str, dict]:
    raw_daos = get_raw_dao_list(request.limit)
    raw_dao = find_dao(request.dao_name, raw_daos)

    if not raw_dao:
        return {}

    return await get_single_dao_snapshot(raw_dao, request.proposal_limit)
