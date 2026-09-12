#!/usr/bin/env python3
"""Make the layout runtime refresh its preset cache after canonical graph reloads."""
from __future__ import annotations

from pathlib import Path

TARGET = Path("graph/layouts.js")

RESET_FN = '''\n    function resetPresetPositions() {\n        presetPositions = null;\n        capturePresetPositions();\n    }\n'''

EVENT_HOOK = '''\n    window.addEventListener("iuenna:canonical-graph-loaded", () => {\n        resetPresetPositions();\n    });\n'''


def patch(text: str) -> str:
    if "function resetPresetPositions()" not in text:
        marker = "\n    function restorePreset() {"
        if marker not in text:
            raise RuntimeError("Could not find restorePreset() insertion point")
        text = text.replace(marker, RESET_FN + marker, 1)

    export_old = '''            restorePreset,\n            capturePresetPositions\n'''
    export_new = '''            restorePreset,\n            capturePresetPositions,\n            resetPresetPositions\n'''
    if "resetPresetPositions\n        };" not in text:
        if export_old not in text:
            raise RuntimeError("Could not find IUENNAGraphLayouts export block")
        text = text.replace(export_old, export_new, 1)

    if 'window.addEventListener("iuenna:canonical-graph-loaded"' not in text:
        marker = "\n    install();\n})();"
        if marker not in text:
            raise RuntimeError("Could not find layout runtime install tail")
        text = text.replace(marker, EVENT_HOOK + marker, 1)

    return text


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    updated = patch(text)
    if updated != text:
        TARGET.write_text(updated, encoding="utf-8")
        print(f"[✓] {TARGET}: canonical graph preset refresh hook added")
    else:
        print(f"[=] {TARGET}: preset refresh hook already present")


if __name__ == "__main__":
    main()
