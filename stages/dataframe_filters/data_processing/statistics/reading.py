import pandas as pd


def get_organization_df_for(organization: str):
    try:
        with open(
            "../plutocracy_data/pickle_data/unfiltered.parquet", "rb"
        ) as unfiltered_cache:
            return pd.read_parquet(
                unfiltered_cache,
                engine="fastparquet",
                filters=[
                    ("proposal_organization_name", "=", organization),
                ],
            )
    except FileNotFoundError:
        return pd.DataFrame()


def get_error_cache_for(
    organization: str, proposal_id: str, isFiltered: bool
) -> pd.DataFrame:
    return try_get_error_cache_for(organization, proposal_id, isFiltered)


def try_get_error_cache_for(organization: str, proposal_id: str, isFiltered: bool):
    applyFilter = organization and proposal_id
    mode = "filtered" if isFiltered else "unfiltered"

    try:
        with open(
            f"../plutocracy_data/pickle_data/errors_{mode}.parquet", "rb"
        ) as error_cache:
            return pd.read_parquet(
                error_cache,
                engine="fastparquet",
                filters=[
                    ("proposal_id", "==", proposal_id),
                    ("proposal_organization_name", "==", organization),
                ]
                if applyFilter
                else None,
            )
    except FileNotFoundError:
        return pd.DataFrame()
