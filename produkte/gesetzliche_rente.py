from datetime import date

from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from produkte.renten_basis import RentenProdukt


class GesetzlicheRente(RentenProdukt):
    """
    Vereinfachtes GRV-Szenariomodell.
    """

    def __init__(
        self,
        aktuelle_rentenansprueche: float,
        rentenanpassung_prozent: float = 1.5,
        abgaben_typ: str = "gesetzlich",
        durchschnittsentgelt_wachstum_prozent: float | None = None,
        rv_bbg_wachstum_prozent: float | None = None,
        aktueller_rentenwert: float = 42.52,
        durchschnittsentgelt: float = 51944.0,
        rv_bbg_jahr: float = 101400.0
    ):
        self.aktuelle_rentenansprueche = aktuelle_rentenansprueche
        self.rentenanpassung_prozent = rentenanpassung_prozent
        self.abgaben_typ = abgaben_typ

        self.durchschnittsentgelt_wachstum_prozent = durchschnittsentgelt_wachstum_prozent
        self.rv_bbg_wachstum_prozent = rv_bbg_wachstum_prozent
        
        # Konfigurierbare Basiswerte mit Defaults für 2026
        self.aktueller_rentenwert = aktueller_rentenwert
        self.durchschnittsentgelt = durchschnittsentgelt
        self.rv_bbg_jahr = rv_bbg_jahr

        self._letztes_detail = {}

    def name(self) -> str:
        return "Gesetzliche Rentenversicherung (GRV)"

    def _modell_stichtag(self) -> date:
        return date.today()

    def _jahre_bis_rente(self, profil: NutzerProfil) -> float:
        delta = (profil._renteneintrittsdatum_obj - self._modell_stichtag()).days
        return max(0.0, delta / 365.25)

    def _durchschnittsentgelt_wachstum(self, profil: NutzerProfil) -> float:
        if self.durchschnittsentgelt_wachstum_prozent is not None:
            return self.durchschnittsentgelt_wachstum_prozent
        return profil.inflation_prozent

    def _rv_bbg_wachstum(self, profil: NutzerProfil) -> float:
        if self.rv_bbg_wachstum_prozent is not None:
            return self.rv_bbg_wachstum_prozent
        return self._durchschnittsentgelt_wachstum(profil)

    def _durchschnittsentgelt_fuer_jahr(self, jahr: int, profil: NutzerProfil) -> float:
        startjahr = self._modell_stichtag().year
        jahre = max(0, jahr - startjahr)
        wachstum = self._durchschnittsentgelt_wachstum(profil)
        return self.durchschnittsentgelt * ((1 + wachstum / 100.0) ** jahre)

    def _rv_bbg_fuer_jahr(self, jahr: int, profil: NutzerProfil) -> float:
        startjahr = self._modell_stichtag().year
        jahre = max(0, jahr - startjahr)
        wachstum = self._rv_bbg_wachstum(profil)
        return self.rv_bbg_jahr * ((1 + wachstum / 100.0) ** jahre)

    def _rentenwert_zum_rentenbeginn(self, profil: NutzerProfil) -> float:
        jahre = self._jahre_bis_rente(profil)
        return self.aktueller_rentenwert * ((1 + self.rentenanpassung_prozent / 100.0) ** jahre)

    def _bestehende_entgeltpunkte(self) -> float:
        if self.aktuelle_rentenansprueche <= 0:
            return 0.0
        return self.aktuelle_rentenansprueche / self.aktueller_rentenwert

    def _monatliches_brutto_fuer_jahr(self, jahr: int, profil: NutzerProfil) -> float:
        startjahr = self._modell_stichtag().year
        jahre = max(0, jahr - startjahr)
        return profil.aktuelles_brutto_monat * ((1 + profil.gehaltssteigerung_prozent / 100.0) ** jahre)

    def _zusaetzliche_entgeltpunkte_fuer_jahr(self, jahr: int, profil: NutzerProfil) -> float:
        monatsbrutto = self._monatliches_brutto_fuer_jahr(jahr, profil)
        jahresbrutto = monatsbrutto * 12.0
        rv_bbg = self._rv_bbg_fuer_jahr(jahr, profil)
        durchschnittsentgelt = self._durchschnittsentgelt_fuer_jahr(jahr, profil)
        beitragspflichtiges_entgelt = min(jahresbrutto, rv_bbg)
        return beitragspflichtiges_entgelt / durchschnittsentgelt

    def _berechne_zukuenftige_entgeltpunkte(self, profil: NutzerProfil) -> float:
        start = self._modell_stichtag()
        rente = profil._renteneintrittsdatum_obj

        if rente <= start:
            return 0.0

        gesamt_ep = 0.0
        jahr = start.year

        while jahr <= rente.year:
            start_monat = start.month if jahr == start.year else 1
            end_monat = rente.month if jahr == rente.year else 12
            monate = end_monat - start_monat + 1

            if monate <= 0:
                jahr += 1
                continue

            jahres_ep = self._zusaetzliche_entgeltpunkte_fuer_jahr(jahr, profil)
            anteil = monate / 12.0
            gesamt_ep += jahres_ep * anteil
            jahr += 1

        return gesamt_ep

    def _berechne_grv_details(self, profil: NutzerProfil) -> dict:
        bestehende_ep = self._bestehende_entgeltpunkte()
        zusaetzliche_ep = self._berechne_zukuenftige_entgeltpunkte(profil)
        gesamt_ep = bestehende_ep + zusaetzliche_ep
        rentenwert = self._rentenwert_zum_rentenbeginn(profil)
        bestehende_rente_zukunft = bestehende_ep * rentenwert
        zusaetzliche_rente_zukunft = zusaetzliche_ep * rentenwert
        gesamt_rente = bestehende_rente_zukunft + zusaetzliche_rente_zukunft
        stichtag = self._modell_stichtag()

        monate_bis_rente = max(
            0,
            ((profil._renteneintrittsdatum_obj.year - stichtag.year) * 12 + 
             (profil._renteneintrittsdatum_obj.month - stichtag.month)),
        )

        return {
            "bestehende_entgeltpunkte": bestehende_ep,
            "zusaetzliche_entgeltpunkte": zusaetzliche_ep,
            "gesamt_entgeltpunkte": gesamt_ep,
            "rentenwert_heute": self.aktueller_rentenwert,
            "rentenwert_rentenbeginn": rentenwert,
            "bestehende_rente_rentenbeginn": bestehende_rente_zukunft,
            "zusaetzliche_rente_rentenbeginn": zusaetzliche_rente_zukunft,
            "brutto_rentenbeginn": gesamt_rente,
            "jahre_bis_rente": self._jahre_bis_rente(profil),
            "monate_bis_rente": monate_bis_rente,
        }

    def berechne_brutto_nominal(self, profil: NutzerProfil, endkapital: float = None) -> float:
        details = self._berechne_grv_details(profil)
        self._letztes_detail = details
        return round(details["brutto_rentenbeginn"], 2)

    def berechne_netto_nominal(self, profil: NutzerProfil, steuer_rechner: SteuerRechner, endkapital: float = None) -> float:
        brutto = self.berechne_brutto_nominal(profil, endkapital)
        return steuer_rechner.berechne_netto_aus_brutto(brutto, self.abgaben_typ)

    def berechne_endkapital_nominal(self, profil: NutzerProfil) -> float:
        return 0.0

    def berechne_monatliche_netto_eigenleistung(self, profil: NutzerProfil, steuer_rechner: SteuerRechner) -> float:
        return 0.0

    def berechne_details(self, profil: NutzerProfil) -> dict:
        details = self._berechne_grv_details(profil)
        self._letztes_detail = details
        return details