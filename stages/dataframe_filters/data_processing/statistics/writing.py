import pickle

import fastparquet
import pandas as pd
from pathlib import Path


def to_parquet(input_filename: str):
    with pd.read_csv(
        input_filename, engine="c", chunksize=100_000, compression="gzip"
    ) as csv_reader:
        for chunk in csv_reader:
            to_parquet_from_chunk(chunk)


def to_parquet_from_chunk(unfiltered_proposal_df_chunk: pd.DataFrame):
    unfiltered_proposal_df_chunk = clean_df_chunk(unfiltered_proposal_df_chunk)

    parquet_path = Path("../plutocracy_data/pickle_data/unfiltered.parquet")
    if parquet_path.exists():
        fastparquet.write(
            parquet_path,
            unfiltered_proposal_df_chunk,
            append=True,
            object_encoding="utf8",
        )
    else:
        fastparquet.write(
            parquet_path,
            unfiltered_proposal_df_chunk,
            object_encoding="utf8",
        )


def clean_df_chunk(unfiltered_proposal_df_chunk: pd.DataFrame) -> pd.DataFrame:
    unfiltered_proposal_df_chunk = remove_dirty_row(unfiltered_proposal_df_chunk)

    return unfiltered_proposal_df_chunk.astype(
        {
            "Voter Address": "str",
            "id": "str",
            "voter": "str",
            "choice": "str",
            "created": "int64",
            "vp": "float64",
            "proposal_id": "str",
            "proposal_title": "str",
            "proposal_created": "int64",
            "proposal_start": "int64",
            "proposal_end": "int64",
            "proposal_scores_total": "float64",
            "proposal_state": "object",
            "proposal_organization_name": "str",
            "proposal_type": "str",
            "proposal_scores": "str",
            "proposal_choices": "str",
            "organization_id": "str",
            "proposal_organization_id": "str",
        }
    )


def remove_dirty_row(unfiltered_proposal_df_chunk: pd.DataFrame) -> pd.DataFrame:
    return unfiltered_proposal_df_chunk.drop(
        unfiltered_proposal_df_chunk[
            unfiltered_proposal_df_chunk["created"] == "created"
        ].index
    )


def set_error_cache_for(orphaned_proposals: pd.DataFrame, isFiltered: bool):
    mode = "filtered" if isFiltered else "unfiltered"
    with open(
        f"../plutocracy_data/pickle_data/errors_{mode}.parquet", "ab+"
    ) as error_cache:
        orphaned_proposals.to_parquet(error_cache, engine="fastparquet", append=True)


def set_changes_to_cache(
    cachename: str, organization_name: str, cache_data: dict[str, tuple]
):
    pre_pickled_data = {organization_name: dict()}
    try:
        with open(cachename, "rb") as pickled_differences:
            pre_pickled_data.update(pickle.load(pickled_differences))
    except FileNotFoundError:
        pass

    with open(cachename, "wb") as pickled_differences:
        pre_pickled_data[organization_name].update(cache_data)
        pickle.dump(
            pre_pickled_data,
            pickled_differences,
        )
