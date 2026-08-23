from produkte.renten_basis import RentenProdukt
from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from datetime import datetime

class BetriebsrentebAV(RentenProdukt):
    def __init__(self,
                 start_datum: str,
                 monatlicher_beitrag_mitarbeiter: float = 0.0,
                 arbeitgeber_zuschuss_prozent: float = 0.0,
                 erwartete_rendite_prozent: float = 0.0,
                 kostenquote_prozent: float = 0.0,
                 staffel_beitraege: list = None,
                 startkapital: float = 0.0,
                 startkapital_datum: str = None,
                 dynamik_prozent: float = 0.0,
                 abgaben_typ: str = "bav",
                 entnahme_dauer_monate: int = 300,
                 entnahmezins_p_a: float = 2.0):
        
        self.start_datum = start_datum
        self.monatlicher_beitrag_mitarbeiter = monatlicher_beitrag_mitarbeiter
        self.arbeitgeber_zuschuss_prozent = arbeitgeber_zuschuss_prozent
        self.erwartete_rendite_prozent = erwartete_rendite_prozent
        self.kostenquote_prozent = kostenquote_prozent
        self.staffel_beitraege = sorted(
            staffel_beitraege or [],
            key=lambda staffel: staffel.get("ab_jahr", 0),
        )
        self.startkapital = startkapital
        self.startkapital_datum = startkapital_datum
        self.dynamik_prozent = dynamik_prozent
        self.abgaben_typ = abgaben_typ
        self.entnahme_dauer_monate = entnahme_dauer_monate
        self.entnahmezins_p_a = entnahmezins_p_a

    def name(self) -> str:
        return "Betriebliche Altersvorsorge (bAV)"

    def _hole_beitrag_fuer_monat(self, jahre_seit_start: int) -> float:
        """Ermittelt den Mitarbeiter-Beitrag basierend auf Staffelbeiträgen (ab Jahr X) 
           oder greift auf den Standardbeitrag zurück."""
        if not self.staffel_beitraege:
            return self.monatlicher_beitrag_mitarbeiter
        
        aktiver_beitrag = self.monatlicher_beitrag_mitarbeiter
        # Sortiere nach Jahren, um den höchsten zutreffenden Schwellenwert zu finden
        for staffel in self.staffel_beitraege:
            if jahre_seit_start >= staffel.get("ab_jahr", 0):
                aktiver_beitrag = staffel.get("eigenbeitrag", staffel.get("monatlicher_beitrag", aktiver_beitrag))
                
        return aktiver_beitrag

    @property
    def gesamter_monatlicher_beitrag(self) -> float:
        # Gibt standardmäßig den initialen Beitrag aus (für die Übersicht im Report)
        beitrag = self._hole_beitrag_fuer_monat(0)
        zuschuss = beitrag * (self.arbeitgeber_zuschuss_prozent / 100)
        return beitrag + zuschuss

    def berechne_monatliche_netto_eigenleistung(self, profil: NutzerProfil, steuer_rechner: SteuerRechner, datum=None) -> float:
        """Berechnet die Netto-Belastung für den angegebenen Monat oder den Startmonat."""
        if datum is None:
            jahre_seit_start = 0
        else:
            start_dt = datetime.strptime(self.start_datum, "%Y-%m-%d") if isinstance(self.start_datum, str) else self.start_datum
            monate = (datum.year - start_dt.year) * 12 + (datum.month - start_dt.month)
            if datum.day < start_dt.day:
                monate -= 1
            jahre_seit_start = max(0, monate // 12)

        brutto_beitrag = self._hole_beitrag_fuer_monat(jahre_seit_start)
        if self.dynamik_prozent > 0 and jahre_seit_start > 0:
            brutto_beitrag *= (1 + self.dynamik_prozent / 100) ** jahre_seit_start

        return steuer_rechner.berechne_nettoaufwand_entgeltumwandlung(
            profil.aktuelles_brutto_monat,
            brutto_beitrag,
        )["nettoaufwand"]

    def berechne_monatliche_details(self, aktueller_monat: datetime, profil: NutzerProfil, steuer_rechner: SteuerRechner) -> tuple[float, float, float, float]:
        start_dt = datetime.strptime(self.start_datum, "%Y-%m-%d") if isinstance(self.start_datum, str) else self.start_datum
        if aktueller_monat < start_dt:
            return 0.0, 0.0, 0.0, 0.0

        monate = (aktueller_monat.year - start_dt.year) * 12 + (aktueller_monat.month - start_dt.month)
        if aktueller_monat.day < start_dt.day:
            monate -= 1
        jahre_seit_start = max(0, monate // 12)

        brutto_beitrag = self._hole_beitrag_fuer_monat(jahre_seit_start)
        if self.dynamik_prozent > 0 and jahre_seit_start > 0:
            brutto_beitrag *= (1 + self.dynamik_prozent / 100) ** jahre_seit_start

        ag_beitrag = brutto_beitrag * (self.arbeitgeber_zuschuss_prozent / 100)
        netto_eigenleistung = self.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner, aktueller_monat)
        gesamt_sparbeitrag = brutto_beitrag + ag_beitrag
        return netto_eigenleistung, ag_beitrag, 0.0, gesamt_sparbeitrag

    def berechne_netto_staffel(self, profil: NutzerProfil, steuer_rechner: SteuerRechner) -> list:
        """Gibt eine Liste von Dicts zurück mit (ab_jahr, netto_eigenleistung) für jede Staffel."""
        ergebnisse = []
        if not self.staffel_beitraege:
            netto = self.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner)
            return [{"ab_jahr": 0, "netto": netto}]
            
        ersparnis_faktor = (steuer_rechner.persoenlicher_steuersatz + steuer_rechner.kv_pv_satz_voll) / 100
        erfolgs_faktor = 1 - min(ersparnis_faktor, 0.55)
        
        for s in self.staffel_beitraege:
            jahr = s.get("ab_jahr", 0)
            brutto_beitrag = s.get("eigenbeitrag", s.get("monatlicher_beitrag", 0.0))
            netto_wert = max(brutto_beitrag * erfolgs_faktor, 0.0)
            ergebnisse.append({"ab_jahr": jahr, "netto": netto_wert})
            
        return ergebnisse

    def berechne_endkapital_nominal(self, profil: NutzerProfil) -> float:
        netto_rendite_p_a = self.erwartete_rendite_prozent - self.kostenquote_prozent
        monatlicher_zins = (1 + netto_rendite_p_a / 100) ** (1 / 12) - 1
        
        beitrags_start = self.start_datum
        if self.startkapital_datum and self.startkapital_datum > beitrags_start:
            beitrags_start = self.startkapital_datum
        monate_sparen = profil.berechne_monate_fuer_zeitraum(beitrags_start)
        if monate_sparen <= 0:
            return self.startkapital

        volle_jahre = int(monate_sparen // 12)
        rest_monate = int(monate_sparen % 12)
        
        kapital_laufend = 0.0
        
        for jahr in range(volle_jahre):
            basis_beitrag = self._hole_beitrag_fuer_monat(jahr)
            
            if self.dynamik_prozent > 0.0 and jahr > 0:
                for _ in range(jahr):
                    basis_beitrag *= (1 + self.dynamik_prozent / 100)
            
            ag_zuschuss = basis_beitrag * (self.arbeitgeber_zuschuss_prozent / 100)
            monatlicher_gesamtbeitrag = basis_beitrag + ag_zuschuss
            
            for _ in range(12):
                kapital_laufend = (kapital_laufend * (1 + monatlicher_zins)) + monatlicher_gesamtbeitrag

        if rest_monate > 0:
            aktuelles_jahr = volle_jahre
            basis_beitrag = self._hole_beitrag_fuer_monat(aktuelles_jahr)
            if self.dynamik_prozent > 0.0 and aktuelles_jahr > 0:
                for _ in range(aktuelles_jahr):
                    basis_beitrag *= (1 + self.dynamik_prozent / 100)
            
            ag_zuschuss = basis_beitrag * (self.arbeitgeber_zuschuss_prozent / 100)
            monatlicher_gesamtbeitrag = basis_beitrag + ag_zuschuss
            
            for _ in range(rest_monate):
                kapital_laufend = (kapital_laufend * (1 + monatlicher_zins)) + monatlicher_gesamtbeitrag
                
        endkapital_sparen = kapital_laufend

        endkapital_start = 0.0
        if self.startkapital > 0:
            if self.startkapital_datum:
                monate_startkapital = profil.berechne_monate_fuer_zeitraum(self.startkapital_datum)
            else:
                monate_startkapital = monate_sparen
            
            if monate_startkapital > 0:
                endkapital_start = self.startkapital * ((1 + monatlicher_zins) ** monate_startkapital)
            else:
                endkapital_start = self.startkapital

        return endkapital_start + endkapital_sparen

    def berechne_brutto_nominal(self, profil: NutzerProfil, endkapital: float = None) -> float:
        if endkapital is None:
            endkapital = self.berechne_endkapital_nominal(profil)
        if endkapital <= 0:
            return 0.0
            
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
        return steuer_rechner.berechne_netto_aus_brutto(brutto, self.abgaben_typ)