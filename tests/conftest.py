import pytest

from store_bot.bot import Asistent
from store_bot.sklad import Sklad, nacti_objednavky
from store_bot.tisk import SimulovanaTiskarna


@pytest.fixture
def sklad():
    return Sklad.nacti()


@pytest.fixture
def objednavky():
    return nacti_objednavky()


@pytest.fixture
def asistent(sklad, objednavky, tmp_path):
    return Asistent(sklad, objednavky, SimulovanaTiskarna(tmp_path), tmp_path)
