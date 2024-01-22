import pandas as pd

from ..datatypes import ProposalsStats, WinningChoiceIndexes


def refine_data(
    filtered_proposal_df: pd.DataFrame,
    unfiltered_proposal_df: pd.DataFrame,
    proposal_id: int,
) -> tuple[pd.Series, ProposalsStats]:
    first_row = get_unfiltered_first_row_for(unfiltered_proposal_df, proposal_id)

    return (
        (first_row, get_proposals_stats(first_row, filtered_proposal_df))
        if not first_row.empty
        else (first_row, ProposalsStats())
    )


def get_unfiltered_first_row_for(
    unfiltered_proposal_df: pd.DataFrame,
    proposal_id: int,
) -> pd.Series:
    unfiltered_proposal_df: pd.DataFrame = unfiltered_proposal_df[
        unfiltered_proposal_df["proposal_id"] == proposal_id
    ]

    return (
        unfiltered_proposal_df.iloc[0].copy(deep=True)
        if not unfiltered_proposal_df.empty
        else pd.Series()
    )


def get_proposals_stats(
    first_row: pd.Series, filtered_proposal_df: pd.DataFrame
) -> ProposalsStats:
    try:
        proposal_scores: list[float] = eval(first_row["proposal_scores"])
    except NameError:
        return ProposalsStats()

    proposal_scores_filtered = eval(filtered_proposal_df.iloc[0]["proposal_scores"])

    winning_choice_indexes = get_winning_choice_indexes(
        proposal_scores, proposal_scores_filtered
    )

    choices = eval(first_row["proposal_choices"])

    score_differences = get_score_differences(proposal_scores, proposal_scores_filtered)

    return ProposalsStats(
        winning_choice_indexes,
        choices,
        score_differences,
    )


def get_winning_choice_indexes(
    proposal_scores: list, proposal_scores_filtered: list
) -> WinningChoiceIndexes:
    unfiltered_winning_choice_index = proposal_scores.index(max(proposal_scores))
    filtered_winning_choice_index = proposal_scores_filtered.index(
        max(proposal_scores_filtered)
    )

    return WinningChoiceIndexes(
        unfiltered_winning_choice_index, filtered_winning_choice_index
    )


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
