"""Tisk cenovek. Ukázka tiskne „naoko“ — úlohu zapíše do out/tisk.log.

Skutečná tiskárna (v reálném nasazení tisk přes SumatraPDF s kontrolou
v logu tiskové služby Windows) má stejné rozhraní `vytiskni(pdf, kopie)`.
Tisk se nikdy sám neopakuje: papír zpátky nevrátíš.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class VysledekTisku:
    vytisteno: int
    chyba: str | None = None

    @property
    def ok(self) -> bool:
        return self.chyba is None


class SimulovanaTiskarna:
    def __init__(self, slozka: Path, ted=datetime.now):
        self.log = Path(slozka) / "tisk.log"
        self._ted = ted

    @property
    def nazev(self) -> str:
        return f"simulovaný tisk, záznam v {self.log.parent.name}/{self.log.name}"

    def vytiskni(self, pdf: Path, kopie: int) -> VysledekTisku:
        pdf = Path(pdf)
        if kopie < 1:
            return VysledekTisku(0, "Počet kopií musí být aspoň 1.")
        if not pdf.exists():
            return VysledekTisku(0, f"Soubor {pdf.name} neexistuje.")
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("a", encoding="utf-8") as f:
            f.write(f"{self._ted():%Y-%m-%d %H:%M:%S}\t{pdf.name}\t{kopie}x\n")
        return VysledekTisku(kopie)
