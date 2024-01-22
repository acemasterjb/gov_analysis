import sys
from collections import namedtuple
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

MINIMUM_FLOAT = sys.float_info.min

WinningChoiceIndexes = namedtuple(
    "WinningChoiceIndexes",
    ["unfiltered", "filtered"],
    defaults=(MINIMUM_FLOAT, MINIMUM_FLOAT),
)


@dataclass
class ProposalsStats:
    winning_choice_indexes: WinningChoiceIndexes = WinningChoiceIndexes()
    choices: list[Any] = field(default_factory=list)
    score_differences: list[float] = field(default_factory=list)
    whale_vp_proportion: float = MINIMUM_FLOAT
    total_voting_power: float = MINIMUM_FLOAT

    def set_whale_vp_proportion(self, first_row: pd.Series):
        if first_row["proposal_type"] == "approval":
            whale_voting_power = self.score_differences[0]
        else:
            whale_voting_power = sum(self.score_differences)

        try:
            self.total_voting_power = float(first_row["proposal_scores_total"])
            self.whale_vp_proportion = whale_voting_power / self.total_voting_power
        except (ValueError, ZeroDivisionError):
            pass

    def __bool__(self):
        choices_empty = WinningChoiceIndexes()

        return all(
            (
                (not self.winning_choice_indexes == choices_empty),
                self.choices,
                self.score_differences,
                (not self.whale_vp_proportion == MINIMUM_FLOAT),
                (not self.total_voting_power == MINIMUM_FLOAT),
            )
        )
