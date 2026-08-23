# Rentenrechner

Der Rentenrechner ist ein kleines Python-Tool zur groben Planung der privaten Altersvorsorge und der späteren Rentenlücke. Es kombiniert persönliche Annahmen mit verschiedenen Vorsorgeprodukten und zeigt, wie sich die eigene Rente in heutiger Kaufkraft entwickeln könnte.

## Aktueller Stand der Entwicklung

Das Programm kann aktuell:

- eine lokale Konfiguration aus einer JSON-Datei laden,
- ein Nutzerprofil mit Geburtsdatum, Renteneintritt und Zielrente anlegen,
- steuerliche und sozialversicherungsrechtliche Annahmen über ein dynamisches Parameter- und Engine-Modell berücksichtigen,
- verschiedene Vorsorgebausteine dynamisch aus dem Ordner "produkte" laden,
- Brutto-, Netto- und Endkapitalwerte berechnen,
- einen ausführlichen Report in der Konsole ausgeben,
- die monatliche Projektion als CSV-Datei exportieren,
- zeitabhängige Beiträge, Staffeln und Förderungen berücksichtigen und
- einzelne Bausteine über die Konfiguration deaktivieren.


Die Steuer- und Sozialversicherungswerte basieren auf einer modularen Engine (`SozialversicherungsEngine` und `SteuerRechner`). Gesetzlich bekannte Werte für 2026 (inkl. Beitragsbemessungsgrenzen, KV/PV-Sätzen und Freibeträgen wie dem bAV-KV-Freibetrag) werden verwendet; für spätere Jahre werden die Werte als ausdrücklich dokumentierte Modellannahme fortgeschrieben. Die Ausgabe ersetzt keine individuelle Steuer- oder Rentenberatung.

## Was im Report enthalten ist

Der Report enthält unter anderem:

- den Startzeitpunkt der Einzahlungen je Baustein,
- Annahmen zu Rendite, Kosten und Abgaben,
- Staffel- oder Stufenpläne, sofern vorhanden,
- das Gesamtkapital zum Renteneintritt,
- das zukünftige Brutto- und Netto-Renteneinkommen,
- die Kaufkraft in heutigen Euro,
- die Zielabdeckung je Baustein,
- einen Gesamtpuffer oder Fehlbetrag sowie
- einen kurzen Hinweis zur Kranken- und Pflegeversicherung im Ruhestand (KVdR) inkl. Berücksichtigung von Freibeträgen.

Bausteine mit einem Startdatum in der Zukunft werden im Report als „noch nicht aktiv“ angezeigt und bei der aktuellen Sparbelastung nicht berücksichtigt.

## Unterstützte Produktarten

Die aktuelle Version kann diese Bausteine verarbeiten:

- Gesetzliche Rentenversicherung (mit konfigurierbarem aktuellen Rentenwert, Durchschnittsentgelt und BBG)
- Betriebliche Altersvorsorge (bAV)
- Altersvorsorge-Depot
- Unterstützungskasse
- Privater ETF-Sparplan
- Aktienrente / Staatsfonds (Schweden-Modell)

## Funktionsweise

1. Die Datei "config.json" wird geladen.
2. Ein Nutzerprofil sowie die Rechen-Engines für Steuern und Sozialversicherungen werden initialisiert.
3. Die gewünschten Produkte werden über die Einträge in der Konfiguration dynamisch geladen.
4. Der Aggregator berechnet für jedes Produkt die relevanten Werte.
5. Ein zusammengefasster Report wird auf der Konsole ausgegeben.
6. Zusätzlich wird die monatliche Projektion als CSV-Datei in "renten_verlauf.csv" gespeichert.

## Voraussetzungen

- Python 3.10 oder höher
- Keine zusätzlichen Abhängigkeiten sind erforderlich

Für die Tests wird zusätzlich `pytest` benötigt. Im Projekt kann die
Testsuite mit folgendem Befehl ausgeführt werden:

```bash
python3 -m pytest -q
```

## Schnellstart

1. Kopiere die Beispiel-Konfiguration nach "config.json":

```bash
cp config.example.json config.json
```

2. Passe die Werte in "config.json" an deine Situation an.
3. Starte das Programm:

```bash
python3 main.py
```

## Konfigurationsdatei

Die Konfigurationsdatei besteht aus drei Hauptteilen:

- "profil": persönliche Angaben und Zielrente
- "steuern": Annahmen zu Sozialversicherungs- und Steuerbelastung
- "produkte": Liste der Vorsorgeprodukte, die simuliert werden sollen

Ein Beispiel findest du in "config.example.json".

### Steuerparameter

Im Abschnitt "steuern" können folgende Werte gesetzt werden:

- "kv_pv_satz_voll": Kranken- und Pflegeversicherungssatz für volle Belastung
- "kv_pv_satz_ermässigt": ermäßigter Kranken- und Pflegeversicherungssatz
- "persoenlicher_steuersatz": angenommener persönlicher Einkommensteuersatz
- "abgeltungsteuersatz_prozent": Grundsatz für die Abgeltungsteuer auf Kapitalerträge
- "solidaritaetszuschlag_prozent": Solidaritätszuschlag auf die Abgeltungsteuer
- "kirchensteuer_prozent": Kirchensteuer auf die Abgeltungsteuer (0.0 bedeutet keine Kirchensteuer)
- "teilfreistellung_prozent": Anteil der Kapitalerträge, der bei privatem ETF-Sparplan steuerfrei bleibt (z. B. 70 für 70 % Teilfreistellung)

