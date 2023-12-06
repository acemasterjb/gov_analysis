import pytest

from stages.extract.data_processing.filters import find_dao
from stages.extract.data_processing.tests.constants import raw_dao_list


@pytest.fixture
def raw_daos() -> list[dict]:
    return raw_dao_list


@pytest.mark.parametrize("user_dao_name", ["GoodDAO", "KindaGoodDAO"])
def test_find_dao(user_dao_name, raw_daos):
    raw_dao_found = find_dao(user_dao_name, raw_daos)

    assert user_dao_name == raw_dao_found["daoName"]
