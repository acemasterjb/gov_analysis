from ...apis.snapshot.execution import get_votes


def sanitize_vote(vote: dict, dao_id: str) -> dict:
    vote["proposal_id"] = vote["proposal"]["id"]
    vote["proposal_title"] = vote["proposal"]["title"]
    vote["proposal_created"] = vote["proposal"]["created"]
    vote["proposal_start"] = vote["proposal"]["start"]
    vote["proposal_end"] = vote["proposal"]["end"]
    vote["proposal_scores_total"] = vote["proposal"]["scores_total"]
    vote["proposal_state"] = vote["proposal"]["state"]
    vote["proposal_organization_name"] = vote["proposal"]["space"]["name"]
    vote["proposal_type"] = vote["proposal"]["type"]
    vote["proposal_scores"] = vote["proposal"]["scores"]
    vote["proposal_choices"] = vote["proposal"]["choices"]
    vote["organization_id"] = dao_id
    vote["proposal_organization_id"] = vote["proposal"]["space"]["id"]
    vote.pop("proposal")

    return vote


async def get_proposal_payload(proposal: dict, dao_metadata: dict) -> dict:
    print(f"\tprocessing proposal {proposal['id']}")
    dao_id, _ = dao_metadata.values()

    proposal_id: str = proposal["id"]
    payload = {proposal_id: dict()}

    proposal["organization_name"] = proposal["space"]["name"]
    proposal["organization_id"] = proposal["space"]["id"]
    del proposal["space"]

    response = await get_votes(proposal_id)
    votes: list[dict] = response["votes"]
    if not votes or votes[0]["proposal"]["type"] in [
        "quadratic",
        "ranked-choice",
    ]:
        return {}

    payload[proposal_id]["proposal"] = proposal

    for vote_index, vote in enumerate(votes.copy()):
        votes[vote_index] = sanitize_vote(vote, dao_id)

    payload[proposal_id].update({"votes": votes.copy()})
    return payload
