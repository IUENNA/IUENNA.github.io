#!/usr/bin/env python3
"""
build_complete_arche_graph.py
Builds the complete Cytoscape Knowledge Graph containing:
 - All 434 Collections (L0 - L6)
 - All 21 Persons (with ORCID, Wikidata, affiliation)
 - All 9 Organisations (with ROR, Wikidata)
 - All 23 Publications (with authors, year, publisher, pages, URL)
 - Primary Places, Epochs, Subjects, Licenses
 - Full semantic edge network (isPartOf, hasCreator, hasContributor, hasAuthor, documents, isMemberOf, hasSpatialCoverage)
"""

import os
import re
import json
import time
import math
import networkx as nx

def format_size(size_bytes):
    if not size_bytes:
        return "0 B"
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit in ['MB', 'GB'] else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

LEVEL_COLORS = {
    0: "#8B2616",  # TopCollection (L0): Rich Terracotta
    1: "#C85A32",  # Subcollection (L1): Warm Rust
    2: "#D48B38",  # Hauptkategorie (L2): Golden Amber
    3: "#3D7068",  # Fachordner (L3): Forest Teal
    4: "#5B8296",  # Teilsammlung (L4): Slate Blue
    5: "#6A5D7B",  # Befundordner (L5): Dusty Purple
    6: "#8A6D5D",  # Detailordner (L6): Warm Muted Umber
}

LEVEL_LABELS = {
    0: "Top-Collection",
    1: "Subcollection (L1)",
    2: "Hauptkategorie (L2)",
    3: "Fachordner (L3)",
    4: "Teilsammlung (L4)",
    5: "Befundordner (L5)",
    6: "Detailordner (L6)",
}

LEVEL_ICONS = {
    0: "fa-landmark",
    1: "fa-folder-tree",
    2: "fa-folder-open",
    3: "fa-folder",
    4: "fa-folder-minus",
    5: "fa-box-archive",
    6: "fa-camera",
}

