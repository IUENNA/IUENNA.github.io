#!/usr/bin/env python3
"""Build static, read-optimized indexes for the public IUENNA Remote MCP.

The authoritative research data remain the canonical files in ``data/``.
This script emits a non-authoritative query projection under
``data/mcp_remote/`` so a stateless remote MCP can answer requests without
loading the complete corpus or knowledge graph per request.
"""
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

SEARCH_FIELDS = (
    "title", "name", "filename", "description", "breadcrumb", "folder",
    "folder_code", "place", "alternative_title", "pid", "arche_id", "id",
)
SEARCH_LIST_FIELDS = ("path", "subjs", "subjects", "alternative_titles")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )


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
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    text = text.replace("_", " ")
    return " ".join(text.split())


def fnv_bucket(value: str) -> str:
    h = 0x811C9DC5
    for byte in value.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h & 0xFF:02x}"


def graph_bucket(value: str) -> str:
    return fnv_bucket(str(value))


def search_tokens(item: dict[str, Any]) -> set[str]:
    values: list[Any] = [item.get(k) for k in SEARCH_FIELDS]
    for key in SEARCH_LIST_FIELDS:
        value = item.get(key)
        if isinstance(value, list):
            values.extend(value)
        elif value:
            values.append(value)
    out: set[str] = set()
    for value in values:
        for token in normalize(value).split():
            if len(token) >= 2:
                out.add(token)
    return out


def compact_resource(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"), "arche_id": item.get("arche_id"),
        "title": item.get("title"), "filename": item.get("filename"),
        "type": item.get("type"), "date": item.get("date"),
        "place": item.get("place"), "spatial_ids": item.get("spatial_ids", []),
        "parent_collection_id": item.get("col"), "collection_id": item.get("col_id"),
        "folder": item.get("folder"), "path": item.get("path", []),
        "pid": item.get("pid"), "description": item.get("description", ""),
        "formatted_size": item.get("formatted_size"), "size_bytes": item.get("size_bytes"),
    }


def compact_dataset(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"), "arche_id": item.get("arche_id"),
        "title": item.get("title"), "filename": item.get("filename"),
        "description": item.get("description", ""), "parent_id": item.get("parent_id"),
        "spatial_ids": item.get("spatial_ids", []), "documented_ids": item.get("documented_ids", []),
        "pid": item.get("pid"), "formatted_size": item.get("formatted_size"),
        "license_summary": item.get("license_summary"),
        "access_restriction": item.get("access_restriction"), "citation": item.get("citation"),
    }


def compact_collection(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"), "arche_id": item.get("arche_id"),
        "title": item.get("title"), "filename": item.get("filename"),
        "parent_id": item.get("parent_id"), "level": item.get("level"),
        "items": item.get("items"), "formatted_size": item.get("formatted_size"),
        "spatial_ids": item.get("spatial_ids", []),
        "item_spatial_ids": item.get("item_spatial_ids", []), "pid": item.get("pid"),
    }


def compact_node(data: dict[str, Any]) -> list[Any]:
    return [
        data.get("id"), data.get("arche_id"), data.get("label") or data.get("title"),
        data.get("type"), data.get("type_label"), data.get("pid"), data.get("parent_col"),
    ]


def build_descendant_resolver(collections: list[dict[str, Any]]):
    children: dict[str, list[str]] = defaultdict(list)
    for item in collections:
        cid = entity_id(item)
        parent = str(item.get("parent_id") or "")
        if parent:
            children[parent].append(cid)
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


