import csv
from datetime import datetime
from typing import List
from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from produkte.renten_basis import RentenProdukt

class CsvExport:
    def __init__(self, profil: NutzerProfil, steuer_rechner: SteuerRechner, produkte: List[RentenProdukt]):
        self.profil = profil
        self.steuer_rechner = steuer_rechner
        # Gesetzliche Rentenversicherung aus dem Export ausschließen (per Name oder Flag)
        self.produkte = [
            p for p in produkte 
            if "Gesetzliche Rentenversicherung" not in p.name() and not getattr(p, "is_gesetzlich", False)
        ]

    def _ermittle_monatswerte(self, p: RentenProdukt, aktueller_monat: datetime):
        """Ermittelt die Monatswerte über das Produkt-Interface ohne Seiteneffekte."""
        return p.berechne_monatliche_details(
            aktueller_monat,
            self.profil,
            self.steuer_rechner,
        )

    def exportiere_monatliche_projektion(self, dateiname: str = "renten_verlauf.csv"):
        with open(dateiname, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            
            # Header erstellen
            header = [
                "Jahr", 
                "Monat", 
                "Gesamtnettoaufwand", 
                "Gesamtförderung Arbeitgeber", 
                "Gesamtförderung Staat"
            ]
            for p in self.produkte:
                p_name = p.name()
                header.extend([
                    f"{p_name} - Netto Eigenleistung",
                    f"{p_name} - AG-Beitrag",
                    f"{p_name} - Kapitalstand",
                    f"{p_name} - Staatliche Förderung"
                ])
            writer.writerow(header)

            heute = datetime.today()
            rente_datum = datetime.strptime(self.profil.renteneintrittsdatum, "%Y-%m-%d")

            # Vorbereitung der Produktdaten
            produkt_daten = []
            for produkt in self.produkte:
                p_start_str = getattr(produkt, "start_datum", heute.strftime("%Y-%m-%d"))
                try:
                    p_start = datetime.strptime(p_start_str, "%Y-%m-%d")
                except ValueError:
                    p_start = heute

                startkapital_wert = getattr(produkt, "startkapital", 0.0)
                startkapital_datum_str = getattr(produkt, "startkapital_datum", None)
                
                if startkapital_datum_str:
                    try:
                        p_startkapital_dt = datetime.strptime(startkapital_datum_str, "%Y-%m-%d")
                    except ValueError:
                        p_startkapital_dt = p_start
                else:
                    p_startkapital_dt = p_start

                rendite_pa = getattr(produkt, "erwartete_rendite_prozent", 0.0)
                kosten_pa = getattr(produkt, "kostenquote_prozent", getattr(produkt, "kosten_renditeminderung_prozent", 0.0))
                monatlicher_zins = (1 + (rendite_pa - kosten_pa) / 100) ** (1 / 12) - 1

                produkt_daten.append({
                    "objekt": produkt,
                    "aktuelles_datum": p_start,
                    "startkapital_wert": startkapital_wert,
                    "startkapital_datum": p_startkapital_dt,
                    "kapital": 0.0,
                    "startkapital_verbucht": False,
                    "monatlicher_zins": monatlicher_zins,
                    "name": produkt.name()
                })

            start_daten = [d["aktuelles_datum"] for d in produkt_daten]
            if not start_daten:
                print("⚠️ Keine gültigen Produkte für den Export gefunden.")
                return
            
            global_start = min(start_daten)
            delta_jahre = rente_datum.year - global_start.year
            delta_monate = delta_jahre * 12 + (rente_datum.month - global_start.month)
            gesamt_monate = max(delta_monate, 0)

            aktueller_monat = global_start

            # Schleife über jeden Monat
            for m in range(1, gesamt_monate + 1):
                monat_netto_gesamt = 0.0
                monat_ag_gesamt = 0.0
                monat_staat_gesamt = 0.0
                
                produkt_zeilen_werte = []

                for p_dict in produkt_daten:
                    p = p_dict["objekt"]
                    p_start = p_dict["aktuelles_datum"]

                    netto_leistung = 0.0
                    ag_beitrag = 0.0
                    staatliche_foerderung = 0.0
                    gesamt_spar_beitrag = 0.0

                    # 1. Prüfen, ob das Produkt aktiv ist
                    if aktueller_monat >= p_start:
                        netto_leistung, ag_beitrag, staatliche_foerderung, gesamt_spar_beitrag = self._ermittle_monatswerte(p, aktueller_monat)

                        monat_netto_gesamt += netto_leistung
                        monat_ag_gesamt += ag_beitrag
                        monat_staat_gesamt += staatliche_foerderung

                    # 2. Startkapital verbuchen
                    if aktueller_monat >= p_dict["startkapital_datum"] and not p_dict["startkapital_verbucht"]:
                        p_dict["kapital"] += p_dict["startkapital_wert"]
                        p_dict["startkapital_verbucht"] = True

                    # 3. Zinseszins + laufender Sparbeitrag
                    if aktueller_monat >= p_start or p_dict["startkapital_verbucht"]:
                        p_dict["kapital"] = (p_dict["kapital"] * (1 + p_dict["monatlicher_zins"])) + (gesamt_spar_beitrag if aktueller_monat >= p_start else 0.0)

                    # Produktdaten anhängen
                    produkt_zeilen_werte.extend([
                        f"{netto_leistung:.2f}".replace(".", ","),
                        f"{ag_beitrag:.2f}".replace(".", ","),
                        f"{p_dict['kapital']:.2f}".replace(".", ","),
                        f"{staatliche_foerderung:.2f}".replace(".", ",")
                    ])

                zeilen_werte = [
                    aktueller_monat.year,
                    aktueller_monat.month,
                    f"{monat_netto_gesamt:.2f}".replace(".", ","),
                    f"{monat_ag_gesamt:.2f}".replace(".", ","),
                    f"{monat_staat_gesamt:.2f}".replace(".", ",")
                ] + produkt_zeilen_werte

                writer.writerow(zeilen_werte)

                # Datum um einen Monat vorrücken
                if aktueller_monat.month == 12:
                    aktueller_monat = aktueller_monat.replace(year=aktueller_monat.year + 1, month=1)
                else:
                    aktueller_monat = aktueller_monat.replace(month=aktueller_monat.month + 1)

        print(f"✅ CSV-Export erfolgreich unter '{dateiname}' gespeichert!")