#!/usr/bin/env python3
"""Compact generated IUENNA graph JSON without discarding semantic information.

The full in-memory graph keeps verbose edge provenance for auditing. For the
published JSON representation we remove values that are deterministic or
redundantly repeated on hundreds of thousands of edges:

* schema predicates are reconstructed as SCHEMA_BASE + edge.label;
* semantic=true is the default and therefore omitted;
* provenance_sources is omitted when it contains only edge.provenance;
* asserted/curated derivation arrays are redundant with provenance/status;
* for inherited/aggregated/synthetic edges only non-default derivation details
  are retained.

The encoding rules are written into graph metadata so the compact form is
self-describing and semantically reversible.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

SCHEMA_BASE = "https://vocabs.acdh.oeaw.ac.at/schema#"


def compact_graph(graph: dict) -> dict:
    edges = graph.get("elements", {}).get("edges", [])
    for edge in edges:
        data = edge.get("data", {})
        label = str(data.get("label", ""))
        if data.get("predicate") == SCHEMA_BASE + label:
            data.pop("predicate", None)
        if data.get("semantic") is True:
            data.pop("semantic", None)
        if data.get("provenance_sources") == [data.get("provenance")]:
            data.pop("provenance_sources", None)

        status = data.get("relation_status")
        derivations = data.get("derivations", [])
        if status in {"asserted", "curated"}:
            data.pop("derivations", None)
        elif derivations:
            slim = []
            for derivation in derivations:
                reduced = {
                    key: value
                    for key, value in derivation.items()
                    if key not in {"provenance", "relation_status", "source"}
                }
                if reduced and reduced not in slim:
                    slim.append(reduced)
            if slim:
                data["derivations"] = slim
            else:
                data.pop("derivations", None)

    graph.setdefault("metadata", {})["edge_encoding"] = {
        "schema_predicate_base": SCHEMA_BASE,
        "implicit_predicate_rule": "If edge.data.predicate is absent, predicate = schema_predicate_base + edge.data.label.",
        "implicit_semantic_rule": "If edge.data.semantic is absent, semantic = true.",
        "provenance_rule": "edge.data.provenance and edge.data.relation_status are canonical; provenance_sources is emitted only for multiple sources.",
        "derivation_rule": "Verbose derivations are retained only for inherited, aggregated, or synthetic relations where they add non-default information."
    }
    return graph


def write_atomic(path: Path, graph: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    try:
        with open(tmp_name, "w", encoding="utf-8") as fh:
            json.dump(graph, fh, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="data/arche_graph.json")
    args = parser.parse_args()
    path = Path(args.path)
    before = path.stat().st_size
    graph = json.loads(path.read_text(encoding="utf-8"))
    compact_graph(graph)
    write_atomic(path, graph)
    after = path.stat().st_size
    print(f"[✓] Compacted {path}: {before / 1024 / 1024:.2f} MiB -> {after / 1024 / 1024:.2f} MiB")


if __name__ == "__main__":
    main()
