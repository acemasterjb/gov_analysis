import pandas as pd

from .filters import get_quartile_by_vp


def get_number_of_whales_to_all_voters_ratio(
    dao_proposals: dict[str, pd.DataFrame],
    dao_proposals_filtered: dict[str, pd.DataFrame],
) -> list[dict[str, int]]:
    ratios = []
    for organization in dao_proposals.keys():
        all_proposals = dao_proposals[organization]
        try:
            all_proposals_filtered = dao_proposals_filtered[organization]
        except KeyError:
            continue
        top_shareholders_df = get_quartile_by_vp(all_proposals, 0.95)
        top_shareholders_addresses = top_shareholders_df["voter"]
        tally = {organization: [0, 0, 0, 0, 0]}

        tally[organization][0] = (
            all_proposals.shape[0] - all_proposals_filtered.shape[0]
        )
        tally[organization][1] = all_proposals.shape[0]
        tally[organization][2] = all_proposals_filtered["vp"].mean()
        tally[organization][3] = all_proposals.loc[
            lambda df: [
                voter in top_shareholders_addresses.values for voter in df["voter"]
            ]
        ]["vp"].mean()
        tally[organization][4] = all_proposals["cost_per_vote"].mean()
        ratios.append(tally)

    return ratios


def get_score_differences(
    dao_proposals: dict[str, pd.DataFrame],
    dao_proposals_filtered: dict[str, pd.DataFrame],
) -> list[dict[str, dict]]:
    diffrences: list[dict[str, dict]] = []
    for organization in dao_proposals.keys():
        diffrences.append({organization: dict()})
        organization_proposals = diffrences[-1][organization]
        all_proposals = [
            proposal
            for _, proposal in dao_proposals[organization].groupby(
                "proposal_id", sort=False
            )
        ]
        try:
            all_proposals_filtered = [
                proposal
                for _, proposal in dao_proposals_filtered[organization].groupby(
                    "proposal_id", sort=False
                )
            ]
        except KeyError:
            del diffrences[-1]
            continue

        for proposal, proposal_filtered in zip(all_proposals, all_proposals_filtered):
            proposal_id: str = proposal.iloc[0]["proposal_id"]
            organization_proposals[proposal_id] = [
                score - score_filtered
                for score, score_filtered in zip(
                    eval(proposal.iloc[0]["proposal_scores"]),
                    eval(proposal_filtered.iloc[0]["proposal_scores"]),
                )
            ]
    return diffrences