Der Einkommensteuertarif 2026 wird progressiv nach § 32a EStG berechnet. Bei
mehreren steuerpflichtigen Rentenbausteinen wird die Einkommensteuer gemeinsam
ermittelt und anschließend proportional verteilt. ETF-Erträge bleiben davon
getrennt und werden als Kapitalerträge behandelt.

Für die Entgeltumwandlung werden KV, PV, RV und ALV getrennt betrachtet. Die
Beitragsbemessungsgrenzen und Beitragssätze 2026 stammen aus den gesetzlichen
Parametern; unbekannte Folgejahre werden konstant fortgeschrieben.

### Aktivierung einzelner Bausteine

Jeder Eintrag unter "produkte" kann optional deaktiviert werden. Dafür genügt ein Flag wie dieses:

```json
{
  "modul_name": "bav",
  "klassen_name": "BetriebsrentebAV",
  "aktiviert": false,
  "parameter": {
    "start_datum": "2025-01-01"
  }
}
```

Wenn das Feld nicht angegeben wird, wird das Produkt standardmäßig aktiviert.

### Produktparameter im Überblick

#### GesetzlicheRente

- "aktuelle_rentenansprueche": aktuelle Monatsrente, die du aus der gesetzlichen Rentenversicherung erwartest
- "rentenanpassung_prozent": jährliche Anpassung der gesetzlichen Rente
- "abgaben_typ": Abgabentyp, typischerweise "gesetzlich"

#### BetriebsrentebAV

- "start_datum": Beginn der Sparphase
- "monatlicher_beitrag_mitarbeiter": eigener Monatsbeitrag
- "arbeitgeber_zuschuss_prozent": Arbeitgeberzuschuss in Prozent
- "staffel_beitraege": optionale Staffelung der Beiträge über die Jahre
- "erwartete_rendite_prozent": erwartete Rendite pro Jahr
- "kostenquote_prozent": Kostenquote in Prozent
- "startkapital": Startkapital zum Beginn
- "startkapital_datum": Datum des Startkapitals
- "dynamik_prozent": jährliche Dynamik der Beiträge
- "abgaben_typ": Abgabentyp, typischerweise "bav"

#### AltersvorsorgeDepot

- "start_datum": Beginn der Sparphase
- "monatlicher_eigenbeitrag": monatlicher eigener Beitrag
- "anzahl_kinder": optional, Anzahl der Kinder für Kinderzulage
- "kindergeburtsjahre": optionale Liste mit Geburtsjahren, um die Kinderzulage altersabhängig zu berechnen
- Die frühere Option "staatliche_foerderung_prozent" wird ignoriert. Es gilt die
  gesetzliche Zulagenstaffel: 50 % auf die ersten 360 € und 25 % auf die
  nächsten 1.440 € Eigenbeitrag pro Jahr, maximal 540 € Grundzulage.
- "erwartete_rendite_prozent": erwartete Rendite pro Jahr
- "kostenquote_prozent": Kostenquote in Prozent
- "abgaben_typ": Abgabentyp, typischerweise "altersvorsorgedepot"

#### Unterstuetzungskasse

- "start_datum": Beginn der Sparphase
- "staffel_beitraege": Staffelung der Beiträge über die Jahre
- "beschaeftigungs_start_datum": Datum des Beschäftigungsbeginns
- "erwartete_rendite_prozent": erwartete Rendite pro Jahr
- "kosten": Objekt mit Renditekosten, Beitragskosten und Fixkosten
- "startkapital": Startkapital zum Beginn
- "abgaben_typ": Abgabentyp, typischerweise "bav"

Beitragskosten und monatliche Fixkosten reduzieren den tatsächlich investierten
Sparbeitrag und werden auch in der Monatsprojektion berücksichtigt.

#### ETFSparplan

- "start_datum": Beginn der Sparphase
- "monatlicher_sparplan": monatlicher Sparplan-Beitrag
- "erwartete_rendite_prozent": erwartete Rendite pro Jahr
- "kostenquote_prozent": Kostenquote in Prozent
- "startkapital": Startkapital zum Beginn
- "abgaben_typ": Abgabentyp, typischerweise "etf"

#### StaatsfondsAktienrente

- "start_datum": Beginn der Sparphase
- "aktuelles_brutto_monat": aktuelles Bruttogehalt pro Monat
- "gehaltssteigerung_prozent": jährliche Gehaltssteigerung
- "stufenplan": optionale Staffelung von Arbeitgeber- und Arbeitnehmeranteilen über die Jahre
- "erwartete_rendite_prozent": erwartete Rendite pro Jahr
- "kostenquote_prozent": Kostenquote in Prozent
- "startkapital": Startkapital zum Beginn
- "abgaben_typ": Abgabentyp, typischerweise "gesetzlich"

Die Netto-Rente wird anhand der im Abschnitt "steuern" konfigurierten Werte
berechnet. Rendite, Kosten und Beiträge werden monatlich bis zum Renteneintritt
projiziert. Die Entlastung bei einer Entgeltumwandlung berücksichtigt die
Grenzsteuerwirkung und nur die Sozialversicherungszweige, deren
Beitragsbemessungsgrenze tatsächlich noch nicht erreicht ist.

### Entnahmeparameter

Für kapitalbildende Produkte können folgende Parameter gesetzt werden:

- "entnahme_dauer_monate": Standardwert 300 (25 Jahre)
- "entnahmezins_p_a": angenommener Zins während der Entnahmephase

Diese Werte sind Modellannahmen und stellen keine garantierte lebenslange Rente
dar.