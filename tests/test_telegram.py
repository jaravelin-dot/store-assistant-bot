import io
import json
import urllib.error

import pytest

from store_bot.telegram import TelegramApi, TelegramKanal

TOKEN = "0:ukazkovy-token"


class FalesneApi:
    def __init__(self):
        self.zpravy, self.soubory = [], []

    def posli(self, chat, text):
        self.zpravy.append((chat, text))

    def posli_soubor(self, chat, cesta, popis=""):
        self.soubory.append((chat, cesta, popis))


def update(text, chat=7):
    return {"update_id": 1, "message": {"chat": {"id": chat, "type": "private"}, "text": text}}


def test_textova_odpoved(asistent):
    api = FalesneApi()
    TelegramKanal(api, asistent).zpracuj(update("objednávka 1041"))
    assert api.zpravy[0][0] == 7 and api.zpravy[0][1].startswith("Objednávka 1041")


def test_cenovka_jde_jako_dokument(asistent):
    api = FalesneApi()
    TelegramKanal(api, asistent).zpracuj(update("cenovka UP-140"))
    [(chat, cesta, popis)] = api.soubory
    assert chat == 7 and cesta.name == "cenovka-UP-140.pdf" and popis.startswith("Cenovka")


def test_cizi_chat_nedostane_data(asistent):
    api = FalesneApi()
    TelegramKanal(api, asistent, povolene_chaty={1}).zpracuj(update("holínky", chat=99))
    assert api.zpravy == [(99, "Tenhle bot je jen pro zaměstnance prodejny. Vaše chat ID je 99.")]


def test_zprava_bez_textu_se_ignoruje(asistent):
    api = FalesneApi()
    TelegramKanal(api, asistent).zpracuj({"update_id": 1, "message": {"chat": {"id": 7}}})
    assert api.zpravy == []


def test_api_posle_json_na_spravnou_metodu():
    volani = []

    def otevri(req, timeout):
        volani.append(req)
        return io.BytesIO(json.dumps({"ok": True, "result": []}).encode())

    TelegramApi(TOKEN, otevri).posli(5, "ahoj")
    req = volani[0]
    assert req.full_url.endswith("/sendMessage")
    assert json.loads(req.data) == {"chat_id": 5, "text": "ahoj"}


def test_soubor_jde_jako_multipart(tmp_path):
    volani = []
    pdf = tmp_path / "c.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    def otevri(req, timeout):
        volani.append(req)
        return io.BytesIO(b'{"ok": true, "result": {}}')

    TelegramApi(TOKEN, otevri).posli_soubor(5, pdf, "popis")
    req = volani[0]
    assert req.get_header("Content-type").startswith("multipart/form-data; boundary=")
    assert b'filename="c.pdf"' in req.data and b"%PDF-1.4 test" in req.data


def test_token_se_nevypise_v_chybe():
    def otevri(req, timeout):
        raise urllib.error.URLError(f"spojení selhalo: {req.full_url}")

    with pytest.raises(RuntimeError) as chyba:
        TelegramApi(TOKEN, otevri).posli(5, "ahoj")
    assert TOKEN not in str(chyba.value) and "***" in str(chyba.value)
