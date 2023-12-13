from dataclasses import dataclass
from typing import Any


@dataclass
class Request:
    limit: int
    whitelisted_raw_daos: list[dict[str, Any]]
    max_number_of_daos: int = 60
    dao_name: str = None
    proposal_limit: int = None
