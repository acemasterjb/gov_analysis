from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil import parser


def get_proposal_state(proposal: dict) -> str:
    now = datetime.now(ZoneInfo("UTC"))
    proposal_start = parser.parse(proposal["start"]["timestamp"])
    proposal_end = parser.parse(proposal["end"]["timestamp"])

    return (
        "pending"
        if proposal_start > now
        else "active"
        if now > proposal_start and now < proposal_end
        else "closed"
    )


def sanitize_vote(vote: dict, proposal: dict, dao_id: str):
    try:
        vote["vp"] = int(vote["weight"])
    except KeyError:
        return
    vote["proposal_id"] = proposal["id"]
    vote["proposal_title"] = proposal["title"]
    vote["proposal_created"] = proposal["start"]
    vote["proposal_start"] = proposal["start"]["timestamp"]
    vote["proposal_end"] = proposal["end"]["timestamp"]
    vote["proposal_scores_total"] = sum(
        [int(choice["weight"]) for choice in proposal["voteStats"]]
    )
    vote["proposal_state"] = get_proposal_state(proposal)
    vote["proposal_organization_name"] = proposal["organization_name"]
    vote["proposal_type"] = "single-choice"
    vote["proposal_scores"] = [int(stat["weight"]) for stat in proposal["voteStats"]]
    vote["proposal_choices"] = [stat["support"] for stat in proposal["voteStats"]]
    vote["proposal_organization_id"] = dao_id
    vote["created"] = vote["transaction"]["block"]["timestamp"]
    vote["choice"] = vote["proposal_choices"].index(vote["support"]) + 1
    vote["voter_ens"] = vote["voter"]["ens"]
    vote["voter"] = vote["voter"]["address"]
    del vote["weight"]
    del vote["transaction"]
    del vote["support"]


async def get_dao_metadata(governance_metadata: dict) -> dict[str, str]:
    return {
        "tally_id": governance_metadata["id"],
        "name": governance_metadata["name"],
    }


async def get_proposal_payload(
    proposal: dict, governance_metadata: dict
) -> dict | None:
    print(f"\tprocessing proposal {proposal['id']}")
    dao_tally_id, dao_name = (await get_dao_metadata(governance_metadata)).values()

    proposal_id: str = proposal["id"]
    payload = {proposal_id: dict()}

    proposal["organization_name"] = dao_name
    proposal["organization_id"] = dao_tally_id

    votes = proposal["votes"]
    if not votes:
        return None

    payload[proposal_id]["proposal"] = proposal

    for vote in votes:
        sanitize_vote(vote, proposal, dao_tally_id)

    payload[proposal_id].update({"votes": votes})
    return payload
