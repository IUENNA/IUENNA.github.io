# Ask IUENNA – clientseitige ARCHE-Metadaten-Discovery

## Zweck und Provenienz

**Ask IUENNA** ist die clientseitige, dialogorientierte Discovery-Oberfläche der IUENNA-Website. Die Anwendung verwendet **kein Sprachmodell** und erzeugt keine freien archäologischen Synthesen. Sie durchsucht ARCHE-abgeleitete IUENNA-Metadaten und verweist für die fachliche Nachnutzung auf die jeweiligen ARCHE-Datensätze als *source of record*.

Die Entitätssuche basiert auf `data/arche_search_index.json`, der reproduzierbar aus dem ARCHE-RDF/TTL-Metadatenexport erzeugt wird. Für ausdrücklich angeforderte Dateisuchen wird zusätzlich `data/arche_corpus_browser_index.json` als kompakte Browserprojektion des autoritativen Primärressourcen-Korpus verwendet. Die zentrale Implementierung befindet sich in `scripts/iuenna-chat.js`.

## Retrieval-Pipeline

Die Verarbeitung einer Anfrage erfolgt in einer festen Reihenfolge:

1. Normalisierung der Eingabe, einschließlich Kleinschreibung, Entfernung von Diakritika für den Vergleich und Vereinheitlichung von Sonderzeichen.
2. Erkennung explizit genannter Entitäten und Ortsaliase.
3. Intent-Erkennung, etwa für Dateien, Publikationen, Personen, Karten, Urheber:innen oder Beziehungen.
4. Auflösung eines tatsächlichen Follow-ups gegen den Dialogkontext.
5. Deterministisches Entity-Ranking.
6. Falls kein Entitätstreffer vorliegt: Dateisuche im kompakten Primärressourcen-Index.

Damit steht die **explizite Entitätsauflösung vor dem Dialogkontext und vor dem allgemeinen Metadaten-Ranking**. Ein vorheriger Gesprächskontext darf einen neu und eindeutig genannten Ort oder eine andere explizite Entität nicht überschreiben.

## Deterministische Entity-Resolution

Seit der Überarbeitung vom 12. September 2026 verwendet Ask IUENNA eine zusätzliche Prioritätsschicht vor dem bisherigen Metadaten-Score. Die Reihenfolge lautet:

1. **Exakter normalisierter Treffer** auf Label, Code oder ARCHE-ID.
2. **Expliziter IUENNA-Ortsalias**, wobei eine Ortsentität vor einer gleichnamigen Collection/Subcollection priorisiert wird.
3. **Vollständige Anfrage als Bestandteil des Labels**.
4. **Alle primären Suchterme im Label**.
5. Erst danach das bestehende gewichtete Ranking über Label, Sublabel, Kategorie, Code, indexierte Tokens und ARCHE-ID.

Dadurch kann die Menge oder Dichte von Metadaten eines häufig dokumentierten Ortes keinen eindeutigen Ortsnamen mehr überstimmen.

### Aktuell explizit normalisierte Ortsaliase

| Kanonischer Dialogkontext | Erkannte Varianten |
| --- | --- |
| Hemmaberg | `Hemmaberg`, `gora svete Heme` |
| Globasnitz | `Globasnitz`, `Globasnica`, `Iuenna` |
| Jaunstein | `Jaunstein` |
| Sankt Stefan | `Sankt Stefan`, `St. Stefan`, `St Stefan`, `Šteben`, `Steben` |
| Jauntal | `Jauntal`, `Podjuna` |

Die Aliase dienen ausschließlich der Retrieval- und Dialoglogik. Die angezeigten Metadatenwerte bleiben ARCHE-abgeleitet.

## Dialogkontext und Follow-ups

Der Dialogzustand wird ausschließlich im `sessionStorage` des aktuellen Browser-Tabs gehalten. Die aktuelle Zustandskennung lautet `iuenna_chat_dialogue_v32`; damit werden ältere, mit der vorherigen Follow-up-Heuristik gespeicherte Kontexte nicht weiterverwendet.

