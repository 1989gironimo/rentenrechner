from datetime import datetime

from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from engine.aggregator import RentenAggregator
from engine.csv_export import CsvExport
from produkte.bav import BetriebsrentebAV
from produkte.gesetzliche_rente import GesetzlicheRente
from produkte.aktienrente import StaatsfondsAktienrente
from produkte.altersvorsorgedepot import AltersvorsorgeDepot
from produkte.etf_sparplan import ETFSparplan
from produkte.unterstuetzungskasse import Unterstuetzungskasse


def _profil(gehaltssteigerung_prozent: float) -> NutzerProfil:
    return NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=2000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=gehaltssteigerung_prozent,
    )


def test_gehaltssteigerung_erhoeht_gesetzliche_rente_und_aktienrente():
    profil_low = _profil(0.0)
    profil_high = _profil(3.0)

    grv = GesetzlicheRente(
        aktuelle_rentenansprueche=2000.0,
        rentenanpassung_prozent=1.5,
        abgaben_typ="gesetzlich",
    )
    aktienrente = StaatsfondsAktienrente(
        start_datum="2025-01-01",
        stufenplan=[{"jahr": 2025, "an_prozent": 1.0, "ag_prozent": 1.0}],
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.1,
        abgaben_typ="gesetzlich",
    )

    grv_low = grv.berechne_brutto_nominal(profil_low)
    grv_high = grv.berechne_brutto_nominal(profil_high)
    assert grv_high > grv_low

    aktien_low = aktienrente.berechne_endkapital_nominal(profil_low)
    aktien_high = aktienrente.berechne_endkapital_nominal(profil_high)
    assert aktien_high > aktien_low


def test_generiere_report_zeigt_prozentuale_gesamtrente(capsys):
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=100.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    aggregator = RentenAggregator(profil=profil, steuer_rechner=SteuerRechner())

    class DummyProdukt:
        def __init__(self, name: str, rente: float):
            self._name = name
            self._rente = rente

        def name(self) -> str:
            return self._name

        def berechne_endkapital_nominal(self, profil):
            return 0.0

        def berechne_brutto_nominal(self, profil):
            return self._rente

        def berechne_netto_nominal(self, profil, steuer_rechner):
            return self._rente

        def berechne_monatliche_netto_eigenleistung(self, profil, steuer_rechner):
            return 0.0

    aggregator.produkt_hinzufuegen(DummyProdukt("Baustein A", 100.0))
    aggregator.produkt_hinzufuegen(DummyProdukt("Baustein B", 300.0))

    aggregator.generiere_report()

    output = capsys.readouterr().out
    assert "ZIEL-ABDECKUNG" in output
    assert "Baustein A:" in output
    assert "Baustein B:" in output
    assert "SUMME DER BAUSTEINE" in output
    assert "PUFFER" in output
    assert "FEHLBETRAG" not in output


def test_generiere_report_zeigt_fehlbetrag_kurz(capsys):
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=400.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    aggregator = RentenAggregator(profil=profil, steuer_rechner=SteuerRechner())

    class DummyProdukt:
        def __init__(self, name: str, rente: float):
            self._name = name
            self._rente = rente

        def name(self) -> str:
            return self._name

        def berechne_endkapital_nominal(self, profil):
            return 0.0

        def berechne_brutto_nominal(self, profil):
            return self._rente

        def berechne_netto_nominal(self, profil, steuer_rechner):
            return self._rente

        def berechne_monatliche_netto_eigenleistung(self, profil, steuer_rechner):
            return 0.0

    aggregator.produkt_hinzufuegen(DummyProdukt("Baustein A", 100.0))
    aggregator.produkt_hinzufuegen(DummyProdukt("Baustein B", 100.0))

    aggregator.generiere_report()

    output = capsys.readouterr().out
    assert "FEHLBETRAG" in output
    assert "PUFFER" not in output
    assert "€ / Monat" in output


