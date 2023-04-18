import pandas as pd


def get_quartile_by_vp(snapshot_df: pd.DataFrame, quartile: float) -> pd.DataFrame:
    assert quartile > 0 and quartile < 1, "Quartile must be a value in range (0, 1)"

    quartile_value = snapshot_df["vp"].quantile(quartile)
    return snapshot_df[snapshot_df["vp"] >= quartile_value]


def find_dao(dao_name: str, dao_metadata_list: list[dict[str, dict]]) -> dict | None:
    for dao_metadata in dao_metadata_list:
        if dao_name == dao_metadata["daoName"]:
            return dao_metadata
    return None
