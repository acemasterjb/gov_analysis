import pandas as pd


def get_whales(
    unfiltered_proposal: pd.DataFrame, top_shareholders: pd.Series
) -> pd.DataFrame:
    return unfiltered_proposal.loc[
        lambda df: [voter in top_shareholders.values for voter in df["voter"]]
    ]


def reaggregate_votes_single_choice_or_basic(
    unfiltered_proposal: pd.DataFrame, top_shareholders: pd.Series
) -> pd.DataFrame | None:
    whales: pd.DataFrame = get_whales(unfiltered_proposal, top_shareholders)
    for _, whale in whales.iterrows():
        if type(whale["choice"]) is dict:
            whale["choice"] = list(whale["choice"].values())[0]

        scores: list[float | int] = unfiltered_proposal["proposal_scores"].iloc[0]
        scores[whale["choice"] - 1] -= whale["vp"]
        unfiltered_proposal["proposal_scores"] = [scores] * unfiltered_proposal.shape[0]

    return unfiltered_proposal


def reaggregate_votes_approval(
    unfiltered_proposal: pd.DataFrame, top_shareholders: pd.Series
) -> pd.DataFrame:
    whales: pd.DataFrame = get_whales(unfiltered_proposal, top_shareholders)
    for _, whale in whales.iterrows():
        scores: list[float | int] = unfiltered_proposal["proposal_scores"].iloc[0]
        new_scores = [score - whale["vp"] for score in scores]
        n_rows = unfiltered_proposal.shape[0]
        unfiltered_proposal["proposal_scores"] = [new_scores] * n_rows

    return unfiltered_proposal


def reaggregate_votes_weighted(
    unfiltered_proposal: pd.DataFrame, top_shareholders: pd.Series
) -> pd.DataFrame:
    whales: pd.DataFrame = get_whales(unfiltered_proposal, top_shareholders)
    for _, whale in whales.iterrows():
        scores: list[int | float] = unfiltered_proposal["proposal_scores"].iloc[0]
        weights: list[int | float] = whale["choice"].values()
        weight_total = sum(weights)
        weight_values: list[float] = [
            (weight / weight_total) * whale["vp"] for weight in weights
        ]
        new_scores = {
            int(whale_choice): scores[int(whale_choice) - 1] - weight
            for whale_choice, weight in zip(whale["choice"].keys(), weight_values)
        }
        for choice in new_scores.keys():
            scores[choice - 1] = new_scores[choice]
        n_rows = unfiltered_proposal.shape[0]
        unfiltered_proposal["proposal_scores"] = [scores] * n_rows

    return unfiltered_proposal
