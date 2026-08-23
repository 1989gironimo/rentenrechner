"""Berechnung und Ergebnisanzeige."""

import streamlit as st
import importlib
import io
import csv
from io import StringIO
from contextlib import redirect_stdout

from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from engine.aggregator import RentenAggregator
from engine.visualisierung import KapitalVerlauf


def _generate_csv(aggregator):
    """Erzeugt die monatliche Projektion als CSV-String im Speicher."""
    df = aggregator.berechne_monatliche_projektion()
    if df.empty:
        return None

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

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
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

    return buffer.getvalue()


def render_ergebnis(profil_values, produkte_config):
    st.divider()

    if not st.button("🚀 Berechnung starten", type="primary", use_container_width=True):
        return

    with st.spinner("Berechnung läuft... Das kann einen Moment dauern."):
        try:
            mein_profil = NutzerProfil(
                geburtsdatum=profil_values["geburtsdatum"].strftime("%Y-%m-%d"),
                renteneintrittsdatum=profil_values["renteneintritt"].strftime("%Y-%m-%d"),
                wunschrente_heutige_kaufkraft=profil_values["wunschrente"],
                aktuelles_brutto_monat=profil_values["brutto"],
                inflation_prozent=profil_values["inflation"],
                gehaltssteigerung_prozent=profil_values["gehaltssteigerung"],
                anzahl_kinder=int(profil_values.get("anzahl_kinder", 0)),
                kindergeburtsjahre=profil_values.get("kindergeburtsjahre", []),
            )

            steuer_rechner = SteuerRechner(
                kv_pv_satz_voll=profil_values["kv_pv_voll"],
                kv_pv_satz_ermässigt=profil_values["kv_pv_erm"],
                persoenlicher_steuersatz=profil_values["steuersatz"],
                abgeltungsteuersatz_prozent=profil_values["abgeltung"],
                solidaritaetszuschlag_prozent=profil_values["soli"],
                kirchensteuer_prozent=profil_values["kirchen"],
                teilfreistellung_prozent=profil_values["teilfrei"],
            )

            rechner = RentenAggregator(profil=mein_profil, steuer_rechner=steuer_rechner)

            for eintrag in produkte_config:
                if not eintrag.get("aktiviert", True):
                    continue

                mod_name = eintrag["modul_name"]
                class_name = eintrag["klassen_name"]
                parameter = dict(eintrag.get("parameter", {}))
                for flag_key in ("aktiviert", "enabled"):
                    parameter.pop(flag_key, None)

                modul = importlib.import_module(f"produkte.{mod_name}")
                produkt_klasse = getattr(modul, class_name)
                produkt_objekt = produkt_klasse(**parameter)
                rechner.produkt_hinzufuegen(produkt_objekt)

            report_buffer = StringIO()
            with redirect_stdout(report_buffer):
                rechner.generiere_report()
            report_text = report_buffer.getvalue()

            csv_data = _generate_csv(rechner)

            st.success("Berechnung abgeschlossen!")

            gesamt_kapital = sum(
                p.berechne_endkapital_nominal(mein_profil) for p in rechner.produkte
            )

            st.subheader("📊 Ergebnisübersicht")
            st.metric("Gesamtes Vermögen zum Renteneintritt", f"{gesamt_kapital:,.2f} €")

            st.subheader("📈 Kapitalverlauf")
            verlauf = KapitalVerlauf(mein_profil, steuer_rechner, rechner.produkte)
            fig = verlauf.plot_streamlit()
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Keine kapitalbildenden Produkte zur Visualisierung vorhanden.")

            st.subheader("📝 Detaillierter Report")
            st.text(report_text)

            st.subheader("📥 Export")
            if csv_data:
                st.download_button(
                    label="CSV herunterladen (renten_verlauf.csv)",
                    data=csv_data,
                    file_name="renten_verlauf.csv",
                    mime="text/csv",
                )
            else:
                st.info("Keine gültigen Produkte für den CSV-Export gefunden.")

        except Exception as e:
            st.error(f"Fehler bei der Berechnung: {e}")
            st.exception(e)