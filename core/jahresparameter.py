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
