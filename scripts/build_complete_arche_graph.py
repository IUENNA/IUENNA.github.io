#!/usr/bin/env python3
"""
build_complete_arche_graph.py

Build the IUENNA Cytoscape Knowledge Graph as a provenance-aware projection of
ARCHE metadata.

Core invariants:
  * all graph nodes are created before semantic ARCHE relations are resolved;
  * one ARCHE identifier maps to exactly one graph node;
  * curated dataset records enrich matching ARCHE Resource nodes instead of
    creating duplicate dts_* nodes;
  * asserted, inherited, aggregated, curated, and synthetic relations retain
    explicit provenance;
  * a machine-readable graph audit is emitted for every build.
"""
from __future__ import annotations
import json
import math
import os
import re
import time
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
import networkx as nx
SCHEMA_BASE = 'https://vocabs.acdh.oeaw.ac.at/schema#'
ARCHE_API_BASE = 'https://arche.acdh.oeaw.ac.at/api/'
TOP_COLLECTION_ID = '1792170'
TTL_TARGET_PREDS = {'isPartOf', 'hasHosting', 'hasOwner', 'hasLicensor', 'hasRightsHolder', 'hasCurator', 'hasDepositor', 'hasMetadataCreator', 'hasCreator', 'hasContributor', 'hasAuthor', 'documents', 'hasDigitisingAgent', 'hasSpatialCoverage', 'isMemberOf'}
STATUS_PRIORITY = {'synthetic': 0, 'aggregated': 1, 'inherited': 2, 'curated': 3, 'asserted': 4}
LEVEL_COLORS = {0: '#8B2616', 1: '#C85A32', 2: '#D48B38', 3: '#3D7068', 4: '#5B8296', 5: '#6A5D7B', 6: '#8A6D5D'}
LEVEL_LABELS = {0: 'Top-Collection', 1: 'Subcollection (L1)', 2: 'Hauptkategorie (L2)', 3: 'Fachordner (L3)', 4: 'Teilsammlung (L4)', 5: 'Befundordner (L5)', 6: 'Detailordner (L6)'}
LEVEL_ICONS = {0: 'fa-landmark', 1: 'fa-folder-tree', 2: 'fa-folder-open', 3: 'fa-folder', 4: 'fa-folder-minus', 5: 'fa-box-archive', 6: 'fa-camera'}
RES_TYPE_INFO = {'image': ('ARCHE-Bild', '#2A9D8F', 'fa-image'), 'vector': ('ARCHE-Plan/Vektor', '#E76F51', 'fa-draw-polygon'), 'document': ('ARCHE-Dokument/PDF', '#457B9D', 'fa-file-lines'), 'database': ('ARCHE-Datenbank/Tabelle', '#1D3557', 'fa-table'), 'model': ('ARCHE-3D-Modell', '#F4A261', 'fa-cube'), '3d': ('ARCHE-3D-Modell', '#F4A261', 'fa-cube'), 'audio': ('ARCHE-Audio', '#E9C46A', 'fa-volume-high'), 'other': ('ARCHE-Datei', '#3D7068', 'fa-file')}

def format_size(size_bytes):
    if not size_bytes:
        return '0 B'
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024.0:
            return f'{size:.1f} {unit}' if unit in ('MB', 'GB') else f'{int(size)} {unit}'
        size /= 1024.0
    return f'{size:.1f} PB'

def ordered_unique(values: Iterable) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for value in values or []:
        value = str(value)
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out

def emptyish(value) -> bool:
    return value is None or value == '' or value == [] or (value == {})

def flatten_collection_tree(root_tree: dict) -> List[dict]:
    root_node = root_tree.get('root', root_tree)
    collections: List[dict] = []
    def walk(node: dict, parent_id: Optional[str]=None):
        current = dict(node)
        current['parent_id'] = parent_id
        children = current.pop('children', [])
        collections.append(current)
        for child in children:
            walk(child, str(node['arche_id']))
    walk(root_node)
    return collections

class NodeRegistry:
    """Canonical node registry enforcing one ARCHE ID -> one graph node."""
    def __init__(self):
        self.nodes_by_id: Dict[str, dict] = {}
        self.arche_to_node_id: Dict[str, str] = {}
    def add(self, node_data: dict, *, role: Optional[str]=None, arche_id: Optional[str]=None, prefer_incoming: Sequence[str]=()) -> str:
        node_data = dict(node_data)
        aid = str(arche_id or node_data.get('arche_id') or '').strip() or None
        proposed_id = str(node_data['id'])
        if aid and aid in self.arche_to_node_id:
            node_id = self.arche_to_node_id[aid]
            existing = self.nodes_by_id[node_id]
            incoming = dict(node_data)
            incoming.pop('id', None)
            incoming.pop('arche_id', None)
            for key, value in incoming.items():
                if key == 'roles':
                    continue
                if key in prefer_incoming and (not emptyish(value)):
                    existing[key] = value
                elif key not in existing or emptyish(existing[key]):
                    existing[key] = value
            roles = set(existing.get('roles', []))
            roles.update(node_data.get('roles', []))
            if role:
                roles.add(role)
            existing['roles'] = sorted(roles)
            return node_id
        if proposed_id in self.nodes_by_id:
            raise ValueError(f'Duplicate graph node id: {proposed_id}')
        if aid:
            node_data['arche_id'] = aid
        roles = set(node_data.get('roles', []))
        if role:
            roles.add(role)
        if roles:
            node_data['roles'] = sorted(roles)
        self.nodes_by_id[proposed_id] = node_data
        if aid:
            self.arche_to_node_id[aid] = proposed_id
        return proposed_id
    def get_by_arche_id(self, arche_id: str) -> Optional[dict]:
        node_id = self.arche_to_node_id.get(str(arche_id))
        return self.nodes_by_id.get(node_id) if node_id else None
    def node_id_for_arche_id(self, arche_id: str) -> Optional[str]:
        return self.arche_to_node_id.get(str(arche_id))
    def as_cytoscape_nodes(self) -> List[dict]:
        return [{'data': data} for data in self.nodes_by_id.values()]

