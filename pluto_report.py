from asyncio import run as asyncio_run

from stages import (
    dataframes,
    dataframe_filters,
    export,
    merge,
    raw,
)

raw_dao_data = asyncio_run(raw.dao_snapshot_data(85, 60, 100))

proposal_dataframes = dataframes.all_proposals(raw_dao_data)
filtered_proposal_dataframes = dataframe_filters.filter_top_shareholders(
    proposal_dataframes
)

organization_dataframes = merge.organization_dataframes(filtered_proposal_dataframes)

export.organization_dataframes_to_xls(
    merge.organization_dataframes(proposal_dataframes), "./plutocracy_data/full_report/plutocracy_report.xlsx"
)
export.organization_dataframes_to_xls(
    organization_dataframes, "./plutocracy_data/full_report/plutocracy_report_filtered.xlsx"
)
