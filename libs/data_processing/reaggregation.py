import pandas as pd


def get_whales(unfiltered_propsal: pd.DataFrame, top_shareholders: pd.Series) -> pd.DataFrame:
    return unfiltered_propsal.loc[
        lambda df: [voter in top_shareholders.values for voter in df["voter"]]
    ]


def reaggregate_votes_single_choice_or_basic(
    unfiltered_propsal: pd.DataFrame, top_shareholders: pd.Series
) -> pd.DataFrame | None:
    whales: pd.DataFrame = get_whales(unfiltered_propsal, top_shareholders)
    if whales.empty:
        return whales
    for _, whale in whales.iterrows():
        scores: list[float | int] = unfiltered_propsal["proposal_scores"].iloc[0]
        scores[whale["choice"] - 1] -= whale["vp"]
        unfiltered_propsal["proposal_scores"] = [scores] * unfiltered_propsal.shape[0]

    return unfiltered_propsal


def reaggregate_votes_approval(
    unfiltered_propsal: pd.DataFrame, top_shareholders: pd.Series
):
    whales: pd.DataFrame = get_whales(unfiltered_propsal, top_shareholders)
    if whales.empty:
        return whales
    for _, whale in whales.iterrows():
        scores: list[float | int] = unfiltered_propsal["proposal_scores"].iloc[0]
        new_scores = [score - whale["vp"] for score in scores]
        n_rows = unfiltered_propsal.shape[0]
        unfiltered_propsal["proposal_scores"] = [new_scores] * n_rows

    return unfiltered_propsal


def reaggregate_votes_weighted(
    unfiltered_propsal: pd.DataFrame, top_shareholders: pd.Series
):
    whales: pd.DataFrame = get_whales(unfiltered_propsal, top_shareholders)
    if whales.empty:
        return whales
    for _, whale in whales.iterrows():
        scores: list[int | float] = unfiltered_propsal["proposal_scores"].iloc[0]
        weights: list[int | float] = whale["choice"].values()
        weight_total = sum(weights)
        weight_values: list[float] = [
            (weight / weight_total) * whale["vp"] for weight in weights
        ]
        new_scores = [score - weight for score, weight in zip(scores, weight_values)]
        n_rows = unfiltered_propsal.shape[0]
        unfiltered_propsal["proposal_scores"] = [new_scores] * n_rows

    return unfiltered_propsal
