"""python -m store_bot demo | chat | telegram"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .bot import Asistent
from .sklad import Sklad, nacti_objednavky
from .tisk import SimulovanaTiskarna

DEMO_DOTAZY = [
    "Máte pracovní boty vel. 43?",
    "zandrk s3 43",
    "Kolik stojí lehká bunda?",
    "kalhoty do pasu 52",
    "2001400430006",
    "objednávka 1042",
    "objednávka 1043",
    "Cenovka na ZANDRIK S3, 2 kusy",
    "elektrická kytara",
]


def sestav(out: Path) -> Asistent:
    return Asistent(Sklad.nacti(), nacti_objednavky(), SimulovanaTiskarna(out), out)


def demo(asistent: Asistent) -> None:
    for dotaz in DEMO_DOTAZY:
        print(f"\n> {dotaz}")
        for z in asistent.odpovez(dotaz):
            print(z.text)
            if z.soubor:
                print(f"[příloha: {z.soubor.as_posix()}]")


def chat(asistent: Asistent) -> None:
    print("Ukázková prodejna — asistent. Pište dotazy, „konec“ ukončí.")
    while True:
        try:
            text = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if text.strip().lower() in ("konec", "exit", "quit"):
            return
        for z in asistent.odpovez(text):
            print(z.text)
            if z.soubor:
                print(f"[příloha: {z.soubor.as_posix()}]")


def nacti_env(cesta: Path = Path(".env")) -> None:
    """Minimální čtení .env (KLÍČ=hodnota); proměnné prostředí mají přednost."""
    if not cesta.exists():
        return
    for radek in cesta.read_text(encoding="utf-8").splitlines():
        klic, rovnitko, hodnota = radek.strip().partition("=")
        if rovnitko and klic and not klic.startswith("#"):
            os.environ.setdefault(klic.strip(), hodnota.strip().strip('"\''))


def telegram(asistent: Asistent) -> int:
    from .telegram import TelegramApi, TelegramKanal
    nacti_env()
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if not token:
        print("Chybí TELEGRAM_TOKEN. Vytvořte bota u @BotFather a token dejte do .env "
              "(vzor je v .env.example). Bez tokenu zkuste `python -m store_bot chat`.")
        return 2
    povolene = {int(x) for x in os.environ.get("TELEGRAM_ALLOWED_CHATS", "").split(",")
                if x.strip()}
    TelegramKanal(TelegramApi(token), asistent, povolene or None).bez()
    return 0


def main(argv: list[str] | None = None) -> int:
    for proud in (sys.stdout, sys.stdin):          # konzole Windows bývá cp1250
        try:
            proud.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="python -m store_bot",
                                 description="Asistent prodejny — ukázka nad vymyšlenými daty.")
    ap.add_argument("prikaz", nargs="?", default="demo", choices=["demo", "chat", "telegram"])
    ap.add_argument("--out", type=Path, default=Path("out"),
                    help="složka pro cenovky a záznam tisku (výchozí out/)")
    a = ap.parse_args(argv)
    asistent = sestav(a.out)
    if a.prikaz == "demo":
        demo(asistent)
        return 0
    if a.prikaz == "chat":
        chat(asistent)
        return 0
    try:
        return telegram(asistent)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
