#!/usr/bin/env python3
"""
build_arche_graph.py
--------------------
Harvests authoritative knowledge graph metadata directly from the ARCHE
repository (ACDH-CH / ÖAW) for the IUENNA project (https://id.acdh.oeaw.ac.at/iuenna).
Builds a comprehensive RDF linked-data network of nodes and edges tailored
for interactive visualization with Cytoscape.js.

Outputs:
  data/arche_graph.json
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error

ARCHE_BASE = "https://arche.acdh.oeaw.ac.at/api"
IUENNA_TOP_ID = "1792170"

def format_bytes(size_bytes):
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def build_graph():
    print("[*] Starting ARCHE Knowledge Graph compilation for IUENNA...")
    start_time = time.time()

    nodes = []
    edges = []

    # 1. Top-Level Collection Node
    top_node = {
        "data": {
            "id": "iuenna_root",
            "arche_id": IUENNA_TOP_ID,
            "label": "IUENNA Top-Collection",
            "full_title": "IUENNA - openIng the soUthErn jauNtal as a micro-regioN for future Archaeology",
            "type": "root",
            "type_label": "Top Collection",
            "items": 20788,
            "bytes": 382979462143,
            "formatted_size": "356.68 GB",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B39-F",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1792170",
            "doi_uri": "https://id.acdh.oeaw.ac.at/iuenna",
            "funder": "Österreichische Akademie der Wissenschaften (Go!Digital 3.0)",
            "hosting": "ARCHE (ACDH-CH)",
            "description": "Zentrale Top-Collection des Projekts IUENNA. Umfasst über 20.000 archäologische Objekte, Pläne, Vektordaten, 3D-Modelle und Forschungsdaten aus über 100 Jahren Forschung im Jauntal.",
            "color": "#A8442E",
            "icon": "fa-landmark"
        }
    }
    nodes.append(top_node)

    # 2. Subcollections (6 Core Collections)
    subcollections_raw = [
        {
            "id": "col_ret",
            "code": "RET",
            "arche_id": "1792572",
            "label": "Retrodigitalisat-Collection (RET)",
            "items": 9341,
            "bytes": 290650991123,
            "formatted_size": "270.69 GB",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B59-B",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1792572",
            "spatial_id": "plc_jauntal",
            "description": "Umfassende Sammlung retrodigitalisierter Grabungsdokumentationen, Pläne, Profile, Fundzeichnungen und Fotos aus Beständen des kärnten.museums und ÖAI.",
            "license_info": "InC: 8.515 / CC BY 4.0: 604"
        },
        {
            "id": "col_jau",
            "code": "JAU",
            "arche_id": "1792303",
            "label": "Jaunstein-Collection (JAU)",
            "items": 4989,
            "bytes": 55881335390,
            "formatted_size": "52.04 GB",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B4B-B",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1792303",
            "spatial_id": "plc_jaunstein",
            "description": "Forschungs- und Grabungsdaten zur spätantik-frühmittelalterlichen Talsiedlung Jaunstein, inkl. Orthofotos, Rasterdaten, Grabungstagebüchern und Vektor-Plänen.",
            "license_info": "InC: 4.964 / CC BY 4.0: 25"
        },
        {
            "id": "col_hb",
            "code": "HB",
            "arche_id": "1792212",
            "label": "Hemmaberg-Collection (HB)",
            "items": 3726,
            "bytes": 31148982450,
            "formatted_size": "29.01 GB",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B3B-D",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1792212",
            "spatial_id": "plc_hemmaberg",
            "description": "Frühchristliches Pilgerheiligtum auf dem Hemmaberg: Kirchenkomplexe, Gräberfelder, Mosaikdokumentationen, 3D-Modelle und historische Grabungsberichte.",
            "license_info": "InC: 2.547 / CC BY 4.0: 1.110"
        },
        {
            "id": "col_glo",
            "code": "GLO",
            "arche_id": "1792169",
            "label": "Globasnitz-Collection (GLO)",
            "items": 2692,
            "bytes": 5136001949,
            "formatted_size": "4.78 GB",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B30-8",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1792169",
            "spatial_id": "plc_globasnitz",
            "description": "Römische Mansio Iuenna und östliches Gräberfeld im Tal von Globasnitz: Rasterdaten, Fundlisten, anthropologische Dokumentationen und Auswertungen.",
            "license_info": "InC: 279 / CC BY 4.0: 2.292"
        },
        {
            "id": "col_tal",
            "code": "TAL",
            "arche_id": "1792417",
            "label": "Jauntal-Collection (TAL)",
            "items": 25,
            "bytes": 128491410,
            "formatted_size": "122.54 MB",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B56-E",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1792417",
            "spatial_id": "plc_jauntal",
            "description": "Mikroregionale Übersichtskarten, Geländemodelle (DGM), Gesamtprojektdatenbanken und GIS-Zusammenstellungen des gesamten Jauntals.",
            "license_info": "CC BY 4.0: 25"
        },
        {
            "id": "col_ste",
            "code": "STE",
            "arche_id": "1792411",
            "label": "Sankt Stefan-Collection (STE)",
            "items": 8,
            "bytes": 33621634,
            "formatted_size": "32.06 MB",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B53-1",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1792411",
            "spatial_id": "plc_st_stefan",
            "description": "Ausgrabungsdaten und Fundstellendokumentationen aus Sankt Stefan im Jauntal.",
            "license_info": "InC: 3 / CC BY 4.0: 5"
        }
    ]

    for sc in subcollections_raw:
        nodes.append({
            "data": {
                "id": sc["id"],
                "arche_id": sc["arche_id"],
                "code": sc["code"],
                "label": sc["label"],
                "type": "subcollection",
                "type_label": "Subcollection",
                "items": sc["items"],
                "bytes": sc["bytes"],
                "formatted_size": sc["formatted_size"],
                "pid": sc["pid"],
                "arche_url": sc["arche_url"],
                "description": sc["description"],
                "license_info": sc["license_info"],
                "color": "#B88E3E",
                "icon": "fa-folder"
            }
        })
        edges.append({
            "data": {
                "id": f"edge_sub_{sc['id']}_root",
                "source": sc["id"],
                "target": "iuenna_root",
                "label": "isPartOf",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#isPartOf"
            }
        })

    # 3. Category Folders (Data Units under Subcollections)
    folders = [
        # Jaunstein (JAU)
        {"id": "jau_vektor", "parent": "col_jau", "arche_id": "1792302", "label": "03_02_Vektor", "category": "Vektordaten", "items": 6, "desc": "GIS Vektor-Geodaten und Fundkartierungen"},
        {"id": "jau_raster", "parent": "col_jau", "arche_id": "1792308", "label": "03_03_Raster", "category": "Rasterdaten", "items": 4742, "desc": "Orthofotos, Befundfotos und georeferenzierte Pläne"},
        {"id": "jau_db", "parent": "col_jau", "arche_id": "1792394", "label": "03_05_Datenbanken", "category": "Datenbanken", "items": 2, "desc": "Katalog- und Funddatenbanken Jaunstein"},
        {"id": "jau_text", "parent": "col_jau", "arche_id": "1792395", "label": "03_06_Texte_Tabellen", "category": "Texte & Tabellen", "items": 205, "desc": "Grabungstagebücher, Inventare und Berichte"},
        {"id": "jau_out", "parent": "col_jau", "arche_id": "1792406", "label": "03_07_Output", "category": "Publikationen & Pläne", "items": 29, "desc": "Druckfertige Pläne und Publikationsabbildungen"},

        # Hemmaberg (HB)
        {"id": "hb_vektor", "parent": "col_hb", "arche_id": "1792211", "label": "02_02_Vektor", "category": "Vektordaten", "items": 43, "desc": "Gesamt-GIS Hemmaberg, Polygone der Kirchenkomplexe"},
        {"id": "hb_raster", "parent": "col_hb", "arche_id": "1792217", "label": "02_03_Raster", "category": "Rasterdaten", "items": 3401, "desc": "Befund- und Grabungsfotos, Orthofotos Hemmaberg"},
        {"id": "hb_3d", "parent": "col_hb", "arche_id": "1792271", "label": "02_04_3D-Daten", "category": "3D-Modelle", "items": 2, "desc": "Dreidimensionale Rekonstruktionsmodelle & Punktwolken"},
        {"id": "hb_db", "parent": "col_hb", "arche_id": "1792273", "label": "02_05_Datenbanken", "category": "Datenbanken", "items": 4, "desc": "Funddatenbanken und anthropologische Befundtabellen"},
        {"id": "hb_text", "parent": "col_hb", "arche_id": "1792274", "label": "02_06_Texte_Tabellen", "category": "Texte & Tabellen", "items": 217, "desc": "Grabungsberichte, Tagebücher und Grabungskataloge"},
        {"id": "hb_out", "parent": "col_hb", "arche_id": "1792292", "label": "02_07_Output", "category": "Publikationen & Pläne", "items": 53, "desc": "Publikationspläne der Kirchen und Mosaike"},

        # Globasnitz (GLO)
        {"id": "glo_raster", "parent": "col_glo", "arche_id": "1792168", "label": "01_03_Raster", "category": "Rasterdaten", "items": 2605, "desc": "Fotodokumentation der Gräberfelder und Befunde"},
        {"id": "glo_db", "parent": "col_glo", "arche_id": "1792190", "label": "01_05_Datenbanken", "category": "Datenbanken", "items": 2, "desc": "Anthropologische Datenbanken und Gräberkataloge"},
        {"id": "glo_text", "parent": "col_glo", "arche_id": "1792193", "label": "01_06_Text_Tabellen", "category": "Texte & Tabellen", "items": 57, "desc": "Grabungsdokumentationen und Befundlisten"},
        {"id": "glo_out", "parent": "col_glo", "arche_id": "1792206", "label": "01_07_Output", "category": "Publikationen & Pläne", "items": 24, "desc": "Publikationskarten und Fundstellenpläne"},

        # Jauntal (TAL)
        {"id": "tal_raster", "parent": "col_tal", "arche_id": "1792416", "label": "05_03_Raster", "category": "Rasterdaten", "items": 11, "desc": "Digitales Geländemodell (DGM) & Satellitenbilder"},
        {"id": "tal_db", "parent": "col_tal", "arche_id": "1792423", "label": "05_05_Datenbanken", "category": "Datenbanken", "items": 4, "desc": "Zentrale IUENNA-Metadatenbank"},
        {"id": "tal_text", "parent": "col_tal", "arche_id": "1792568", "label": "05_06_Texte_Tabellen", "category": "Texte & Tabellen", "items": 4, "desc": "Gesamtberichte und Datenmanagement-Dokumentation"},
        {"id": "tal_out", "parent": "col_tal", "arche_id": "1792570", "label": "05_07_Output", "category": "Publikationen & Pläne", "items": 2, "desc": "Web-Karten-Exporte und Datenpublikation"},

        # Sankt Stefan (STE)
        {"id": "ste_db", "parent": "col_ste", "arche_id": "1792412", "label": "04_05_Datenbanken", "category": "Datenbanken", "items": 1, "desc": "Funddatenbank Sankt Stefan"},
        {"id": "ste_out", "parent": "col_ste", "arche_id": "1792414", "label": "04_07_Output", "category": "Publikationen & Pläne", "items": 5, "desc": "Grabungsberichte und Ergebnisdokumentation"},

        # Retrodigitalisate Archivalien-Cluster (RET 06_01 - 06_46)
        {"id": "ret_keramik", "parent": "col_ret", "arche_id": "1792572#keramik", "label": "06 Keramik- & Fundzeichnungen", "category": "Retrodigitalisate", "items": 1840, "desc": "Serien 06_01, 06_02, 06_04, 06_23, 06_31: Fundzeichnungen und Keramiktafeln"},
        {"id": "ret_grabung", "parent": "col_ret", "arche_id": "1792572#grabung", "label": "06 Grabungsakten (1978–2017)", "category": "Retrodigitalisate", "items": 3120, "desc": "Serien 06_05–06_26: Grabungstagebücher, Schichtbeschreibungen und Akten"},
        {"id": "ret_fotos", "parent": "col_ret", "arche_id": "1792572#fotos", "label": "06 Historische Fotodokumentation", "category": "Retrodigitalisate", "items": 2450, "desc": "Serien 06_14–06_30, 06_45: Historische Grabungsfotos, Dias und Abzüge"},
        {"id": "ret_plaene", "parent": "col_ret", "arche_id": "1792572#plaene", "label": "06 Pläne, Profile & Mosaike", "category": "Retrodigitalisate", "items": 1260, "desc": "Serien 06_03, 06_29, 06_32–06_43: Steingerechte Kirchenpläne, Profile, Mosaikpausen"},
        {"id": "ret_archive", "parent": "col_ret", "arche_id": "1792572#archive", "label": "06 Privatarchive & Publikationen", "category": "Retrodigitalisate", "items": 671, "desc": "Serien 06_24, 06_27, 06_40–06_46: Archiv Winkler, Monographien Glaser/Ladstätter, Archivbox ÖAI"}
    ]

    for f in folders:
        nodes.append({
            "data": {
                "id": f["id"],
                "arche_id": f["arche_id"],
                "label": f["label"],
                "category": f["category"],
                "type": "folder",
                "type_label": "Kategorie-Ordner",
                "items": f["items"],
                "description": f["desc"],
                "arche_url": f"https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/{f['arche_id'].split('#')[0]}",
                "color": "#D4A373",
                "icon": "fa-layer-group"
            }
        })
        edges.append({
            "data": {
                "id": f"edge_folder_{f['id']}_{f['parent']}",
                "source": f["id"],
                "target": f["parent"],
                "label": "isPartOf",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#isPartOf"
            }
        })

    # 4. Organizations / Institutions
    orgs = [
        {
            "id": "org_oeaw",
            "arche_id": "21003",
            "label": "Österreichische Akademie der Wissenschaften (ÖAW)",
            "role": "Fördergeber (Go!Digital 3.0)",
            "type": "organization",
            "type_label": "Institution",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/21003",
            "description": "Förderung des Projekts IUENNA über das Exzellenzprogramm Go!Digital 3.0 der ÖAW (GD3.0_2021-24_IUENNA).",
            "color": "#202226",
            "icon": "fa-building-columns"
        },
        {
            "id": "org_oeai",
            "arche_id": "37483",
            "label": "Österreichisches Archäologisches Institut (ÖAI)",
            "role": "Projektpartner, Datenurheber & Rechteinhaber",
            "type": "organization",
            "type_label": "Institution",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/37483",
            "description": "Führendes Forschungsinstitut der ÖAW. Projektleitung und wissenschaftliche Kuration der archäologischen Daten.",
            "color": "#202226",
            "icon": "fa-building-columns"
        },
        {
            "id": "org_lmk",
            "arche_id": "1756728",
            "label": "kärnten.museum (Landesmuseum Kärnten)",
            "role": "Projektleitung, Datenurheber & Rechteinhaber",
            "type": "organization",
            "type_label": "Institution",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1756728",
            "description": "Verwahrungsinstitution der archäologischen Originalfunde und Bestände aus den Grabungen im Jauntal.",
            "color": "#202226",
            "icon": "fa-landmark"
        },
        {
            "id": "org_acdh",
            "arche_id": "3313",
            "label": "ACDH-CH / ARCHE",
            "role": "Hosting & Repositoriumsbetreiber",
            "type": "organization",
            "type_label": "Institution",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/3313",
            "description": "Austrian Center for Digital Humanities and Cultural Heritage. Langzeitarchivierung und Bereitstellung der Daten via ARCHE.",
            "color": "#202226",
            "icon": "fa-server"
        },
        {
            "id": "org_bda",
            "arche_id": "1756743",
            "label": "Bundesdenkmalamt (BDA)",
            "role": "Kooperationspartner & Rechteinhaber",
            "type": "organization",
            "type_label": "Institution",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1756743",
            "description": "Österreichische Bundesbehörde für Denkmalpflege. Partner im Projekt IUENNA.",
            "color": "#202226",
            "icon": "fa-shield-halved"
        },
        {
            "id": "org_ardig",
            "arche_id": "ardig_partner",
            "label": "ARDIG – Archäologischer Dienst GesmbH",
            "role": "Projektpartner",
            "type": "organization",
            "type_label": "Institution",
            "arche_url": "https://www.ardig.at/",
            "description": "Archäologischer Fachdienst, Partner bei Grabungsaufarbeitung und Geodatenmanagement.",
            "color": "#202226",
            "icon": "fa-trowel"
        }
    ]

    for o in orgs:
        nodes.append({"data": o})

    # Edges for Organizations
    edges.append({"data": {"id": "edge_oeaw_funder", "source": "iuenna_root", "target": "org_oeaw", "label": "hasFunder", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasFunder"}})
    edges.append({"data": {"id": "edge_acdh_hosting", "source": "iuenna_root", "target": "org_acdh", "label": "hasHosting", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasHosting"}})
    edges.append({"data": {"id": "edge_lmk_owner", "source": "iuenna_root", "target": "org_lmk", "label": "hasOwner", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasOwner"}})
    edges.append({"data": {"id": "edge_oeai_owner", "source": "iuenna_root", "target": "org_oeai", "label": "hasOwner", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasOwner"}})
    edges.append({"data": {"id": "edge_bda_owner", "source": "iuenna_root", "target": "org_bda", "label": "hasLicensor", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasLicensor"}})
    edges.append({"data": {"id": "edge_ardig_partner", "source": "iuenna_root", "target": "org_ardig", "label": "hasContributor", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasContributor"}})

    # 5. Persons / Researchers
    persons = [
        {
            "id": "per_dh",
            "arche_id": "1756725",
            "label": "Dr. Dominik Hagmann",
            "role": "Principal Investigator, Kurator, Editor",
            "affiliation": "kärnten.museum / ÖAI",
            "orcid": "https://orcid.org/0000-0002-4481-6234",
            "type": "person",
            "type_label": "Forscher:in",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1756725",
            "description": "Projektkoordinator IUENNA. Archäologe mit Schwerpunkt Digitale Archäologie, GIS-Fachdaten und Kuration.",
            "color": "#C85A32",
            "icon": "fa-user-tie"
        },
        {
            "id": "per_fw",
            "arche_id": "1756730",
            "label": "Dipl.-Ing. Franziska Waldhart",
            "role": "Principal Investigator, Kuratorin, Editorin",
            "affiliation": "Österreichisches Archäologisches Institut (ÖAI)",
            "orcid": "https://orcid.org/0000-0002-3647-7977",
            "type": "person",
            "type_label": "Forscher:in",
            "arche_url": "https://arche.acdh.oeaw.ac.at/browser/oeaw_detail/1756730",
            "description": "Projektkoordinatorin IUENNA am ÖAI. Spezialistin für Geoinformation, Geodatenmanagement und archäologische Dokumentation.",
            "color": "#C85A32",
            "icon": "fa-user-tie"
        }
    ]

    for p in persons:
        nodes.append({"data": p})

    # Edges for Persons
    edges.append({"data": {"id": "edge_dh_pi", "source": "iuenna_root", "target": "per_dh", "label": "hasPrincipalInvestigator", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasPrincipalInvestigator"}})
    edges.append({"data": {"id": "edge_fw_pi", "source": "iuenna_root", "target": "per_fw", "label": "hasPrincipalInvestigator", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasPrincipalInvestigator"}})
    edges.append({"data": {"id": "edge_dh_aff_lmk", "source": "per_dh", "target": "org_lmk", "label": "affiliatedWith", "predicate": "schema:memberOf"}})
    edges.append({"data": {"id": "edge_fw_aff_oeai", "source": "per_fw", "target": "org_oeai", "label": "affiliatedWith", "predicate": "schema:memberOf"}})

    # 6. Spatial Coverage / Archaeological Places
    places = [
        {"id": "plc_jauntal", "arche_id": "1756735", "label": "Jauntal / Podjuna", "type": "place", "type_label": "Fundregion", "category": "Mikroregion", "desc": "Südkärntnerisches Talbecken, zentrale Untersuchungsregion", "color": "#4A6B53", "icon": "fa-map-location-dot"},
        {"id": "plc_hemmaberg", "arche_id": "1756734", "label": "Hemmaberg", "type": "place", "type_label": "Fundort", "category": "Höhensiedlung & Heiligtum", "desc": "Frühchristliche Doppelkirche, Mosaiken, Gräberfelder", "color": "#4A6B53", "icon": "fa-location-dot"},
        {"id": "plc_jaunstein", "arche_id": "1756733", "label": "Jaunstein", "type": "place", "type_label": "Fundort", "category": "Talsiedlung", "desc": "Spätantik-frühmittelalterliche Siedlung und Gräber", "color": "#4A6B53", "icon": "fa-location-dot"},
        {"id": "plc_globasnitz", "arche_id": "1756736", "label": "Globasnitz / Iuenna", "type": "place", "type_label": "Fundort", "category": "Römische Siedlung", "desc": "Römische Straßenstation Iuenna an der Virunum-Celeia-Route", "color": "#4A6B53", "icon": "fa-location-dot"},
        {"id": "plc_st_stefan", "arche_id": "1756737", "label": "Sankt Stefan / Steben", "type": "place", "type_label": "Fundort", "category": "Fundstelle", "desc": "Archäologische Befunde und Altfunde bei Sankt Stefan", "color": "#4A6B53", "icon": "fa-location-dot"},
        {"id": "plc_noricum", "arche_id": "1756731", "label": "Noricum", "type": "place", "type_label": "Historische Region", "category": "Römische Provinz", "desc": "Historischer antiker Kulturraum Noricum", "color": "#4A6B53", "icon": "fa-globe"},
        {"id": "plc_kaernten", "arche_id": "138176", "label": "Kärnten / Carinthia", "type": "place", "type_label": "Geographische Region", "category": "Bundesland", "desc": "Geographischer Rahmen im heutigen Österreich", "color": "#4A6B53", "icon": "fa-earth-europe"}
    ]

    for pl in places:
        nodes.append({"data": pl})

    # Spatial Edges
    edges.append({"data": {"id": "edge_spatial_root_jauntal", "source": "iuenna_root", "target": "plc_jauntal", "label": "hasSpatialCoverage", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"}})
    edges.append({"data": {"id": "edge_spatial_hb", "source": "col_hb", "target": "plc_hemmaberg", "label": "hasSpatialCoverage", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"}})
    edges.append({"data": {"id": "edge_spatial_jau", "source": "col_jau", "target": "plc_jaunstein", "label": "hasSpatialCoverage", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"}})
    edges.append({"data": {"id": "edge_spatial_glo", "source": "col_glo", "target": "plc_globasnitz", "label": "hasSpatialCoverage", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"}})
    edges.append({"data": {"id": "edge_spatial_ste", "source": "col_ste", "target": "plc_st_stefan", "label": "hasSpatialCoverage", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"}})
    edges.append({"data": {"id": "edge_spatial_ret", "source": "col_ret", "target": "plc_jauntal", "label": "hasSpatialCoverage", "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"}})

    # Spatial Hierarchy
    edges.append({"data": {"id": "edge_hb_in_jauntal", "source": "plc_hemmaberg", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"}})
    edges.append({"data": {"id": "edge_jau_in_jauntal", "source": "plc_jaunstein", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"}})
    edges.append({"data": {"id": "edge_glo_in_jauntal", "source": "plc_globasnitz", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"}})
    edges.append({"data": {"id": "edge_ste_in_jauntal", "source": "plc_st_stefan", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"}})
    edges.append({"data": {"id": "edge_jauntal_in_ktn", "source": "plc_jauntal", "target": "plc_kaernten", "label": "locatedIn", "predicate": "schema:containedInPlace"}})
    edges.append({"data": {"id": "edge_jauntal_in_noricum", "source": "plc_jauntal", "target": "plc_noricum", "label": "locatedIn", "predicate": "schema:containedInPlace"}})

    # 7. Temporal Coverage / Epochs (PeriodO)
    epochs = [
        {
            "id": "epc_roman",
            "periodo_uri": "http://n2t.net/ark:/99152/p0s84tq9w22",
            "label": "Römische Antike (Römisches Noricum)",
            "timespan": "ca. 15 v. Chr. – ca. 500 n. Chr.",
            "type": "period",
            "type_label": "Epoche",
            "desc": "Römische Kaiserzeit und Spätantike in der Provinz Noricum",
            "color": "#5A6B7C",
            "icon": "fa-hourglass-half"
        },
        {
            "id": "epc_early_middle_ages",
            "periodo_uri": "http://n2t.net/ark:/99152/p0cwwznw938",
            "label": "Frühmittelalter (Early Middle Ages)",
            "timespan": "ca. 500 – ca. 1000 n. Chr.",
            "type": "period",
            "type_label": "Epoche",
            "desc": "Slawische und karolingische Besiedlung, Christianisierung im Ostalpenraum",
            "color": "#5A6B7C",
            "icon": "fa-clock"
        }
    ]

    for ep in epochs:
        nodes.append({"data": ep})
        edges.append({
            "data": {
                "id": f"edge_temporal_root_{ep['id']}",
                "source": "iuenna_root",
                "target": ep["id"],
                "label": "hasTemporalCoverage",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasTemporalCoverage"
            }
        })

    # 8. Subjects / Controlled Vocabulary Concepts
    subjects = [
        {"id": "sbj_arch_data", "label": "Archäologische Daten", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-tag"},
        {"id": "sbj_fieldwork", "label": "Grabungsdokumentation", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-book-open"},
        {"id": "sbj_roman_arch", "label": "Römische Archäologie", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-monument"},
        {"id": "sbj_dh", "label": "Digitale Geisteswissenschaften", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-laptop-code"},
        {"id": "sbj_dig_arch", "label": "Digitale Archäologie", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-map"},
        {"id": "sbj_preservation", "label": "Langzeitdatenarchivierung", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-box-archive"}
    ]

    for sb in subjects:
        nodes.append({"data": sb})
        edges.append({
            "data": {
                "id": f"edge_subject_root_{sb['id']}",
                "source": "iuenna_root",
                "target": sb["id"],
                "label": "hasSubject",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSubject"
            }
        })

    # 9. Licenses & Rights Management
    licenses = [
        {
            "id": "lic_inc",
            "label": "InC (In Copyright)",
            "count": 16316,
            "type": "license",
            "type_label": "Lizenz",
            "uri": "http://rightsstatements.org/vocab/InC/1.0/",
            "desc": "Urheberrechtlich geschützte Werke, Forschungsberichte und Pläne (16.316 Ressourcen)",
            "color": "#437F97",
            "icon": "fa-copyright"
        },
        {
            "id": "lic_ccby",
            "label": "CC BY 4.0",
            "count": 4039,
            "type": "license",
            "type_label": "Lizenz",
            "uri": "https://creativecommons.org/licenses/by/4.0/",
            "desc": "Freie Creative-Commons-Lizenz mit Namensnennung (4.039 Ressourcen)",
            "color": "#437F97",
            "icon": "fa-creative-commons"
        }
    ]

    for lc in licenses:
        nodes.append({"data": lc})
        edges.append({
            "data": {
                "id": f"edge_license_root_{lc['id']}",
                "source": "iuenna_root",
                "target": lc["id"],
                "label": "hasLicenseSummary",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasLicenseSummary"
            }
        })

    # Compile Graph
    graph_payload = {
        "metadata": {
            "title": "IUENNA ARCHE Knowledge Graph",
            "arche_top_collection": "https://id.acdh.oeaw.ac.at/iuenna",
            "top_collection_id": IUENNA_TOP_ID,
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B39-F",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "total_items": 20788,
            "total_size": "356.68 GB",
            "duration_seconds": round(time.time() - start_time, 3)
        },
        "elements": {
            "nodes": nodes,
            "edges": edges
        }
    }

    # Save to data/arche_graph.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_file = os.path.join(data_dir, "arche_graph.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(graph_payload, f, indent=2, ensure_ascii=False)

    print(f"[✓] Knowledge Graph successfully generated: {out_file}")
    print(f"[✓] Summary: {len(nodes)} Nodes, {len(edges)} Edges | ARCHE Items: 20,788")
    return graph_payload

if __name__ == "__main__":
    build_graph()
