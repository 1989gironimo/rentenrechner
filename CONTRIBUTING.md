# Mitmachen

Danke für dein Interesse am Rentenrechner! Issues und Pull Requests sind willkommen.

## Inhaltsverzeichnis

- [Womit du beitragen kannst](#womit-du-beitragen-kannst)
- [Vor dem ersten Beitrag](#vor-dem-ersten-beitrag)
- [Entwicklungsumgebung einrichten](#entwicklungsumgebung-einrichten)
- [Tests](#tests)
- [Pull Requests](#pull-requests)
- [Code-Style](#code-style)

---

## Womit du beitragen kannst

Besonders interessant sind Beiträge zu:

- zusätzlichen Produktmodellen,
- Tests,
- Steuer- und Sozialversicherungslogik,
- Validierung der Modellannahmen,
- Szenarioanalysen,
- Visualisierung,
- Dokumentation.

## Vor dem ersten Beitrag

- Schau zunächst in die [bestehenden Issues](https://github.com/1989gironimo/rentenrechner/issues), ob dein Anliegen bereits diskutiert wird.
- Für größere strukturelle Änderungen empfiehlt es sich, zunächst ein Issue zu eröffnen, bevor du mit der Umsetzung beginnst.

## Entwicklungsumgebung einrichten

```bash
# Repository klonen
git clone https://github.com/1989gironimo/rentenrechner.git
cd rentenrechner

# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Für die Web-App zusätzlich
pip install streamlit pandas
```

### Lokale Entwicklung der Web-App

```bash
streamlit run app.py
```

Die App öffnet sich unter `http://localhost:8501`.

### Lokale Entwicklung der CLI

```bash
python3 main.py
```

## Tests

Bei Änderungen an der Berechnungslogik sollten nach Möglichkeit automatisierte Tests ergänzt oder angepasst werden.

```bash
python3 -m pytest -q
```

Der GitHub-Actions-Workflow führt die Tests automatisch aus.

## Pull Requests

1. Forke das Repository und erstelle einen Feature-Branch:
   ```bash
   git checkout -b feature/dein-feature-name
   ```
2. Committe deine Änderungen mit aussagekräftigen Commit-Nachrichten.
3. Stelle sicher, dass alle Tests bestehen.
4. Öffne einen Pull Request mit einer kurzen Beschreibung der Änderungen.

## Code-Style

- Python-Code folgt PEP 8.
- Docstrings für öffentliche Funktionen und Klassen sind erwünscht.
- Typ-Hinweise (Type Hints) werden nach Möglichkeit verwendet.
