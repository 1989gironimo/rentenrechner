"""Generische Produkt-UI, die sich aus der Registry aufbaut."""

import streamlit as st
import pandas as pd
from datetime import date, datetime

from utils.config import _prod_param, _prod_aktiv, _get_toggle_map
from ui.produkt_registry import PRODUKTE


def _set_nested(d: dict, key: str, value):
    """Speichert einen Wert unter einem verschachtelten Key (Punkt-Notation)."""
    parts = key.split(".")
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


def _safe_date(value, default_str):
    """Parst ein Datum sicher. Bei Fehler wird der Default zurückgegeben."""
    if isinstance(value, str):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            pass

    return default_str


def _render_field(modul: str, field: dict, col):
    """Rendert ein einzelnes Feld aus der Registry."""
    key = field["key"]
    label = field["label"]
    ftype = field["type"]
    default = field["default"]
    help_text = field.get("help", "")
    widget_key = f"{modul}_{key.replace('.', '_')}"

    # Importierten Wert holen und typ-sicher casten
    if ftype == "date":
        imported_val = _prod_param(
            modul,
            key,
            default,
            expected_type="date",
        )

        dt_val = _safe_date(imported_val, default)

        with col:
            return st.date_input(
                label,
                value=datetime.strptime(dt_val, "%Y-%m-%d").date(),
                key=widget_key,
                help=help_text,
            )

    elif ftype == "int":
        imported_val = _prod_param(
            modul,
            key,
            default,
            expected_type="int",
        )

        with col:
            return st.number_input(
                label,
                min_value=field.get("min", 0),
                value=imported_val,
                step=field.get("step", 1),
                key=widget_key,
                help=help_text,
            )

    else:  # number (float)
        imported_val = _prod_param(
            modul,
            key,
            default,
            expected_type="number",
        )

        with col:
            return st.number_input(
                label,
                min_value=field.get("min", 0.0),
                value=imported_val,
                step=field.get("step", 0.1),
                key=widget_key,
                help=help_text,
            )


