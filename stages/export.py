import pandas as pd


def organization_dataframes_to_csv(
    organization_dataframes: pd.DataFrame, file_name: str, update: bool = False
):
    print("Generating csv...")
    organization_dataframes.to_csv(
        file_name + ".gzip",
        chunksize=50,
        compression="gzip",
        mode="a" if update else "w",
    )
    print("Done")
