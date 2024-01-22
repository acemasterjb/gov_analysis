from asyncio import run as asyncio_run

import click

from datatypes import Blacklist, DaoData, RawReports, Reports, RawReport, Report
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

    raw_reports = RawReport(
        dataframe_filters.filter_top_shareholders(proposal_dataframes),
        proposal_dataframes,
    )

    return raw_reports


def get_raw_report(api_response: DaoData) -> RawReport:
    proposal_dataframes = dataframes.proposals_from(
        api_response.file_name, api_response.raw_dao_data
    )

    raw_report = RawReport(
        dataframe_filters.filter_top_shareholders_for(proposal_dataframes),
        proposal_dataframes,
    )

    return raw_report


def get_report(raw_report: RawReport) -> Report:
    return Report(
        merge.into_single_dataframe(raw_report.filtered),
        merge.into_single_dataframe(raw_report.unfiltered),
    )


async def extract_dao_data(request: extract.Request) -> DaoData:
    default = DaoData("", [{}])

    raw_daos: list[dict] = extract.get_raw_dao_list(request.limit)

    for index, raw_dao in enumerate(raw_daos):
        single_raw_dao_data = DaoData(
            raw_dao["daoName"],
            await extract.get_single_dao_snapshot(raw_dao, request.proposal_limit),
        )
        yield default if single_raw_dao_data == [
            {}
        ] or not single_raw_dao_data else single_raw_dao_data

        if (index + 1) == request.max_number_of_daos:
            break


async def run(request: extract.Request):
    async for api_response in extract_dao_data(request):
        if not api_response:
            continue

        raw_report = get_raw_report(api_response)
        report = get_report(raw_report)

        export.organization_dataframes_to_csv(
            report.unfiltered,
            # ToDo: make report name dynamic
            "./plutocracy_data/full_report/plutocracy_report.csv",
            True,
        )
        export.organization_dataframes_to_csv(
            report.filtered,
            # ToDo: make report name dynamic
            "./plutocracy_data/full_report/plutocracy_report_filtered.csv",
            True,
        )


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
def entrypoint(number: int, name: str, use_tally: bool, blacklist: list[str]):
    if not blacklist:
        blacklist = []

    raw_daos: list[dict] = extract.get_raw_dao_list(number)
    whitelisted_raw_daos = [
        raw_dao for raw_dao in raw_daos if raw_dao["daoName"] not in blacklist
    ]

    request = extract.Request(
        150,
        proposal_limit=150,
        whitelisted_raw_daos=whitelisted_raw_daos,
        max_number_of_daos=number,
    )

    asyncio_run(run(request))
