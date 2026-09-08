#!/usr/bin/env python3
"""
parse_arche_full_ttl.py
Fast streaming parser for ARCHE IUENNA full metadata TTL (54 MB).
Extracts:
 - 434 Collections (hierarchy, items, sizes, creators, PIDs, licenses)
 - 21 Persons (names, ORCID, VIAF, GND, email, affiliations)
 - 9 Organisations (names, city, country, Wikidata, ROR)
 - 23 Publications (title, authors, year, publisher, pages, URL, documented collections)
 - 219 Places (title, coordinates, GeoNames, WKT)
 - Unified Autocomplete Search Index
"""

import os
import re
import json
import time

def format_size(size_bytes):
    if not size_bytes:
        return "0 B"
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit in ['MB', 'GB'] else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def parse_arche_ttl(ttl_path):
    print(f"[1/5] Loading and tokenizing {ttl_path}...")
    t0 = time.time()
    
    with open(ttl_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Split into blocks by subject URI
    raw_blocks = content.split("\n<https://arche.acdh.oeaw.ac.at/api/")
    print(f"Read {len(content) / (1024*1024):.2f} MB, found {len(raw_blocks)} blocks in {time.time() - t0:.2f}s")

    persons = {}
    organisations = {}
    publications = {}
    places = {}
    collections = {}
    resources_summary = {}

    def extract_literal(pred, block_text):
        m = re.search(r"n2:" + pred + r'\s+"([^"\\]*(?:\\.[^"\\]*)*)"(?:@[a-z]+|\^\^<[^>]+>)?', block_text)
        if m:
            val = m.group(1)
            return val.replace('\\"', '"').replace('\\\\', '\\')
        return None

    def extract_all_literals(pred, block_text):
        matches = re.findall(r"n2:" + pred + r'\s+"([^"\\]*(?:\\.[^"\\]*)*)"(?:@[a-z]+|\^\^<[^>]+>)?', block_text)
        return [m.replace('\\"', '"').replace('\\\\', '\\') for m in matches]

    def extract_uris(pred, block_text):
        m = re.search(r"n2:" + pred + r"\s+(.*?)(?:;|\.\s*$)", block_text, re.MULTILINE)
        if not m:
            return []
        chunk = m.group(1)
        uris = []
        for token in chunk.split(","):
            token = token.strip()
            m_arche = re.search(r"https://arche\.acdh\.oeaw\.ac\.at/api/(\d+)", token)
            if m_arche:
                uris.append(m_arche.group(1))
            else:
                m_raw = re.search(r"<([^>]+)>", token)
                if m_raw:
                    uris.append(m_raw.group(1))
                else:
                    m_pref = re.match(r"(n\d+|[a-zA-Z0-9_-]+):([^\s,]+)", token)
                    if m_pref:
                        uris.append(token)
        return uris

    def extract_identifiers(block_text):
        m = re.search(r"n2:hasIdentifier\s+(.*?)(?:;|\.\s*$)", block_text, re.MULTILINE)
        if not m:
            return []
        ids = []
        for token in m.group(1).split(","):
            token = token.strip()
            m_raw = re.search(r"<([^>]+)>", token)
            if m_raw:
                ids.append(m_raw.group(1))
            else:
                m_n = re.match(r"(n\d+|[a-zA-Z0-9_-]+):([^\s,]+)", token)
                if m_n:
                    ids.append(token)
        return ids

    print("[2/5] Parsing entities and subjects...")
    for b in raw_blocks[1:]:
        lines = b.splitlines()
        first_line = lines[0]
        m_head = re.match(r"^(\d+)>\s+a\s+n2:(\w+);?", first_line)
        if not m_head:
            continue
        arche_id, entity_type = m_head.groups()

        if entity_type == "Person":
            first_name = extract_literal("hasFirstName", b) or ""
            last_name = extract_literal("hasLastName", b) or ""
            title = extract_literal("hasTitle", b) or f"{first_name} {last_name}".strip()
            personal_title = extract_literal("hasPersonalTitle", b) or ""
            email = extract_literal("hasEmail", b) or ""
            member_of = extract_uris("isMemberOf", b)
            ident_tokens = extract_identifiers(b)

            orcid = None
            wikidata = None
            viaf = None
            gnd = None

            for i in ident_tokens:
                if "orcid.org" in i:
                    m_o = re.search(r"(\d{4}-\d{4}-\d{4}-[\dX]{4})", i)
                    if m_o: orcid = m_o.group(1)
                elif "wikidata.org" in i or i.startswith("n7:"):
                    m_w = re.search(r"(Q\d+)", i)
                    if m_w: wikidata = m_w.group(1)
                elif "viaf.org" in i:
                    viaf = i
                elif "d-nb.info/gnd" in i:
                    gnd = i

            persons[arche_id] = {
                "id": f"per_{arche_id}",
                "arche_id": arche_id,
                "type": "Person",
                "first_name": first_name,
                "last_name": last_name,
                "academic_title": personal_title,
                "name": title,
                "email": email,
                "affiliation_id": member_of[0] if member_of else None,
                "orcid": orcid,
                "wikidata": wikidata,
                "viaf": viaf,
                "gnd": gnd,
                "uri": f"https://arche.acdh.oeaw.ac.at/api/{arche_id}"
            }

        elif entity_type == "Organisation":
            title = extract_literal("hasTitle", b) or f"Organisation {arche_id}"
            alt_title = extract_literal("hasAlternativeTitle", b) or ""
            city = extract_literal("hasCity", b) or ""
            country = extract_literal("hasCountry", b) or ""
            url = extract_literal("hasUrl", b) or ""
            member_of = extract_uris("isMemberOf", b)
            ident_tokens = extract_identifiers(b)

            wikidata = None
            ror = None
            for i in ident_tokens:
                if "wikidata.org" in i or i.startswith("n7:"):
                    m_w = re.search(r"(Q\d+)", i)
                    if m_w: wikidata = m_w.group(1)
                elif "ror.org" in i:
                    ror = i

            organisations[arche_id] = {
                "id": f"org_{arche_id}",
                "arche_id": arche_id,
                "type": "Organisation",
                "name": title,
                "short_name": alt_title,
                "city": city,
                "country": country,
                "url": url,
                "parent_org_id": member_of[0] if member_of else None,
                "wikidata": wikidata,
                "ror": ror,
                "uri": f"https://arche.acdh.oeaw.ac.at/api/{arche_id}"
            }

        elif entity_type == "Publication":
            title = extract_literal("hasTitle", b) or f"Publikation {arche_id}"
            authors = extract_uris("hasAuthor", b)
            issued = extract_literal("hasIssuedDate", b) or ""
            year = issued[:4] if len(issued) >= 4 else None
            pages = extract_literal("hasPages", b) or ""
            publisher = extract_literal("hasPublisher", b) or ""
            series = extract_literal("hasSeriesInformation", b) or ""
            pub_url = extract_literal("hasUrl", b) or ""
            documents = extract_uris("documents", b)

            publications[arche_id] = {
                "id": f"pub_{arche_id}",
                "arche_id": arche_id,
                "type": "Publication",
                "title": title,
                "author_ids": authors,
                "year": year,
                "issued_date": issued,
                "pages": pages,
                "publisher": publisher,
                "series": series,
                "url": pub_url,
                "documents": documents,
                "uri": f"https://arche.acdh.oeaw.ac.at/api/{arche_id}"
            }

        elif entity_type == "Place":
            title = extract_literal("hasTitle", b) or f"Ort {arche_id}"
            alt_titles = extract_all_literals("hasAlternativeTitle", b)
            lat = extract_literal("hasLatitude", b)
            lon = extract_literal("hasLongitude", b)
            wkt = extract_literal("hasWKT", b)
            ident_tokens = extract_identifiers(b)
            geonames = [i for i in ident_tokens if "geonames.org" in i]

            places[arche_id] = {
                "id": f"place_{arche_id}",
                "arche_id": arche_id,
                "type": "Place",
                "title": title,
                "alternative_titles": alt_titles,
                "latitude": float(lat) if lat else None,
                "longitude": float(lon) if lon else None,
                "wkt": wkt,
                "geonames": geonames[0] if geonames else None,
                "uri": f"https://arche.acdh.oeaw.ac.at/api/{arche_id}"
            }

        elif entity_type in ["Collection", "TopCollection"]:
            title = extract_literal("hasTitle", b) or f"Sammlung {arche_id}"
            alt_title = extract_literal("hasAlternativeTitle", b) or ""
            filename = extract_literal("hasFilename", b) or ""
            is_part_of = extract_uris("isPartOf", b)
            creators = extract_uris("hasCreator", b)
            contributors = extract_uris("hasContributor", b)
            curators = extract_uris("hasCurator", b)
            licensors = extract_uris("hasLicensor", b)
            items_str = extract_literal("hasNumberOfItems", b)
            size_str = extract_literal("hasBinarySize", b)
            pid = extract_literal("hasPid", b) or ""
            license_summary = extract_literal("hasLicenseSummary", b) or ""
            access_restriction = extract_literal("hasAccessRestrictionSummary", b) or ""
            spatial = extract_uris("hasSpatialCoverage", b)

            items_count = int(items_str) if items_str and items_str.isdigit() else 0
            size_bytes = int(size_str) if size_str and size_str.isdigit() else 0

            years = []
            for t in [title, alt_title, filename]:
                if t:
                    found_yrs = re.findall(r"\b(19\d\d|20\d\d)\b", t)
                    for y in found_yrs:
                        if 1950 <= int(y) <= 2030 and y not in years:
                            years.append(y)
            campaign_years = "–".join(sorted(years)) if years else None

            collections[arche_id] = {
                "id": f"col_{arche_id}" if (entity_type != "TopCollection" and arche_id != "1792170") else "iuenna_root",
                "arche_id": arche_id,
                "is_top_collection": (entity_type == "TopCollection" or arche_id == "1792170"),
                "title": title,
                "alternative_title": alt_title,
                "filename": filename,
                "parent_id": is_part_of[0] if is_part_of else None,
                "creator_ids": creators,
                "contributor_ids": contributors,
                "curator_ids": curators,
                "licensor_ids": licensors,
                "items": items_count,
                "size_bytes": size_bytes,
                "formatted_size": format_size(size_bytes),
                "pid": pid,
                "license_summary": license_summary,
                "access_restriction": access_restriction,
                "spatial_ids": spatial,
                "campaign_years": campaign_years,
                "uri": f"https://arche.acdh.oeaw.ac.at/api/{arche_id}"
            }

        elif entity_type == "Resource":
            is_part_of = extract_uris("isPartOf", b)
            parent = is_part_of[0] if is_part_of else "unknown"
            resources_summary[parent] = resources_summary.get(parent, 0) + 1

    print(f"[✓] Parsed: {len(collections)} Collections, {len(persons)} Persons, {len(organisations)} Organisations, "
          f"{len(publications)} Publications, {len(places)} Places")

    # Resolve person affiliations
    for p in persons.values():
        aff_id = p.get("affiliation_id")
        if aff_id and aff_id in organisations:
            p["affiliation"] = organisations[aff_id]["name"]
            p["affiliation_short"] = organisations[aff_id].get("short_name")
        else:
            p["affiliation"] = None
            p["affiliation_short"] = None

    # Resolve publication author names
    for pub in publications.values():
        author_names = []
        for a_id in pub.get("author_ids", []):
            if a_id in persons:
                author_names.append(persons[a_id]["name"])
            elif a_id in organisations:
                author_names.append(organisations[a_id]["name"])
            else:
                author_names.append(f"Autor {a_id}")
        pub["authors_formatted"] = ", ".join(author_names) if author_names else "Unbekannt"

    # Assign correct tree levels to collections
    root_id = "1792170"
    if root_id in collections:
        collections[root_id]["level"] = 0

    def compute_levels():
        changed = True
        while changed:
            changed = False
            for col_id, col in collections.items():
                if "level" not in col:
                    p_id = col.get("parent_id")
                    if p_id and p_id in collections and "level" in collections[p_id]:
                        col["level"] = collections[p_id]["level"] + 1
                        changed = True
        for col in collections.values():
            if "level" not in col:
                col["level"] = 1

    compute_levels()

    # Build collection creators mapping
    collection_creators = {}
    for col_id, col in collections.items():
        creators_list = []
        for c_id in col.get("creator_ids", []):
            if c_id in persons:
                p = persons[c_id]
                creators_list.append({
                    "id": p["id"],
                    "arche_id": c_id,
                    "name": p["name"],
                    "type": "Person",
                    "orcid": p.get("orcid"),
                    "affiliation": p.get("affiliation")
                })
            elif c_id in organisations:
                org = organisations[c_id]
                creators_list.append({
                    "id": org["id"],
                    "arche_id": c_id,
                    "name": org["name"],
                    "type": "Organisation"
                })

        contributors_list = []
        for c_id in col.get("contributor_ids", []):
            if c_id in persons:
                p = persons[c_id]
                contributors_list.append({
                    "id": p["id"],
                    "arche_id": c_id,
                    "name": p["name"],
                    "type": "Person",
                    "orcid": p.get("orcid"),
                    "affiliation": p.get("affiliation")
                })
            elif c_id in organisations:
                org = organisations[c_id]
                contributors_list.append({
                    "id": org["id"],
                    "arche_id": c_id,
                    "name": org["name"],
                    "type": "Organisation"
                })

        collection_creators[col_id] = {
            "creators": creators_list,
            "contributors": contributors_list
        }

    # Build recursive collections tree
    print("[3/5] Building hierarchical collections tree...")
    nodes_by_id = {}
    for col_id, col in collections.items():
        nodes_by_id[col_id] = {
            "id": col["id"],
            "arche_id": col_id,
            "name": col["filename"] or col["title"],
            "title": col["title"],
            "alt_title": col["alternative_title"],
            "level": col["level"],
            "items": col["items"],
            "size_bytes": col["size_bytes"],
            "formatted_size": col["formatted_size"],
            "pid": col["pid"],
            "license": col["license_summary"],
            "access": col["access_restriction"],
            "campaign_years": col["campaign_years"],
            "creators": collection_creators.get(col_id, {}).get("creators", []),
            "contributors": collection_creators.get(col_id, {}).get("contributors", []),
            "children": []
        }

    root_node = nodes_by_id.get(root_id)
    unparented = []
    parented_count = 0
    for col_id, col in collections.items():
        if col_id == root_id:
            continue
        p_id = col.get("parent_id")
        if p_id and p_id in nodes_by_id:
            nodes_by_id[p_id]["children"].append(nodes_by_id[col_id])
            parented_count += 1
        else:
            unparented.append(nodes_by_id[col_id])

    print(f"Parented nodes: {parented_count}, Unparented: {len(unparented)}")

    # Sort children alphabetically
    def sort_tree(node):
        node["children"].sort(key=lambda x: x["name"])
        for ch in node["children"]:
            sort_tree(ch)

    if root_node:
        sort_tree(root_node)
        for unp in unparented:
            root_node["children"].append(unp)

    # Build Unified Autocomplete Search Index
    print("[4/5] Constructing unified Autocomplete Search Index...")
    search_index = []

    # 1. Persons
    for p in persons.values():
        search_index.append({
            "id": p["id"],
            "arche_id": p["arche_id"],
            "type": "person",
            "category": "Forscher:innen",
            "label": p["name"],
            "sublabel": p.get("affiliation") or "Archäologe / Forscher:in",
            "icon": "fa-user",
            "color": "#C85A32",
            "tokens": [p["name"], p.get("first_name", ""), p.get("last_name", ""), p.get("orcid") or "", p.get("affiliation") or ""],
            "meta": {
                "orcid": p.get("orcid"),
                "wikidata": p.get("wikidata"),
                "email": p.get("email"),
                "affiliation": p.get("affiliation")
            }
        })

    # 2. Organisations
    for org in organisations.values():
        search_index.append({
            "id": org["id"],
            "arche_id": org["arche_id"],
            "type": "organization",
            "category": "Institutionen",
            "label": org["name"],
            "sublabel": f"{org.get('city', '')}, {org.get('country', '')}".strip(" ,") or "Forschungsinstitution",
            "icon": "fa-building-columns",
            "color": "#3B5266",
            "tokens": [org["name"], org.get("short_name", ""), org.get("city", "")],
            "meta": {
                "wikidata": org.get("wikidata"),
                "ror": org.get("ror"),
                "url": org.get("url")
            }
        })

    # 3. Collections (all 434)
    level_labels = {
        0: "Top-Collection (L0)",
        1: "Subcollection (L1)",
        2: "Hauptkategorie (L2)",
        3: "Fachordner (L3)",
        4: "Teilsammlung (L4)",
        5: "Befundordner (L5)",
        6: "Detailordner (L6)"
    }
    level_colors = {
        0: "#8B2616", 1: "#C85A32", 2: "#D48B38", 3: "#3D7068", 4: "#5B8296", 5: "#6A5D7B", 6: "#8A6D5D"
    }

    for col in collections.values():
        lvl = col.get("level", 1)
        sublabel_parts = [level_labels.get(lvl, f"Ebene L{lvl}")]
        if col.get("items"):
            sublabel_parts.append(f"{col['items']:,} Items")
        if col.get("campaign_years"):
            sublabel_parts.append(f"Kampagne: {col['campaign_years']}")

        tokens = [col["title"], col["alternative_title"], col["filename"], col["arche_id"]]
        if col.get("campaign_years"):
            tokens.append(col["campaign_years"])
        for c in collection_creators.get(col["arche_id"], {}).get("creators", []):
            tokens.append(c["name"])

        search_index.append({
            "id": col["id"],
            "arche_id": col["arche_id"],
            "type": "folder" if lvl > 1 else ("root" if lvl == 0 else "subcollection"),
            "category": "Sammlungen & Ordner",
            "label": col["filename"] or col["title"],
            "sublabel": " • ".join(sublabel_parts),
            "icon": "fa-folder" if lvl > 0 else "fa-sitemap",
            "color": level_colors.get(lvl, "#C85A32"),
            "tokens": tokens,
            "meta": {
                "items": col["items"],
                "size": col["formatted_size"],
                "pid": col["pid"],
                "level": lvl,
                "years": col.get("campaign_years"),
                "creators": [c["name"] for c in collection_creators.get(col["arche_id"], {}).get("creators", [])]
            }
        })

    # 4. Publications
    for pub in publications.values():
        sub = f"{pub.get('authors_formatted', '')} ({pub.get('year', '–')})"
        search_index.append({
            "id": pub["id"],
            "arche_id": pub["arche_id"],
            "type": "publication",
            "category": "Publikationen",
            "label": pub["title"],
            "sublabel": sub,
            "icon": "fa-book-open",
            "color": "#7B4F36",
            "tokens": [pub["title"], pub.get("authors_formatted", ""), pub.get("year", ""), pub.get("publisher", "")],
            "meta": {
                "year": pub.get("year"),
                "authors": pub.get("authors_formatted"),
                "publisher": pub.get("publisher"),
                "pages": pub.get("pages"),
                "url": pub.get("url")
            }
        })

    # 5. Places
    for pl in places.values():
        coord_str = f"{pl['latitude']:.4f}, {pl['longitude']:.4f}" if pl.get("latitude") and pl.get("longitude") else ""
        search_index.append({
            "id": pl["id"],
            "arche_id": pl["arche_id"],
            "type": "place",
            "category": "Fundorte & Orte",
            "label": pl["title"],
            "sublabel": f"Fundort {coord_str}".strip(),
            "icon": "fa-location-dot",
            "color": "#2D6A4F",
            "tokens": [pl["title"]] + pl.get("alternative_titles", []),
            "meta": {
                "lat": pl.get("latitude"),
                "lon": pl.get("longitude"),
                "geonames": pl.get("geonames")
            }
        })

    print(f"[5/5] Writing output files...")
    out_tree = "data/arche_collections_tree.json"
    tree_payload = {
        "crawl_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_collections": len(collections),
        "collections": collections,
        "root": root_node
    }
    with open(out_tree, "w", encoding="utf-8") as f:
        json.dump(tree_payload, f, ensure_ascii=False, indent=2)
    print(f" [✓] Wrote {out_tree} ({os.path.getsize(out_tree) / 1024:.1f} KB)")

    out_entities = "data/arche_resolved_entities.json"
    with open(out_entities, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "total_persons": len(persons),
                "total_organisations": len(organisations),
                "source": "ARCHE RDF TTL 2026",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "persons": persons,
            "organisations": organisations
        }, f, ensure_ascii=False, indent=2)
    print(f" [✓] Wrote {out_entities} ({os.path.getsize(out_entities) / 1024:.1f} KB)")

    out_creators = "data/arche_collection_creators.json"
    with open(out_creators, "w", encoding="utf-8") as f:
        json.dump(collection_creators, f, ensure_ascii=False, indent=2)
    print(f" [✓] Wrote {out_creators} ({os.path.getsize(out_creators) / 1024:.1f} KB)")

    out_pubs = "data/arche_publications.json"
    with open(out_pubs, "w", encoding="utf-8") as f:
        json.dump(publications, f, ensure_ascii=False, indent=2)
    print(f" [✓] Wrote {out_pubs} ({os.path.getsize(out_pubs) / 1024:.1f} KB)")

    out_places = "data/arche_places.json"
    with open(out_places, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=2)
    print(f" [✓] Wrote {out_places} ({os.path.getsize(out_places) / 1024:.1f} KB)")

    out_search = "data/arche_search_index.json"
    with open(out_search, "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    print(f" [✓] Wrote {out_search} ({os.path.getsize(out_search) / 1024:.1f} KB, {len(search_index)} indexed entities)")

    print(f"\n[DONE] Successfully parsed full ARCHE metadata in {time.time() - t0:.2f}s!")

if __name__ == "__main__":
    parse_arche_ttl("data/arche_full_metadata.ttl")
