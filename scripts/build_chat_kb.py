#!/usr/bin/env python3
"""
build_chat_kb.py
----------------
Aggregates authoritative project metadata, ARCHE statistics, subcollections,
site clusters, document types, and project context into a compact knowledge
base (data/iuenna_kb.json) for the client-side 'Chat with IUENNA' assistant.

Usage:
  python3 scripts/build_chat_kb.py
"""

import os
import sys
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WMA_DIR = os.path.join(BASE_DIR, "wma")

STATS_FILE = os.path.join(DATA_DIR, "arche_stats.json")
GRAPH_FILE = os.path.join(DATA_DIR, "arche_graph.json")
GEOJSON_FILE = os.path.join(WMA_DIR, "R00_WGS84.geojson")
FOUNDATIONS_FILE = os.path.join(DATA_DIR, "iuenna_grundlagen.md")
OUTPUT_FILE = os.path.join(DATA_DIR, "iuenna_kb.json")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_foundations(path):
    if not os.path.exists(path):
        print(f"[!] Warning: Foundations file not found at {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = []
    raw_sections = re.split(r"\n(?=##\s+)", content)
    for raw in raw_sections:
        raw = raw.strip()
        if not raw.startswith("## "):
            continue
        lines = raw.split("\n")
        title = lines[0].replace("## ", "").strip()
        body = "\n".join(lines[1:]).strip()

        sec_id = "found_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        keywords = []
        node_id = None
        category = "Historischer & Archäologischer Kontext"

        if "Mikroregion" in title:
            sec_id = "found_mikroregion"
            keywords = ["mikroregion", "jauntal", "podjuna", "karawanken", "luschasattel", "virunum", "celeia", "römerstraße", "kulturlandschaft", "siedlungslandschaft"]
            node_id = "col_1792417"
            category = "Archäologische Landschaft"
        elif "Iuenna und Globasnitz" in title:
            sec_id = "found_iuenna_globasnitz"
            keywords = ["iuenna", "globasnitz", "kleindorf", "mansio", "straßenstation", "iouenat", "tabula peutingeriana", "friedhof", "gräberfeld", "bestattungen", "merowinger", "ostgoten", "kontaktregion", "geophysik", "kaiserzeit"]
            node_id = "col_1792169"
            category = "Siedlungszentrum & Straßenstation"
        elif "Hemmaberg" in title:
            sec_id = "found_hemmaberg"
            keywords = ["hemmaberg", "pilgerzentrum", "pilger", "höhensiedlung", "kirchen", "doppelkirche", "baptisterium", "reliquien", "mosaik", "mosaikböden", "rosaliengrotte", "hemma", "dorothea", "jouenat", "arianisch", "ostgoten", "spätantike", "wallfahrt"]
            node_id = "col_1792212"
            category = "Spätantikes Pilgerzentrum"
        elif "Stefan" in title:
            sec_id = "found_st_stefan"
            keywords = ["st. stefan", "sankt stefan", "šteben", "steben", "villa", "villenanlage", "landgut", "super-villa", "hypokaust", "hypokaustheizung", "apsiden", "georadar", "geomagnetik", "römerzeit"]
            node_id = "col_1792411"
            category = "Römische Villenanlage"
        elif "IUENNA‑Projekt" in title or "IUENNA-Projekt" in title:
            sec_id = "found_iuenna_projekt"
            keywords = ["iuenna", "projekt", "iuenna-projekt", "godigital", "öaw", "öai", "kärnten.museum", "acdh-ch", "bda", "ardig", "arche", "fair", "care", "open science", "geopackage", "wma", "web-mapping", "datenrettung", "repositorium"]
            node_id = "top_iuenna"
            category = "Digital Humanities Projekt"
        elif "Literatur" in title:
            sec_id = "found_literatur"
            keywords = ["literatur", "quellen", "publikationen", "glaser", "hagmann", "reiner", "pollak", "schwaiger", "peer community journal"]
            node_id = None
            category = "Fachliteratur & Referenzen"

        citations = re.findall(r"\(([A-Z][a-zA-Z\s,–-]+,\s*\d{4}[^\)]*)\)", body)
        if sec_id == "found_literatur":
            citations = ["Glaser (2002)", "Hagmann & Reiner (2023)", "Pollak (2023)", "Schwaiger & Reiner (2022)", "Hagmann & Reiner (2025)"]

        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        summary = paragraphs[0] if paragraphs else ""

        sections.append({
            "id": sec_id,
            "title": title,
            "category": category,
            "summary": summary,
            "content": body,
            "citations": list(dict.fromkeys(citations)),
            "keywords": keywords,
            "graph_node_id": node_id
        })

    print(f"[+] Loaded {len(sections)} authoritative foundation chapters from {os.path.basename(path)}")
    return sections

def build_knowledge_base():
    print("[*] Compiling IUENNA Chat Knowledge Base...")

    stats_data = load_json(STATS_FILE) or {}
    graph_data = load_json(GRAPH_FILE) or {}
    foundations = load_foundations(FOUNDATIONS_FILE)

    total_items = stats_data.get("collection", {}).get("total_items", 20788)
    total_size = stats_data.get("collection", {}).get("total_size_formatted", "356.68 GB")
    top_pid = stats_data.get("collection", {}).get("pid", "https://hdl.handle.net/21.11115/0000-0016-7B39-F")
    doi_uri = stats_data.get("collection", {}).get("arche_id", "https://id.acdh.oeaw.ac.at/iuenna")

    # 1. Project Core Information
    project_info = {
        "title": "IUENNA - openIng the soUthErn jauNtal as a micro-regioN for future Archaeology",
        "short_title": "IUENNA",
        "subtitle": "Archäologische Mikro-Region Jauntal (Kärnten / Österreich)",
        "funding": "Österreichische Akademie der Wissenschaften (ÖAW), Förderprogramm Go!Digital 3.0",
        "duration": "Go!Digital 3.0 Projekt",
        "doi_url": doi_uri,
        "pid": top_pid,
        "total_items": total_items,
        "total_size": total_size,
        "total_sites": "Über 200 erfasste archäologische Fundstellen",
        "time_span": "Über 130 Jahre moderne Forschungsgeschichte; Besiedlungsspuren von der Urgeschichte (Hallstatt) über Römerzeit und Spätantike bis zum Frühmittelalter",
        "leadership": [
            {
                "name": "Dr. Dominik Hagmann",
                "role": "Projektleitung / Koordination",
                "institution": "Landesmuseum für Kärnten (kärnten.museum)",
                "orcid": "https://orcid.org/0000-0002-4481-6234"
            },
            {
                "name": "Dipl.-Ing. Franziska Waldhart",
                "role": "Projektleitung / Koordination",
                "institution": "Österreichisches Archäologisches Institut (ÖAI), ÖAW",
                "url": "https://www.oeaw.ac.at/oeai"
            }
        ],
        "partners": [
            {"name": "kärnten.museum", "full": "Landesmuseum für Kärnten", "url": "https://landesmuseum.ktn.gv.at/"},
            {"name": "ÖAI", "full": "Österreichisches Archäologisches Institut (ÖAW)", "url": "https://www.oeaw.ac.at/oeai"},
            {"name": "ACDH-CH", "full": "Austrian Center for Digital Humanities and Cultural Heritage (ÖAW)", "url": "https://www.oeaw.ac.at/acdh"},
            {"name": "BDA", "full": "Bundesdenkmalamt", "url": "https://bda.gv.at/"},
            {"name": "ARDIG", "full": "ARDIG – Archäologischer Dienst GesmbH", "url": "https://www.ardig.at/"}
        ],
        "curation_workflow": [
            "1. Bestandsaufnahme & Sichtung analoger und digitaler Altbestände",
            "2. Normalisierung von Ordner- und Verzeichnisstrukturen",
            "3. Standardisierung und Konsolidierung von Dateinamen",
            "4. Metadatenerstellung nach FAIR- und CARE-Prinzipien",
            "5. Langzeitarchivierung im Repositorium ARCHE (ACDH-CH)",
            "6. Bereitstellung in Web-Mapping-Layern & Open Science Katalogen"
        ],
        "ai_methods": {
            "framework": "Google Antigravity, Claude Opus & Gemini Flash",
            "vibe_coding": "Nutzung von Vibe Coding und agentischer KI für konsolidierte Webentwicklung und Datenstrukturen",
            "iuenna_refiner": "Custom GPT 'IUENNA Refiner' für Metadatenbereinigung und GeoJSON-Validierung",
            "transparency": "Vollständige wissenschaftliche Offenlegung und menschliche Validierung aller KI-generierten Strukturen"
        },
        "links": {
            "website": "https://iuenna.github.io/",
            "arche": "https://id.acdh.oeaw.ac.at/iuenna",
            "blog": "https://iuenna.hypotheses.org/",
            "wma": "https://iuenna.github.io/wma/wma.html",
            "gpkg_download": "https://github.com/IUENNA/IUENNA.github.io/blob/main/wma/IUENNA-WMA.gpkg"
        }
    }

    # 2. Subcollections from arche_stats.json
    subcollections_raw = stats_data.get("subcollections", [])
    subcollections = []
    for col in subcollections_raw:
        code = col.get("code")
        title = col.get("title")
        items = col.get("items", 0)
        size = col.get("formatted_size", "")
        pid = col.get("pid", "")
        arche_uri = col.get("arche_uri", "")

        desc = ""
        keywords = []
        if code == "RET":
            desc = "Sammlung von Retrodigitalisaten historischer Grabungsdokumentationen, Pläne, handgezeichneter Profile, Fundinventare und Fotos aus den Archiven des Landesmuseums für Kärnten und des ÖAI."
            keywords = ["retro", "retrodigitalisat", "altbestand", "archiv", "tagebuch", "grabungsbericht", "historisch", "zeichnung", "altakten"]
        elif code == "JAU":
            desc = "Dokumentation und Funddaten zum bedeutenden frühmittelalterlichen und kaiserzeitlichen Gräberfeld sowie zu Siedlungsspuren in Jaunstein (Gemeinde Globasnitz)."
            keywords = ["jaunstein", "jau", "gräberfeld", "gräber", "skelett", "bestattung", "frühmittelalter", "beigaben", "karantanien"]
        elif code == "HB":
            desc = "Umfangreiche Forschungsdaten zum spätantiken Pilgerheiligtum Hemmaberg mit seinen fünf frühchristlichen Kirchen, Mosaiken, Befestigungen und Grabanlagen."
            keywords = ["hemmaberg", "hb", "kirche", "kirchen", "doppelkirche", "frühchristlich", "pilger", "mosaik", "spätantike", "joven", "wallfahrt", "rosaliengrotte"]
        elif code == "GLO":
            desc = "Archäologische Befunde und Funde aus dem Ortsgebiet Globasnitz (römisches Straßenstations- und Siedlungszentrum Iuenna an der Römerstraße Virunum–Celeia)."
            keywords = ["globasnitz", "glo", "iuenna", "römer", "römerzeit", "mansio", "straßenstation", "münzen", "siedlung", "ostgoten"]
        elif code == "TAL":
            desc = "Regionale Übersichtsdaten, GIS-Projekte, Geländemodelle und geophysikalische Prospektionsdaten der gesamten Mikro-Region Jauntal."
            keywords = ["jauntal", "tal", "geodaten", "gis", "übersicht", "landschaft", "prospektion", "geophysik", "podjuna"]
        elif code == "STE":
            desc = "Dokumentation archäologischer Funde und Befunde aus dem Bereich Sankt Stefan im Jauntal."
            keywords = ["sankt stefan", "ste", "st. stefan", "stefan", "fundort"]

        subcollections.append({
            "id": f"col_{code.lower()}",
            "code": code,
            "title": title,
            "items": items,
            "size": size,
            "pid": pid,
            "arche_url": arche_uri,
            "description": desc,
            "keywords": keywords
        })

    # 3. Key Archaeological Sites & Spatial Coverage
    sites = [
        {
            "id": "site_hemmaberg",
            "name": "Hemmaberg",
            "geonames": "https://www.geonames.org/12719971/hemmaberg.html",
            "items_count": 11092,
            "period": "Mittelbronzezeit, Spätlatène, Römerzeit, Spätantike (4.–6. Jh. n. Chr.), Frühmittelalter",
            "highlights": "843 m hoher Bergrücken; bedeutendstes spätantikes Pilgerzentrum des Ostalpenraums. Fünf frühchristliche Kirchen, darunter monumentale Doppelkirchenanlagen des frühen 6. Jhs. (Eucharistie-, Memorialkirchen, Baptisterien, Reliquienaltäre für katholische und arianisch-gotische Gemeinden), Rosaliengrotte, Pilgerhospiz, Mosaike und Höhensiedlung (Glaser 2002; Hagmann & Reiner 2023).",
            "subcollection": "HB / RET",
            "keywords": ["hemmaberg", "pilgerzentrum", "pilgerheiligtum", "doppelkirche", "rosaliengrotte", "mosaik", "mosaikböden", "reliquien", "baptisterium", "bischof", "spätantike", "kirchenanlage", "heiligengrab", "jouenat", "arianisch"]
        },
        {
            "id": "site_jaunstein",
            "name": "Jaunstein",
            "items_count": 4899,
            "period": "Römerzeit, Spätantike bis Frühmittelalter (Köttlach-Kultur / slawisch-karantanisch)",
            "highlights": "Großes frühmittelalterliches Reihengräberfeld mit hunderten Gräbern; reiche Schmuckbeigaben (Korbgehänge, Fingerringe, Perlenketten) und Waffen der karantanischen Bevölkerung.",
            "subcollection": "JAU / RET",
            "keywords": ["jaunstein", "gräberfeld", "frühmittelalter", "reihengräber", "slawisch", "karantanien", "schmuck", "ohrringe", "perlen", "korbgehänge"]
        },
        {
            "id": "site_globasnitz",
            "name": "Globasnitz (Iuenna)",
            "items_count": 2775,
            "period": "Römische Kaiserzeit, Spätantike, Merowingerzeit (4.–6. Jh. n. Chr.)",
            "highlights": "Römische Straßenstation (Mansio Iuenna) an der Reichsstraße Virunum–Celeia, benannt nach keltischer Gottheit Iouenat (Tabula Peutingeriana). Größtes spätantik-merowingerzeitliches Gräberfeld Österreichs mit rund 425 Gräbern / 440 Bestattungen und zwei aufeinanderfolgenden Kirchen (ältere aus späten 4. Jh.); Kontaktregion romanischer, ostgotischer und merowingischer Einflüsse (Pollak 2023; Schwaiger & Reiner 2022).",
            "subcollection": "GLO / RET",
            "keywords": ["globasnitz", "iuenna", "mansio", "straßenstation", "römerstraße", "virunum", "celeia", "pilgermuseum", "kaiserzeit", "inschrift", "gräberfeld", "friedhof", "merowinger", "ostgoten", "iouenat", "tabula peutingeriana"]
        },
        {
            "id": "site_sankt_stefan",
            "name": "Sankt Stefan im Jauntal (Šteben)",
            "items_count": 15,
            "period": "Römische Kaiserzeit bis Spätantike",
            "highlights": "Ausgedehnte römische Villenanlage / Landgut ('Super-Villa') im Umland von Globasnitz. Geophysikalisch prospektiertes Areal von ca. 7.700 m² mit mehreren Gebäuden, repräsentativem Saal mit zwei gegenüberliegenden Apsiden und 1930 dokumentierter Hypokaustheizung (Schwaiger & Reiner 2022; Hagmann & Reiner 2023).",
            "subcollection": "STE",
            "keywords": ["sankt stefan", "st. stefan", "šteben", "steben", "villa", "super-villa", "landgut", "hypokaust", "apsiden", "geophysik", "georadar"]
        }
    ]

    # 4. Document Types & Formats
    doc_types = [
        {
            "id": "doc_plans",
            "name": "Aufmaßzeichnungen & Grabungspläne",
            "count": "ca. 4.400 Dokumente",
            "formats": "TIF, PDF, DWG, DXF",
            "description": "Präzise händische und digitale Grundrisse, Schnittzeichnungen, Steinpläne und Profilaufnahmen von Grabungen auf dem Hemmaberg und in Jaunstein.",
            "keywords": ["plan", "pläne", "aufmaß", "zeichnung", "profil", "schnitt", "grundriss", "steinplan", "bauaufnahme"]
        },
        {
            "id": "doc_photos",
            "name": "Dokumentarfotografien",
            "count": "Über 11.600 Aufnahmen",
            "formats": "TIF, JPG",
            "description": "Historische Schwarzweiß- und Farbfotografien, Fundaufnahmen, Grabungsdokumentationen und Übersichtsaufnahmen aus über 100 Jahren Forschung.",
            "keywords": ["foto", "fotos", "fotografie", "aufnahme", "bild", "diapositiv", "schwarzweiß", "negativ"]
        },
        {
            "id": "doc_index_cards",
            "name": "Karteikarten & Fundinventare",
            "count": "ca. 3.600 Karteikarten",
            "formats": "TIF, PDF",
            "description": "Originale Fundzettel, Grabungsinventare und Fundkarteikarten mit detaillierten Beschreibungen, Maßen und Fundortkoordinaten.",
            "keywords": ["karteikarte", "kartei", "inventar", "fundzettel", "notizen", "tagebuch", "fundkatalog"]
        },
        {
            "id": "doc_geodata",
            "name": "Vektorgeodaten & GIS",
            "count": "Über 20.500 Vektorpunkte & Polygone",
            "formats": "GeoPackage (.gpkg), GeoJSON (.geojson), Shapefile",
            "description": "Exakt verortete Fundpunkte, Grabungsgrenzen, Befundpolygone und Höhendaten im WGS84-System, frei herunterladbar und direkt in QGIS ladbar.",
            "keywords": ["geodaten", "gis", "gpkg", "geojson", "karte", "qgis", "vektordaten", "koordinaten", "wgs84"]
        }
    ]

    # 5. Curated FAQs for Quick Retrieval
    faq_entries = [
        {
            "id": "faq_what_is_iuenna",
            "question": "Was ist das Projekt IUENNA?",
            "answer": "IUENNA ('openIng the soUthErn jauNtal as a micro-regioN for future Archaeology') ist ein durch das Go!Digital 3.0 Programm der ÖAW gefördertes Digital-Humanities-Projekt von kärnten.museum, ÖAI, ACDH-CH, BDA und ARDIG (Hagmann & Reiner 2023). Es erschließt über 20.000 archäologische Objekte, Grabungsberichte, Pläne und Fotos aus über 100 Jahren Forschung im südlichen Jauntal und archiviert sie dauerhaft im Repositorium ARCHE.",
            "links": [{"text": "ARCHE Repositorium", "url": doi_uri}],
            "keywords": ["was ist iuenna", "projekt", "godigital", "ziel", "über das projekt", "forschung", "jauntal"]
        },
        {
            "id": "faq_name_iuenna",
            "question": "Woher stammt der Name Iuenna und was bedeutet er?",
            "answer": "Der Name 'Iuenna' bezeichnet die antike römische Straßenstation und Siedlung im Bereich von Globasnitz und Kleindorf an der Reichsstraße Virunum–Celeia (belegt auf der Tabula Peutingeriana). Er geht auf die einheimische keltische Gottheit 'Iouenat' zurück, die durch einen Votivaltar vom Hemmaberg belegt ist. Von dieser Wortwurzel leiten sich auch 'Jaunberg' und 'Jauntal' (slowenisch Podjuna) ab (Glaser 2002).",
            "links": [
                {"text": "Subcollection Globasnitz (GLO)", "url": "https://hdl.handle.net/21.11115/0000-0016-7B3A-E"},
                {"text": "Web-Mapping Globasnitz", "url": "https://iuenna.github.io/wma/wma.html"}
            ],
            "keywords": ["name", "woher kommt iuenna", "iouenat", "bedeutung", "gottheit", "tabula peutingeriana", "jaunberg", "jauntal", "etymologie", "kleindorf"]
        },
        {
            "id": "faq_graeberfeld_globasnitz",
            "question": "Was zeichnet das spätantike Gräberfeld von Globasnitz aus?",
            "answer": "Das östlich von Globasnitz gelegene Gräberfeld ist mit rund 425 Gräbern und etwa 440 Bestattungen der größte spätantik-merowingerzeitliche Bestattungsplatz Österreichs und der bisher einzige umfassend erforschte Friedhof einer norischen Straßenstation (Pollak 2023). Innerhalb der Nekropole lagen zudem zwei aufeinanderfolgende Kirchen (die ältere bereits aus dem späten 4. Jh.). Beigaben wie Gürtelbeschläge, Fibeln und Perlen bezeugen weitreichende Kontakte im Alpenraum.",
            "links": [
                {"text": "Subcollection Globasnitz (GLO)", "url": "https://hdl.handle.net/21.11115/0000-0016-7B3A-E"},
                {"text": "Web-Mapping Globasnitz", "url": "https://iuenna.github.io/wma/wma.html"}
            ],
            "keywords": ["gräberfeld globasnitz", "friedhof", "bestattungen", "merowinger", "ostgoten", "425 gräber", "440 bestattungen", "marianne pollak", "fibeln", "gürtel"]
        },
        {
            "id": "faq_doppelkirchen_hemmaberg",
            "question": "Welche Bedeutung haben die Doppelkirchen auf dem Hemmaberg?",
            "answer": "Auf dem 843 m hohen Hemmaberg entstanden im frühen 6. Jahrhundert zwei monumentale Doppelkirchenanlagen mit Eucharistie- und Memorialkirchen, Baptisterien, Reliquienkammern und Pilgerhospizen (Glaser 2002). Die doppelte Ausführung gilt in der Forschung als Zeugnis zweier nebeneinander existierender christlicher Gemeinden: einer katholisch-romanischen und einer arianisch-gotischen Gemeinde zur Zeit der ostgotischen Herrschaft.",
            "links": [
                {"text": "Subcollection Hemmaberg (HB)", "url": "https://hdl.handle.net/21.11115/0000-0016-7B3B-D"},
                {"text": "Web-Mapping Hemmaberg", "url": "https://iuenna.github.io/wma/wma.html"}
            ],
            "keywords": ["doppelkirche", "doppelkirchen", "kirchen", "arianisch", "katholisch", "ostgoten", "pilgerzentrum", "mosaike", "reliquien", "franz glaser"]
        },
        {
            "id": "faq_villa_st_stefan",
            "question": "Was ist die römische Villenanlage in St. Stefan (Šteben)?",
            "answer": "In St. Stefan/Šteben bei Globasnitz liegt ein großes römisches Landgut ('Super-Villa'). Geophysikalische Messungen mit Georadar und Geomagnetik belegen ein über 7.700 m² großes bebautes Areal mit Begrenzungsmauern, einem repräsentativen Raum mit zwei gegenüberliegenden Apsiden sowie einer bereits 1930 freigelegten Hypokaust-Fußbodenheizung (Schwaiger & Reiner 2022).",
            "links": [
                {"text": "Subcollection St. Stefan (STE)", "url": "https://hdl.handle.net/21.11115/0000-0016-7B3C-C"},
                {"text": "Web-Mapping St. Stefan", "url": "https://iuenna.github.io/wma/wma.html"}
            ],
            "keywords": ["st. stefan", "stefan", "šteben", "steben", "villa", "super-villa", "landgut", "hypokaust", "apsiden", "schwaiger", "reiner"]
        },
        {
            "id": "faq_hemmaberg",
            "question": "Wo finde ich die Grabungsdaten und Pläne zum Hemmaberg?",
            "answer": "Die Daten zum Hemmaberg sind in der Subcollection 'HB' (Hemmaberg-Collection, PID: https://hdl.handle.net/21.11115/0000-0016-7B3B-D) sowie im Retrodigitalisate-Bestand 'RET' archiviert. Sie umfassen über 11.000 Einzelobjekte – darunter historische Steinpläne der frühchristlichen Kirchen, Profilzeichnungen und Fotodokumentationen. Nutzen Sie auch unsere interaktive Web-Map!",
            "links": [
                {"text": "Hemmaberg in ARCHE", "url": "https://hdl.handle.net/21.11115/0000-0016-7B3B-D"},
                {"text": "Web-Mapping öffnen", "url": "https://iuenna.github.io/wma/wma.html"}
            ],
            "keywords": ["hemmaberg pläne", "hemmaberg daten", "kirchen", "grabungspläne hemmaberg", "rosaliengrotte", "doppelkirche"]
        },
        {
            "id": "faq_leadership",
            "question": "Wer leitet das IUENNA-Projekt?",
            "answer": "IUENNA wurde gemeinsam von Dr. Dominik Hagmann (Landesmuseum für Kärnten / kärnten.museum) und Dipl.-Ing. Franziska Waldhart (Österreichisches Archäologisches Institut / ÖAI an der ÖAW) geleitet und koordiniert.",
            "links": [
                {"text": "Dr. Dominik Hagmann (ORCID)", "url": "https://orcid.org/0000-0002-4481-6234"},
                {"text": "ÖAI Website", "url": "https://www.oeaw.ac.at/oeai"}
            ],
            "keywords": ["wer leitet", "leitung", "koordination", "dominik hagmann", "franziska waldhart", "team", "forscher"]
        },
        {
            "id": "faq_licenses",
            "question": "Unter welchen Lizenzen stehen die IUENNA-Daten?",
            "answer": "Die Daten sind nach den FAIR- und CARE-Prinzipien öffentlich zugänglich. Neu erstellte Metadaten, Vektorgeodaten (GeoPackage/GeoJSON) und Web-Inhalte stehen unter der freien Lizenz Creative Commons Namensnennung (CC BY 4.0). Bei historischen Bild- und Archivdokumenten greift teilweise InC (In Copyright / geschützte Bestände), die über ARCHE für wissenschaftliche Zwecke einsehbar sind.",
            "links": [{"text": "CC BY 4.0 Lizenz", "url": "https://creativecommons.org/licenses/by/4.0/"}],
            "keywords": ["lizenz", "lizenzen", "cc by", "urheberrecht", "fair", "open access", "copyright", "inc"]
        },
        {
            "id": "faq_gis_download",
            "question": "Kann ich die Geodaten direkt in QGIS herunterladen?",
            "answer": "Ja! Sie können das vollständige GIS-Paket als GeoPackage ('IUENNA-WMA.gpkg', ca. 7.8 MB) direkt von unserem GitHub-Repositorium herunterladen und ohne Konvertierung in QGIS oder ArcGIS öffnen. Es enthält alle Fundstellen und Attribute.",
            "links": [
                {"text": "GeoPackage (.gpkg) Download", "url": "https://github.com/IUENNA/IUENNA.github.io/blob/main/wma/IUENNA-WMA.gpkg"},
                {"text": "Web-Mapping Portal", "url": "https://iuenna.github.io/wma/wma.html"}
            ],
            "keywords": ["download", "gis download", "qgis", "geopackage", "gpkg", "geojson", "shapefile", "karten"]
        },
        {
            "id": "faq_vibe_coding",
            "question": "Was bedeutet Vibe Coding und GenAI bei IUENNA?",
            "answer": "IUENNA setzt pionierhaft auf moderne agentische KI-Tools (wie Google Antigravity) und das Entwicklungsparadigma des 'Vibe Coding': Forschende fungieren als kreative und fachliche Regisseure, während KI-Assistenten Code-Strukturen, Stylesheets und Geodatenfilter iterativ miterstellen. Alle Resultate werden akademisch geprüft und transparent deklariert.",
            "links": [{"text": "KI-Deklaration auf der Startseite", "url": "#ai-declaration"}],
            "keywords": ["vibe coding", "ki", "genai", "antigravity", "chatgpt", "künstliche intelligenz", "methoden"]
        }
    ]

    # 6. Extract All Knowledge Graph Entities from arche_graph.json
    graph_entities = []
    if graph_data and "elements" in graph_data:
        for node in graph_data["elements"].get("nodes", []):
            d = node.get("data", {})
            nid = d.get("id")
            label = d.get("label", "")
            ntype = d.get("type", "folder")
            desc = d.get("description") or d.get("desc") or ""
            items_c = d.get("items")
            size_f = d.get("formatted_size")
            arche_url = d.get("arche_url") or d.get("pid") or ""
            
            graph_entities.append({
                "id": nid,
                "label": label,
                "type": ntype,
                "type_label": d.get("type_label", ntype),
                "description": desc,
                "items": items_c,
                "size": size_f,
                "arche_url": arche_url,
                "color": d.get("color", "#B88E3E")
            })

    kb_payload = {
        "meta": {
            "title": "IUENNA Interactive Knowledge Base",
            "version": "1.2.0",
            "generated_at": "2026-09-07",
            "description": "Comprehensive client-side knowledge corpus combining ARCHE stats, Knowledge Graph (215 nodes), archaeological foundations, and spatial clusters.",
            "total_items": total_items,
            "total_storage": total_size,
            "license": "CC BY 4.0"
        },
        "project": project_info,
        "foundations": foundations,
        "subcollections": subcollections,
        "sites": sites,
        "doc_types": doc_types,
        "faq": faq_entries,
        "graph_entities": graph_entities
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(kb_payload, f, ensure_ascii=False, indent=2)

    file_size_kb = os.path.getsize(OUTPUT_FILE) / 1024.0
    print(f"[+] Knowledge Base written successfully to {OUTPUT_FILE} ({file_size_kb:.1f} KB)")
    print(f"[+] Elements: {len(subcollections)} subcollections, {len(sites)} sites, {len(doc_types)} doc types, {len(faq_entries)} FAQs.")

if __name__ == "__main__":
    build_knowledge_base()
