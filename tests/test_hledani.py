import pytest

from store_bot.hledani import hledej
from store_bot.text import vzdalenost


def kody(nalez):
    return [m.kod for m in nalez.modely]


@pytest.mark.parametrize("dotaz", [
    "holinky",            # bez diakritiky
    "HOLÍNKY",            # verzálky
    "holínek",            # jiný pád
    "holinkz",            # překlep
    "talmo",              # jméno modelu
    "up140", "UP-140",    # kód s pomlčkou i bez
])
def test_tolerantni_hledani(sklad, dotaz):
    assert kody(hledej(sklad, dotaz)) == ["UP-140"]


def test_preklep_v_modelu_a_presna_rada(sklad):
    assert kody(hledej(sklad, "zandrk s3")) == ["UP-120"]


def test_sklonovani_a_preklep(sklad):
    assert kody(hledej(sklad, "zimnni bundu")) == ["UB-320"]


def test_vic_modelu_razeno_podle_skladu(sklad):
    nalez = hledej(sklad, "pracovni boty")
    assert set(kody(nalez)) == {"UP-110", "UP-120", "UP-130", "UP-140"}
    ks = [m.ks for m in nalez.modely]
    assert ks == sorted(ks, reverse=True)


def test_vsechna_slova_musi_sedet(sklad):
    assert kody(hledej(sklad, "zimni bunda")) == ["UB-320"]


def test_ean_vrati_kartu_s_velikosti(sklad):
    nalez = hledej(sklad, "2001400430006")
    assert kody(nalez) == ["UP-140"]
    assert nalez.karta.velikost == "43"


@pytest.mark.parametrize("dotaz", ["", "elektrická kytara", "2009999999999", "xy"])
def test_nic(sklad, dotaz):
    assert hledej(sklad, dotaz).modely == []


def test_vzdalenost():
    assert vzdalenost("zandrik", "zandrik") == 0
    assert vzdalenost("zandrk", "zandrik") == 1
    assert vzdalenost("zandrik", "zadnrik") == 1   # prohozená písmena
    assert vzdalenost("bunda", "bundu") == 1
