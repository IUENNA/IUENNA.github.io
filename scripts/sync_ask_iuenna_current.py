#!/usr/bin/env python3
"""Synchronize Ask IUENNA documentation, privacy text and implementation details."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


# 1) Tighten the assistant implementation: ARCHE links must remain ARCHE links,
# source-language sublabels are not presented as English UI, and corpus counts are dynamic.
rel = "scripts/iuenna-chat.js"
s = read(rel)
s = s.replace(
    "    if (item && item.meta && item.meta.url && /^https?:\\/\\//.test(item.meta.url)) return item.meta.url;\n",
    "",
)
s = s.replace("      valueRow('Context', item.sublabel),\n", "")
s = s.replace(
    "File results come from the compact browser projection of the authoritative 20,355-resource corpus. Use the linked ARCHE record as the source of record.",
    "File results come from the compact browser projection of the authoritative ${corpusIndex.length.toLocaleString()}-resource corpus. Use the linked ARCHE record as the source of record.",
)
write(rel, s)

# 2) Ensure both generated graph entry points are covered by the repeatable installer.
rel = "scripts/enable_ask_iuenna_sitewide.py"
s = read(rel)
if '"graph/graph.html",' not in s:
    s = s.replace('    "graph/index.html",\n', '    "graph/index.html",\n    "graph/graph.html",\n')
write(rel, s)

# 3) Privacy wording must describe the current metadata-only implementation precisely.
privacy_html = '''            <h4>Ask IUENNA (clientseitige Metadatensuche)</h4>
            <p><strong>Ask IUENNA</strong> durchsucht im Browser einen aus den IUENNA-Metadaten in ARCHE erzeugten Discovery-Index; für eine ausdrücklich angeforderte Dateisuche wird zusätzlich ein kompakter Browser-Index des autoritativen Primärressourcen-Korpus geladen. Der Assistent verwendet dabei kein Sprachmodell und erzeugt keine eigenständigen archäologischen Interpretationen. Suchanfragen werden nicht an einen externen LLM-Anbieter übermittelt. Damit Ask IUENNA beim Navigieren innerhalb der Website seinen Sitzungszustand beibehalten kann, werden der Öffnungszustand und der dargestellte Suchverlauf im <code>sessionStorage</code> des aktuellen Browser-Tabs gespeichert (<code>iuenna_chat_open</code> und <code>iuenna_chat_history</code>). Diese lokale Sitzungsinformation wird durch den IUENNA-Code nicht als serverseitige Chat-Historie gespeichert und nicht für Modelltraining verwendet. Sie endet grundsätzlich mit der Browser-Seitensitzung; Funktionen zur Sitzungswiederherstellung des jeweiligen Browsers können eine Sitzung technisch wiederherstellen.</p>'''
rel = "impressum-datenschutz.html"
s = read(rel)
s, n = re.subn(
    r'\s*<h4>(?:Interaktiver Sammlungs-Assistent \(clientseitige Recherche\)|Ask IUENNA \(clientseitige Metadatensuche\))</h4>\s*<p>.*?iuenna_chat_history.*?</p>',
    "\n" + privacy_html,
    s,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("Could not synchronize Ask IUENNA privacy HTML")
write(rel, s)

rel = "impressum-datenschutz.md"
s = read(rel)
s = re.sub(
    r'#### \*\*3\. Interaktiver Sammlungs-Assistent und lokaler Browser-Speicher\*\*\n\n.*?(?=\nIn der AI-assisted Web-Mapping-Anwendung)',
    '''#### **3. Ask IUENNA und lokaler Browser-Speicher**

**Ask IUENNA** durchsucht im Browser einen aus den IUENNA-Metadaten in ARCHE erzeugten Discovery-Index; für eine ausdrücklich angeforderte Dateisuche wird zusätzlich ein kompakter Browser-Index des autoritativen Primärressourcen-Korpus geladen. Der Assistent verwendet dabei kein Sprachmodell und erzeugt keine eigenständigen archäologischen Interpretationen. Suchanfragen werden nicht an einen externen LLM-Anbieter übermittelt. Zur Sitzungsfortsetzung speichert die Oberfläche den Öffnungszustand und den dargestellten Suchverlauf im `sessionStorage` des aktuellen Browser-Tabs (`iuenna_chat_open`, `iuenna_chat_history`). Diese Daten werden durch den IUENNA-Code nicht als serverseitige Chat-Historie gespeichert und nicht für Modelltraining verwendet. Die Speicherung endet grundsätzlich mit der Browser-Seitensitzung; Browser-Funktionen zur Sitzungswiederherstellung können eine Sitzung technisch wiederherstellen.

''',
    s,
    count=1,
    flags=re.S,
)
write(rel, s)

# 4) Replace the obsolete assistant chapter with the actual 3.0 architecture.
rel = "DOKUMENTATION.md"
s = read(rel)
section = '''### 3.7 Ask IUENNA – siteweite ARCHE-Metadatensuche

**Ask IUENNA** (`scripts/iuenna-chat.js`) ist die englischsprachige, clientseitige Discovery-Oberfläche der Website. Sie ist auf allen öffentlichen IUENNA-Hauptseiten eingebunden: Startseite, Web-Mapping-Übersicht, beide WMA-Wrapper, Knowledge Graph (`graph/index.html` und `graph/graph.html`), BYOAI sowie Legal/Privacy. Die eingebetteten Karten-Dokumente innerhalb der WMA werden bewusst nicht mit einer zweiten Instanz versehen, damit der Assistent in `iframe`-Ansichten nicht doppelt erscheint.

#### Datenbasis und Provenienz
* **Entitätssuche:** `data/arche_search_index.json` (ca. 0,5 MB), reproduzierbar direkt aus dem vollständigen ARCHE-RDF/TTL-Metadatenexport erzeugt. Der Index enthält Personen, Organisationen, Sammlungen/Ordner, Publikationen, Fundorte und kuratierte Forschungsdatensätze.
* **Dateisuche:** `data/arche_corpus_browser_index.json`, eine kompakte, ausdrücklich nicht-autoritative Browserprojektion des autoritativen `data/arche_corpus.json` mit aktuell 20.355 Primärressourcen. Sie wird erst bei einer Dateisuche bzw. bei ausbleibenden Entitätstreffern nachgeladen.
* **Source of record:** Ergebnislisten verlinken zurück nach ARCHE sowie – je nach Entität – in den Knowledge Graph und das Web Mapping. Für Zitation, Rechte und Zugriffsbedingungen bleibt der jeweilige ARCHE-Datensatz maßgeblich.

#### Keine generative Fachauskunft
Ask IUENNA führt **kein Sprachmodell** aus und formuliert **keine eigenständigen archäologischen Synthesen**. Frühere experimentelle hart codierte bzw. synthetisch erzeugte Fachtexte sind nicht mehr Teil der Antwortlogik. Die Oberfläche zeigt ausschließlich indexierte Metadatenfelder (z. B. Titel, Typ, ARCHE-ID, PID, Bestandsumfang, Datierung, Urheber:innen, Dateiformat, Fundort) und kennzeichnet die Ergebnisse als Metadata Discovery.

#### Suche und Performance
* Der kleine ARCHE-Discovery-Index wird beim Laden von Ask IUENNA vorbereitet.
* Die Suche normalisiert Schreibweisen und gewichtet exakte Titel-/Code-/ARCHE-ID-Treffer höher als Teiltreffer.
* Der größere Primärressourcen-Index wird lazy geladen, um die normale Seitennutzung nicht mit einem ca. 12,8-MB-Download zu belasten.
* Ergebnisse sind limitiert und dienen der Discovery; exhaustive Retrieval-Aufgaben können über den öffentlichen Remote MCP oder den vollständigen autoritativen Korpus erfolgen.

#### Datenschutz
* Die Suche läuft clientseitig; Suchtexte werden von Ask IUENNA nicht an einen externen LLM-Anbieter gesendet.
* Öffnungszustand und dargestellter Suchverlauf werden zur Navigation innerhalb derselben Browser-Sitzung in `sessionStorage` unter `iuenna_chat_open` und `iuenna_chat_history` gehalten.
* Es gibt keine projektseitige serverseitige Chat-Historie und kein Modelltraining mit den Suchanfragen.
* Normale Netzwerkzugriffe auf GitHub Pages/ARCHE sowie die gesondert dokumentierten externen Karten-, CDN- und MCP-Dienste bleiben davon unberührt.

#### BYOAI-Abgrenzung
Ask IUENNA ist die leichte Website-Discovery. Wer IUENNA mit einem eigenen LLM oder Agenten abfragen möchte, nutzt den öffentlichen, read-only Remote MCP unter `https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp`; die Dokumentation befindet sich auf `byoai.html`.
'''
s, n = re.subn(
    r'### 3\.7 .*?\n\n---\n\n## 4\.',
    section + '\n\n---\n\n## 4.',
    s,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("Could not replace obsolete Ask IUENNA documentation section")
write(rel, s)

# 5) Prevent the older UI refresh helper from reintroducing obsolete terminology.
rel = "scripts/refresh_site_ui.py"
s = read(rel)
s = s.replace('»Frag IUENNA«', '»Ask IUENNA«')
s = s.replace(
    'durchsucht und synthetisiert die veröffentlichten IUENNA-Metadaten clientseitig im Browser; Chatfragen werden dabei nicht an einen externen LLM-Anbieter gesendet.',
    'durchsucht ARCHE-abgeleitete IUENNA-Metadaten clientseitig im Browser; der Assistent verwendet dabei kein Sprachmodell und erzeugt keine eigenständigen archäologischen Interpretationen. Suchanfragen werden nicht an einen externen LLM-Anbieter gesendet.',
)
write(rel, s)

print('[OK] Ask IUENNA implementation, privacy disclosure and documentation synchronized.')