def test_generiere_report_zeigt_gesamtkapital_und_kvdr_hinweis(capsys):
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=400.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    aggregator = RentenAggregator(profil=profil, steuer_rechner=SteuerRechner())

    class DummyProdukt:
        def __init__(self, name: str, kapital: float, belastung: float):
            self._name = name
            self._kapital = kapital
            self._belastung = belastung

        def name(self) -> str:
            return self._name

        def berechne_endkapital_nominal(self, profil):
            return self._kapital

        def berechne_brutto_nominal(self, profil):
            return 100.0

        def berechne_netto_nominal(self, profil, steuer_rechner):
            return 100.0

        def berechne_monatliche_netto_eigenleistung(self, profil, steuer_rechner):
            return self._belastung

    aggregator.produkt_hinzufuegen(DummyProdukt("Baustein A", 100.0, 10.0))
    aggregator.produkt_hinzufuegen(DummyProdukt("Baustein B", 200.0, 20.0))

    aggregator.generiere_report()

    output = capsys.readouterr().out
    assert "GESAMTES VERMÖGEN ZUM RENTENEINTRITT" in output
    assert "300.00 €" in output
    assert "GESAMTE MONATLICHE SPARBELASTUNG (Ende)" in output
    assert "KVdR" in output


def test_generiere_report_zeigt_startzeitpunkt_der_einzahlungen(capsys):
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=400.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    aggregator = RentenAggregator(profil=profil, steuer_rechner=SteuerRechner())

    class DummyProdukt:
        def __init__(self, name: str, start_datum: str):
            self._name = name
            self.start_datum = start_datum

        def name(self) -> str:
            return self._name

        def berechne_endkapital_nominal(self, profil):
            return 0.0

        def berechne_brutto_nominal(self, profil):
            return 0.0

        def berechne_netto_nominal(self, profil, steuer_rechner):
            return 0.0

        def berechne_monatliche_netto_eigenleistung(self, profil, steuer_rechner):
            return 0.0

    aggregator.produkt_hinzufuegen(DummyProdukt("Baustein A", "2025-01-01"))

    aggregator.generiere_report()

    output = capsys.readouterr().out
    assert "Start der Einzahlungen: 01.01.2025" in output


def test_generiere_report_zeigt_netto_eigenleistung_bei_staffel(capsys):
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=400.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    aggregator = RentenAggregator(profil=profil, steuer_rechner=SteuerRechner())

    class DummyProdukt:
        def __init__(self):
            self.staffel_beitraege = [{"ab_jahr": 0, "eigenbeitrag": 100.0}]

        def name(self) -> str:
            return "Baustein Staffel"

        def berechne_endkapital_nominal(self, profil):
            return 0.0

        def berechne_brutto_nominal(self, profil):
            return 0.0

        def berechne_netto_nominal(self, profil, steuer_rechner):
            return 0.0

        def berechne_monatliche_netto_eigenleistung(self, profil, steuer_rechner):
            return 10.0

    aggregator.produkt_hinzufuegen(DummyProdukt())

    aggregator.generiere_report()

    output = capsys.readouterr().out
    assert "Monatliche Netto-Eigenleistung" in output
    assert "Baustein Staffel" in output


def test_generiere_report_zeigt_netto_eigenleistung_fuer_avd_und_etf(capsys):
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    aggregator = RentenAggregator(profil=profil, steuer_rechner=SteuerRechner())

    avd = AltersvorsorgeDepot(
        start_datum="2027-01-01",
        monatlicher_eigenbeitrag=150.0,
        staatliche_foerderung_prozent=0.0,
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.5,
    )
    etf = ETFSparplan(
        start_datum="2027-01-01",
        monatlicher_sparplan=200.0,
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.2,
        startkapital=0.0,
    )

    aggregator.produkt_hinzufuegen(avd)
    aggregator.produkt_hinzufuegen(etf)

    aggregator.generiere_report()
    output = capsys.readouterr().out

    assert "Altersvorsorgedepot (ab 2027)" in output
    assert "Monatliche Netto-Eigenleistung:" in output
    assert "noch nicht aktiv" in output
    assert "Privater ETF-Sparplan" in output


def test_aktienrente_verwendet_steuerrechner():
    profil = _profil(0.0)
    steuer_rechner = SteuerRechner(
        kv_pv_satz_voll=0.0,
        persoenlicher_steuersatz=10.0,
    )
    aktienrente = StaatsfondsAktienrente(
        start_datum="2025-01-01",
        stufenplan=[{"jahr": 2025, "an_prozent": 1.0, "ag_prozent": 0.0}],
        erwartete_rendite_prozent=0.0,
    )

    brutto = aktienrente.berechne_brutto_nominal(profil)
    netto = aktienrente.berechne_netto_nominal(profil, steuer_rechner)

    assert netto == steuer_rechner.berechne_netto_aus_brutto(brutto, "gesetzlich")


