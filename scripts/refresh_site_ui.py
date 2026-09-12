#!/usr/bin/env python3
"""Synchronize public IUENNA UI conventions and factual disclosure text.

This script intentionally touches only maintained public surfaces. It keeps the
sitewide burger-navigation rule, WMA language metadata, browser-tab icons, and
privacy/AI-development wording aligned with the current implementation.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing expected text: {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Sitewide navigation: burger menu at every viewport width.
# ---------------------------------------------------------------------------
css_rel = "styles.css"
css = read(css_rel)
marker = "/* IUENNA sitewide compact burger navigation */"
if marker not in css:
    css += """

/* IUENNA sitewide compact burger navigation */
.nav-toggle {
  display: inline-flex !important;
}

.nav-menu {
  position: absolute !important;
  top: calc(100% + 0.7rem) !important;
  right: 0 !important;
  left: auto !important;
  width: min(410px, calc(100vw - 2rem)) !important;
  background-color: rgba(250, 248, 245, 0.985) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-md) !important;
  padding: 0.65rem !important;
  max-height: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
  transform: translateY(-6px);
  transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease, transform 0.2s ease !important;
  z-index: 1100 !important;
}

.nav-menu.is-active {
  max-height: min(620px, calc(100vh - 100px)) !important;
  overflow-y: auto !important;
  opacity: 1 !important;
  pointer-events: auto !important;
  transform: translateY(0);
}

.nav-menu .nav-links {
  width: 100% !important;
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 4px !important;
}

.nav-menu .nav-link {
  display: flex !important;
  width: 100% !important;
  align-items: center !important;
  gap: 12px !important;
  padding: 10px 12px !important;
  font-size: 0.92rem !important;
  border: 1px solid transparent;
}

.nav-menu .nav-link i {
  width: 22px;
  text-align: center;
  flex: 0 0 22px;
}

.nav-menu .nav-link.btn {
  justify-content: center !important;
  margin-top: 4px !important;
}

