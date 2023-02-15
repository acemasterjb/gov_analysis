from typing import Any

from fastapi import FastAPI
import pandas as pd


def get_winning_choice_indexes(
    proposal_scores: list, proposal_scores_filtered: list
) -> tuple[int, int]:
    unfiltered_winning_choice_index = proposal_scores.index(max(proposal_scores))
    filtered_winning_choice_index = proposal_scores_filtered.index(
        max(proposal_scores_filtered)
    )

    return unfiltered_winning_choice_index, filtered_winning_choice_index


def get_score_differences(
    proposal_scores: list, proposal_scores_filtered: list
) -> list:
    return [
        score - score_filtered
        for score, score_filtered in zip(
            proposal_scores,
            proposal_scores_filtered,
        )
    ]


def process_merged_proposal(merged_proposal: pd.DataFrame):
    first_row = merged_proposal.iloc[0]
    proposal_scores = eval(first_row["proposal_scores_x"])
    proposal_scores_filtered = eval(first_row["proposal_scores_y"])

    (
        unfiltered_winning_choice_index,
        filtered_winning_choice_index,
    ) = get_winning_choice_indexes(proposal_scores, proposal_scores_filtered)

    proposal_type = first_row["proposal_type_x"]
    choices = first_row["proposal_choices"]
    score_differences = get_score_differences(proposal_scores, proposal_scores_filtered)
    total_voting_power = first_row["proposal_scores_total_x"]
    return first_row["proposal_id"], [
        proposal_type,
        choices,
        score_differences,
        total_voting_power,
        not unfiltered_winning_choice_index == filtered_winning_choice_index,
        eval(choices)[filtered_winning_choice_index],
    ]


app = FastAPI()


@app.get("/")
def root():
    return {"status": "Success"}


@app.post("/process_dataframe")
def process_dataframe(dataframe_json: str) -> dict[str, Any]:
    df = pd.read_json(dataframe_json)

    proposal_id, paylaod = process_merged_proposal(df)

    return {"proposal_id": proposal_id, "payload": paylaod}