def render_produkte(brutto: float):
    st.header("📦 Vorsorgeprodukte")

    produkte_config = []
    toggle_map = _get_toggle_map()

    for prod in PRODUKTE:
        modul = prod["modul_name"]
        aktiv = _prod_aktiv(
            modul,
            prod["default_aktiv"],
        )
        toggle_key = toggle_map.get(
            modul,
            f"{modul}_on",
        )

        with st.expander(
            prod["display_name"],
            expanded=aktiv,
        ):
            toggle = st.toggle(
                "Aktivieren",
                value=aktiv,
                key=toggle_key,
            )

            if not toggle:
                continue

            if prod.get("brutto_from_profil"):
                st.info(
                    f"Bruttogehalt wird aus dem Profil übernommen: "
                    f"**{brutto:,.2f} €/Monat**"
                )

            fields = prod.get("fields", [])
            values = {}

            c1, c2 = st.columns(2)

            for i, field in enumerate(fields):
                col = c1 if i % 2 == 0 else c2
                val = _render_field(
                    modul,
                    field,
                    col,
                )
                values[field["key"]] = val

            kosten_values = {}

            if prod.get("has_kosten"):
                kosten_fields = prod.get(
                    "kosten_fields",
                    [],
                )

                c1, c2 = st.columns(2)

                for i, field in enumerate(kosten_fields):
                    col = c1 if i % 2 == 0 else c2
                    val = _render_field(
                        modul,
                        field,
                        col,
                    )
                    kosten_values[field["key"]] = val

            staffel = None

            if prod.get("has_staffel"):
                st.subheader("Beitragsstaffel")

                if prod.get("staffel_caption"):
                    st.caption(
                        prod["staffel_caption"]
                    )

                staffel_default = _prod_param(
                    modul,
                    "staffel_beitraege",
                    prod.get("staffel_default", []),
                )

                if not isinstance(staffel_default, list):
                    staffel_default = prod.get(
                        "staffel_default",
                        [],
                    )

                df_default = (
                    pd.DataFrame(staffel_default)
                    if staffel_default
                    else pd.DataFrame(
                        prod.get("staffel_default", [])
                    )
                )

                col_cfg = {}

                for sc in prod["staffel_columns"]:
                    cfg = {
                        "label": sc["label"]
                    }

                    if sc["type"] == "int":
                        cfg["min_value"] = sc.get(
                            "min",
                            0,
                        )
                        cfg["step"] = sc.get(
                            "step",
                            1,
                        )
                        col_cfg[sc["key"]] = (
                            st.column_config.NumberColumn(
                                **cfg
                            )
                        )
                    else:
                        cfg["min_value"] = sc.get(
                            "min",
                            0.0,
                        )
                        cfg["step"] = sc.get(
                            "step",
                            10.0,
                        )
                        col_cfg[sc["key"]] = (
                            st.column_config.NumberColumn(
                                **cfg
                            )
                        )

                staffel_df = st.data_editor(
                    df_default,
                    num_rows="dynamic",
                    column_config=col_cfg,
                    key=f"{modul}_staffel_editor",
                    use_container_width=True,
                )

                staffel = (
                    staffel_df.to_dict("records")
                    if not staffel_df.empty
                    else []
                )

            stufenplan = None

            if prod.get("has_stufenplan"):
                st.subheader("Stufenplan")

                if prod.get("stufenplan_caption"):
                    st.caption(
                        prod["stufenplan_caption"]
                    )

                stufen_default = _prod_param(
                    modul,
                    "stufenplan",
                    prod.get("stufenplan_default", []),
                )

                if not isinstance(stufen_default, list):
                    stufen_default = prod.get(
                        "stufenplan_default",
                        [],
                    )

                df_default = (
                    pd.DataFrame(stufen_default)
                    if stufen_default
                    else pd.DataFrame(
                        prod.get("stufenplan_default", [])
                    )
                )

                col_cfg = {}

                for sc in prod["stufenplan_columns"]:
                    cfg = {
                        "label": sc["label"]
                    }

                    if sc["type"] == "int":
                        cfg["min_value"] = sc.get(
                            "min",
                            1900,
                        )
                        cfg["step"] = sc.get(
                            "step",
                            1,
                        )
                        col_cfg[sc["key"]] = (
                            st.column_config.NumberColumn(
                                **cfg
                            )
                        )
                    else:
                        cfg["min_value"] = sc.get(
                            "min",
                            0.0,
                        )
                        cfg["max_value"] = sc.get(
                            "max",
                            100.0,
                        )
                        cfg["step"] = sc.get(
                            "step",
                            0.25,
                        )
                        col_cfg[sc["key"]] = (
                            st.column_config.NumberColumn(
                                **cfg
                            )
                        )

                stufen_df = st.data_editor(
                    df_default,
                    num_rows="dynamic",
                    column_config=col_cfg,
                    key=f"{modul}_stufen_editor",
                    use_container_width=True,
                )

                stufenplan = (
                    stufen_df.to_dict("records")
                    if not stufen_df.empty
                    else []
                )

            if prod.get("caption"):
                st.caption(prod["caption"])

            # Normale Felder in die Produktparameter übernehmen.
            # Streamlit st.date_input liefert datetime.date.
            # Die Produktklassen erwarten ISO-Strings.
            parameter = {}

            for k, v in values.items():
                if isinstance(v, (date, datetime)):
                    v = v.strftime("%Y-%m-%d")

                _set_nested(
                    parameter,
                    k,
                    v,
                )

            # Kostenparameter übernehmen.
            for k, v in kosten_values.items():
                if isinstance(v, (date, datetime)):
                    v = v.strftime("%Y-%m-%d")

                _set_nested(
                    parameter,
                    k,
                    v,
                )

            if staffel is not None:
                parameter["staffel_beitraege"] = staffel

            if stufenplan is not None:
                parameter["stufenplan"] = stufenplan

            parameter["abgaben_typ"] = prod.get(
                "abgaben_typ",
                "",
            )

            produkte_config.append(
                {
                    "modul_name": modul,
                    "klassen_name": prod["klassen_name"],
                    "aktiviert": True,
                    "parameter": parameter,
                }
            )

    return produkte_config
