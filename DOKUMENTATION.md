# IUENNA – Knowledge Graph & Corpus Explorer
## Umfassende Gesamtdokumentation aller Entwicklungen, Datenpipelines & Features

Diese Dokumentation beschreibt den aktuellen technischen und funktionalen Stand des **IUENNA Knowledge Graph & Corpus Explorers** einschließlich Datenquellen, Transformationspipelines, semantischem Modell, Weboberflächen, Ask IUENNA, Web Mapping und BYOAI-Schnittstellen. Maßgeblich für archäologische Forschungsdaten und ressourcenspezifische Metadaten bleibt ARCHE; die IUENNA-Webanwendungen bilden darauf aufbauende Discovery-, Visualisierungs- und Retrieval-Schichten.

**Dokumentationsstand:** 12.09.2026. Eingearbeitet sind die am 11.–12.09.2026 vorgenommenen Änderungen an Knowledge Graph, LOD-Runtime, Ask IUENNA/NLP, Remote MCP, BYOAI, `llms.txt`, Zotero-Integration, WMA, Navigation, Datenschutzdarstellung, Startseite und Repository-Verlinkung.

---

## 1. Projekt- & Systemübersicht

* **Projekt:** IUENNA – *openIng the soUthErn jauNtal as a micro-regioN for future Archaeology*
* **Räumlicher Schwerpunkt:** archäologische Mikroregion Jauntal/Podjuna, Kärnten, Österreich
* **Förderung:** Österreichische Akademie der Wissenschaften (ÖAW), Go!Digital 3.0
* **Primärrepositorium:** ARCHE (Austrian Research Culture Heritage Extended, ACDH-CH / ÖAW)
* **Basis-PID:** [https://hdl.handle.net/21.11115/0000-0016-7B39-F](https://hdl.handle.net/21.11115/0000-0016-7B39-F)
* **Gesamtumfang in ARCHE:** 20.788 ARCHE-Einträge, darunter 434 Sammlungen und 20.355 Primärressourcen; Datenvolumen 356,68 GB
* **Knowledge Graph:** 21.071 Knoten und 281.851 Kanten
* **Graph-Audit:** 281.159/281.159 auflösbare konfigurierte ARCHE-Tripel als asserted Beziehungen erhalten; keine doppelten ARCHE-IDs und keine dangling edges
* **Technologie-Stack:** Cytoscape.js, Leaflet/qgis2web, Font Awesome 6, Google Fonts, Python 3, Vanilla JavaScript/CSS, GitHub Pages/GitHub Actions, Cloudflare Workers für den Remote MCP

Die öffentliche Website verbindet mehrere klar getrennte Ebenen:

1. **ARCHE als Source of Record** für archivierte Forschungsdaten, Metadaten, Rechte und persistente Identifikatoren.
2. **Autoritative maschinenlesbare IUENNA-Projektionen** wie `arche_corpus.json`, `arche_graph.json` und die ARCHE-abgeleiteten Entitätsdateien.
3. **Performante Browserprojektionen** für Knowledge Graph und Ask IUENNA, die aus den autoritativen Daten reproduzierbar erzeugt werden.
4. **Web-Mapping-Anwendungen** für die räumliche Exploration.
5. **BYOAI/Remote MCP, OpenAPI und `llms.txt`** für externe LLMs und Agents.

---

## 2. Datenarchitektur & ETL-Pipelines

Die Datenverarbeitung folgt einer reproduzierbaren Kette. Der vollständige ARCHE-RDF/TTL-Bestand wird als maßgebliche Metadatenquelle verarbeitet; daraus werden Korpus, Entitätsindizes, Knowledge Graph, Audits sowie performante Browser- und Remote-Projektionen erzeugt.

```text
ARCHE Top Collection
        │
        ▼
scripts/fetch_arche_full_metadata.py
        │
        ▼
data/arche_full_metadata.ttl
        │
        ▼
scripts/parse_arche_full_ttl.py
        │
        ├── data/arche_collections_tree.json
        ├── data/arche_resolved_entities.json
        ├── data/arche_publications.json
        ├── data/arche_places.json
        ├── data/arche_datasets.json
        └── data/arche_search_index.json
        │
        ├──────────────────────────────────────────────┐
        ▼                                              ▼
scripts/build_authoritative_corpus.py       scripts/build_complete_arche_graph.py
        │                                              │
        ▼                                              ├── data/arche_graph.json
 data/arche_corpus.json                               └── data/arche_graph_audit.json
        │                                              │
        ├── compact browser index                      ▼
        │                                    scripts/build_graph_lod.py
        │                                              │
        ▼                                              ├── data/arche_graph_macro.json
Ask IUENNA / Corpus Browser                            ├── data/arche_graph_lod_manifest.json
                                                       └── data/graph_shards/
                                                              │
                                                              ▼
                                                     graph/data-source.js
                                                              │
                                                              ▼
                                                    Progressive Graph Runtime
```

### 2.1 Zentrale Skripte und Datenartefakte

| Komponente | Ausgabe / Funktion | Beschreibung |
|---|---|---|
| `scripts/fetch_arche_full_metadata.py` | `data/arche_full_metadata.ttl` | Bezieht den autoritativen IUENNA-Metadatengraphen aus der ARCHE-Top-Collection `1792170` über `readMode=relatives`. |
| `scripts/parse_arche_full_ttl.py` | Entitäts-, Orts-, Publikations-, Dataset-, Collection- und Suchindizes | Parst den vollständigen TTL-Bestand. Der kompakte `arche_search_index.json` dient der Discovery und ist nicht mit dem vollständigen Datei-Korpus gleichzusetzen. |
| `scripts/build_authoritative_corpus.py` | `data/arche_corpus.json` | Extrahiert alle **20.355 Primärressourcen** mit ARCHE-ID, PID, Elternsammlung, Breadcrumb, Datierung, Dateityp, Beschreibungen, Schlagworten und Raumbezügen. Dies ist der autoritative IUENNA-Layer für exhaustive File-Level-Retrieval. |
| `scripts/build_complete_arche_graph.py` | `data/arche_graph.json`, `data/arche_graph_audit.json` | Erzeugt die provenance-erhaltende vollständige Graphprojektion und validiert Identitäten, dangling edges, auflösbare Tripel und Predicate Recall. |
| `scripts/build_graph_lod.py` | `arche_graph_macro.json`, `arche_graph_lod_manifest.json`, `graph_shards/` | Erzeugt aus dem vollständigen Graphen die performante Level-of-Detail-Projektion: Struktur-/Kontextgraph beim Start, Primärressourcen collectionweise als Shards. |
| `graph/data-source.js` | progressive Graphdaten-Laufzeit | Lädt initial nur den Makrographen und materialisiert Hierarchieebenen sowie Ressourcen bei Bedarf. Der vollständige Graph bleibt die autoritative semantische Projektion. |
| `graph/layouts.js` | Layout- und Edge-Bundling-Runtime | Steuert progressive Hierarchietiefe, Layouts, Homepage-Palette und hierarchieorientiertes Kanten-Bundling. |
| `scripts/generate_graph_html.py` | `graph/index.html`, `graph/graph.html` | Generiert die produktionsreife Graphoberfläche mit Toolbar, Inspector, Korpus-Katalog, Ordnerbaum und Merkliste. |
| `data/arche_corpus_browser_index.json` | Browserprojektion des Korpus | Kompakter, nicht-autoritativer Index für clientseitige Dateisuche; wird lazy geladen. |
| `scripts/iuenna-chat.js` | Ask IUENNA | Siteweiter clientseitiger Discovery-Assistent mit deterministischem NLP, Dialogkontext und ARCHE-basiertem Retrieval; kein eingebettetes Sprachmodell. |
| `data/mcp_remote/` | Remote-Query-Projektionen | Reproduzierbare, nicht-autoritative Shards/Indizes für den öffentlichen Remote MCP. |

### 2.2 Autoritative Daten und abgeleitete Projektionen

Die Implementierung unterscheidet strikt zwischen Source of Record, autoritativer Projektprojektion und Browser-/Remote-Projektion:

* **ARCHE** bleibt für einzelne Forschungsressourcen, Metadaten, Zugriffsrechte und PIDs maßgeblich.
* `data/arche_corpus.json` ist der vollständige autoritative IUENNA-Primärressourcen-Korpus.
* `data/arche_graph.json` ist die vollständige provenance-erhaltende semantische Graphprojektion.
* `arche_graph_macro.json`, `graph_shards/`, `arche_corpus_browser_index.json` und `data/mcp_remote/` sind Performance-/Query-Projektionen. Sie ersetzen die autoritativen Quellen nicht.
* `arche_search_index.json` ist ein Discovery-Index für Entitäten und zentrale Ressourcen, kein vollständiger Dateiindex.

---

## 3. Durchgeführte Arbeiten & gelöste Herausforderungen

### 3.1 Behebung von Datenfragmentierungen & Fundort-Isolation

Zahlreiche Fundorte waren in früheren Graphständen isoliert, weil Raumbezüge in ARCHE teilweise auf Primärressourcen oder GeoPackages und nicht auf übergeordneten Sammlungen lagen. Die aktuelle Graphpipeline aggregiert diese Bezüge kontrolliert und unterscheidet dabei direkte, geerbte, aggregierte, kuratierte und synthetische Relationen provenance-seitig.

* Alle **219 Fundorte** sind eigenständige Graphknoten.
* Die **9 primären GeoPackages** sind als Forschungsdatensätze integriert.
* Synthetische Navigationsbeziehungen werden nicht fälschlich als asserted `hasSpatialCoverage` ausgegeben.

### 3.2 Vollständige Einbindung des Haupt-GeoPackages `tal_bda_fsdb_2023.gpkg`

* **Kanonische Graph-Knoten-ID:** `res_1804081` mit Rollen `resource` und `dataset`
* **Übergeordneter Ordner:** `05_05_Datenbanken` (`col_1792423`)
* **Urheber:innen:** Bundesdenkmalamt, Dominik Hagmann, René Ployer, Astrid Steinegger
* **Verknüpfte Fachpublikationen:** Tiefengraber 2021 und Hagmann 2024
* **Raumbezug:** 140 Fundorte des Jauntals
* **PID:** `https://hdl.handle.net/21.11115/0000-0016-0E4A-7`

### 3.3 Fundort „Stari Trg“ und flexible ARCHE-ID-Auflösung

Der frühere Fehler `Eintrag [1757171] im Graphen nicht gefunden` wurde beseitigt. Fundorte werden als vollwertige `place`-Knoten geführt; `getNodeByIdFlexible` normalisiert Präfixvarianten und Roh-IDs. Der Inspector kann dadurch ARCHE-ID, Geokoordinaten, GeoNames, Forschungsdatensätze, Sammlungen und räumliche Beziehungen konsistent auflösen.

### 3.4 Korrekte Zuordnung von `6582.tif`

Ein früherer Altzustand ordnete `6582.tif` fälschlich `06_14` zu. Der autoritative Rebuild aus dem ARCHE-TTL weist die Ressource korrekt der Sammlung **„Umschlag von Hans Winkler“** (`1792741`) zu. Die ARCHE-Vorschau wird über den Thumbnail-Dienst eingebunden.

### 3.5 Sprechende Collection-Titel und `col_ret`

Interne numerische Codes werden in Suchindex, Breadcrumbs und Graphlabels durch sprechende ARCHE-Titel ergänzt bzw. ersetzt. Das interne Kürzel `col_ret` wird in der Benutzeroberfläche als **Retrodigitalisat-Collection (RET)** aufgelöst.

### 3.6 Knowledge-Graph-Oberfläche und Inspector

Die Graphoberfläche umfasst:

* einklappbare ARCHE-Dateivorschau;
* hochauflösenden Zoom-/Pan-Viewer für Karten, Pläne und Bildressourcen;
* Fundort-Minikarten und vergrößerbare Leaflet-Karten mit OSM/OpenTopoMap;
* Fundort-Deep-Links in das WMA mit `lat`, `lng` und `zoom`;
* Korpus-Katalog mit dynamischen Fundortfiltern und Trefferzahlen;
* Mehrwortsuche;
* Merkliste mit `localStorage` und Permalink-Unterstützung;
* umschaltbare Knoten-, Kanten- und Relationstexte;
* semantische Kantenlabels;
* Inspector Drawer mit Breitbildmodus, zweispaltigem Layout, Resize-Handle und Tastatursteuerung;
* kontextbezogene Hervorhebung direkter Nachbarknoten und Kanten.

### 3.7 Progressive LOD-Runtime & hierarchieorientiertes Edge Bundling

Am 12.09.2026 wurde die Graphdarstellung grundlegend auf eine progressive **Level-of-Detail-Runtime** umgestellt. Ziel ist, die vollständige Semantik zu erhalten, ohne beim ersten Seitenaufruf alle mehr als 20.000 Primärressourcen und sämtliche Kanten gleichzeitig im Browser zu materialisieren.

#### Progressive Hierarchietiefe

* Beim Start wird `arche_graph_macro.json` geladen.
* Die initiale Makrotiefe beträgt **2**; weitere Collection-Ebenen werden progressiv materialisiert.
* Fundorte werden erst ab einer tieferen Übersichtsebene in den Makrograph aufgenommen, um den First Paint nicht zu überladen.
* Primärressourcen verbleiben in collection-spezifischen Shards unter `data/graph_shards/` und werden bei Bedarf nachgeladen.
* Wird eine Hierarchieebene wieder ausgeblendet, werden zugehörige Resource-Shards aus Cytoscape und aus dem Loader-Zustand entfernt, damit ein späteres erneutes Öffnen korrekt funktioniert.
* `arche_graph_lod_manifest.json` dokumentiert vollständige und lazy geladene Mengen.

#### Layout und Edge Bundling

`graph/layouts.js` behandelt Hierarchie- und semantische Beziehungen bewusst unterschiedlich. Beziehungen innerhalb desselben Top-Level-Collection-Bereichs bleiben weitgehend direkt; nur Beziehungen zwischen unterschiedlichen Top-Level-Bereichen werden hierarchieorientiert gebündelt. Dafür wird ein Routing-Korridor zwischen den beiden Collection-Hubs berechnet, der nur schwach zum IUENNA-Wurzelknoten gewichtet wird. Dadurch bleibt ein dichtes semantisches Netzwerk lesbarer, ohne Beziehungen zu entfernen oder lokale Verbindungen künstlich stark zu krümmen.

* `isPartOf` bleibt als Hierarchiekante separat behandelt.
* Andere Relationen können als `unbundled-bezier` mit berechneten Kontrollpunkten gerendert werden.
* Nach Layoutwechseln oder Wiederherstellung der Preset-Positionen wird das Bundling erneut berechnet.
* Die Kantenkrümmung wurde nach der Einführung nochmals bewusst abgeschwächt, um überzeichnete Bogenführungen zu vermeiden.
* Die visuelle Grundpalette wurde an die IUENNA-Startseite angeglichen; selektierte bzw. hervorgehobene Beziehungen erhalten deutlich höhere Sichtbarkeit.

#### Layout-Fine-Tuning vom 12.09.2026

Der zweite Layout-Tuning-Pass verfolgt das Prinzip **intern kompakter, zwischen Hauptclustern großzügiger, semantische Cross-Links sanft gebündelt**. Er verändert ausschließlich die Browservisualisierung; Knoten, Kanten, Provenienz und der autoritative Graph bleiben unverändert.

| Parameter / Regel | Aktueller Wert | Zweck |
|---|---:|---|
| Initiale Makrotiefe | `2` | Schneller, klarer First Paint; tiefere Hierarchien werden progressiv materialisiert. |
| `isPartOf`-Kanten | `straight` | Hierarchiestruktur bleibt unmittelbar lesbar und wird nicht künstlich gebogen. |
| Lokale semantische Kanten | normales `bezier` | Beziehungen innerhalb desselben Top-Level-Clusters bleiben nahezu direkt. |
| Cross-Collection-Kanten | `unbundled-bezier` | Nur clusterübergreifende Beziehungen werden gebündelt. |
| Root-Einfluss auf Routing-Korridor | `0.22` | Der Wurzelknoten dient nur schwach als Orientierung; ein Radnaben-Effekt wird vermieden. |
| Bundling-Distanzfaktor | `0.36` | Reduziert die seitliche Ablenkung der Kontrollpunkte. |
| Max. Bundling-Abweichung | `min(90 px, 16 % der Kantenlänge)` | Verhindert überzeichnete Bögen bei langen Verbindungen. |
| COSE `componentSpacing` | `170` | Größere visuelle Trennung übergeordneter Bereiche. |
| COSE `gravity` | `0.22` | Schwächerer Zug zum globalen Zentrum. |
| COSE `nestingFactor` | `1.30` | Stärkere hierarchische Gliederung. |
| COSE Iterationen | `1600` | Stabilere Konvergenz des Strukturgraphen. |
| Root-Repulsion | `2,600,000` | Verhindert Verdichtung am Projektwurzelknoten. |
| L1-Repulsion | `1,700,000` | Hält die sechs Hauptsammlungen deutlicher auseinander. |
| L2-Repulsion | `900,000` | Erhält Abstand in der Übersichtsebene. |
| Kontextknoten-Repulsion | `650,000` | Gibt Datasets, Personen, Organisationen, Orte und Publikationen ausreichend Raum. |
| Sonstige Strukturknoten | `420,000` | Tiefere Teilstrukturen bleiben kompakter. |
| `isPartOf`-Ideallänge Root | `235` | Hauptsammlungen liegen deutlich vom Root entfernt. |
| `isPartOf`-Ideallänge L1 | `205` | Top-Level-Cluster erhalten Raum. |
| `isPartOf`-Ideallänge L2 | `130` | Unterstrukturen rücken näher zusammen. |
| `isPartOf`-Ideallänge L3 | `102` | Hierarchie wird mit Tiefe kompakter. |
| `isPartOf`-Ideallänge L4 | `86` | Feinere Folder bleiben lokal gebündelt. |
| `isPartOf`-Ideallänge L5+ | `74` | Tiefste Struktur wird bewusst kompakt gehalten. |
| Sonstige COSE-Kantenlänge | `165` | Semantische Beziehungen bleiben lesbar, ohne Cluster unnötig auseinanderzuziehen. |
| Concentric `minNodeSpacing` | `52` | Weniger Überlagerung bei Ringdarstellung. |
| Breadth-first `spacingFactor` | `1.35` | Hierarchische Ansicht bleibt kompakt, aber lesbar. |
| Circle `spacingFactor` | `1.18` | Vermeidet unnötig weit auseinandergezogene Kreislayouts. |

Die COSE-Kantenelastizität ist ebenfalls hierarchiesensitiv: Root-Verbindungen werden relativ locker (`85`), L1-Verbindungen mit `110`, L2 mit `145` und tiefere `isPartOf`-Verbindungen mit `185` geführt. Nicht-hierarchische Beziehungen verwenden `58`. Damit bleiben tiefe Teilbäume kompakt, während die sechs Hauptbereiche nicht zu stark an den Root gezogen werden.

Das **Preset-Layout bleibt die stabile Referenzansicht**. COSE, Concentric, Hierarchy und Circular sind alternative Explorationslayouts; nach jeder Neuberechnung wird das Edge-Routing erneut aus den aktuellen Knotenpositionen bestimmt.

Damit existieren zwei ausdrücklich getrennte Graphschichten: `arche_graph.json` als vollständige semantische Projektion und die LOD-Dateien als Browserdarstellung.

### 3.8 Ask IUENNA – siteweite ARCHE-Discovery mit deterministischem NLP

**Ask IUENNA** (`scripts/iuenna-chat.js`) ist die englischsprachige, clientseitige Discovery-Oberfläche der Website. Sie ist auf den öffentlichen IUENNA-Hauptseiten eingebunden – Startseite, Web-Mapping-Übersicht, WMA-Wrapper, Knowledge Graph, BYOAI und Legal/Privacy. Eingebettete Karten-Iframes erhalten bewusst keine zweite Assistant-Instanz.

#### Datenbasis und Provenienz

* **Entitätssuche:** `data/arche_search_index.json`, direkt aus dem ARCHE-RDF/TTL-Export erzeugt.
* **Dateisuche:** `data/arche_corpus_browser_index.json`, kompakte Browserprojektion der 20.355 Primärressourcen.
* **Source of Record:** Treffer verlinken zurück nach ARCHE und – soweit sinnvoll – in Knowledge Graph und Web Mapping.
* Ask IUENNA erzeugt **keine neuen archäologischen Fakten** aus einer separaten Wissensbasis und verwendet die früheren experimentellen freien Synthesen nicht mehr als Fachauskunft.

#### Deterministische NLP-Schicht

Nach der Umstellung auf strikt ARCHE-basierte Metadaten-Discovery wurde die frühere Interaktionsfähigkeit gezielt wiederhergestellt, ohne ein Sprachmodell einzubetten. Die NLP-Schicht arbeitet vollständig deterministisch und clientseitig:

* deutsch- und englischsprachige Stopwords;
* Unicode-/Umlautnormalisierung;
* leichtes regelbasiertes Stemming;
* Synonymgruppen für zentrale Retrieval-Konzepte wie Fotografien/Bilder, Pläne/Zeichnungen, Gräber/Bestattungen, Publikationen, Personen, Orte und Geodaten;
* Intent-Erkennung für u. a. Dateisuche, Publikationen, Personen, Urheber:innen, Kartenansicht, Beziehungen und Zählfragen;
* Erkennung kontextabhängiger Follow-up-Fragen;
* Dialogzustand mit zuletzt aufgelöster Entität, Fundort, Kategorie, Intent, Ergebnisart, ARCHE-Link, Koordinaten und Urheber:innen;
* Kontextfortschreibung bei kurzen Folgefragen;
* zeitliche Filterung, darunter Jahrzehnt-Erkennung;
* gewichtetes Ranking mit höherer Priorität für exakte Titel-, Code- und ARCHE-ID-Treffer sowie Intent-spezifische Kategorien.

Damit ist Ask IUENNA wieder dialogisch bedienbar, bleibt aber eine **Retrieval- und Metadata-Discovery-Oberfläche**, kein generatives archäologisches Frage-Antwort-System.

#### Ergebnisdarstellung und Interaktion

* ARCHE-basierte Trefferkarten erhalten kurze, ausschließlich aus angezeigten Metadaten abgeleitete Zusammenfassungen.
* Der Welcome-Bereich zeigt pro Erzeugung **1–2 rotierende Personennamen und 2–3 rotierende Themen**. Die Vorschläge tragen kontextabhängige Font-Awesome-Icons, z. B. Person, Fundort, Foto, Plan, GeoPackage/Datenbank oder Publikation.
* Ein eigener **BYOAI / Remote MCP**-Chip mit Microchip-Icon bleibt als fixer Zugang zur offenen AI-Schnittstelle erhalten.
* Der Assistant kann über einen eigenen **Minimieren-Button** eingeklappt und über den weiterhin sichtbaren „Ask IUENNA“-Trigger wieder geöffnet werden; Verlauf und Dialogkontext bleiben dabei erhalten.
* Rote UI-Flächen – Trigger, Header und User-Bubbles – verwenden kontrastgesicherten weißen bzw. leicht gedämpft weißen Text.
* Dynamisch erzeugte Vorschlags- und Follow-up-Chips werden über einen zentralen, delegierten Click-Handler am Assistant-Fenster verarbeitet. Dadurch funktionieren auch nach Rotation, Reset oder dynamischem Rendern erzeugte Buttons zuverlässig und lösen die entsprechende Assistant-Suche aus.
* Kontextaktionen wie **Search archived files**, **Photos**, **Plans**, **Publications**, **People** und **Map** bleiben damit direkt klickbar und verwenden denselben Retrieval-/Navigationskontext.
* **Knowledge-Graph-Deep-Links:** Assistant-Links werden auf `graph/graph.html?search=…` normalisiert. `graph/corpus-data.js` übernimmt den Suchparameter nach dem Laden, löst die Graphsuche aus und öffnet/fokussiert automatisch den exakten Treffer; falls kein exakter Titel vorhanden ist, wird zunächst ein mit dem Suchstring beginnender und anschließend der bestplatzierte erste Treffer verwendet. Dadurch entfällt ein zusätzlicher Klick in der Graph-Suchbox.
* **Web-Mapping-Deep-Links:** Assistant-Aktionen führen direkt auf `wma/genai-wma-home.html` statt auf die allgemeine Web-Mapping-Übersicht. Der jeweilige Kontext wird als `q`-Parameter an den WMA-Wrapper und weiter an die eingebettete Karte übergeben; vorhandene `lat`, `lng` und `zoom`-Parameter werden in der Ziel-URL erhalten.

#### Session State und Datenschutz

Ask IUENNA läuft clientseitig und sendet Suchtexte nicht an einen externen LLM-Anbieter. Für die Navigation innerhalb derselben Browser-Sitzung werden lokale Zustände in `sessionStorage` geführt, darunter:

* `iuenna_chat_open` – Öffnungszustand;
* `iuenna_chat_history` – dargestellter Sitzungsverlauf;
* `iuenna_chat_dialogue_v31` – deterministischer Dialog-/Follow-up-Kontext.

Es existiert keine projektseitige serverseitige Chat-Historie und kein Modelltraining mit diesen Suchanfragen. Normale Netzwerkzugriffe auf GitHub Pages, ARCHE sowie separat dokumentierte Karten-, CDN- und MCP-Dienste bleiben davon unberührt.

### 3.9 Siteweite Navigation, Web Mapping und UI-Konsolidierung

Die öffentlichen IUENNA-Seiten wurden am 12.09.2026 sprachlich und funktional vereinheitlicht.

* **Navigation:** siteweit kompakte Burger-Navigation auch auf großen Viewports; responsive Darstellung auf kleineren Geräten.
* **WMA:** qgis2web- und AI-assisted-WMA-Wrapper wurden modernisiert und auf konsistente englische UI-Texte umgestellt.
* **Provenienz:** Die AI-assisted WMA beschreibt generative AI korrekt als Entwicklungsunterstützung; die archäologischen Quelldaten selbst werden nicht als KI-generiert dargestellt.
* **Datenschutz:** Angaben zu clientseitigem Assistant, lokal gespeicherten WMA-Filtern, Remote MCP/Cloudflare und lokalen Browser-Speichern wurden präzisiert.
* **Personendarstellung:** akademische Titel wurden in den vereinheitlichten Personenansichten und zugehörigen UI-/Assistant-Texten entfernt; Projektleitung und Forschungsteam werden strukturell getrennt dargestellt.
* **Footer:** direkte Verlinkung des eigentlichen GitHub-Repositories wurde siteweit ergänzt und anschließend bereinigt, damit GitHub Pages und Quellrepository nicht verwechselt werden.

### 3.10 Startseite: Projektfokus, Förderung und BYOAI

Die Projektübersicht auf der Startseite wurde neu gewichtet:

* eigener Abschnitt **Area of Interest** für das Jauntal/Podjuna;
* visuell deutlich hervorgehobener **Funding**-Block bei der Projektleitung;
* explizite Nennung der **Austrian Academy of Sciences (ÖAW)** und direkte Verlinkung des **Go!Digital 3.0 programme**;
* deutlicherer **BYOAI – Bring Your Own AI**-Teaser mit dem Hinweis, IUENNA über den öffentlichen Remote MCP an externe AI-Clients anzubinden;
* die Handlungsaufforderung **„Connect IUENNA to your AI via the public Remote MCP“** wird als eigener violetter Chip dargestellt, damit sie visuell klar von der BYOAI-Hauptüberschrift getrennt bleibt.

Diese Darstellung trennt räumlichen Forschungsfokus, Projektleitung, Förderung und technische Nachnutzung klarer voneinander.

---

## 4. Semantisches Datenmodell im Graphen

### 4.1 Knotentypen (`type`)

* `root` – Top-Collection / IUENNA-Repositorium
* `subcollection`, `folder_l1` bis `folder_l6` – Collection-Hierarchie
* `dataset` – Forschungsdatensätze / GeoPackages
* `place` – Fundorte und geographische Entitäten
* `person` – Personen
* `organization` – Institutionen und Partner
* `publication` – Fachpublikationen / Literaturnachweise
* `resource` – ARCHE-Primärressourcen

### 4.2 Zentrale Kantenrelationen

* `isPartOf` – Sammlungshierarchie und Ressourcenzugehörigkeit
* `hasHosting` – Repositoriums-/Hostingbeziehung
* `hasOwner`, `hasLicensor`, `hasRightsHolder` – Eigentum und Rechte
* `hasCurator` – Kuration
* `hasCreator`, `hasContributor` – Urheber:innen und Mitwirkende
* `hasDepositor`, `hasMetadataCreator`, `hasDigitisingAgent` – Depositing, Metadatenpflege und Digitalisierung
* `hasSpatialCoverage` – asserted Raumbezüge
* `documents` – Dokumentationsbeziehungen
* `hasAuthor` – Publikationsautorschaft
* `isMemberOf` – institutionelle Zugehörigkeit

### 4.3 Provenienzregeln

Graphkanten tragen nicht nur ein semantisches Label, sondern werden nach ihrem Entstehungsstatus unterschieden. Entscheidend ist insbesondere die Trennung zwischen:

* direkt in ARCHE asserted Beziehungen;
* geerbten Beziehungen;
* aggregierten Beziehungen;
* kuratierten Zuordnungen;
* synthetischen Navigationsbeziehungen.

Die LOD-Darstellung verändert diese semantische Provenienz nicht. Sie entscheidet ausschließlich, welche Teile des vollständigen Graphen im Browser aktuell materialisiert werden.

---

## 5. BYOAI – offene Schnittstellen & Agentenzugriff

### 5.1 Konzept

BYOAI (**Bring Your Own AI**) trennt die Forschungsdaten von einem einzelnen proprietären AI-Frontend. IUENNA stellt offene, lesende und dokumentierte Schnittstellen bereit, die von kompatiblen externen LLMs und Agents genutzt werden können.

### 5.2 Remote MCP

Der öffentliche, read-only Remote MCP ist der kanonische MCP-Zugangsweg:

`https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp`

* zustandsloser Streamable-HTTP-MCP;
* Cloudflare Workers Free;
* kein projektspezifischer API-Key;
* kein lokaler Python-/Node-Server erforderlich;
* kanonische Forschungsdaten verbleiben in IUENNA/ARCHE;
* Remote-Projektionen unter `data/mcp_remote/` sind reproduzierbar und nicht autoritativ.

Der frühere lokale/stdio-MCP wurde als offiziell unterstützter Zugangsweg zurückgezogen, nachdem der Remote MCP produktiv verifiziert worden war.

### 5.3 MCP-Fachtools

1. `search_iuenna_corpus` – Volltext-/Metadatensuche über den Primärressourcen-Korpus.
2. `get_findspot_details` – Fundort-Metadaten und verknüpfte kuratierte Datensätze.
3. `get_related_resources` – Auflösung und Traversierung von Fundort, Datensatz, Sammlung oder Publikation zu verbundenen Ressourcen.
4. `get_graph_neighborhood` – Multi-Hop-/Nachbarschaftsabfrage im Knowledge Graph mit Prädikats- und Richtungsfilterung.
5. `get_geodata_catalog` – Katalog der neun GeoPackages.
6. `get_corpus_statistics` – Bestandsstatistik mit expliziter Trennung von ARCHE-Gesamtbestand und 20.355 Primärressourcen.
7. `get_project_bibliography` – Abfrage der öffentlichen IUENNA-Zotero-Bibliothek.

### 5.4 OpenAPI und statische Endpunkte

* `data/openapi.json` – OpenAPI 3.1
* `data/arche_places.json` – 219 Fundorte
* `data/arche_datasets.json` – 9 kuratierte GeoPackages/Forschungsdatensätze
* `data/arche_collections_tree.json` – 434 Sammlungen
* `data/arche_search_index.json` – kompakter Discovery-Index
* `data/arche_graph.json` – vollständige Graphprojektion
* `data/arche_graph_audit.json` – Graph-Audit
* `data/arche_corpus.json` – 20.355 Primärressourcen

### 5.5 `llms.txt`

`https://iuenna.github.io/llms.txt` dient als Routing- und Provenienzschicht für LLMs und Agents. Die Datei dokumentiert:

* Source Priority;
* Retrieval-Strategien;
* Relationship Semantics;
* PID-first-Zitierregeln;
* Trennung zwischen Discovery- und autoritativen Quellen;
* ressourcenspezifische Rechte und Zugriffsbedingungen;
* Remote MCP und Knowledge-Graph-Routing.

### 5.6 Zotero-Bibliothek

Die öffentliche IUENNA-Zotero-Gruppe `4910727` ist in BYOAI, MCP, `llms.txt`, Assistant und Referenzlogik eingebunden. Sie enthält 427+ Titel zu Grabungen, Projektpublikationen, Digital Archaeology, FAIR Data und angrenzenden Themen. Die öffentliche Zotero REST API ermöglicht maschinenlesbare Zitationen u. a. als BibTeX, CSL-JSON, RIS und JSON.

---

## 6. Empfohlene Agent-Routing-Logik

1. **Entität finden:** `arche_search_index.json` oder MCP-Resolver.
2. **Fundortfrage:** `arche_places.json` → `arche_datasets.json` → individueller ARCHE-PID.
3. **Kuratierten Forschungsdatensatz suchen:** `arche_datasets.json`.
4. **Semantische Netzwerke / Multi-Hop-Beziehungen:** `arche_graph.json` oder MCP `get_graph_neighborhood`.
5. **„Alle Dateien/Dokumentationen zu X“:** zusätzlich zwingend `arche_corpus.json` durchsuchen und Collection-Hierarchie berücksichtigen; alternativ MCP `get_related_resources`.
6. **Provenienz:** `parent_id`, `col`/`col_id`, direkte und geerbte Raum-IDs sowie Kanten-`provenance`/`relation_status` beachten.
7. **Zitieren:** nach Möglichkeit individuellen Handle-PID der tatsächlich verwendeten ARCHE-Ressource angeben.
8. **Rechte:** öffentlich erreichbare Discovery-Endpunkte implizieren nicht automatisch offene Binärressourcen oder CC BY 4.0; Rechte und Zugriff sind ressourcenspezifisch zu prüfen.

---

## 7. Konsolidierter Änderungsstand 11.–12.09.2026

Die folgenden Arbeiten sind in dieser Dokumentation nun ausdrücklich berücksichtigt:

* Aufbau und Integration des BYOAI-Hubs, OpenAPI und `llms.txt`;
* Integration der Zotero-Gruppe und Bibliographie-Abfrage;
* Erweiterung des MCP um Knowledge-Graph- und Korpus-Routing;
* Umstellung auf den **öffentlichen Remote MCP als einzigen offiziell unterstützten MCP-Zugangsweg**;
* Aktualisierung und Validierung der autoritativen ARCHE-Daten-, Graph- und AI-Stacks;
* Aufbau von `arche_graph_macro.json`, LOD-Manifest und collectionweisen Resource-Shards;
* Lazy Loading des Korpus-Browserindex und der Graphressourcen;
* progressive Hierarchieebenen im Graphen;
* hierarchieorientiertes Edge Bundling und nachträgliche Abschwächung der Kantenkrümmung;
* Vereinheitlichung von Graphlayout, Palette, Sprache und Performanceverhalten;
* Überarbeitung von WMA-Wrappern, englischer UI und Provenienztexten;
* siteweite Burger-Navigation und konsolidierte Icons/Navigation;
* präzisierte Datenschutzdarstellung für Assistant, Browser-Speicher, WMA und Remote MCP;
* Entfernung bzw. Korrektur unbelegter oder unzutreffender Assistant-Inhalte;
* Umstellung von Ask IUENNA auf ARCHE-basierte Metadata Discovery;
* Wiederherstellung deterministischer NLP-, Intent-, Synonym- und Follow-up-Funktionen ohne Rückkehr zu freien archäologischen Synthesen;
* Grounded Summaries aus angezeigten Metadaten;
* rotierende Assistant-Prompts mit **1–2 Personen und 2–3 Themen**, kontextabhängigen Icons sowie fixem BYOAI-Chip;
* Minimize-Control, Kontrastkorrekturen und zentral delegierte Button-/Chip-Aktionen für dynamisch erzeugte Assistant-Elemente;
* Normalisierung der Assistant-Deep-Links zum Knowledge Graph und direkten GenAI-WMA-Einstieg;
* automatische Auswahl und Fokussierung des passenden Knowledge-Graph-Treffers bei `?search=…`-Deep-Links;
* direkte Übergabe des Assistant-Kontexts per `q` an die AI-assisted WMA;
* Hervorhebung von Projektleitung und Forschungsteam bei vereinheitlichter Personendarstellung;
* stärkere Hervorhebung von Jauntal/Podjuna als Area of Interest;
* deutliche Hervorhebung der ÖAW-/Go!Digital-3.0-Förderung;
* stärkere BYOAI-Kommunikation auf der Startseite einschließlich separatem **„Connect IUENNA to your AI via the public Remote MCP“**-Chip;
* direkte GitHub-Repository-Verlinkung in den Site-Footern.

---

## 8. Deployment & Versionskontrolle

* **Repository:** [https://github.com/IUENNA/IUENNA.github.io](https://github.com/IUENNA/IUENNA.github.io)
* **Branch:** `main`
* **Hosting:** GitHub Pages
* **Automatisierung:** GitHub Actions für Rebuilds, Validierung, Graph-/LOD-Generierung und Daten-Synchronisierung

### Live-URLs

* Startseite: `https://iuenna.github.io/`
* BYOAI Hub: `https://iuenna.github.io/byoai.html`
* Remote MCP: `https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp`
* Knowledge Graph: `https://iuenna.github.io/graph/graph.html`
* alternativer Graph-Einstieg: `https://iuenna.github.io/graph/index.html`
* Web-Mapping-Übersicht: `https://iuenna.github.io/wma/wma.html`
* AI-assisted WMA: `https://iuenna.github.io/wma/genai-wma-home.html`
* qgis2web WMA: `https://iuenna.github.io/wma/qgis2web-home.html`
* Zotero Library: `https://www.zotero.org/groups/4910727/iuenna/library`
* `llms.txt`: `https://iuenna.github.io/llms.txt`
* OpenAPI 3.1: `https://iuenna.github.io/data/openapi.json`
* vollständiger Primärressourcen-Korpus: `https://iuenna.github.io/data/arche_corpus.json`
* vollständiger Knowledge Graph: `https://iuenna.github.io/data/arche_graph.json`
* Graph-Audit: `https://iuenna.github.io/data/arche_graph_audit.json`
* LOD-Makrograph: `https://iuenna.github.io/data/arche_graph_macro.json`
* LOD-Manifest: `https://iuenna.github.io/data/arche_graph_lod_manifest.json`

---

## 9. Wartungsprinzip

Bei künftigen Änderungen sollen Dokumentation und Runtime nicht mehr getrennt fortgeschrieben werden. Änderungen an Datenpipeline, Graphsemantik, Assistant-Retrieval, MCP/API, WMA oder Datenschutz müssen gemeinsam mit den zugehörigen reproduzierbaren Skripten und öffentlichen Beschreibungen aktualisiert werden. Insbesondere dürfen abgeleitete Browser-/Remote-Indizes nicht als neue autoritative Datenquellen beschrieben werden; die Provenienzkette zurück zu ARCHE bzw. den autoritativen IUENNA-Projektionen muss erhalten bleiben.