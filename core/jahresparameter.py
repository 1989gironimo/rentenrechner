from dataclasses import dataclass


@dataclass(frozen=True)
class Jahresparameter:
    """Gesetzeswerte 2026 und transparente Fortschreibung fuer Folgejahre.

    Werte ab 2027 sind Modellannahmen, sofern sie nicht gesetzlich feststehen.
    """

    jahr: int
    grundfreibetrag: float
    kv_bbg_monat: float
    rv_bbg_monat: float
    alv_bbg_monat: float
    kv_allgemein_prozent: float
    kv_zusatzbeitrag_prozent: float
    pv_prozent: float
    pv_kinderlosenzuschlag_prozent: float
    rv_prozent: float
    alv_prozent: float
    bav_kv_freibetrag_monat: float
    etf_basiszinssatz_prozent: float

    # Altersvorsorgedepot (Stand 2026)
    av_grundzulage: float = 175.0
    av_kinderzulage: float = 300.0
    av_berufseinsteiger_bonus: float = 200.0
    av_subsidized_cap: float = 1800.0
    av_mindestbeitrag_kinderzulage: float = 300.0

    # Einkommensteuer 2026 (Progressionszonen)
    est_grundfreibetrag: float = 12348.0
    est_zone2_grenze: float = 17799.0
    est_zone3_grenze: float = 69878.0
    est_zone4_grenze: float = 277825.0
    # Hinweis: Formelkoeffizienten (914.51, 1400, 173.10, 2397, 1034.87)
    # sind fuer 2026 gueltig und werden hier nicht jahresabhaengig modelliert,
    # da sie selten aenderen und eine vollstaendige Tarifformel den Rahmen
    # sprengen wuerde.


PARAMETER_2026 = Jahresparameter(
    jahr=2026,
    grundfreibetrag=12348.0,
    kv_bbg_monat=5812.50,
    rv_bbg_monat=8450.00,
    alv_bbg_monat=8450.00,
    kv_allgemein_prozent=14.6,
    kv_zusatzbeitrag_prozent=2.9,
    pv_prozent=3.6,
    pv_kinderlosenzuschlag_prozent=0.6,
    rv_prozent=18.6,
    alv_prozent=2.6,
    bav_kv_freibetrag_monat=197.75,
    etf_basiszinssatz_prozent=2.53,
)


def jahresparameter(jahr: int) -> Jahresparameter:
    if jahr <= 2026:
        return PARAMETER_2026

    # Explizite Modellannahme: unbekannte kuenftige Werte werden konstant gehalten.
    return Jahresparameter(**{
        **PARAMETER_2026.__dict__,
        "jahr": jahr,
    })
