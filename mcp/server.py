#!/usr/bin/env python3
"""IUENNA Model Context Protocol (MCP) server – Python implementation."""

import json
import sys
import urllib.parse
import urllib.request

BASE_URL = "https://iuenna.github.io/data"
CACHE = {}


def fetch_json(endpoint):
    if endpoint in CACHE:
        return CACHE[endpoint]
    req = urllib.request.Request(
        f"{BASE_URL}/{endpoint}",
        headers={"User-Agent": "IUENNA-MCP-Server/1.1"},
    )
    timeout = 30 if endpoint == "arche_corpus.json" else 15
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    CACHE[endpoint] = data
    return data


def as_list(data, key=None):
    if key and isinstance(data, dict):
        data = data.get(key, {})
    if isinstance(data, dict):
        return list(data.values())
    return data if isinstance(data, list) else []


def norm_id(value):
    value = str(value or "").strip().lower()
    for prefix in ("place_", "plc_", "dts_", "col_", "pub_", "res_"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


def entity_id(item):
    return str(item.get("arche_id") or norm_id(item.get("id")))


def searchable(item):
    fields = [
        item.get("title"), item.get("name"), item.get("filename"),
        item.get("description"), item.get("breadcrumb"), item.get("folder"),
        item.get("folder_code"), item.get("place"), item.get("alternative_title"),
        item.get("pid"),
    ]
    for key in ("path", "subjs", "subjects", "alternative_titles"):
        value = item.get(key)
        if isinstance(value, list):
            fields.extend(value)
        elif value:
            fields.append(value)
    return " ".join(str(v) for v in fields if v).lower()


def matches_tokens(item, tokens):
    text = searchable(item)
    return all(token in text for token in tokens)


def compact_resource(item):
    return {
        "id": item.get("id"), "arche_id": item.get("arche_id"),
        "title": item.get("title"), "filename": item.get("filename"),
        "type": item.get("type"), "date": item.get("date"),
        "place": item.get("place"), "spatial_ids": item.get("spatial_ids", []),
        "parent_collection_id": item.get("col"), "folder": item.get("folder"),
        "path": item.get("path", []), "pid": item.get("pid"),
        "description": item.get("description", ""),
    }


def compact_dataset(item):
    return {
        "id": item.get("id"), "arche_id": item.get("arche_id"),
        "title": item.get("title"), "filename": item.get("filename"),
        "description": item.get("description", ""), "parent_id": item.get("parent_id"),
        "spatial_ids": item.get("spatial_ids", []), "documented_ids": item.get("documented_ids", []),
        "pid": item.get("pid"), "formatted_size": item.get("formatted_size"),
        "license_summary": item.get("license_summary"),
        "access_restriction": item.get("access_restriction"), "citation": item.get("citation"),
    }


def compact_collection(item):
    return {
        "id": item.get("id"), "arche_id": item.get("arche_id"),
        "title": item.get("title"), "filename": item.get("filename"),
        "parent_id": item.get("parent_id"), "level": item.get("level"),
        "items": item.get("items"), "formatted_size": item.get("formatted_size"),
        "spatial_ids": item.get("spatial_ids", []),
        "item_spatial_ids": item.get("item_spatial_ids", []), "pid": item.get("pid"),
    }


def descendants(collections, roots):
    result = {str(v) for v in roots if v}
    changed = True
    while changed:
        changed = False
        for cid, item in collections.items():
            if str(item.get("parent_id") or "") in result and cid not in result:
                result.add(cid)
                changed = True
    return result


def resolve_entity(target, places, datasets, collections, publications):
    query = str(target or "").strip().lower()
    normalized = norm_id(query)
    pools = (("place", places), ("dataset", datasets), ("collection", collections), ("publication", publications))
    partial = []
    for kind, items in pools:
        for item in items:
            labels = [item.get("title"), item.get("name"), item.get("filename"), item.get("alternative_title")]
            labels += item.get("alternative_titles", []) or []
            labels = [str(v).strip().lower() for v in labels if v]
            if normalized and normalized == norm_id(entity_id(item)):
                return (kind, item), 1
            if query and query in labels:
                return (kind, item), 1
            if query and any(query in label for label in labels):
                partial.append((kind, item))
    return (partial[0], len(partial)) if partial else (None, 0)


def related_resources(args):
    target = str(args.get("name_or_id", "")).strip()
    query = str(args.get("query", "")).strip()
    tokens = [t for t in query.lower().split() if t]
    limit = min(max(int(args.get("limit", 50)), 1), 100)

    places = as_list(fetch_json("arche_places.json"))
    datasets = as_list(fetch_json("arche_datasets.json"))
    tree = fetch_json("arche_collections_tree.json")
    collections = as_list(tree, "collections")
    publications = as_list(fetch_json("arche_publications.json"))
    resources = as_list(fetch_json("arche_corpus.json"), "resources")
    collections_by_id = {entity_id(c): c for c in collections}

    resolved, candidate_count = resolve_entity(target, places, datasets, collections, publications)
    if not resolved:
        return {"message": f'No IUENNA place, dataset, collection, or publication matching "{target}" found.'}

    kind, entity = resolved
    eid = entity_id(entity)
    title = entity.get("title") or entity.get("name") or entity.get("filename") or target
    spatial = set()
    collection_roots = set()
    publication_ids = set()
    dataset_ids = set()

    if kind == "place":
        spatial.add(eid)
    elif kind == "dataset":
        dataset_ids.add(eid)
        spatial.update(map(str, entity.get("spatial_ids", [])))
        if entity.get("parent_id"):
            collection_roots.add(str(entity["parent_id"]))
        publication_ids.update(map(str, entity.get("documented_ids", [])))
    elif kind == "collection":
        collection_roots.add(eid)
        spatial.update(map(str, entity.get("spatial_ids", [])))
        spatial.update(map(str, entity.get("item_spatial_ids", [])))
    else:
        publication_ids.add(eid)

    if kind == "publication":
        for dataset in datasets:
            if eid in {str(v) for v in dataset.get("documented_ids", [])}:
                dataset_ids.add(entity_id(dataset))
                spatial.update(map(str, dataset.get("spatial_ids", [])))
                if dataset.get("parent_id"):
                    collection_roots.add(str(dataset["parent_id"]))

    collection_ids = descendants(collections_by_id, collection_roots)
    related_datasets = []
    for dataset in datasets:
        did = entity_id(dataset)
        d_spatial = {str(v) for v in dataset.get("spatial_ids", [])}
        d_docs = {str(v) for v in dataset.get("documented_ids", [])}
        related = (
            did in dataset_ids
            or bool(spatial & d_spatial)
            or str(dataset.get("parent_id") or "") in collection_ids
            or bool(publication_ids & d_docs)
        )
        if related and (not tokens or matches_tokens(dataset, tokens) or did in dataset_ids):
            related_datasets.append(dataset)

    for dataset in related_datasets:
        dataset_ids.add(entity_id(dataset))
        spatial.update(map(str, dataset.get("spatial_ids", [])))
        publication_ids.update(map(str, dataset.get("documented_ids", [])))
        if dataset.get("parent_id"):
            collection_roots.add(str(dataset["parent_id"]))
    collection_ids = descendants(collections_by_id, collection_roots)

    related_files = []
    for resource in resources:
        r_spatial = {str(v) for v in resource.get("spatial_ids", [])}
        r_col = str(resource.get("col") or "")
        relation = bool(spatial & r_spatial) or r_col in collection_ids
        if kind == "place" and str(resource.get("place", "")).lower() == str(title).lower():
            relation = True
        if relation and (not tokens or matches_tokens(resource, tokens)):
            related_files.append(resource)

    used_cols = {str(r.get("col")) for r in related_files if r.get("col")}
    used_cols.update(collection_ids)
    related_collections = [c for c in collections if entity_id(c) in used_cols]
    related_publications = [p for p in publications if entity_id(p) in publication_ids]

    related_files.sort(key=lambda r: (" / ".join(r.get("path", [])), str(r.get("title", ""))))
    return {
        "resolved_entity": {
            "type": kind, "arche_id": eid, "title": title,
            "pid": entity.get("pid"), "candidate_count": candidate_count,
        },
        "query": query or None,
        "counts": {
            "datasets": len(related_datasets), "collections": len(related_collections),
            "publications": len(related_publications),
            "resources_total_matching": len(related_files),
            "resources_returned": min(len(related_files), limit),
        },
        "datasets": [compact_dataset(d) for d in related_datasets],
        "collections": [compact_collection(c) for c in related_collections[:50]],
        "publications": related_publications[:20],
        "resources": [compact_resource(r) for r in related_files[:limit]],
        "truncated": len(related_files) > limit,
    }


TOOLS = [
    {
        "name": "search_iuenna_corpus",
        "description": "Search the authoritative IUENNA primary-resource corpus (20,355 archived files) across titles, filenames, descriptions, collection paths, places, subjects, and PIDs.",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Search terms, e.g. Georadar Hemmaberg or Münzen Globasnitz."},
            "limit": {"type": "integer", "description": "Maximum results (default 10, max 30)."},
        }, "required": ["query"]},
    },
    {
        "name": "get_findspot_details",
        "description": "Retrieve findspot metadata and associated curated datasets for one of the recorded findspots in the Southern Jauntal.",
        "inputSchema": {"type": "object", "properties": {
            "name_or_id": {"type": "string", "description": "Findspot name or ARCHE ID, e.g. Hemmaberg, Stari Trg, or 1756734."},
        }, "required": ["name_or_id"]},
    },
    {
        "name": "get_related_resources",
        "description": "Resolve an IUENNA place, dataset, collection, or publication and return related datasets, collections, publications, and primary archived files.",
        "inputSchema": {"type": "object", "properties": {
            "name_or_id": {"type": "string", "description": "Entity title or ARCHE ID."},
            "query": {"type": "string", "description": "Optional filter such as Georadar, Interpretation, Grab, or 2015."},
            "limit": {"type": "integer", "description": "Maximum primary resources (default 50, max 100)."},
        }, "required": ["name_or_id"]},
    },
    {"name": "get_geodata_catalog", "description": "List the 9 authoritative IUENNA archaeological GeoPackages.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_corpus_statistics", "description": "Retrieve high-level metrics of the IUENNA collection archived on ARCHE.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_project_bibliography",
        "description": "Retrieve bibliographic entries from the official IUENNA Zotero Library (Group 4910727).",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Optional author, keyword, or site filter."},
            "limit": {"type": "integer", "description": "Maximum items (default 10, max 30)."},
        }},
    },
    {
        "name": "get_graph_neighborhood",
        "description": "Query the IUENNA Knowledge Graph (21,071 nodes, 281,851 edges) to traverse semantic relationships. Returns connected nodes, edge predicates (hasCreator, hasAuthor, hasSpatialCoverage, documents, isPartOf, isMemberOf), and neighbor entities.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_or_id": {"type": "string", "description": "Node label, entity name (e.g. 'Sabine Ladstätter', 'Michaela Binder', 'Hemmaberg', 'glo_geodaten_open.gpkg'), or ARCHE ID (e.g. '1756744', 'plc_1756734')."},
                "predicate": {"type": "string", "description": "Optional edge predicate filter (e.g. 'hasCreator', 'hasAuthor', 'hasSpatialCoverage', 'documents', 'isPartOf', 'isMemberOf')."},
                "direction": {"type": "string", "enum": ["all", "outgoing", "incoming"], "description": "Edge direction to follow (default: 'all')."},
                "limit": {"type": "integer", "description": "Maximum number of connected neighbor nodes to return (default: 25, max: 100)."}
            },
            "required": ["node_or_id"]
        }
    },
]


