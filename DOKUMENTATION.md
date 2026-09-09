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
| `scripts/parse_arche_full_ttl.py` | `data/arche_collections_tree.json`<br>`data/arche_resolved_entities.json`<br>`data/arche_publications.json`<br>`data/arche_places.json`<br>`data/arche_datasets.json`<br>`data/arche_search_index.json` | Parst in 1,2 Sekunden die 54 MB TTL-Rohdaten. Extrahiert 434 Sammlungen, 21 Personen, 9 Organisationen, 23 Publikationen, 219 Fundorte und alle 9 GeoPackages inklusive aller Metadaten (ORCID, ROR, Geonames, WKT, PIDs). |
| `scripts/build_authoritative_corpus.py` | `data/arche_corpus.json` (17,4 MB) | Extrahiert alle **20.355 Primärressourcen** aus dem TTL-Vollbestand. Verknüpft jede Ressource mit ihrer echten Elternsammlung, berechnet sprechende Breadcrumbs (ohne `col_ret`), extrahiert PIDs, Datumsangaben, Dateigrößen, Schlagworte und Raumbezüge. |
| `scripts/build_complete_arche_graph.py` | `data/arche_graph.json` | Erstellt das Cytoscape-Graphmodell mit vollständiger semantischer Kantenmodellierung (`isPartOf`, `hasCreator`, `hasContributor`, `hasAuthor`, `documents`, `isMemberOf`, `hasSpatialCoverage`). |
| `scripts/generate_graph_html.py` | `graph/index.html`<br>`graph/graph.html` (2,3 MB) | Generiert die produktionsreife Webanwendung mit eingebettetem Graphen, interaktiver Toolbar, Detail-Drawer, Korpus-Katalog-Modal, Ordnerbaum-Modal und Merkliste. |

---

## 3. Durchgeführte Arbeiten & gelöste Herausforderungen

### 3.1 Behebung von Datenfragmentierungen & Fundort-Isolation
* **Problem:** Zuvor waren viele Fundorte (`plc_...`) isoliert im Graphen dargestellt, da Raumbezüge in ARCHE teilweise auf Ressourcen und GeoPackages anstatt auf übergeordneten Ordnern lagen.
* **Lösung:**
  - Aggregation aller Raumbezüge aus den Primärressourcen und Forschungsdatensätzen.
  - Integration aller **9 primären GeoPackages** (u. a. `tal_bda_fsdb_2023.gpkg`, `tal_geodaten_open.gpkg`, Bioarchäologie) als Rauten-Knoten (`dataset`).
  - **Ergebnis:** **219 von 219 Fundorten vollständig vernetzt (0 isolierte Orte)**.

### 3.2 Vollständige Einbindung des Haupt-GeoPackages `tal_bda_fsdb_2023.gpkg`
* **Knoten-ID:** `dts_1804081`
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
1. **Ausklappbare Dateivorschau:** Der Vorschaubereich im Inspector Drawer kann per Klick auf den Header flexibel auf- und zugeklappt werden.
2. **Dynamische Fundorte im Korpus-Katalog:** Das Dropdown im Katalog befüllt sich dynamisch aus allen 219 Fundorten mit exakten Trefferzahlen.
3. **Mehrwort-Suche:** Die Suche splittet Abfragen in Tokens und wendet eine logische AND-Verknüpfung an.
4. **Merkliste (Auswahl merken):** Ersatz des unhandlichen Forscher:innen-Dropdowns durch einen Button *»Auswahl merken«* und ein interaktives Merklisten-Modal mit Speicherung in `localStorage` und Permalink-Teilfunktion (`?bookmarks=id1,id2`).

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
* `hasCreator` / `hasContributor`: Beteiligte Personen und Institutionen
* `hasSpatialCoverage`: Raumbezüge zu Fundorten (gestrichelt grün)
* `documents`: Dokumentationsnachweis von Publikationen zu Sammlungen/Datensätzen
* `hasAuthor`: Autorschaft bei Publikationen
* `isMemberOf`: Institutionszugehörigkeit von Forscher:innen

---

## 5. Deployment & Versionskontrolle

* **Repository:** [https://github.com/iuenna/iuenna.github.io](https://github.com/iuenna/iuenna.github.io)
* **Branch:** `main`
* **Live-URLs:**
  - Startseite / Katalog: `https://iuenna.github.io/`
  - Knowledge Graph: `https://iuenna.github.io/graph/index.html` (sowie `graph.html`)
  - Web Mapping: `https://iuenna.github.io/wma/wma.html`
