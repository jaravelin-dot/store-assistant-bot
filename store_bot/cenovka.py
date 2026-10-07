"""Cenovka na regál do PDF (A6 na šířku) — neutrální vzhled v odstínech šedi.

Písmo s českou diakritikou se hledá v systému (Arial, DejaVu, Liberation).
Když žádné není, použije se vestavěná Helvetica a text se zapíše bez
diakritiky — cenovka vznikne vždycky.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.graphics.barcode import code128
from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A6, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from .sklad import Model
from .text import bez_diakritiky, kc

SEDA = Color(0.38, 0.38, 0.38)
SVETLA = Color(0.82, 0.82, 0.82)
KANDIDATI_PISMA = [
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf",
     "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
]


def _pismo() -> tuple[str, str, bool]:
    """(běžné, tučné, umí diakritiku)."""
    for bezne, tucne in KANDIDATI_PISMA:
        if Path(bezne).exists() and Path(tucne).exists():
            if "Cenovka" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("Cenovka", bezne))
                pdfmetrics.registerFont(TTFont("Cenovka-Tucne", tucne))
            return "Cenovka", "Cenovka-Tucne", True
    return "Helvetica", "Helvetica-Bold", False


def vytvor_cenovku(model: Model, cesta: Path, prodejna: str = "Ukázková prodejna",
                   datum: date | None = None) -> Path:
    cesta = Path(cesta)
    cesta.parent.mkdir(parents=True, exist_ok=True)
    bezne, tucne, diakritika = _pismo()

    def t(s: str) -> str:
        return s if diakritika else bez_diakritiky(s)

    sirka, vyska = landscape(A6)
    okraj = 7 * mm
    c = Canvas(str(cesta), pagesize=(sirka, vyska), invariant=1)
    c.setTitle(t(f"Cenovka {model.kod}"))
    c.setAuthor(t(prodejna))
    c.setCreator("store_bot")
    c.setSubject(t(model.nazev))

    # rámeček na stříhání
    c.setStrokeColor(SVETLA)
    c.setLineWidth(0.6)
    c.roundRect(3 * mm, 3 * mm, sirka - 6 * mm, vyska - 6 * mm, 3 * mm)

    # hlavička: prodejna | kategorie
    y = vyska - okraj - 4 * mm
    c.setFillColor(SEDA)
    c.setFont(tucne, 7.5)
    c.drawString(okraj, y, t(prodejna.upper()))
    c.setFont(bezne, 7.5)
    c.drawRightString(sirka - okraj, y, t(model.kategorie))
    c.setStrokeColor(black)
    c.setLineWidth(1.2)
    c.line(okraj, y - 3 * mm, sirka - okraj, y - 3 * mm)

    # název modelu (max. 2 řádky)
    c.setFillColor(black)
    velikost_nazvu = 21
    radky = simpleSplit(t(model.nazev), tucne, velikost_nazvu, sirka - 2 * okraj)[:2]
    y -= 13 * mm
    for r in radky:
        c.setFont(tucne, velikost_nazvu)
        c.drawString(okraj, y, r)
        y -= velikost_nazvu * 1.15
    c.setFillColor(SEDA)
    c.setFont(bezne, 10)
    c.drawString(okraj, y - 1 * mm, t(f"Kód {model.kod}   ·   Velikosti {model.rozsah_velikosti}"))

    # cena
    c.setFillColor(black)
    c.setFont(tucne, 54)
    c.drawRightString(sirka - okraj, 29 * mm, t(kc(model.cena_s_dph)))
    c.setFillColor(SEDA)
    c.setFont(bezne, 9)
    c.drawRightString(sirka - okraj, 10 * mm,
                      t(f"bez DPH {kc(model.cena_bez_dph, desetiny=True)}   ·   "
                        f"DPH {model.dph_procent} %"))

    # čárový kód kódu modelu + datum
    kod = code128.Code128(model.kod, barHeight=9 * mm, barWidth=0.75)
    kod.drawOn(c, okraj - 3 * mm, 15 * mm)
    c.setFont(bezne, 8)
    dnes = datum or date.today()
    c.drawString(okraj, 10 * mm, t(f"Platí od {dnes.day}. {dnes.month}. {dnes.year}"))

    c.showPage()
    c.save()
    return cesta