GRAPH_CACHE = None


def get_graph_index():
    global GRAPH_CACHE
    if GRAPH_CACHE is not None:
        return GRAPH_CACHE
    raw_graph = fetch_json("arche_graph.json")
    nodes_by_id = {}
    nodes_by_arche_id = {}
    nodes_list = []

    for n in raw_graph.get("elements", {}).get("nodes", []):
        d = n.get("data", {})
        nid = str(d.get("id", "")).strip()
        nodes_by_id[nid] = d
        if d.get("arche_id"):
            nodes_by_arche_id[str(d["arche_id"])] = d
        nodes_list.append(d)

    adj = {}
    for e in raw_graph.get("elements", {}).get("edges", []):
        ed = e.get("data", {})
        src = str(ed.get("source", "")).strip()
        tgt = str(ed.get("target", "")).strip()
        lbl = ed.get("label") or ""
        pred = ed.get("predicate") or ""
        if src not in adj:
            adj[src] = []
        if tgt not in adj:
            adj[tgt] = []
        adj[src].append({"dir": "outgoing", "neighbor_id": tgt, "predicate": lbl, "uri": pred})
        adj[tgt].append({"dir": "incoming", "neighbor_id": src, "predicate": lbl, "uri": pred})

    GRAPH_CACHE = (nodes_by_id, nodes_by_arche_id, nodes_list, adj)
    return GRAPH_CACHE


