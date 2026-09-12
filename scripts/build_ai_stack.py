#!/usr/bin/env python3
"""Build and validate all AI-facing IUENNA artifacts from the canonical graph.

Pipeline:
  arche_graph_audit.json -> AI text normalization -> public metadata sync ->
  iuenna_kb.json -> validation

The canonical graph remains data/arche_graph.json. This script does not build
or mutate that graph; it ensures BYOAI, llms.txt, OpenAPI, MCP descriptions and
the client-side chat knowledge base describe and index the same validated state.
It is also the CI contract that prevents the AI-facing surfaces from drifting
away from the audited graph after future ARCHE refreshes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "arche_graph_audit.json"
GRAPH = ROOT / "data" / "arche_graph.json"
KB = ROOT / "data" / "iuenna_kb.json"


def run(script: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)


def main() -> None:
    run("sync_ai_text_corpus.py")
    run("sync_graph_metadata.py")
    run("build_chat_kb.py")

    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    kb = json.loads(KB.read_text(encoding="utf-8"))

    if audit.get("status") != "pass":
        raise SystemExit("AI stack refuses a non-passing graph audit")

    graph_nodes = int(audit["graph"]["nodes"])
    graph_edges = int(audit["graph"]["edges"])
    arche_backed = int(audit["graph"]["arche_backed_nodes"])
    resources = int(audit["inputs"]["resources"])
    asserted = int(audit["ttl_semantics"]["graph_asserted_target_edges"])
    resolvable = int(audit["ttl_semantics"]["resolvable_target_triples"])

    actual_nodes = len(graph.get("elements", {}).get("nodes", []))
    actual_edges = len(graph.get("elements", {}).get("edges", []))
    kb_entities = kb.get("graph_entities")
    if not isinstance(kb_entities, list):
        raise SystemExit("data/iuenna_kb.json has no graph_entities list")

    assert actual_nodes == graph_nodes, (actual_nodes, graph_nodes)
    assert actual_edges == graph_edges, (actual_edges, graph_edges)
    assert len(kb_entities) == graph_nodes, (len(kb_entities), graph_nodes)

    kb["build_metadata"] = {
        "canonical_graph": "data/arche_graph.json",
        "graph_audit": "data/arche_graph_audit.json",
        "audit_status": "pass",
        "audit_generated_at": audit.get("generated_at"),
        "graph_nodes": graph_nodes,
        "graph_edges": graph_edges,
        "arche_backed_graph_entities": arche_backed,
        "primary_resources": resources,
        "configured_arche_triples_preserved": asserted,
        "configured_arche_triples_resolvable": resolvable,
        "configured_arche_recall": 1.0 if resolvable and asserted == resolvable else (asserted / resolvable if resolvable else None),
    }
    KB.write_text(json.dumps(kb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    public_checks = {
        "byoai.html": [f"{graph_nodes:,}", f"{arche_backed:,}", f"{resources:,}"],
        "llms.txt": [f"{graph_nodes:,}", f"{arche_backed:,}", f"{resources:,}"],
        "data/openapi.json": [f"{graph_nodes:,}", f"{graph_edges:,}"],
        "mcp/server.py": [f"{graph_nodes:,}", f"{graph_edges:,}"],
        "mcp/index.mjs": [f"{graph_nodes:,}", f"{graph_edges:,}"],
    }
    forbidden = (
        "20,788 ARCHE records",
        "20,788 repository records",
        "20,788 repository entities",
        "20,788 digital resources",
        "21,080 nodes",
        "38,696 edges",
    )
    for rel, required in public_checks.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        missing = [token for token in required if token not in text]
        stale = [token for token in forbidden if token in text]
        if missing or stale:
            raise SystemExit(f"AI metadata validation failed for {rel}: missing={missing}, stale={stale}")

    kb_text = KB.read_text(encoding="utf-8")
    stale_kb = [token for token in forbidden if token in kb_text]
    if stale_kb:
        raise SystemExit(f"Stale quantitative claims remain in data/iuenna_kb.json: {stale_kb}")

    print(
        f"[✓] AI stack synchronized: {graph_nodes:,} graph nodes / {graph_edges:,} edges; "
        f"{len(kb_entities):,} KB graph entities; {resources:,} primary resources"
    )


if __name__ == "__main__":
    main()
