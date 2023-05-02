from dataclasses import dataclass


@dataclass
class Request:
    limit: int
    max_number_of_daos: int = None
    dao_name: str = None
    proposal_limit: int = None
    use_tally: bool = False
    blacklist: list[str] = None
