from datetime import datetime
import inspect
from typing import List
from core.profil import NutzerProfil
from core.steuern import SteuerRechner
from produkte.renten_basis import RentenProdukt

class RentenAggregator:
    def __init__(self, profil: NutzerProfil, steuer_rechner: SteuerRechner):
        self.profil = profil
        self.steuer_rechner = steuer_rechner
        self.produkte: List[RentenProdukt] = []

    def produkt_hinzufuegen(self, produkt: RentenProdukt):
        self.produkte.append(produkt)

    def _berechne_monatliche_sparbelastung_am_ende(self, produkt: RentenProdukt) -> float:
        if hasattr(produkt, "berechne_monatliche_sparbelastung_am_ende"):
            return produkt.berechne_monatliche_sparbelastung_am_ende(self.profil, self.steuer_rechner)
        return produkt.berechne_monatliche_netto_eigenleistung(self.profil, self.steuer_rechner)

    def _produkt_ist_heute_aktiv(self, produkt: RentenProdukt, heute: datetime) -> bool:
        start_datum = getattr(produkt, "start_datum", None)
        if start_datum is None:
            return True

        if isinstance(start_datum, str):
            try:
                start_datum = datetime.strptime(start_datum, "%Y-%m-%d")
            except ValueError:
                return True
        elif hasattr(start_datum, "date"):
            start_datum = start_datum if isinstance(start_datum, datetime) else datetime.combine(start_datum, datetime.min.time())
        else:
            return True

        return heute.date() >= start_datum.date()

    def _drucke_staffel_oder_stufenplan(self, produkt: RentenProdukt):
        """Ermittelt und druckt Beitragsstaffeln oder Stufenpläne dynamisch."""
        # 1. Option: Das Produkt bringt eine eigene Formatierungsmethode mit
        if hasattr(produkt, "get_staffel_info"):
            for zeile in produkt.get_staffel_info():
                print(f"    • {zeile}")
            return

        # 2. Option: Euro-Staffeln (z. B. bAV / U-Kasse)
        staffel = getattr(produkt, "staffel_beitraege", [])
        if staffel:
            print(f"  [Brutto-Beitragsstaffel]:")
            for s in staffel:
                jahr = s.get("ab_jahr", s.get("jahr", 0))
                eb = s.get("eigenbeitrag", s.get("monatlicher_beitrag", 0.0))
                ag = s.get("ag_beitrag", 0.0)
                
                if ag > 0:
                    print(f"    • Ab Jahr {jahr:2d}: Eigen: {eb:6.2f} € + AG: {ag:6.2f} € (Gesamt: {eb+ag:6.2f} €/Monat)")
                else:
                    print(f"    • Ab Jahr {jahr:2d}: {eb:6.2f} € / Monat")
                    
            if hasattr(produkt, "berechne_netto_staffel"):
                netto_staffel = produkt.berechne_netto_staffel(self.profil, self.steuer_rechner)
                if netto_staffel:
                    print(f"  [Netto-Eigenleistungs-Staffel (tatsächliche Belastung)]:")
                    for ns in netto_staffel:
                        jahr = ns.get("ab_jahr", ns.get("jahr", 0))
                        nw = ns.get("netto", 0.0)
                        print(f"    • Ab Jahr {jahr:2d}: {nw:6.2f} € / Monat")
            return

        # 3. Option: Prozentualer Stufenplan vom Brutto (z. B. Aktienrente / Generationenkapital)
        stufenplan = getattr(produkt, "stufenplan", [])
        if stufenplan:
            print(f"  [Prozentualer Stufenplan vom Bruttogehalt]:")
            for stufe in stufenplan:
                jahr = stufe.get("jahr", stufe.get("ab_jahr", 0))
                an = stufe.get("an_prozent", 0.0)
                ag = stufe.get("ag_prozent", 0.0)
                gesamt = an + ag
                if ag > 0:
                    print(f"    • Ab Jahr {jahr}: Arbeitnehmer: {an:.2f} % + Arbeitgeber: {ag:.2f} % (Gesamt: {gesamt:.2f} %)")
                else:
                    print(f"    • Ab Jahr {jahr}: {an:.2f} % vom Brutto")

    def generiere_report(self):
        print("=" * 65)
        print("📊 DEIN RENTEN-REPORT (INKL. ANNAHMEN & SPARLEISTUNG)")
        print("=" * 65)
        heute = datetime.today()
        print(f"Jahre bis zur Rente:              {self.profil.jahre_bis_rente:.1f}")
        print(f"Angenommene Inflation:            {self.profil.inflation_prozent} % p.a.")
        print(f"Gehaltssteigerung:      {self.profil.gehaltssteigerung_prozent:.2f} % p.a.")
        print(f"Persönlicher Steuersatz (Rente):  {self.steuer_rechner.persoenlicher_steuersatz} %")
        print(f"Ziel-Rente (Netto, heutige Kaufkr.): {self.profil.wunschrente_heutige_kaufkraft:.2f} €\n")
        
        gesamte_rente_netto_kaufkraft = 0.0
        gesamte_netto_eigenleistung = 0.0
        gesamt_kapital_zum_renteneintritt = 0.0
        anteile = []

        produkt_rohwerte = []
        for produkt in self.produkte:
            endkapital = produkt.berechne_endkapital_nominal(self.profil)
            brutto_methode = produkt.berechne_brutto_nominal
            if len(inspect.signature(brutto_methode).parameters) >= 2:
                brutto_nominal = brutto_methode(self.profil, endkapital)
            else:
                brutto_nominal = brutto_methode(self.profil)
            produkt_rohwerte.append((produkt, endkapital, brutto_nominal))

        renten_rohwerte = [
            (
                brutto,
                getattr(produkt, "abgaben_typ", "unbekannt"),
                getattr(produkt, "steuerpflichtiger_anteil", 1.0),
            )
            for produkt, _, brutto in produkt_rohwerte
            if getattr(produkt, "abgaben_typ", "unbekannt") != "etf"
        ]
        gemeinsame_netto = iter(
            self.steuer_rechner.berechne_netto_aus_rentengruppe(
                renten_rohwerte,
                jahr=self.profil._renteneintrittsdatum_obj.year,
            )
        )
        netto_werte = {}
        for produkt, _, brutto in produkt_rohwerte:
            if getattr(produkt, "abgaben_typ", "unbekannt") == "etf":
                netto_werte[id(produkt)] = produkt.berechne_netto_nominal(
                    self.profil,
                    self.steuer_rechner,
                )
            else:
                netto_werte[id(produkt)] = next(gemeinsame_netto)

        for produkt, endkapital, brutto_nominal in produkt_rohwerte:
            netto_nominal = netto_werte[id(produkt)]
            netto_heute = self.profil.in_heutige_kaufkraft_umrechnen(netto_nominal)
            
            aktiv = self._produkt_ist_heute_aktiv(produkt, heute)
            netto_eigenleistung_start = (
                produkt.berechne_monatliche_netto_eigenleistung(
                    self.profil,
                    self.steuer_rechner,
                )
                if aktiv
                else 0.0
            )
            gesamte_netto_eigenleistung += netto_eigenleistung_start
            gesamte_rente_netto_kaufkraft += netto_heute
            gesamt_kapital_zum_renteneintritt += endkapital
            anteile.append((produkt.name(), netto_heute))
            
            print(f"🔹 Baustein: {produkt.name()}")
            start_datum = getattr(produkt, "start_datum", None)
            if start_datum:
                if isinstance(start_datum, str):
                    try:
                        start_datum_text = datetime.strptime(start_datum, "%Y-%m-%d").strftime("%d.%m.%Y")
                    except ValueError:
                        start_datum_text = start_datum
                else:
                    start_datum_text = start_datum.strftime("%d.%m.%Y")
                print(f"  Start der Einzahlungen: {start_datum_text}")
            
            # 1. Annahmen & Kosten dynamisch auslesen
            rendite = getattr(produkt, "erwartete_rendite_prozent", None)
            kosten_rendite = getattr(
                produkt, 
                "kosten_renditeminderung_prozent", 
                getattr(produkt, "kostenquote_prozent", 0.0)
            )
            kosten_beitrag = getattr(produkt, "kosten_beitrag_prozent", 0.0)
            dynamik = getattr(produkt, "dynamik_prozent", 0.0)
            gehaltssteigerung = getattr(produkt, "gehaltssteigerung_prozent", 0.0)
            rentenanpassung = getattr(produkt, "rentenanpassung_prozent", None)
            abgaben = getattr(produkt, "abgaben_typ", "unbekannt")
            fixe_kosten = getattr(produkt, "fixe_verwaltungskosten_monat", 0.0)
            psvag = getattr(
                produkt, 
                "psvag_promille_info", 
                getattr(produkt, "psvag_promille", 0.0)
            )
            
            # 2. Ausgabe der Annahmen & Kosten
            if rendite is not None:
                info_line = f"  [Annahme] Rendite: {rendite:.2f} % p.a. | Renditekosten: {kosten_rendite:.2f} % p.a."
                if dynamik > 0:
                    info_line += f" | Dynamik: {dynamik:.2f} %"
                if gehaltssteigerung > 0:
                    info_line += f" | Gehaltssteigerung: {gehaltssteigerung:.2f} %"
                info_line += f" | Abgabe: {abgaben}"
                print(info_line)
                
                # Zusatzkosten übersichtlich listen
                zusatz_kosten = []
                if kosten_beitrag > 0:
                    zusatz_kosten.append(f"Beitragskosten: {kosten_beitrag:.2f} %")
                if fixe_kosten > 0:
                    zusatz_kosten.append(f"Fix: {fixe_kosten:.2f} €/m")
                if psvag > 0:
                    zusatz_kosten.append(f"PSVaG (AG-Kosten): {psvag:.2f} ‰")
                    
                if zusatz_kosten:
                    print(f"            Zusatzkosten: " + " | ".join(zusatz_kosten))
                
                # 3. Dynamische Staffeln & Stufenpläne ausgeben
                self._drucke_staffel_oder_stufenplan(produkt)
                
            elif rentenanpassung is not None:
                print(f"  [Annahme] Rentenanpassung: {rentenanpassung:.2f} % p.a. | Abgabe: {abgaben}")

            # Optionale benutzerspezifische Ausgabe-Methode für zukünftige Module
            if hasattr(produkt, "drucke_zusatz_infos"):
                produkt.drucke_zusatz_infos()

            # Start-Eigenleistung ausgeben, auch bei Staffel- oder Stufenplänen
            if netto_eigenleistung_start > 0:
                hat_staffel = bool(getattr(produkt, "staffel_beitraege", None) or getattr(produkt, "stufenplan", None))
                if has_staffel := hat_staffel:
                    print(f"  Monatliche Netto-Eigenleistung (aktuell): {netto_eigenleistung_start:7.2f} € / Monat")
                else:
                    print(f"  Monatliche Netto-Eigenleistung:   {netto_eigenleistung_start:7.2f} € / Monat")
            elif not aktiv and getattr(produkt, "start_datum", None):
                print("  Monatliche Netto-Eigenleistung:       noch nicht aktiv")

            if hasattr(produkt, "berechne_monatliche_steuerersparnis"):
                steuerersparnis = produkt.berechne_monatliche_steuerersparnis(self.profil, self.steuer_rechner)
                if steuerersparnis > 0:
                    print(f"  Monatliche Steuerersparnis:      {steuerersparnis:7.2f} € / Monat")
                
            print(f"  Gesamtkapital bei Rente:        {endkapital:11.2f} €")
            print(f"  Zukünftiges Brutto:             {brutto_nominal:7.2f} € / Monat")
            print(f"  Zukünftiges Netto:              {netto_nominal:7.2f} € / Monat")
            print(f"  -> Kaufkraft heute:             {netto_heute:7.2f} € / Monat\n")
            
        print("-" * 65)
        print(f"GESAMTES VERMÖGEN ZUM RENTENEINTRITT:     {gesamt_kapital_zum_renteneintritt:10.2f} €")
        print(f"GESAMTE MONATLICHE SPARBELASTUNG (Start): {gesamte_netto_eigenleistung:7.2f} € / Monat")

        endbelastung = 0.0
        if self.produkte:
            for produkt in self.produkte:
                endbelastung += self._berechne_monatliche_sparbelastung_am_ende(produkt)
        print(f"GESAMTE MONATLICHE SPARBELASTUNG (Ende): {endbelastung:7.2f} € / Monat")

        print(f"GESAMTE RENTE (Kaufkraft heute):          {gesamte_rente_netto_kaufkraft:7.2f} € / Monat")

        ziel = self.profil.wunschrente_heutige_kaufkraft
        print(f"\nZIEL-ABDECKUNG (Bezug auf {ziel:7.2f} € Netto-Ziel):")
        if gesamte_rente_netto_kaufkraft > 0 and ziel > 0:
            anteile_prozent = []
            for name, betrag in anteile:
                anteil = (betrag / ziel) * 100.0
                anteile_prozent.append((name, anteil))
                print(f"  • {name}: {anteil:7.2f} %")

            summe_anteile = sum(anteil for _, anteil in anteile_prozent)
            print("  " + "-" * 34)
            print(f"  SUMME DER BAUSTEINE: {summe_anteile:7.2f} %")

            saldo_prozent = summe_anteile - 100.0
            saldo_euro = gesamte_rente_netto_kaufkraft - ziel
            if saldo_prozent >= 0:
                print(f"🎉 PUFFER: +{saldo_prozent:6.2f} % (+{saldo_euro:7.2f} € / Monat)")
            else:
                print(f"⚠️ FEHLBETRAG: {saldo_prozent:6.2f} % ({saldo_euro:7.2f} € / Monat)")
        else:
            print("  • Keine Renteneinkünfte vorhanden")

        print("\nHinweis zur KVdR im Ruhestand:")
        print("  • Betriebsrenten (bAV/U-Kasse) können in der Auszahlungsphase volle KVdR-Beiträge haben.")
        print("  • Private Produkte wie ETF-Sparplan oder Altersvorsorgedepot sind oft nur kapitalertragsbezogen betroffen und haben typischerweise keine Beiträge auf den Auszahlungsbetrag.")
        
        luecke = self.profil.wunschrente_heutige_kaufkraft - gesamte_rente_netto_kaufkraft
        if luecke > 0:
            print(f"⚠️ RENTENLÜCKE: Dir fehlen kaufkraftbereinigt noch {luecke:.2f} € pro Monat!")