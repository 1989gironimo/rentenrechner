"""Sidebar mit Profil & Steuern."""

import streamlit as st
from datetime import datetime
from utils.config import _imported


def render_sidebar():
    with st.sidebar:
        st.header("👤 Profil")
        geburtsdatum = st.date_input(
            "Geburtsdatum",
            value=datetime.strptime(_imported(["profil", "geburtsdatum"], "1995-01-01"), "%Y-%m-%d"),
            help="Dein Geburtsdatum im Format YYYY-MM-DD."
        )
        renteneintritt = st.date_input(
            "Renteneintrittsdatum",
            value=datetime.strptime(_imported(["profil", "renteneintrittsdatum"], "2062-01-01"), "%Y-%m-%d"),
            help="Beginn der modellierten Rentenphase."
        )
        wunschrente = st.number_input(
            "Wunschrente (heutige Kaufkraft, €/Monat)",
            min_value=0.0,
            value=_imported(["profil", "wunschrente_heutige_kaufkraft"], 3000.0),
            step=100.0,
            help="Gewünschtes monatliches Renteneinkommen in **heutiger Kaufkraft**."
        )
        inflation = st.number_input(
            "Inflation (% p.a.)",
            min_value=0.0,
            value=_imported(["profil", "inflation_prozent"], 2.0),
            step=0.1,
            help="Angenommene jährliche Inflation."
        )
        brutto = st.number_input(
            "Aktuelles Bruttogehalt (€/Monat)",
            min_value=0.0,
            value=_imported(["profil", "aktuelles_brutto_monat"], 4500.0),
            step=100.0,
            help="Aktuelles monatliches Bruttogehalt."
        )
        gehaltssteigerung = st.number_input(
            "Gehaltssteigerung (% p.a.)",
            min_value=0.0,
            value=_imported(["profil", "gehaltssteigerung_prozent"], 1.5),
            step=0.1,
            help="Angenommene jährliche Gehaltssteigerung."
        )
        anzahl_kinder = st.number_input(
            "Anzahl Kinder",
            min_value=0,
            value=int(_imported(["profil", "anzahl_kinder"], 0)),
            step=1,
            key="profil_anzahl_kinder",
            help="Anzahl der Kinder. Wird für die Förderung des Altersvorsorge-Depots genutzt."
        )

        # Dynamische Geburtsjahre basierend auf Anzahl Kinder
        kindergeburtsjahre = []
        if anzahl_kinder > 0:
            st.markdown("**Geburtsjahre der Kinder**")
            imported_kinder = _imported(["profil", "kindergeburtsjahre"], [])
            if not isinstance(imported_kinder, list):
                imported_kinder = []

            for i in range(int(anzahl_kinder)):
                default_jahr = imported_kinder[i] if i < len(imported_kinder) else 2020
                jahr = st.number_input(
                    f"Geburtsjahr Kind {i + 1}",
                    min_value=1900,
                    max_value=datetime.now().year,
                    value=int(default_jahr) if isinstance(default_jahr, (int, float)) else 2020,
                    step=1,
                    key=f"kind_geburtsjahr_{i}",
                    help=f"Geburtsjahr des {i + 1}. Kindes."
                )
                kindergeburtsjahre.append(int(jahr))

        st.header("💶 Steuern & Abgaben")
        kv_pv_voll = st.number_input(
            "KV/PV-Satz voll (%)",
            min_value=0.0,
            value=_imported(["steuern", "kv_pv_satz_voll"], 18.5),
            step=0.1,
            help="Angenommener kombinierter KV-/PV-Satz für die **volle** Belastung."
        )
        kv_pv_erm = st.number_input(
            "KV/PV-Satz ermäßigt (%)",
            min_value=0.0,
            value=_imported(["steuern", "kv_pv_satz_ermässigt"], 11.3),
            step=0.1,
            help="Angenommener **reduzierter** KV-/PV-Satz."
        )
        steuersatz = st.number_input(
            "Persönlicher Steuersatz (%)",
            min_value=0.0,
            value=_imported(["steuern", "persoenlicher_steuersatz"], 20.0),
            step=0.5,
            help="Angenommener persönlicher Einkommensteuersatz für die Rentenphase."
        )
        abgeltung = st.number_input(
            "Abgeltungsteuer (%)",
            min_value=0.0,
            value=_imported(["steuern", "abgeltungsteuersatz_prozent"], 25.0),
            step=0.5,
            help="Angenommener Abgeltungsteuersatz auf Kapitalerträge."
        )
        soli = st.number_input(
            "Solidaritätszuschlag (%)",
            min_value=0.0,
            value=_imported(["steuern", "solidaritaetszuschlag_prozent"], 5.5),
            step=0.1,
            help="Solidaritätszuschlag auf die Abgeltungsteuer."
        )
        kirchen = st.number_input(
            "Kirchensteuer (%)",
            min_value=0.0,
            value=_imported(["steuern", "kirchensteuer_prozent"], 0.0),
            step=0.5,
            help="Kirchensteuer; `0.0` bedeutet keine Kirchensteuer."
        )
        teilfrei = st.number_input(
            "Teilfreistellung (%)",
            min_value=0.0, max_value=100.0,
            value=_imported(["steuern", "teilfreistellung_prozent"], 70.0),
            step=1.0,
            help="Angenommene Teilfreistellung bei Kapitalerträgen."
        )

    return {
        "geburtsdatum": geburtsdatum,
        "renteneintritt": renteneintritt,
        "wunschrente": wunschrente,
        "inflation": inflation,
        "brutto": brutto,
        "gehaltssteigerung": gehaltssteigerung,
        "anzahl_kinder": anzahl_kinder,
        "kindergeburtsjahre": kindergeburtsjahre,
        "kv_pv_voll": kv_pv_voll,
        "kv_pv_erm": kv_pv_erm,
        "steuersatz": steuersatz,
        "abgeltung": abgeltung,
        "soli": soli,
        "kirchen": kirchen,
        "teilfrei": teilfrei,
    }
