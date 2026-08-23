import csv
from engine.aggregator import RentenAggregator


class CsvExport:
    def __init__(self, aggregator: RentenAggregator):
        self.aggregator = aggregator

    def exportiere_monatliche_projektion(self, dateiname: str = "renten_verlauf.csv"):
        df = self.aggregator.berechne_monatliche_projektion()
        if df.empty:
            print("⚠️ Keine gültigen Produkte für den Export gefunden.")
            return

        # Produkte ermitteln (ohne "Gesamt")
        produkte = [p for p in df["produkt"].unique() if p != "Gesamt"]

        # Header aufbauen
        header = [
            "Jahr",
            "Monat",
            "Gesamtnettoaufwand",
            "Gesamtförderung Arbeitgeber",
            "Gesamtförderung Staat",
        ]
        for p_name in produkte:
            header.extend([
                f"{p_name} - Netto Eigenleistung",
                f"{p_name} - AG-Beitrag",
                f"{p_name} - Kapitalstand",
                f"{p_name} - Staatliche Förderung",
            ])

        with open(dateiname, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(header)

            # Pro Jahr/Monat aggregieren
            for (jahr, monat), gruppe in df.groupby(["jahr", "monat"]):
                # Gesamtsummen
                gesamt_netto = gruppe["netto_eigenleistung"].sum()
                gesamt_ag = gruppe["ag_beitrag"].sum()
                gesamt_staat = gruppe["staatliche_foerderung"].sum()

                zeile = [
                    jahr,
                    monat,
                    f"{gesamt_netto:.2f}".replace(".", ","),
                    f"{gesamt_ag:.2f}".replace(".", ","),
                    f"{gesamt_staat:.2f}".replace(".", ","),
                ]

                # Pro Produkt die Werte
                for p_name in produkte:
                    prod_df = gruppe[gruppe["produkt"] == p_name]
                    if not prod_df.empty:
                        row = prod_df.iloc[0]
                        zeile.extend([
                            f"{row['netto_eigenleistung']:.2f}".replace(".", ","),
                            f"{row['ag_beitrag']:.2f}".replace(".", ","),
                            f"{row['kapital']:.2f}".replace(".", ","),
                            f"{row['staatliche_foerderung']:.2f}".replace(".", ","),
                        ])
                    else:
                        zeile.extend(["0,00", "0,00", "0,00", "0,00"])

                writer.writerow(zeile)

        print(f"✅ CSV-Export erfolgreich unter '{dateiname}' gespeichert!")
