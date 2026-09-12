#!/usr/bin/env python3
"""Build a compact browser-only index from the authoritative ARCHE corpus.

``data/arche_corpus.json`` remains the complete authoritative primary-resource
corpus for BYOAI and reproducible downstream processing. The public Remote MCP
uses a separate reproducible query projection; the graph explorer only needs a
small discovery projection for its corpus catalogue,
autocomplete, filters and previews. This script emits that projection as
``data/arche_corpus_browser_index.json``.

The browser index is deliberately non-authoritative: omitted fields remain
available in the authoritative corpus and, for graph interaction, in the
collection-scoped graph shards.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_SOURCE = Path("data/arche_corpus.json")
DEFAULT_OUTPUT = Path("data/arche_corpus_browser_index.json")

# Fields actually consumed by the graph explorer's corpus catalogue/search,
# plus a few cheap identifiers useful for robust deep links.
KEEP_FIELDS = (
    "id",
    "arche_id",
    "title",
    "filename",
    "pid",
    "col",
    "col_id",
    "parent_id",
    "folder",
    "path",
    "place",
    "subjs",
    "date",
    "type",
    "ftype",
    "formatted_size",
    "size_bytes",
)


def compact_resource(resource: dict[str, Any]) -> dict[str, Any]:
    item: dict[str, Any] = {}
    for key in KEEP_FIELDS:
        value = resource.get(key)
        if value is None or value == "" or value == []:
            continue
        item[key] = value

    # Keep the historical frontend aliases stable even if an upstream corpus
    # build omits one of them.
    if "id" not in item and resource.get("arche_id"):
        item["id"] = f"res_{resource['arche_id']}"
    if "arche_id" not in item and isinstance(item.get("id"), str):
        item["arche_id"] = item["id"].removeprefix("res_")
    if "title" not in item:
        item["title"] = resource.get("filename") or resource.get("label") or item.get("id", "Resource")
    if "folder" not in item:
        path = resource.get("path") or []
        if path:
            item["folder"] = path[-1]
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    corpus = json.loads(args.source.read_text(encoding="utf-8"))
    resources = corpus.get("resources", [])
    if not isinstance(resources, list) or not resources:
        raise SystemExit("Authoritative corpus contains no resources")

    compact = [compact_resource(resource) for resource in resources]
    ids = [item.get("id") for item in compact]
    if any(not value for value in ids):
        raise SystemExit("Browser corpus index contains a resource without id")
    if len(set(ids)) != len(ids):
        raise SystemExit("Browser corpus index contains duplicate resource ids")

    source_metadata = corpus.get("metadata") if isinstance(corpus.get("metadata"), dict) else {}
    payload = {
        "metadata": {
            "mode": "browser-discovery-index",
            "authoritative_source": "arche_corpus.json",
            "total_resources": len(compact),
            "fields": list(KEEP_FIELDS),
            "non_authoritative_projection": True,
            "source_generated_at": source_metadata.get("generated_at"),
        },
        "resources": compact,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    source_size = args.source.stat().st_size
    output_size = args.output.stat().st_size
    ratio = output_size / source_size if source_size else 0
    print(
        f"[✓] Browser corpus index: {len(compact):,} resources / "
        f"{output_size / 1024 / 1024:.2f} MiB "
        f"({ratio:.1%} of authoritative corpus)"
    )


if __name__ == "__main__":
    main()
