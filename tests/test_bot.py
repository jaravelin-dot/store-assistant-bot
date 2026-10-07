from store_bot.bot import Asistent
from store_bot.odpovedi import NAPOVEDA
from store_bot.sklad import Sklad
from store_bot.tisk import SimulovanaTiskarna, VysledekTisku


def platny_ean13(s):
    soucet = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(s[:12]))
    return len(s) == 13 and s.isdigit() and (10 - soucet % 10) % 10 == int(s[12])


def test_ukazkova_data(sklad, objednavky):
    eany = [k.ean for m in sklad.modely for k in m.karty]
    assert 35 <= len(eany) <= 50
    assert len(set(eany)) == len(eany)
    assert all(e.startswith("200") and platny_ean13(e) for e in eany)
    assert len(objednavky) == 5
    assert all(sklad.podle_eanu(p.ean) for o in objednavky.values() for p in o.polozky)


def test_napoveda(asistent):
    assert asistent.odpovez("/start")[0].text == NAPOVEDA


def test_dotaz_na_sklad(asistent):
    [z] = asistent.odpovez("Máte pracovní boty vel. 43?")
    assert z.text.startswith("Ve velikosti 43 mám tyto modely:")
    assert z.soubor is None


def test_ean_ukaze_velikost(asistent):
    [z] = asistent.odpovez("2001400430006")
    assert "✓ Velikost 43: skladem 4 ks" in z.text


def test_nic_ukaze_puvodni_text(asistent):
    [z] = asistent.odpovez("elektrická kytara?")
    assert "„elektrická kytara“" in z.text


def test_jen_vyplnova_slova(asistent):
    [z] = asistent.odpovez("máte?")
    assert z.text.startswith("Napište, co hledáte")


def test_cenovka_vytvori_pdf_a_vytiskne(asistent, tmp_path):
    [z] = asistent.odpovez("Cenovka na ZANDRIK S3, 2 kusy")
    assert z.soubor == tmp_path / "cenovka-UP-120.pdf" and z.soubor.exists()
    assert "Vytištěno 2× ✓" in z.text
    log = (tmp_path / "tisk.log").read_text(encoding="utf-8")
    assert log.strip().endswith("cenovka-UP-120.pdf\t2x")


def test_cenovka_vic_modelu_chce_upresnit(asistent, tmp_path):
    [z] = asistent.odpovez("cenovka zandrik")
    assert z.text.startswith("Pro cenovku potřebuji jeden model")
    assert not list(tmp_path.glob("*.pdf"))


def test_cenovka_moc_kopii(asistent, tmp_path):
    [z] = asistent.odpovez("cenovka UP-120 9x")
    assert z.text == "Počet kopií může být 1 až 5."
    assert not (tmp_path / "tisk.log").exists()


def test_tisk_se_nepovedl(sklad, objednavky, tmp_path):
    class Rozbita:
        nazev = "rozbitá"

        def vytiskni(self, pdf, kopie):
            return VysledekTisku(0, "Došel papír.")

    [z] = Asistent(sklad, objednavky, Rozbita(), tmp_path).odpovez("cenovka UP-140")
    assert "Tisk se nepovedl: Došel papír. Znovu netisknu" in z.text


def test_simulovana_tiskarna_odmitne_chybejici_soubor(tmp_path):
    v = SimulovanaTiskarna(tmp_path).vytiskni(tmp_path / "neni.pdf", 1)
    assert not v.ok and v.vytisteno == 0


def test_demo_bezi(tmp_path, capsys):
    from store_bot.__main__ import main
    assert main(["demo", "--out", str(tmp_path)]) == 0
    vystup = capsys.readouterr().out
    assert "> objednávka 1042" in vystup
    assert (tmp_path / "cenovka-UP-120.pdf").exists()


def test_vlastni_data(tmp_path):
    (tmp_path / "s.json").write_text(
        '{"modely": [{"kod": "X-1", "nazev": "Testovací položka", "kategorie": "Oděvy",'
        ' "cena_s_dph": 121, "karty": [{"velikost": "UNI", "ean": "2000000000008", "ks": 1}]}]}',
        encoding="utf-8")
    s = Sklad.nacti(tmp_path / "s.json")
    assert s.modely[0].cena_bez_dph == 100
