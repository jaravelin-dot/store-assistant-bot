"""Texty odpovědí — krátké, aby se daly přečíst na telefonu mezi zákazníky."""
from __future__ import annotations

from .sklad import Model, Objednavka, Sklad, poradi_velikosti
from .text import kc

NAPOVEDA = (
    "Zeptejte se obyčejnou větou, třeba:\n"
    "• Máte pracovní boty vel. 43?\n"
    "• Kolik stojí lehká bunda?\n"
    "• objednávka 1042\n"
    "• Cenovka na ZANDRIK S3, 2 kusy\n"
    "Funguje i EAN nebo kód modelu."
)
LIMIT_SEZNAMU = 6

STAVY = {
    "pripravit": ("k vychystání", None),
    "ceka_na_platbu": ("čeká na platbu", "⚠ Zatím nevychystávat, čeká se na platbu."),
    "odeslana": ("odeslaná", None),
    "zrusena": ("zrušená", "⚠ Zrušená, nevychystávat."),
}


def nic(hledane: str) -> str:
    if not hledane:
        return "Napište, co hledáte — název, kód nebo EAN."
    return f"Nic jsem nenašel pro „{hledane}“. Zkuste kratší slovo, kód nebo EAN."


def _nejblizsi(m: Model, velikost: str, pocet: int = 2) -> list[str]:
    cil = poradi_velikosti(velikost)
    skladem = [k for k in m.karty if k.ks > 0 and poradi_velikosti(k.velikost)[0] == cil[0]]
    skladem.sort(key=lambda k: abs(poradi_velikosti(k.velikost)[1] - cil[1]))
    vybrane = sorted(skladem[:pocet], key=lambda k: poradi_velikosti(k.velikost))
    return [f"{k.velikost} ({k.ks} ks)" for k in vybrane]


def detail(m: Model, velikost: str | None = None) -> str:
    radky = [f"{m.nazev} · {m.kod}", f"Cena {kc(m.cena_s_dph)} s DPH"]
    if velikost:
        k = m.karta(velikost)
        if k is None:
            radky.append(f"Velikost {velikost} tento model nemá (vede se {m.rozsah_velikosti}).")
        elif k.ks > 0:
            radky.append(f"✓ Velikost {k.velikost}: skladem {k.ks} ks")
        else:
            radky.append(f"✗ Velikost {k.velikost}: teď není skladem")
            if blizko := _nejblizsi(m, velikost):
                radky.append("Nejbližší skladem: " + ", ".join(blizko))
    skladem = [f"{k.velikost} ({k.ks})" for k in m.karty if k.ks > 0]
    if skladem:
        radky.append("Všechny velikosti skladem: " + ", ".join(skladem))
    else:
        radky.append("Není skladem v žádné velikosti.")
    return "\n".join(radky)


def seznam(modely: list[Model], velikost: str | None = None) -> str:
    if velikost:
        def ks(m: Model) -> int:
            k = m.karta(velikost)
            return k.ks if k else -1
        modely = sorted(modely, key=lambda m: -ks(m))
        radky = [f"Ve velikosti {velikost} mám tyto modely:"]
        for m in modely[:LIMIT_SEZNAMU]:
            k = m.karta(velikost)
            stav = (f"{k.ks} ks ✓" if k and k.ks > 0 else
                    "vyprodáno" if k else "tuto velikost nevede")
            radky.append(f"• {m.nazev} · {kc(m.cena_s_dph)} · {stav}")
    else:
        radky = [f"Našel jsem {len(modely)} modely:" if len(modely) < 5 else
                 f"Našel jsem {len(modely)} modelů:"]
        for m in modely[:LIMIT_SEZNAMU]:
            radky.append(f"• {m.nazev} · {kc(m.cena_s_dph)} · skladem {m.ks} ks")
    if len(modely) > LIMIT_SEZNAMU:
        radky.append(f"…a dalších {len(modely) - LIMIT_SEZNAMU}, upřesněte hledání.")
    radky.append("Napište název nebo kód modelu a ukážu všechny velikosti.")
    return "\n".join(radky)


def sklad(modely: list[Model], hledane: str, velikost: str | None = None) -> str:
    if not modely:
        return nic(hledane)
    if len(modely) == 1:
        return detail(modely[0], velikost)
    return seznam(modely, velikost)


def cena(modely: list[Model], hledane: str) -> str:
    if not modely:
        return nic(hledane)
    if len(modely) == 1:
        m = modely[0]
        return (f"{m.nazev} · {m.kod}\n{kc(m.cena_s_dph)} s DPH "
                f"({kc(m.cena_bez_dph, desetiny=True)} bez DPH)")
    radky = ["Ceny s DPH:"]
    radky += [f"• {m.nazev} · {kc(m.cena_s_dph)}" for m in modely[:LIMIT_SEZNAMU]]
    if len(modely) > LIMIT_SEZNAMU:
        radky.append(f"…a dalších {len(modely) - LIMIT_SEZNAMU}, upřesněte hledání.")
    return "\n".join(radky)


def objednavka(o: Objednavka | None, cislo: str, sklad_: Sklad) -> str:
    if o is None:
        return f"Objednávku {cislo} nevidím. Zkontrolujte prosím číslo."
    cesky, varovani = STAVY.get(o.stav, (o.stav, None))
    radky = [f"Objednávka {o.cislo} · {cesky}"]
    if varovani:
        radky.append(varovani)
    radky.append(f"{o.doprava} · {o.platba}")
    hlidat_sklad = o.stav in ("pripravit", "ceka_na_platbu")
    vse_skladem = True
    for i, p in enumerate(o.polozky, 1):
        z = sklad_.podle_eanu(p.ean)
        if z is None:
            radky.append(f"{i}) neznámá položka (EAN {p.ean}) · {p.ks} ks")
            vse_skladem = False
            continue
        m, k = z
        radek = f"{i}) {m.nazev}, vel. {k.velikost} · {p.ks} ks"
        if hlidat_sklad:
            if k.ks >= p.ks:
                radek += f" · skladem {k.ks} ✓"
            else:
                radek += f" · ⚠ skladem jen {k.ks}" if k.ks > 0 else " · ⚠ není skladem"
                vse_skladem = False
        radky.append(radek)
    if o.stav == "pripravit":
        radky.append("Vše je skladem, můžete vychystat." if vse_skladem else
                     "Něco chybí — vychystejte, co je, a dejte vědět vedoucímu.")
    return "\n".join(radky)


def vyber_pro_cenovku(modely: list[Model]) -> str:
    radky = ["Pro cenovku potřebuji jeden model. Myslíte některý z těchto?"]
    radky += [f"• {m.nazev} · kód {m.kod}" for m in modely[:LIMIT_SEZNAMU]]
    radky.append(f"Napište třeba „cenovka {modely[0].kod} 2x“.")
    return "\n".join(radky)