def execute_tool(name, args):
    if name == "search_iuenna_corpus":
        query = str(args.get("query", "")).strip()
        tokens = [t for t in query.lower().split() if t]
        limit = min(max(int(args.get("limit", 10)), 1), 30)
        resources = as_list(fetch_json("arche_corpus.json"), "resources")
        found = [r for r in resources if matches_tokens(r, tokens)]
        return {"query": query, "total_found": len(found), "returned": min(len(found), limit), "results": [compact_resource(r) for r in found[:limit]]}

    if name == "get_findspot_details":
        target = str(args.get("name_or_id", "")).strip()
        target_id = norm_id(target)
        target_lc = target.lower()
        places = as_list(fetch_json("arche_places.json"))
        datasets = as_list(fetch_json("arche_datasets.json"))
        found = []
        for place in places:
            title = str(place.get("title", "")).lower()
            if target_id == norm_id(entity_id(place)) or target_lc == title or target_lc in title:
                item = dict(place)
                pid = entity_id(place)
                item["datasets"] = [compact_dataset(d) for d in datasets if pid in {str(v) for v in d.get("spatial_ids", [])}]
                found.append(item)
        return {"count": len(found), "findspots": found[:5]} if found else {"message": f'No findspot matching "{target}" found.'}

    if name == "get_related_resources":
        return related_resources(args)

    if name == "get_geodata_catalog":
        datasets = as_list(fetch_json("arche_datasets.json"))
        return {"count": len(datasets), "datasets": [compact_dataset(d) for d in datasets]}

    if name == "get_corpus_statistics":
        stats = fetch_json("arche_stats.json")
        corpus = fetch_json("arche_corpus.json")
        return {**stats, "primary_resource_corpus": corpus.get("metadata", {})}

    if name == "get_project_bibliography":
        query = str(args.get("query", "")).strip()
        limit = min(max(int(args.get("limit", 10)), 1), 30)
        url = f"https://api.zotero.org/groups/4910727/items?format=json&limit={limit}"
        if query:
            url += f"&q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "IUENNA-MCP-Server/1.1"})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                items = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return {"error": f"Failed to query Zotero API: {exc}", "zotero_web": "https://www.zotero.org/groups/4910727/iuenna"}
        results = []
        for item in items:
            data = item.get("data", {})
            creators = ", ".join(f"{c.get('lastName', '')} {c.get('firstName', '')}".strip() for c in data.get("creators", []) if c.get("lastName"))
            results.append({
                "key": data.get("key"), "title": data.get("title"), "itemType": data.get("itemType"),
                "creators": creators, "date": data.get("date"),
                "publicationTitle": data.get("publicationTitle") or data.get("bookTitle"),
                "doi": data.get("DOI"),
                "url": data.get("url") or f"https://www.zotero.org/groups/4910727/iuenna/items/{data.get('key')}",
            })
        return {"zotero_group_url": "https://www.zotero.org/groups/4910727/iuenna", "count": len(results), "items": results}

    if name == "get_graph_neighborhood":
        target = str(args.get("node_or_id", "")).strip()
        predicate = str(args.get("predicate", "")).strip().lower() or None
        direction = str(args.get("direction", "all")).strip().lower()
        limit = min(max(int(args.get("limit", 25)), 1), 100)

        nodes_by_id, nodes_by_arche_id, nodes_list, adj = get_graph_index()
        t_lc = target.lower()
        t_norm = norm_id(t_lc)

        matched = None
        if t_lc in nodes_by_id:
            matched = nodes_by_id[t_lc]
        elif t_norm in nodes_by_arche_id:
            matched = nodes_by_arche_id[t_norm]
        else:
            for n in nodes_list:
                lbl = (n.get("label") or n.get("title") or "").lower()
                aid = str(n.get("arche_id", "")).lower()
                nid = str(n.get("id", "")).lower()
                if t_lc == lbl or t_lc == aid or t_lc == nid or t_norm == aid:
                    matched = n
                    break
            if not matched:
                for n in nodes_list:
                    lbl = (n.get("label") or n.get("title") or "").lower()
                    if t_lc in lbl:
                        matched = n
                        break

        if not matched:
            return {"message": f'Node "{target}" not found in IUENNA Knowledge Graph.'}

        nid = matched.get("id")
        edges = adj.get(nid, [])

        from collections import Counter
        pred_counts = Counter(e["predicate"] for e in edges)

        filtered = []
        for e in edges:
            if predicate and predicate != e["predicate"].lower():
                continue
            if direction in ("outgoing", "incoming") and direction != e["dir"]:
                continue
            nb_node = nodes_by_id.get(e["neighbor_id"], {})
            filtered.append({
                "direction": e["dir"],
                "predicate": e["predicate"],
                "neighbor": {
                    "id": nb_node.get("id"),
                    "arche_id": nb_node.get("arche_id"),
                    "label": nb_node.get("label") or nb_node.get("title"),
                    "type": nb_node.get("type"),
                    "type_label": nb_node.get("type_label"),
                    "pid": nb_node.get("pid"),
                }
            })

        return {
            "node": {
                "id": matched.get("id"),
                "arche_id": matched.get("arche_id"),
                "label": matched.get("label") or matched.get("title"),
                "type": matched.get("type"),
                "type_label": matched.get("type_label"),
                "pid": matched.get("pid"),
            },
            "total_connections": len(edges),
            "predicate_counts": dict(pred_counts),
            "returned_count": min(len(filtered), limit),
            "neighbors": filtered[:limit],
            "truncated": len(filtered) > limit,
        }

    raise ValueError(f"Unknown tool: {name}")


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except Exception:
            continue
        method = request.get("method")
        msg_id = request.get("id")

        if method == "initialize":
            response = {"jsonrpc": "2.0", "id": msg_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "iuenna-mcp", "version": "1.1.0"}}}
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            response = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            params = request.get("params", {})
            try:
                result = execute_tool(params.get("name"), params.get("arguments", {}))
                response = {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}
            except Exception as exc:
                response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": str(exc)}}
        elif msg_id is not None:
            response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
        else:
            continue
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
