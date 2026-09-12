#!/usr/bin/env python3
"""Synchronize published IUENNA graph counts/wording with the validated graph audit.

This keeps human- and machine-facing descriptions aligned with
``data/arche_graph_audit.json`` after authoritative ARCHE rebuilds.  It does
not alter the graph itself; it only updates documentation, API descriptions,
and tool metadata that would otherwise hard-code stale counts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data" / "arche_graph_audit.json"

TEXT_TARGETS = [
    "DOKUMENTATION.md",
    "llms.txt",
    "byoai.html",
    "data/openapi.json",
    "mcp/index.mjs",
    "mcp/server.py",
    "scripts/export_arche_graph_ttl.py",
    "scripts/iuenna-chat.js",
]


def replace(text: str, old: str, new: str) -> str:
    return text.replace(old, new)


def main() -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit.get("status") != "pass":
        raise SystemExit("Refusing to publish graph metadata from a non-passing audit")

    graph = audit["graph"]
    ttl = audit["ttl_semantics"]
    nodes = int(graph["nodes"])
    edges = int(graph["edges"])
    asserted = int(ttl["graph_asserted_target_edges"])
    resolvable = int(ttl["resolvable_target_triples"])

    en_nodes = f"{nodes:,}"
    en_edges = f"{edges:,}"
    de_nodes = en_nodes.replace(",", ".")
    de_edges = en_edges.replace(",", ".")
    en_asserted = f"{asserted:,}"
    de_asserted = en_asserted.replace(",", ".")
    en_resolvable = f"{resolvable:,}"
    de_resolvable = en_resolvable.replace(",", ".")

    changed: list[str] = []

    # Broad count synchronization, deliberately limited to explanatory source files.
    for rel in TEXT_TARGETS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        original = text
        text = replace(text, "21,080", en_nodes)
        text = replace(text, "38,696", en_edges)
        text = replace(text, "21.080", de_nodes)
        text = replace(text, "38.696", de_edges)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(rel)

    # Publication wording: graph projection, not a lossless RDF replacement.
    path = ROOT / "llms.txt"
    text = path.read_text(encoding="utf-8")
    original = text
    text = replace(
        text,
        f"Complete semantic graph of the IUENNA collection in Cytoscape-compatible JSON format ({en_nodes} nodes, {en_edges} directed edges), encompassing collections, datasets, resources, places, persons, organizations, publications, epochs, and subjects linked by formal ARCHE ontology predicates (`isPartOf`, `hasSpatialCoverage`, `hasCreator`, `hasAuthor`, `documents`, `isMemberOf`, `hasContributor`, etc.).",
        f"Provenance-aware graph projection of the IUENNA ARCHE metadata in Cytoscape-compatible JSON format ({en_nodes} nodes, {en_edges} directed edges). It integrates ARCHE-backed entities plus curated helper nodes and distinguishes asserted, inherited, aggregated, curated, and synthetic relations. For the configured ARCHE object predicates, {en_asserted}/{en_resolvable} resolvable triples are preserved in the validated build (recall 1.0).",
    )
    if text != original:
        path.write_text(text, encoding="utf-8")
        if "llms.txt" not in changed:
            changed.append("llms.txt")

    # OpenAPI description: avoid the old "complete semantic graph" overclaim.
    path = ROOT / "data" / "openapi.json"
    text = path.read_text(encoding="utf-8")
    original = text
    text = replace(
        text,
        f"Retrieves the complete Cytoscape-format semantic knowledge graph of {en_nodes} nodes and {en_edges} directed edges connecting collections, datasets, findspots, actors, institutions, publications, and primary archived resources across the IUENNA micro-region.",
        f"Retrieves the provenance-aware Cytoscape-format graph projection of {en_nodes} nodes and {en_edges} directed edges connecting ARCHE-backed collections, resources, datasets, places, actors, institutions and publications together with curated helper nodes. Asserted, inherited, aggregated, curated and synthetic relations are distinguished in the graph metadata.",
    )
    if text != original:
        path.write_text(text, encoding="utf-8")
        if "data/openapi.json" not in changed:
            changed.append("data/openapi.json")

    # Main documentation: semantic scope, canonical dataset/resource identity and audit.
    path = ROOT / "DOKUMENTATION.md"
    text = path.read_text(encoding="utf-8")
    original = text
    text = replace(text, "Parst in 1,2 Sekunden die 54 MB TTL-Rohdaten.", "Parst den reproduzierbar aus ARCHE bezogenen TTL-Vollbestand (ca. 54,12 MB).")
    text = replace(text, "`data/arche_corpus.json` (17,4 MB)", "`data/arche_corpus.json` (ca. 29,66 MB im validierten Rebuild vom 12.09.2026)")
    text = replace(
        text,
        "Erstellt das Cytoscape-Graphmodell mit vollständiger semantischer Kantenmodellierung (`isPartOf`, `hasCreator`, `hasContributor`, `hasAuthor`, `documents`, `isMemberOf`, `hasSpatialCoverage`).",
        "Erstellt eine provenance-erhaltende Cytoscape-Graphprojektion. Die konfigurierten ARCHE-Objektprädikate werden nach dem Aufbau aller kanonischen Knoten in einem zweiten Pass aufgelöst; direkte, geerbte, aggregierte, kuratierte und synthetische Relationen bleiben unterscheidbar. Der Build erzeugt zusätzlich `data/arche_graph_audit.json`.",
    )
    text = replace(
        text,
        "  - **Ergebnis:** **219 von 219 Fundorten vollständig vernetzt (0 isolierte Orte)**.",
        "  - **Ergebnis:** Alle **219 Fundorte** sind als eigenständige Graphknoten vertreten. Direkte ARCHE-Raumbezüge werden von aggregierten bzw. synthetischen Navigationsbeziehungen provenance-seitig unterschieden; synthetische Navigation wird nicht als `hasSpatialCoverage` ausgegeben.",
    )
    text = replace(
        text,
        "* **Knoten-ID:** `dts_1804081`",
        "* **Kanonische Graph-Knoten-ID:** `res_1804081` (Rollen: `resource`, `dataset`; die kuratierte Dataset-Quelle führt weiterhin `dts_1804081` als Quell-ID).",
    )
    text = replace(text, "Im Weitwinkel-Überblick (35.597 Kanten)", f"Im Weitwinkel-Überblick ({de_edges} Kanten)")
    text = replace(text, "**Vollständige semantische ARCHE-Relationen & Canvas-Sichtbarkeit bei Selektion:**", "**Auditierte ARCHE-Relationen, Provenienz & Canvas-Sichtbarkeit bei Selektion:**")
    text = replace(text, "**Lückenlose Prädikaten-Extraktion aus ARCHE-TTL:**", "**Auditierte Prädikaten-Extraktion aus ARCHE-TTL:**")
    text = replace(
        text,
        "Neben den hierarchischen und Urheber-Beziehungen werden nun alle autoritativen ARCHE-Prädikate verarbeitet:",
        "Neben den hierarchischen und Urheber-Beziehungen werden die für IUENNA konfigurierten ARCHE-Objektprädikate verarbeitet:",
    )
    old_total = f"**Gesamtzahl:** Anstieg von 35.597 auf **{de_edges} semantische Kanten** bei {de_nodes} Knoten (z. B. 16 direkte Beziehungen für die Sammlung `col_1792693`)."
    new_total = f"**Validierter Stand:** **{de_nodes} Knoten** und **{de_edges} Kanten**. Der Audit weist **{de_asserted}/{de_resolvable}** auflösbare konfigurierte ARCHE-Tripel als asserted Kanten nach (Recall 1,0); doppelte ARCHE-IDs und dangling edges: 0."
    text = replace(text, old_total, new_total)
    text = replace(
        text,
        f"`arche_graph.json`: {de_nodes} Knoten und {de_edges} Kanten als vollständiger semantischer Wissensgraph.",
        f"`arche_graph.json`: {de_nodes} Knoten und {de_edges} Kanten als provenance-erhaltende Graphprojektion; Details und Invarianten stehen in `arche_graph_audit.json`.",
    )
    text = replace(
        text,
        "6. **Provenienz und Archivstruktur:** `parent_id`, `col`/`col_id`, `spatial_ids` und `documented_ids` nachverfolgen.",
        "6. **Provenienz und Archivstruktur:** `parent_id`, `col`/`col_id`, `spatial_ids_direct`, `spatial_ids_inherited`, `spatial_relation_status` sowie Kanten-`provenance`/`relation_status` nachverfolgen.",
    )
    # Add the reproducible fetcher/audit to the pipeline table if not already documented.
    marker = "| `scripts/parse_arche_full_ttl.py` |"
    fetch_row = "| `scripts/fetch_arche_full_metadata.py` | `data/arche_full_metadata.ttl` | Bezieht den autoritativen IUENNA-Metadatengraphen reproduzierbar aus der ARCHE-Top-Collection `1792170` über `readMode=relatives` im Turtle-Format. |\n"
    if fetch_row.strip() not in text and marker in text:
        text = text.replace(marker, fetch_row + marker, 1)
    audit_marker = "| `scripts/generate_graph_html.py` |"
    audit_row = f"| `data/arche_graph_audit.json` | Build-Audit | Validiert kanonische ARCHE-Identitäten, dangling edges, auflösbare ARCHE-Tripel und prädikatsweisen Recall. Aktueller Stand: {en_asserted}/{en_resolvable} auflösbare Tripel erhalten. |\n"
    if audit_row.strip() not in text and audit_marker in text:
        text = text.replace(audit_marker, audit_row + audit_marker, 1)
    if "arche_graph_audit.json`" not in text.split("## 5. Deployment", 1)[-1]:
        text = text.replace(
            "  - Vollständiger Primärressourcen-Korpus: `https://iuenna.github.io/data/arche_corpus.json`",
            "  - Vollständiger Primärressourcen-Korpus: `https://iuenna.github.io/data/arche_corpus.json`\n  - Graph-Audit: `https://iuenna.github.io/data/arche_graph_audit.json`",
        )
    if text != original:
        path.write_text(text, encoding="utf-8")
        if "DOKUMENTATION.md" not in changed:
            changed.append("DOKUMENTATION.md")

    # Ensure the published HTML does not call the graph "complete" merely because counts match.
    path = ROOT / "byoai.html"
    text = path.read_text(encoding="utf-8")
    original = text
    text = replace(text, "complete semantic knowledge graph", "provenance-aware semantic graph projection")
    text = replace(text, "Complete semantic knowledge graph", "Provenance-aware semantic graph projection")
    if text != original:
        path.write_text(text, encoding="utf-8")
        if "byoai.html" not in changed:
            changed.append("byoai.html")

    # The exporter's count in its docstring is descriptive, not a fixed contract.
    path = ROOT / "scripts" / "export_arche_graph_ttl.py"
    text = path.read_text(encoding="utf-8")
    original = text
    text = replace(
        text,
        f"Serializes data/arche_graph.json ({en_nodes} nodes, {en_edges} edges) into canonical W3C RDF Turtle format.",
        "Serializes the current data/arche_graph.json into W3C RDF Turtle format; graph counts are read at runtime.",
    )
    if text != original:
        path.write_text(text, encoding="utf-8")
        if "scripts/export_arche_graph_ttl.py" not in changed:
            changed.append("scripts/export_arche_graph_ttl.py")

    # Guard against the specific stale public counts that motivated this sync.
    stale = ("21,080", "38,696", "21.080", "38.696")
    for rel in TEXT_TARGETS:
        text = (ROOT / rel).read_text(encoding="utf-8")
        hits = [token for token in stale if token in text]
        if hits:
            raise SystemExit(f"Stale graph counts remain in {rel}: {hits}")

    print(f"[✓] Graph metadata synchronized from audit: {en_nodes} nodes, {en_edges} edges")
    print(f"[✓] Asserted ARCHE recall: {en_asserted}/{en_resolvable}")
    if changed:
        print("[✓] Updated: " + ", ".join(sorted(changed)))
    else:
        print("[✓] Published graph metadata already synchronized")


if __name__ == "__main__":
    main()