def build_indexes(output: Path) -> dict[str, Any]:
    corpus = load_json(DATA_DIR / "arche_corpus.json")
    graph = load_json(DATA_DIR / "arche_graph.json")
    places = as_list(load_json(DATA_DIR / "arche_places.json"))
    datasets = as_list(load_json(DATA_DIR / "arche_datasets.json"))
    collections = as_list(load_json(DATA_DIR / "arche_collections_tree.json"), "collections")
    publications = as_list(load_json(DATA_DIR / "arche_publications.json"))
    resources = as_list(corpus, "resources")

    if not resources:
        raise RuntimeError("Authoritative corpus contains no resources")
    if not graph.get("elements", {}).get("nodes"):
        raise RuntimeError("Authoritative graph contains no nodes")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    resource_by_id: dict[str, dict[str, Any]] = {}
    resource_to_collection: dict[str, str] = {}
    resource_shards: dict[str, list[dict[str, Any]]] = defaultdict(list)
    search_postings: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    resources_by_spatial: dict[str, set[str]] = defaultdict(set)
    resources_by_col: dict[str, set[str]] = defaultdict(set)
    resources_by_place: dict[str, set[str]] = defaultdict(set)

    for resource in resources:
        rid = str(resource.get("id") or f"res_{resource.get('arche_id')}")
        col_id = str(resource.get("col_id") or (f"col_{resource.get('col')}" if resource.get("col") else "iuenna_root"))
        resource["id"] = rid
        resource["col_id"] = col_id
        resource_by_id[rid] = resource
        resource_to_collection[rid] = col_id
        resource_shards[col_id].append(compact_resource(resource))
        for token in sorted(search_tokens(resource)):
            search_postings[fnv_bucket(token[:2])][token].append(rid)
        for sid in resource.get("spatial_ids", []) or []:
            resources_by_spatial[str(sid)].add(rid)
        if resource.get("col"):
            resources_by_col[str(resource["col"])].add(rid)
        if resource.get("place"):
            resources_by_place[normalize(resource["place"])].add(rid)

    for col_id, items in resource_shards.items():
        write_json(output / "resources" / f"{col_id}.json", {"collection_id": col_id, "resources": items})
    for shard, terms in search_postings.items():
        write_json(output / "search" / f"{shard}.json", {"bucket": shard, "terms": dict(sorted(terms.items()))})
    write_json(output / "resource_to_collection.json", resource_to_collection)

    graph_nodes = [n.get("data", {}) for n in graph["elements"]["nodes"] if isinstance(n, dict)]
    nodes_by_id = {str(n.get("id")): n for n in graph_nodes if n.get("id")}
    graph_by_arche = {str(n.get("arche_id")): n for n in graph_nodes if n.get("arche_id") not in (None, "")}

    lookup_records: dict[str, list[list[Any]]] = defaultdict(list)
    seen_lookup: set[tuple[str, str]] = set()
    for node in graph_nodes:
        nid = str(node.get("id") or "")
        if not nid:
            continue
        label = node.get("label") or node.get("title") or nid
        aliases = [nid, node.get("arche_id"), label, node.get("title"), node.get("filename"), node.get("alternative_title")]
        for alias in aliases:
            key = normalize(alias)
            if not key or (key, nid) in seen_lookup:
                continue
            seen_lookup.add((key, nid))
            lookup_records[fnv_bucket(key[:2])].append([
                key, nid, node.get("arche_id"), label, node.get("type"),
                node.get("type_label"), node.get("pid"), node.get("parent_col"),
            ])
    for shard, records in lookup_records.items():
        records.sort(key=lambda row: (row[0], row[1]))
        write_json(output / "lookup" / f"{shard}.json", {"bucket": shard, "aliases": records})

    adjacency: dict[str, list[list[Any]]] = defaultdict(list)
    predicate_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for edge in graph["elements"].get("edges", []):
        ed = edge.get("data", {})
        src = str(ed.get("source") or "")
        tgt = str(ed.get("target") or "")
        if not src or not tgt or src not in nodes_by_id or tgt not in nodes_by_id:
            continue
        predicate = str(ed.get("label") or "")
        adjacency[src].append(["o", predicate, *compact_node(nodes_by_id[tgt])])
        adjacency[tgt].append(["i", predicate, *compact_node(nodes_by_id[src])])
        predicate_counts[src][predicate] += 1
        predicate_counts[tgt][predicate] += 1

    graph_shards: dict[str, dict[str, Any]] = defaultdict(dict)
    for nid, node in nodes_by_id.items():
        graph_shards[graph_bucket(nid)][nid] = {
            "n": compact_node(node), "e": adjacency.get(nid, []), "pc": dict(predicate_counts.get(nid, {})),
        }
    for shard, entries in graph_shards.items():
        write_json(output / "graph" / f"{shard}.json", {"bucket": shard, "nodes": entries})

    descendants = build_descendant_resolver(collections)
    resource_sort = {
        rid: (" / ".join(resource_by_id[rid].get("path", []) or []), str(resource_by_id[rid].get("title", "")))
        for rid in resource_by_id
    }

    def graph_node_id_for(item: dict[str, Any], fallback_prefix: str) -> str:
        aid = entity_id(item)
        node = graph_by_arche.get(aid)
        if node and node.get("id"):
            return str(node["id"])
        raw = str(item.get("id") or "")
        if raw and raw.startswith(fallback_prefix):
            return raw
        return f"{fallback_prefix}{aid}"

    relation_shards: dict[str, dict[str, Any]] = defaultdict(dict)
    entities: list[tuple[str, dict[str, Any], str]] = []
    entities += [("place", p, "plc_") for p in places]
    entities += [("dataset", d, "dts_") for d in datasets]
    entities += [("collection", c, "col_") for c in collections]
    entities += [("publication", p, "pub_") for p in publications]

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
            spatial.update(str(v) for v in entity.get("spatial_ids", []) or [])
            if entity.get("parent_id"):
                collection_roots.add(str(entity["parent_id"]))
            publication_ids.update(str(v) for v in entity.get("documented_ids", []) or [])
        elif kind == "collection":
            collection_roots.add(eid)
            spatial.update(str(v) for v in entity.get("spatial_ids", []) or [])
            spatial.update(str(v) for v in entity.get("item_spatial_ids", []) or [])
        else:
            publication_ids.add(eid)

        if kind == "publication":
            for dataset in datasets:
                if eid in {str(v) for v in dataset.get("documented_ids", []) or []}:
                    dataset_ids.add(entity_id(dataset))
                    spatial.update(str(v) for v in dataset.get("spatial_ids", []) or [])
                    if dataset.get("parent_id"):
                        collection_roots.add(str(dataset["parent_id"]))

        collection_ids = descendants(collection_roots)
        related_datasets: list[dict[str, Any]] = []
        for dataset in datasets:
            did = entity_id(dataset)
            d_spatial = {str(v) for v in dataset.get("spatial_ids", []) or []}
            d_docs = {str(v) for v in dataset.get("documented_ids", []) or []}
            if (
                did in dataset_ids or bool(spatial & d_spatial)
                or str(dataset.get("parent_id") or "") in collection_ids
                or bool(publication_ids & d_docs)
            ):
                related_datasets.append(dataset)

        for dataset in related_datasets:
            dataset_ids.add(entity_id(dataset))
            spatial.update(str(v) for v in dataset.get("spatial_ids", []) or [])
            publication_ids.update(str(v) for v in dataset.get("documented_ids", []) or [])
            if dataset.get("parent_id"):
                collection_roots.add(str(dataset["parent_id"]))
        collection_ids = descendants(collection_roots)

        related_ids: set[str] = set()
        for sid in spatial:
            related_ids.update(resources_by_spatial.get(sid, set()))
        for cid in collection_ids:
            related_ids.update(resources_by_col.get(cid, set()))
        if kind == "place":
            related_ids.update(resources_by_place.get(normalize(title), set()))

        ordered_resource_ids = sorted(related_ids, key=lambda rid: resource_sort.get(rid, ("", rid)))
        used_cols = {
            str(resource_by_id[rid].get("col")) for rid in ordered_resource_ids if resource_by_id[rid].get("col")
        }
        used_cols.update(collection_ids)
        related_collections = [c for c in collections if entity_id(c) in used_cols]
        related_publications = [p for p in publications if entity_id(p) in publication_ids]

        relation_shards[graph_bucket(nid)][nid] = {
            "resolved_entity": {"type": kind, "arche_id": eid, "title": title, "pid": entity.get("pid")},
            "datasets": [compact_dataset(d) for d in related_datasets],
            "collections": [compact_collection(c) for c in related_collections[:50]],
            "publications": related_publications[:20],
            "resource_ids": ordered_resource_ids,
        }

    for shard, entries in relation_shards.items():
        write_json(output / "relations" / f"{shard}.json", {"bucket": shard, "entities": entries})

    manifest = {
        "version": 1,
        "mode": "remote-mcp-query-projection",
        "authoritative_sources": {
            "corpus": "../arche_corpus.json", "graph": "../arche_graph.json",
            "places": "../arche_places.json", "datasets": "../arche_datasets.json",
            "collections": "../arche_collections_tree.json", "publications": "../arche_publications.json",
        },
        "non_authoritative_projection": True,
        "resources": len(resources), "graph_nodes": len(graph_nodes),
        "graph_edges": len(graph["elements"].get("edges", [])), "entity_relations": len(entities),
        "resource_shards": len(resource_shards), "search_shards": len(search_postings),
        "lookup_shards": len(lookup_records), "graph_shards": len(graph_shards),
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
    total_size = sum(p.stat().st_size for p in files)
    print(
        f"[✓] Remote MCP projection: {manifest['resources']:,} resources, "
        f"{manifest['graph_nodes']:,} graph nodes, {manifest['graph_edges']:,} graph edges; "
        f"{total_size / 1024 / 1024:.2f} MiB across {len(files):,} JSON files"
    )


if __name__ == "__main__":
    main()
