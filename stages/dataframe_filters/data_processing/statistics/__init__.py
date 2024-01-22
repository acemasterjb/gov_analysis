from typing import Any
import pandas as pd

from stages.dataframe_filters.data_processing.datatypes import ProposalsStats

from .filtering import get_filtered_proposals_for
from .reading import get_organization_df_for
from .refining import refine_data
from .writing import (
    set_changes_to_cache,
)


def get_number_of_voters_per_proposal(
    all_proposals: dict[str, pd.Series]
) -> dict[str, pd.DataFrame]:
    voters = {}

    for organization in all_proposals.keys():
        org_proposals = all_proposals[organization]
        voter_turnout: pd.Series[int] = org_proposals.groupby("proposal_id")[
            "voter"
        ].size()

        voters[organization] = voter_turnout

    return voters


def get_number_of_whales_to_all_voters_ratio(
    all_proposals: dict[str, pd.DataFrame],
    all_proposals_filtered: dict[str, pd.DataFrame],
) -> list[dict[str, int]]:
    ratios = []
    for organization in all_proposals.keys():
        org_proposals = all_proposals[organization]
        try:
            org_proposals_filtered = all_proposals_filtered[organization]
        except KeyError:
            continue
        tally = {organization: [0, 0]}

        num_of_voters = org_proposals["voter"].unique().shape[0]
        num_of_voters_filtered = org_proposals_filtered["voter"].unique().shape[0]
        tally[organization][0] = num_of_voters - num_of_voters_filtered
        tally[organization][1] = num_of_voters
        ratios.append(tally)

    return ratios


def get_differences_from_stats(
    first_row: pd.Series, proposals_stats: ProposalsStats
) -> tuple[Any]:
    if first_row.empty:
        return ()

    proposals_stats.set_whale_vp_proportion(first_row)

    if not proposals_stats:
        return ()

    return (
        first_row["proposal_id"],
        first_row["proposal_title"],
        first_row["proposal_start"],
        first_row["proposal_end"],
        proposals_stats.score_differences,
        proposals_stats.whale_vp_proportion,
        proposals_stats.total_voting_power,
        not proposals_stats.winning_choice_indexes.unfiltered
        == proposals_stats.winning_choice_indexes.filtered,
        proposals_stats.choices[proposals_stats.winning_choice_indexes.unfiltered],
        proposals_stats.choices[proposals_stats.winning_choice_indexes.filtered],
    )


def get_differences_for(
    filtered_proposal: pd.DataFrame,
    unfiltered_proposals: pd.DataFrame,
    proposal_id: str,
) -> tuple[tuple[Any], bool]:
    (first_row, proposals_stats) = refine_data(
        filtered_proposal, unfiltered_proposals, proposal_id
    )

    return get_differences_from_stats(first_row, proposals_stats)


def get_score_comparisons(
    all_proposals_filtered: dict[str, pd.DataFrame],
) -> list[dict[str, dict]]:
    differences = dict()

    for organization in all_proposals_filtered.keys():
        org_proposals_filtered = get_filtered_proposals_for(
            all_proposals_filtered, organization
        )
        unfiltered_org_proposals = get_organization_df_for(organization)

        for filtered_proposal in org_proposals_filtered.values():
            proposal_id = filtered_proposal.iloc[0]["proposal_id"]
            proposal_differences = get_differences_for(
                filtered_proposal, unfiltered_org_proposals, proposal_id
            )

            if not proposal_differences:
                continue

            differences[filtered_proposal.iloc[0]["proposal_id"]] = proposal_differences

        if differences:
            set_changes_to_cache(
                "../plutocracy_data/pickle_data/differences.pkl",
                organization,
                differences,
            )
            differences.clear()

        unfiltered_org_proposals.drop(unfiltered_org_proposals.index, inplace=True)
