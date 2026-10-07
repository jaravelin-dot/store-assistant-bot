"""Ukázkový sklad a objednávky z JSONu (vše vymyšlené).

V reálném nasazení stojí na místě JSONu ranní kopie skladu z pokladního
systému (POS) a objednávky z e-shopu; zbytek bota se nemění.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

DATA = Path(__file__).parent / "data"
PORADI_PISMEN = ["UNI", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"]


@dataclass
class Karta:
    velikost: str
    ean: str
    ks: int


@dataclass
class Model:
    kod: str
    nazev: str
    kategorie: str
    cena_s_dph: int
    klicova_slova: list[str]
    karty: list[Karta]
    dph_procent: int = 21

    @property
    def ks(self) -> int:
        return sum(max(k.ks, 0) for k in self.karty)

    @property
    def cena_bez_dph(self) -> Decimal:
        return (Decimal(self.cena_s_dph) * 100 / (100 + self.dph_procent)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)

    def karta(self, velikost: str) -> Karta | None:
        v = velikost.upper()
        return next((k for k in self.karty if k.velikost.upper() == v), None)

    @property
    def rozsah_velikosti(self) -> str:
        if len(self.karty) == 1:
            return self.karty[0].velikost
        return f"{self.karty[0].velikost}–{self.karty[-1].velikost}"


def poradi_velikosti(velikost: str) -> tuple:
    v = velikost.upper()
    if v in PORADI_PISMEN:
        return (1, PORADI_PISMEN.index(v))
    cislo = "".join(c for c in v.split("-")[0] if c.isdigit())
    return (0, int(cislo)) if cislo else (2, 0)


@dataclass
class Polozka:
    ean: str
    ks: int


@dataclass
class Objednavka:
    cislo: str
    stav: str
    doprava: str
    platba: str
    polozky: list[Polozka] = field(default_factory=list)


class Sklad:
    def __init__(self, modely: list[Model], prodejna: str = "Ukázková prodejna"):
        self.modely, self.prodejna = modely, prodejna
        self._podle_eanu = {k.ean: (m, k) for m in modely for k in m.karty}

    @classmethod
    def nacti(cls, cesta: Path = DATA / "sklad.json") -> "Sklad":
        data = json.loads(Path(cesta).read_text(encoding="utf-8"))
        dph = int(data.get("dph_procent", 21))
        modely = []
        for m in data["modely"]:
            karty = sorted((Karta(str(k["velikost"]), str(k["ean"]), int(k["ks"]))
                            for k in m["karty"]), key=lambda k: poradi_velikosti(k.velikost))
            modely.append(Model(m["kod"], m["nazev"], m["kategorie"], int(m["cena_s_dph"]),
                                list(m.get("klicova_slova", [])), karty, dph))
        return cls(modely, data.get("prodejna", "Ukázková prodejna"))

    def podle_eanu(self, ean: str) -> tuple[Model, Karta] | None:
        return self._podle_eanu.get(ean.strip())


def nacti_objednavky(cesta: Path = DATA / "objednavky.json") -> dict[str, Objednavka]:
    data = json.loads(Path(cesta).read_text(encoding="utf-8"))
    return {o["cislo"]: Objednavka(o["cislo"], o["stav"], o["doprava"], o["platba"],
                                   [Polozka(p["ean"], int(p["ks"])) for p in o["polozky"]])
            for o in data["objednavky"]}
