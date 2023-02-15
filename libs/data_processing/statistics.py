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

        num_of_voters = all_proposals["voter"].unique().shape[0]
        num_of_voters_filtered = (
            all_proposals_filtered["Voter Address"].unique().shape[0]
        )
        tally[organization][0] = num_of_voters - num_of_voters_filtered
        tally[organization][1] = num_of_voters
        tally[organization][2] = all_proposals_filtered["vp"].mean()
        tally[organization][3] = all_proposals.loc[
            lambda df: [
                voter in top_shareholders_addresses.values for voter in df["voter"]
            ]
        ]["vp"].mean()
        tally[organization][4] = all_proposals["cost_per_vote"].mean()
        ratios.append(tally)

    return ratios


def get_all_proposals(
    dao_proposals: dict[str, pd.DataFrame],
    dao_proposals_filtered: dict[str, pd.DataFrame],
    organization: str,
) -> tuple[list, list] | None:
    all_proposals = [
        proposal.sort_index()
        for _, proposal in dao_proposals[organization].groupby(
            "proposal_id", sort=False
        )
    ]
    try:
        all_proposals_filtered = [
            proposal.sort_index()
            for _, proposal in dao_proposals_filtered[organization].groupby(
                "proposal_id", sort=False
            )
        ]
    except KeyError:
        return None
    return all_proposals, all_proposals_filtered


def get_winning_choice_indexes(
    proposal_scores: list, proposal_scores_filtered: list
) -> tuple[int, int]:
    unfiltered_winning_choice_index = proposal_scores.index(max(proposal_scores))
    filtered_winning_choice_index = proposal_scores_filtered.index(
        max(proposal_scores_filtered)
    )

    return unfiltered_winning_choice_index, filtered_winning_choice_index


def get_score_differences(
    proposal_scores: list, proposal_scores_filtered: list
) -> list:
    return [
        score - score_filtered
        for score, score_filtered in zip(
            proposal_scores,
            proposal_scores_filtered,
        )
    ]


def get_score_comparisons(
    dao_proposals: dict[str, pd.DataFrame],
    dao_proposals_filtered: dict[str, pd.DataFrame],
) -> list[dict[str, dict]]:
    differences: list[dict[str, dict]] = []
    for organization in dao_proposals.keys():
        differences.append({organization: dict()})
        organization_proposals = differences[-1][organization]
        maybe_proposals = get_all_proposals(
            dao_proposals, dao_proposals_filtered, organization
        )
        if not maybe_proposals:
            continue
        all_proposals, all_proposals_filtered = maybe_proposals

        for proposal, proposal_filtered in zip(all_proposals, all_proposals_filtered):
            first_row = proposal.iloc[0]
            proposal_scores = eval(first_row["proposal_scores"])
            proposal_scores_filtered = eval(
                proposal_filtered.iloc[0]["proposal_scores"]
            )

            (
                unfiltered_winning_choice_index,
                filtered_winning_choice_index,
            ) = get_winning_choice_indexes(proposal_scores, proposal_scores_filtered)

            proposal_type = first_row["proposal_type"]
            choices = first_row["proposal_choices"]
            score_differences = get_score_differences(
                proposal_scores, proposal_scores_filtered
            )
            total_voting_power = first_row["proposal_scores_total"]

            try:
                organization_proposals[first_row["proposal_id"]] = [
                    proposal_type,
                    choices,
                    score_differences,
                    total_voting_power,
                    not unfiltered_winning_choice_index == filtered_winning_choice_index,
                    eval(choices)[filtered_winning_choice_index]
                ]
            except IndexError:
                continue
    return differences
