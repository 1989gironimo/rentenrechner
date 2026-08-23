DEFAULT_ABGELTUNGSSTEUERSATZ = 25.0
DEFAULT_SOLIDARITAETSZUSCHLAG = 5.5
DEFAULT_TEILFREISTELLUNG = 70.0
SPARER_PAUSCHBETRAG = 1000.0

from core.jahresparameter import jahresparameter
from core.sozialversicherung import SozialversicherungsEngine


class SteuerRechner:
    def __init__(
        self,
        kv_pv_satz_voll: float = 18.5,
        kv_pv_satz_ermässigt: float = 11.3,
        persoenlicher_steuersatz: float = 20.0,
        abgeltungsteuersatz_prozent: float = DEFAULT_ABGELTUNGSSTEUERSATZ,
        solidaritaetszuschlag_prozent: float = DEFAULT_SOLIDARITAETSZUSCHLAG,
        kirchensteuer_prozent: float = 0.0,
        teilfreistellung_prozent: float = DEFAULT_TEILFREISTELLUNG,
        kinderlos: bool = False,
    ):
        self.kv_pv_satz_voll = kv_pv_satz_voll
        self.kv_pv_satz_ermässigt = kv_pv_satz_ermässigt
        self.persoenlicher_steuersatz = persoenlicher_steuersatz
        self.abgeltungsteuersatz_prozent = abgeltungsteuersatz_prozent
        self.solidaritaetszuschlag_prozent = solidaritaetszuschlag_prozent
        self.kirchensteuer_prozent = kirchensteuer_prozent
        self.teilfreistellung_prozent = teilfreistellung_prozent
        self.sozialversicherung = SozialversicherungsEngine(kinderlos=kinderlos)

    def berechne_einkommensteuer(self, zve: float) -> float:
        zve = max(0, int(zve))
        if zve <= 12348:
            return 0.0
        if zve <= 17799:
            y = (zve - 12348) / 10000
            return (914.51 * y + 1400) * y
        if zve <= 69878:
            z = (zve - 17799) / 10000
            return (173.10 * z + 2397) * z + 1034.87
        if zve <= 277825:
            return 0.42 * zve - 11135.63
        return 0.45 * zve - 19470.38

    def berechne_grenzsteuer(self, amount: float, zve: float) -> float:
        if amount <= 0:
            return 0.0
        return max(0.0, self.berechne_einkommensteuer(zve + amount) - self.berechne_einkommensteuer(zve))

    def berechne_abgeltungssteuersatz_prozent(self) -> float:
        soli = self.solidaritaetszuschlag_prozent / 100.0
        kirchensteuer = self.kirchensteuer_prozent / 100.0
        return self.abgeltungsteuersatz_prozent * (1.0 + soli + kirchensteuer) / (1.0 + kirchensteuer)

    def berechne_kapitalertragsteuer(self, gewinn: float) -> float:
        effektiver_anteil = max(0.0, 100.0 - self.teilfreistellung_prozent) / 100.0
        steuerpflichtiger_gewinn = max(
            0.0,
            gewinn * effektiver_anteil - SPARER_PAUSCHBETRAG,
        )
        return steuerpflichtiger_gewinn * self.berechne_abgeltungssteuersatz_prozent() / 100.0

    def guensigerpruefung(self, taxable_gain: float, zve: float) -> float:
        return min(self.berechne_kapitalertragsteuer(taxable_gain), self.berechne_grenzsteuer(taxable_gain, zve))

    def berechne_netto_aus_brutto(self, brutto: float, abgaben_typ: str) -> float:
        """
        Berechnet das Nettoreinkommen basierend auf dem Bruttobetrag und dem Abgabentyp.
        """
        if abgaben_typ == "etf":
            steuer = self.berechne_kapitalertragsteuer(brutto)
            return max(0.0, brutto - steuer)

        steuer = self.berechne_einkommensteuer(brutto * 12) / 12
        sozialabgaben = self._berechne_sozialabgaben(brutto, abgaben_typ)
        return max(0.0, brutto - steuer - sozialabgaben)

    def berechne_nettoaufwand_entgeltumwandlung(
        self,
        brutto_monat: float,
        eigenbeitrag_monat: float,
        jahr: int = 2026,
        steuerlich_abzugsfaehig_monat: float | None = None,
    ) -> dict[str, float]:
        """Berechnet den Nettoaufwand einer Entgeltumwandlung.

        Das Brutto wird als Naeherung fuer das zu versteuernde Einkommen genutzt;
        die Abweichung ist eine dokumentierte Modellvereinfachung.
        """
        beitrag = min(max(0.0, eigenbeitrag_monat), max(0.0, brutto_monat))
        abzugsbetrag = beitrag if steuerlich_abzugsfaehig_monat is None else min(
            beitrag,
            max(0.0, steuerlich_abzugsfaehig_monat),
        )
        steuer_vorher = self.berechne_einkommensteuer(brutto_monat * 12)
        steuer_nachher = self.berechne_einkommensteuer((brutto_monat - abzugsbetrag) * 12)
        steuerersparnis = max(0.0, (steuer_vorher - steuer_nachher) / 12)
        sv = self.sozialversicherung.arbeitnehmer_ersparnis_entgeltumwandlung(
            brutto_monat,
            beitrag,
            jahr,
        )
        return {
            "beitrag": beitrag,
            "steuerersparnis": steuerersparnis,
            "kv_ersparnis": sv["kv"],
            "pv_ersparnis": sv["pv"],
            "rv_ersparnis": sv["rv"],
            "alv_ersparnis": sv["alv"],
            "sv_ersparnis": sv["gesamt"],
            "nettoaufwand": max(0.0, beitrag - steuerersparnis - sv["gesamt"]),
        }

    def berechne_altersvorsorge_steuerentlastung(
        self,
        brutto_monat: float,
        eigenbeitrag_monat: float,
        zulage_monat: float,
    ) -> float:
        """Naeherung der Guenstigerpruefung fuer einen zertifizierten Vertrag."""
        zv_einkommen = max(0.0, brutto_monat * 12)
        sonderausgaben = min(2100.0, max(0.0, eigenbeitrag_monat + zulage_monat) * 12)
        steuer_vorher = self.berechne_einkommensteuer(zv_einkommen)
        steuer_nachher = self.berechne_einkommensteuer(
            max(0.0, zv_einkommen - sonderausgaben)
        )
        steuerliche_entlastung = max(0.0, steuer_vorher - steuer_nachher)
        zulagen = max(0.0, zulage_monat) * 12
        return max(0.0, steuerliche_entlastung - zulagen) / 12

    def _berechne_sozialabgaben(self, brutto: float, abgaben_typ: str) -> float:
        if abgaben_typ == "bav":
            return brutto * self.kv_pv_satz_voll / 100.0
        if abgaben_typ == "gesetzlich":
            return brutto * (self.kv_pv_satz_voll / 2) / 100.0
        return 0.0

    def berechne_netto_aus_rentengruppe(
        self,
        brutto_werte: list[tuple],
        jahr: int = 2057,
    ) -> list[float]:
        """Verteilt eine gemeinsame Einkommensteuer auf mehrere Rentenbausteine."""
        normalisierte_werte = [
            (wert[0], wert[1], wert[2] if len(wert) > 2 else 1.0)
            for wert in brutto_werte
        ]
        steuerbemessung = [max(0.0, brutto) * anteil for brutto, _, anteil in normalisierte_werte]
        gesamt_bemessung = sum(steuerbemessung)
        if gesamt_bemessung <= 0:
            return [0.0 for _ in brutto_werte]

        gemeinsame_steuer = self.berechne_einkommensteuer(gesamt_bemessung * 12) / 12
        netto_werte = []
        for brutto, abgaben_typ, _ in normalisierte_werte:
            steueranteil = gemeinsame_steuer * steuerbemessung[len(netto_werte)] / gesamt_bemessung
            sozialabgaben = self.sozialversicherung.beitrag_im_ruhestand(
                brutto,
                jahr,
                abgaben_typ,
            )
            netto_werte.append(max(0.0, brutto - steueranteil - sozialabgaben))
        return netto_werte
