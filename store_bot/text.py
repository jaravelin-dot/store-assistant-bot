"""Práce s textem: normalizace bez diakritiky, překlepy, formát čísel."""
from __future__ import annotations

import re
import unicodedata


def bez_diakritiky(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c))


def norm(s: str) -> str:
    """„Kotníková OBUV“ → „kotnikova obuv“."""
    return bez_diakritiky(s).lower()


def slova(s: str) -> list[str]:
    """Slova bez diakritiky, malými písmeny; pomlčka v kódu zůstává."""
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", norm(s))


def kompakt(s: str) -> str:
    """„UP-120“ → „up120“ — kód se najde i bez pomlčky."""
    return re.sub(r"[^a-z0-9]", "", norm(s))


def vzdalenost(a: str, b: str) -> int:
    """Počet překlepů mezi slovy (Damerau–Levenshtein, prohození sousedních znaků = 1)."""
    if a == b:
        return 0
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cena = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cena)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


def kc(castka: float, desetiny: bool = False) -> str:
    """1290 → „1 290 Kč“, s desetinami „1 066,12 Kč“."""
    if desetiny:
        cele = f"{castka:,.2f}".replace(",", " ").replace(".", ",")
    else:
        cele = f"{round(castka):,}".replace(",", " ")
    return f"{cele} Kč"