class EdgeRegistry:
    """Deduplicate graph edges while retaining all derivation/provenance paths."""
    def __init__(self):
        self.by_triple: Dict[Tuple[str, str, str], dict] = {}
    @staticmethod
    def _edge_id(source: str, target: str, label: str) -> str:
        safe_label = re.sub('[^A-Za-z0-9_]+', '_', label).strip('_')
        return f'edge_{safe_label}_{source}_{target}'
    def add(self, source: str, target: str, label: str, *, predicate: Optional[str]=None, provenance: str, relation_status: str, semantic: bool=True, derivation: Optional[dict]=None) -> dict:
        key = (str(source), str(target), str(label))
        predicate = predicate or f'{SCHEMA_BASE}{label}'
        derivation_entry = {'provenance': provenance, 'relation_status': relation_status}
        if derivation:
            derivation_entry.update(derivation)
        if key not in self.by_triple:
            edge = {'id': self._edge_id(*key), 'source': key[0], 'target': key[1], 'label': key[2], 'predicate': predicate, 'provenance': provenance, 'provenance_sources': [provenance], 'relation_status': relation_status, 'semantic': bool(semantic), 'derivations': [derivation_entry]}
            self.by_triple[key] = edge
            return edge
        edge = self.by_triple[key]
        if provenance not in edge['provenance_sources']:
            edge['provenance_sources'].append(provenance)
        if derivation_entry not in edge['derivations']:
            edge['derivations'].append(derivation_entry)
        current_priority = STATUS_PRIORITY.get(edge.get('relation_status'), -1)
        incoming_priority = STATUS_PRIORITY.get(relation_status, -1)
        if incoming_priority > current_priority:
            edge['provenance'] = provenance
            edge['relation_status'] = relation_status
            edge['predicate'] = predicate
        edge['semantic'] = bool(edge.get('semantic', True) or semantic)
        return edge
    def as_cytoscape_edges(self) -> List[dict]:
        return [{'data': edge} for edge in self.by_triple.values()]

def parse_arche_relation_triples(ttl_file: str) -> Set[Tuple[str, str, str]]:
    """Extract configured ARCHE-to-ARCHE object relations from Turtle subject blocks."""
    if not os.path.exists(ttl_file):
        return set()
    with open(ttl_file, 'r', encoding='utf-8', errors='ignore') as fh:
        content = fh.read()
    blocks = re.split('(?m)^<https://arche\\.acdh\\.oeaw\\.ac\\.at/api/', content)
    triples: Set[Tuple[str, str, str]] = set()
    for block in blocks[1:]:
        head = re.match('(\\d+)>', block)
        if not head:
            continue
        source_id = head.group(1)
        for pred in TTL_TARGET_PREDS:
            pattern = re.compile(f'n2:{re.escape(pred)}\\s+(.*?)(?=(?:\\s*;\\s*(?:n2:|a\\s)|\\s*\\.\\s*(?:$|\\n)))', re.DOTALL | re.MULTILINE)
            for match in pattern.finditer(block):
                object_chunk = match.group(1)
                target_ids = re.findall('https://arche\\.acdh\\.oeaw\\.ac\\.at/api/(\\d+)', object_chunk)
                for target_id in target_ids:
                    triples.add((source_id, pred, target_id))
    return triples

def provenance_edge(edges: EdgeRegistry, source: Optional[str], target: Optional[str], label: str, provenance: str, relation_status: str, *, semantic: bool=True, derivation: Optional[dict]=None):
    if source and target:
        edges.add(source, target, label, predicate=f'{SCHEMA_BASE}{label}', provenance=provenance, relation_status=relation_status, semantic=semantic, derivation=derivation)

def build_input_role_index(collections: Sequence[dict], corpus: Sequence[dict], datasets: dict, persons: dict, organisations: dict, publications: dict, places: dict) -> Dict[str, Set[str]]:
    role_index: Dict[str, Set[str]] = defaultdict(set)
    for c in collections:
        role_index[str(c.get('arche_id'))].add('collection')
    for r in corpus:
        role_index[str(r.get('arche_id'))].add('resource')
    for aid in datasets:
        role_index[str(aid)].add('dataset')
    for aid in persons:
        role_index[str(aid)].add('person')
    for aid in organisations:
        role_index[str(aid)].add('organization')
    for aid in publications:
        role_index[str(aid)].add('publication')
    for aid in places:
        role_index[str(aid)].add('place')
    role_index.pop('None', None)
    role_index.pop('', None)
    return role_index

