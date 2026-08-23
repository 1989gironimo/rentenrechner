from abc import ABC, abstractmethod
from datetime import datetime
import inspect
from typing import Tuple

from core.profil import NutzerProfil
from core.steuern import SteuerRechner

class RentenProdukt(ABC):
    is_gesetzlich = False

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def berechne_brutto_nominal(
        self,
        profil: NutzerProfil,
        endkapital: float = None,
    ) -> float:
        pass

    @abstractmethod
    def berechne_netto_nominal(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
        endkapital: float = None,
    ) -> float:
        pass

    @abstractmethod
    def berechne_endkapital_nominal(self, profil: NutzerProfil) -> float:
        pass

    def berechne_monatliche_details(
        self,
        aktueller_monat: datetime,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
    ) -> Tuple[float, float, float, float]:
        start_datum = getattr(self, "start_datum", None)
        if isinstance(start_datum, str):
            try:
                start_datum = datetime.strptime(start_datum, "%Y-%m-%d")
            except ValueError:
                start_datum = None

        if start_datum is not None and aktueller_monat < start_datum:
            return 0.0, 0.0, 0.0, 0.0

        netto_methode = self.berechne_monatliche_netto_eigenleistung
        if len(inspect.signature(netto_methode).parameters) >= 3:
            netto_eigenleistung = netto_methode(profil, steuer_rechner, aktueller_monat)
        else:
            netto_eigenleistung = self.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner)

        basisbeitrag = float(
            getattr(self, "monatlicher_beitrag_mitarbeiter",
                    getattr(self, "monatlicher_eigenbeitrag",
                            getattr(self, "monatlicher_sparplan", 0.0)))
        )

        if hasattr(self, "_hole_aktuelle_beitraege"):
            eigenbeitrag, ag_beitrag = self._hole_aktuelle_beitraege()
            if basisbeitrag == 0.0:
                basisbeitrag = eigenbeitrag
        elif hasattr(self, "arbeitgeber_zuschuss_prozent"):
            ag_beitrag = basisbeitrag * (self.arbeitgeber_zuschuss_prozent / 100.0)
        else:
            ag_beitrag = 0.0

        if hasattr(self, "berechne_monatliche_foerderung"):
            foerder_methode = self.berechne_monatliche_foerderung
            if len(inspect.signature(foerder_methode).parameters) >= 1:
                staatliche_foerderung = foerder_methode(aktueller_monat)
            else:
                staatliche_foerderung = self.berechne_monatliche_foerderung()
        else:
            staatliche_foerderung = 0.0

        if hasattr(self, "berechne_monatlichen_sparbeitrag"):
            spar_methode = self.berechne_monatlichen_sparbeitrag
            if len(inspect.signature(spar_methode).parameters) >= 1:
                gesamt_sparbeitrag = spar_methode(aktueller_monat)
            else:
                gesamt_sparbeitrag = self.berechne_monatlichen_sparbeitrag()
        else:
            gesamt_sparbeitrag = basisbeitrag + ag_beitrag + staatliche_foerderung

        return netto_eigenleistung, ag_beitrag, staatliche_foerderung, gesamt_sparbeitrag

    def berechne_monatliche_sparbelastung_am_ende(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
    ) -> float:
        """Berechnet die letzte Monatsbelastung vor Renteneintritt über die Produktdetails."""
        start_datum = getattr(self, "start_datum", None)
        if isinstance(start_datum, str):
            try:
                start_datum = datetime.strptime(start_datum, "%Y-%m-%d").date()
            except ValueError:
                start_datum = None
        elif isinstance(start_datum, datetime):
            start_datum = start_datum.date()
        elif hasattr(start_datum, "date"):
            start_datum = start_datum.date()

        renten_dt = profil._renteneintrittsdatum_obj
        if start_datum is not None and renten_dt <= start_datum:
            return 0.0

        if renten_dt.month == 1:
            letzter_beitragsmonat = datetime(renten_dt.year - 1, 12, 1)
        else:
            letzter_beitragsmonat = datetime(renten_dt.year, renten_dt.month - 1, 1)

        if start_datum is not None and letzter_beitragsmonat.date() < start_datum:
            return 0.0

        try:
            netto, *_ = self.berechne_monatliche_details(letzter_beitragsmonat, profil, steuer_rechner)
            return netto
        except TypeError:
            return self.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner)
