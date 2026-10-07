"""Obrázky do README: ukázková konverzace (HTML → PNG) a cenovka (PDF → PNG).

    pip install -e .[screenshots] && python -m playwright install chromium
    python tools/screenshoty.py

Vše z vymyšlených dat. PNG se ukládají bez metadat.
"""
from __future__ import annotations

import html
import sys
import tempfile
from pathlib import Path

import pypdfium2 as pdfium
import PIL.Image
from playwright.sync_api import sync_playwright

KOREN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOREN))

from store_bot.__main__ import sestav  # noqa: E402

DOCS = KOREN / "docs"
DOTAZY = [
    ("8:02", "Máte pracovní boty vel. 43?"),
    ("8:03", "zandrk s3 43"),
    ("8:05", "objednávka 1042"),
    ("8:06", "Cenovka na ZANDRIK S3, 2 kusy"),
]

STYL = """
* { box-sizing: border-box; margin: 0; }
body { font: 15px/1.38 "Segoe UI", system-ui, sans-serif; background: #e9edf1; width: 460px; }
.hlava { background: #fff; padding: 12px 16px; display: flex; gap: 12px; align-items: center;
         border-bottom: 1px solid #d5dbe1; }
.avatar { width: 38px; height: 38px; border-radius: 50%; background: #2f3a45; color: #fff;
          display: grid; place-items: center; font-weight: 600; font-size: 14px; }
.jmeno { font-weight: 600; } .pod { color: #6b7783; font-size: 13px; }
.chat { padding: 14px 12px 18px; display: flex; flex-direction: column; gap: 8px; }
.b { max-width: 86%; padding: 8px 11px 6px; border-radius: 12px; white-space: pre-wrap;
     box-shadow: 0 1px 1px rgba(0,0,0,.08); }
.ja { align-self: flex-end; background: #d9f2d0; border-bottom-right-radius: 4px; }
.bot { align-self: flex-start; background: #fff; border-bottom-left-radius: 4px; }
.cas { display: block; text-align: right; color: #8a96a1; font-size: 11px; margin-top: 2px; }
.soubor { display: flex; gap: 10px; align-items: center; margin-bottom: 6px; }
.ikona { width: 40px; height: 40px; border-radius: 8px; background: #2f3a45; color: #fff;
         display: grid; place-items: center; font-size: 11px; font-weight: 700; }
.soubor small { color: #6b7783; display: block; }
"""


def chat_html(dvojice: list[tuple[str, str, list]]) -> str:
    casti = ['<div class="hlava"><div class="avatar">UP</div><div>'
             '<div class="jmeno">Ukázková prodejna · asistent</div>'
             '<div class="pod">bot pro zaměstnance prodejny</div></div></div><div class="chat">']
    for cas, dotaz, odpovedi in dvojice:
        casti.append(f'<div class="b ja">{html.escape(dotaz)}<span class="cas">{cas}</span></div>')
        for z in odpovedi:
            priloha = ""
            if z.soubor:
                kb = max(1, z.soubor.stat().st_size // 1024)
                priloha = (f'<div class="soubor"><div class="ikona">PDF</div><div>'
                           f'{html.escape(z.soubor.name)}<small>{kb} kB</small></div></div>')
            casti.append(f'<div class="b bot">{priloha}{html.escape(z.text)}'
                         f'<span class="cas">{cas}</span></div>')
    casti.append("</div>")
    return f"<!doctype html><meta charset=utf-8><style>{STYL}</style>{''.join(casti)}"


def bez_metadat(cesta: Path) -> None:
    obr = PIL.Image.open(cesta)
    obr.load()
    cista = PIL.Image.new(obr.mode, obr.size)
    cista.paste(obr)
    cista.save(cesta, "PNG", optimize=True)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        asistent = sestav(Path(tmp) / "out")
        dvojice = [(cas, d, asistent.odpovez(d)) for cas, d in DOTAZY]

        with sync_playwright() as p:
            prohlizec = p.chromium.launch()
            stranka = prohlizec.new_page(viewport={"width": 460, "height": 400},
                                         device_scale_factor=2)
            stranka.set_content(chat_html(dvojice))
            stranka.screenshot(path=str(DOCS / "chat.png"), full_page=True)
            prohlizec.close()

        pdf = next(z.soubor for _, _, oo in dvojice for z in oo if z.soubor)
        dokument = pdfium.PdfDocument(str(pdf))
        cenovka = dokument[0].render(scale=3).to_pil().convert("RGB")
        dokument.close()
        okraj = 40
        plocha = PIL.Image.new("RGB", (cenovka.width + 2 * okraj, cenovka.height + 2 * okraj),
                           (233, 237, 241))
        plocha.paste(cenovka, (okraj, okraj))
        plocha.save(DOCS / "cenovka.png", "PNG", optimize=True)

    bez_metadat(DOCS / "chat.png")
    print("hotovo:", DOCS / "chat.png", DOCS / "cenovka.png")


if __name__ == "__main__":
    main()