def build_graph(data_dir: Optional[str]=None):
    started = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    data_dir = data_dir or os.path.join(project_root, 'data')
    def load_json(filename):
        path = os.path.join(data_dir, filename)
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    print(f'[*] Loading graph inputs from {data_dir}...')
    root_tree = load_json('arche_collections_tree.json')
    entities_data = load_json('arche_resolved_entities.json')
    persons = entities_data.get('persons', {})
    organisations = entities_data.get('organisations', {})
    col_creators = load_json('arche_collection_creators.json')
    publications = load_json('arche_publications.json')
    places_data = load_json('arche_places.json')
    datasets_data = load_json('arche_datasets.json')
    corpus_data = load_json('arche_corpus.json')
    corpus = corpus_data.get('resources', [])
    ttl_file = os.path.join(data_dir, 'arche_full_metadata.ttl')
    collections = flatten_collection_tree(root_tree)
    collection_meta = root_tree.get('collections', {})
    print(f'[✓] Loaded {len(collections)} collections and {len(corpus)} resources.')
    input_role_index = build_input_role_index(collections, corpus, datasets_data, persons, organisations, publications, places_data)
    source_role_overlaps = {aid: sorted(roles) for aid, roles in input_role_index.items() if len(roles) > 1}
    registry = NodeRegistry()
    for col in collections:
        aid = str(col['arche_id'])
        lvl = int(col.get('level', 1))
        node_id = 'iuenna_root' if aid == TOP_COLLECTION_ID else col.get('id') or f'col_{aid}'
        meta = collection_meta.get(aid, col)
        label = meta.get('title') or col.get('title') or col.get('name') or aid
        alt_label = meta.get('alternative_title') or meta.get('filename') or col.get('alt_title') or col.get('name') or ''
        registry.add({'id': node_id, 'arche_id': aid, 'label': label, 'title': meta.get('title') or col.get('title') or label, 'full_title': meta.get('title') or col.get('title') or label, 'alt_title': alt_label, 'filename': meta.get('filename') or col.get('filename') or '', 'level': lvl, 'type': 'root' if lvl == 0 else 'subcollection' if lvl == 1 else f'folder_l{lvl}', 'type_label': LEVEL_LABELS.get(lvl, f'Ebene L{lvl}'), 'color': LEVEL_COLORS.get(lvl, '#5A6B7C'), 'icon': LEVEL_ICONS.get(lvl, 'fa-folder'), 'items': col.get('items', 0), 'size': col.get('formatted_size', '0 B'), 'formatted_size': col.get('formatted_size', '0 B'), 'size_bytes': col.get('size_bytes', 0), 'pid': col.get('pid', ''), 'license': col.get('license', col.get('license_summary', '')), 'license_summary': col.get('license_summary', col.get('license', '')), 'access': col.get('access', col.get('access_restriction', '')), 'access_restriction': col.get('access_restriction', col.get('access', '')), 'campaign_years': col.get('campaign_years'), 'creators': col_creators.get(aid, {}).get('creators', []), 'contributors': col_creators.get(aid, {}).get('contributors', []), 'parent_arche_id': str(col.get('parent_id')) if col.get('parent_id') else None, 'uri': f'{ARCHE_API_BASE}{aid}'}, role='collection')
    for aid, person in persons.items():
        aid = str(aid)
        registry.add({'id': person.get('id') or f'per_{aid}', 'arche_id': aid, 'label': person.get('name') or f'Person {aid}', 'name': person.get('name') or f'Person {aid}', 'first_name': person.get('first_name', ''), 'last_name': person.get('last_name', ''), 'academic_title': person.get('academic_title', ''), 'type': 'person', 'type_label': 'Forscher:in', 'category': 'Akteur', 'email': person.get('email', ''), 'orcid': person.get('orcid'), 'wikidata': person.get('wikidata'), 'viaf': person.get('viaf'), 'gnd': person.get('gnd'), 'affiliation': person.get('affiliation'), 'affiliation_id': person.get('affiliation_id'), 'color': '#C85A32', 'icon': 'fa-user', 'uri': person.get('uri', f'{ARCHE_API_BASE}{aid}')}, role='person')
    for aid, org in organisations.items():
        aid = str(aid)
        registry.add({'id': org.get('id') or f'org_{aid}', 'arche_id': aid, 'label': org.get('short_name') or org.get('name') or f'Organisation {aid}', 'name': org.get('name') or f'Organisation {aid}', 'full_name': org.get('name') or f'Organisation {aid}', 'short_name': org.get('short_name', ''), 'type': 'organization', 'type_label': 'Institution / Partner', 'category': 'Trägerorganisation', 'city': org.get('city', ''), 'country': org.get('country', ''), 'url': org.get('url', ''), 'wikidata': org.get('wikidata'), 'ror': org.get('ror'), 'parent_org_id': org.get('parent_org_id'), 'color': '#3B5266', 'icon': 'fa-building-columns', 'uri': org.get('uri', f'{ARCHE_API_BASE}{aid}')}, role='organization')
    for aid, pub in publications.items():
        aid = str(aid)
        registry.add({'id': pub.get('id') or f'pub_{aid}', 'arche_id': aid, 'label': pub.get('title') or f'Publikation {aid}', 'title': pub.get('title') or f'Publikation {aid}', 'type': 'publication', 'type_label': 'Publikation', 'category': 'Fachpublikation', 'year': pub.get('year', '–'), 'issued_date': pub.get('issued_date', ''), 'authors': pub.get('authors_formatted', ''), 'publisher': pub.get('publisher', ''), 'series': pub.get('series', ''), 'pages': pub.get('pages', ''), 'url': pub.get('url', ''), 'author_ids': pub.get('author_ids', []), 'documents': pub.get('documents', []), 'color': '#7B4F36', 'icon': 'fa-book-open', 'uri': pub.get('uri', f'{ARCHE_API_BASE}{aid}')}, role='publication')
    for aid, place in places_data.items():
        aid = str(aid)
        registry.add({'id': f'plc_{aid}', 'arche_id': aid, 'label': place.get('title') or f'Ort {aid}', 'title': place.get('title') or f'Ort {aid}', 'type': 'place', 'type_label': 'Fundort / Ort', 'category': 'Geographischer Fundort', 'latitude': place.get('latitude'), 'longitude': place.get('longitude'), 'wkt': place.get('wkt'), 'geonames': place.get('geonames', ''), 'color': '#2D6A4F', 'icon': 'fa-location-dot', 'uri': place.get('uri', f'{ARCHE_API_BASE}{aid}')}, role='place')
    collection_node_ids = {registry.node_id_for_arche_id(str(c['arche_id'])) for c in collections}
    collection_node_ids.discard(None)
    for resource in corpus:
        aid = str(resource.get('arche_id'))
        rid = resource.get('id') or f'res_{aid}'
        ftype = resource.get('type', 'other')
        type_label, color, icon = RES_TYPE_INFO.get(ftype, RES_TYPE_INFO['other'])
        parent_aid = str(resource.get('col')) if resource.get('col') else None
        parent_node = registry.node_id_for_arche_id(parent_aid) if parent_aid else None
        if not parent_node or parent_node not in collection_node_ids:
            parent_node = 'iuenna_root'
        registry.add({'id': rid, 'arche_id': aid, 'label': resource.get('title') or resource.get('filename') or rid, 'title': resource.get('title') or resource.get('filename') or rid, 'filename': resource.get('filename', ''), 'type': 'resource', 'type_label': type_label, 'ftype': ftype, 'parent_col': parent_node, 'parent_arche_id': parent_aid, 'pid': resource.get('pid', ''), 'place': resource.get('place', ''), 'spatial_ids': resource.get('spatial_ids', []), 'spatial_ids_direct': resource.get('spatial_ids_direct', []), 'spatial_ids_inherited': resource.get('spatial_ids_inherited', []), 'spatial_relation_status': resource.get('spatial_relation_status'), 'spatial_inherited_from': resource.get('spatial_inherited_from'), 'subjs': resource.get('subjs', []), 'path': resource.get('path', []), 'date': resource.get('date', ''), 'size_bytes': resource.get('size_bytes', 0), 'formatted_size': format_size(resource.get('size_bytes', 0)), 'thumb_url': resource.get('thumb_url', ''), 'coords': resource.get('coords'), 'description': resource.get('description', ''), 'color': color, 'icon': icon, 'uri': resource.get('uri', f'{ARCHE_API_BASE}{aid}')}, role='resource')
    dataset_prefer = ('type', 'type_label', 'category', 'color', 'icon', 'citation', 'license', 'license_summary', 'access', 'access_restriction', 'creators', 'contributors', 'dataset_spatial_ids', 'documented_ids')
    for aid, dataset in datasets_data.items():
        aid = str(aid)
        existing_id = registry.node_id_for_arche_id(aid)
        proposed_id = existing_id or f'dts_{aid}'
        registry.add({'id': proposed_id, 'arche_id': aid, 'label': dataset.get('filename') or dataset.get('title') or proposed_id, 'title': dataset.get('filename') or dataset.get('title') or proposed_id, 'full_title': dataset.get('title') or dataset.get('filename') or proposed_id, 'filename': dataset.get('filename', ''), 'type': 'dataset', 'type_label': 'Forschungsdatensatz / GeoPackage', 'category': 'Geodaten & Forschungsdaten', 'color': '#1B4965', 'icon': 'fa-database', 'dataset_spatial_ids': dataset.get('spatial_ids', []), 'documented_ids': dataset.get('documented_ids', []), 'creators': dataset.get('creators', []), 'contributors': dataset.get('contributors', []), 'citation': dataset.get('citation', ''), 'license': dataset.get('license_summary', ''), 'license_summary': dataset.get('license_summary', ''), 'access': dataset.get('access_restriction', ''), 'access_restriction': dataset.get('access_restriction', ''), 'dataset_parent_arche_id': dataset.get('parent_id'), 'dataset_size_bytes': dataset.get('size_bytes', 0), 'dataset_formatted_size': dataset.get('formatted_size', '0 B'), 'uri': dataset.get('uri', f'{ARCHE_API_BASE}{aid}')}, role='dataset', prefer_incoming=dataset_prefer)
    epochs = [{'id': 'epc_roman', 'label': 'Römische Kaiserzeit', 'type': 'epoch', 'type_label': 'Zeitepoche', 'uri': 'http://n2t.net/ark:/99152/p0qhb66t32q', 'range': '15 v. Chr. – 476 n. Chr.', 'color': '#5A6B7C', 'icon': 'fa-hourglass-half', 'roles': ['curated-helper']}, {'id': 'epc_early_medieval', 'label': 'Frühmittelalter', 'type': 'epoch', 'type_label': 'Zeitepoche', 'uri': 'http://n2t.net/ark:/99152/p0qhb66h52w', 'range': 'ca. 500 – 1050 n. Chr.', 'color': '#5A6B7C', 'icon': 'fa-clock', 'roles': ['curated-helper']}]
    subjects = [{'id': 'sbj_arch_data', 'label': 'Archäologische Daten', 'type': 'subject', 'type_label': 'Fachschlagwort', 'color': '#7E6B8F', 'icon': 'fa-tag', 'roles': ['curated-helper']}, {'id': 'sbj_fieldwork', 'label': 'Grabungsdokumentation', 'type': 'subject', 'type_label': 'Fachschlagwort', 'color': '#7E6B8F', 'icon': 'fa-book-open', 'roles': ['curated-helper']}, {'id': 'sbj_roman_arch', 'label': 'Römische Archäologie', 'type': 'subject', 'type_label': 'Fachschlagwort', 'color': '#7E6B8F', 'icon': 'fa-monument', 'roles': ['curated-helper']}, {'id': 'sbj_dh', 'label': 'Digitale Geisteswissenschaften', 'type': 'subject', 'type_label': 'Fachschlagwort', 'color': '#7E6B8F', 'icon': 'fa-laptop-code', 'roles': ['curated-helper']}, {'id': 'sbj_dig_arch', 'label': 'Dokumentarfotografien', 'type': 'subject', 'type_label': 'Fachschlagwort', 'color': '#7E6B8F', 'icon': 'fa-camera', 'roles': ['curated-helper']}, {'id': 'sbj_reprografie', 'label': 'Reprografien & Aufmaße', 'type': 'subject', 'type_label': 'Fachschlagwort', 'color': '#7E6B8F', 'icon': 'fa-pen-ruler', 'roles': ['curated-helper']}]
    licenses = [{'id': 'lic_inc', 'label': 'In Copyright (InC 1.0)', 'type': 'license', 'type_label': 'Lizenz / Nutzungsrechte', 'desc': 'Urheberrechtlich geschützte Archivbestände des kärnten.museums und ÖAI.', 'color': '#437F97', 'icon': 'fa-shield-halved', 'roles': ['curated-helper']}, {'id': 'lic_ccby', 'label': 'Creative Commons Attribution 4.0 (CC BY 4.0)', 'type': 'license', 'type_label': 'Open Access Lizenz', 'desc': 'Open Access Forschungsdaten des Go!Digital-Projekts IUENNA.', 'color': '#3D7068', 'icon': 'fa-creative-commons', 'roles': ['curated-helper']}]
    for helper in epochs + subjects + licenses:
        registry.add(helper)
    node_id_map = dict(registry.arche_to_node_id)
    final_arche_counts = Counter((str(node.get('arche_id')) for node in registry.nodes_by_id.values() if node.get('arche_id')))
    duplicate_arche_ids_final = sorted((aid for aid, count in final_arche_counts.items() if count > 1))
    if duplicate_arche_ids_final:
        raise RuntimeError('Canonical node invariant violated; duplicate ARCHE IDs remain: ' + ', '.join(duplicate_arche_ids_final[:20]))
    print(f'[✓] PASS 1 complete: {len(registry.nodes_by_id)} canonical nodes; {len(source_role_overlaps)} source-role overlaps merged.')
    edges = EdgeRegistry()
    for col in collections:
        aid = str(col['arche_id'])
        source = node_id_map.get(aid)
        parent_aid = str(col.get('parent_id')) if col.get('parent_id') else None
        parent = node_id_map.get(parent_aid) if parent_aid else None
        provenance_edge(edges, source, parent, 'isPartOf', 'IUENNA-collection-index', 'curated', derivation={'source': 'arche_collections_tree.json'})
        meta = collection_meta.get(aid, col)
        direct_spatial = ordered_unique(meta.get('spatial_ids', []))
        aggregated_spatial = ordered_unique(list(meta.get('item_spatial_ids', [])) + list(col.get('item_spatial_ids', [])))
        for sid in direct_spatial:
            provenance_edge(edges, source, node_id_map.get(sid), 'hasSpatialCoverage', 'IUENNA-collection-index', 'curated', derivation={'source': 'collection.spatial_ids'})
        for sid in aggregated_spatial:
            provenance_edge(edges, source, node_id_map.get(sid), 'hasSpatialCoverage', 'IUENNA-derived', 'aggregated', derivation={'method': 'aggregated-from-children', 'source': 'item_spatial_ids'})
        for relation_name, key in (('hasCreator', 'creators'), ('hasContributor', 'contributors')):
            for entity in col_creators.get(aid, {}).get(key, []):
                target_aid = str(entity.get('arche_id') or '')
                target = node_id_map.get(target_aid) or entity.get('id')
                provenance_edge(edges, source, target if target in registry.nodes_by_id else None, relation_name, 'IUENNA-resolved-index', 'curated', derivation={'source': 'arche_collection_creators.json'})
    for resource in corpus:
        aid = str(resource.get('arche_id'))
        source = node_id_map.get(aid)
        parent_aid = str(resource.get('col')) if resource.get('col') else None
        parent = node_id_map.get(parent_aid) if parent_aid else node_id_map.get(TOP_COLLECTION_ID)
        provenance_edge(edges, source, parent, 'isPartOf', 'ARCHE-corpus', 'asserted', derivation={'source': 'arche_corpus.json', 'field': 'col'})
        direct_spatial = ordered_unique(resource.get('spatial_ids_direct', []))
        inherited_spatial = ordered_unique(resource.get('spatial_ids_inherited', []))
        effective_spatial = ordered_unique(resource.get('spatial_ids', []))
        if not direct_spatial and (not inherited_spatial) and effective_spatial:
            if resource.get('spatial_relation_status') == 'asserted':
                direct_spatial = effective_spatial
            elif resource.get('spatial_relation_status') == 'inherited':
                inherited_spatial = effective_spatial
            else:
                inherited_spatial = effective_spatial
        for sid in direct_spatial:
            provenance_edge(edges, source, node_id_map.get(sid), 'hasSpatialCoverage', 'ARCHE-corpus', 'asserted', derivation={'source': 'resource.hasSpatialCoverage'})
        for sid in inherited_spatial:
            provenance_edge(edges, source, node_id_map.get(sid), 'hasSpatialCoverage', 'IUENNA-derived', 'inherited', derivation={'method': 'inherited-from-parent', 'inherited_from': resource.get('spatial_inherited_from') or parent_aid})
    for aid, person in persons.items():
        source = node_id_map.get(str(aid))
        aff_aid = str(person.get('affiliation_id')) if person.get('affiliation_id') else None
        provenance_edge(edges, source, node_id_map.get(aff_aid) if aff_aid else None, 'isMemberOf', 'IUENNA-resolved-index', 'curated', derivation={'source': 'arche_resolved_entities.json'})
    for aid, org in organisations.items():
        source = node_id_map.get(str(aid))
        parent_aid = str(org.get('parent_org_id')) if org.get('parent_org_id') else None
        provenance_edge(edges, source, node_id_map.get(parent_aid) if parent_aid else None, 'isMemberOf', 'IUENNA-resolved-index', 'curated', derivation={'source': 'arche_resolved_entities.json'})
    for aid, pub in publications.items():
        source = node_id_map.get(str(aid))
        for author_aid in pub.get('author_ids', []):
            provenance_edge(edges, source, node_id_map.get(str(author_aid)), 'hasAuthor', 'IUENNA-publication-index', 'curated', derivation={'source': 'arche_publications.json'})
        for documented_aid in pub.get('documents', []):
            provenance_edge(edges, source, node_id_map.get(str(documented_aid)), 'documents', 'IUENNA-publication-index', 'curated', derivation={'source': 'arche_publications.json'})
    for aid, dataset in datasets_data.items():
        source = node_id_map.get(str(aid))
        parent_aid = str(dataset.get('parent_id')) if dataset.get('parent_id') else None
        provenance_edge(edges, source, node_id_map.get(parent_aid) if parent_aid else None, 'isPartOf', 'IUENNA-dataset-index', 'curated', derivation={'source': 'arche_datasets.json'})
        for creator_aid in dataset.get('creator_ids', []):
            provenance_edge(edges, source, node_id_map.get(str(creator_aid)), 'hasCreator', 'IUENNA-dataset-index', 'curated', derivation={'source': 'arche_datasets.json'})
        for contributor_aid in dataset.get('contributor_ids', []):
            provenance_edge(edges, source, node_id_map.get(str(contributor_aid)), 'hasContributor', 'IUENNA-dataset-index', 'curated', derivation={'source': 'arche_datasets.json'})
        for sid in dataset.get('spatial_ids', []):
            provenance_edge(edges, source, node_id_map.get(str(sid)), 'hasSpatialCoverage', 'IUENNA-dataset-index', 'curated', derivation={'source': 'arche_datasets.json'})
    ttl_triples = parse_arche_relation_triples(ttl_file)
    unresolved_source_ids: Set[str] = set()
    unresolved_target_ids: Set[str] = set()
    resolvable_ttl_triples: Set[Tuple[str, str, str]] = set()
    if ttl_triples:
        print(f'[*] Injecting {len(ttl_triples)} unique ARCHE object triples...')
        for source_aid, pred, target_aid in sorted(ttl_triples):
            source = node_id_map.get(source_aid)
            target = node_id_map.get(target_aid)
            if not source:
                unresolved_source_ids.add(source_aid)
                continue
            if not target:
                unresolved_target_ids.add(target_aid)
                continue
            resolvable_ttl_triples.add((source_aid, pred, target_aid))
            provenance_edge(edges, source, target, pred, 'ARCHE-direct', 'asserted', derivation={'source': 'arche_full_metadata.ttl'})
        print(f'[✓] ARCHE pass: {len(resolvable_ttl_triples)} resolvable triples; {len(unresolved_source_ids)} unresolved sources; {len(unresolved_target_ids)} unresolved targets.')
    else:
        print('[!] arche_full_metadata.ttl not present or no target triples extracted; TTL audit disabled.')
    root_id = node_id_map.get(TOP_COLLECTION_ID, 'iuenna_root')
    for helper in epochs:
        edges.add(root_id, helper['id'], 'hasTemporalCoverage', predicate=f'{SCHEMA_BASE}hasTemporalCoverage', provenance='IUENNA-curated', relation_status='curated', semantic=False, derivation={'method': 'curated-helper'})
    for helper in subjects:
        edges.add(root_id, helper['id'], 'hasSubject', predicate=f'{SCHEMA_BASE}hasSubject', provenance='IUENNA-curated', relation_status='curated', semantic=False, derivation={'method': 'curated-helper'})
    for helper in licenses:
        edges.add(root_id, helper['id'], 'hasLicense', predicate=f'{SCHEMA_BASE}hasLicense', provenance='IUENNA-curated', relation_status='curated', semantic=False, derivation={'method': 'curated-helper'})
    place_node_ids = {node_id_map[str(aid)] for aid in places_data if str(aid) in node_id_map}
    connected_places = {edge['target'] for edge in edges.by_triple.values() if edge['target'] in place_node_ids} | {edge['source'] for edge in edges.by_triple.values() if edge['source'] in place_node_ids}
    for place_node in sorted(place_node_ids - connected_places):
        edges.add(root_id, place_node, 'connectedForNavigation', predicate='https://iuenna.github.io/vocab#connectedForNavigation', provenance='IUENNA-navigation', relation_status='synthetic', semantic=False, derivation={'method': 'layout-connectivity-fallback'})
    node_ids = set(registry.nodes_by_id)
    all_edges = list(edges.by_triple.values())
    dangling = [edge for edge in all_edges if edge['source'] not in node_ids or edge['target'] not in node_ids]
    if dangling:
        for edge in dangling:
            edges.by_triple.pop((edge['source'], edge['target'], edge['label']), None)
    macro_ids = {node_id for node_id, node in registry.nodes_by_id.items() if 'resource' not in node.get('roles', []) or 'dataset' in node.get('roles', [])}
    macro_graph = nx.Graph()
    macro_graph.add_nodes_from(macro_ids)
    for edge in edges.by_triple.values():
        if edge['source'] in macro_ids and edge['target'] in macro_ids:
            macro_graph.add_edge(edge['source'], edge['target'])
    print(f'[*] Computing macro layout for {len(macro_ids)} structural nodes...')
    pos_macro = nx.spring_layout(macro_graph, k=0.18, iterations=60, seed=42)
    scale = 3500.0
    macro_positions = {node_id: (coords[0] * scale, coords[1] * scale) for node_id, coords in pos_macro.items()}
    cytoscape_nodes = registry.as_cytoscape_nodes()
    cytoscape_by_id = {item['data']['id']: item for item in cytoscape_nodes}
    for node_id, (x, y) in macro_positions.items():
        cytoscape_by_id[node_id]['position'] = {'x': round(x, 1), 'y': round(y, 1)}
    resources_by_parent: Dict[str, List[str]] = defaultdict(list)
    for aid, resource in ((str(r.get('arche_id')), r) for r in corpus):
        node_id = node_id_map.get(aid)
        if not node_id:
            continue
        roles = registry.nodes_by_id[node_id].get('roles', [])
        if 'dataset' in roles:
            continue
        parent = registry.nodes_by_id[node_id].get('parent_col') or root_id
        resources_by_parent[parent].append(node_id)
    for parent, resource_ids in resources_by_parent.items():
        cx, cy = macro_positions.get(parent, (0.0, 0.0))
        for i, node_id in enumerate(resource_ids):
            theta = i * 2.3999632
            radius = 35.0 + 14.0 * math.sqrt(i + 1)
            cytoscape_by_id[node_id]['position'] = {'x': round(cx + radius * math.cos(theta), 1), 'y': round(cy + radius * math.sin(theta), 1)}
    cytoscape_edges = edges.as_cytoscape_edges()
    graph_asserted_arche_triples = set()
    for source_aid, pred, target_aid in resolvable_ttl_triples:
        source = node_id_map[source_aid]
        target = node_id_map[target_aid]
        edge = edges.by_triple.get((source, target, pred))
        if edge and 'ARCHE-direct' in edge.get('provenance_sources', []):
            graph_asserted_arche_triples.add((source_aid, pred, target_aid))
    predicate_audit = {}
    for pred in sorted(TTL_TARGET_PREDS):
        ttl_for_pred = {t for t in ttl_triples if t[1] == pred}
        resolvable_for_pred = {t for t in resolvable_ttl_triples if t[1] == pred}
        graph_for_pred = {t for t in graph_asserted_arche_triples if t[1] == pred}
        predicate_audit[pred] = {'ttl_triples': len(ttl_for_pred), 'resolvable_ttl_triples': len(resolvable_for_pred), 'graph_asserted_edges': len(graph_for_pred), 'recall_of_resolvable': round(len(graph_for_pred) / len(resolvable_for_pred), 6) if resolvable_for_pred else None}
    role_counts = Counter()
    type_counts = Counter()
    for node in registry.nodes_by_id.values():
        type_counts[str(node.get('type', 'unknown'))] += 1
        for role in node.get('roles', []):
            role_counts[role] += 1
    provenance_counts = Counter((edge['provenance'] for edge in edges.by_triple.values()))
    status_counts = Counter((edge['relation_status'] for edge in edges.by_triple.values()))
    label_counts = Counter((edge['label'] for edge in edges.by_triple.values()))
    final_arche_node_count = sum((1 for node in registry.nodes_by_id.values() if node.get('arche_id')))
    helper_node_count = len(registry.nodes_by_id) - final_arche_node_count
    audit = {'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'status': 'pass', 'invariants': {'one_arche_id_one_node': len(duplicate_arche_ids_final) == 0, 'no_dangling_edges': len(dangling) == 0, 'all_resolvable_ttl_relations_preserved': len(graph_asserted_arche_triples) == len(resolvable_ttl_triples) if ttl_triples else None}, 'inputs': {'collections': len(collections), 'resources': len(corpus), 'datasets': len(datasets_data), 'persons': len(persons), 'organisations': len(organisations), 'publications': len(publications), 'places': len(places_data), 'unique_arche_ids_across_input_roles': len(input_role_index), 'source_role_overlaps': source_role_overlaps, 'source_role_overlap_count': len(source_role_overlaps)}, 'graph': {'nodes': len(registry.nodes_by_id), 'arche_backed_nodes': final_arche_node_count, 'curated_helper_nodes': helper_node_count, 'edges': len(edges.by_triple), 'node_role_counts': dict(sorted(role_counts.items())), 'node_type_counts': dict(sorted(type_counts.items())), 'edge_label_counts': dict(sorted(label_counts.items())), 'edge_provenance_counts': dict(sorted(provenance_counts.items())), 'edge_relation_status_counts': dict(sorted(status_counts.items())), 'duplicate_arche_ids_final': duplicate_arche_ids_final, 'dangling_edges_removed': len(dangling)}, 'ttl_semantics': {'ttl_available': os.path.exists(ttl_file), 'target_predicates': sorted(TTL_TARGET_PREDS), 'unique_target_triples': len(ttl_triples), 'resolvable_target_triples': len(resolvable_ttl_triples), 'graph_asserted_target_edges': len(graph_asserted_arche_triples), 'unresolved_source_ids': sorted(unresolved_source_ids), 'unresolved_target_ids': sorted(unresolved_target_ids), 'predicate_audit': predicate_audit}}
    if duplicate_arche_ids_final or dangling:
        audit['status'] = 'fail'
    if ttl_triples and len(graph_asserted_arche_triples) != len(resolvable_ttl_triples):
        audit['status'] = 'fail'
    graph_payload = {'metadata': {'title': 'IUENNA ARCHE Knowledge Graph', 'description': 'Provenance-aware graph projection of IUENNA ARCHE metadata for discovery and exploration.', 'arche_uri': 'https://id.acdh.oeaw.ac.at/iuenna', 'top_collection_id': TOP_COLLECTION_ID, 'pid': 'https://hdl.handle.net/21.11115/0000-0016-7B39-F', 'generated_at': audit['generated_at'], 'total_nodes': len(registry.nodes_by_id), 'total_edges': len(edges.by_triple), 'total_arche_entities': final_arche_node_count, 'total_collections': len(collections), 'total_datasets': len(datasets_data), 'total_dataset_nodes': role_counts.get('dataset', 0), 'total_resources': role_counts.get('resource', 0), 'total_persons': len(persons), 'total_organisations': len(organisations), 'total_publications': len(publications), 'total_places': len(places_data), 'source_role_overlap_count': len(source_role_overlaps), 'ttl_semantic_recall': round(len(graph_asserted_arche_triples) / len(resolvable_ttl_triples), 6) if resolvable_ttl_triples else None, 'total_size': '356.68 GB', 'duration_seconds': round(time.time() - started, 3)}, 'elements': {'nodes': cytoscape_nodes, 'edges': cytoscape_edges}}
    out_file = os.path.join(data_dir, 'arche_graph.json')
    audit_file = os.path.join(data_dir, 'arche_graph_audit.json')
    with open(out_file, 'w', encoding='utf-8') as fh:
        json.dump(graph_payload, fh, ensure_ascii=False)
    with open(audit_file, 'w', encoding='utf-8') as fh:
        json.dump(audit, fh, ensure_ascii=False, indent=2)
    print(f'[✓] Knowledge Graph written to {out_file}')
    print(f"[✓] Graph audit written to {audit_file} (status={audit['status']})")
    print(f"[✓] Summary: {len(registry.nodes_by_id)} nodes, {len(edges.by_triple)} edges | resources={role_counts.get('resource', 0)} | datasets={role_counts.get('dataset', 0)} | merged source-role overlaps={len(source_role_overlaps)}")
    if audit['status'] != 'pass':
        raise RuntimeError('Graph audit failed; inspect data/arche_graph_audit.json')
    return graph_payload
if __name__ == '__main__':
    build_graph()
