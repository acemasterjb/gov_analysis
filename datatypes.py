from dataclasses import dataclass
from json import loads

from click import ParamType
from click.core import Context, Parameter
from pandas import DataFrame


@dataclass
class DaoData:
    file_name: str
    raw_dao_data: list[dict]

    def __bool__(self) -> bool:
        return len(self.file_name) > 0 and len(self.raw_dao_data) > 0


@dataclass
class RawReports:
    filtered: list[DataFrame]
    unfiltered: list[DataFrame]


@dataclass
class Reports(RawReports):
    filtered: DataFrame
    unfiltered: DataFrame


class Blacklist(ParamType):
    def __init__(self) -> None:
        self.name = "json_list"

    def convert(
        self, value: str | list, param: Parameter | None, ctx: Context | None
    ) -> list[str]:
        if value is list:
            return value
        try:
            maybe_blacklist = loads(value)
            assert (
                type(maybe_blacklist) is list
            ), "Given `blacklist` is not a list of strings"
            assert all(
                [type(dao) is str for dao in maybe_blacklist]
            ), "DAO names must be strings"
            return maybe_blacklist
        except:
            self.fail(value, param, ctx)

    def __repr__(self) -> str:
        return "jsonList"
