from datetime import datetime
import warnings
from typing import List, Optional

from produkte.renten_basis import RentenProdukt
from core.profil import NutzerProfil
from core.steuern import SteuerRechner


AV_SUBSIDIZED_CAP = 1800.0
KINDERZULAGE_PRO_KIND = 300.0
MIN_BEITRAG_KINDERZULAGE = 300.0
BERUFSEINSTEIGER_BONUS = 200.0


class AltersvorsorgeDepot(RentenProdukt):
    def __init__(
        self,
        start_datum: str,
        monatlicher_eigenbeitrag: float,
        erwartete_rendite_prozent: float = 6.0,
        kostenquote_prozent: float = 0.5,
        staatliche_foerderung_prozent: float = 0.0,
        abgaben_typ: str = "altersvorsorgedepot",
        entnahme_dauer_monate: int = 300,
        entnahmezins_p_a: float = 2.0,
        **kwargs,
    ):
        self.start_datum = start_datum
        self.monatlicher_eigenbeitrag = monatlicher_eigenbeitrag
        self.erwartete_rendite_prozent = erwartete_rendite_prozent
        self.kostenquote_prozent = kostenquote_prozent

        if staatliche_foerderung_prozent:
            warnings.warn(
                "staatliche_foerderung_prozent wird ignoriert; "
                "es gilt die gesetzliche Zulagenstaffel.",
                UserWarning,
                stacklevel=2,
            )

        self.staatliche_foerderung_prozent = 0.0
        self.abgaben_typ = abgaben_typ
        self.entnahme_dauer_monate = entnahme_dauer_monate
        self.entnahmezins_p_a = entnahmezins_p_a

    def name(self) -> str:
        return "Altersvorsorgedepot"

    def _parse_start_datum(self) -> datetime:
        return datetime.fromisoformat(self.start_datum)

    def _alter_zum_start(self, profil: NutzerProfil) -> int:
        start = self._parse_start_datum().date()
        geburt = profil._geburtsdatum_obj
        return start.year - geburt.year - (
            (start.month, start.day) < (geburt.month, geburt.day)
        )

    def _berechne_grundzulage(
        self,
        jahres_beitrag: float,
        jahr_index: int,
        profil: NutzerProfil,
    ) -> float:
        gefoerderter_beitrag = min(jahres_beitrag, AV_SUBSIDIZED_CAP)

        grundzulage = min(gefoerderter_beitrag, 360.0) * 0.50

        if gefoerderter_beitrag > 360.0:
            grundzulage += (gefoerderter_beitrag - 360.0) * 0.25

        if jahr_index == 0 and self._alter_zum_start(profil) < 25:
            grundzulage += BERUFSEINSTEIGER_BONUS

        return grundzulage

    def _berechne_kinderzulage(
        self,
        jahres_beitrag: float,
        kalenderjahr: int,
        profil: NutzerProfil,
    ) -> float:
        if jahres_beitrag < MIN_BEITRAG_KINDERZULAGE:
            return 0.0

        if profil.kindergeburtsjahre:
            return sum(
                KINDERZULAGE_PRO_KIND
                for geburt in profil.kindergeburtsjahre
                if 0 <= kalenderjahr - geburt < 18
            )

        return profil.anzahl_kinder * KINDERZULAGE_PRO_KIND

    def _berechne_jahrliche_zulage(
        self,
        profil: NutzerProfil,
        jahr_index: int = 0,
    ) -> float:
        jahres_beitrag = self.monatlicher_eigenbeitrag * 12

        # Optionaler Parameter wird ignoriert, da die gesetzliche
        # Zulagenstaffel verwendet werden soll.
        if self.staatliche_foerderung_prozent > 0.0:
            return (
                jahres_beitrag
                * self.staatliche_foerderung_prozent
                / 100.0
            )

        kalenderjahr = self._parse_start_datum().year + jahr_index

        grundzulage = self._berechne_grundzulage(
            jahres_beitrag,
            jahr_index,
            profil,
        )

        kinderzulage = self._berechne_kinderzulage(
            jahres_beitrag,
            kalenderjahr,
            profil,
        )

        return grundzulage + kinderzulage

    def berechne_monatliche_foerderung(self, *args) -> float:
        if len(args) == 1:
            arg = args[0]

            if isinstance(arg, NutzerProfil):
                return self._berechne_jahrliche_zulage(
                    arg,
                    0,
                ) / 12.0

        raise ValueError(
            "Für die Berechnung der monatlichen Förderung "
            "wird ein NutzerProfil benötigt."
        )

    def berechne_monatliche_details(
        self,
        aktueller_monat: datetime,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
    ) -> tuple[float, float, float, float]:
        start_dt = self._parse_start_datum()

        if aktueller_monat < start_dt:
            return 0.0, 0.0, 0.0, 0.0

        jahr_index = aktueller_monat.year - start_dt.year

        foerderung = (
            self._berechne_jahrliche_zulage(
                profil,
                jahr_index,
            )
            / 12.0
        )

        beitrag = self.monatlicher_eigenbeitrag

        return (
            beitrag,
            0.0,
            foerderung,
            beitrag + foerderung,
        )

    def berechne_monatliche_steuerersparnis(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
    ) -> float:
        zulage = (
            self._berechne_jahrliche_zulage(
                profil,
                0,
            )
            / 12.0
        )

        return steuer_rechner.berechne_altersvorsorge_steuerentlastung(
            profil.aktuelles_brutto_monat,
            self.monatlicher_eigenbeitrag,
            zulage,
        )

    def berechne_monatliche_netto_eigenleistung(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
        aktueller_monat: datetime = None,
    ) -> float:
        return max(
            0.0,
            self.monatlicher_eigenbeitrag,
        )

    def berechne_endkapital_nominal(
        self,
        profil: NutzerProfil,
    ) -> float:
        monate = profil.berechne_monate_fuer_zeitraum(
            self.start_datum
        )

        if monate <= 0:
            return 0.0

        netto_rendite_p_a = (
            self.erwartete_rendite_prozent
            - self.kostenquote_prozent
        )

        monatlicher_zins = (
            (1 + netto_rendite_p_a / 100.0) ** (1 / 12.0)
            - 1
        )

        annualer_beitrag = self.monatlicher_eigenbeitrag * 12

        subsidized_capital = 0.0
        ueberzahlung_capital = 0.0

        volle_jahre = monate // 12
        rest_monate = monate % 12

        for jahr in range(volle_jahre):
            zulage = self._berechne_jahrliche_zulage(
                profil,
                jahr,
            )

            subsidized_beitrag = min(
                annualer_beitrag,
                AV_SUBSIDIZED_CAP,
            )

            ueberzahlung_beitrag = max(
                0.0,
                annualer_beitrag - AV_SUBSIDIZED_CAP,
            )

            monatlicher_subsidized = (
                subsidized_beitrag / 12.0
                + zulage / 12.0
            )

            monatlicher_ueberzahlung = (
                ueberzahlung_beitrag / 12.0
            )

            for _ in range(12):
                subsidized_capital = (
                    subsidized_capital
                    * (1 + monatlicher_zins)
                    + monatlicher_subsidized
                )

                ueberzahlung_capital = (
                    ueberzahlung_capital
                    * (1 + monatlicher_zins)
                    + monatlicher_ueberzahlung
                )

        if rest_monate > 0:
            zulage = (
                self._berechne_jahrliche_zulage(
                    profil,
                    volle_jahre,
                )
                * (rest_monate / 12.0)
            )

            subsidized_beitrag = (
                min(
                    annualer_beitrag,
                    AV_SUBSIDIZED_CAP,
                )
                * (rest_monate / 12.0)
            )

            ueberzahlung_beitrag = (
                max(
                    0.0,
                    annualer_beitrag - AV_SUBSIDIZED_CAP,
                )
                * (rest_monate / 12.0)
            )

            monatlicher_subsidized = (
                subsidized_beitrag / rest_monate
                + zulage / rest_monate
            )

            monatlicher_ueberzahlung = (
                ueberzahlung_beitrag / rest_monate
            )

            for _ in range(rest_monate):
                subsidized_capital = (
                    subsidized_capital
                    * (1 + monatlicher_zins)
                    + monatlicher_subsidized
                )

                ueberzahlung_capital = (
                    ueberzahlung_capital
                    * (1 + monatlicher_zins)
                    + monatlicher_ueberzahlung
                )

        return subsidized_capital + ueberzahlung_capital

    def berechne_brutto_nominal(
        self,
        profil: NutzerProfil,
        endkapital: float = None,
    ) -> float:
        if endkapital is None:
            endkapital = self.berechne_endkapital_nominal(
                profil
            )

        if endkapital <= 0:
            return 0.0

        renten_monate = self.entnahme_dauer_monate

        renten_zins = (
            1 + self.entnahmezins_p_a / 100.0 / 12.0
        ) - 1

        if renten_zins == 0:
            return endkapital / renten_monate

        return (
            endkapital
            * (
                renten_zins
                * (1 + renten_zins) ** renten_monate
            )
            / (
                (1 + renten_zins) ** renten_monate - 1
            )
        )

    def berechne_netto_nominal(
        self,
        profil: NutzerProfil,
        steuer_rechner: SteuerRechner,
        endkapital: float = None,
    ) -> float:
        brutto = self.berechne_brutto_nominal(
            profil,
            endkapital,
        )

        return steuer_rechner.berechne_netto_aus_brutto(
            brutto,
            self.abgaben_typ,
        )
