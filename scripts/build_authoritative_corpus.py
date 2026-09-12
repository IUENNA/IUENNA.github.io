#!/usr/bin/env python3
"""
build_authoritative_corpus.py

Extract authoritative metadata for all ARCHE Resource entities from
`data/arche_full_metadata.ttl` and write `data/arche_corpus.json`.

Spatial provenance is retained explicitly:
  * spatial_ids_direct: hasSpatialCoverage asserted on the resource in ARCHE
  * spatial_ids_inherited: coverage inherited from the parent collection
  * spatial_ids: effective coverage used by discovery/search
  * spatial_relation_status: asserted | inherited | none
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse

ARCHE_API_BASE = "https://arche.acdh.oeaw.ac.at/api/"
TOP_COLLECTION_ID = "1792170"


def ordered_unique(values):
    seen = set()
    out = []
    for value in values or []:
        value = str(value)
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def extract_arche_uris(predicate, block_text):
    """Extract ARCHE object URIs for one Turtle predicate without breaking on dots in URLs."""
    pattern = re.compile(
        rf"n2:{re.escape(predicate)}\s+(.*?)(?=(?:\s*;\s*(?:n2:|a\s)|\s*\.\s*(?:$|\n)))",
        re.DOTALL | re.MULTILINE,
    )
    values = []
    for match in pattern.finditer(block_text):
        values.extend(re.findall(r"https://arche\.acdh\.oeaw\.ac\.at/api/(\d+)", match.group(1)))
    return ordered_unique(values)


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

    def get_collection_path(col_id):
        path = []
        curr = str(col_id or "")
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
        re.MULTILINE | re.DOTALL,
    )
    matches = pattern.findall(content)
    print(f"[✓] Found {len(matches)} resource blocks in TTL.")

    resources = []
    seen_ids = set()
    direct_spatial_count = 0
    inherited_spatial_count = 0
    no_spatial_count = 0

    for arche_id, body in matches:
        if arche_id in seen_ids:
            continue
        seen_ids.add(arche_id)

        fn_m = re.search(r'n2:hasFilename\s+"([^"\\]*(?:\\.[^"\\]*)*)"', body)
        title_m = re.search(r'n2:hasTitle\s+"([^"\\]*(?:\\.[^"\\]*)*)"', body)
        filename = fn_m.group(1).replace(r'\"', '"') if fn_m else f"res_{arche_id}"
        title = title_m.group(1).replace(r'\"', '"') if title_m else filename

        parent_ids = extract_arche_uris("isPartOf", body)
        parent_id = parent_ids[0] if parent_ids else None
        parent_col = collections.get(parent_id, {}) if parent_id else {}

        folder_title = parent_col.get("title") or parent_col.get("filename") or (f"Ordner {parent_id}" if parent_id else "IUENNA")
        folder_code = parent_col.get("filename") or ""
        path = get_collection_path(parent_id) if parent_id else ["IUENNA"]

        pid_m = re.search(r'n2:hasPid\s+"(https://hdl\.handle\.net/[^"]+)"', body)
        if not pid_m:
            pid_m = re.search(r'<(https://hdl\.handle\.net/[^>]+)>', body)
        pid = pid_m.group(1) if pid_m else f"{ARCHE_API_BASE}{arche_id}"

        desc_m = re.search(r'n2:hasDescription\s+"([^"\\]*(?:\\.[^"\\]*)*)"', body)
        desc = desc_m.group(1).replace(r'\"', '"') if desc_m else ""

        spatial_ids_direct = extract_arche_uris("hasSpatialCoverage", body)
        spatial_ids_inherited = []
        spatial_inherited_from = None
        if spatial_ids_direct:
            spatial_ids = spatial_ids_direct
            spatial_relation_status = "asserted"
            direct_spatial_count += 1
        elif parent_col:
            spatial_ids_inherited = ordered_unique(parent_col.get("spatial_ids") or [])
            spatial_ids = spatial_ids_inherited
            if spatial_ids_inherited:
                spatial_relation_status = "inherited"
                spatial_inherited_from = parent_id
                inherited_spatial_count += 1
            else:
                spatial_relation_status = "none"
                no_spatial_count += 1
        else:
            spatial_ids = []
            spatial_relation_status = "none"
            no_spatial_count += 1

        place_name = None
        coords = None
        for sid in spatial_ids:
            if sid in places_dict:
                pinfo = places_dict[sid]
                place_name = pinfo.get("title") or None
                lon = pinfo.get("longitude")
                lat = pinfo.get("latitude")
                if lon is not None and lat is not None:
                    coords = [float(lon), float(lat)]
                break

        subjects = []
        subject_pattern = re.compile(
            r"n2:hasSubject\s+(.*?)(?=(?:\s*;\s*(?:n2:|a\s)|\s*\.\s*(?:$|\n)))",
            re.DOTALL | re.MULTILINE,
        )
        for match in subject_pattern.finditer(body):
            for subject in re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', match.group(1)):
                subject = subject.replace(r'\"', '"')
                if subject not in subjects:
                    subjects.append(subject)

        date_m = re.search(r'n2:hasCreatedDateOriginal\s+"([^"]+)"', body) or re.search(r'n2:hasAvailableDate\s+"([^"T]+)', body)
        date_str = date_m.group(1) if date_m else "n/a"

        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()
        elif "." in title:
            ext = "." + title.rsplit(".", 1)[-1].lower()

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

        thumb_url = f"https://arche-thumbnails.acdh.oeaw.ac.at/?id={urllib.parse.quote(pid, safe='')}&width=360" if pid else ""

        size_m = re.search(r'n2:hasRawBinarySize\s+"(\d+)"', body) or re.search(r'n2:hasBinarySize\s+"(\d+)"', body)
        raw_size = int(size_m.group(1)) if size_m else 0

        res_entry = {
            "id": f"res_{arche_id}",
            "arche_id": arche_id,
            "title": title,
            "filename": filename,
            "col": parent_id or TOP_COLLECTION_ID,
            "col_id": "iuenna_root" if parent_id == TOP_COLLECTION_ID or not parent_id else f"col_{parent_id}",
            "folder": folder_title,
            "folder_code": folder_code,
            "path": path,
            "place": place_name,
            "spatial_ids": spatial_ids,
            "spatial_ids_direct": spatial_ids_direct,
            "spatial_ids_inherited": spatial_ids_inherited,
            "spatial_relation_status": spatial_relation_status,
            "spatial_inherited_from": spatial_inherited_from,
            "subjs": subjects,
            "pid": pid,
            "uri": f"{ARCHE_API_BASE}{arche_id}",
            "thumb_url": thumb_url,
            "date": date_str,
            "type": ftype,
            "size_bytes": raw_size,
            "coords": coords,
            "description": desc,
        }
        resources.append(res_entry)

    print(f"[✓] Extracted {len(resources)} authoritative resources.")

    type_counts = {}
    place_counts = {}
    for r in resources:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
        if r.get("place"):
            place_counts[r["place"]] = place_counts.get(r["place"], 0) + 1

    print(f"[✓] Resource types: {type_counts}")
    print(f"[✓] Spatial provenance: direct={direct_spatial_count}, inherited={inherited_spatial_count}, none={no_spatial_count}")
    print(f"[✓] Unique represented places: {len(place_counts)}")
    for place, count in sorted(place_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    - {place}: {count} resources")

    out_data = {
        "metadata": {
            "total_resources": len(resources),
            "generated_from": "arche_full_metadata.ttl",
            "type_counts": type_counts,
            "place_counts": place_counts,
            "spatial_provenance_counts": {
                "asserted": direct_spatial_count,
                "inherited": inherited_spatial_count,
                "none": no_spatial_count,
            },
        },
        "resources": resources,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"[✓] Saved authoritative corpus to {out_file} ({os.path.getsize(out_file)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
