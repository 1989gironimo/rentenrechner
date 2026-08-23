from datetime import datetime
from produkte.renten_basis import RentenProdukt
from core.profil import NutzerProfil
from core.steuern import SteuerRechner

class Unterstuetzungskasse(RentenProdukt):
    def __init__(self,
                 start_datum: str,
                 staffel_beitraege: list,
                 beschaeftigungs_start_datum: str = None,
                 jahre_beschaeftigung_bisher: int = 0,
                 erwartete_rendite_prozent: float = 4.5,
                 kosten: dict = None,                      
                 kosten_renditeminderung_prozent: float = 0.0,
                 kosten_beitrag_prozent: float = 0.0,
                 fixe_verwaltungskosten_monat: float = 0.0,
                 psvag_promille: float = 0.0,
                 startkapital: float = 0.0,
                 abgaben_typ: str = "bav",
                 entnahme_dauer_monate: int = 300,
                 entnahmezins_p_a: float = 2.0):

        self.start_datum = start_datum
        self.staffel_beitraege = sorted(
            staffel_beitraege,
            key=lambda staffel: staffel.get("ab_jahr", 0),
        )
        self.erwartete_rendite_prozent = erwartete_rendite_prozent
        self.startkapital = startkapital
        self.abgaben_typ = abgaben_typ
        self.entnahme_dauer_monate = entnahme_dauer_monate
        self.entnahmezins_p_a = entnahmezins_p_a

        if kosten is not None:
            self.kosten_renditeminderung_prozent = kosten.get("renditeminderung_prozent", 0.0)
            self.kosten_beitrag_prozent = kosten.get("beitrag_prozent", 0.0)
            self.fixe_verwaltungskosten_monat = kosten.get("fix_monatlich", 0.0)
            self.psvag_promille_info = kosten.get("psvag_promille", 0.0)
        else:
            self.kosten_renditeminderung_prozent = kosten_renditeminderung_prozent
            self.kosten_beitrag_prozent = kosten_beitrag_prozent
            self.fixe_verwaltungskosten_monat = fixe_verwaltungskosten_monat
            self.psvag_promille_info = psvag_promille

        if beschaeftigungs_start_datum:
            self.jahre_beschaeftigung_bisher = self._berechne_initiale_jahre(start_datum, beschaeftigungs_start_datum)
        else:
            self.jahre_beschaeftigung_bisher = jahre_beschaeftigung_bisher

    def name(self) -> str:
        return "Unterstützungskasse (U-Kasse)"

    def _berechne_initiale_jahre(self, start_datum: str, beschaeftigungs_start_datum: str) -> int:
        d_beschaeftigung = datetime.fromisoformat(beschaeftigungs_start_datum)
        d_start = datetime.fromisoformat(start_datum)

        if d_start < d_beschaeftigung:
            return 0

        jahre = d_start.year - d_beschaeftigung.year
        if (d_start.month, d_start.day) < (d_beschaeftigung.month, d_beschaeftigung.day):
            jahre -= 1
        return jahre

    def _hole_beitraege_fuer_jahre(self, jahre: int) -> tuple:
        eigenbeitrag = 50.0
        ag_beitrag = 50.0

        for stufe in self.staffel_beitraege:
            if jahre >= stufe.get("ab_jahr", 0):
                eigenbeitrag = stufe.get("eigenbeitrag", eigenbeitrag)
                ag_beitrag = stufe.get("ag_beitrag", ag_beitrag)

        return eigenbeitrag, ag_beitrag

    def _hole_aktuelle_beitraege(self) -> tuple:
        return self._hole_beitraege_fuer_jahre(self.jahre_beschaeftigung_bisher)

    @property
    def gesamter_monatlicher_beitrag(self) -> float:
        eigen, ag = self._hole_aktuelle_beitraege()
        return eigen + ag

    def berechne_monatliche_netto_eigenleistung(self, profil: NutzerProfil, steuer_rechner: SteuerRechner, datum=None) -> float:
        if datum is None:
            jahre = self.jahre_beschaeftigung_bisher
        else:
            start_dt = datetime.fromisoformat(self.start_datum)
            monate = (datum.year - start_dt.year) * 12 + (datum.month - start_dt.month)
            if datum.day < start_dt.day:
                monate -= 1
            jahre_seit_start = max(0, monate // 12)
            jahre = self.jahre_beschaeftigung_bisher + jahre_seit_start

        eigenbeitrag, _ = self._hole_beitraege_fuer_jahre(jahre)
        return steuer_rechner.berechne_nettoaufwand_entgeltumwandlung(
            profil.aktuelles_brutto_monat,
            eigenbeitrag,
        )["nettoaufwand"]

    def berechne_monatliche_details(self, aktueller_monat: datetime, profil: NutzerProfil, steuer_rechner: SteuerRechner) -> tuple[float, float, float, float]:
        start_dt = datetime.fromisoformat(self.start_datum)
        if aktueller_monat < start_dt:
            return 0.0, 0.0, 0.0, 0.0

        monate = (aktueller_monat.year - start_dt.year) * 12 + (aktueller_monat.month - start_dt.month)
        if aktueller_monat.day < start_dt.day:
            monate -= 1
        jahre_seit_start = max(0, monate // 12)

        jahre = self.jahre_beschaeftigung_bisher + jahre_seit_start
        eigenbeitrag, ag_beitrag = self._hole_beitraege_fuer_jahre(jahre)
        netto_eigenleistung = self.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner, aktueller_monat)
        brutto_monats_beitrag = eigenbeitrag + ag_beitrag
        beitragskosten = brutto_monats_beitrag * (self.kosten_beitrag_prozent / 100.0)
        gesamt_sparbeitrag = max(
            0.0,
            brutto_monats_beitrag - beitragskosten - self.fixe_verwaltungskosten_monat,
        )
        return netto_eigenleistung, ag_beitrag, 0.0, gesamt_sparbeitrag

    def berechne_netto_staffel(self, profil: NutzerProfil, steuer_rechner: SteuerRechner) -> list:
        ergebnisse = []
        if not self.staffel_beitraege:
            netto = self.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner)
            return [{"ab_jahr": 0, "netto": netto}]

        ersparnis_faktor = (steuer_rechner.persoenlicher_steuersatz + steuer_rechner.kv_pv_satz_voll) / 100
        erfolgs_faktor = 1 - min(ersparnis_faktor, 0.55)

        for stufe in self.staffel_beitraege:
            jahr = stufe.get("ab_jahr", 0)
            eigenbeitrag = stufe.get("eigenbeitrag", 50.0)
            netto_wert = max(eigenbeitrag * erfolgs_faktor, 0.0)
            ergebnisse.append({"ab_jahr": jahr, "netto": netto_wert})

        return ergebnisse

    def berechne_endkapital_nominal(self, profil: NutzerProfil) -> float:
        monate = profil.berechne_monate_fuer_zeitraum(self.start_datum)
        if monate <= 0:
            return self.startkapital

        netto_rendite_p_a = max(0.0, self.erwartete_rendite_prozent - self.kosten_renditeminderung_prozent)
        monatlicher_zins = (1 + netto_rendite_p_a / 100) ** (1 / 12) - 1

        kapital = self.startkapital
        aktuelle_jahre = self.jahre_beschaeftigung_bisher

        for m in range(1, int(monate) + 1):
            if m > 1 and (m - 1) % 12 == 0:
                aktuelle_jahre += 1

            eigen, ag = self._hole_beitraege_fuer_jahre(aktuelle_jahre)
            brutto_monats_beitrag = eigen + ag

            beitragskosten_prozentual = brutto_monats_beitrag * (self.kosten_beitrag_prozent / 100.0)
            gesamt_monats_kosten = beitragskosten_prozentual + self.fixe_verwaltungskosten_monat

            netto_monats_beitrag = max(0.0, brutto_monats_beitrag - gesamt_monats_kosten)

            kapital = (kapital * (1 + monatlicher_zins)) + netto_monats_beitrag

        return max(0.0, kapital)

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