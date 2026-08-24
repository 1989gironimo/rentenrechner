"""Config-Export UI-Komponente."""

import streamlit as st
import json
from datetime import date, datetime

from ui.produkt_registry import PRODUKTE
from utils.config import _get_toggle_map


def _serialize_value(value):
    """Wandelt Werte in JSON-serialisierbare Formate um."""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return str(value)


def _build_export_config(profil_values, produkte_config):
    """Baut die vollständige Config aus den aktuellen UI-Werten."""

    # Profil
    profil = {
        "geburtsdatum": profil_values["geburtsdatum"].strftime("%Y-%m-%d"),
        "renteneintrittsdatum": profil_values["renteneintritt"].strftime("%Y-%m-%d"),
        "wunschrente_heutige_kaufkraft": profil_values["wunschrente"],
        "inflation_prozent": profil_values["inflation"],
        "aktuelles_brutto_monat": profil_values["brutto"],
        "gehaltssteigerung_prozent": profil_values["gehaltssteigerung"],
        "anzahl_kinder": int(profil_values.get("anzahl_kinder", 0)),
        "kindergeburtsjahre": profil_values.get("kindergeburtsjahre", []),
    }

    # Steuern
    steuern = {
        "kv_pv_satz_voll": profil_values["kv_pv_voll"],
        "kv_pv_satz_ermässigt": profil_values["kv_pv_erm"],
        "persoenlicher_steuersatz": profil_values["steuersatz"],
        "abgeltungsteuersatz_prozent": profil_values["abgeltung"],
        "solidaritaetszuschlag_prozent": profil_values["soli"],
        "kirchensteuer_prozent": profil_values["kirchen"],
        "teilfreistellung_prozent": profil_values["teilfrei"],
    }

    # Produkte
    toggle_map = _get_toggle_map()
    active_by_modul = {p["modul_name"]: p for p in produkte_config}
    produkte = []

    for prod in PRODUKTE:
        modul = prod["modul_name"]
        toggle_key = toggle_map.get(modul, f"{modul}_on")
        is_active = st.session_state.get(toggle_key, False)

        if modul in active_by_modul:
            param = dict(active_by_modul[modul]["parameter"])
            param.pop("abgaben_typ", None)  # interner Key, nicht in Config nötig
            produkte.append({
                "modul_name": modul,
                "klassen_name": prod["klassen_name"],
                "aktiviert": True,
                "parameter": _serialize_value(param),
            })
        else:
            # Deaktiviert – Status erhalten, Parameter leer
            produkte.append({
                "modul_name": modul,
                "klassen_name": prod["klassen_name"],
                "aktiviert": False,
                "parameter": {},
            })

    config = {
        "profil": profil,
        "steuern": steuern,
        "produkte": produkte,
    }

    return json.dumps(config, indent=2, ensure_ascii=False)


def render_config_export(profil_values, produkte_config):
    """Zeigt den Export-Button für die aktuelle Konfiguration an."""
    with st.expander("💾 Aktuelle Konfiguration exportieren"):
        config_json = _build_export_config(profil_values, produkte_config)

        st.download_button(
            label="📤 Config als JSON herunterladen",
            data=config_json,
            file_name="rentenrechner_config.json",
            mime="application/json",
        )

        st.caption(
            "Die Datei enthält alle aktuellen Eingaben und kann später "
            'wieder über "Config.json importieren" geladen werden.'
        )
