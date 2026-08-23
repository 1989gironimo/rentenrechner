"""Config-Import UI-Komponente mit Security-Checks."""

import streamlit as st
import json
from datetime import datetime
from utils.config import _clear_import, _validate_config_structure


_MAX_FILE_SIZE_MB = 1
_MAX_JSON_DEPTH = 10


def _check_json_depth(obj, depth=0):
    """Prüft die Verschachtelungstiefe eines JSON-Objekts."""
    if depth > _MAX_JSON_DEPTH:
        return False
    if isinstance(obj, dict):
        for v in obj.values():
            if not _check_json_depth(v, depth + 1):
                return False
    elif isinstance(obj, list):
        for item in obj:
            if not _check_json_depth(item, depth + 1):
                return False
    return True


def _apply_imported_profil_values(imported_cfg: dict):
    """Wendet importierte Profil-Werte direkt auf die Widget-Session-States an."""
    profil = imported_cfg.get("profil", {})

    # Anzahl Kinder
    anzahl = int(profil.get("anzahl_kinder", 0))
    st.session_state["profil_anzahl_kinder"] = anzahl

    # Geburtsjahre
    kinder = profil.get("kindergeburtsjahre", [])
    if not isinstance(kinder, list):
        kinder = []

    for i in range(20):
        key = f"kind_geburtsjahr_{i}"
        if i < anzahl and i < len(kinder):
            st.session_state[key] = int(kinder[i])
        else:
            st.session_state.pop(key, None)


def _flatten_dict(d, parent_key='', sep='.'):
    """Flacht verschachtelte Dictionaries (z.B. für Kosten) auf."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _apply_imported_produkt_values(imported_cfg: dict):
    """Schreibt importierte Produkt-Werte direkt in den Widget-State."""
    produkte = imported_cfg.get("produkte", [])
    
    for prod in produkte:
        modul = prod.get("modul_name")
        parameter = prod.get("parameter", {})
        if not modul:
            continue
        
        flache_parameter = _flatten_dict(parameter)
        
        for key, val in flache_parameter.items():
            # Erstellt exakt denselben Schlüssel, den produkte.py nutzt
            widget_key = f"{modul}_{key.replace('.', '_')}"
            
            # Text-Daten in echte Datumsobjekte umwandeln für st.date_input
            if isinstance(val, str):
                try:
                    val = datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            # Wert zwingend in den Session State schreiben
            st.session_state[widget_key] = val


def render_config_import():
    with st.expander("📁 Config.json importieren / zurücksetzen"):
        uploaded = st.file_uploader(
            "Bestehende `config.json` hochladen (max. 1 MB)",
            type=["json"],
            key="config_uploader"
        )

        if uploaded is not None:
            # Dateigröße prüfen
            if uploaded.size > _MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"❌ Datei zu groß. Maximal {_MAX_FILE_SIZE_MB} MB erlaubt.")
                return

            if st.button("📥 Import anwenden", width="stretch", key="btn_import"):
                try:
                    raw = uploaded.read()
                    # Nur UTF-8 erlauben
                    text = raw.decode("utf-8")
                    imported = json.loads(text)

                    # Tiefe prüfen
                    if not _check_json_depth(imported):
                        st.error(f"❌ JSON zu tief verschachtelt (max. {_MAX_JSON_DEPTH} Ebenen).")
                        return

                    # Struktur validieren
                    ok, msg = _validate_config_structure(imported)
                    if not ok:
                        st.error(f"❌ Ungültige Config-Struktur: {msg}")
                        return

                    # Importierte Config speichern und Widget-States sofort aktualisieren
                    st.session_state["_imported_config"] = imported
                    _apply_imported_profil_values(imported)
                    
                    # Neue Funktion aufrufen: Produkte synchronisieren
                    _apply_imported_produkt_values(imported)
                    
                    st.session_state["_toggles_need_sync"] = True
                    st.success("✅ Config importiert!")
                    st.rerun()

                except json.JSONDecodeError as e:
                    st.error(f"❌ Ungültiges JSON: {e}")
                except UnicodeDecodeError:
                    st.error("❌ Datei muss UTF-8 kodiert sein.")
                except Exception as e:
                    st.error(f"❌ Fehler beim Import: {e}")

        if st.session_state.get("_imported_config"):
            st.info("Aktuell sind importierte Werte aus einer `config.json` aktiv.")
            if st.button(
                "❌ Import zurücksetzen (Standardwerte laden)",
                width="stretch",
                key="btn_reset"
            ):
                _clear_import()