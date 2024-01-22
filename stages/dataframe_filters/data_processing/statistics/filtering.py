import pandas as pd


def get_filtered_proposals_for(
    dao_proposals_filtered: dict[str, pd.DataFrame],
    organization: str,
) -> dict[str, pd.DataFrame]:
    maybe_proposals = get_all_proposals(dao_proposals_filtered, organization)
    if not maybe_proposals:
        return dict()

    return maybe_proposals


def get_all_proposals(
    dao_proposals_filtered: dict[str, pd.DataFrame],
    organization: str,
) -> dict[str, pd.DataFrame]:
    try:
        all_proposals_filtered = get_proposals_for(organization, dao_proposals_filtered)
    except KeyError:
        return dict()
    return all_proposals_filtered


def get_proposals_for(
    organization: str, dao_proposals: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    return {
        proposal_df.iloc[0]["proposal_id"]: proposal_df
        for _, proposal_df in dao_proposals[organization].groupby(
            "proposal_id", sort=False
        )
    }
