from copy import deepcopy

import pandas as pd

from data_processing.reaggregation import (
    reaggregate_votes_approval,
    reaggregate_votes_single_choice_or_basic,
    reaggregate_votes_weighted,
)
from data_processing.filters import get_quartile_by_vp

def filter_top_shareholders_from_df(proposal_df: pd.DataFrame) -> pd.DataFrame:
    def reaggregate_votes(
        unfiltered_proposal: pd.DataFrame, top_shareholders: pd.Series
    ) -> pd.DataFrame:
        proposal_type_map = {
            "single-choice": reaggregate_votes_single_choice_or_basic,
            "basic": reaggregate_votes_single_choice_or_basic,
            "approval": reaggregate_votes_approval,
            "weighted": reaggregate_votes_weighted,
        }
        proposal_type: str = unfiltered_proposal.iloc[0]["proposal_type"]

        result: pd.DataFrame = proposal_type_map[proposal_type](
            unfiltered_proposal, top_shareholders
        )

        return result

    top_shareholders_df = get_quartile_by_vp(proposal_df, 0.95)
    top_shareholder_addresses = top_shareholders_df["voter"]
    reaggregated_proposal_df = reaggregate_votes(proposal_df, top_shareholder_addresses)
    if not reaggregated_proposal_df.empty:
        proposal_df = reaggregated_proposal_df
    return (
        proposal_df.loc[
            lambda df: [voter not in top_shareholder_addresses for voter in df["voter"]]
        ]
    ).drop(["voter", "id"], axis=1)


def filter_top_shareholders(
    proposal_dfs: list[pd.DataFrame],
) -> list[pd.DataFrame]:
    print("Filtereing out top 10 holders for each dao")
    filtered_dfs = []
    for proposal_df in proposal_dfs:
        proposal_df_copy = proposal_df.copy()
        proposal_df_copy["proposal_scores"] = deepcopy(
            proposal_df["proposal_scores"].values
        )
        filtered_dfs.append(filter_top_shareholders_from_df(proposal_df_copy))
    return filtered_dfs
