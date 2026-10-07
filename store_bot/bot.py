"""Jádro asistenta: text dovnitř → odpovědi ven. O kanálu (terminál,
Telegram) nic neví, proto se celé dá otestovat bez sítě."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import odpovedi
from .cenovka import vytvor_cenovku
from .hledani import hledej
from .rozpoznani import MAX_KOPII, rozpoznej
from .sklad import Objednavka, Sklad
from .text import kc


@dataclass
class Zprava:
    text: str
    soubor: Path | None = None   # přiložené PDF (cenovka)


class Asistent:
    def __init__(self, sklad: Sklad, objednavky: dict[str, Objednavka], tiskarna,
                 slozka_cenovek: Path):
        self.sklad, self.objednavky, self.tiskarna = sklad, objednavky, tiskarna
        self.slozka_cenovek = Path(slozka_cenovek)

    def odpovez(self, text: str) -> list[Zprava]:
        z = rozpoznej(text)
        if z.druh == "napoveda":
            return [Zprava(odpovedi.NAPOVEDA)]
        if z.druh == "objednavka":
            o = self.objednavky.get(z.cislo or "")
            return [Zprava(odpovedi.objednavka(o, z.cislo or "", self.sklad))]
        puvodni = " ".join(text.replace("?", " ").split())
        if z.druh == "cenovka":
            return self._cenovka(z.hledane, z.kopie, puvodni)
        if not z.hledane:
            return [Zprava(odpovedi.nic(""))]
        nalez = hledej(self.sklad, z.hledane)
        if z.druh == "cena":
            return [Zprava(odpovedi.cena(nalez.modely, puvodni))]
        velikost = z.velikost or (nalez.karta.velikost if nalez.karta else None)
        return [Zprava(odpovedi.sklad(nalez.modely, puvodni, velikost))]

    def _cenovka(self, hledane: str, kopie: int, puvodni: str) -> list[Zprava]:
        if not 1 <= kopie <= MAX_KOPII:
            return [Zprava(f"Počet kopií může být 1 až {MAX_KOPII}.")]
        if not hledane:
            return [Zprava("Napište, na co cenovku, třeba „cenovka UP-120 2x“.")]
        modely = hledej(self.sklad, hledane).modely
        if not modely:
            return [Zprava(odpovedi.nic(puvodni))]
        if len(modely) > 1:
            return [Zprava(odpovedi.vyber_pro_cenovku(modely))]
        m = modely[0]
        pdf = vytvor_cenovku(m, self.slozka_cenovek / f"cenovka-{m.kod}.pdf",
                             prodejna=self.sklad.prodejna)
        v = self.tiskarna.vytiskni(pdf, kopie)
        stav = (f"Vytištěno {v.vytisteno}× ✓ ({self.tiskarna.nazev})" if v.ok else
                f"Tisk se nepovedl: {v.chyba} Znovu netisknu, zkontrolujte tiskárnu.")
        return [Zprava(f"Cenovka {m.nazev} · {kc(m.cena_s_dph)}\n{stav}", soubor=pdf)]
