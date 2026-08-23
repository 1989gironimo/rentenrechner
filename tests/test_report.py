import pytest
from datetime import datetime
from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from engine.aggregator import RentenAggregator
from produkte.gesetzliche_rente import GesetzlicheRente
from produkte.bav import BetriebsrentebAV
from produkte.altersvorsorgedepot import AltersvorsorgeDepot
from produkte.etf_sparplan import ETFSparplan


@pytest.fixture
def profil():
    return NutzerProfil(
        geburtsdatum="1995-01-01",
        renteneintrittsdatum="2062-01-01",
        wunschrente_heutige_kaufkraft=3000.0,
        aktuelles_brutto_monat=4500.0,
        inflation_prozent=2.0,
        gehaltssteigerung_prozent=1.5,
        anzahl_kinder=1,
        kindergeburtsjahre=[2025],
    )


@pytest.fixture
def steuer_rechner():
    return SteuerRechner(
        kv_pv_satz_voll=18.5,
        kv_pv_satz_ermässigt=11.3,
        persoenlicher_steuersatz=20.0,
        abgeltungsteuersatz_prozent=25.0,
        solidaritaetszuschlag_prozent=5.5,
        kirchensteuer_prozent=0.0,
        teilfreistellung_prozent=70.0,
    )


@pytest.fixture
def aggregator(profil, steuer_rechner):
    return RentenAggregator(profil=profil, steuer_rechner=steuer_rechner)


@pytest.fixture
def gesetzliche_rente():
    return GesetzlicheRente(
        aktuelle_rentenansprueche=1000.0,
        rentenanpassung_prozent=1.5,
        abgaben_typ="gesetzlich",
        aktueller_rentenwert=42.52,
        durchschnittsentgelt=51944.0,
        rv_bbg_jahr=101400.0,
    )


@pytest.fixture
def bav():
    return BetriebsrentebAV(
        start_datum="2025-01-01",
        monatlicher_beitrag_mitarbeiter=100.0,
        arbeitgeber_zuschuss_prozent=15.0,
        erwartete_rendite_prozent=4.0,
        kostenquote_prozent=1.03,
        startkapital=0.0,
        startkapital_datum="2025-01-01",
        dynamik_prozent=0.0,
        abgaben_typ="bav",
    )


@pytest.fixture
def av_depot():
    return AltersvorsorgeDepot(
        start_datum="2025-01-01",
        monatlicher_eigenbeitrag=150.0,
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.2,
        abgaben_typ="altersvorsorgedepot",
    )


@pytest.fixture
def etf_sparplan():
    return ETFSparplan(
        start_datum="2025-01-01",
        monatlicher_sparplan=200.0,
        erwartete_rendite_prozent=6.0,
        kostenquote_prozent=0.2,
        startkapital=0.0,
        abgaben_typ="etf",
    )


def test_gesetzliche_rente_endkapital(gesetzliche_rente, profil):
    kapital = gesetzliche_rente.berechne_endkapital_nominal(profil)
    assert kapital == 0.0


def test_gesetzliche_rente_brutto(gesetzliche_rente, profil):
    brutto = gesetzliche_rente.berechne_brutto_nominal(profil)
    assert brutto > 1000.0


def test_bav_endkapital(bav, profil):
    kapital = bav.berechne_endkapital_nominal(profil)
    assert kapital > 0.0


def test_av_depot_endkapital(av_depot, profil):
    kapital = av_depot.berechne_endkapital_nominal(profil)
    assert kapital > 0.0


def test_av_depot_foerderung_mit_kind(av_depot, profil):
    foerderung = av_depot.berechne_monatliche_foerderung(profil)
    assert foerderung > 0.0


def test_etf_endkapital(etf_sparplan, profil):
    kapital = etf_sparplan.berechne_endkapital_nominal(profil)
    assert kapital > 0.0


def test_aggregator_report(aggregator, gesetzliche_rente, bav, av_depot, etf_sparplan):
    aggregator.produkt_hinzufuegen(gesetzliche_rente)
    aggregator.produkt_hinzufuegen(bav)
    aggregator.produkt_hinzufuegen(av_depot)
    aggregator.produkt_hinzufuegen(etf_sparplan)
    aggregator.generiere_report()


def test_csv_export(aggregator, gesetzliche_rente, bav, av_depot, etf_sparplan):
    from engine.csv_export import CsvExport
    aggregator.produkt_hinzufuegen(gesetzliche_rente)
    aggregator.produkt_hinzufuegen(bav)
    aggregator.produkt_hinzufuegen(av_depot)
    aggregator.produkt_hinzufuegen(etf_sparplan)
    export = CsvExport(aggregator=aggregator)
    export.exportiere_monatliche_projektion("test_renten_verlauf.csv")