@media (max-width: 900px) {
  .nav-menu {
    top: calc(100% + 1px) !important;
    left: 0 !important;
    right: 0 !important;
    width: auto !important;
    border-left: 0 !important;
    border-right: 0 !important;
    border-radius: 0 0 var(--radius-lg) var(--radius-lg) !important;
  }
}
"""
write(css_rel, css)


# ---------------------------------------------------------------------------
# Embedded AI-assisted WMA: English metadata and factual provenance wording.
# ---------------------------------------------------------------------------
rel = "wma/genai-wma-index.html"
s = read(rel)
s = s.replace('<html lang="de">', '<html lang="en">', 1)
s = s.replace('<title>IUENNA GenAI WMA</title>', '<title>IUENNA AI-assisted Web Map</title>', 1)
s = s.replace(
    'content="Interactive analysis and presentation of the Jauntal Valley, created using GenAI technologies."',
    'content="Interactive IUENNA web map for filtering, selecting and exporting project geospatial metadata; generative AI assisted software development but did not create the archaeological source data."',
)
s = s.replace('<meta name="DC.language" content="de">', '<meta name="DC.language" content="en">')
s = s.replace(
    '<meta name="DC.identifier" content="https://iuenna.github.io/">',
    '<meta name="DC.identifier" content="https://iuenna.github.io/wma/genai-wma-index.html">',
)
s = s.replace(
    '<meta name="DC.rights" content="CC BY 4.0">',
    '<meta name="DC.rights" content="CC BY 4.0 where indicated; archived resources retain record-specific rights and access conditions">',
)
s = s.replace("Go!Digital 3.0 Projekt IUENNA", "Go!Digital 3.0 Project IUENNA")
write(rel, s)


# ---------------------------------------------------------------------------
# Public privacy statement: document actual local storage and Remote MCP.
# ---------------------------------------------------------------------------
rel = "impressum-datenschutz.html"
s = read(rel)
pattern = re.compile(
    r"\s*<h4>Interaktiver Sammlungs-Assistent \(Client-Side In-Browser KI\)</h4>\s*<p>.*?</p>",
    re.S,
)
replacement = """
            <h4>Interaktiver Sammlungs-Assistent (clientseitige Recherche)</h4>
            <p>Der interaktive Sammlungs-Assistent (»Ask IUENNA«) durchsucht ARCHE-abgeleitete IUENNA-Metadaten clientseitig im Browser; der Assistent verwendet dabei kein Sprachmodell und erzeugt keine eigenständigen archäologischen Interpretationen. Suchanfragen werden nicht an einen externen LLM-Anbieter gesendet. Damit der Assistent beim Navigieren innerhalb der Website seinen Sitzungszustand beibehalten kann, werden der Öffnungszustand und der Chatverlauf im <code>sessionStorage</code> des aktuellen Browser-Tabs gespeichert (<code>iuenna_chat_open</code> und <code>iuenna_chat_history</code>). Diese lokale Sitzungsinformation wird durch den IUENNA-Code nicht serverseitig als Chat-Historie gespeichert und nicht für Modelltraining verwendet. Sie endet grundsätzlich mit der Browser-Seitensitzung; Funktionen zur Sitzungswiederherstellung des jeweiligen Browsers können eine Sitzung technisch wiederherstellen.</p>

            <h4>Lokale Speicherung gespeicherter WMA-Filter</h4>
            <p>In der AI-assisted Web-Mapping-Anwendung können Nutzer*innen eine Filterauswahl ausdrücklich über die Funktion »Save Query« speichern. Dabei werden ausgewählte Themen, Orte und gegebenenfalls der eingegebene Suchtext ausschließlich im <code>localStorage</code> des Browsers unter dem Schlüssel <code>iuenna_saved_queries</code> abgelegt. Die Speicherung dient nur dazu, die ausdrücklich gespeicherte Auswahl auf demselben Gerät wieder aufzurufen; sie bleibt bestehen, bis die Auswahl in der Anwendung gelöscht oder der lokale Browser-Speicher geleert wird. Die Funktion dient nicht dem Tracking. Freitextfelder sollten nicht für personenbezogene oder vertrauliche Angaben verwendet werden.</p>

            <h4>IUENNA Remote MCP</h4>
            <p>IUENNA stellt zusätzlich einen öffentlichen, lesenden Remote-MCP-Endpunkt über Cloudflare Workers bereit (<code>https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp</code>). Wenn ein externer MCP-Client diesen Dienst aufruft, wird eine Netzwerkverbindung zu Cloudflare hergestellt; hierbei können insbesondere IP-Adresse und technische Verbindungsdaten beim Hostinganbieter verarbeitet werden. Der IUENNA-MCP-Code richtet keine Benutzerkonten ein und führt keine projektseitige Chat-Historie. Weitere Informationen zur Verarbeitung durch Cloudflare finden Sie in der Datenschutzerklärung von Cloudflare.</p>"""
s, count = pattern.subn(replacement, s, count=1)
if count != 1 and "iuenna_chat_history" not in s:
    raise RuntimeError("Could not replace the obsolete collection-assistant privacy section")

s = s.replace(
    '<h3>6. Cookies</h3>\n            <p>Diese Website verwendet keine Cookies zur Erhebung personenbezogener Daten.</p>',
    '<h3>6. Cookies und lokaler Browser-Speicher</h3>\n            <p>IUENNA setzt nach aktuellem Stand keine eigenen Analyse-, Marketing- oder Tracking-Cookies. Für ausdrücklich bereitgestellte Funktionen werden jedoch die oben beschriebenen lokalen Browser-Speicher <code>sessionStorage</code> und <code>localStorage</code> verwendet. Diese funktionalen Speicherungen dienen ausschließlich der Sitzungsfortsetzung beziehungsweise dem vom Nutzer ausdrücklich gewünschten Speichern einer WMA-Auswahl.</p>',
)

s = re.sub(
    r'<h2>KI-Erklärung \(GenAI, Vibe Coding &amp; Antigravity\)</h2>.*?</div>\s*</main>',
    '''<h2>KI-Erklärung</h2>
            <p>Bei der Entwicklung und redaktionellen Überarbeitung dieser Website wurden generative KI- und Large-Language-Model-Werkzeuge als Programmier-, Strukturierungs- und Formulierungshilfen eingesetzt. Dazu gehörten allgemeine Coding-Assistenten sowie der projektspezifische IUENNA Refiner. Kommerzielle Modellbezeichnungen und Versionsnummern werden hier bewusst nicht als dauerhafte wissenschaftliche Provenienz angegeben, da sich diese Systeme und ihre Konfigurationen laufend ändern.</p>
            <p>KI-Werkzeuge sind keine Quelle für die archäologischen Forschungsdaten. Maßgeblich bleiben die publizierten Projektquellen, die im Repository versionierten Transformations- und Auswertungsskripte sowie die in ARCHE archivierten Datensätze und Metadaten. KI-gestützte Code- und Textvorschläge werden vor der Veröffentlichung menschlich geprüft; automatisierte Vorschläge ersetzen keine fachwissenschaftliche Quellenkritik oder Validierung.</p>
        </div>
    </main>''',
    s,
    count=1,
    flags=re.S,
)

footer_pattern = re.compile(
    r'Developed with <a href="https://antigravity\.google".*?Website Version 2\.1\.7',
    re.S,
)
s = footer_pattern.sub("Human-reviewed AI-assisted development workflow | Go!Digital 3.0 Project IUENNA", s)
s = s.replace("styles.css?v=2.1.7", "styles.css?v=2.5.0")
s = s.replace("scripts/nav.js?v=2.4.0", "scripts/nav.js?v=2.5.0")
write(rel, s)


# ---------------------------------------------------------------------------
# Markdown privacy source: same substantive statements as the HTML page.
# ---------------------------------------------------------------------------
rel = "impressum-datenschutz.md"
s = read(rel)
s = re.sub(
    r'#### \*\*3\. Interaktiver Sammlungs-Assistent \(Client-Side In-Browser KI\)\*\*.*?(?=\n### \*\*5\.)',
    '''#### **3. Interaktiver Sammlungs-Assistent und lokaler Browser-Speicher**

Der interaktive Sammlungs-Assistent (»Ask IUENNA«) durchsucht und synthetisiert veröffentlichte IUENNA-Metadaten clientseitig im Browser; Chatfragen werden nicht an einen externen LLM-Anbieter gesendet. Zur Sitzungsfortsetzung speichert die Oberfläche den Öffnungszustand und den Chatverlauf im `sessionStorage` des aktuellen Browser-Tabs (`iuenna_chat_open`, `iuenna_chat_history`). Diese Daten werden durch den IUENNA-Code nicht als serverseitige Chat-Historie gespeichert und nicht für Modelltraining verwendet. Die Speicherung endet grundsätzlich mit der Browser-Seitensitzung; Browser-Funktionen zur Sitzungswiederherstellung können eine Sitzung technisch wiederherstellen.

In der AI-assisted Web-Mapping-Anwendung können Nutzer*innen Filterauswahlen ausdrücklich über »Save Query« im `localStorage` unter `iuenna_saved_queries` speichern. Gespeichert werden ausgewählte Themen, Orte und gegebenenfalls der Freitext-Suchbegriff. Diese Informationen bleiben lokal im Browser, bis sie in der Anwendung gelöscht oder der Browser-Speicher geleert wird. Die Funktion dient nicht dem Tracking; Freitextfelder sollten nicht für personenbezogene oder vertrauliche Angaben verwendet werden.

IUENNA bietet außerdem einen öffentlichen, lesenden Remote-MCP-Endpunkt über Cloudflare Workers (`https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp`). Bei einem Aufruf durch einen externen MCP-Client wird eine Netzwerkverbindung zu Cloudflare hergestellt; hierbei können insbesondere IP-Adresse und technische Verbindungsdaten beim Hostinganbieter verarbeitet werden. Der IUENNA-MCP-Code richtet keine Benutzerkonten ein und führt keine projektseitige Chat-Historie.

''',
    s,
    count=1,
    flags=re.S,
)
s = re.sub(
    r'### \*\*6\. Verwendung von Cookies\*\*\n.*?(?=\n### \*\*7\.)',
    '''### **6. Cookies und lokaler Browser-Speicher**
IUENNA setzt nach aktuellem Stand keine eigenen Analyse-, Marketing- oder Tracking-Cookies. Für ausdrücklich bereitgestellte Funktionen werden die oben beschriebenen lokalen Browser-Speicher `sessionStorage` und `localStorage` verwendet. Sie dienen ausschließlich der Sitzungsfortsetzung beziehungsweise dem vom Nutzer ausdrücklich gewünschten Speichern einer WMA-Auswahl.

''',
    s,
    count=1,
    flags=re.S,
)
s = re.sub(
    r'## \*\*KI-Erklärung\*\*.*$',
    '''## **KI-Erklärung**

Bei der Entwicklung und redaktionellen Überarbeitung dieser Website wurden generative KI- und Large-Language-Model-Werkzeuge als Programmier-, Strukturierungs- und Formulierungshilfen eingesetzt. Dazu gehörten allgemeine Coding-Assistenten sowie der projektspezifische IUENNA Refiner. Kommerzielle Modellbezeichnungen und Versionsnummern werden bewusst nicht als dauerhafte wissenschaftliche Provenienz geführt, da sich diese Systeme und ihre Konfigurationen laufend ändern.

KI-Werkzeuge sind keine Quelle für die archäologischen Forschungsdaten. Maßgeblich bleiben die publizierten Projektquellen, die im Repository versionierten Transformations- und Auswertungsskripte sowie die in ARCHE archivierten Datensätze und Metadaten. KI-gestützte Code- und Textvorschläge werden vor der Veröffentlichung menschlich geprüft; automatisierte Vorschläge ersetzen keine fachwissenschaftliche Quellenkritik oder Validierung.

Bei Fragen zur Website wenden Sie sich an [dominik.hagmann@univie.ac.at](mailto:dominik.hagmann@univie.ac.at).
''',
    s,
    count=1,
    flags=re.S,
)
write(rel, s)


# ---------------------------------------------------------------------------
# Remove volatile model-version wording from maintained public source pages.
# ---------------------------------------------------------------------------
for rel in ("index.html", "wma/wma.html", "scripts/generate_graph_html.py"):
    s = read(rel)
    s = re.sub(
        r'Developed with <a href="https://antigravity\.google"[^>]*><strong>Google Antigravity</strong></a> v1\.2\.0 \(powered by LLMs such as <a href="https://deepmind\.google"[^>]*>Gemini 3\.8 Flash</a>, <a href="https://www\.anthropic\.com"[^>]*>Claude Opus 4\.6</a>, and <a href="https://chatgpt\.com"[^>]*>ChatGPT 5\.6</a>\) \| Website Version 2\.1\.7',
        'Human-reviewed AI-assisted development workflow | Go!Digital 3.0 Project IUENNA',
        s,
    )
    s = s.replace("styles.css?v=2.1.7", "styles.css?v=2.5.0")
    s = s.replace("../styles.css?v=2.4.0", "../styles.css?v=2.5.0")
    s = s.replace("scripts/nav.js?v=2.4.0", "scripts/nav.js?v=2.5.0")
    s = s.replace("../scripts/nav.js?v=2.4.0", "../scripts/nav.js?v=2.5.0")
    write(rel, s)

# BYOAI uses the same shared CSS/nav assets.
rel = "byoai.html"
s = read(rel).replace("styles.css?v=2.1.7", "styles.css?v=2.5.0").replace("scripts/nav.js?v=2.4.0", "scripts/nav.js?v=2.5.0")
write(rel, s)


# ---------------------------------------------------------------------------
# Ensure IUENNA browser-tab icons on all maintained public HTML entry pages.
# ---------------------------------------------------------------------------
html_paths = [
    Path("index.html"), Path("byoai.html"), Path("impressum-datenschutz.html"),
    Path("wma/wma.html"), Path("wma/genai-wma-home.html"), Path("wma/genai-wma-index.html"),
    Path("wma/qgis2web-home.html"), Path("wma/qgis2web/qgis2web-index.html"),
    Path("graph/index.html"), Path("graph/graph.html"),
]
for relative in html_paths:
    p = ROOT / relative
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    if "favicon.svg" in s:
        continue
    depth = len(relative.parent.parts)
    prefix = "../" * depth
    icons = f'''\n    <!-- IUENNA favicon / browser-tab icons -->
    <link rel="icon" type="image/svg+xml" href="{prefix}favicon.svg">
    <link rel="alternate icon" type="image/png" sizes="32x32" href="{prefix}media/favicon-32x32.png">
    <link rel="alternate icon" type="image/png" sizes="16x16" href="{prefix}media/favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="{prefix}media/apple-touch-icon.png">
    <link rel="shortcut icon" href="{prefix}favicon.ico">
'''
    s, count = re.subn(r"(</title>)", r"\1" + icons, s, count=1, flags=re.I)
    if count != 1:
        raise RuntimeError(f"Could not insert favicon in {relative}")
    p.write_text(s, encoding="utf-8")


# ---------------------------------------------------------------------------
# Validation: no known stale/hallucinatory WMA wording remains.
# ---------------------------------------------------------------------------
public_wma = [
    "wma/wma.html", "wma/genai-wma-home.html", "wma/qgis2web-home.html", "wma/genai-wma-index.html"
]
for rel in public_wma:
    s = read(rel)
    if "favicon.svg" not in s:
        raise RuntimeError(f"Missing IUENNA browser-tab icon in {rel}")
    for stale in (
        "Gemini 3.8 Flash", "ChatGPT 5.5 Instant", "autonomous co-pilot",
        "Karte vergrößern", "Vollbild beenden", "Fokussierter Fundort",
        "Antiquities preservation zone", "core archaeological zone", "wether to render",
    ):
        if stale in s:
            raise RuntimeError(f"{rel}: stale or mixed-language wording remains: {stale}")

legal = read("impressum-datenschutz.html")
for required in ("sessionStorage", "localStorage", "iuenna_chat_history", "iuenna_saved_queries", "Remote MCP"):
    if required not in legal:
        raise RuntimeError(f"Privacy page missing current disclosure: {required}")
for stale in ("SmolLM2", "ChatGPT 5.5 Instant", "Gemini 3.8 Flash"):
    if stale in legal:
        raise RuntimeError(f"Privacy page still contains stale AI claim: {stale}")

print("IUENNA public UI/privacy refresh validated.")
