from store_bot import odpovedi


def model(sklad, kod):
    return next(m for m in sklad.modely if m.kod == kod)


def test_detail_velikost_skladem(sklad):
    text = odpovedi.detail(model(sklad, "UP-110"), "43")
    assert "✓ Velikost 43: skladem 3 ks" in text
    assert "1 290 Kč" in text


def test_detail_vyprodano_nabidne_nejblizsi(sklad):
    text = odpovedi.detail(model(sklad, "UP-120"), "43")
    assert "✗ Velikost 43: teď není skladem" in text
    assert "Nejbližší skladem: 42 (1 ks), 44 (2 ks)" in text


def test_detail_velikost_neexistuje(sklad):
    text = odpovedi.detail(model(sklad, "UP-130"), "47")
    assert "Velikost 47 tento model nemá (vede se 40–43)" in text


def test_seznam_s_velikosti(sklad):
    modely = [model(sklad, k) for k in ("UP-120", "UP-110", "UP-130")]
    radky = odpovedi.seznam(modely, "43").splitlines()
    assert radky[0] == "Ve velikosti 43 mám tyto modely:"
    assert radky[1].startswith("• Pracovní polobotky ZANDRIK S1P") and radky[1].endswith("3 ks ✓")
    assert radky[3].endswith("vyprodáno")


def test_cena_s_dph_i_bez(sklad):
    text = odpovedi.cena([model(sklad, "UB-310")], "bunda")
    assert "1 490 Kč s DPH (1 231,40 Kč bez DPH)" in text


def test_nic():
    assert "Nic jsem nenašel pro „kytara“" in odpovedi.nic("kytara")


def test_objednavka_k_vychystani_s_chybejici_polozkou(sklad, objednavky):
    text = odpovedi.objednavka(objednavky["1042"], "1042", sklad)
    assert text.startswith("Objednávka 1042 · k vychystání")
    assert "Pracovní kalhoty do pasu TOBRAK, vel. 52 · 1 ks · ⚠ není skladem" in text
    assert "Něco chybí" in text


def test_objednavka_vse_skladem(sklad, objednavky):
    assert "Vše je skladem, můžete vychystat." in odpovedi.objednavka(objednavky["1041"], "1041", sklad)


def test_objednavka_ceka_na_platbu(sklad, objednavky):
    assert "⚠ Zatím nevychystávat" in odpovedi.objednavka(objednavky["1043"], "1043", sklad)


def test_objednavka_zrusena_bez_kontroly_skladu(sklad, objednavky):
    text = odpovedi.objednavka(objednavky["1045"], "1045", sklad)
    assert "⚠ Zrušená" in text and "skladem" not in text


def test_neznama_objednavka(sklad):
    assert odpovedi.objednavka(None, "9999", sklad) == "Objednávku 9999 nevidím. Zkontrolujte prosím číslo."
