#!/usr/bin/env python3
"""Build a browser-optimized LOD projection from the complete IUENNA graph.

The authoritative graph remains ``data/arche_graph.json`` and is not modified.
For the interactive explorer this script creates:

* ``data/arche_graph_macro.json`` – all structural/non-resource nodes plus only
  edges whose endpoints are both structural;
* ``data/arche_graph_lod_manifest.json`` – shard metadata and a compact reverse
  lookup from resource node -> parent collection;
* ``data/graph_shards/*.json`` – pure resource nodes grouped by their immediate
  ARCHE collection together with all incident semantic edges.

This lets the browser start with the macro network and materialize resource
subgraphs only when a collection is expanded, while BYOAI/MCP continue to use
the complete authoritative graph.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GRAPH_PATH = DATA / "arche_graph.json"
MACRO_PATH = DATA / "arche_graph_macro.json"
MANIFEST_PATH = DATA / "arche_graph_lod_manifest.json"
SHARD_DIR = DATA / "graph_shards"

STRUCTURAL_ROLES = {"collection", "dataset", "person", "organization", "publication", "place"}


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def roles(node: dict) -> set[str]:
    data = node.get("data", {})
    raw = data.get("roles") or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(v) for v in raw if v}


def is_lazy_resource(node: dict) -> bool:
    r = roles(node)
    # Dataset/resource overlaps must stay in the macro graph because they are
    # first-class structural research datasets. Only pure resources are lazy.
    return "resource" in r and not (r & STRUCTURAL_ROLES)


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return value or "unassigned"


def main() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = graph.get("elements", {}).get("nodes", [])
    edges = graph.get("elements", {}).get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise SystemExit("arche_graph.json has no valid Cytoscape elements arrays")

    nodes_by_id = {}
    macro_ids: set[str] = set()
    lazy_ids: set[str] = set()
    collection_ids: set[str] = set()
    collection_by_arche: dict[str, str] = {}

    for node in nodes:
        data = node.get("data", {})
        nid = str(data.get("id") or "")
        if not nid:
            raise SystemExit("Graph contains a node without data.id")
        nodes_by_id[nid] = node
        r = roles(node)
        if is_lazy_resource(node):
            lazy_ids.add(nid)
        else:
            macro_ids.add(nid)
        if "collection" in r or data.get("type") in {"root", "subcollection"} or str(data.get("type", "")).startswith("folder_l"):
            collection_ids.add(nid)
            aid = str(data.get("arche_id") or "")
            if aid:
                collection_by_arche[aid] = nid

    parent_for_resource: dict[str, str] = {}
    for edge in edges:
        d = edge.get("data", {})
        src = str(d.get("source") or "")
        tgt = str(d.get("target") or "")
        if d.get("label") == "isPartOf" and src in lazy_ids and tgt in collection_ids:
            parent_for_resource.setdefault(src, tgt)

    # Fallback to resource node metadata in case a future graph build omits an
    # explicit isPartOf edge for a resource but still carries the parent ID.
    for rid in lazy_ids:
        if rid in parent_for_resource:
            continue
        d = nodes_by_id[rid].get("data", {})
        candidates = [d.get("parent_arche_id"), d.get("col"), d.get("collection_id"), d.get("parent_id")]
        for raw in candidates:
            if raw is None:
                continue
            value = str(raw)
            if value in collection_by_arche:
                parent_for_resource[rid] = collection_by_arche[value]
                break
            prefixed = f"col_{value}"
            if prefixed in collection_ids:
                parent_for_resource[rid] = prefixed
                break

    unresolved = sorted(lazy_ids - set(parent_for_resource))
    if unresolved:
        raise SystemExit(f"LOD build cannot assign {len(unresolved)} pure resources to a collection; first IDs: {unresolved[:10]}")

    macro_nodes = [node for node in nodes if str(node.get("data", {}).get("id")) in macro_ids]
    macro_edges = []
    shard_edges: dict[str, list] = defaultdict(list)
    shard_edge_ids: dict[str, set[str]] = defaultdict(set)

    for edge in edges:
        d = edge.get("data", {})
        src = str(d.get("source") or "")
        tgt = str(d.get("target") or "")
        if src in macro_ids and tgt in macro_ids:
            macro_edges.append(edge)
            continue

        # Store every resource-related edge in the shard of each participating
        # resource. Cross-shard edges may therefore appear in two files; the
        # runtime deduplicates by edge ID and keeps them pending until both
        # endpoints are loaded.
        shard_keys = set()
        if src in lazy_ids:
            shard_keys.add(parent_for_resource[src])
        if tgt in lazy_ids:
            shard_keys.add(parent_for_resource[tgt])
        edge_id = str(d.get("id") or f"{src}|{d.get('label','')}|{tgt}")
        for key in shard_keys:
            if edge_id not in shard_edge_ids[key]:
                shard_edge_ids[key].add(edge_id)
                shard_edges[key].append(edge)

    resources_by_collection: dict[str, list] = defaultdict(list)
    for rid, parent in parent_for_resource.items():
        resources_by_collection[parent].append(nodes_by_id[rid])

    SHARD_DIR.mkdir(parents=True, exist_ok=True)
    for old in SHARD_DIR.glob("*.json"):
        old.unlink()

    manifest_collections = {}
    resource_to_collection = {}
    total_shard_bytes = 0

    for collection_id in sorted(resources_by_collection):
        resource_nodes = sorted(resources_by_collection[collection_id], key=lambda n: str(n.get("data", {}).get("id", "")))
        for node in resource_nodes:
            resource_to_collection[str(node["data"]["id"])] = collection_id
        filename = f"{safe_name(collection_id)}.json"
        shard = {
            "metadata": {
                "mode": "resource-shard",
                "collection_id": collection_id,
                "resource_count": len(resource_nodes),
                "edge_count": len(shard_edges.get(collection_id, [])),
                "authoritative_graph": "../arche_graph.json",
            },
            "elements": {
                "nodes": resource_nodes,
                "edges": shard_edges.get(collection_id, []),
            },
        }
        path = SHARD_DIR / filename
        dump_json(path, shard)
        total_shard_bytes += path.stat().st_size
        collection_node = nodes_by_id.get(collection_id, {}).get("data", {})
        manifest_collections[collection_id] = {
            "url": f"graph_shards/{filename}",
            "arche_id": collection_node.get("arche_id"),
            "label": collection_node.get("label") or collection_node.get("title") or collection_id,
            "resource_count": len(resource_nodes),
            "edge_count": len(shard_edges.get(collection_id, [])),
        }

    source_meta = dict(graph.get("metadata") or {})
    full_node_count = len(nodes)
    full_edge_count = len(edges)
    source_meta["lod"] = {
        "mode": "macro-plus-resource-shards",
        "authoritative_graph": "arche_graph.json",
        "macro_nodes": len(macro_nodes),
        "macro_edges": len(macro_edges),
        "lazy_resource_nodes": len(lazy_ids),
        "full_nodes": full_node_count,
        "full_edges": full_edge_count,
        "shards": len(manifest_collections),
    }
    macro = {"metadata": source_meta, "elements": {"nodes": macro_nodes, "edges": macro_edges}}
    dump_json(MACRO_PATH, macro)

    manifest = {
        "version": 1,
        "mode": "macro-plus-resource-shards",
        "authoritative_graph": "arche_graph.json",
        "macro_graph": "arche_graph_macro.json",
        "full_nodes": full_node_count,
        "full_edges": full_edge_count,
        "macro_nodes": len(macro_nodes),
        "macro_edges": len(macro_edges),
        "lazy_resource_nodes": len(lazy_ids),
        "shard_count": len(manifest_collections),
        "collections": manifest_collections,
        "resource_to_collection": resource_to_collection,
    }
    dump_json(MANIFEST_PATH, manifest)

    macro_size = MACRO_PATH.stat().st_size
    manifest_size = MANIFEST_PATH.stat().st_size
    print(
        f"[✓] LOD graph built: {len(macro_nodes):,} macro nodes / {len(macro_edges):,} macro edges; "
        f"{len(lazy_ids):,} lazy resources in {len(manifest_collections):,} shards"
    )
    print(
        f"[✓] Initial graph payload: {macro_size / 1024 / 1024:.2f} MiB + "
        f"manifest {manifest_size / 1024 / 1024:.2f} MiB; shards total {total_shard_bytes / 1024 / 1024:.2f} MiB"
    )


if __name__ == "__main__":
    main()
