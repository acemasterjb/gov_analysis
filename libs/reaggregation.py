import pandas as pd


def reaggregate_votes_single_choice_or_basic(
    unfiltered_propsal: pd.DataFrame, top_shareholders: list[str]
) -> pd.DataFrame | None:
    whales: pd.DataFrame = unfiltered_propsal.loc[
        lambda df: [voter in top_shareholders for voter in df["voter"]]
    ]
    if whales.empty:
        return None
    for whale in whales:
        scores = unfiltered_propsal["proposal_scores"].iloc[0]
        scores[whale["choice"] - 1] -= whale["vp"]
        unfiltered_propsal["proposal_scores"] = [scores] * unfiltered_propsal.shape[0]

    return unfiltered_propsal


def reaggregate_votes_approval(
    unfiltered_propsal: pd.DataFrame, top_shareholders: list[str]
):
    whales: pd.DataFrame = unfiltered_propsal.loc[
        lambda df: [voter in top_shareholders for voter in df["voter"]]
    ]
    if whales.empty:
        return None
    for whale in whales:
        scores = unfiltered_propsal["proposal_scores"].iloc[0]
        new_scores = [score - whale["vp"] for score in scores]
        unfiltered_propsal["proposal_scores"] = [new_scores] * unfiltered_propsal.shape[
            0
        ]

    return unfiltered_propsal


def reaggregate_votes_weighted(
    unfiltered_propsal: pd.DataFrame, top_shareholders: list[str]
):
    whales: pd.DataFrame = unfiltered_propsal.loc[
        lambda df: [voter in top_shareholders for voter in df["voter"]]
    ]
    if whales.empty:
        return None
    for whale in whales:
        scores: list[int | float] = unfiltered_propsal["proposal_scores"].iloc[0]
        weights: list[int | float] = whale["choice"].values()
        weight_total = sum(weights)
        weight_values: list[float] = [
            (weight / weight_total) * whale["vp"] for weight in weights
        ]
        new_scores = [score - weight for score, weight in zip(scores, weight_values)]
        unfiltered_propsal["proposal_scores"] = [new_scores] * unfiltered_propsal.shape[
            0
        ]
