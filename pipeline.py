from asyncio import run as asyncio_run

import click

from datatypes import Blacklist, DaoData, RawReports, Reports
from docs import help
from stages import (
    dataframes,
    dataframe_filters,
    export,
    merge,
    extract,
)


def get_reports(raw_reports: RawReports) -> Reports:
    return Reports(
        merge.into_single_dataframe(raw_reports.filtered),
        merge.into_single_dataframe(raw_reports.unfiltered),
    )


def get_raw_reports(api_response: DaoData) -> RawReports:
    proposal_dataframes = dataframes.all_proposals(api_response.raw_dao_data)
    raw_reports = RawReports(
        dataframe_filters.filter_top_shareholders(proposal_dataframes),
        proposal_dataframes,
    )

    return raw_reports


def extract_dao_data(
    number: int, name: str, use_tally: bool, blacklist: list[str]
) -> DaoData:
    raw_dao_data = []
    request = extract.Request(
        150, proposal_limit=150, use_tally=use_tally, blacklist=blacklist
    )
    if name == "all":
        request.max_number_of_daos = number
        raw_dao_data = asyncio_run(extract.dao_snapshot_data(request))
        export_file_name = "plutocracy_tally" if use_tally else "plutocracy"
    else:
        request.dao_name = name
        raw_dao_data = [asyncio_run(extract.dao_snapshot_data_for(request))]
        export_file_name = name + "_tally" if use_tally else name

    if raw_dao_data == [{}] or not raw_dao_data:
        click.echo("ERROR: DAO(s) not found. Aborting...")
        return DaoData("", [{}])

    return DaoData(export_file_name, raw_dao_data)


@click.command()
@click.option(
    "-n",
    "--number",
    default=60,
    show_default=True,
    type=click.IntRange(1, 60),
    help=help["number"],
)
@click.option(
    "-d",
    "--dao_name",
    "name",
    default="all",
    help=help["dao_name"],
)
@click.option("-t", "--use_tally", default=False, is_flag=True, help=help["use_tally"])
@click.option(
    "-b",
    "--blacklist",
    type=Blacklist(),
    help=help["blacklist"],
)
def run(number: int, name: str, use_tally: bool, blacklist: list[str]):
    if not blacklist:
        blacklist = []
    api_response = extract_dao_data(number, name, use_tally, blacklist)
    if not api_response:
        return

    raw_reports = get_raw_reports(api_response)
    reports = get_reports(raw_reports)

    export.organization_dataframes_to_csv(
        reports.unfiltered,
        f"./plutocracy_data/full_report/{api_response.file_name}_report.csv",
    )
    export.organization_dataframes_to_csv(
        reports.filtered,
        f"./plutocracy_data/full_report/{api_response.file_name}_report_filtered.csv",
    )
