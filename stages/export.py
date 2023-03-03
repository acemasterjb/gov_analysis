import pandas as pd


def organization_dataframes_to_xls(
    organization_dataframes: list[pd.DataFrame], file_name: str
):
    print("Generating Spreadsheet...")
    with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
        for organization_dataframe in organization_dataframes:
            organization_name: str = organization_dataframe.iloc[0][
                "proposal_space_name"
            ]
            if "/" in organization_name:
                organization_name = organization_name.replace("/", "_")
            organization_dataframe.to_excel(writer, organization_name, "N/A")

    print("Done")

