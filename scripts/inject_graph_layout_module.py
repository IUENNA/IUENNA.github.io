#!/usr/bin/env python3
"""Prepare the generated IUENNA graph explorer for the LOD runtimes.

The complete ``data/arche_graph.json`` and ``data/arche_corpus.json`` remain the
authoritative products for BYOAI/MCP and reproducibility. The browser shell is
populated from the graph macro projection plus collection-scoped graph shards;
its corpus catalogue uses a compact discovery index loaded only on demand.

This post-processor removes the historical embedded/full-data browser fetches,
injects the graph/corpus runtimes, and applies conservative visualization
defaults (edge labels hidden; node labels retained).
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

START = "<!-- IUENNA graph runtime: start -->"
END = "<!-- IUENNA graph runtime: end -->"
LEGACY_START = "<!-- IUENNA graph layout runtime: start -->"
LEGACY_END = "<!-- IUENNA graph layout runtime: end -->"
BLOCK = f'''{START}\n<script src="./data-source.js?v=20260912-3"></script>\n<script src="./corpus-data.js?v=20260912-2"></script>\n<script src="./layouts.js?v=20260912-2"></script>\n{END}'''

GRAPH_SHELL = 'let graphData = { elements: { nodes: [], edges: [] }, metadata: { source: "arche_graph_macro.json", authoritative_source: "arche_graph.json", mode: "lod" } };'


def strip_embedded_graph(text: str) -> str:
    pattern = re.compile(
        r"let graphData\s*=\s*.*?;\s*\n\s*let treeData\s*=",
        re.DOTALL,
    )
    replacement = GRAPH_SHELL + "\n        let treeData ="
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1 and GRAPH_SHELL not in text:
        raise RuntimeError("Could not locate embedded graphData assignment")
    return updated


def remove_legacy_graph_fetch(text: str) -> str:
    start_marker = "// Fetch Live Updates if Available"
    end_marker = "// 2. Fetch Complete ARCHE Resource Corpus"
    if start_marker not in text:
        return text
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    replacement = (
        "// Graph visualization is loaded by ./data-source.js in LOD mode.\n"
        "        // The complete authoritative graph is not downloaded into Cytoscape.\n\n"
        "        " + end_marker
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Could not remove legacy graph fetch block")
    return updated


def remove_legacy_corpus_fetch(text: str) -> str:
    """Remove the eager ~30 MiB corpus download and its dependent deep-link block."""
    start_marker = "// 2. Fetch Complete ARCHE Resource Corpus"
    end_marker = "// Immediate URL Parameter handling for Tree Modal, Bookmarks & Collection focus"
    if start_marker not in text:
        return text
    if end_marker not in text:
        raise RuntimeError("Could not locate end of legacy corpus fetch block")
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    replacement = (
        "// Corpus discovery is loaded lazily by ./corpus-data.js.\n"
        "        // data/arche_corpus.json remains authoritative and is not fetched at startup.\n\n"
        "        " + end_marker
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Could not remove legacy corpus fetch block")
    return updated


def apply_visual_defaults(text: str) -> str:
    """Keep node labels on, but hide relation labels by default."""
    text = text.replace("let edgeLabelsVisible = true;", "let edgeLabelsVisible = false;", 1)
    text = text.replace(
        '<button id="btnToggleEdgeLabels" class="tool-btn"',
        '<button id="btnToggleEdgeLabels" class="tool-btn btn-active"',
        1,
    )
    text = text.replace(
        '<span id="btnToggleEdgeLabelsText">Kantentexte verbergen</span>',
        '<span id="btnToggleEdgeLabelsText">Kantentexte einblenden</span>',
        1,
    )
    return text


def inject_runtime(text: str) -> str:
    legacy_pattern = re.compile(
        re.escape(LEGACY_START) + r".*?" + re.escape(LEGACY_END),
        re.DOTALL,
    )
    text = legacy_pattern.sub("", text)

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(BLOCK, text)
    if "</body>" not in text:
        raise RuntimeError("No </body> tag found in generated graph HTML")
    return text.replace("</body>", BLOCK + "\n</body>", 1)


def validate(text: str) -> None:
    if GRAPH_SHELL not in text:
        raise RuntimeError("Generated frontend still contains an embedded graph payload")
    if "Fetch Live Updates if Available" in text:
        raise RuntimeError("Legacy duplicate graph fetch block is still present")
    if 'fetch("../data/arche_corpus.json")' in text or "fetch('../data/arche_corpus.json')" in text:
        raise RuntimeError("Generated frontend still eagerly fetches the authoritative corpus")
    if './data-source.js?v=20260912-3' not in text:
        raise RuntimeError("LOD graph loader was not injected")
    if './corpus-data.js?v=20260912-2' not in text:
        raise RuntimeError("Lazy corpus loader was not injected")
    if './layouts.js?v=20260912-2' not in text:
        raise RuntimeError("Layout runtime was not injected")
    if "let edgeLabelsVisible = false;" not in text:
        raise RuntimeError("Edge labels are not disabled by default")
    if '<span id="btnToggleEdgeLabelsText">Kantentexte einblenden</span>' not in text:
        raise RuntimeError("Edge-label button does not reflect the hidden default")


def inject(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    updated = strip_embedded_graph(text)
    updated = remove_legacy_graph_fetch(updated)
    updated = remove_legacy_corpus_fetch(updated)
    updated = apply_visual_defaults(updated)
    updated = inject_runtime(updated)
    validate(updated)
    changed = updated != text
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="graph/index.html")
    args = parser.parse_args()
    path = Path(args.path)
    changed = inject(path)
    print(
        f"[{'✓' if changed else '='}] {path}: graph/corpus LOD runtime "
        f"{'injected/updated' if changed else 'already current'}"
    )


if __name__ == "__main__":
    main()