def test_av_depot_foerderung_verwendet_kalenderjahr():
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    av_depot = AltersvorsorgeDepot(
        start_datum="2025-01-01",
        monatlicher_eigenbeitrag=150.0,
        anzahl_kinder=1,
        kindergeburtsjahre=[2025],
    )

    details_2025 = av_depot.berechne_monatliche_details(
        datetime(2025, 1, 1), profil, SteuerRechner()
    )
    details_2043 = av_depot.berechne_monatliche_details(
        datetime(2043, 1, 1), profil, SteuerRechner()
    )

    assert details_2025[2] > details_2043[2]


def test_unterstuetzungskasse_zieht_beitragskosten_vom_sparbeitrag_ab():
    profil = _profil(0.0)
    u_kasse = Unterstuetzungskasse(
        start_datum="2025-01-01",
        staffel_beitraege=[{"ab_jahr": 0, "eigenbeitrag": 100.0, "ag_beitrag": 100.0}],
        kosten_beitrag_prozent=10.0,
        fixe_verwaltungskosten_monat=5.0,
    )

    details = u_kasse.berechne_monatliche_details(
        datetime(2025, 1, 1), profil, SteuerRechner()
    )

    assert details[3] == 175.0


def test_av_depot_beruecksichtigt_berufseinsteiger_und_kinderzulage():
    profil = NutzerProfil(
        geburtsdatum="2002-06-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    steuer_rechner = SteuerRechner()
    av_depot = AltersvorsorgeDepot(
        start_datum="2025-01-01",
        monatlicher_eigenbeitrag=150.0,
        anzahl_kinder=1,
        kindergeburtsjahre=[2015],
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.5,
    )

    foerderung = av_depot.berechne_monatliche_foerderung(profil)
    assert foerderung > 0.0
    assert abs(foerderung - 1040.0 / 12.0) < 0.01

    netto_eigenleistung = av_depot.berechne_monatliche_netto_eigenleistung(profil, steuer_rechner)
    assert netto_eigenleistung == 150.0

    steuerersparnis = av_depot.berechne_monatliche_steuerersparnis(profil, steuer_rechner)
    assert steuerersparnis >= 0.0


def test_av_depot_fuer_staatliche_foerderung_prozent():
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    av_depot = AltersvorsorgeDepot(
        start_datum="2025-01-01",
        monatlicher_eigenbeitrag=150.0,
        staatliche_foerderung_prozent=20.0,
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.5,
    )

    foerderung = av_depot.berechne_monatliche_foerderung(profil)
    assert abs(foerderung - 45.0) < 0.01


def test_steuerechner_berechnet_abgeltungsteuer_mit_kirchensteuer():
    steuer_rechner = SteuerRechner(
        abgeltungsteuersatz_prozent=25.0,
        solidaritaetszuschlag_prozent=5.5,
        kirchensteuer_prozent=9.0,
        teilfreistellung_prozent=70.0,
    )
    effektiver_satz = steuer_rechner.berechne_abgeltungssteuersatz_prozent()

    assert abs(effektiver_satz - 26.2614678899) < 0.001
    steuer = steuer_rechner.berechne_kapitalertragsteuer(1000.0)
    assert steuer == 0.0

    netto = steuer_rechner.berechne_netto_aus_brutto(1000.0, "etf")
    assert netto == 1000.0


def test_steuerechner_verwendet_2026er_einkommensteuertarif():
    steuer_rechner = SteuerRechner()

    assert steuer_rechner.berechne_einkommensteuer(12348.0) == 0.0
    assert steuer_rechner.berechne_einkommensteuer(12349.0) > 0.0


def test_steuerechner_besteuert_rentengruppe_gemeinsam():
    steuer_rechner = SteuerRechner(
        kv_pv_satz_voll=0.0,
    )

    netto_gesamt = steuer_rechner.berechne_netto_aus_rentengruppe(
        [(1000.0, "gesetzlich"), (1000.0, "bav")]
    )

    assert sum(netto_gesamt) < 2000.0
    assert netto_gesamt[0] > netto_gesamt[1]


def test_bav_entgeltumwandlung_beachtet_kv_bbg_und_rv_alv():
    steuer_rechner = SteuerRechner()

    entlastung = steuer_rechner.berechne_nettoaufwand_entgeltumwandlung(
        brutto_monat=8025.0,
        eigenbeitrag_monat=200.0,
        jahr=2026,
    )

    assert entlastung["kv_ersparnis"] == 0.0
    assert entlastung["pv_ersparnis"] == 0.0
    assert entlastung["rv_ersparnis"] > 0.0
    assert entlastung["alv_ersparnis"] > 0.0
    assert 50.0 < entlastung["nettoaufwand"] < 150.0


def test_etf_besteuert_bei_nullrendite_nur_den_gewinnanteil():
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2030-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    steuer_rechner = SteuerRechner()
    etf = ETFSparplan(
        start_datum="2025-01-01",
        monatlicher_sparplan=200.0,
        erwartete_rendite_prozent=0.0,
        kostenquote_prozent=0.0,
    )

    brutto = etf.berechne_brutto_nominal(profil)
    netto = etf.berechne_netto_nominal(profil, steuer_rechner)

    assert abs(netto - brutto) < 0.01


def test_etf_besteuert_nicht_das_eingezahlte_kapital():
    profil = _profil(0.0)
    steuer_rechner = SteuerRechner()
    etf = ETFSparplan(
        start_datum="2025-01-01",
        monatlicher_sparplan=200.0,
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.0,
    )

    brutto = etf.berechne_brutto_nominal(profil)
    netto = etf.berechne_netto_nominal(profil, steuer_rechner)

    assert 0.0 < netto <= brutto


def test_av_depot_berechnet_endkapital_und_brutto_rente():
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2057-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    av_depot = AltersvorsorgeDepot(
        start_datum="2025-01-01",
        monatlicher_eigenbeitrag=150.0,
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.5,
    )

    endkapital = av_depot.berechne_endkapital_nominal(profil)
    brutto = av_depot.berechne_brutto_nominal(profil)

    assert endkapital > 0.0
    assert brutto > 0.0
    assert brutto < endkapital


def test_bav_berechnet_monatliche_details_richtig():
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2040-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    steuer_rechner = SteuerRechner(18.5, 11.3, 20.0)
    bav = BetriebsrentebAV(
        start_datum="2025-01-01",
        monatlicher_beitrag_mitarbeiter=200.0,
        arbeitgeber_zuschuss_prozent=20.0,
        dynamik_prozent=5.0,
    )

    details_start = bav.berechne_monatliche_details(datetime(2025, 1, 1), profil, steuer_rechner)
    details_letzter_monat = bav.berechne_monatliche_details(datetime(2039, 12, 1), profil, steuer_rechner)

    assert details_start[0] > 0.0
    assert details_start[1] == 40.0
    assert details_letzter_monat[0] > details_start[0]
    assert details_letzter_monat[1] == 79.19726397757596
    assert details_letzter_monat[3] > details_start[3]


def test_unterstuetzungskasse_berechnet_monatliche_details_richtig():
    profil = NutzerProfil(
        geburtsdatum="1990-01-01",
        renteneintrittsdatum="2040-01-01",
        wunschrente_heutige_kaufkraft=1000.0,
        aktuelles_brutto_monat=4000.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=2.0,
    )
    steuer_rechner = SteuerRechner(18.5, 11.3, 20.0)
    u_kasse = Unterstuetzungskasse(
        start_datum="2025-01-01",
        staffel_beitraege=[
            {"ab_jahr": 0, "eigenbeitrag": 100.0, "ag_beitrag": 100.0},
            {"ab_jahr": 5, "eigenbeitrag": 150.0, "ag_beitrag": 150.0},
        ],
        jahre_beschaeftigung_bisher=0,
    )

    details_start = u_kasse.berechne_monatliche_details(datetime(2025, 1, 1), profil, steuer_rechner)
    details_letzter_monat = u_kasse.berechne_monatliche_details(datetime(2039, 12, 1), profil, steuer_rechner)

    assert abs(details_start[0] - 44.6321338) < 0.01
    assert details_start[1] == 100.0
    assert abs(details_letzter_monat[0] - 67.1039907) < 0.01
    assert details_letzter_monat[1] == 150.0
    assert details_letzter_monat[3] == 300.0
