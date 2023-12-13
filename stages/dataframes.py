import pandas as pd


def create_dataframe_from(dao_snapshot_vote_data: list[dict]) -> pd.DataFrame:
    verified_vote_data = [
        vote_data for vote_data in dao_snapshot_vote_data if vote_data
    ]
    index = pd.Index(
        [vote["voter"] for vote in verified_vote_data if vote],
        "str",
        name="Voter Address",
        tupleize_cols=False,
    )

    return (
        pd.DataFrame(
            verified_vote_data,
            index=index,
        )
        .astype({"vp": "float", "proposal_scores_total": "float"})
        .dropna(how="all")
        .drop_duplicates(["id"])
    )


def all_proposals(
    dao_snapshot_datas: list[dict[str, dict]],
) -> list[pd.DataFrame]:
    print("Generating DFs for dao snapshot data")
    proposal_dfs = []
    validated_dao_data = [dao for dao in dao_snapshot_datas if type(dao) is dict]
    for dao in validated_dao_data:
        for proposal in dao.values():
            proposal_dfs.append(create_dataframe_from(proposal["votes"]))

    return proposal_dfs


def proposals_from(
    dao_name: str, dao_snapshot_data: dict[str, dict]
) -> list[pd.DataFrame]:
    print(f"Generating DFs for {dao_name} snapshot data")
    proposal_dfs = []
    for proposal in dao_snapshot_data.values():
        proposal_dfs.append(create_dataframe_from(proposal["votes"]))

    return proposal_dfs