def build_graph():
    start_time = time.time()
    data_dir = "data"
    
    # 1. Load inputs
    tree_file = os.path.join(data_dir, "arche_collections_tree.json")
    entities_file = os.path.join(data_dir, "arche_resolved_entities.json")
    creators_file = os.path.join(data_dir, "arche_collection_creators.json")
    pubs_file = os.path.join(data_dir, "arche_publications.json")
    places_file = os.path.join(data_dir, "arche_places.json")
    datasets_file = os.path.join(data_dir, "arche_datasets.json")
    corpus_file = os.path.join(data_dir, "arche_corpus.json")

    print(f"[*] Loading datasets from {data_dir}...")
    with open(tree_file, "r", encoding="utf-8") as f:
        root_tree = json.load(f)
    with open(entities_file, "r", encoding="utf-8") as f:
        entities_data = json.load(f)
        persons = entities_data.get("persons", {})
        organisations = entities_data.get("organisations", {})
    with open(creators_file, "r", encoding="utf-8") as f:
        col_creators = json.load(f)
    with open(pubs_file, "r", encoding="utf-8") as f:
        publications = json.load(f)
    with open(places_file, "r", encoding="utf-8") as f:
        places_data = json.load(f)
    with open(datasets_file, "r", encoding="utf-8") as f:
        datasets_data = json.load(f)
    with open(corpus_file, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)
        corpus = corpus_data.get("resources", [])

    # Flatten collection tree
    root_node = root_tree.get("root", root_tree)
    collections = []
    def flatten_tree(node, parent_id=None):
        c = dict(node)
        c["parent_id"] = parent_id
        children = c.pop("children", [])
        collections.append(c)
        for ch in children:
            flatten_tree(ch, node["arche_id"])

    flatten_tree(root_node)
    print(f"[✓] Flattened {len(collections)} collections from tree.")

    nodes = []
    edges = []
    seen_edge_ids = set()
    seen_edge_triples = set()

    def add_edge(edge_data):
        e_id = edge_data["id"]
        triple = (edge_data["source"], edge_data["target"], edge_data["label"])
        if e_id not in seen_edge_ids and triple not in seen_edge_triples:
            seen_edge_ids.add(e_id)
            seen_edge_triples.add(triple)
            edges.append({"data": edge_data})

    # 2. Add Collection Nodes & isPartOf Edges
    for col in collections:
        lvl = col.get("level", 1)
        arche_id = col["arche_id"]
        node_id = "iuenna_root" if arche_id == "1792170" else col["id"]
        parent_id = col.get("parent_id")

        ntype = "root" if lvl == 0 else ("subcollection" if lvl == 1 else f"folder_l{lvl}")
        col_meta = root_tree.get("collections", {}).get(arche_id, col)
        label = col_meta.get("title") or col.get("title") or col.get("name") or arche_id
        alt_label = col_meta.get("alternative_title") or col_meta.get("filename") or col.get("alt_title") or col.get("name") or ""

        node_data = {
            "id": node_id,
            "arche_id": arche_id,
            "label": label,
            "title": col_meta.get("title") or col.get("title") or label,
            "full_title": col_meta.get("title") or col.get("title") or label,
            "alt_title": alt_label,
            "filename": col_meta.get("filename") or col.get("filename") or "",
            "level": lvl,
            "type": ntype,
            "type_label": LEVEL_LABELS.get(lvl, f"Ebene L{lvl}"),
            "color": LEVEL_COLORS.get(lvl, "#5A6B7C"),
            "icon": LEVEL_ICONS.get(lvl, "fa-folder"),
            "items": col.get("items", 0),
            "size": col.get("formatted_size", "0 B"),
            "formatted_size": col.get("formatted_size", "0 B"),
            "size_bytes": col.get("size_bytes", 0),
            "pid": col.get("pid", ""),
            "license": col.get("license", ""),
            "license_summary": col.get("license", ""),
            "access": col.get("access", ""),
            "access_restriction": col.get("access", ""),
            "campaign_years": col.get("campaign_years"),
            "creators": col_creators.get(arche_id, {}).get("creators", []),
            "contributors": col_creators.get(arche_id, {}).get("contributors", []),
            "uri": f"https://arche.acdh.oeaw.ac.at/api/{arche_id}"
        }
        nodes.append({"data": node_data})

        # Add isPartOf edge
        if parent_id:
            parent_node_id = "iuenna_root" if parent_id == "1792170" else f"col_{parent_id}"
            add_edge({
                "id": f"edge_part_{node_id}_{parent_node_id}",
                "source": node_id,
                "target": parent_node_id,
                "label": "isPartOf",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#isPartOf"
            })

        # Add Spatial Coverage edges (both direct and from collection resources)
        all_spatial = set(col_meta.get("spatial_ids", []))
        all_spatial.update(col_meta.get("item_spatial_ids", []))
        all_spatial.update(col.get("item_spatial_ids", []))
        for sid in all_spatial:
            sid_str = str(sid)
            if sid_str in places_data:
                add_edge({
                    "id": f"edge_spat_{node_id}_plc_{sid_str}",
                    "source": node_id,
                    "target": f"plc_{sid_str}",
                    "label": "hasSpatialCoverage",
                    "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"
                })

        # Add Creator & Contributor edges
        for cr in col_creators.get(arche_id, {}).get("creators", []):
            target_id = cr["id"]
            add_edge({
                "id": f"edge_creator_{node_id}_{target_id}",
                "source": node_id,
                "target": target_id,
                "label": "hasCreator",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasCreator"
            })

        for ct in col_creators.get(arche_id, {}).get("contributors", []):
            target_id = ct["id"]
            add_edge({
                "id": f"edge_contrib_{node_id}_{target_id}",
                "source": node_id,
                "target": target_id,
                "label": "hasContributor",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasContributor"
            })

    # 2b. Add Dataset Nodes & Edges (GeoPackages & Research Datasets)
    print(f"[*] Adding {len(datasets_data)} primary research datasets...")
    for d_id, d in datasets_data.items():
        node_id = f"dts_{d_id}"
        parent_id = d.get("parent_id")
        parent_node_id = "iuenna_root" if parent_id == "1792170" else f"col_{parent_id}"

        node_data = {
            "id": node_id,
            "arche_id": str(d_id),
            "label": d["filename"],
            "title": d["filename"],
            "full_title": d.get("title") or d["filename"],
            "filename": d["filename"],
            "type": "dataset",
            "type_label": "Forschungsdatensatz / GeoPackage",
            "category": "Geodaten & Forschungsdaten",
            "color": "#1B4965",
            "icon": "fa-database",
            "items": len(d.get("spatial_ids", [])),
            "size": d.get("formatted_size", "0 B"),
            "formatted_size": d.get("formatted_size", "0 B"),
            "size_bytes": d.get("size_bytes", 0),
            "pid": d.get("pid", ""),
            "license": d.get("license_summary", ""),
            "license_summary": d.get("license_summary", ""),
            "access": d.get("access_restriction", ""),
            "access_restriction": d.get("access_restriction", ""),
            "description": d.get("description", ""),
            "citation": d.get("citation", ""),
            "creators": d.get("creators", []),
            "contributors": d.get("contributors", []),
            "spatial_ids": d.get("spatial_ids", []),
            "parent_id": parent_id,
            "uri": d.get("uri", f"https://arche.acdh.oeaw.ac.at/api/{d_id}")
        }
        nodes.append({"data": node_data})

        # isPartOf edge to parent collection
        if parent_id:
            add_edge({
                "id": f"edge_part_{node_id}_{parent_node_id}",
                "source": node_id,
                "target": parent_node_id,
                "label": "isPartOf",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#isPartOf"
            })

        # hasCreator edges
        for cr in d.get("creators", []):
            cr_target = cr["id"]
            add_edge({
                "id": f"edge_creator_{node_id}_{cr_target}",
                "source": node_id,
                "target": cr_target,
                "label": "hasCreator",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasCreator"
            })

        # hasSpatialCoverage edges (e.g. 140 places for 1804081!)
        for sid in d.get("spatial_ids", []):
            sid_str = str(sid)
            if sid_str in places_data:
                add_edge({
                    "id": f"edge_spat_{node_id}_plc_{sid_str}",
                    "source": node_id,
                    "target": f"plc_{sid_str}",
                    "label": "hasSpatialCoverage",
                    "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasSpatialCoverage"
                })

        # documents edges
        for doc_id in d.get("documented_ids", []):
            if doc_id in publications:
                add_edge({
                    "id": f"edge_doc_{node_id}_pub_{doc_id}",
                    "source": node_id,
                    "target": f"pub_{doc_id}",
                    "label": "documents",
                    "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#documents"
                })

    # 3. Add Person Nodes
    for p_id, p in persons.items():
        node_data = {
            "id": p["id"],
            "arche_id": p_id,
            "label": p["name"],
            "name": p["name"],
            "first_name": p.get("first_name", ""),
            "last_name": p.get("last_name", ""),
            "academic_title": p.get("academic_title", ""),
            "type": "person",
            "type_label": "Forscher:in",
            "category": "Akteur",
            "email": p.get("email", ""),
            "orcid": p.get("orcid"),
            "wikidata": p.get("wikidata"),
            "viaf": p.get("viaf"),
            "gnd": p.get("gnd"),
            "affiliation": p.get("affiliation"),
            "affiliation_id": p.get("affiliation_id"),
            "color": "#C85A32",
            "icon": "fa-user",
            "uri": p["uri"]
        }
        nodes.append({"data": node_data})

        # isMemberOf edge
        if p.get("affiliation_id"):
            aff_org_id = f"org_{p['affiliation_id']}"
            add_edge({
                "id": f"edge_member_{p['id']}_{aff_org_id}",
                "source": p["id"],
                "target": aff_org_id,
                "label": "isMemberOf",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#isMemberOf"
            })

    # 4. Add Organisation Nodes
    for o_id, org in organisations.items():
        node_data = {
            "id": org["id"],
            "arche_id": o_id,
            "label": org.get("short_name") or org["name"],
            "name": org["name"],
            "full_name": org["name"],
            "short_name": org.get("short_name", ""),
            "type": "organization",
            "type_label": "Institution / Partner",
            "category": "Trägerorganisation",
            "city": org.get("city", ""),
            "country": org.get("country", ""),
            "url": org.get("url", ""),
            "wikidata": org.get("wikidata"),
            "ror": org.get("ror"),
            "color": "#3B5266",
            "icon": "fa-building-columns",
            "uri": org["uri"]
        }
        nodes.append({"data": node_data})

        # parent org edge
        if org.get("parent_org_id"):
            parent_org_node = f"org_{org['parent_org_id']}"
            add_edge({
                "id": f"edge_org_member_{org['id']}_{parent_org_node}",
                "source": org["id"],
                "target": parent_org_node,
                "label": "isMemberOf",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#isMemberOf"
            })

    # 5. Add Publication Nodes
    for pub_id, pub in publications.items():
        node_data = {
            "id": pub["id"],
            "arche_id": pub_id,
            "label": pub["title"],
            "title": pub["title"],
            "type": "publication",
            "type_label": "Publikation",
            "category": "Fachpublikation",
            "year": pub.get("year", "–"),
            "issued_date": pub.get("issued_date", ""),
            "authors": pub.get("authors_formatted", ""),
            "publisher": pub.get("publisher", ""),
            "series": pub.get("series", ""),
            "pages": pub.get("pages", ""),
            "url": pub.get("url", ""),
            "color": "#7B4F36",
            "icon": "fa-book-open",
            "uri": pub["uri"]
        }
        nodes.append({"data": node_data})

        # hasAuthor edges
        for a_id in pub.get("author_ids", []):
            if a_id in persons:
                author_node_id = f"per_{a_id}"
                add_edge({
                    "id": f"edge_pub_author_{pub['id']}_{author_node_id}",
                    "source": pub["id"],
                    "target": author_node_id,
                    "label": "hasAuthor",
                    "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#hasAuthor"
                })

        # documents edges
        for d_id in pub.get("documents", []):
            doc_target = "iuenna_root" if d_id == "1792170" else f"col_{d_id}"
            add_edge({
                "id": f"edge_pub_doc_{pub['id']}_{doc_target}",
                "source": pub["id"],
                "target": doc_target,
                "label": "documents",
                "predicate": "https://vocabs.acdh.oeaw.ac.at/schema#documents"
            })

    # 6. Places (authoritative from arche_places.json)
    for p_id, pl in places_data.items():
        node_id = f"plc_{p_id}"
        node_data = {
            "id": node_id,
            "arche_id": str(p_id),
            "label": pl.get("title") or f"Ort {p_id}",
            "title": pl.get("title") or f"Ort {p_id}",
            "type": "place",
            "type_label": "Fundort / Ort",
            "category": "Geographischer Fundort",
            "latitude": pl.get("latitude"),
            "longitude": pl.get("longitude"),
            "wkt": pl.get("wkt"),
            "geonames": pl.get("geonames", ""),
            "color": "#2D6A4F",
            "icon": "fa-location-dot",
            "uri": pl.get("uri", f"https://arche.acdh.oeaw.ac.at/api/{p_id}")
        }
        nodes.append({"data": node_data})

    # Spatial edge for root
    for r_sid in ["1756730", "1756735", "1756731", "138176"]:
        if r_sid in places_data:
            add_edge({"id": f"edge_spat_root_{r_sid}", "source": "iuenna_root", "target": f"plc_{r_sid}", "label": "hasSpatialCoverage", "predicate": "schema:hasSpatialCoverage"})

    # Verify and ensure 100% graph connectivity for all places
    place_node_ids = set(f"plc_{pid}" for pid in places_data)
    connected_places = set(e["data"]["target"] for e in edges if e["data"]["target"] in place_node_ids)
    connected_places.update(e["data"]["source"] for e in edges if e["data"]["source"] in place_node_ids)
    unconnected = place_node_ids - connected_places
    if unconnected:
        print(f"[*] Connecting {len(unconnected)} remaining places to root fallback...")
        for u in sorted(unconnected):
            add_edge({"id": f"edge_spat_fallback_{u}", "source": "iuenna_root", "target": u, "label": "hasSpatialCoverage", "predicate": "schema:hasSpatialCoverage"})
    print(f"[✓] Place connectivity verified: {len(place_node_ids)} / {len(place_node_ids)} places connected (0 isolated).")

    # 7. Epochs
    epochs = [
        {"id": "epc_roman", "label": "Römische Kaiserzeit", "type": "epoch", "type_label": "Zeitepoche", "uri": "http://n2t.net/ark:/99152/p0qhb66t32q", "range": "15 v. Chr. – 476 n. Chr.", "color": "#5A6B7C", "icon": "fa-hourglass-half"},
        {"id": "epc_early_medieval", "label": "Frühmittelalter", "type": "epoch", "type_label": "Zeitepoche", "uri": "http://n2t.net/ark:/99152/p0qhb66h52w", "range": "ca. 500 – 1050 n. Chr.", "color": "#5A6B7C", "icon": "fa-clock"}
    ]
    for ep in epochs:
        nodes.append({"data": ep})
        add_edge({"id": f"edge_epc_{ep['id']}_root", "source": "iuenna_root", "target": ep["id"], "label": "hasTemporalCoverage", "predicate": "schema:hasTemporalCoverage"})

    # 8. Subjects & Licenses
    subjects = [
        {"id": "sbj_arch_data", "label": "Archäologische Daten", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-tag"},
        {"id": "sbj_fieldwork", "label": "Grabungsdokumentation", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-book-open"},
        {"id": "sbj_roman_arch", "label": "Römische Archäologie", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-monument"},
        {"id": "sbj_dh", "label": "Digitale Geisteswissenschaften", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-laptop-code"},
        {"id": "sbj_dig_arch", "label": "Dokumentarfotografien", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-camera"},
        {"id": "sbj_reprografie", "label": "Reprografien & Aufmaße", "type": "subject", "type_label": "Fachschlagwort", "color": "#7E6B8F", "icon": "fa-pen-ruler"}
    ]
    for sb in subjects:
        nodes.append({"data": sb})
        add_edge({"id": f"edge_sbj_{sb['id']}_root", "source": "iuenna_root", "target": sb["id"], "label": "hasSubject", "predicate": "schema:hasSubject"})

    licenses = [
        {"id": "lic_inc", "label": "In Copyright (InC 1.0)", "type": "license", "type_label": "Lizenz / Nutzungsrechte", "desc": "Urheberrechtlich geschützte Archivbestände des kärnten.museums und ÖAI.", "color": "#437F97", "icon": "fa-shield-halved"},
        {"id": "lic_ccby", "label": "Creative Commons Attribution 4.0 (CC BY 4.0)", "type": "license", "type_label": "Open Access Lizenz", "desc": "Open Access Forschungsdaten des Go!Digital-Projekts IUENNA.", "color": "#3D7068", "icon": "fa-creative-commons"}
    ]
    for lc in licenses:
        nodes.append({"data": lc})
        add_edge({"id": f"edge_lic_{lc['id']}_root", "source": "iuenna_root", "target": lc["id"], "label": "hasLicense", "predicate": "schema:hasLicense"})

    # 8.2 Extract comprehensive semantic relations from arche_full_metadata.ttl
    ttl_file = os.path.join(data_dir, "arche_full_metadata.ttl")
    if os.path.exists(ttl_file):
        print("[*] Extracting comprehensive semantic relations from arche_full_metadata.ttl...")
        node_id_map = {}
        for c in collections:
            aid = str(c.get("arche_id"))
            node_id_map[aid] = "iuenna_root" if aid == "1792170" else c.get("id") or f"col_{aid}"
        for d_id in datasets_data:
            node_id_map[str(d_id)] = f"dts_{d_id}"
        for p_id in persons:
            node_id_map[str(p_id)] = f"per_{p_id}"
        for o_id in organisations:
            node_id_map[str(o_id)] = f"org_{o_id}"
        for pub_id in publications:
            node_id_map[str(pub_id)] = f"pub_{pub_id}"
        for plc_id in places_data:
            node_id_map[str(plc_id)] = f"plc_{plc_id}"

        ttl_target_preds = {
            "hasHosting": "hasHosting",
            "hasOwner": "hasOwner",
            "hasLicensor": "hasLicensor",
            "hasRightsHolder": "hasRightsHolder",
            "hasCurator": "hasCurator",
            "hasDepositor": "hasDepositor",
            "hasMetadataCreator": "hasMetadataCreator",
            "hasCreator": "hasCreator",
            "hasContributor": "hasContributor",
            "documents": "documents",
            "hasDigitisingAgent": "hasDigitisingAgent",
            "hasSpatialCoverage": "hasSpatialCoverage"
        }

        ttl_edges_added = 0
        with open(ttl_file, "r", encoding="utf-8") as f:
            curr_subj = None
            for line in f:
                m_subj = re.match(r"^<https://arche.acdh.oeaw.ac.at/api/(\d+)>", line)
                if m_subj:
                    curr_subj = m_subj.group(1)
                if curr_subj and curr_subj in node_id_map:
                    source_nid = node_id_map[curr_subj]
                    for pred, target_aid in re.findall(r"n2:([a-zA-Z0-9_]+)\s+<https://arche.acdh.oeaw.ac.at/api/(\d+)>", line):
                        if pred in ttl_target_preds and target_aid in node_id_map:
                            target_nid = node_id_map[target_aid]
                            if source_nid != target_nid:
                                edge_lbl = ttl_target_preds[pred]
                                add_edge({
                                    "id": f"edge_ttl_{pred}_{source_nid}_{target_nid}",
                                    "source": source_nid,
                                    "target": target_nid,
                                    "label": edge_lbl,
                                    "predicate": f"https://vocabs.acdh.oeaw.ac.at/schema#{pred}"
                                })
                                ttl_edges_added += 1
        print(f"[✓] Successfully injected {ttl_edges_added} semantic edges from ARCHE TTL.")

    # 8.5 Add all 20,355 ARCHE Resources (arche:Resource)
    print(f"[*] Integrating {len(corpus)} ARCHE Resources into Knowledge Graph...")
    RES_TYPE_INFO = {
        'image': ('ARCHE-Bild', '#2A9D8F', 'fa-image'),
        'vector': ('ARCHE-Plan/Vektor', '#E76F51', 'fa-draw-polygon'),
        'document': ('ARCHE-Dokument/PDF', '#457B9D', 'fa-file-lines'),
        'database': ('ARCHE-Datenbank/Tabelle', '#1D3557', 'fa-table'),
        'model': ('ARCHE-3D-Modell', '#F4A261', 'fa-cube'),
        'audio': ('ARCHE-Audio', '#E9C46A', 'fa-volume-high'),
        'other': ('ARCHE-Datei', '#3D7068', 'fa-file')
    }

    place_node_ids = set(f"plc_{pid}" for pid in places_data)
    collection_id_set = set(c["id"] for c in collections)
    collection_id_set.add("iuenna_root")

    # Group resources by parent collection for radial clustering
    col_to_resources = {}
    for r in corpus:
        col_id = r.get("col_id") or f"col_{r.get('col')}"
        if col_id == "col_1792170" or col_id not in collection_id_set:
            col_id = "iuenna_root"
        if col_id not in col_to_resources:
            col_to_resources[col_id] = []
        col_to_resources[col_id].append(r)

    # Compute macro layout positions using NetworkX for structural nodes
    print("[*] Computing macro graph layout positions with NetworkX...")
    G_macro = nx.Graph()
    for n in nodes:
        G_macro.add_node(n["data"]["id"])
    for e in edges:
        G_macro.add_edge(e["data"]["source"], e["data"]["target"])

    pos_macro = nx.spring_layout(G_macro, k=0.18, iterations=60, seed=42)
    SCALE = 3500.0
    macro_positions = {}
    for nid, p in pos_macro.items():
        macro_positions[nid] = (p[0] * SCALE, p[1] * SCALE)

    # Assign positions to macro nodes
    for n in nodes:
        nid = n["data"]["id"]
        if nid in macro_positions:
            px, py = macro_positions[nid]
            n["position"] = {"x": round(px, 1), "y": round(py, 1)}

    # Now add all resources with positions clustered around their parent collection
    added_res_count = 0
    added_res_spatial_edges = 0

    for col_id, res_list in col_to_resources.items():
        cx, cy = macro_positions.get(col_id, (0.0, 0.0))

        for i, r in enumerate(res_list):
            rid = r["id"]
            arche_id = r.get("arche_id")
            ftype = r.get("type", "other")
            t_lbl, col, icon = RES_TYPE_INFO.get(ftype, ("ARCHE-Datei", "#3D7068", "fa-file"))

            # Golden spiral positioning around parent collection
            theta = i * 2.3999632
            radius = 35.0 + 14.0 * math.sqrt(i + 1)
            rx = cx + radius * math.cos(theta)
            ry = cy + radius * math.sin(theta)

            size_b = r.get("size_bytes", 0)
            res_node = {
                "data": {
                    "id": rid,
                    "arche_id": str(arche_id),
                    "label": r.get("title") or r.get("filename") or rid,
                    "title": r.get("title") or r.get("filename") or rid,
                    "filename": r.get("filename", ""),
                    "type": "resource",
                    "type_label": t_lbl,
                    "ftype": ftype,
                    "parent_col": col_id,
                    "pid": r.get("pid", ""),
                    "place": r.get("place", ""),
                    "spatial_ids": r.get("spatial_ids", []),
                    "subjs": r.get("subjs", []),
                    "path": r.get("path", []),
                    "date": r.get("date", ""),
                    "size_bytes": size_b,
                    "formatted_size": format_size(size_b),
                    "thumb_url": r.get("thumb_url", ""),
                    "coords": r.get("coords"),
                    "description": r.get("description", ""),
                    "color": col,
                    "icon": icon
                },
                "position": {
                    "x": round(rx, 1),
                    "y": round(ry, 1)
                }
            }
            nodes.append(res_node)
            added_res_count += 1

            # 1. isPartOf edge to parent collection
            add_edge({
                "id": f"edge_{rid}_partof_{col_id}",
                "source": rid,
                "target": col_id,
                "label": "isPartOf",
                "predicate": "arche:isPartOf"
            })

            # 2. hasSpatialCoverage edges to places
            for sid in r.get("spatial_ids", []):
                plc_target = f"plc_{sid}"
                if plc_target in place_node_ids:
                    add_edge({
                        "id": f"edge_{rid}_spat_{sid}",
                        "source": rid,
                        "target": plc_target,
                        "label": "hasSpatialCoverage",
                        "predicate": "arche:hasSpatialCoverage"
                    })
                    added_res_spatial_edges += 1

    print(f"[✓] Added {added_res_count} resource nodes and {added_res_spatial_edges} spatial coverage edges.")

    # Ensure 100% graph referential integrity: no edge can reference a non-existent node
    node_id_set = set(n["data"]["id"] for n in nodes)
    valid_edges = [e for e in edges if e["data"]["source"] in node_id_set and e["data"]["target"] in node_id_set]
    edges = valid_edges

    # 9. Assemble Graph Payload
    graph_payload = {
        "metadata": {
            "title": "IUENNA Complete ARCHE Knowledge Graph",
            "arche_uri": "https://id.acdh.oeaw.ac.at/iuenna",
            "top_collection_id": "1792170",
            "pid": "https://hdl.handle.net/21.11115/0000-0016-7B39-F",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "total_collections": len(collections),
            "total_datasets": len(datasets_data),
            "total_persons": len(persons),
            "total_organisations": len(organisations),
            "total_publications": len(publications),
            "total_places": len(places_data),
            "total_items": 20788,
            "total_resources": added_res_count,
            "total_size": "356.68 GB",
            "duration_seconds": round(time.time() - start_time, 3)
        },
        "elements": {
            "nodes": nodes,
            "edges": edges
        }
    }

    out_file = os.path.join(data_dir, "arche_graph.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(graph_payload, f, ensure_ascii=False)

    print(f"[✓] Knowledge Graph successfully generated: {out_file}")
    print(f"[✓] Summary: {len(nodes)} Nodes, {len(edges)} Edges | Collections: {len(collections)} | Datasets: {len(datasets_data)} | Resources: {added_res_count} | Persons: {len(persons)} | Orgs: {len(organisations)} | Pubs: {len(publications)} | Places: {len(places_data)}")
    return graph_payload

if __name__ == "__main__":
    build_graph()
