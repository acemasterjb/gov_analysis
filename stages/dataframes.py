import pandas as pd


def get_snapshot_dataframe(dao_snapshot_vote_data: list[dict]) -> pd.DataFrame:
    index = pd.Index(
        [vote["voter"] for vote in dao_snapshot_vote_data],
        "str",
        name="Voter Address",
        tupleize_cols=False,
    )

    return pd.DataFrame(
        dao_snapshot_vote_data,
        index=index,
    )


def all_proposals(
    dao_snapshot_datas: list[dict[str, dict]],
) -> list[pd.DataFrame]:
    print("Generating DFs for dao snapshot data")
    proposal_dfs = []
    for dao in dao_snapshot_datas:
        for proposal in dao.values():
            proposal_dfs.append(get_snapshot_dataframe(proposal["votes"]))

    return proposal_dfs
