"""Streamlit Web-App für den Rentenrechner."""

import streamlit as st
from ui.import_config import render_config_import
from ui.export_config import render_config_export
from ui.sidebar import render_sidebar
from ui.produkte import render_produkte
from ui.ergebnis import render_ergebnis
from utils.config import sync_toggles_with_session_state

st.set_page_config(page_title="Rentenrechner", layout="wide")
st.title("Rentenrechner")
st.markdown("Modulare Simulation deiner Altersvorsorge")

with st.expander("ℹ️ Hinweise zu Einheiten und Annahmen"):
    st.markdown("""
    - **Geldbeträge:** Euro  
    - **`*_monat`:** Euro pro Monat  
    - **`*_jahr`:** Euro pro Jahr  
    - **`*_prozent`:** Prozent pro Jahr (z. B. `5.0` = **5 %**, nicht 0,05)  
    - **`*_datum`:** Datum im Format `YYYY-MM-DD`  
    - Alle Ergebnisse sind **Modellrechnungen**.
    """)

render_config_import()

# WICHTIG: Toggles mit importierter Config synchronisieren, BEVOR die Widgets gerendert werden
sync_toggles_with_session_state()

profil_values = render_sidebar()
produkte_config = render_produkte(profil_values["brutto"])

# Export der aktuellen Eingaben (vor der Berechnung)
render_config_export(profil_values, produkte_config)

render_ergebnis(profil_values, produkte_config)
