from typing import Callable

import pandas as pd


payload = dict[str, pd.DataFrame]


def to_organization_map(
    filtered_input_filename: str,
    applied_function: Callable[[payload, payload], None],
) -> tuple[payload, payload]:
    filtered_output: payload = dict()

    with pd.read_csv(
        filtered_input_filename, engine="c", chunksize=10_000, compression="gzip"
    ) as filtered_csv_reader:
        for filtered_chunk in filtered_csv_reader:
            if filtered_chunk.empty:
                continue

            filtered_output.update(
                {
                    space_name: pd.concat(
                        [
                            filtered_output.get(space_name, pd.DataFrame()),
                            space_proposals,
                        ]
                    )
                    for space_name, space_proposals in filtered_chunk.groupby(
                        "proposal_organization_name",
                    )
                }
            )

            applied_function(filtered_output)
            filtered_output.clear()
