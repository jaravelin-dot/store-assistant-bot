"""Telegram přes long polling — jen standardní knihovna, žádný webhook ani server.

Spustí se jen s vlastním tokenem v proměnné TELEGRAM_TOKEN. Volitelně
TELEGRAM_ALLOWED_CHATS="123,456" omezí, kdo smí psát (zaměstnanci prodejny).
Token se nikdy nevypisuje — ani v chybách.
"""
from __future__ import annotations

import json
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path

from .bot import Asistent

ZAKLAD = "https://api.telegram.org"
MAX_TEXT = 4096


class TelegramApi:
    def __init__(self, token: str, otevri=urllib.request.urlopen):
        self.token, self._otevri = token, otevri

    def _chyba(self, exc: Exception) -> RuntimeError:
        return RuntimeError(str(exc).replace(self.token, "***"))

    def _posli_pozadavek(self, metoda: str, telo: bytes, typ: str, timeout: int):
        req = urllib.request.Request(f"{ZAKLAD}/bot{self.token}/{metoda}", data=telo,
                                     headers={"Content-Type": typ}, method="POST")
        try:
            with self._otevri(req, timeout=timeout) as r:
                odpoved = json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise self._chyba(exc) from None
        if not odpoved.get("ok"):
            raise RuntimeError(f"Telegram {metoda}: {odpoved.get('description')}")
        return odpoved["result"]

    def _volej(self, metoda: str, timeout: int = 70, **data):
        return self._posli_pozadavek(metoda, json.dumps(data).encode("utf-8"),
                                     "application/json", timeout)

    def aktualizace(self, offset: int | None) -> list[dict]:
        return self._volej("getUpdates", offset=offset, timeout=50,
                           allowed_updates=["message"])

    def posli(self, chat_id: int, text: str) -> None:
        if len(text) > MAX_TEXT:
            text = text[:MAX_TEXT - 30].rstrip() + "\n…(zkráceno)"
        self._volej("sendMessage", chat_id=chat_id, text=text)

    def posli_soubor(self, chat_id: int, cesta: Path, popis: str = "") -> None:
        hranice = uuid.uuid4().hex
        cesta = Path(cesta)
        casti = []
        for nazev, hodnota in (("chat_id", str(chat_id)), ("caption", popis[:1024])):
            casti.append(f'--{hranice}\r\nContent-Disposition: form-data; name="{nazev}"'
                         f"\r\n\r\n{hodnota}\r\n".encode("utf-8"))
        casti.append(f'--{hranice}\r\nContent-Disposition: form-data; name="document"; '
                     f'filename="{cesta.name}"\r\nContent-Type: application/pdf\r\n\r\n'
                     .encode("utf-8") + cesta.read_bytes() + b"\r\n")
        casti.append(f"--{hranice}--\r\n".encode("utf-8"))
        self._posli_pozadavek("sendDocument", b"".join(casti),
                              f"multipart/form-data; boundary={hranice}", 120)


class TelegramKanal:
    def __init__(self, api: TelegramApi, asistent: Asistent,
                 povolene_chaty: set[int] | None = None):
        self.api, self.asistent, self.povolene = api, asistent, povolene_chaty

    def zpracuj(self, update: dict) -> None:
        msg = update.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        text = msg.get("text")
        if chat is None or text is None:
            return
        if self.povolene and chat not in self.povolene:
            self.api.posli(chat, f"Tenhle bot je jen pro zaměstnance prodejny. "
                                 f"Vaše chat ID je {chat}.")
            return
        for z in self.asistent.odpovez(text):
            if z.soubor is not None:
                self.api.posli_soubor(chat, z.soubor, z.text)
            else:
                self.api.posli(chat, z.text)

    def bez(self, spi=time.sleep) -> None:
        offset = None
        print("Bot běží v Telegramu, ukončíte Ctrl+C.")
        while True:
            try:
                aktualizace = self.api.aktualizace(offset)
            except RuntimeError as exc:
                print(f"Chyba spojení s Telegramem: {exc}")
                spi(10)
                continue
            for u in aktualizace:
                offset = u["update_id"] + 1
                try:
                    self.zpracuj(u)
                except Exception as exc:  # noqa: BLE001 — jedna zpráva nesmí shodit bota
                    print(f"Chyba zprávy: {type(exc).__name__}: {exc}")
