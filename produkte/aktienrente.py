from datetime import datetime

from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from produkte.renten_basis import RentenProdukt

class StaatsfondsAktienrente(RentenProdukt):
    def __init__(self, 
                 start_datum: str = "2028-01-01",
                 stufenplan: list = None,
                 erwartete_rendite_prozent: float = 7.0,
                 kostenquote_prozent: float = 0.1,
                 startkapital: float = 0.0,
                 abgaben_typ: str = "gesetzlich",
                 entnahme_rate_prozent: float = 4.0,
                 rentenfaktor: float = None,
                 aktuelles_brutto_monat: float = None,
                 entnahme_dauer_monate: int = 300,
                 entnahmezins_p_a: float = 2.0):
        self.start_datum = start_datum
        self.erwartete_rendite_prozent = erwartete_rendite_prozent
        self.kosten_renditeminderung_prozent = kostenquote_prozent
        self.kostenquote_prozent = kostenquote_prozent
        self.startkapital = startkapital
        self.abgaben_typ = abgaben_typ
        self.entnahme_rate_prozent = entnahme_rate_prozent
        self.rentenfaktor = rentenfaktor
        self.aktuelles_brutto_monat = aktuelles_brutto_monat
        self.entnahme_dauer_monate = entnahme_dauer_monate
        self.entnahmezins_p_a = entnahmezins_p_a

        if stufenplan is not None:
            self.stufenplan = stufenplan
        else:
            self.stufenplan = [
                {"jahr": 2027, "an_prozent": 0.25, "ag_prozent": 0.25},
                {"jahr": 2028, "an_prozent": 0.50, "ag_prozent": 0.50},
                {"jahr": 2029, "an_prozent": 0.75, "ag_prozent": 0.75},
                {"jahr": 2030, "an_prozent": 1.00, "ag_prozent": 1.00}
            ]

    def name(self) -> str:
        return "Aktienrente / Staatsfonds (Schweden-Modell)"

    def _hole_prozentsaetze_fuer_jahr(self, kalenderjahr: int) -> tuple[float, float]:
        an_p, ag_p = 0.25, 0.25
        for stufe in sorted(self.stufenplan, key=lambda x: x["jahr"]):
            if kalenderjahr >= stufe["jahr"]:
                an_p = stufe.get("an_prozent", an_p)
                ag_p = stufe.get("ag_prozent", ag_p)
        return an_p, ag_p

    def _hole_brutto_fuer_jahr(self, kalenderjahr: int, profil) -> float:
        """Liest aktuelles Brutto und Gehaltssteigerung direkt aus dem NutzerProfil."""
        start_jahr = datetime.strptime(self.start_datum, "%Y-%m-%d").year if isinstance(self.start_datum, str) else self.start_datum.year
        jahre_diff = max(0, kalenderjahr - start_jahr)
        
        # Werte aus dem NutzerProfil beziehen (mit Sicherheits-Fallbacks)
        aktuelles_brutto = profil.aktuelles_brutto_monat if profil else 4000.0
        gehaltssteigerung = profil.gehaltssteigerung_prozent if profil else 2.0
        
        return aktuelles_brutto * ((1 + gehaltssteigerung / 100.0) ** jahre_diff)

    def berechne_monatliche_netto_eigenleistung(self, profil: NutzerProfil, steuer_rechner: SteuerRechner, datum: datetime = None) -> float:
        if datum is None:
            datum = datetime.strptime(self.start_datum, "%Y-%m-%d") if isinstance(self.start_datum, str) else self.start_datum

        brutto_aktuell = self._hole_brutto_fuer_jahr(datum.year, profil)
        an_p, _ = self._hole_prozentsaetze_fuer_jahr(datum.year)
        brutto_beitrag_an = brutto_aktuell * (an_p / 100.0)
        return steuer_rechner.berechne_nettoaufwand_entgeltumwandlung(
            profil.aktuelles_brutto_monat,
            brutto_beitrag_an,
            jahr=datum.year,
        )["nettoaufwand"]

    def berechne_monatliche_details(self, aktueller_monat: datetime, profil: NutzerProfil, steuer_rechner: SteuerRechner) -> tuple[float, float, float, float]:
        start_dt = datetime.strptime(self.start_datum, "%Y-%m-%d") if isinstance(self.start_datum, str) else self.start_datum
        if aktueller_monat < start_dt:
            return 0.0, 0.0, 0.0, 0.0

        brutto_aktuell = self._hole_brutto_fuer_jahr(aktueller_monat.year, profil)
        an_p, ag_p = self._hole_prozentsaetze_fuer_jahr(aktueller_monat.year)
        netto_eigenleistung = self.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner, aktueller_monat)
        ag_beitrag = brutto_aktuell * (ag_p / 100.0)
        brutto_beitrag_an = brutto_aktuell * (an_p / 100.0)
        gesamt_sparbeitrag = brutto_beitrag_an + ag_beitrag
        return netto_eigenleistung, ag_beitrag, 0.0, gesamt_sparbeitrag

    def berechne_endkapital_nominal(self, profil) -> float:
        renten_dt = datetime.strptime(profil.renteneintrittsdatum, "%Y-%m-%d") if isinstance(profil.renteneintrittsdatum, str) else profil.renteneintrittsdatum
        start_dt = datetime.strptime(self.start_datum, "%Y-%m-%d") if isinstance(self.start_datum, str) else self.start_datum

        if start_dt >= renten_dt:
            return float(self.startkapital)

        effektive_rendite_p_a = self.erwartete_rendite_prozent - self.kostenquote_prozent
        monats_zins = (1 + effektive_rendite_p_a / 100.0) ** (1 / 12.0) - 1.0

        kapital = float(self.startkapital)
        jahr, monat = start_dt.year, start_dt.month

        while datetime(jahr, monat, 1) < datetime(renten_dt.year, renten_dt.month, 1):
            brutto_aktuell = self._hole_brutto_fuer_jahr(jahr, profil)
            an_p, ag_p = self._hole_prozentsaetze_fuer_jahr(jahr)

            monatlicher_sparbeitrag = brutto_aktuell * ((an_p + ag_p) / 100.0)
            kapital = (kapital * (1.0 + monats_zins)) + monatlicher_sparbeitrag

            monat += 1
            if monat > 12:
                monat = 1
                jahr += 1

        return round(kapital, 2)

    def berechne_endkapital_real(self, profil, inflationsrate_prozent: float = None) -> float:
        if inflationsrate_prozent is None:
            inflationsrate_prozent = profil.inflation_prozent if profil else 2.0
        nominal = self.berechne_endkapital_nominal(profil)
        start_jahr = datetime.strptime(self.start_datum, "%Y-%m-%d").year if isinstance(self.start_datum, str) else self.start_datum.year
        renten_jahr = datetime.strptime(profil.renteneintrittsdatum, "%Y-%m-%d").year if isinstance(profil.renteneintrittsdatum, str) else profil.renteneintrittsdatum.year
        jahre = max(0, renten_jahr - start_jahr)
        return round(nominal / ((1 + inflationsrate_prozent / 100.0) ** jahre), 2)

    def berechne_brutto_nominal(self, profil, endkapital: float = None) -> float:
        if endkapital is None:
            endkapital = self.berechne_endkapital_nominal(profil)
        if getattr(self, "rentenfaktor", None) is not None and self.rentenfaktor > 0:
            return round((endkapital / 10000.0) * self.rentenfaktor, 2)
        
        entnahme_p_a = getattr(self, "entnahme_rate_prozent", 4.0)
        monatliche_rente = (endkapital * (entnahme_p_a / 100.0)) / 12.0
        return round(monatliche_rente, 2)

    def berechne_brutto_real(self, profil, inflationsrate_prozent: float = None) -> float:
        if inflationsrate_prozent is None:
            inflationsrate_prozent = profil.inflation_prozent if profil else 2.0
        brutto_nom = self.berechne_brutto_nominal(profil)
        start_jahr = datetime.strptime(self.start_datum, "%Y-%m-%d").year if isinstance(self.start_datum, str) else self.start_datum.year
        renten_jahr = datetime.strptime(profil.renteneintrittsdatum, "%Y-%m-%d").year if isinstance(profil.renteneintrittsdatum, str) else profil.renteneintrittsdatum.year
        jahre = max(0, renten_jahr - start_jahr)
        return round(brutto_nom / ((1 + inflationsrate_prozent / 100.0) ** jahre), 2)

    def berechne_netto_nominal(self, profil, steuer_rechner=None, endkapital: float = None) -> float:
        brutto_nom = self.berechne_brutto_nominal(profil, endkapital)
        if steuer_rechner is None:
            return round(brutto_nom * 0.80, 2)
        return steuer_rechner.berechne_netto_aus_brutto(brutto_nom, self.abgaben_typ)

    def berechne_netto_real(self, profil, steuer_rechner=None, inflationsrate_prozent: float = None) -> float:
        if inflationsrate_prozent is None:
            inflationsrate_prozent = profil.inflation_prozent if profil else 2.0
        netto_nom = self.berechne_netto_nominal(profil, steuer_rechner)
        start_jahr = datetime.strptime(self.start_datum, "%Y-%m-%d").year if isinstance(self.start_datum, str) else self.start_datum.year
        renten_jahr = datetime.strptime(profil.renteneintrittsdatum, "%Y-%m-%d").year if isinstance(profil.renteneintrittsdatum, str) else profil.renteneintrittsdatum.year
        jahre = max(0, renten_jahr - start_jahr)
        return round(netto_nom / ((1 + inflationsrate_prozent / 100.0) ** jahre), 2)