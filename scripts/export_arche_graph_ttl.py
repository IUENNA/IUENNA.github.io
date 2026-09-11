#!/usr/bin/env python3
"""
export_arche_graph_ttl.py
Serializes data/arche_graph.json (21,080 nodes, 38,696 edges) into canonical W3C RDF Turtle format.
Zero external dependencies.
"""

import os
import sys
import json
import time

def escape_ttl_literal(val: str) -> str:
    """Escapes special characters in Turtle string literals."""
    if not val:
        return ""
    val = val.replace("\\", "\\\\")
    val = val.replace('"', '\\"')
    val = val.replace("\n", "\\n")
    val = val.replace("\r", "\\r")
    val = val.replace("\t", "\\t")
    return val

def resolve_node_uri(nd: dict) -> str:
    """Determines canonical URI for an entity node."""
    uri = nd.get("uri")
    if uri and uri.startswith("http"):
        return f"<{uri}>"
    arche_id = nd.get("arche_id")
    if arche_id and str(arche_id).strip():
        return f"<https://arche.acdh.oeaw.ac.at/api/{arche_id}>"
    pid = nd.get("pid")
    if pid and pid.startswith("http"):
        return f"<{pid}>"
    nid = nd.get("id", "unknown")
    return f"<https://iuenna.github.io/entity/{nid}>"

def resolve_predicate(pred: str) -> str:
    """Maps predicate string to Turtle prefix or URI."""
    if not pred:
        return "arche:related"
    if pred.startswith("https://vocabs.acdh.oeaw.ac.at/schema#"):
        return f"arche:{pred.split('#')[-1]}"
    if pred.startswith("arche:"):
        return f"arche:{pred.split('arche:')[-1]}"
    if pred.startswith("schema:"):
        return f"schema:{pred.split('schema:')[-1]}"
    if pred.startswith("http://") or pred.startswith("https://"):
        return f"<{pred}>"
    return f"arche:{pred}"

def map_node_type(ntype: str) -> str:
    """Maps node internal type to RDF ontology class."""
    if ntype in ("root", "subcollection", "folder_l2", "folder_l3", "folder_l4", "folder_l5", "folder_l6"):
        return "arche:Collection"
    if ntype == "dataset":
        return "arche:Dataset"
    if ntype == "resource":
        return "arche:Resource"
    if ntype == "person":
        return "arche:Person"
    if ntype == "organization":
        return "arche:Organisation"
    if ntype == "publication":
        return "arche:Publication"
    if ntype == "place":
        return "arche:Place"
    if ntype == "epoch":
        return "schema:TemporalCoverage"
    if ntype == "subject":
        return "schema:DefinedTerm"
    if ntype == "license":
        return "schema:CreativeWork"
    return "rdfs:Resource"

def export_ttl(json_path: str, ttl_path: str):
    start_time = time.time()
    print(f"[*] Reading graph from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("elements", {}).get("nodes", [])
    edges = data.get("elements", {}).get("edges", [])
    metadata = data.get("metadata", {})

    print(f"[*] Found {len(nodes):,} nodes and {len(edges):,} edges.")

    # Build node_id -> URI map
    id_to_uri = {}
    for n in nodes:
        nd = n.get("data", {})
        id_to_uri[nd.get("id")] = resolve_node_uri(nd)

    print(f"[*] Serializing to Turtle {ttl_path}...")
    with open(ttl_path, "w", encoding="utf-8") as out:
        # 1. Prefixes
        out.write("### IUENNA Knowledge Graph - Canonical RDF Turtle Export ###\n")
        out.write(f"### Generated from ARCHE metadata snapshot: {metadata.get('generated_at', '2026-09-10')} ###\n")
        out.write(f"### Total Nodes: {len(nodes):,} | Total Edges: {len(edges):,} ###\n\n")

        out.write("@prefix arche: <https://vocabs.acdh.oeaw.ac.at/schema#> .\n")
        out.write("@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .\n")
        out.write("@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
        out.write("@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .\n")
        out.write("@prefix schema: <https://schema.org/> .\n")
        out.write("@prefix dcterms: <http://purl.org/dc/terms/> .\n")
        out.write("@prefix iuenna: <https://iuenna.github.io/entity/> .\n\n")

        # 2. Node triples
        for n in nodes:
            nd = n.get("data", {})
            sub = id_to_uri.get(nd.get("id"))
            if not sub:
                continue

            lines = []
            rdf_type = map_node_type(nd.get("type", ""))
            lines.append(f"    a {rdf_type}")

            label = nd.get("label") or nd.get("title")
            if label:
                lines.append(f'    rdfs:label "{escape_ttl_literal(label)}"@de')

            title = nd.get("title")
            if title and title != label:
                lines.append(f'    schema:name "{escape_ttl_literal(title)}"@de')

            pid = nd.get("pid")
            if pid and pid.startswith("http"):
                lines.append(f"    arche:hasPid <{pid}>")

            arche_id = nd.get("arche_id")
            if arche_id:
                lines.append(f'    arche:hasIdentifier "{escape_ttl_literal(str(arche_id))}"')

            orcid = nd.get("orcid")
            if orcid:
                lines.append(f"    schema:identifier <https://orcid.org/{orcid.strip()}>")

            ror = nd.get("ror")
            if ror:
                lines.append(f"    schema:identifier <{ror.strip()}>")

            wikidata = nd.get("wikidata")
            if wikidata:
                lines.append(f"    schema:sameAs <{wikidata.strip()}>")

            geonames = nd.get("geonames")
            if geonames:
                lines.append(f"    schema:sameAs <{geonames.strip()}>")

            size_bytes = nd.get("size_bytes")
            if size_bytes:
                try:
                    sb = int(size_bytes)
                    lines.append(f'    arche:hasBinarySize "{sb}"^^xsd:long')
                except (ValueError, TypeError):
                    pass

            filename = nd.get("filename")
            if filename:
                lines.append(f'    arche:hasFilename "{escape_ttl_literal(filename)}"')

            out.write(f"{sub}\n" + " ;\n".join(lines) + " .\n\n")

        # 3. Edge triples
        out.write("### Knowledge Graph Relations / Edges ###\n\n")
        for e in edges:
            ed = e.get("data", {})
            src_id = ed.get("source")
            tgt_id = ed.get("target")
            src_uri = id_to_uri.get(src_id)
            tgt_uri = id_to_uri.get(tgt_id)
            if not src_uri or not tgt_uri:
                continue

            pred = resolve_predicate(ed.get("predicate", ed.get("label", "")))
            out.write(f"{src_uri} {pred} {tgt_uri} .\n")

    size_mb = os.path.getsize(ttl_path) / (1024 * 1024)
    elapsed = time.time() - start_time
    print(f"[+] Successfully wrote {ttl_path} ({size_mb:.2f} MB in {elapsed:.2f}s).")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "arche_graph.json")
    ttl_path = os.path.join(base_dir, "data", "arche_graph.ttl")
    export_ttl(json_path, ttl_path)
