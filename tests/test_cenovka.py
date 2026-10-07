from datetime import date

from pypdf import PdfReader

from store_bot import cenovka


def model(sklad, kod):
    return next(m for m in sklad.modely if m.kod == kod)


def test_cenovka_pdf(sklad, tmp_path):
    pdf = cenovka.vytvor_cenovku(model(sklad, "UP-120"), tmp_path / "c.pdf", datum=date(2026, 10, 7))
    r = PdfReader(pdf)
    assert len(r.pages) == 1
    text = r.pages[0].extract_text()
    for cast in ("ZANDRIK S3", "UP-120", "1 590 Kč", "bez DPH 1 314,05 Kč", "42–45", "7. 10. 2026"):
        assert cast in text
    sirka, vyska = float(r.pages[0].mediabox.width), float(r.pages[0].mediabox.height)
    assert sirka > vyska   # A6 na šířku
    assert r.metadata.author == "Ukázková prodejna"


def test_cenovka_bez_systemoveho_pisma(sklad, tmp_path, monkeypatch):
    monkeypatch.setattr(cenovka, "KANDIDATI_PISMA", [])
    pdf = cenovka.vytvor_cenovku(model(sklad, "UK-210"), tmp_path / "c.pdf")
    text = PdfReader(pdf).pages[0].extract_text()
    assert "Pracovni kalhoty do pasu TOBRAK" in text   # Helvetica bez diakritiky
    assert "790 K" in text


def test_dlouhy_nazev_se_zalomi(sklad, tmp_path):
    m = model(sklad, "UP-110")
    m.nazev = "Velmi dlouhý název pracovní boty, který se na jeden řádek cenovky nevejde"
    pdf = cenovka.vytvor_cenovku(m, tmp_path / "c.pdf")
    assert "Velmi dlouhý název" in PdfReader(pdf).pages[0].extract_text()
