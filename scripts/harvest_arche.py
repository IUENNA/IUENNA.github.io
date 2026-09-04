#!/usr/bin/env python3
"""
harvest_arche.py
----------------
Harvests authoritative collection statistics directly from the ARCHE repository (ACDH-CH)
for the IUENNA project (https://id.acdh.oeaw.ac.at/iuenna).

Outputs:
  data/arche_stats.json
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error

ARCHE_BASE = "https://arche.acdh.oeaw.ac.at/api"
IUENNA_COLLECTION_ID = "1792170"  # Top-level IUENNA collection

def format_bytes(size_bytes):
    """Convert bytes into human-readable unit (MB, GB, TB)."""
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def http_get_json(url, params=None, timeout=30):
    """HTTP GET returning parsed JSON using Python standard library."""
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "IUENNA-Harvester/1.0 (https://iuenna.github.io)"
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content = response.read().decode("utf-8")
        return json.loads(content)

def harvest():
    print(f"[*] Fetching IUENNA Top-Level Collection Metadata (ID: {IUENNA_COLLECTION_ID})...")
    start_time = time.time()
    
    top_url = f"{ARCHE_BASE}/{IUENNA_COLLECTION_ID}/metadata"
    top_data = http_get_json(top_url)
    
    # Extract top-level metadata
    title_de = ""
    title_en = ""
    for t in top_data.get("n1:hasTitle", []):
        if isinstance(t, dict):
            if t.get("@language") == "de":
                title_de = t.get("@value", "")
            elif t.get("@language") == "en":
                title_en = t.get("@value", "")
        elif isinstance(t, str):
            title_de = t
            
    total_items = int(top_data.get("n1:hasNumberOfItems", {}).get("@value", 0))
    total_bytes = int(top_data.get("n1:hasBinarySize", {}).get("@value", 0))
    updated_date = top_data.get("n1:hasUpdatedDate", {}).get("@value", "Unknown")
    pid = top_data.get("n1:hasPid", {}).get("@value", "https://hdl.handle.net/21.11115/0000-0016-7B39-F")
    
    # Licenses
    licenses = []
    for lic in top_data.get("n1:hasLicenseSummary", []):
        if isinstance(lic, dict) and lic.get("@language") == "de":
            licenses.append(lic.get("@value"))
        elif isinstance(lic, str):
            licenses.append(lic)
    if not licenses and top_data.get("n1:hasLicenseSummary"):
        licenses = [str(top_data.get("n1:hasLicenseSummary"))]
        
    # 2. Fetch Subcollections
    print("[*] Fetching IUENNA Sub-Collections...")
    search_url = f"{ARCHE_BASE}/search"
    search_params = {
        "property[0]": "https://vocabs.acdh.oeaw.ac.at/schema#isPartOf",
        "value[0]": f"{ARCHE_BASE}/{IUENNA_COLLECTION_ID}"
    }
    sub_data = http_get_json(search_url, params=search_params)
    sub_graph = sub_data.get("@graph", [])
    
    subcollections = []
    for node in sub_graph:
        if node.get("@type") == "n1:Collection":
            # Extract subcollection title
            col_title = node.get("n1:hasTitle")
            if isinstance(col_title, dict):
                col_title = col_title.get("@value", "")
            elif isinstance(col_title, list):
                col_title = col_title[0].get("@value", "") if col_title else ""
            elif not isinstance(col_title, str):
                col_title = str(col_title)
                
            items_cnt = int(node.get("n1:hasNumberOfItems", {}).get("@value", 0))
            bytes_sz = int(node.get("n1:hasBinarySize", {}).get("@value", 0))
            col_pid = node.get("n1:hasPid", {}).get("@value", "")
            col_id = node.get("@id", "")
            
            # Extract short code from title, e.g. "RET", "JAU", "HB", "GLO", "TAL", "STE"
            code = ""
            if "(" in col_title and ")" in col_title:
                code = col_title[col_title.rfind("(")+1:col_title.rfind(")")]
            
            subcollections.append({
                "code": code,
                "title": col_title,
                "items": items_cnt,
                "bytes": bytes_sz,
                "formatted_size": format_bytes(bytes_sz),
                "pid": col_pid,
                "arche_uri": f"{ARCHE_BASE}/{col_id.replace('n0:', '')}" if "n0:" in col_id else col_id
            })
            
    # Sort subcollections by item count descending
    subcollections.sort(key=lambda x: x["items"], reverse=True)
    
    elapsed = time.time() - start_time
    
    stats = {
        "harvest_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "collection": {
            "title_de": title_de,
            "title_en": title_en,
            "arche_id": f"https://id.acdh.oeaw.ac.at/iuenna",
            "pid": pid,
            "last_updated_in_arche": updated_date,
            "total_items": total_items,
            "total_size_bytes": total_bytes,
            "total_size_formatted": format_bytes(total_bytes),
            "licenses": licenses
        },
        "subcollections": subcollections,
        "harvest_duration_seconds": round(elapsed, 2)
    }
    
    # Save output to data/arche_stats.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, "arche_stats.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        
    print(f"[✓] Successfully wrote harvested statistics to {output_path}")
    print(f"[✓] Total Items: {total_items:,} | Volume: {format_bytes(total_bytes)} | Duration: {stats['harvest_duration_seconds']}s")
    return stats

if __name__ == "__main__":
    try:
        harvest()
    except Exception as e:
        print(f"[!] Error harvesting ARCHE data: {e}", file=sys.stderr)
        sys.exit(1)
