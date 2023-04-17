from asyncio import run as asyncio_run

import click

from stages import (
    dataframes,
    dataframe_filters,
    export,
    merge,
    raw,
)

cli_help = "[Optional] Name of the DAO you'd like to run report on. Will get top 60 DAOs if not given."


@click.command()
@click.option("--dao_name", default="all", help=cli_help)
def run_pipeline(dao_name: str):
    raw_dao_data = None
    if dao_name == "all":
        raw_dao_data = asyncio_run(raw.dao_snapshot_data(85, 60, 100))
        export_file_name = "plutocracy"
    else:
        raw_dao_data = [asyncio_run(raw.dao_snapshot_data_for(dao_name, 150))]
        export_file_name = dao_name

    if raw_dao_data == [{}] or not raw_dao_data:
        print("ERROR: DAO(s) not found. Aborting...")
        return

    proposal_dataframes = dataframes.all_proposals(raw_dao_data)
    filtered_proposal_dataframes = dataframe_filters.filter_top_shareholders(
        proposal_dataframes
    )

    filtered_all_organizations_dataframe = merge.into_single_dataframe(
        filtered_proposal_dataframes
    )
    all_organizations_dataframe = merge.into_single_dataframe(proposal_dataframes)

    export.organization_dataframes_to_csv(
        all_organizations_dataframe,
        f"./plutocracy_data/full_report/{export_file_name}_report.csv",
    )
    export.organization_dataframes_to_csv(
        filtered_all_organizations_dataframe,
        f"./plutocracy_data/full_report/{export_file_name}_report_filtered.csv",
    )


if __name__ == "__main__":
    run_pipeline()
