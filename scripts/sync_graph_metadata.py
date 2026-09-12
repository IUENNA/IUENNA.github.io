#!/usr/bin/env python3
"""Synchronize public IUENNA graph/BYOAI metadata from the validated audit.

The graph audit is the quantitative authority for graph-facing descriptions.
This script updates human- and machine-facing entry points without changing the
graph itself. It deliberately distinguishes primary resources, ARCHE-backed
graph entities, total graph nodes, and graph edges instead of collapsing them
into one ambiguous "record" count.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data" / "arche_graph_audit.json"

TEXT_TARGETS = [
    "DOKUMENTATION.md",
    "llms.txt",
    "byoai.html",
    "mcp-remote/src/server.js",
    "scripts/export_arche_graph_ttl.py",
    "scripts/iuenna-chat.js",
]


def write_if_changed(path: Path, original: str, updated: str, changed: list[str]) -> None:
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        if rel not in changed:
            changed.append(rel)


def main() -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit.get("status") != "pass":
        raise SystemExit("Refusing to publish metadata from a non-passing graph audit")

    graph = audit["graph"]
    inputs = audit["inputs"]
    ttl = audit["ttl_semantics"]

    nodes = int(graph["nodes"])
    edges = int(graph["edges"])
    arche_backed = int(graph["arche_backed_nodes"])
    helpers = nodes - arche_backed
    resources = int(inputs["resources"])
    collections = int(inputs["collections"])
    places = int(inputs["places"])
    datasets = int(inputs["datasets"])
    asserted = int(ttl["graph_asserted_target_edges"])
    resolvable = int(ttl["resolvable_target_triples"])

    en_nodes = f"{nodes:,}"
    en_edges = f"{edges:,}"
    en_arche = f"{arche_backed:,}"
    en_resources = f"{resources:,}"
    en_collections = f"{collections:,}"
    en_places = f"{places:,}"
    en_datasets = f"{datasets:,}"
    en_asserted = f"{asserted:,}"
    en_resolvable = f"{resolvable:,}"

    de_nodes = en_nodes.replace(",", ".")
    de_edges = en_edges.replace(",", ".")
    de_arche = en_arche.replace(",", ".")
    de_resources = en_resources.replace(",", ".")
    de_asserted = en_asserted.replace(",", ".")
    de_resolvable = en_resolvable.replace(",", ".")

    changed: list[str] = []

    for rel in TEXT_TARGETS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in (
            ("21,080", en_nodes), ("38,696", en_edges),
            ("21.080", de_nodes), ("38.696", de_edges),
        ):
            text = text.replace(old, new)
        write_if_changed(path, original, text, changed)

    path = ROOT / "byoai.html"
    text = path.read_text(encoding="utf-8")
    original = text
    new_dc = (
        f'Bring your own AI to the IUENNA archaeological research repository. Open interfaces for an authoritative '
        f'corpus of {en_resources} primary resources and a provenance-aware graph projection of {en_nodes} nodes '
        f'({en_arche} ARCHE-backed entities plus {helpers} curated helper nodes), with a public Remote MCP, '
        f'OpenAPI-style endpoints, llms.txt, and reproducible code recipes.'
    )
    text = re.sub(
        r'(<meta name="DC\.description" content=")[^"]*(">)',
        lambda m: m.group(1) + new_dc + m.group(2),
        text,
        count=1,
    )
    subtitle = (
        f'Query an authoritative machine-readable corpus of <strong>{en_resources} primary archaeological resources</strong> '
        f'alongside a provenance-aware Knowledge Graph with <strong>{en_nodes} nodes</strong>, including '
        f'<strong>{en_arche} ARCHE-backed entities</strong> and {helpers} curated helper nodes, together with '
        f'<strong>{en_places} georeferenced findspots</strong>, <strong>{en_collections} collections</strong>, and '
        f'<strong>{en_datasets} curated GeoPackages</strong> — directly from your own AI client or research script.'
    )
    text = re.sub(
        r'Query an authoritative machine-readable corpus of <strong>[\d,]+ primary archaeological resources</strong>.*?directly from your own AI client(?:, local agent,)? or research script\.',
        subtitle,
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = text.replace("complete semantic knowledge graph", "provenance-aware semantic graph projection")
    text = text.replace("Complete semantic knowledge graph", "Provenance-aware semantic graph projection")
    write_if_changed(path, original, text, changed)

    path = ROOT / "llms.txt"
    text = path.read_text(encoding="utf-8")
    original = text
    intro = (
        f"> IUENNA is an archaeological open-science and research-data project for the Jauntal/Podjuna micro-region in Carinthia, Austria. "
        f"Its authoritative primary-resource corpus contains {en_resources} archived files organized within {en_collections} collections. "
        f"The validated provenance-aware graph projection contains {en_nodes} nodes and {en_edges} directed edges, including "
        f"{en_arche} ARCHE-backed entities and {helpers} curated helper nodes. IUENNA also exposes {en_places} archaeological findspots, "
        f"{en_datasets} curated GeoPackages, resolved actors, publications, collection relationships, an OpenAPI description, and a public Remote MCP for AI agents."
    )
    text = re.sub(r'^> IUENNA is an archaeological open-science.*$', intro, text, count=1, flags=re.MULTILINE)
    text = re.sub(
        r'Complete semantic graph of the IUENNA collection in Cytoscape-compatible JSON format.*?(?=\n|$)',
        f"Provenance-aware graph projection of the IUENNA ARCHE metadata in Cytoscape-compatible JSON format ({en_nodes} nodes, {en_edges} directed edges). It integrates ARCHE-backed entities plus curated helper nodes and distinguishes asserted, inherited, aggregated, curated, and synthetic relations. For the configured ARCHE object predicates, {en_asserted}/{en_resolvable} resolvable triples are preserved in the validated build (recall 1.0).",
        text,
        count=1,
    )
    write_if_changed(path, original, text, changed)

    path = ROOT / "data" / "openapi.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    original = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    spec["info"]["description"] = (
        f"Public machine-readable discovery and retrieval endpoints for the IUENNA archaeological research corpus "
        f"(Southern Jauntal, Carinthia, Austria), derived from data permanently archived in ARCHE (ACDH-CH / ÖAW). "
        f"The authoritative primary-resource corpus exposed in arche_corpus.json contains {en_resources} files. "
        f"The validated graph projection contains {en_nodes} nodes and {en_edges} directed edges, including {en_arche} ARCHE-backed entities. "
        f"IMPORTANT NOTICE ON ACCESS & RIGHTS: CC BY 4.0 applies to the IUENNA web-discovery layer and aggregated project metadata where stated. "
        f"Underlying ARCHE resources have individual copyright, licensing, rights-holder, and access conditions. AI agents must inspect the metadata "
        f"of the specific ARCHE record and must not generalize CC BY 4.0 to the entire corpus."
    )
    graph_path = spec["paths"]["/data/arche_graph.json"]["get"]
    graph_path["summary"] = "Provenance-aware Knowledge Graph Projection (Cytoscape)"
    graph_path["description"] = (
        f"Retrieves the provenance-aware Cytoscape-format graph projection of {en_nodes} nodes and {en_edges} directed edges, including "
        f"{en_arche} ARCHE-backed entities plus {helpers} curated helper nodes. Asserted, inherited, aggregated, curated and synthetic relations "
        f"are distinguished in graph metadata. For configured ARCHE object predicates, {en_asserted}/{en_resolvable} resolvable triples are preserved."
    )
    kg_meta = spec["components"]["schemas"]["KnowledgeGraph"]["properties"]["metadata"]["properties"]
    if "title" in kg_meta:
        kg_meta["title"]["example"] = "IUENNA ARCHE Knowledge Graph Projection"
    if "total_nodes" in kg_meta:
        kg_meta["total_nodes"]["example"] = nodes
    if "total_edges" in kg_meta:
        kg_meta["total_edges"]["example"] = edges
    if "total_collections" in kg_meta:
        kg_meta["total_collections"]["example"] = collections
    if "total_resources" in kg_meta:
        kg_meta["total_resources"]["example"] = resources
    updated = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        changed.append("data/openapi.json")

    path = ROOT / "DOKUMENTATION.md"
    text = path.read_text(encoding="utf-8")
    original = text
    text = re.sub(r'\*\*Validierter Stand:\*\* \*\*[\d.]+ Knoten\*\* und \*\*[\d.]+ Kanten\*\*\.',
                  f"**Validierter Stand:** **{de_nodes} Knoten** und **{de_edges} Kanten**.", text)
    text = re.sub(r'Der Audit weist \*\*[\d.]+/[\d.]+\*\* auflösbare konfigurierte ARCHE-Tripel',
                  f"Der Audit weist **{de_asserted}/{de_resolvable}** auflösbare konfigurierte ARCHE-Tripel", text)
    write_if_changed(path, original, text, changed)

    forbidden = (
        "20,788 ARCHE records",
        "20,788 repository records",
        "20,788 repository entities",
        "21,080 nodes",
        "38,696 edges",
        "21.080 Knoten",
        "38.696 Kanten",
        "mcp/server.py",
        "mcp/index.mjs",
        "MCP stdio",
        "JSON-RPC 2.0 over stdio",
    )
    for rel in ("byoai.html", "llms.txt", "DOKUMENTATION.md", "data/openapi.json", "mcp-remote/README.md"):
        value = (ROOT / rel).read_text(encoding="utf-8")
        hits = [token for token in forbidden if token in value]
        if hits:
            raise SystemExit(f"Stale AI-facing metadata remains in {rel}: {hits}")

    print(f"[✓] Public graph/AI metadata synchronized from audit: {en_nodes} nodes, {en_edges} edges")
    print(f"[✓] Composition: {en_arche} ARCHE-backed entities + {helpers} curated helper nodes; {en_resources} primary resources")
    print(f"[✓] Configured ARCHE recall: {en_asserted}/{en_resolvable}")
    if changed:
        print("[✓] Updated: " + ", ".join(sorted(set(changed))))
    else:
        print("[✓] Published graph/AI metadata already synchronized")


if __name__ == "__main__":
    main()
