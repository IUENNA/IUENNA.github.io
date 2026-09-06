#!/usr/bin/env python3
"""
harvest_arche_tree.py
---------------------
Recursively crawls and harvests ALL 434 collections, sub-collections, 
sub-sub-collections, and nested folder nodes in the IUENNA repository 
on ARCHE (ACDH-CH / ÖAW).

Outputs:
  data/arche_collections_tree.json
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

ARCHE_BASE = "https://arche.acdh.oeaw.ac.at/api"
TOP_ID = "1792170"

def format_bytes(size_bytes):
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def is_collection(n):
    t = n.get("@type")
    if t and ("Collection" in str(t)): return True
    t2 = n.get("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    if t2:
        for x in t2:
            if isinstance(x, dict) and "Collection" in x.get("@id", ""): return True
            if isinstance(x, str) and "Collection" in x: return True
    return False

def get_prop(n, names):
    for name in names:
        val = n.get(name) or n.get(f"n1:{name}") or n.get(f"https://vocabs.acdh.oeaw.ac.at/schema#{name}")
        if val is not None:
            if isinstance(val, dict): return val.get("@value", "")
            if isinstance(val, list) and len(val) > 0:
                first = val[0]
                if isinstance(first, dict): return first.get("@value", first.get("@id", ""))
                return str(first)
            return str(val)
    return ""

def get_children(parent_id, retries=3):
    search_url = f"{ARCHE_BASE}/search"
    params = {
        "property[0]": "https://vocabs.acdh.oeaw.ac.at/schema#isPartOf",
        "value[0]": f"{ARCHE_BASE}/{parent_id}"
    }
    url = f"{search_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "IUENNA-Tree/1.0"})
    
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                graph = data.get("@graph", [])
                cols = []
                for n in graph:
                    if is_collection(n):
                        raw_id = n.get("@id", "")
                        nid = raw_id.split("/")[-1].replace("n0:", "")
                        title = get_prop(n, ["hasTitle", "hasAlternativeTitle", "hasFilename"])
                        items = get_prop(n, ["hasNumberOfItems"])
                        bytes_sz = get_prop(n, ["hasBinarySize"])
                        pid = get_prop(n, ["hasPid"])
                        spatial = get_prop(n, ["hasSpatialCoverage"])
                        
                        try: items_cnt = int(items)
                        except: items_cnt = 0
                        try: bytes_cnt = int(bytes_sz)
                        except: bytes_cnt = 0
                        
                        cols.append({
                            "arche_id": nid,
                            "title": title or f"Ordner {nid}",
                            "parent_id": str(parent_id),
                            "items": items_cnt,
                            "bytes": bytes_cnt,
                            "formatted_size": format_bytes(bytes_cnt),
                            "pid": pid,
                            "spatial": spatial,
                            "arche_uri": f"{ARCHE_BASE}/{nid}"
                        })
                return cols
        except Exception as e:
            if attempt == retries - 1:
                print(f"[!] Error fetching {parent_id}: {e}", flush=True)
                return []
            time.sleep(1)
    return []

def main():
    print(f"[*] Harvesting ALL collections across the entire ARCHE hierarchy (Root: {TOP_ID})...", flush=True)
    start_time = time.time()
    
    root_node = {
        "arche_id": TOP_ID,
        "title": "IUENNA Top Collection",
        "parent_id": None,
        "items": 20788,
        "bytes": 382980000000,
        "formatted_size": format_bytes(382980000000),
        "pid": "https://hdl.handle.net/21.11115/0000-0016-7B39-F",
        "spatial": "Jauntal",
        "arche_uri": f"{ARCHE_BASE}/{TOP_ID}",
        "level": 0,
        "path": ["IUENNA"]
    }
    
    all_collections = {TOP_ID: root_node}
    curr_ids = [TOP_ID]
    lvl = 1
    
    while curr_ids:
        print(f"[*] Processing Level {lvl}: querying {len(curr_ids)} collection(s)...", flush=True)
        next_ids = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            fmap = {ex.submit(get_children, pid): pid for pid in curr_ids}
            for fut in as_completed(fmap):
                parent_id = fmap[fut]
                children = fut.result()
                parent_path = all_collections[parent_id]["path"]
                
                for c in children:
                    cid = c["arche_id"]
                    if cid not in all_collections:
                        c["level"] = lvl
                        c["path"] = parent_path + [c["title"]]
                        all_collections[cid] = c
                        next_ids.append(cid)
                        
        print(f"[✓] Level {lvl} finished: {len(next_ids)} child collection(s). Total so far: {len(all_collections)}", flush=True)
        curr_ids = next_ids
        lvl += 1

    elapsed = round(time.time() - start_time, 2)
    print(f"\n[✓] Crawl complete in {elapsed}s! Discovered {len(all_collections)} collections across {lvl-1} levels.", flush=True)
    
    # Summary of levels
    level_counts = {}
    for c in all_collections.values():
        l = c["level"]
        level_counts[l] = level_counts.get(l, 0) + 1
    for l in sorted(level_counts.keys()):
        print(f"    - Level {l}: {level_counts[l]} collections")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    out_file = os.path.join(project_root, "data", "arche_collections_tree.json")
    
    payload = {
        "crawl_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_collections": len(all_collections),
        "duration_seconds": elapsed,
        "level_counts": level_counts,
        "collections": all_collections
    }
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    print(f"[✓] Successfully written complete hierarchy to {out_file}", flush=True)

if __name__ == "__main__":
    main()
