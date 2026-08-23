"""Hilfsfunktionen für den Config-Import in der Streamlit-App."""

import streamlit as st
from datetime import datetime


# Erlaubte Top-Level-Keys in der Config
_ALLOWED_TOP_KEYS = {"profil", "steuern", "produkte"}
_MAX_PRODUKTE = 50


def _validate_config_structure(cfg: dict) -> tuple[bool, str]:
    """
    Prüft die grundlegende Struktur der importierten Config.
    Gibt (ok, fehlermeldung) zurück.
    """
    if not isinstance(cfg, dict):
        return False, "Die Datei enthält kein gültiges JSON-Objekt."

    unbekannte = set(cfg.keys()) - _ALLOWED_TOP_KEYS
    if unbekannte:
        return False, f"Unbekannte Top-Level-Keys: {', '.join(unbekannte)}"

    produkte = cfg.get("produkte", [])
    if not isinstance(produkte, list):
        return False, "'produkte' muss eine Liste sein."
    if len(produkte) > _MAX_PRODUKTE:
        return False, f"Maximal {_MAX_PRODUKTE} Produkte erlaubt."

    for i, p in enumerate(produkte):
        if not isinstance(p, dict):
            return False, f"Produkt {i} ist kein Objekt."
        modul = p.get("modul_name", "")
        if not isinstance(modul, str) or not modul:
            return False, f"Produkt {i}: 'modul_name' fehlt oder ist ungültig."
        # Nur erlaubte Zeichen in Modulnamen (keine Slashes/Punkte für Path-Traversal)
        if not all(c.isalnum() or c == "_" for c in modul):
            return False, f"Produkt {i}: 'modul_name' enthält ungültige Zeichen."

    return True, ""


def _imported(path: list, default):
    """Holt einen verschachtelten Wert aus der importierten Config."""
    cfg = st.session_state.get("_imported_config", {})
    for key in path:
        if isinstance(cfg, dict) and key in cfg:
            cfg = cfg[key]
        else:
            return default
    return cfg


def _safe_cast(value, target_type, default):
    """Castet einen Wert sicher in den Zieltyp. Bei Fehler wird default zurückgegeben."""
    if value is None:
        return default
    try:
        if target_type == "date":
            if isinstance(value, str):
                datetime.strptime(value, "%Y-%m-%d")
                return value
            return default
        elif target_type == "int":
            return int(float(value))
        elif target_type == "number":
            return float(value)
        elif target_type == "str":
            return str(value)
        return value
    except (ValueError, TypeError):
        return default


def _prod_param(modul: str, key: str, default, expected_type: str = None):
    """
    Holt einen Parameterwert aus dem importierten Produkt.
    Unterstützt verschachtelte Keys mit Punkt-Notation.
    Optional: Typ-Validierung via expected_type ('date', 'int', 'number', 'str').
    """
    cfg = st.session_state.get("_imported_config", {})
    for p in cfg.get("produkte", []):
        if p.get("modul_name") == modul and p.get("aktiviert", True):
            param = p.get("parameter", {})
            for part in key.split("."):
                if isinstance(param, dict) and part in param:
                    param = param[part]
                else:
                    return default
            if expected_type:
                return _safe_cast(param, expected_type, default)
            return param
    return default


def _prod_aktiv(modul: str, default: bool) -> bool:
    """
    Prüft, ob ein Produkt in der importierten Config aktiviert ist.
    Fehlendes 'aktiviert' = True (wie im CLI-Verhalten).
    """
    cfg = st.session_state.get("_imported_config", {})
    for p in cfg.get("produkte", []):
        if p.get("modul_name") == modul:
            val = p.get("aktiviert", True)
            return bool(val) if isinstance(val, (bool, int)) else default
    return default


def _get_toggle_map():
    """Baut die Toggle-Map dynamisch aus der Produkt-Registry auf."""
    from ui.produkt_registry import PRODUKTE
    return {p["modul_name"]: f"{p['modul_name']}_on" for p in PRODUKTE}


def _clear_import():
    """Löscht den Import-Cache und alle Toggle-Zustände, lädt die Seite neu."""
    st.session_state.pop("_imported_config", None)
    st.session_state.pop("config_uploader", None)
    st.session_state.pop("_toggles_need_sync", None)
    for key in _get_toggle_map().values():
        st.session_state.pop(key, None)
    # Profil-Widget-Keys zurücksetzen, damit Standardwerte greifen
    st.session_state.pop("profil_anzahl_kinder", None)
    for i in range(20):
        st.session_state.pop(f"kind_geburtsjahr_{i}", None)
    st.rerun()


def sync_toggles_with_session_state():
    """
    Schreibt die aktiviert/deaktiviert-Werte aus der importierten Config
    direkt in den Streamlit Session State.
    """
    if not st.session_state.get("_toggles_need_sync"):
        return

    for modul, key in _get_toggle_map().items():
        st.session_state[key] = _prod_aktiv(modul, False)

    st.session_state.pop("_toggles_need_sync", None)
