import pytest

from store_bot.rozpoznani import rozpoznej


@pytest.mark.parametrize("text, druh, hledane, velikost", [
    ("Máte pracovní boty vel. 43?", "sklad", "pracovni boty", "43"),
    ("mate pracovni boty velikost 43", "sklad", "pracovni boty", "43"),
    ("zandrk s3 43", "sklad", "zandrk s3", "43"),
    ("Lehká bunda XL", "sklad", "lehka bunda", "XL"),
    ("tricko zeto l", "sklad", "tricko zeto", "L"),
    ("rukavice vel 10", "sklad", "rukavice", "10"),
    ("kalhoty do pasu", "sklad", "kalhoty pasu", None),
    ("bunda s límcem", "sklad", "bunda limcem", None),
    ("UP-120", "sklad", "up-120", None),
    ("2001400430006", "sklad", "2001400430006", None),
    ("Kolik stojí lehká bunda?", "cena", "lehka bunda", None),
    ("cena holínky", "cena", "holinky", None),
    ("za kolik je zimní bunda", "cena", "zimni bunda", None),
])
def test_sklad_a_cena(text, druh, hledane, velikost):
    z = rozpoznej(text)
    assert (z.druh, z.hledane, z.velikost) == (druh, hledane, velikost)


@pytest.mark.parametrize("text, cislo", [
    ("objednávka 1042", "1042"),
    ("Jak je na tom objednávka č. 1043?", "1043"),
    ("stav objednávky #1044", "1044"),
    ("1045", "1045"),
])
def test_objednavka(text, cislo):
    z = rozpoznej(text)
    assert (z.druh, z.cislo) == ("objednavka", cislo)


@pytest.mark.parametrize("text, hledane, kopie", [
    ("Cenovka na ZANDRIK S3, 2 kusy", "zandrik s3", 2),
    ("cenovka UP-120 3x", "up-120", 3),
    ("vytiskni cenovku na holínky", "holinky", 1),
    ("cedulka zimní bunda 2 ks", "zimni bunda", 2),
    ("cenovky vesta QUORTA ×4", "vesta quorta", 4),
])
def test_cenovka(text, hledane, kopie):
    z = rozpoznej(text)
    assert (z.druh, z.hledane, z.kopie) == ("cenovka", hledane, kopie)


@pytest.mark.parametrize("text", ["", "/start", "/help", "pomoc", "Ahoj", "?"])
def test_napoveda(text):
    assert rozpoznej(text).druh == "napoveda"
