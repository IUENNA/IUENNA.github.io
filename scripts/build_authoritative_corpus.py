#!/usr/bin/env python3
"""
build_authoritative_corpus.py
Extracts authoritative metadata for all resources from data/arche_full_metadata.ttl
and produces data/arche_corpus.json with exact collection parenting, clean human-readable
breadcrumb paths (no col_ret), spatial coverages (e.g. Stari Trg), and descriptions.
"""

import os
import re
import json
import urllib.parse

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    
    ttl_file = os.path.join(data_dir, "arche_full_metadata.ttl")
    tree_file = os.path.join(data_dir, "arche_collections_tree.json")
    places_file = os.path.join(data_dir, "arche_places.json")
    out_file = os.path.join(data_dir, "arche_corpus.json")

    print(f"[*] Loading collections from {tree_file}...")
    with open(tree_file, "r", encoding="utf-8") as f:
        tree_data = json.load(f)
    collections = tree_data.get("collections", {})
    print(f"[✓] Loaded {len(collections)} collections.")

    print(f"[*] Loading places from {places_file}...")
    with open(places_file, "r", encoding="utf-8") as f:
        places_dict = json.load(f)
    print(f"[✓] Loaded {len(places_dict)} places.")

    # Path helper
    def get_collection_path(col_id):
        path = []
        curr = str(col_id)
        seen = set()
        while curr and curr in collections and curr not in seen:
            seen.add(curr)
            c = collections[curr]
            name = c.get("title") or c.get("filename") or f"Collection {curr}"
            path.append(name)
            curr = str(c.get("parent_id") or "")
        path.reverse()
        if not path or path[0] != "IUENNA":
            path = ["IUENNA"] + path
        return path

    print(f"[*] Reading {ttl_file}...")
    with open(ttl_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    print("[*] Parsing resource blocks via regex...")
    pattern = re.compile(
        r"^<https://arche\.acdh\.oeaw\.ac\.at/api/(\d+)> a n2:Resource;\s*\n(.*?)(?=^<https://arche\.acdh\.oeaw\.ac\.at/api/|\Z)",
        re.MULTILINE | re.DOTALL
    )
    matches = pattern.findall(content)
    print(f"[✓] Found {len(matches)} resource blocks in TTL.")

    resources = []
    seen_ids = set()

    for arche_id, body in matches:
        if arche_id in seen_ids:
            continue
        seen_ids.add(arche_id)

        # 1. Filename & Title
        fn_m = re.search(r'n2:hasFilename\s+"([^"\\]*(?:\\.[^"\\]*)*)"', body)
        title_m = re.search(r'n2:hasTitle\s+"([^"\\]*(?:\\.[^"\\]*)*)"', body)
        filename = fn_m.group(1).replace(r'\"', '"') if fn_m else f"res_{arche_id}"
        title = title_m.group(1).replace(r'\"', '"') if title_m else filename

        # 2. Parent collection (isPartOf)
        part_m = re.search(r'n2:isPartOf\s+<https://arche\.acdh\.oeaw\.ac\.at/api/(\d+)>', body)
        parent_id = part_m.group(1) if part_m else None
        parent_col = collections.get(parent_id, {}) if parent_id else {}

        # Folder title & code
        folder_title = parent_col.get("title") or parent_col.get("filename") or (f"Ordner {parent_id}" if parent_id else "IUENNA")
        folder_code = parent_col.get("filename") or ""

        # True path without col_ret
        path = get_collection_path(parent_id) if parent_id else ["IUENNA"]

        # 3. Handle / PID
        pid_m = re.search(r'n2:hasPid\s+"(https://hdl\.handle\.net/[^"]+)"', body)
        if not pid_m:
            pid_m = re.search(r'<(https://hdl\.handle\.net/[^>]+)>', body)
        pid = pid_m.group(1) if pid_m else f"https://arche.acdh.oeaw.ac.at/api/{arche_id}"

        # 4. Description
        desc_m = re.search(r'n2:hasDescription\s+"([^"\\]*(?:\\.[^"\\]*)*)"', body)
        desc = desc_m.group(1).replace(r'\"', '"') if desc_m else ""

        # 5. Spatial Coverage (Places)
        spatial_blocks = re.findall(r'n2:hasSpatialCoverage\s+([^\.;]+)', body)
        spatial_ids = []
        for sb in spatial_blocks:
            spatial_ids.extend(re.findall(r'https://arche\.acdh\.oeaw\.ac\.at/api/(\d+)', sb))
        
        # If no direct spatial, inherit from parent collection
        if not spatial_ids and parent_col:
            spatial_ids = parent_col.get("spatial_ids") or []

        place_name = "Jauntal"
        coords = [14.7333, 46.5833]
        for sid in spatial_ids:
            if sid in places_dict:
                pinfo = places_dict[sid]
                place_name = pinfo.get("title") or place_name
                if pinfo.get("longitude") and pinfo.get("latitude"):
                    coords = [float(pinfo["longitude"]), float(pinfo["latitude"])]
                break

        # 6. Subjects (Tags)
        subjs_blocks = re.findall(r'n2:hasSubject\s+([^\.;]+)', body)
        subjects = []
        for sb in subjs_blocks:
            for s in re.findall(r'"([^"]+)"', sb):
                if s not in subjects:
                    subjects.append(s)

        # 7. Date
        date_m = re.search(r'n2:hasCreatedDateOriginal\s+"([^"]+)"', body) or re.search(r'n2:hasAvailableDate\s+"([^"T]+)', body)
        date_str = date_m.group(1) if date_m else "n/a"

        # 8. File Type
        ext = ""
        if "." in filename:
            ext = "." + filename.split(".")[-1].lower()
        elif "." in title:
            ext = "." + title.split(".")[-1].lower()

        ftype = "other"
        if ext in [".tif", ".tiff", ".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            ftype = "image"
        elif ext in [".shp", ".gpkg", ".dxf", ".dwg", ".geojson", ".kml", ".svg"]:
            ftype = "vector"
        elif ext in [".ply", ".obj", ".stl", ".xyz", ".laz", ".las"]:
            ftype = "3d"
        elif ext in [".accdb", ".sqlite", ".db", ".xlsx", ".xls", ".csv", ".tsv"]:
            ftype = "database"
        elif ext in [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"]:
            ftype = "document"

        # Thumbnail URL
        thumb_url = f"https://arche-thumbnails.acdh.oeaw.ac.at/?id={urllib.parse.quote(pid, safe='')}&width=360" if pid else ""

        # Raw size
        size_m = re.search(r'n2:hasRawBinarySize\s+"(\d+)"', body) or re.search(r'n2:hasBinarySize\s+"(\d+)"', body)
        raw_size = int(size_m.group(1)) if size_m else 0

        res_entry = {
            "id": f"res_{arche_id}",
            "arche_id": arche_id,
            "title": title,
            "filename": filename,
            "col": parent_id or "iuenna_root",
            "col_id": f"col_{parent_id}" if parent_id else "iuenna_root",
            "folder": folder_title,
            "folder_code": folder_code,
            "path": path,
            "place": place_name,
            "spatial_ids": spatial_ids,
            "subjs": subjects,
            "pid": pid,
            "thumb_url": thumb_url,
            "date": date_str,
            "type": ftype,
            "size_bytes": raw_size,
            "coords": coords,
            "description": desc
        }
        resources.append(res_entry)

    print(f"[✓] Extracted {len(resources)} authoritative resources.")

    # Statistics
    type_counts = {}
    place_counts = {}
    for r in resources:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
        place_counts[r["place"]] = place_counts.get(r["place"], 0) + 1

    print(f"[✓] Resource types: {type_counts}")
    print(f"[✓] Unique places represented: {len(place_counts)} places. Top places:")
    for p, c in sorted(place_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    - {p}: {c} resources")

    out_data = {
        "metadata": {
            "total_resources": len(resources),
            "generated_from": "arche_full_metadata.ttl",
            "type_counts": type_counts,
            "place_counts": place_counts
        },
        "resources": resources
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"[✓] Saved authoritative corpus to {out_file} ({os.path.getsize(out_file)/1024/1024:.2f} MB)")

if __name__ == "__main__":
    main()
