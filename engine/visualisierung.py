"""
Visualisierungsmodul für Kapitalverläufe im Rentenrechner.

Berechnet monatliche Kapitalstände aller aktivierten Produkte
und stellt sie als Liniengraphen dar (matplotlib + Streamlit).
"""

from datetime import datetime
from typing import List
import pandas as pd

from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from engine.aggregator import RentenAggregator
from produkte.renten_basis import RentenProdukt


class KapitalVerlauf:
    """
    Berechnet und visualisiert die monatliche Kapitalentwicklung
    aller Vorsorgeprodukte bis zum Renteneintritt.
    """

    def __init__(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
        produkte: List[RentenProdukt],
    ):
        self.profil = profil
        self.steuer_rechner = steuer_rechner
        # Temporärer Aggregator für die Projektion
        self._aggregator = RentenAggregator(profil=profil, steuer_rechner=steuer_rechner)
        for p in produkte:
            self._aggregator.produkt_hinzufuegen(p)

    def berechne_verlauf(self) -> pd.DataFrame:
        """
        Berechnet den Kapitalverlauf für alle Produkte monatlich.

        Returns:
            pd.DataFrame mit Spalten: Datum, Produktname, Kapitalstand
        """
        df = self._aggregator.berechne_monatliche_projektion()
        if df.empty:
            return pd.DataFrame(columns=["datum", "produkt", "kapital"])

        # Gesamt-Kapital pro Monat berechnen
        monatlich = df.groupby(["datum", "produkt"])["kapital"].last().reset_index()

        # Gesamt pro Monat hinzufügen
        gesamt = df.groupby("datum")["kapital"].sum().reset_index()
        gesamt["produkt"] = "Gesamt"
        gesamt = gesamt[["datum", "produkt", "kapital"]]

        return pd.concat([monatlich, gesamt], ignore_index=True)

    def als_dataframe_breit(self) -> pd.DataFrame:
        """
        Wandelt den Verlauf in ein breites DataFrame um (Datum als Index,
        Produkte als Spalten). Praktisch für externe Plotting-Libraries.
        """
        df = self.berechne_verlauf()
        if df.empty:
            return df
        return df.pivot(index="datum", columns="produkt", values="kapital").reset_index()

    def plot_matplotlib(self, dateiname: str = "kapitalverlauf.png",
                        titel: str = "Kapitalverlauf der Vorsorgeprodukte"):
        """
        Erzeugt einen Liniengraphen mit matplotlib und speichert ihn.
        Für Standalone-Nutzung ohne Streamlit.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib ist erforderlich. Installiere mit: pip install matplotlib")

        df = self.als_dataframe_breit()
        if df.empty:
            print("Keine Daten zum Plotten vorhanden.")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        spalten = [c for c in df.columns if c not in ("datum", "Gesamt")]
        if "Gesamt" in df.columns:
            spalten.append("Gesamt")

        for col in spalten:
            if col == "Gesamt":
                ax.plot(df["datum"], df[col], label=col, linewidth=2.5,
                       linestyle="--", color="#FF9500")
            else:
                ax.plot(df["datum"], df[col], label=col, linewidth=1.5)

        ax.set_xlabel("Jahr")
        ax.set_ylabel("Kapital (€)")
        ax.set_title(titel)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x/1e6:.1f} Mio" if abs(x) >= 1e6 else f"{x/1e3:.0f}k" if abs(x) >= 1e3 else f"{x:.0f}")
        )
        plt.tight_layout()
        plt.savefig(dateiname, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"✅ Graph gespeichert unter '{dateiname}'")

    def plot_streamlit(self, titel: str = "Kapitalverlauf der Vorsorgeprodukte"):
        """
        Gibt einen Plotly-Graphen zurück, der direkt in Streamlit
        mit st.plotly_chart() angezeigt werden kann.
        """
        try:
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError("plotly ist erforderlich. Installiere mit: pip install plotly")

        df = self.als_dataframe_breit()
        if df.empty:
            return None

        fig = go.Figure()

        spalten = [c for c in df.columns if c not in ("datum", "Gesamt")]

        for col in spalten:
            fig.add_trace(go.Scatter(
                x=df["datum"], y=df[col],
                name=col,
                line=dict(width=2),
                hovertemplate="%{y:,.0f} €<extra>" + col + "</extra>",
            ))

        if "Gesamt" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["datum"], y=df["Gesamt"],
                name="Gesamt",
                line=dict(width=3, dash="dash", color="#FF9500"),
                hovertemplate="%{y:,.0f} €<extra>Gesamt</extra>",
            ))

        fig.update_layout(
            title=titel,
            xaxis_title="Jahr",
            yaxis_title="Kapital (€)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            template="plotly_white",
            height=500,
        )

        fig.update_yaxes(tickformat=",.0f")

        return fig
