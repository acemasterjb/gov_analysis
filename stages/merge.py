import pandas as pd


def organization_dataframes(
    filtered_proposal_dfs: list[pd.DataFrame],
) -> list[pd.DataFrame]:
    organization_map: dict[str, list[pd.DataFrame]] = dict()
    for proposal_df in filtered_proposal_dfs:
        if proposal_df.empty:
            continue
        organization_name: str = proposal_df.iloc[0]["proposal_space_name"]
        if organization_name not in organization_map.keys():
            organization_map[organization_name] = []
        organization_map[organization_name].append(proposal_df)

    organization_dfs = []
    for organization in organization_map.keys():
        organization_df = pd.concat(organization_map[organization])
        organization_dfs.append(organization_df)

    return organization_dfs
