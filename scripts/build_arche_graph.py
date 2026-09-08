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

    def add_edge(edge_data):
        e_id = edge_data["id"]
        if e_id not in seen_edge_ids:
            seen_edge_ids.add(e_id)
            edges.append({"data": edge_data})

    # 2. Add Collection Nodes & isPartOf Edges
    for col in collections:
        lvl = col.get("level", 1)
        arche_id = col["arche_id"]
        node_id = "iuenna_root" if arche_id == "1792170" else col["id"]
        parent_id = col.get("parent_id")

        ntype = "root" if lvl == 0 else ("subcollection" if lvl == 1 else f"folder_l{lvl}")
        label = col.get("name") or col.get("title")

        node_data = {
            "id": node_id,
            "arche_id": arche_id,
            "label": label,
            "title": col.get("title") or label,
            "full_title": col.get("title") or label,
            "alt_title": col.get("alt_title") or "",
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

    # 6. Primary Places
    places = [
        {"id": "plc_jauntal", "arche_id": "1756730", "label": "Jauntal", "type": "place", "type_label": "Fundlandschaft", "category": "Mikroregion", "items": 20788, "desc": "Archäologische Mikroregion im südlichen Kärnten", "color": "#2D6A4F", "icon": "fa-mountain"},
        {"id": "plc_hemmaberg", "arche_id": "1756732", "label": "Hemmaberg", "type": "place", "type_label": "Fundort", "category": "Höhensiedlung & Wallfahrtsort", "items": 3657, "desc": "Bedeutendes spätantikes Pilgerheiligtum und Gräberfeld", "color": "#2D6A4F", "icon": "fa-location-dot"},
        {"id": "plc_jaunstein", "arche_id": "1756733", "label": "Jaunstein", "type": "place", "type_label": "Fundort", "category": "Talsiedlung", "items": 4899, "desc": "Spätantik-frühmittelalterliche Siedlung und Gräber", "color": "#2D6A4F", "icon": "fa-location-dot"},
        {"id": "plc_globasnitz", "arche_id": "1756736", "label": "Globasnitz / Iuenna", "type": "place", "type_label": "Fundort", "category": "Römische Siedlung", "items": 2775, "desc": "Römische Straßenstation Iuenna an der Virunum-Celeia-Route", "color": "#2D6A4F", "icon": "fa-location-dot"},
        {"id": "plc_st_stefan", "arche_id": "1756737", "label": "Sankt Stefan / Steben", "type": "place", "type_label": "Fundort", "category": "Fundstelle", "items": 51, "desc": "Archäologische Befunde und Altfunde bei Sankt Stefan", "color": "#2D6A4F", "icon": "fa-location-dot"},
        {"id": "plc_noricum", "arche_id": "1756731", "label": "Noricum", "type": "place", "type_label": "Historische Region", "category": "Römische Provinz", "items": 0, "desc": "Historischer antiker Kulturraum Noricum", "color": "#2D6A4F", "icon": "fa-globe"},
        {"id": "plc_kaernten", "arche_id": "138176", "label": "Kärnten / Carinthia", "type": "place", "type_label": "Geographische Region", "category": "Bundesland", "items": 0, "desc": "Geographischer Rahmen im heutigen Österreich", "color": "#2D6A4F", "icon": "fa-earth-europe"}
    ]
    for pl in places:
        nodes.append({"data": pl})

    # Spatial edges
    add_edge({"id": "edge_spat_root", "source": "iuenna_root", "target": "plc_jauntal", "label": "hasSpatialCoverage", "predicate": "schema:hasSpatialCoverage"})
    add_edge({"id": "edge_spat_hb", "source": "col_1792212", "target": "plc_hemmaberg", "label": "hasSpatialCoverage", "predicate": "schema:hasSpatialCoverage"})
    add_edge({"id": "edge_spat_jau", "source": "col_1792303", "target": "plc_jaunstein", "label": "hasSpatialCoverage", "predicate": "schema:hasSpatialCoverage"})
    add_edge({"id": "edge_spat_glo", "source": "col_1792169", "target": "plc_globasnitz", "label": "hasSpatialCoverage", "predicate": "schema:hasSpatialCoverage"})
    add_edge({"id": "edge_spat_ste", "source": "col_1792411", "target": "plc_st_stefan", "label": "hasSpatialCoverage", "predicate": "schema:hasSpatialCoverage"})

    add_edge({"id": "edge_hb_in_jau", "source": "plc_hemmaberg", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"})
    add_edge({"id": "edge_jau_in_jau", "source": "plc_jaunstein", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"})
    add_edge({"id": "edge_glo_in_jau", "source": "plc_globasnitz", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"})
    add_edge({"id": "edge_ste_in_jau", "source": "plc_st_stefan", "target": "plc_jauntal", "label": "locatedIn", "predicate": "schema:containedInPlace"})
    add_edge({"id": "edge_jau_in_ktn", "source": "plc_jauntal", "target": "plc_kaernten", "label": "locatedIn", "predicate": "schema:containedInPlace"})
    add_edge({"id": "edge_jau_in_nor", "source": "plc_jauntal", "target": "plc_noricum", "label": "locatedIn", "predicate": "schema:containedInPlace"})

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
            "total_persons": len(persons),
            "total_organisations": len(organisations),
            "total_publications": len(publications),
            "total_items": 20788,
            "total_resources": 20555,
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
        json.dump(graph_payload, f, indent=2, ensure_ascii=False)

    print(f"[✓] Knowledge Graph successfully generated: {out_file}")
    print(f"[✓] Summary: {len(nodes)} Nodes, {len(edges)} Edges | Collections: {len(collections)} | Persons: {len(persons)} | Orgs: {len(organisations)} | Pubs: {len(publications)}")
    return graph_payload

if __name__ == "__main__":
    build_graph()
