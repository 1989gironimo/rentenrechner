from dataclasses import dataclass

from core.jahresparameter import jahresparameter


@dataclass(frozen=True)
class SozialversicherungsEngine:
    kinderlos: bool = False

    def parameter(self, jahr: int):
        return jahresparameter(jahr)

    def arbeitnehmer_ersparnis_entgeltumwandlung(
        self,
        brutto_monat: float,
        umwandlung_monat: float,
        jahr: int,
    ) -> dict[str, float]:
        p = self.parameter(jahr)
        brutto = max(0.0, brutto_monat)
        umwandlung = min(max(0.0, umwandlung_monat), brutto)
        result = {}
        for name, bbg, satz in (
            ("kv", p.kv_bbg_monat, p.kv_allgemein_prozent + p.kv_zusatzbeitrag_prozent),
            ("pv", p.kv_bbg_monat, p.pv_prozent + (p.pv_kinderlosenzuschlag_prozent if self.kinderlos else 0.0)),
            ("rv", p.rv_bbg_monat, p.rv_prozent),
            ("alv", p.alv_bbg_monat, p.alv_prozent),
        ):
            vor_bbg = min(brutto, bbg)
            nach_bbg = min(max(0.0, brutto - umwandlung), bbg)
            beitragsminderung = max(0.0, vor_bbg - nach_bbg)
            result[name] = beitragsminderung * (satz / 2) / 100.0
        result["gesamt"] = sum(result.values())
        return result

    def beitrag_im_ruhestand(self, brutto_monat: float, jahr: int, art: str) -> float:
        p = self.parameter(jahr)
        if art == "gesetzlich":
            kv_basis = brutto_monat
            kv = kv_basis * (p.kv_allgemein_prozent + p.kv_zusatzbeitrag_prozent) / 2 / 100
            pv = kv_basis * (p.pv_prozent + (p.pv_kinderlosenzuschlag_prozent if self.kinderlos else 0.0)) / 100
            return kv + pv
        if art in {"bav", "ukasse"}:
            kv_basis = max(0.0, brutto_monat - p.bav_kv_freibetrag_monat)
            kv = kv_basis * (p.kv_allgemein_prozent + p.kv_zusatzbeitrag_prozent) / 100
            pv = brutto_monat * (p.pv_prozent + (p.pv_kinderlosenzuschlag_prozent if self.kinderlos else 0.0)) / 100
            return kv + pv
        return 0.0
