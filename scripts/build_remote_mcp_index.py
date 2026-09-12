#!/usr/bin/env python3
"""Build the compact, non-authoritative query projection for IUENNA Remote MCP."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

DATA_DIR = Path("data")
DEFAULT_OUTPUT = DATA_DIR / "mcp_remote"
RESOURCE_FIELDS = (
    "arche_id", "title", "filename", "type", "date", "place", "spatial_ids",
    "col", "col_id", "folder", "path", "pid", "description", "formatted_size", "size_bytes",
)
SEARCH_FIELDS = (
    "title", "name", "filename", "description", "breadcrumb", "folder", "folder_code",
    "place", "alternative_title", "pid", "arche_id", "id",
)
SEARCH_LIST_FIELDS = ("path", "subjs", "subjects", "alternative_titles")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def as_list(data: Any, key: str | None = None) -> list[dict[str, Any]]:
    if key and isinstance(data, dict):
        data = data.get(key, {})
    if isinstance(data, dict):
        return [v for v in data.values() if isinstance(v, dict)]
    if isinstance(data, list):
        return [v for v in data if isinstance(v, dict)]
    return []


def norm_id(value: Any) -> str:
    value = str(value or "").strip().lower()
    for prefix in ("place_", "plc_", "dts_", "col_", "pub_", "res_"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


def entity_id(item: dict[str, Any]) -> str:
    return str(item.get("arche_id") or norm_id(item.get("id")))


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE).replace("_", " ")
    return " ".join(text.split())


def fnv_bucket(value: str) -> str:
    h = 0x811C9DC5
    for byte in value.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h & 0xFF:02x}"


def search_tokens(item: dict[str, Any]) -> set[str]:
    values: list[Any] = [item.get(k) for k in SEARCH_FIELDS]
    for key in SEARCH_LIST_FIELDS:
        value = item.get(key)
        values.extend(value if isinstance(value, list) else [value] if value else [])
    return {token for value in values for token in normalize(value).split() if len(token) >= 2}


def resource_row(item: dict[str, Any]) -> list[Any]:
    return [item.get(field) for field in RESOURCE_FIELDS]


def build_descendant_resolver(collections: list[dict[str, Any]]):
    children: dict[str, list[str]] = defaultdict(list)
    for item in collections:
        parent = str(item.get("parent_id") or "")
        if parent:
            children[parent].append(entity_id(item))
    cache: dict[str, set[str]] = {}

    def one(root: str) -> set[str]:
        if root in cache:
            return set(cache[root])
        seen = {root}
        queue = deque([root])
        while queue:
            current = queue.popleft()
            for child in children.get(current, []):
                if child not in seen:
                    seen.add(child)
                    queue.append(child)
        cache[root] = seen
        return set(seen)

    def many(roots: Iterable[str]) -> set[str]:
        out: set[str] = set()
        for root in roots:
            if root:
                out.update(one(str(root)))
        return out

    return many


def prefixed_collection_id(value: str) -> str:
    value = str(value)
    if value == "iuenna_root" or value.startswith("col_"):
        return value
    return f"col_{value}"


def build_indexes(output: Path) -> dict[str, Any]:
    corpus = load_json(DATA_DIR / "arche_corpus.json")
    graph = load_json(DATA_DIR / "arche_graph.json")
    places = as_list(load_json(DATA_DIR / "arche_places.json"))
    datasets = as_list(load_json(DATA_DIR / "arche_datasets.json"))
    collections = as_list(load_json(DATA_DIR / "arche_collections_tree.json"), "collections")
    publications = as_list(load_json(DATA_DIR / "arche_publications.json"))
    resources = as_list(corpus, "resources")
    nodes = [n.get("data", {}) for n in graph.get("elements", {}).get("nodes", []) if isinstance(n, dict)]
    edges = graph.get("elements", {}).get("edges", [])
    if not resources or not nodes:
        raise RuntimeError("Authoritative corpus/graph is empty")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    resource_shards: dict[str, list[list[Any]]] = defaultdict(list)
    resource_to_collection: dict[str, str] = {}
    collection_to_resources: dict[str, list[int]] = defaultdict(list)
    spatial_to_resources: dict[str, list[int]] = defaultdict(list)
    search_postings: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for resource in resources:
        aid = int(str(resource.get("arche_id") or norm_id(resource.get("id"))))
        col_id = str(resource.get("col_id") or (f"col_{resource.get('col')}" if resource.get("col") else "iuenna_root"))
        resource["arche_id"] = str(aid)
        resource["col_id"] = col_id
        resource_shards[col_id].append(resource_row(resource))
        resource_to_collection[str(aid)] = col_id
        collection_to_resources[col_id].append(aid)
        for sid in resource.get("spatial_ids", []) or []:
            spatial_to_resources[str(sid)].append(aid)
        for token in sorted(search_tokens(resource)):
            search_postings[fnv_bucket(token[:2])][token].append(aid)

    for col_id, rows in resource_shards.items():
        write_json(output / "resources" / f"{col_id}.json", {"c": col_id, "r": rows})
    for shard, terms in search_postings.items():
        write_json(output / "search" / f"{shard}.json", {"t": dict(sorted(terms.items()))})
    write_json(output / "resource_to_collection.json", resource_to_collection)
    write_json(output / "collection_to_resources.json", dict(collection_to_resources))
    write_json(output / "spatial_to_resources.json", dict(spatial_to_resources))

    nodes_by_id = {str(n.get("id")): n for n in nodes if n.get("id")}
    graph_by_arche = {str(n.get("arche_id")): n for n in nodes if n.get("arche_id") not in (None, "")}
    aliases: dict[str, list[list[str]]] = defaultdict(list)
    seen_alias: set[tuple[str, str]] = set()
    node_meta: dict[str, dict[str, list[Any]]] = defaultdict(dict)
    adjacency: dict[str, list[list[str]]] = defaultdict(list)
    pred_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for node in nodes:
        nid = str(node.get("id") or "")
        if not nid:
            continue
        label = node.get("label") or node.get("title") or nid
        node_meta[fnv_bucket(nid)][nid] = [
            node.get("arche_id"), label, node.get("type"), node.get("type_label"),
            node.get("pid"), node.get("parent_col"),
        ]
        for alias in (nid, node.get("arche_id"), label, node.get("title"), node.get("filename"), node.get("alternative_title")):
            key = normalize(alias)
            if key and (key, nid) not in seen_alias:
                seen_alias.add((key, nid))
                aliases[fnv_bucket(key[:2])].append([key, nid])

    for edge in edges:
        ed = edge.get("data", {})
        src, tgt = str(ed.get("source") or ""), str(ed.get("target") or "")
        if src not in nodes_by_id or tgt not in nodes_by_id:
            continue
        predicate = str(ed.get("label") or "")
        adjacency[src].append(["o", predicate, tgt])
        adjacency[tgt].append(["i", predicate, src])
        pred_counts[src][predicate] += 1
        pred_counts[tgt][predicate] += 1

    graph_shards: dict[str, dict[str, Any]] = defaultdict(dict)
    for nid in nodes_by_id:
        graph_shards[fnv_bucket(nid)][nid] = {"e": adjacency.get(nid, []), "p": dict(pred_counts.get(nid, {}))}
    for shard, rows in aliases.items():
        rows.sort(key=lambda row: (row[0], row[1]))
        write_json(output / "aliases" / f"{shard}.json", {"a": rows})
    for shard, entries in node_meta.items():
        write_json(output / "nodes" / f"{shard}.json", {"n": entries})
    for shard, entries in graph_shards.items():
        write_json(output / "graph" / f"{shard}.json", {"n": entries})

    descendants = build_descendant_resolver(collections)
    relation_shards: dict[str, dict[str, Any]] = defaultdict(dict)
    entities: list[tuple[str, dict[str, Any], str]] = (
        [("place", p, "plc_") for p in places]
        + [("dataset", d, "dts_") for d in datasets]
        + [("collection", c, "col_") for c in collections]
        + [("publication", p, "pub_") for p in publications]
    )

    def graph_node_id_for(item: dict[str, Any], prefix: str) -> str:
        aid = entity_id(item)
        node = graph_by_arche.get(aid)
        return str(node.get("id")) if node and node.get("id") else f"{prefix}{aid}"

    for kind, entity, prefix in entities:
        eid = entity_id(entity)
        nid = graph_node_id_for(entity, prefix)
        title = entity.get("title") or entity.get("name") or entity.get("filename") or nid
        spatial: set[str] = set()
        collection_roots: set[str] = set()
        publication_ids: set[str] = set()
        dataset_ids: set[str] = set()

        if kind == "place":
            spatial.add(eid)
        elif kind == "dataset":
            dataset_ids.add(eid)
            spatial.update(map(str, entity.get("spatial_ids", []) or []))
            if entity.get("parent_id"):
                collection_roots.add(str(entity["parent_id"]))
            publication_ids.update(map(str, entity.get("documented_ids", []) or []))
        elif kind == "collection":
            collection_roots.add(eid)
            spatial.update(map(str, entity.get("spatial_ids", []) or []))
            spatial.update(map(str, entity.get("item_spatial_ids", []) or []))
        else:
            publication_ids.add(eid)

        if kind == "publication":
            for dataset in datasets:
                if eid in {str(v) for v in dataset.get("documented_ids", []) or []}:
                    dataset_ids.add(entity_id(dataset))
                    spatial.update(map(str, dataset.get("spatial_ids", []) or []))
                    if dataset.get("parent_id"):
                        collection_roots.add(str(dataset["parent_id"]))

        collection_ids = descendants(collection_roots)
        related_dataset_ids: set[str] = set()
        for dataset in datasets:
            did = entity_id(dataset)
            d_spatial = {str(v) for v in dataset.get("spatial_ids", []) or []}
            d_docs = {str(v) for v in dataset.get("documented_ids", []) or []}
            if did in dataset_ids or spatial & d_spatial or str(dataset.get("parent_id") or "") in collection_ids or publication_ids & d_docs:
                related_dataset_ids.add(did)
                spatial.update(d_spatial)
                publication_ids.update(d_docs)
                if dataset.get("parent_id"):
                    collection_roots.add(str(dataset["parent_id"]))
        collection_ids = descendants(collection_roots)

        relation_shards[fnv_bucket(nid)][nid] = {
            "k": kind, "a": eid, "t": title, "p": entity.get("pid"),
            "s": sorted(spatial),
            "c": sorted(prefixed_collection_id(cid) for cid in collection_ids),
            "d": sorted(related_dataset_ids),
            "u": sorted(publication_ids),
        }

    for shard, entries in relation_shards.items():
        write_json(output / "relations" / f"{shard}.json", {"e": entries})

    manifest = {
        "version": 2,
        "mode": "remote-mcp-query-projection",
        "non_authoritative_projection": True,
        "resource_fields": list(RESOURCE_FIELDS),
        "authoritative_sources": {
            "corpus": "../arche_corpus.json", "graph": "../arche_graph.json",
            "places": "../arche_places.json", "datasets": "../arche_datasets.json",
            "collections": "../arche_collections_tree.json", "publications": "../arche_publications.json",
        },
        "resources": len(resources), "graph_nodes": len(nodes), "graph_edges": len(edges),
        "entity_relations": len(entities), "resource_shards": len(resource_shards),
        "search_shards": len(search_postings), "alias_shards": len(aliases),
        "node_shards": len(node_meta), "graph_shards": len(graph_shards),
        "relation_shards": len(relation_shards), "corpus_metadata": corpus.get("metadata", {}),
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_indexes(args.output)
    files = list(args.output.rglob("*.json"))
    total = sum(p.stat().st_size for p in files)
    by_dir: dict[str, int] = defaultdict(int)
    for path in files:
        rel = path.relative_to(args.output)
        by_dir[rel.parts[0] if len(rel.parts) > 1 else "root"] += path.stat().st_size
    detail = ", ".join(f"{k}={v/1024/1024:.2f} MiB" for k, v in sorted(by_dir.items()))
    print(f"[✓] Remote MCP projection v2: {total/1024/1024:.2f} MiB across {len(files):,} JSON files ({detail})")


if __name__ == "__main__":
    main()
