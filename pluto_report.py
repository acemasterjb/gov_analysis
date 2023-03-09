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

filtered_all_organizations_dataframe = merge.into_single_dataframe(filtered_proposal_dataframes)
all_organizations_dataframe = merge.into_single_dataframe(proposal_dataframes)

export.organization_dataframes_to_csv(
    all_organizations_dataframe, "./plutocracy_data/full_report/plutocracy_report.csv"
)
export.organization_dataframes_to_csv(
    filtered_all_organizations_dataframe, "./plutocracy_data/full_report/plutocracy_report_filtered.csv"
)
