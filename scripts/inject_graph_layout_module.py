#!/usr/bin/env python3
"""Inject the standalone IUENNA graph layout runtime into generated HTML.

The graph explorer is generated from scripts/generate_graph_html.py and contains
legacy inline layout listeners. The external runtime is loaded after that script
and intercepts layout/LOD events in capture phase, so the repaired topology-aware
implementation is used without duplicating the complete generated frontend.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

START = "<!-- IUENNA graph layout runtime: start -->"
END = "<!-- IUENNA graph layout runtime: end -->"
BLOCK = f'''{START}\n<script src="./layouts.js?v=20260912-1"></script>\n{END}'''


def inject(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(text):
        updated = pattern.sub(BLOCK, text)
    else:
        if "</body>" not in text:
            raise RuntimeError(f"No </body> tag found in {path}")
        updated = text.replace("</body>", BLOCK + "\n</body>", 1)
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
    print(f"[{'✓' if changed else '='}] {path}: layout runtime {'injected/updated' if changed else 'already current'}")


if __name__ == "__main__":
    main()
