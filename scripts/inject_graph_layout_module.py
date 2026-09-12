#!/usr/bin/env python3
"""Prepare the generated IUENNA graph explorer for canonical runtime loading.

The historical generator embedded the full graph JSON directly into graph/index.html
and then fetched data/arche_graph.json a second time without applying it to Cytoscape.
This post-processing step makes data/arche_graph.json the single graph payload used
by the browser, removes the legacy duplicate fetch block, and injects the standalone
canonical loader plus the repaired topology-aware layout runtime.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

START = "<!-- IUENNA graph runtime: start -->"
END = "<!-- IUENNA graph runtime: end -->"
LEGACY_START = "<!-- IUENNA graph layout runtime: start -->"
LEGACY_END = "<!-- IUENNA graph layout runtime: end -->"
BLOCK = f'''{START}\n<script src="./data-source.js?v=20260912-1"></script>\n<script src="./layouts.js?v=20260912-2"></script>\n{END}'''

GRAPH_SHELL = 'let graphData = { elements: { nodes: [], edges: [] }, metadata: { source: "arche_graph.json" } };'


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
        "// Canonical graph payload is loaded and applied by ./data-source.js.\n"
        "        // This avoids the historical second download that updated graphData but not Cytoscape.\n\n"
        "        " + end_marker
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Could not remove legacy graph fetch block")
    return updated


def inject_runtime(text: str) -> str:
    # Remove the earlier one-script layout block if present.
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
    if './data-source.js?v=20260912-1' not in text:
        raise RuntimeError("Canonical graph loader was not injected")
    if './layouts.js?v=20260912-2' not in text:
        raise RuntimeError("Layout runtime was not injected")


def inject(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    updated = strip_embedded_graph(text)
    updated = remove_legacy_graph_fetch(updated)
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
        f"[{'✓' if changed else '='}] {path}: canonical graph runtime "
        f"{'injected/updated' if changed else 'already current'}"
    )


if __name__ == "__main__":
    main()
