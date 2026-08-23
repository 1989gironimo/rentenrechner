# Rentenrechner

[](LICENSE)[](https://www.python.org/)[](https://github.com/1989gironimo/rentenrechner/actions/workflows/tests.yml)
Live-Beispiel: https://rentenrechner-zhej5b6ppknvwxxhporebd.streamlit.app/

Modularer Python-Baukasten zur **überschlägigen Simulation der eigenen Altersvorsorge, des späteren Renteneinkommens und einer möglichen Rentenlücke**.

Der Rentenrechner kombiniert persönliche Annahmen mit verschiedenen Vorsorgebausteinen. Je nach Produkt werden Beiträge, Rendite, Kosten, Steuern, Sozialabgaben und Förderungen modelliert. Die Berechnung erfolgt monatlich bis zum konfigurierten Renteneintritt.

> [!WARNING]
> **Persönliches und experimentelles Simulationsmodell**
>
> Dieses Projekt ist aus persönlichem Interesse entstanden. Es ist **kein offizieller Rentenrechner und keine individuelle Finanz-, Steuer- oder Rentenberatung**.
>
> Alle Ergebnisse sind Modellrechnungen. Renditen, Inflation, Gehaltsentwicklung, Rentenanpassungen, Steuern und gesetzliche Rahmenbedingungen können künftig erheblich von den verwendeten Annahmen abweichen.

---

## Inhalt

* [Was kann der Rentenrechner?](#was-kann-der-rentenrechner)
* [Unterstützte Vorsorgebausteine](#unterstützte-vorsorgebausteine)
* [Wie funktioniert die Berechnung?](#wie-funktioniert-die-berechnung)
* [Projektstruktur](#projektstruktur)
* [Voraussetzungen](#voraussetzungen)
* [Web-App (Streamlit) – empfohlen](#web-app-streamlit--empfohlen)
  * [Lokale Entwicklung](#lokale-entwicklung)
  * [Veröffentlichung](#veröffentlichung)
* [Kommandozeile (CLI)](#kommandozeile-cli)
  * [Schnellstart](#schnellstart)
  * [Konfiguration](#konfiguration)
* [Profil](#profil)
* [Steuern und Sozialversicherung](#steuern-und-sozialversicherung)
* [Produkte](#produkte)
* [Produktparameter](#produktparameter)
* [Entnahmephase](#entnahmephase)
* [Ausgaben](#ausgaben)
* [Modellannahmen und Grenzen](#modellannahmen-und-grenzen)
* [Datenquellen und Aktualisierung](#datenquellen-und-aktualisierung)
* [Tests](#tests)
* [Eigene Produkte entwickeln](#eigene-produkte-entwickeln)
* [Mitmachen](#mitmachen)
* [Lizenz](#lizenz)

---

## Was kann der Rentenrechner?

Der Rentenrechner kann aktuell:

* ein persönliches Profil konfigurieren,
* Inflation und Gehaltsentwicklung modellieren,
* verschiedene Vorsorgeprodukte kombinieren,
* Beiträge und Beitragsstaffeln abbilden,
* Arbeitgeberzuschüsse und Förderungen berücksichtigen,
* Renditen und Produktkosten modellieren,
* steuerliche und sozialversicherungsrechtliche Effekte berücksichtigen,
* die Entwicklung des Vorsorgekapitals bis zum Renteneintritt simulieren,
* Renten- und Kapitalbausteine aggregieren,
* eine modellierte Entnahmephase berechnen,
* einen ausführlichen Konsolenreport erzeugen und
* die monatliche Projektion als CSV-Datei exportieren.

Produkte sind modular aufgebaut und können über die Konfiguration aktiviert oder deaktiviert werden.

---

## Unterstützte Vorsorgebausteine

Die aktuelle Version enthält folgende Produktarten:

| Produkt                        | Modul                     | Zweck                                                                |
| ------------------------------ | ------------------------- | -------------------------------------------------------------------- |
| Gesetzliche Rentenversicherung | `gesetzliche_rente`       | Fortschreibung eines vorhandenen bzw. konfigurierten Rentenanspruchs |
| Betriebliche Altersvorsorge    | `bav`                     | Modellierung einer bAV mit Eigenbeitrag und Arbeitgeberzuschuss      |
| Altersvorsorge-Depot           | `altersvorsorgedepot`     | Modellierung eines geförderten Vorsorgedepots                        |
| Unterstützungskasse            | `unterstuetzungskasse`    | Modellierung einer Unterstützungskasse                               |
| Privater ETF-Sparplan          | `etf_sparplan`            | Modellierung eines privaten kapitalbildenden Sparplans               |
| Aktienrente / Staatsfonds      | `aktienrente`             | Modellierung eines Aktien-/Staatsfonds-Modells                       |

---

## Wie funktioniert die Berechnung?

Vereinfacht läuft die Berechnung folgendermaßen ab:

```text
app.py (Streamlit)  /  config.json  /  main.py (CLI)
    │
    ▼
Nutzerprofil
    │
    ├── Inflation
    ├── Gehaltsentwicklung
    └── Zielrente
    │
    ▼
Steuer- und Sozialversicherungslogik
    │
    ├── SteuerRechner
    └── Sozialversicherung
    │
    ▼
Produktmodule
    │
    ├── Gesetzliche Rente
    ├── bAV
    ├── Altersvorsorge-Depot
    ├── Unterstützungskasse
    ├── ETF-Sparplan
    └── Aktienrente / Staatsfonds
    │
    ▼
RentenAggregator
    │
    ├── Rentenprojektion
    ├── Brutto-/Netto-Berechnung
    └── Rentenreport
    │
    └── CSV-Export
          │
          ▼
    renten_verlauf.csv
```

Der Einstiegspunkt für die **Web-Oberfläche** ist `app.py`. Für die **Kommandozeile** ist `main.py` zuständig. In beiden Fällen wird das Nutzerprofil erstellt, die Steuerlogik initialisiert und die Produktmodule dynamisch geladen.

Die eigentliche Projektion erfolgt **monatlich**. Beiträge, Rendite und Kosten werden dabei bis zum Renteneintritt fortgeschrieben. Die konkrete steuerliche und sozialversicherungsrechtliche Behandlung hängt vom jeweiligen Produktmodell und den konfigurierten Parametern ab.

---

## Projektstruktur

```text
rentenrechner/
├── core/
│   ├── jahresparameter.py
│   ├── profil.py
│   ├── sozialversicherung.py
│   ├── steuern.py
│   └── ...
│
├── engine/
│   ├── aggregator.py
│   ├── csv_export.py
│   └── ...
│
├── produkte/
│   ├── gesetzliche_rente.py
│   ├── bav.py
│   ├── altersvorsorgedepot.py
│   ├── unterstuetzungskasse.py
│   ├── etf_sparplan.py
│   ├── aktienrente.py
│   └── renten_basis.py
│
├── tests/
│   └── ...
│
├── app.py                 ← Streamlit Web-App (empfohlen)
├── requirements.txt       ← Python-Abhängigkeiten
├── config.example.json    ← Beispielkonfiguration für CLI
├── main.py                ← Kommandozeilen-Einstieg
├── LICENSE
└── README.md
```

### `core/`

Grundlegende Modelle und Berechnungslogik, unter anderem für:

* Nutzerprofil
* Jahresparameter
* Steuern
* Sozialversicherung

### `engine/`

Zentrale Simulations-, Aggregations- und Ausgabe-Logik.

### `produkte/`

Eigenständige Module für die verschiedenen Vorsorgebausteine.

### `tests/`

Automatisierte Tests für die Berechnungslogik und Ausgaben.

---

## Voraussetzungen

* **Python 3.10 oder höher**
* `pytest` für die Tests

Python-Version prüfen:

```bash
python3 --version
```

Für die reine Kommandozeilen-Anwendung werden keine zusätzlichen externen Python-Pakete benötigt. Für die Web-App siehe unten.

---

## Web-App (Streamlit) – empfohlen

Die **interaktive Web-Oberfläche** ist der einfachste Einstieg. Du gibst alle Parameter bequem im Browser ein und löst die Berechnung direkt aus – ohne JSON-Dateien zu editieren.

### Was kann die Web-App?

* **Alle Vorsorgeprodukte** konfigurieren (Gesetzliche Rente, bAV, Altersvorsorge-Depot, Unterstützungskasse, ETF-Sparplan, Aktienrente/Staatsfonds)
* **Beitragsstaffeln und Stufenpläne** dynamisch über Tabellen editieren
* **Zentrales Bruttogehalt** im Profil – wird automatisch von der Aktienrente verwendet
* **Dynamische Kinder-Geburtsjahre** – je nach Anzahl Kinder im Profil werden automatisch die entsprechenden Geburtsjahre-Felder angezeigt
* **Live-Berechnung** mit detailliertem Report, Metriken und CSV-Export

### Voraussetzungen

Zusätzlich zu den bestehenden Abhängigkeiten werden benötigt:

```bash
pip install streamlit pandas
```

Oder über `requirements.txt`:

```text
streamlit
pandas
```

### Lokale Entwicklung

```bash
streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`. Jede Änderung an `app.py` wird nach einem Reload sofort sichtbar.

### Veröffentlichung

Die einfachste Möglichkeit, die App öffentlich zugänglich zu machen, ist die **Streamlit Community Cloud**:

1. Stelle sicher, dass `app.py`, `requirements.txt` und alle Module (`core/`, `engine/`, `produkte/`) im Repository vorhanden sind.
2. Pushe alles auf GitHub:

   ```bash
   git add app.py requirements.txt
   git commit -m "Streamlit Web-App hinzugefügt"
   git push origin main
   ```

3. Gehe zu **[share.streamlit.io](https://share.streamlit.io)** und melde dich mit deinem GitHub-Account an.
4. Klicke auf **„New app"**, wähle dein Repository, den Branch (`main`) und die Datei (`app.py`).
5. Klicke auf **„Deploy"**.

Nach ca. 1–2 Minuten ist die App unter einer öffentlichen URL erreichbar (z. B. `https://rentenrechner-xyz123.streamlit.app`). Bei jedem `git push` wird sie automatisch neu deployed.

> **Hinweis:** `config.json` wird von der Web-App nicht benötigt – alle Eingaben erfolgen über das Formular. Die Datei kann trotzdem parallel für den CLI-Workflow (`main.py`) genutzt werden.

---

## Kommandozeile (CLI)

Alternativ zur Web-App kannst du den Rentenrechner klassisch über eine JSON-Konfigurationsdatei steuern. Das ist besonders nützlich für automatisierte Szenarien, Batch-Berechnungen oder wenn du lieber mit Textdateien arbeitest.

### Schnellstart

Repository klonen:

```bash
git clone https://github.com/1989gironimo/rentenrechner.git
cd rentenrechner
```

Beispielkonfiguration kopieren:

```bash
cp config.example.json config.json
```

`config.json` mit den eigenen Annahmen anpassen und anschließend starten:

```bash
python3 main.py
```

Nach der Berechnung wird zusätzlich folgende Datei erzeugt:

```text
renten_verlauf.csv
```

> `config.json` ist die persönliche Konfiguration und sollte nicht versehentlich in das Repository eingecheckt werden.

### Konfiguration

Die Anwendung wird über eine JSON-Datei gesteuert:

```text
config.json
```

Als Ausgangspunkt dient:

```text
config.example.json
```

Die Konfiguration besteht im Wesentlichen aus drei Bereichen:

```json
{
  "profil": {},
  "steuern": {},
  "produkte": []
}
```

#### Einheiten

Sofern nicht anders angegeben, gelten:

* Geldbeträge: **Euro**
* `*_monat`: **Euro pro Monat**
* `*_jahr`: **Euro pro Jahr**
* `*_prozent`: **Prozent pro Jahr** bzw. entsprechend dem Parameternamen
* `*_datum`: Datum im Format `YYYY-MM-DD`
* `*_monate`: Anzahl Monate

**Wichtig:** Bei Prozentwerten wird beispielsweise `5.0` als **5 %** interpretiert, nicht als `0,05`.

---

## Profil

Im Bereich `profil` werden die persönlichen Rahmenbedingungen festgelegt.

Beispiel:

```json
{
  "profil": {
    "geburtsdatum": "1995-01-01",
    "renteneintrittsdatum": "2062-01-01",
    "wunschrente_heutige_kaufkraft": 3000.0,
    "inflation_prozent": 2.0,
    "aktuelles_brutto_monat": 4500.0,
    "gehaltssteigerung_prozent": 1.5,
    "anzahl_kinder": 2,
    "kindergeburtsjahre": [2018, 2021]
  }
}
```

| Parameter                       | Einheit | Bedeutung                                                     |
| ------------------------------- | ------- | ------------------------------------------------------------- |
| `geburtsdatum`                  | Datum   | Geburtsdatum                                                  |
| `renteneintrittsdatum`          | Datum   | Beginn der modellierten Rentenphase                           |
| `wunschrente_heutige_kaufkraft` | €/Monat | gewünschtes monatliches Renteneinkommen in heutiger Kaufkraft |
| `inflation_prozent`             | % p. a. | angenommene jährliche Inflation                               |
| `aktuelles_brutto_monat`        | €/Monat | aktuelles Bruttogehalt                                        |
| `gehaltssteigerung_prozent`     | % p. a. | angenommene jährliche Gehaltssteigerung                       |
| `anzahl_kinder`                 | Anzahl  | Anzahl der Kinder (relevant für Kinderzulagen)                |
| `kindergeburtsjahre`            | Liste   | Geburtsjahre der Kinder (z. B. `[2018, 2021]`)                |

Die Zielrente wird in **heutiger Kaufkraft** angegeben. Für die Projektion wird sie anhand der konfigurierten Inflationsannahme in die Zukunft fortgeschrieben.

> **Hinweis zu `kindergeburtsjahre`:** Werden Geburtsjahre angegeben, fließen sie altersgenau in die Förderberechnung des Altersvorsorgedepots ein (Kinderzulage gilt bis zum 18. Lebensjahr). Fehlen die Geburtsjahre, wird pauschal `anzahl_kinder × 300 €` pro Jahr angenommen.

---

## Steuern und Sozialversicherung

Im Bereich `steuern` werden die für die Simulation verwendeten Parameter hinterlegt.

Beispiel:

```json
{
  "steuern": {
    "kv_pv_satz_voll": 18.5,
    "kv_pv_satz_ermässigt": 11.3,
    "persoenlicher_steuersatz": 20.0,
    "abgeltungsteuersatz_prozent": 25.0,
    "solidaritaetszuschlag_prozent": 5.5,
    "kirchensteuer_prozent": 0.0,
    "teilfreistellung_prozent": 70.0
  }
}
```

| Parameter                       | Einheit | Bedeutung                                                     |
| ------------------------------- | ------- | ------------------------------------------------------------- |
| `kv_pv_satz_voll`               | %       | angenommener kombinierter KV-/PV-Satz für die volle Belastung |
| `kv_pv_satz_ermässigt`          | %       | angenommener reduzierter KV-/PV-Satz                          |
| `persoenlicher_steuersatz`      | %       | angenommener persönlicher Einkommensteuersatz                 |
| `abgeltungsteuersatz_prozent`   | %       | angenommener Abgeltungsteuersatz                              |
| `solidaritaetszuschlag_prozent` | %       | Solidaritätszuschlag auf die Abgeltungsteuer                  |
| `kirchensteuer_prozent`         | %       | Kirchensteuer; `0.0` bedeutet keine Kirchensteuer             |
| `teilfreistellung_prozent`      | %       | angenommene Teilfreistellung bei Kapitalerträgen              |

### Gesetzliche Werte

Die Anwendung enthält Parameter für gesetzlich bekannte Werte, darunter beispielsweise Beitragsbemessungsgrenzen, Beitragssätze und relevante Freibeträge.

Für zukünftige Jahre sind Werte teilweise **Fortschreibungen bzw. Modellannahmen** und daher keine Prognose zukünftiger Gesetzgebung.

Die Steuerberechnung berücksichtigt unterschiedliche Behandlungswege für rentenähnliche Einkünfte und Kapitalerträge. Insbesondere werden ETF-Erträge getrennt von der gemeinsamen Einkommensteuer der modellierten Rentenbausteine behandelt.

---

## Produkte

Produkte werden als Liste konfiguriert:

```json
{
  "modul_name": "bav",
  "klassen_name": "BetriebsrentebAV",
  "aktiviert": true,
  "parameter": {}
}
```

### `modul_name`

Name des Python-Moduls unter `produkte/`.

### `klassen_name`

Name der Produktklasse, die aus dem Modul geladen werden soll.

### `aktiviert`

Steuert, ob das Produkt in die Berechnung aufgenommen wird.

```json
"aktiviert": false
```

Fehlt das Feld, wird das Produkt standardmäßig aktiviert.

Das aktuelle Programm akzeptiert zusätzlich auch den Schlüssel `enabled`; für neue Konfigurationen wird jedoch `aktiviert` empfohlen.

### `parameter`

Enthält die produktspezifischen Einstellungen.

---

## Produktparameter

### Gesetzliche Rente

Modelliert die Fortschreibung eines vorhandenen bzw. konfigurierten Rentenanspruchs.

```json
{
  "modul_name": "gesetzliche_rente",
  "klassen_name": "GesetzlicheRente",
  "parameter": {
    "aktuelle_rentenansprueche": 1000.0,
    "rentenanpassung_prozent": 1.5,
    "abgaben_typ": "gesetzlich",
    "aktueller_rentenwert": 42.52,
    "durchschnittsentgelt": 51944.0,
    "rv_bbg_jahr": 101400.0
  }
}
```

Wichtige Parameter:

| Parameter                   | Bedeutung                                                |
| --------------------------- | -------------------------------------------------------- |
| `aktuelle_rentenansprueche` | vorhandener bzw. angenommener monatlicher Rentenanspruch |
| `rentenanpassung_prozent`   | angenommene jährliche Rentenanpassung                    |
| `abgaben_typ`               | steuer-/abgabenbezogene Modellklassifikation             |
| `aktueller_rentenwert`      | verwendeter aktueller Rentenwert                         |
| `durchschnittsentgelt`      | verwendetes Durchschnittsentgelt                         |
| `rv_bbg_jahr`               | verwendete jährliche Beitragsbemessungsgrenze            |

> **Wichtig:** Das Modul ersetzt keine individuelle Berechnung anhand des persönlichen Versicherungsverlaufs und keine verbindliche Rentenauskunft.

---

### Betriebliche Altersvorsorge (`bav`)

Unterstützt unter anderem:

* Eigenbeiträge
* Arbeitgeberzuschüsse
* Beitragsstaffeln
* Renditeannahmen
* Kosten
* Startkapital
* Beitragsdynamik
* Steuer- und Sozialversicherungseffekte

Beispielparameter:

```json
{
  "start_datum": "2026-01-01",
  "monatlicher_beitrag_mitarbeiter": 100.0,
  "arbeitgeber_zuschuss_prozent": 15.0,
  "staffel_beitraege": [
    {
      "ab_jahr": 0,
      "eigenbeitrag": 100.0
    }
  ],
  "erwartete_rendite_prozent": 4.0,
  "kostenquote_prozent": 1.03,
  "startkapital": 0.0,
  "startkapital_datum": "2026-01-01",
  "dynamik_prozent": 0.0,
  "abgaben_typ": "bav"
}
```

---

### Altersvorsorge-Depot (`altersvorsorgedepot`)

Unterstützt unter anderem:

* monatliche Eigenbeiträge
* Förderungen (Grundzulage, Kinderzulage, Berufseinsteigerbonus)
* Renditeannahmen
* Kosten

> **Hinweis:** Anzahl und Geburtsjahre der Kinder werden im **Profil** konfiguriert (`anzahl_kinder`, `kindergeburtsjahre`) und fließen automatisch in die Förderberechnung ein.

Beispiel:

```json
{
  "start_datum": "2027-01-01",
  "monatlicher_eigenbeitrag": 150.0,
  "erwartete_rendite_prozent": 6.0,
  "kostenquote_prozent": 0.2,
  "abgaben_typ": "altersvorsorgedepot"
}
```

Die Förderlogik ist Bestandteil des Modells und sollte bei Änderungen der gesetzlichen Rahmenbedingungen überprüft werden.

---

### Unterstützungskasse (`unterstuetzungskasse`)

Unterstützt unter anderem:

* Beitragsstaffeln
* Beschäftigungsbeginn
* Startkapital
* Renditeannahmen
* prozentuale Kosten
* fixe monatliche Kosten

Beispiel:

```json
{
  "start_datum": "2027-01-01",
  "beschaeftigungs_start_datum": "2026-01-01",
  "staffel_beitraege": [
    {
      "ab_jahr": 0,
      "eigenbeitrag": 50.0,
      "ag_beitrag": 50.0
    }
  ],
  "erwartete_rendite_prozent": 4.0,
  "kosten": {
    "renditeminderung_prozent": 2.0,
    "beitrag_prozent": 0.0,
    "fix_monatlich": 0.0,
    "psvag_promille": 0.0
  },
  "startkapital": 0.0,
  "abgaben_typ": "bav"
}
```

Beitragskosten und fixe monatliche Kosten reduzieren den tatsächlich investierten Betrag und werden in der Monatsprojektion berücksichtigt.

---

### ETF-Sparplan (`etf_sparplan`)

Unterstützt unter anderem:

* monatliche Sparrate
* Startkapital
* Renditeannahme
* Kostenquote
* modellierte Besteuerung von Kapitalerträgen

Beispiel:

```json
{
  "start_datum": "2027-01-01",
  "monatlicher_sparplan": 200.0,
  "erwartete_rendite_prozent": 6.0,
  "kostenquote_prozent": 0.2,
  "startkapital": 0.0,
  "abgaben_typ": "etf"
}
```

---

### Aktienrente / Staatsfonds (`aktienrente`)

Das Modell unterstützt unter anderem:

* Startdatum
* Bruttogehalt (aus dem Profil)
* Gehaltsentwicklung
* Stufenpläne
* Renditeannahmen
* Kosten
* Startkapital

Beispiel:

```json
{
  "modul_name": "aktienrente",
  "klassen_name": "StaatsfondsAktienrente",
  "aktiviert": true,
  "parameter": {
    "start_datum": "2028-01-01",
    "stufenplan": [
      {
        "jahr": 2028,
        "an_prozent": 0.25,
        "ag_prozent": 0.25
      },
      {
        "jahr": 2029,
        "an_prozent": 0.50,
        "ag_prozent": 0.50
      },
      {
        "jahr": 2030,
        "an_prozent": 0.75,
        "ag_prozent": 0.75
      },
      {
        "jahr": 2031,
        "an_prozent": 1.00,
        "ag_prozent": 1.00
      }
    ],
    "erwartete_rendite_prozent": 5.0,
    "kostenquote_prozent": 0.1,
    "startkapital": 0.0,
    "abgaben_typ": "gesetzlich"
  }
}
```

---

## Vollständiges Minimalbeispiel

Für einen einfachen Einstieg genügt bereits eine Konfiguration mit einem Produkt:

```json
{
  "profil": {
    "geburtsdatum": "1995-01-01",
    "renteneintrittsdatum": "2062-01-01",
    "wunschrente_heutige_kaufkraft": 3000.0,
    "inflation_prozent": 2.0,
    "aktuelles_brutto_monat": 4500.0,
    "gehaltssteigerung_prozent": 1.5,
    "anzahl_kinder": 0,
    "kindergeburtsjahre": []
  },
  "steuern": {
    "kv_pv_satz_voll": 18.5,
    "kv_pv_satz_ermässigt": 11.3,
    "persoenlicher_steuersatz": 20.0,
    "abgeltungsteuersatz_prozent": 25.0,
    "solidaritaetszuschlag_prozent": 5.5,
    "kirchensteuer_prozent": 0.0,
    "teilfreistellung_prozent": 70.0
  },
  "produkte": [
    {
      "modul_name": "etf_sparplan",
      "klassen_name": "ETFSparplan",
      "aktiviert": true,
      "parameter": {
        "start_datum": "2027-01-01",
        "monatlicher_sparplan": 200.0,
        "erwartete_rendite_prozent": 6.0,
        "kostenquote_prozent": 0.2,
        "startkapital": 0.0,
        "abgaben_typ": "etf"
      }
    }
  ]
}
```

Danach reicht:

```bash
python3 main.py
```

---

## Entnahmephase

Für kapitalbildende Produkte kann zusätzlich eine modellierte Entnahmephase berücksichtigt werden.

Beispiel:

```json
{
  "entnahme_dauer_monate": 300,
  "entnahmezins_p_a": 2.0
}
```

| Parameter               | Einheit | Bedeutung                                        |
| ----------------------- | ------- | ------------------------------------------------ |
| `entnahme_dauer_monate` | Monate  | gewünschter modellierter Entnahmezeitraum        |
| `entnahmezins_p_a`      | % p. a. | angenommene Verzinsung während der Entnahmephase |

Der Standardwert von `300` Monaten entspricht 25 Jahren.

> [!WARNING]
> Die Entnahmephase ist **keine lebenslange Rentengarantie**. Sie zeigt lediglich, welche Entnahme unter den gewählten Modellannahmen über den definierten Zeitraum rechnerisch möglich wäre.

---

## Ausgaben

### Konsolenreport

Der Konsolenreport enthält unter anderem:

* Beiträge
* Renditeannahmen
* Kosten
* Abgaben
* Kapital zum Renteneintritt
* Bruttoeinkommen
* Nettoeinkommen
* Kaufkraft
* Zielrente
* Rentenlücke bzw. Puffer

Produkte mit einem Startdatum in der Zukunft werden entsprechend als noch nicht aktiv behandelt.

### Wie ist das Ergebnis zu verstehen?

Die wichtigsten Größen sind:

**Zielrente**

Das gewünschte monatliche Renteneinkommen in heutiger Kaufkraft.

**Nettoeinkommen**

Das modellierte Einkommen nach den im Modell berücksichtigten Steuern und Sozialabgaben.

**Kaufkraft**

Der auf heutige Euro umgerechnete Wert eines zukünftigen Einkommens. Dieser Wert hängt direkt von der angenommenen Inflation ab.

**Rentenlücke**

Der Betrag, der zwischen dem gewünschten Einkommen und dem modellierten verfügbaren Einkommen fehlt.

**Puffer**

Ein positiver Abstand zwischen modelliertem verfügbaren Einkommen und Zielrente.

Die Werte sind Modellresultate und sollten immer gemeinsam mit den zugrunde liegenden Annahmen betrachtet werden.

---

## CSV-Export

Zusätzlich wird die monatliche Projektion als

```text
renten_verlauf.csv
```

gespeichert.

Die Datei kann beispielsweise mit

* Excel,
* LibreOffice,
* pandas oder
* anderen Datenanalysewerkzeugen

weiterverarbeitet werden.

Damit lassen sich insbesondere Kapitalentwicklung, Beiträge und zeitliche Veränderungen außerhalb des Konsolenreports analysieren.

---

## Modellannahmen und Grenzen

Der Rentenrechner ist ein **persönliches, experimentelles Simulationsmodell**. Er soll Größenordnungen und Szenarien vergleichen und keine amtliche Rentenberechnung oder vollständige professionelle Finanzplanung ersetzen.

### Renditen

Renditen sind Annahmen.

Eine konfigurierte Rendite von beispielsweise `5.0 %` bedeutet nicht, dass tatsächlich jedes Jahr 5 % erreicht werden.

Marktvolatilität, Sequenzrisiken und individuelle Anlageentscheidungen werden nur vereinfacht bzw. nicht vollständig modelliert.

### Inflation

Die zukünftige Inflation wird über einen konfigurierten Prozentsatz modelliert.

Aussagen in „heutiger Kaufkraft" hängen daher direkt von dieser Annahme ab.

### Gehaltsentwicklung

Auch zukünftige Gehaltssteigerungen sind Modellannahmen.

Abweichungen durch beispielsweise

* Arbeitslosigkeit,
* Teilzeit,
* Arbeitgeberwechsel,
* Karriereverlauf oder
* längere Erwerbsunterbrechungen

werden nicht automatisch individuell prognostiziert.

### Gesetzliche Rente

Die gesetzliche Rente wird auf Basis eines vorhandenen bzw. konfigurierten Anspruchs fortgeschrieben.

Das Modul ersetzt keine individuelle Rentenauskunft und keine vollständige Berechnung des persönlichen Versicherungsverlaufs.

### Steuern und Sozialversicherung

Gesetze, Beitragssätze, Freibeträge und Bemessungsgrenzen können sich ändern.

Für zukünftige Jahre sind daher Annahmen und Fortschreibungen erforderlich.

Die in der Konfiguration verwendeten Werte sollten regelmäßig überprüft und bei Bedarf aktualisiert werden.

### Entnahmephase

Die Entnahmephase ist eine mathematische Projektion über einen definierten Zeitraum.

Sie ist nicht mit einer lebenslangen Versicherungsrente oder einer garantierten Auszahlung gleichzusetzen.

---

## Datenquellen und Aktualisierung

Gesetzliche Parameter sollten im Projekt nachvollziehbar und regelmäßig aktualisiert werden.

Dazu gehören insbesondere:

* Beitragsbemessungsgrenzen
* Beitragssätze
* Rentenwerte
* Durchschnittsentgelte
* steuerliche Freibeträge
* Förderbedingungen
* weitere gesetzliche Parameter der Modellrechnung

Bei einer Änderung gesetzlicher Rahmenbedingungen sollten mindestens

1. die entsprechenden Parameter,
2. die Dokumentation,
3. relevante Tests und
4. gegebenenfalls die Modelllogik

überprüft werden.

> **Hinweis für zukünftige Änderungen:** Die im Projekt hinterlegten Werte sind Modellparameter des jeweiligen Entwicklungsstands. Sie sollten nicht als dauerhaft gültige Rechts- oder Finanzdaten interpretiert werden.

---

## Tests

Die Tests befinden sich im Verzeichnis:

```text
tests/
```

Ausführen kannst du sie mit:

```bash
python3 -m pytest -q
```

Der GitHub-Actions-Workflow führt die Tests automatisch aus. Der aktuelle Status ist über das Tests-Badge am Anfang dieser README sichtbar.

Bei Änderungen an der Berechnungslogik sollten passende Tests ergänzt oder angepasst werden.

---

## Eigene Produkte entwickeln

Die modulare Architektur ermöglicht das Hinzufügen eigener Vorsorgeprodukte.

Ein neues Produkt wird grundsätzlich:

1. als Modul unter `produkte/` angelegt,
2. als Klasse implementiert,
3. über `config.json` referenziert und
4. vom Hauptprogramm dynamisch geladen.

Beispiel:

```json
{
  "modul_name": "mein_produkt",
  "klassen_name": "MeinProdukt",
  "aktiviert": true,
  "parameter": {}
}
```

Dadurch können weitere Produktmodelle ergänzt werden, ohne die zentrale Steuerung für jedes neue Produkt zu ändern.

Beim Hinzufügen eines Produkts sollte außerdem dokumentiert werden:

* Zweck und fachliche Annahmen,
* verwendete Parameter und Einheiten,
* steuerliche Behandlung,
* sozialversicherungsrechtliche Behandlung,
* Kostenmodell,
* Entnahme-/Rentenmodell,
* zugehörige Tests.

---

## Mitmachen

Issues und Pull Requests sind willkommen.

Besonders interessant sind Beiträge zu:

* zusätzlichen Produktmodellen,
* Tests,
* Steuer- und Sozialversicherungslogik,
* Validierung der Modellannahmen,
* Szenarioanalysen,
* Visualisierung,
* Dokumentation.

Bei Änderungen an der Berechnungslogik sollten nach Möglichkeit automatisierte Tests ergänzt oder angepasst werden.

Für größere strukturelle Änderungen empfiehlt es sich, zunächst ein Issue zu eröffnen.

---

## Haftungsausschluss

Dieses Projekt dient ausschließlich zu **Informations-, Lern- und Simulationszwecken**.

Die Berechnungen können Fehler, Vereinfachungen oder unvollständige Annahmen enthalten. Gesetzliche Regelungen, Steuern, Sozialversicherungsbeiträge, Rentenwerte, Förderbedingungen und Kapitalmarktrenditen können sich ändern.

Aus den Ergebnissen sollten daher **keine finanziellen Entscheidungen ohne zusätzliche Prüfung** abgeleitet werden.

Der Rentenrechner ersetzt insbesondere keine:

* individuelle Rentenberatung,
* Steuerberatung,
* Finanzberatung,
* Rechtsberatung oder
* verbindliche Auskunft eines Versorgungsträgers.

---

## Lizenz

Dieses Projekt steht unter der **MIT License**.

Der Quellcode darf frei verwendet, kopiert, verändert, veröffentlicht und weitergegeben werden – auch für kommerzielle Zwecke.

Die vollständigen Lizenzbedingungen befinden sich in [`LICENSE`](LICENSE).

---

## Hinweis zur Verwendung

Wenn du dieses Projekt für eigene Berechnungen verwendest, solltest du insbesondere regelmäßig prüfen:

* die gesetzlichen Parameter,
* deine persönlichen Annahmen,
* die Rendite- und Kostenannahmen,
* die Inflationsannahme,
* die steuerlichen Annahmen und
* die Funktionsweise der jeweiligen Produktmodelle.

Der Rentenrechner ist als **offener Ausgangspunkt für eigene Simulationen** gedacht – nicht als verbindliche Prognose der persönlichen finanziellen Zukunft.
