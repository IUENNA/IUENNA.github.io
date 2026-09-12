# IUENNA – Knowledge Graph & Corpus Explorer
## Umfassende Gesamtdokumentation aller Entwicklungen, Datenpipelines & Features

Diese Dokumentation bietet eine lückenlose Übersicht über die Architektur, Datenquellen, Transformationsskripte, semantischen Modelle und Benutzeroberflächen des **IUENNA Knowledge Graph & Corpus Explorers**.

---

## 1. Projekt- & Systemübersicht

* **Projekt:** IUENNA – *openIng the soUthErn jauNtal as a micro-regioN for future Archaeology*
* **Förderung:** Österreichische Akademie der Wissenschaften (ÖAW), Go!Digital 3.0
* **Primärrepositorium:** ARCHE (Austrian Research Culture Heritage Extended, ACDH-CH / ÖAW)
* **Basis-PID:** [https://hdl.handle.net/21.11115/0000-0016-7B39-F](https://hdl.handle.net/21.11115/0000-0016-7B39-F)
* **Gesamtumfang in ARCHE:** 20.788 ARCHE-Einträge (434 Sammlungen, 20.355 Primärressourcen, 356,68 GB Datenvolumen)
* **Technologie-Stack:** Cytoscape.js, Font Awesome 6, Google Fonts (Plus Jakarta Sans & Lora), Python 3 (Streaming-TTL-Parser, Graph-Builder, HTML-Compiler), Vanilla JS / CSS3 (ohne externe Framework-Abhängigkeiten).

---

## 2. Datenarchitektur & ETL-Pipelines

Die Datenverarbeitung erfolgt streng autoritativ und reproduzierbar über eine Kette spezialisierter Python-Skripte im Verzeichnis `scripts/`:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ARCHE Repositorium (ACDH-CH)                           │
│                 Vollständiger TTL-Metadatendump (54,12 MB)                      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
                     scripts/parse_arche_full_ttl.py
                                         │
       ┌──────────────────┬──────────────┼────────────────┬──────────────────┐
       ▼                  ▼              ▼                ▼                  ▼
arche_collections_  arche_resolved_ arche_publica_  arche_places.   arche_datasets.
tree.json (434)     entities.json   tions.json (23) json (219)      json (9 GPKG)
       │                  │              │                │                  │
       └──────────────────┴──────────────┼────────────────┴──────────────────┘
                                         ▼
                     scripts/build_authoritative_corpus.py
                                         │
                                         ▼
                             data/arche_corpus.json
                             (20.355 Primärressourcen)
                                         │
                                         ▼
                     scripts/build_complete_arche_graph.py
                                         │
                                         ▼
                             data/arche_graph.json
                             (Semantisches Netzwerk)
                                         │
                                         ▼
                     scripts/generate_graph_html.py
                                         │
                                         ▼
                             graph/index.html & graph.html
```

### 2.1 Eingesetzte Skripte & Datenartefakte

| Skript | Funktion / Ausgabedatei | Beschreibung |
|---|---|---|
| `scripts/fetch_arche_full_metadata.py` | `data/arche_full_metadata.ttl` | Bezieht den autoritativen IUENNA-Metadatengraphen reproduzierbar aus der ARCHE-Top-Collection `1792170` über `readMode=relatives` im Turtle-Format. |
| `scripts/parse_arche_full_ttl.py` | `data/arche_collections_tree.json`<br>`data/arche_resolved_entities.json`<br>`data/arche_publications.json`<br>`data/arche_places.json`<br>`data/arche_datasets.json`<br>`data/arche_search_index.json` | Parst den reproduzierbar aus ARCHE bezogenen TTL-Vollbestand (ca. 54,12 MB). Extrahiert 434 Sammlungen, 21 Personen, 9 Organisationen, 23 Publikationen, 219 Fundorte und alle 9 GeoPackages inklusive aller Metadaten (ORCID, ROR, Geonames, WKT, PIDs). Der `arche_search_index.json` dient als kompakter semantischer Discovery-Index und ist nicht mit dem vollständigen Datei-Korpus gleichzusetzen. |
| `scripts/build_authoritative_corpus.py` | `data/arche_corpus.json` (ca. 29,66 MB im validierten Rebuild vom 12.09.2026) | Extrahiert alle **20.355 Primärressourcen** aus dem TTL-Vollbestand. Verknüpft jede Ressource mit ihrer echten Elternsammlung, berechnet sprechende Breadcrumbs (ohne `col_ret`), extrahiert PIDs, Datumsangaben, Dateigrößen, Schlagworte und Raumbezüge. Dies ist der autoritative maschinenlesbare Layer für exhaustive File-Level-Retrieval. |
| `scripts/build_complete_arche_graph.py` | `data/arche_graph.json` | Erstellt eine provenance-erhaltende Cytoscape-Graphprojektion. Die konfigurierten ARCHE-Objektprädikate werden nach dem Aufbau aller kanonischen Knoten in einem zweiten Pass aufgelöst; direkte, geerbte, aggregierte, kuratierte und synthetische Relationen bleiben unterscheidbar. Der Build erzeugt zusätzlich `data/arche_graph_audit.json`. |
| `data/arche_graph_audit.json` | Build-Audit | Validiert kanonische ARCHE-Identitäten, dangling edges, auflösbare ARCHE-Tripel und prädikatsweisen Recall. Aktueller Stand: 281,159/281,159 auflösbare Tripel erhalten. |
| `scripts/generate_graph_html.py` | `graph/index.html`<br>`graph/graph.html` (2,3 MB) | Generiert die produktionsreife Webanwendung mit eingebettetem Graphen, interaktiver Toolbar, Detail-Drawer, Korpus-Katalog-Modal, Ordnerbaum-Modal und Merkliste. |
| `scripts/iuenna-chat.js` | UI-Assistent & In-Memory Recherche | Interaktiver schwebender Recherche-Assistent auf der Startseite (`index.html`). Führt clientseitiges Token- & Suffix-Matching gegen die Wissensbasis durch, fasst Metadaten in natürlicher deutscher Sprache zusammen und leitet per Deep-Link in den Graphen, das Web-GIS und ARCHE weiter. |
| `data/iuenna_kb.json` | Wissensbasis des Assistenten | Kompakte JSON-Datenbasis mit 20.000+ Objekten, Fundstellen, Sammlungen, Publikationen und Akteuren inklusive PIDs und Geokoordinaten. |

---

## 3. Durchgeführte Arbeiten & gelöste Herausforderungen

### 3.1 Behebung von Datenfragmentierungen & Fundort-Isolation
* **Problem:** Zuvor waren viele Fundorte (`plc_...`) isoliert im Graphen dargestellt, da Raumbezüge in ARCHE teilweise auf Ressourcen und GeoPackages anstatt auf übergeordneten Ordnern lagen.
* **Lösung:**
  - Aggregation aller Raumbezüge aus den Primärressourcen und Forschungsdatensätzen.
  - Integration aller **9 primären GeoPackages** (u. a. `tal_bda_fsdb_2023.gpkg`, `tal_geodaten_open.gpkg`, Bioarchäologie) als Rauten-Knoten (`dataset`).
  - **Ergebnis:** Alle **219 Fundorte** sind als eigenständige Graphknoten vertreten. Direkte ARCHE-Raumbezüge werden von aggregierten bzw. synthetischen Navigationsbeziehungen provenance-seitig unterschieden; synthetische Navigation wird nicht als `hasSpatialCoverage` ausgegeben.

### 3.2 Vollständige Einbindung des Haupt-GeoPackages `tal_bda_fsdb_2023.gpkg`
* **Kanonische Graph-Knoten-ID:** `res_1804081` (Rollen: `resource`, `dataset`; die kuratierte Dataset-Quelle führt weiterhin `dts_1804081` als Quell-ID).
* **Übergeordneter Ordner:** `05_05_Datenbanken` (TAL, `col_1792423`)
* **Urheber:innen:** Bundesdenkmalamt (`org_1756743`), Dominik Hagmann (`per_1756725`), René Ployer (`per_1756756`), Astrid Steinegger (`per_1756739`)
* **Verknüpfte Fachpublikationen:** Tiefengraber 2021 (`pub_1756783`), Hagmann 2024 (`pub_1757035`)
* **Raumbezug:** Verknüpft mit allen **140 Fundorten des Jauntals** (von Jaunstein über Hemmaberg bis Stari Trg).
* **Exakte APA-Zitationsempfehlung:**
  > *Bundesdenkmalamt, Hagmann, D., Ployer, R., & Steinegger, A. (2025). tal_bda_fsdb_2023.gpkg. In D. Hagmann & F. Reiner (Eds.), IUENNA - openIng the soUthErn jauNtal as a micro-regioN for future Archaeology. ARCHE. Retrieved from https://hdl.handle.net/21.11115/0000-0016-0E4A-7*

### 3.3 Fundort »Stari Trg« (#1757171) & Fehlerbehebung
* **Problem:** Auswahl von Stari Trg (#1757171) führte zu `Eintrag [1757171] im Graphen nicht gefunden`.
* **Lösung:**
  - Fundorte wurden von reinen Metadatenattributen zu vollwertigen Graph-Knoten (`plc_1757171`).
  - `getNodeByIdFlexible` normalisiert alle Präfixe (`plc_`, `place_`, Roh-IDs).
  - Beim Klick öffnet sich der Inspector Drawer mit Koordinaten (`46.50000°, 15.06667°`), Geonames-Link (`#3189942`), dem erfassten Datensatz `tal_geodaten_open.gpkg` sowie allen verorteten Sammlungen (u. a. *Umschlag von Hans Winkler*).

### 3.4 Korrekte Zuordnung & Anzeige von `6582.tif`
* **Problem:** Die Datei `6582.tif` war in einem Altzustand fälschlich unter `06_14` abgelegt.
* **Lösung:**
  - Autoritativer Rebuild aus ARCHE TTL: `6582.tif` ist exakt der Sammlung **`Umschlag von Hans Winkler`** (ARCHE-ID `1792741`, Handle https://hdl.handle.net/21.11115/0000-0016-2AE1-B) zugeordnet.
  - Vorschau über den ARCHE-Thumbnail-Dienst integriert.

### 3.5 Auflösung kryptischer Ordnernamen & `col_ret`
* **Sprechende Titel:** In Suchindex, Breadcrumbs und Graph-Labels werden interne Zifferncodes (z. B. `06_46_157_21`) automatisch durch die vollständigen Titel ersetzt (z. B. **`Skizzenbuch Hans Winkler (II) mit Dokumentationsinformationen`**).
* **`col_ret`-Bereinigung:** Das interne ARCHE-Kürzel `col_ret` wird in allen Breadcrumbs sauber als **`Retrodigitalisat-Collection (RET)`** dargestellt.

### 3.6 Benutzeroberfläche & Interaktion
1. **ARCHE-Dateivorschau (Standardmäßig eingeklappt):** Der Vorschaubereich im Inspector Drawer ist standardmäßig eingeklappt (`(Ausklappen)`), um sofort den Blick auf Kontextmetadaten, Beziehungen und Geodaten freizugeben. Ein Klick klappt die Bildvorschau flüssig auf.
2. **Interaktiver Zoom- & Pan-Viewer für Karten und Pläne:**
   - Eigene Zoom-Bühne (`#quickPreviewModal`) mit schwebender Toolbar (`+`, `-`, Zoom-Stufe in Prozent, `1:1`-Reset).
   - Mausrad-Zoom und Grab-to-Pan (Verschieben mit gedrückter Maustaste).
   - Vollbild-Umschaltung für detaillierte archäologische Dokumentationspläne.
   - Hochauflösender Bildabruf über den ARCHE-Thumbnaildienst (`width=1920`).
3. **Fundort-Karten im Graphen & Großansichts-Modal:**
   - Im Inspector Drawer wird für jeden Fundort eine interaktive Leaflet-Minikarte gerendert.
   - Über den Button *»Vergrößern«* öffnet sich ein 92vw-Modal (`#largePlaceMapModal`) mit umschaltbaren Layern (**OpenStreetMap** und **OpenTopoMap** für Höhendaten) sowie Direktverlinkung ins Web-Mapping-Portal.
4. **Web-Mapping-Portal (WMA) Vollbild & Fundort-Deep-Linking:**
   - Die Live-Karte in `wma/wma.html` besitzt einen Vollbild-Toggle (*»Karte vergrößern / Vollbild«*).
   - Fundorte im Graphen verlinken direkt mit Parametern (`?lat=...&lng=...&zoom=...`) auf das WMA-Portal und zentrieren die Karte dort präzise auf den Fundort.
5. **Dynamische Fundorte im Korpus-Katalog:** Das Dropdown im Katalog befüllt sich dynamisch aus allen 219 Fundorten mit exakten Trefferzahlen.
6. **Mehrwort-Suche:** Die Suche splittet Abfragen in Tokens und wendet eine logische AND-Verknüpfung an.
7. **Merkliste (Auswahl merken):** Ersatz des unhandlichen Forscher:innen-Dropdowns durch einen Button *»Auswahl merken«* und ein interaktives Merklisten-Modal mit Speicherung in `localStorage` und Permalink-Teilfunktion (`?bookmarks=id1,id2`).
8. **Umschaltbare Knoten- und Kantenbeschriftungen & semantische Kantenrelationen:**
   - **Knotentexte umschalten:** Schaltfläche `#btnToggleNodeLabels` in der Toolbar (*»Knotentexte verbergen«* / *»Knotentexte einblenden«*) blendet Beschriftungen aller Knoten auf Knopfdruck aus oder ein.
   - **Kantentexte (Relationen) umschalten:** Schaltfläche `#btnToggleEdgeLabels` (*»Kantentexte verbergen«* / *»Kantentexte einblenden«*) deaktiviert oder aktiviert alle Relationstexte.
   - **Semantische Kanten-Badges:** Kanten tragen ihre Relation (z. B. `isPartOf`, `hasSpatialCoverage`, `documents`, `hasCreator`, `hasSubject`, etc.) als autorotierte Text-Badges mit dezentem Hintergrund und prädikatspezifischen Farben.
   - **Performance-Schutz (`min-zoomed-font-size: 8.5`):** Im Weitwinkel-Überblick (281.851 Kanten) werden keine Kantentexte gezeichnet; bei Heranzoomen an ein Cluster blenden sich die Beziehungsbeschriftungen flüssig ein.
9. **Auditierte ARCHE-Relationen, Provenienz & Canvas-Sichtbarkeit bei Selektion:**
   - **Auditierte Prädikaten-Extraktion aus ARCHE-TTL:** Neben den hierarchischen und Urheber-Beziehungen werden die für IUENNA konfigurierten ARCHE-Objektprädikate verarbeitet: `hasHosting` (zur ÖAW / ARCHE), `hasOwner`, `hasLicensor` und `hasRightsHolder` (zum Landesmuseum Kärnten / kärnten.museum), `hasCurator` (Kuratierende Forscher:innen) sowie `hasDepositor`, `hasMetadataCreator` und `hasDigitisingAgent`.
   - **Validierter Stand:** **21.071 Knoten** und **281.851 Kanten**. Der Audit weist **281.159/281.159** auflösbare konfigurierte ARCHE-Tripel als asserted Kanten nach (Recall 1,0); doppelte ARCHE-IDs und dangling edges: 0.
   - **Garantierte Canvas-Sichtbarkeit:** Wenn Kanten global ausgeblendet sind (*»Kanten verbergen«*), erzwingt das Auswählen eines Knotens via `highlightNeighbors` sofort das Einblenden seiner direkten Beziehungen und Nachbarknoten (`node.connectedEdges().show()`).
10. **Vergrößerbares & stufenlos skalierbares Detail-Popup (Inspector Drawer):**
    - **Breitbildansicht per Button (`#drawerToggleExpandBtn`):** Ein Klick auf den Expand-Button (`<i class="fa-solid fa-expand"></i>`) im Drawer-Header vergrößert das Popup sofort auf eine 2-Spalten-Breitbildansicht (`min(880px, 92vw)`).
    - **Zweispaltiges Ergonomie-Layout:** Links stehen Metadaten, Identifikatoren, Beschreibung und ARCHE-Vorschau; rechts oben thronen prominent die **Verknüpften Entitäten** mit farbigen Kategorie-Badges (`HOSTING`, `EIGENTÜMER`, `LIZENZGEBER`, `KURATOR:IN`, `URHEBER:IN`, `FUNDORT`, etc.), Typ-Icons und Pfeil-Richtungen.
    - **Interaktiver Resize-Handle (`.drawer-resize-handle`):** Der linke Rand des Drawers kann mit der Maus stufenlos von 380px bis fast zur vollen Fensterbreite gezogen werden. Ein Doppelklick toggelt die Breitbildansicht.
    - **Tastatursteuerung:** `Escape` schließt oder verkleinert das geöffnete Panel.

### 3.7 Interaktiver IUENNA Sammlungs-Assistent & Metadaten-Recherche-Engine

Zur intuitiven, niederschwelligen Erkundung des 20.000+ Objekte umfassenden IUENNA-Bestands wurde ein 100 % clientseitiger Recherche-Assistent entwickelt (`scripts/iuenna-chat.js`).

#### 1. Entwicklungsschritte & Architektur-Evolution:
* **Ursprünglicher experimenteller Ansatz:** Test eines browserinternen Small Language Models (SLM: *Qwen 2.5 0.5B Instruct* via HuggingFace Transformers.js, WebGPU und WASM).
* **Praktische Hürden von In-Browser-LLMs im Praxiseinsatz:**
  1. **Hohes Downloadvolumen:** Das Modell erforderte rund 250–300 MB an ONNX-Gewichten, was auf mobilen Endgeräten oder bei schwächerem Empfang zu langen Ladezeiten oder Speicherabstürzen führte.
  2. **Parametrische Halluzinationen:** Ein 0.5B-Modell verfügt über kein fundiertes archäologisches Spezialwissen über Kärntner Mikroregionen. Ohne exakte Grounding-Metadaten neigte es dazu, frei erfundene Bezüge zu Großbritannien, Weltkriegen oder falschen Jahrhunderten zu fabulieren.
  3. **Wissenschaftliche Zielsetzung:** Besucher:innen und Forschende erwarten keine spekulativen KI-Aufsätze, sondern **schnelle, präzise Fakten** und **sofortige Verlinkungen zu den Primärquellen**.
* **Die finale Lösung:** Vollständige Ablösung der ressourcenhungrigen KI-Laufzeit durch eine deterministische, blitzschnelle **Client-Side Metadaten-Synthese-Engine**.

#### 2. Funktionsweise der finalen Engine:
* **Morphologische Relevanz-Suche (`searchKnowledgeBase`):**
  * **Stopword-Filterung:** Bereinigung deutscher Fragestrukturen und Modalverben (*„gab es“*, *„welche“*, *„erzähle mir etwas über“*, *„wer war“*, *„gibt es“*).
  * **Morphologischer Stammformer (`getGermanStem`):** Suffix-Stripping (z. B. *„Münzen“* $\rightarrow$ *„Münz“*), um Flexionen zielsicher auf die echten Katalogtitel abzubilden.
  * **Exaktes Wortgrenzen-Matching:** Verhindert falsche Teilwort-Treffer (z. B. Treffer von *„aufgabe“* bei der Frage *„gab es?“*).
* **Zero-Hit Guard (Gegen Falschinformationen):**
  * Liefert die Suche 0 Treffer (z. B. bei Abfragen wie *„Gibt es Meilensteine?“*, *„Gab es hier Awaren?“*, *„Erzähle mir von den Langobarden“*), wird **kein KI-Text generiert**.
  * Stattdessen erfolgt eine sofortige, variierende Höflichkeitsrückmeldung (z. B. *„Die Anfrage lieferte leider keine Ergebnisse in den Beständen.“* / *„Dazu konnte ich in den IUENNA-Beständen leider keinen passenden Eintrag finden.“*) mitsamt thematischen Schnellwahl-Chips (*Hemmaberg*, *Globasnitz*, *Hans Winkler*).
* **Erweiterte Textglättung & Metadaten-Synthese (`cleanArchaeologicalText` & `formatArchaeologicalSummary`):**
  * **Metadaten-Rauschfilter:** Automatische Bereinigung von technischen Dateiendungen (`.pdf`, `.tif`, `.gpkg`), Ordner-Präfixen (`01_02_`, `HB_`, `GLO_`, `RET_`), Zählklammern, Hierarchie-Tags (`(L1)` bis `(L6)`) und Unterstrichen.
  * **Tautologie- & Dopplungsvermeidung:** Erkennt redundante Ortsnennungen (verhindert *„Münzschatzfund von Globasnitz in Globasnitz“*).
  * **Grammatische Präzision:** Satzmuster verwenden sauber gebeugte Mengenangaben und akkusative Prädikate (*„umfasst 322 römische Münzen“*, *„erschließt 440 Gräber“*).
  * **Kategorienspezifische Synthese:** Maßgeschneiderte Formulierungen für *Münzen/Hortfunde, Bestattungen, Architektur/Befunde, Pläne/Zeichnungen, Personen/Nachlässe und Publikationen*.

* **Kontextsensitive Aktions-Buttons (Smart Action Links):**
  * Statt starrer Dreier-Buttons erzeugt die Engine zielgenaue Aktionen nach Entitätstyp:
    * **Archäologische Befunde & Fundstellen:** `Im Wissensgraphen zeigen 🕸️` + `In Web-GIS ansehen 🗺️` (nur mit gültigen Koordinaten) + `In ARCHE öffnen ↗` (mit Subcollection-PID statt Root-Handle).
    * **Personen & Forscher:innen (z. B. Dr. Hans Winkler):** `Nachlass im Wissensgraphen 🕸️` + `Archivalien in ARCHE ↗` + `Publikationen (Zotero) 📚` + optional gezielter GIS-Link zu konkreten Grabungsorten.
    * **Publikationen & Fachliteratur:** `In Zotero öffnen 📚` (Web-URL zur Zotero-Gruppe 4910727) + `Volltext (PDF) 📄` (falls Direkt-PDF vorhanden) + `Im Wissensgraphen zeigen 🕸️`.
  * **Klickbare Zitations-Referenzen:** Zitate im Ergebniskärtchen (*Referenz: ...*) sind nun anklickbare Links, die direkt den entsprechenden Zotero-Titel oder DOI öffnen.
  * **Resistenz gegen Root-Fallbacks:** Mappt Fundstellen und Ressourcen auf die zuständigen Sammlungs-PIDs (HB, GLO, JAU, STEF, RET, BIO).

#### 3. Datenschutz & DSGVO (Zero-Data-Footprint):
* **100 % Client-Side:** Die gesamte Abfrage und Aufbereitung geschieht ausschließlich im Arbeitsspeicher des Browsers.
* **Keine Speicherung:** Weder `localStorage` noch `sessionStorage` oder Cookies werden für die Chattexte verwendet. Nach einem Neuladen der Seite ist der Chatverlauf restlos gelöscht.
* **Keine externe Datenübertragung:** Weder Suchbegriffe noch IP-Adressen werden an externe Server, LLM-Anbieter oder Tracking-Dienste übermittelt.

#### 4. Vollständige Eliminierung synthetischer KI-Texte (Historische Faktentreue):
* **Ursache historischer Fehlangaben:** In einem frühen Zwischenschritt wurden über ein externes Vorbereitungsskript synthetische Frage-Antwort-Paare (`synthetic_qa`) erzeugt. Dabei generierte ein Sprachmodell fälschlicherweise die Aussage, Notar Hans Winkler sei erst in den *„1920er und 1930er Jahren“* im Jauntal tätig gewesen. Historisch begann Winklers archäologische Feldforschung jedoch bereits **1906** auf dem Hemmaberg (1913 Globasnitz Friedhof, 1930 Badeanlage St. Stefan).
* **Konsequente Bereinigung:** Synthetische Textbausteine wurden vollständig aus dem Suchindex verbannt. Bei Personen- oder Themenanfragen (wie *„Wer war Hans Winkler?“*) liefert die Engine nun ausnahmslos die **originalen ARCHE-Sammlungen** (*Archivalien Hans Winkler*, `col_1792783`, 475 Items; *Skizzenbuch I* `col_1792849`; *Skizzenbuch II* `col_1792850`) mit geprüften Archiv- und Metadatenattributen (*Signatur, Bestandsumfang, Datierung, Ort*).

#### 5. Resiliente Deep-Link-Architektur (100 % funktionale Aktions-Links):
* **Wissensgraph-Navigation mit Dual-Modus:**
  * Klicks auf `Im Wissensgraphen zeigen 🕸️` und `[Im Graph 🕸️]` prüfen zunächst, ob der Knoten im Showcase-Graphen der Startseite (`homeCy`, 58 kuratierte Knoten) vorhanden ist.
  * Falls ja, wird die Kamera dort flüssig zentriert.
  * Falls nein (oder bei Rechtsklick / Neuem Tab), öffnet das Element als valides HTML-`<a>`-Tag mit `target="_blank"` direkt den vollständigen Knowledge Graph Explorer (`graph/index.html?col=${id}&search=${title}`), wo alle 21.071 Knoten des IUENNA-Gesamtbestands instant fokussiert werden.
* **Web-GIS mit Zielkoordinaten:**
  * Der Button `In Web-GIS ansehen 🗺️` übergibt die exakten WGS84-Koordinaten des Fundorts (`wma/wma.html?lat=${lat}&lng=${lng}&zoom=16`), z. B. für Hemmaberg, Globasnitz oder St. Stefan.
* **Echte Handle-PIDs:**
  * `In ARCHE öffnen ↗` verlinkt persistent auf den geprüften Handle-PID des Datensatzes (`https://hdl.handle.net/21.11115/...`).

---

## 4. Semantisches Datenmodell im Graphen

### Knotentypen (`type`):
* `root` (Top-Collection / IUENNA Repositorium) – `#8B2616`
* `subcollection` / `folder_l1` bis `folder_l6` – Farbabstufungen von Rostrot bis Umbra
* `dataset` (Forschungsdatensätze / GeoPackages) – Rautenform, `#1B4965`
* `place` (Geographische Fundorte) – Ellipse, `#4A6B53`
* `person` (Forscher:innen / PIs) – Ellipse, `#C85A32`
* `organization` (Institutionen / Partner) – Rechteck, `#202226`
* `publication` (Fachpublikationen / Literaturnachweise) – Rechteck, `#7B4F36`
* `resource` (ARCHE-Primärdateien) – Rechteck mit Formatfarben (Bild, Vektor, Tabelle etc.)

### Kanten (`label`):
* `isPartOf`: Sammlungshierarchie und Ressourcen-Zugehörigkeit
* `hasHosting`: Repositoriumshosting (z. B. zu ÖAW / ARCHE)
* `hasOwner` / `hasLicensor` / `hasRightsHolder`: Institutionelle Eigentümerschaft und Nutzungsrechte (z. B. Landesmuseum Kärnten)
* `hasCurator`: Kuration von Sammlungen und Funden
* `hasCreator` / `hasContributor`: Beteiligte Urheber:innen und Mitwirkende
* `hasDepositor` / `hasMetadataCreator` / `hasDigitisingAgent`: Datenpflege und Digitalisierung
* `hasSpatialCoverage`: Raumbezüge zu Fundorten (gestrichelt grün)
* `documents`: Dokumentationsnachweis von Publikationen zu Sammlungen/Datensätzen
* `hasAuthor`: Autorschaft bei Publikationen
* `isMemberOf`: Institutionszugehörigkeit von Forscher:innen

### 4.1 BYOAI (Bring Your Own AI): Offene Schnittstellen & Protokolle
* **Konzept:** Vollständige Entkopplung von proprietären Plattformen. Statt Besucher:innen an ein vorgekautes Produkt oder ressourcenintensive In-Browser-Modelle zu binden, stellt IUENNA herstellerneutrale, offene Protokolle und Endpunkte bereit (Motto: *„Bring deine eigene KI mit und befrage unsere Forschungsdaten“*).
* **MCP-Version:** `2.0.0` als öffentlicher, read-only Remote MCP über Streamable HTTP: `https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp`.
* **Retrieval-Prinzip:** `arche_search_index.json` dient der semantischen Entitäts-/Discovery-Suche; `arche_corpus.json` enthält die **20.355 Primärressourcen** und ist die Grundlage für exhaustive File-Level-Suche. Die **20.788 ARCHE-Einträge** bezeichnen den Gesamtbestand des Repositoriums und dürfen nicht mit der Zahl der Primärdateien gleichgesetzt werden.
* **Komponenten:**
  1. **Model Context Protocol (MCP):**
     - Öffentlicher, zustandsloser Remote MCP unter `https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp` mit Streamable HTTP.
     - Kein lokaler Server, keine Python-/Node-Installation und kein projektspezifischer API-Key erforderlich; kompatible AI-Clients verbinden sich direkt mit der HTTPS-URL.
     - Laufzeit über Cloudflare Workers Free; kanonische Forschungsdaten verbleiben auf IUENNA/ARCHE, die Remote-Query-Projektionen unter `data/mcp_remote/` sind nicht-autoritativ und reproduzierbar.
     - Sieben Fach-Tools:
       - `search_iuenna_corpus`: Volltext-/Metadatensuche über `arche_corpus.json` und damit 20.355 Primärressourcen.
       - `get_findspot_details`: Fundort-Metadaten samt direkt verknüpfter kuratierter Datensätze.
       - `get_related_resources`: löst Fundort, Datensatz, Sammlung oder Publikation auf und traversiert Raum-, Collection- und Dokumentationsbeziehungen zu Datensätzen, Sammlungen, Publikationen und einzelnen Primärressourcen.
       - `get_graph_neighborhood`: Traversierung des semantischen Wissensgraphen (21.071 Knoten, 281.851 Kanten) um beliebige indexierte Entitäten mit optionaler Prädikats- und Richtungsfilterung (`all`, `outgoing`, `incoming`).
       - `get_geodata_catalog`: Katalog der 9 autoritativen GeoPackages.
       - `get_corpus_statistics`: Gesamtstatistik mit expliziter Trennung zwischen dem ARCHE-weiten `total_items`-Wert und dem kanonischen Primärressourcen-Korpus von 20.355 Dateien.
       - `get_project_bibliography`: Abfrage der öffentlichen IUENNA-Zotero-Bibliothek.
  2. **OpenAPI 3.1 & Statische REST-Endpunkte:**
     - Spezifikation unter `data/openapi.json`.
     - `arche_places.json`: 219 Fundorte.
     - `arche_datasets.json`: 9 kuratierte GeoPackages/Forschungsdatensätze.
     - `arche_collections_tree.json`: 434 Sammlungen und ihre Parent-Child-Hierarchie.
     - `arche_search_index.json`: kompakter Discovery-Index für Entitäten und zentrale Ressourcen.
     - `arche_graph.json`: 21.071 Knoten und 281.851 Kanten als provenance-erhaltende Graphprojektion; Details und Invarianten stehen in `arche_graph_audit.json`.
     - `arche_corpus.json`: 20.355 Primärressourcen mit ARCHE-ID, PID, Titel/Dateiname, Elternsammlung, Breadcrumb-Pfad, Raumbezug, Schlagworten, Datum, Typ und Beschreibung.
  3. **`llms.txt` (Offener Webstandard):**
     - Bereitstellung von `https://iuenna.github.io/llms.txt` als Routing- und Provenienzschicht für LLMs und Agents.
     - Enthält eine explizite Source-Priority, Retrieval-Strategien, Relationship Semantics, PID-first-Zitierregeln sowie den Hinweis auf ressourcenspezifische Zugriffs- und Lizenzbedingungen.
  4. **BYOAI-Hub (`byoai.html`):**
     - Zentrale englischsprachige Dokumentations- und Rezepte-Seite mit Copy-Paste-Cookbook für lokales Ollama/Llama 3.2, Open-WebUI, cURL/jq, Python/NetworkX und Google NotebookLM.
  5. **Öffentliche Zotero-Bibliothek & REST API:**
     - Gruppe `4910727` (`https://www.zotero.org/groups/4910727/iuenna`) mit 427+ Titeln zu Grabungsberichten, Projektpublikationen, FAIR Data und digitaler Archäologie.
     - Öffentliche REST-API (`https://api.zotero.org/groups/4910727/items`) für maschinenlesbare Zitationen (BibTeX, CSL-JSON, RIS, JSON).

### 4.2 Empfohlene Agent-Routing-Logik

1. **Entität finden:** `arche_search_index.json` oder MCP-Resolver verwenden.
2. **Fundortfrage:** `arche_places.json` → `arche_datasets.json` → ARCHE-PID.
3. **Kuratierten Forschungsdatensatz suchen:** `arche_datasets.json` verwenden.
4. **Semantische Netzwerke / Multi-Hop-Beziehungen:** `arche_graph.json` oder MCP `get_graph_neighborhood` verwenden.
5. **„Alle Daten/Dateien/Dokumentationen zu X“:** zusätzlich zwingend `arche_corpus.json` durchsuchen und `arche_collections_tree.json` traversieren; alternativ MCP `get_related_resources` verwenden.
6. **Provenienz und Archivstruktur:** `parent_id`, `col`/`col_id`, `spatial_ids_direct`, `spatial_ids_inherited`, `spatial_relation_status` sowie Kanten-`provenance`/`relation_status` nachverfolgen.
7. **Zitieren:** nach Möglichkeit den individuellen Handle-PID der tatsächlich verwendeten ARCHE-Ressource angeben; die Discovery-Endpunkte sind nicht Ersatz für die autoritative Repository-Metadatenansicht.
8. **Rechte:** offen zugängliche IUENNA-Discovery-Endpunkte bedeuten nicht, dass jede archivierte Binärressource offen oder CC BY 4.0 lizenziert ist. Zugriff und Rechte sind auf Ressourcenebene zu prüfen.

---

## 5. Deployment & Versionskontrolle

* **Repository:** [https://github.com/iuenna/iuenna.github.io](https://github.com/iuenna/iuenna.github.io)
* **Branch:** `main`
* **Live-URLs:**
  - Startseite / Katalog: `https://iuenna.github.io/`
  - BYOAI Hub: `https://iuenna.github.io/byoai.html`
  - Knowledge Graph: `https://iuenna.github.io/graph/index.html` (sowie `graph.html`)
  - Web Mapping: `https://iuenna.github.io/wma/wma.html`
  - Zotero Library: `https://www.zotero.org/groups/4910727/iuenna/library`
  - AI Web Index: `https://iuenna.github.io/llms.txt`
  - OpenAPI 3.1 Spec: `https://iuenna.github.io/data/openapi.json`
  - Vollständiger Primärressourcen-Korpus: `https://iuenna.github.io/data/arche_corpus.json`
  - Graph-Audit: `https://iuenna.github.io/data/arche_graph_audit.json`