Eine explizit genannte Entität eröffnet bzw. ersetzt den fachlichen Kontext. Kurze Eingaben werden **nicht mehr allein aufgrund ihrer Länge** als Follow-up interpretiert. Die frühere Heuristik, nach der eine Anfrage mit höchstens drei Tokens bei vorhandenem Kontext automatisch als Follow-up gelten konnte, wurde entfernt.

Als Follow-up gelten weiterhin sprachlich erkennbare Anschlussfragen, beispielsweise:

- `Any photographs?`
- `And from the 1980s?`
- `Who created them?`
- `Weitere?`

Explizite kontextuelle Intents wie „photos“, „publications“ oder „people“ können den vorhandenen Kontext weiterhin verwenden, sofern in derselben Anfrage **keine neue explizite Entität** genannt wird.

## Regressionstest: Sankt Stefan

Der Fehlerfall vom 12. September 2026 entstand durch Kontextübernahme: Nach einer vorherigen Suche zu Hemmaberg wurde die kurze Eingabe `Sankt Stefan` fälschlich als Follow-up interpretiert und intern sinngemäß zu `Sankt Stefan Hemmaberg` erweitert. Dadurch konnte Hemmaberg im allgemeinen Ranking vor dem tatsächlich genannten Ort erscheinen.

Nach der Korrektur gilt:

| Eingabefolge | Erwartetes Verhalten |
| --- | --- |
| `Hemmaberg` → `Sankt Stefan` | neuer Kontext Sankt Stefan; kein Hemmaberg-Follow-up |
| `Hemmaberg` → `St. Stefan` | Auflösung auf Sankt Stefan |
| `Hemmaberg` → `Šteben` | Auflösung auf Sankt Stefan |
| `Hemmaberg` → `Any photographs?` | echtes Follow-up im Kontext Hemmaberg |
| `Hemmaberg` → `photos Sankt Stefan` | Dateisuche mit explizitem neuen Kontext Sankt Stefan |
| exakte ARCHE-ID | exakter Datensatz vor allgemeinem Metadaten-Ranking |

Im aktuellen ARCHE-abgeleiteten Datenbestand ist die Ortsentität **Sankt Stefan / Steben** als `place` vorhanden (ARCHE-ID `1756737`); daneben existiert die eigenständige **Sankt Stefan-Collection (STE)**. Für eine reine Ortsanfrage wird die Place-Entität vor der Collection priorisiert.

## Ergebnisdarstellung

Ask IUENNA zeigt indexierte Metadaten und Links zu ARCHE, Knowledge Graph und – soweit räumliche Metadaten vorhanden sind – Web Mapping. Ergebnislisten können weitere rangierte Treffer enthalten; diese sind Discovery-Hinweise und keine automatisch erzeugte archäologische Interpretation.

Die frühere Zusammenfassung „The closest ARCHE-derived match is …“ wurde entfernt, weil sie auch bei deterministisch aufgelösten Entitäten fälschlich eine bloße Ähnlichkeitssuche suggerierte. Die Oberfläche verwendet nun neutral **„ARCHE-derived result: …“**; weitere Treffer werden weiterhin ausdrücklich als *ranked matches* bezeichnet.

## Fachliche Nachnutzung

Für Zitation, Rechte, Zugriffsbeschränkungen und dauerhafte Identifikatoren ist stets der verlinkte ARCHE-Datensatz maßgeblich. Ask IUENNA ist eine Discovery-Schicht über dem archivierten Bestand und ersetzt weder ARCHE noch eine wissenschaftliche Interpretation der Primärdaten.

## Implementierungsstand

- Entity-/Dialog-Fix: `scripts/iuenna-chat.js`
- Ergebnisformulierung: `scripts/nav.js`
- Entity-/Dialog-Commit: `a3bc1522111d2111350118d1cc2250d84d766607`
- UI-Commit: `1b672127e74606c78a9336f3ce12a92c5accbde3`
- Dokumentation: `ASK_IUENNA.md`, verlinkt aus `README.md`
- Datum: 12. September 2026
