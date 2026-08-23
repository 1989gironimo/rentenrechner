from datetime import datetime

from produkte.renten_basis import RentenProdukt
from core.profil import NutzerProfil
from core.steuern import SteuerRechner

class ETFSparplan(RentenProdukt):
    def __init__(self,
                 start_datum: str,
                 monatlicher_sparplan: float,
                 erwartete_rendite_prozent: float = 7.0,
                 kostenquote_prozent: float = 0.2,
                 startkapital: float = 0.0,
                 abgaben_typ: str = "etf",
                 entnahme_dauer_monate: int = 300,
                 entnahmezins_p_a: float = 3.0):
        
        self.start_datum = start_datum
        self.monatlicher_sparplan = monatlicher_sparplan
        self.erwartete_rendite_prozent = erwartete_rendite_prozent
        self.kostenquote_prozent = kostenquote_prozent
        self.startkapital = startkapital
        self.abgaben_typ = abgaben_typ
        self.entnahme_dauer_monate = entnahme_dauer_monate
        self.entnahmezins_p_a = entnahmezins_p_a

    def name(self) -> str:
        return "Privater ETF-Sparplan"

    def berechne_endkapital_nominal(self, profil: NutzerProfil) -> float:
        monate = profil.berechne_monate_fuer_zeitraum(self.start_datum)
        if monate <= 0:
            return self.startkapital

        netto_rendite_p_a = self.erwartete_rendite_prozent - self.kostenquote_prozent
        monatlicher_zins = (1 + netto_rendite_p_a / 100) ** (1 / 12) - 1

        endkapital_start = self.startkapital * ((1 + monatlicher_zins) ** monate)

        if monatlicher_zins == 0:
            endkapital_sparen = self.monatlicher_sparplan * monate
        else:
            endkapital_sparen = self.monatlicher_sparplan * (((1 + monatlicher_zins) ** monate - 1) / monatlicher_zins)

        return endkapital_start + endkapital_sparen

    def berechne_brutto_nominal(self, profil: NutzerProfil, endkapital: float = None) -> float:
        if endkapital is None:
            endkapital = self.berechne_endkapital_nominal(profil)
        if endkapital <= 0:
            return 0.0
            
        # Wir nehmen an, das angesparte Kapital wird in der Rente über 300 Monate (25 Jahre) entnommen
        renten_monate = self.entnahme_dauer_monate
        renten_zins = (1 + self.entnahmezins_p_a / 100 / 12) - 1
        
        if renten_zins == 0:
            return endkapital / renten_monate
            
        return endkapital * (renten_zins * (1 + renten_zins)**renten_monate) / ((1 + renten_zins)**renten_monate - 1)

    def berechne_netto_nominal(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
        endkapital: float = None,
    ) -> float:
        brutto = self.berechne_brutto_nominal(profil, endkapital)
        kapital = self.berechne_endkapital_nominal(profil) if endkapital is None else endkapital
        anschaffungskosten = self.startkapital + (
            self.monatlicher_sparplan
            * profil.berechne_monate_fuer_zeitraum(self.start_datum)
        )
        return self._berechne_netto_aus_entnahmeplan(
            kapital,
            anschaffungskosten,
            steuer_rechner,
            brutto,
        )

    def _berechne_netto_aus_entnahmeplan(
        self,
        kapital: float,
        anschaffungskosten: float,
        steuer_rechner: SteuerRechner,
        brutto_monatlich: float,
    ) -> float:
        """Besteuert nur den Gewinnanteil der monatlichen ETF-Entnahmen."""
        if kapital <= 0 or brutto_monatlich <= 0:
            return 0.0

        entnahmezins = (1 + self.entnahmezins_p_a / 100 / 12) - 1
        restkapital = kapital
        restbasis = min(max(0.0, anschaffungskosten), kapital)
        netto_summe = 0.0
        jahresgewinn = 0.0
        jahresauszahlung = 0.0

        for monat in range(1, self.entnahme_dauer_monate + 1):
            gewinnanteil = max(0.0, restkapital - restbasis)
            anteil = gewinnanteil / restkapital if restkapital > 0 else 0.0
            gewinn_auf_entnahme = brutto_monatlich * anteil
            jahresgewinn += gewinn_auf_entnahme
            jahresauszahlung += brutto_monatlich

            restkapital = max(0.0, restkapital * (1 + entnahmezins) - brutto_monatlich)
            restbasis = max(0.0, restbasis - brutto_monatlich * (1 - anteil))

            if monat % 12 == 0 or monat == self.entnahme_dauer_monate:
                steuer = steuer_rechner.berechne_kapitalertragsteuer(jahresgewinn)
                netto_summe += jahresauszahlung - steuer
                jahresgewinn = 0.0
                jahresauszahlung = 0.0

        return netto_summe / self.entnahme_dauer_monate

    def berechne_monatliche_details(
        self,
        aktueller_monat: datetime,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
    ) -> tuple[float, float, float, float]:
        start_dt = datetime.fromisoformat(self.start_datum)
        if aktueller_monat < start_dt:
            return 0.0, 0.0, 0.0, 0.0
        return self.monatlicher_sparplan, 0.0, 0.0, self.monatlicher_sparplan

    def berechne_monatliche_netto_eigenleistung(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
        aktueller_monat: datetime = None,
    ) -> float:
        return self.monatlicher_sparplan