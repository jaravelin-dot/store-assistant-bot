"""Co zákazník nebo prodavač chce — z obyčejné české věty, bez AI.

„Máte pracovní boty vel. 43?“        → sklad, hledá „pracovni boty“, velikost 43
„Kolik stojí lehká bunda?“           → cena
„objednávka 1042“                    → stav objednávky
„Cenovka na ZANDRIK S3, 2 kusy“       → cenovka do PDF a tisk 2×
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .text import norm

MAX_KOPII = 5

NAPOVEDA_SLOVA = {"", "/start", "/help", "help", "pomoc", "napoveda", "?", "ahoj", "dobry den"}
CENOVKA = re.compile(r"\b(?:cenovk|cedul|stitk|stitek|etiket)\w*")
KOPIE = re.compile(r"(?<![\w-])(?:(\d{1,2})\s*(?:x|×|ks|kus\w*|kopi\w*)|(?:x|×)\s*(\d{1,2}))(?=\W|$)")
OBJEDNAVKA = re.compile(r"\bobjednav\w*\s*(?:c\.?|cislo)?\s*#?\s*(\d{3,6})\b")
JEN_CISLO_OBJEDNAVKY = re.compile(r"#?\s*(\d{4})")
CENA = re.compile(r"\b(?:cen[auyo]|stoji|stoj|za kolik)\b")
EAN = re.compile(r"\d{8,14}")
VELIKOST_PO_SLOVU = re.compile(
    r"(?<![\w-])(?:velikost[iy]?|vel|cislo|c)\s*\.?\s*(\d{1,2}(?:-\d{2})?|xs|s|m|l|xl|xxl|[2-5]xl|uni)\b")
PISMENA = {"xs", "s", "m", "l", "xl", "xxl", "2xl", "3xl", "4xl", "5xl"}
JEDNOZNACNA_PISMENA = {"xl", "xxl", "2xl", "3xl", "4xl", "5xl"}

STOP = set("""
mate mame mas mate-li je jsou jeste skladem sklade sklad na nejake nejakou nejaky nejaka
nejakych prosim kolik ks kusu kusy kus kusech pro a i to ten ta tu mi me nam vam dobry den
ahoj zdravim hledam potrebuju potreboval potrebovala bych chci chtel chtela jake jaky jaka
jakou model modelu modely z ze se o s do v ve k od tam tady ted dnes taky take jestli jak
velikost velikosti vel cislo c kdyz uz porad prosimvas diky dekuji vytiskni vytisknout tisk
udelej udelat
""".split())


@dataclass
class Zamer:
    druh: str                  # napoveda | sklad | cena | objednavka | cenovka
    hledane: str = ""          # slova k hledání, bez diakritiky a výplňových slov
    velikost: str | None = None
    kopie: int = 1
    cislo: str | None = None   # číslo objednávky


def _vyjmi(text: str, m: re.Match) -> str:
    return text[:m.start()] + " " + text[m.end():]


def _velikost(text: str) -> tuple[str | None, str]:
    m = VELIKOST_PO_SLOVU.search(text)
    if m:
        return m.group(1).upper(), _vyjmi(text, m)
    tokeny = text.split()
    for i, t in enumerate(tokeny):
        posledni = i == len(tokeny) - 1
        cislo = t.isdigit() and len(t) == 2 and 34 <= int(t) <= 64
        if cislo or t in JEDNOZNACNA_PISMENA or (posledni and t in PISMENA and i > 0):
            return t.upper(), " ".join(tokeny[:i] + tokeny[i + 1:])
    return None, text


def _hledane(text: str) -> str:
    slova = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text)
    return " ".join(s for s in slova if s not in STOP)


def rozpoznej(text: str) -> Zamer:
    n = " ".join(norm(text).replace("?", " ").replace(",", " ").split())
    if n in NAPOVEDA_SLOVA:
        return Zamer("napoveda")

    if m := CENOVKA.search(n):
        zbytek, kopie = _vyjmi(n, m), 1
        if k := KOPIE.search(zbytek):
            kopie, zbytek = int(k.group(1) or k.group(2)), _vyjmi(zbytek, k)
        return Zamer("cenovka", _hledane(zbytek), kopie=kopie)

    if (m := OBJEDNAVKA.search(n)) or (m := JEN_CISLO_OBJEDNAVKY.fullmatch(n)):
        return Zamer("objednavka", cislo=m.group(1))

    if EAN.fullmatch(n):
        return Zamer("sklad", n)

    druh = "sklad"
    if m := CENA.search(n):
        druh, n = "cena", _vyjmi(n, m)
    velikost, n = _velikost(n)
    return Zamer(druh, _hledane(n), velikost)
