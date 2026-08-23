import json
import os
import importlib
from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from engine.aggregator import RentenAggregator
from engine.csv_export import CsvExport  # <--- NEU: Import für den CSV-Export


def produkt_soll_aktiviert(eintrag: dict) -> bool:
    if "aktiviert" in eintrag:
        return bool(eintrag["aktiviert"])
    if "enabled" in eintrag:
        return bool(eintrag["enabled"])
    return True


def main():
    config_pfad = "config.json"
    
    if not os.path.exists(config_pfad):
        print(f"Fehler: Die Datei '{config_pfad}' konnte nicht gefunden werden.")
        return

    with open(config_pfad, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    # 1. Nutzerprofil laden
    profil_daten = daten["profil"]
    mein_profil = NutzerProfil(
        geburtsdatum=profil_daten["geburtsdatum"],
        renteneintrittsdatum=profil_daten["renteneintrittsdatum"],
        wunschrente_heutige_kaufkraft=profil_daten["wunschrente_heutige_kaufkraft"],
        aktuelles_brutto_monat=profil_daten["aktuelles_brutto_monat"],
        inflation_prozent=profil_daten["inflation_prozent"],
        gehaltssteigerung_prozent=profil_daten.get("gehaltssteigerung_prozent", 2.0)
    )

    # 2. Steuerrechner initialisieren
    steuer_daten = daten.get("steuern", {})
    steuer_rechner = SteuerRechner(
        kv_pv_satz_voll=steuer_daten.get("kv_pv_satz_voll", 18.5),
        kv_pv_satz_ermässigt=steuer_daten.get("kv_pv_satz_ermässigt", 11.3),
        persoenlicher_steuersatz=steuer_daten.get("persoenlicher_steuersatz", 20.0),
        abgeltungsteuersatz_prozent=steuer_daten.get("abgeltungsteuersatz_prozent", 25.0),
        solidaritaetszuschlag_prozent=steuer_daten.get("solidaritaetszuschlag_prozent", 5.5),
        kirchensteuer_prozent=steuer_daten.get("kirchensteuer_prozent", 0.0),
        teilfreistellung_prozent=steuer_daten.get("teilfreistellung_prozent", 70.0),
    )

    # 3. Aggregator mit Profil und Steuern starten
    rechner = RentenAggregator(profil=mein_profil, steuer_rechner=steuer_rechner)

    # 4. Produkte dynamisch laden
    produkt_eintraege = daten.get("produkte", [])
    for eintrag in produkt_eintraege:
        if not produkt_soll_aktiviert(eintrag):
            continue

        mod_name = eintrag["modul_name"]
        class_name = eintrag["klassen_name"]
        parameter = dict(eintrag.get("parameter", {}))
        for flag_key in ("aktiviert", "enabled"):
            parameter.pop(flag_key, None)

        try:
            modul = importlib.import_module(f"produkte.{mod_name}")
            produkt_klasse = getattr(modul, class_name)
            produkt_objekt = produkt_klasse(**parameter)
            rechner.produkt_hinzufuegen(produkt_objekt)
        except (ModuleNotFoundError, AttributeError) as e:
            print(f"⚠️ Warnung: Konnte Produkt '{class_name}' aus Modul 'produkte.{mod_name}' nicht laden. Fehler: {e}")

    # 5. Report ausgeben
    rechner.generiere_report()

    # 6. Monatliche Projektion als CSV exportieren <--- NEU
    export = CsvExport(profil=mein_profil, steuer_rechner=steuer_rechner, produkte=rechner.produkte)
    export.exportiere_monatliche_projektion("renten_verlauf.csv")

if __name__ == "__main__":
    main()