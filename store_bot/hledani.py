"""Hledání ve skladu: EAN, kód modelu, nebo slova z názvu.

Snese chybějící diakritiku („holinky“), skloňování („montérek“, „bundu“)
i překlep („zandrk“). Každé hledané slovo musí sedět na název, kategorii
nebo klíčové slovo modelu; přesná shoda vyhrává nad shodou s překlepem.
"""
from __future__ import annotations

from dataclasses import dataclass

from .sklad import Karta, Model, Sklad
from .text import kompakt, slova, vzdalenost

PRESNE, PREKLEP, NIC = 2, 1, 0


@dataclass
class Nalez:
    modely: list[Model]
    karta: Karta | None = None   # při hledání EANem konkrétní velikost


def _tokeny(m: Model) -> set[str]:
    t = set(slova(" ".join([m.nazev, m.kategorie, *m.klicova_slova])))
    t |= {cast for s in list(t) for cast in s.split("-")}
    t.add(kompakt(m.kod))
    return t


def shoda(slovo: str, tokeny: set[str]) -> int:
    if slovo in tokeny:
        return PRESNE
    if len(slovo) >= 3 and any(t.startswith(slovo) for t in tokeny):
        return PRESNE
    if len(slovo) >= 4:
        limit = 1 if len(slovo) <= 6 else 2 if len(slovo) <= 9 else 3
        for t in tokeny:
            if vzdalenost(slovo, t) <= limit:
                return PREKLEP
            if len(t) > len(slovo) and vzdalenost(slovo, t[:len(slovo)]) <= limit:
                return PREKLEP
    return NIC


def hledej(sklad: Sklad, text: str) -> Nalez:
    dotaz = (text or "").strip()
    if not dotaz:
        return Nalez([])
    if dotaz.isdigit() and (z := sklad.podle_eanu(dotaz)):
        return Nalez([z[0]], z[1])
    kod = kompakt(dotaz)
    podle_kodu = [m for m in sklad.modely if kompakt(m.kod) == kod]
    if podle_kodu:
        return Nalez(podle_kodu)

    hledana = slova(dotaz)
    vysledky = []
    for m in sklad.modely:
        tokeny = _tokeny(m)
        body = [shoda(s, tokeny) for s in hledana]
        if all(body):
            vysledky.append((sum(body), m))
    if not vysledky:
        return Nalez([])
    nejlepsi = max(b for b, _ in vysledky)
    modely = [m for b, m in vysledky if b == nejlepsi]
    modely.sort(key=lambda m: (-m.ks, m.nazev))
    return Nalez(modely)
