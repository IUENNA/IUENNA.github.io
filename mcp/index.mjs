#!/usr/bin/env node

/** IUENNA Model Context Protocol server – Node.js implementation. */
import * as readline from 'node:readline';

const BASE_URL = 'https://iuenna.github.io/data';
const CACHE = new Map();

async function fetchJson(endpoint) {
  if (CACHE.has(endpoint)) return CACHE.get(endpoint);
  const res = await fetch(`${BASE_URL}/${endpoint}`, {
    headers: { 'User-Agent': 'IUENNA-MCP-Server/1.1' }
  });
  if (!res.ok) throw new Error(`Failed to fetch ${endpoint}: HTTP ${res.status}`);
  const data = await res.json();
  CACHE.set(endpoint, data);
  return data;
}

function asArray(data, key = null) {
  if (key && data && typeof data === 'object' && !Array.isArray(data)) data = data[key] ?? {};
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') return Object.values(data);
  return [];
}

function normId(value) {
  let v = String(value ?? '').trim().toLowerCase();
  for (const p of ['place_', 'plc_', 'dts_', 'col_', 'pub_', 'res_']) {
    if (v.startsWith(p)) return v.slice(p.length);
  }
  return v;
}

const entityId = item => String(item?.arche_id ?? normId(item?.id));

function searchable(item) {
  const fields = [
    item?.title, item?.name, item?.filename, item?.description,
    item?.breadcrumb, item?.folder, item?.folder_code, item?.place,
    item?.alternative_title, item?.pid
  ];
  for (const key of ['path', 'subjs', 'subjects', 'alternative_titles']) {
    const value = item?.[key];
    if (Array.isArray(value)) fields.push(...value);
    else if (value) fields.push(value);
  }
  return fields.filter(Boolean).join(' ').toLowerCase();
}

const matchesTokens = (item, tokens) => tokens.every(t => searchable(item).includes(t));

function compactResource(item) {
  return {
    id: item.id,
    arche_id: item.arche_id,
    title: item.title,
    filename: item.filename,
    type: item.type,
    date: item.date,
    place: item.place,
    spatial_ids: item.spatial_ids ?? [],
    parent_collection_id: item.col,
    folder: item.folder,
    path: item.path ?? [],
    pid: item.pid,
    description: item.description ?? ''
  };
}

function compactDataset(item) {
  return {
    id: item.id,
    arche_id: item.arche_id,
    title: item.title,
    filename: item.filename,
    description: item.description ?? '',
    parent_id: item.parent_id,
    spatial_ids: item.spatial_ids ?? [],
    documented_ids: item.documented_ids ?? [],
    pid: item.pid,
    formatted_size: item.formatted_size,
    license_summary: item.license_summary,
    access_restriction: item.access_restriction,
    citation: item.citation
  };
}

function compactCollection(item) {
  return {
    id: item.id,
    arche_id: item.arche_id,
    title: item.title,
    filename: item.filename,
    parent_id: item.parent_id,
    level: item.level,
    items: item.items,
    formatted_size: item.formatted_size,
    spatial_ids: item.spatial_ids ?? [],
    item_spatial_ids: item.item_spatial_ids ?? [],
    pid: item.pid
  };
}

function descendants(collectionsById, roots) {
  const out = new Set([...roots].filter(Boolean).map(String));
  let changed = true;
  while (changed) {
    changed = false;
    for (const [cid, item] of collectionsById.entries()) {
      if (out.has(String(item.parent_id ?? '')) && !out.has(cid)) {
        out.add(cid);
        changed = true;
      }
    }
  }
  return out;
}

function resolveEntity(target, places, datasets, collections, publications) {
  const query = String(target ?? '').trim().toLowerCase();
  const normalized = normId(query);
  const pools = [
    ['place', places], ['dataset', datasets],
    ['collection', collections], ['publication', publications]
  ];
  const partial = [];

  for (const [kind, items] of pools) {
    for (const item of items) {
      const labels = [item.title, item.name, item.filename, item.alternative_title, ...(item.alternative_titles ?? [])]
        .filter(Boolean).map(v => String(v).trim().toLowerCase());
      if (normalized && normalized === normId(entityId(item))) return { resolved: [kind, item], candidateCount: 1 };
      if (query && labels.includes(query)) return { resolved: [kind, item], candidateCount: 1 };
      if (query && labels.some(label => label.includes(query))) partial.push([kind, item]);
    }
  }
  return partial.length
    ? { resolved: partial[0], candidateCount: partial.length }
    : { resolved: null, candidateCount: 0 };
}

async function getRelatedResources(args = {}) {
  const target = String(args.name_or_id ?? '').trim();
  const query = String(args.query ?? '').trim();
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
  const limit = Math.min(Math.max(Number(args.limit) || 50, 1), 100);

  const [placesData, datasetsData, tree, publicationsData, corpus] = await Promise.all([
    fetchJson('arche_places.json'),
    fetchJson('arche_datasets.json'),
    fetchJson('arche_collections_tree.json'),
    fetchJson('arche_publications.json'),
    fetchJson('arche_corpus.json')
  ]);

  const places = asArray(placesData);
  const datasets = asArray(datasetsData);
  const collections = asArray(tree, 'collections');
  const publications = asArray(publicationsData);
  const resources = asArray(corpus, 'resources');
  const collectionsById = new Map(collections.map(c => [entityId(c), c]));

  const { resolved, candidateCount } = resolveEntity(target, places, datasets, collections, publications);
  if (!resolved) return { message: `No IUENNA place, dataset, collection, or publication matching "${target}" found.` };

  const [kind, entity] = resolved;
  const eid = entityId(entity);
  const title = entity.title ?? entity.name ?? entity.filename ?? target;
  const spatial = new Set();
  const collectionRoots = new Set();
  const publicationIds = new Set();
  const datasetIds = new Set();

  if (kind === 'place') spatial.add(eid);
  else if (kind === 'dataset') {
    datasetIds.add(eid);
    (entity.spatial_ids ?? []).forEach(v => spatial.add(String(v)));
    if (entity.parent_id) collectionRoots.add(String(entity.parent_id));
    (entity.documented_ids ?? []).forEach(v => publicationIds.add(String(v)));
  } else if (kind === 'collection') {
    collectionRoots.add(eid);
    (entity.spatial_ids ?? []).forEach(v => spatial.add(String(v)));
    (entity.item_spatial_ids ?? []).forEach(v => spatial.add(String(v)));
  } else publicationIds.add(eid);

  if (kind === 'publication') {
    for (const dataset of datasets) {
      if ((dataset.documented_ids ?? []).map(String).includes(eid)) {
        datasetIds.add(entityId(dataset));
        (dataset.spatial_ids ?? []).forEach(v => spatial.add(String(v)));
        if (dataset.parent_id) collectionRoots.add(String(dataset.parent_id));
      }
    }
  }

  let collectionIds = descendants(collectionsById, collectionRoots);
  const relatedDatasets = datasets.filter(dataset => {
    const did = entityId(dataset);
    const dSpatial = new Set((dataset.spatial_ids ?? []).map(String));
    const dDocs = new Set((dataset.documented_ids ?? []).map(String));
    const related = datasetIds.has(did)
      || [...spatial].some(v => dSpatial.has(v))
      || collectionIds.has(String(dataset.parent_id ?? ''))
      || [...publicationIds].some(v => dDocs.has(v));
    return related && (!tokens.length || matchesTokens(dataset, tokens) || datasetIds.has(did));
  });

  for (const dataset of relatedDatasets) {
    datasetIds.add(entityId(dataset));
    (dataset.spatial_ids ?? []).forEach(v => spatial.add(String(v)));
    (dataset.documented_ids ?? []).forEach(v => publicationIds.add(String(v)));
    if (dataset.parent_id) collectionRoots.add(String(dataset.parent_id));
  }
  collectionIds = descendants(collectionsById, collectionRoots);

  const relatedFiles = resources.filter(resource => {
    const rSpatial = new Set((resource.spatial_ids ?? []).map(String));
    let related = [...spatial].some(v => rSpatial.has(v)) || collectionIds.has(String(resource.col ?? ''));
    if (kind === 'place' && String(resource.place ?? '').toLowerCase() === String(title).toLowerCase()) related = true;
    return related && (!tokens.length || matchesTokens(resource, tokens));
  });

  relatedFiles.sort((a, b) => {
    const pa = (a.path ?? []).join(' / ');
    const pb = (b.path ?? []).join(' / ');
    return pa.localeCompare(pb) || String(a.title ?? '').localeCompare(String(b.title ?? ''));
  });

  const usedCollections = new Set(relatedFiles.map(r => String(r.col ?? '')).filter(Boolean));
  collectionIds.forEach(v => usedCollections.add(v));
  const relatedCollections = collections.filter(c => usedCollections.has(entityId(c)));
  const relatedPublications = publications.filter(p => publicationIds.has(entityId(p)));

  return {
    resolved_entity: {
      type: kind,
      arche_id: eid,
      title,
      pid: entity.pid ?? null,
      candidate_count: candidateCount
    },
    query: query || null,
    counts: {
      datasets: relatedDatasets.length,
      collections: relatedCollections.length,
      publications: relatedPublications.length,
      resources_total_matching: relatedFiles.length,
      resources_returned: Math.min(relatedFiles.length, limit)
    },
    datasets: relatedDatasets.map(compactDataset),
    collections: relatedCollections.slice(0, 50).map(compactCollection),
    publications: relatedPublications.slice(0, 20),
    resources: relatedFiles.slice(0, limit).map(compactResource),
    truncated: relatedFiles.length > limit
  };
}

const TOOLS = [
  {
    name: 'search_iuenna_corpus',
    description: 'Search the authoritative IUENNA primary-resource corpus (20,355 archived files) across titles, filenames, descriptions, collection paths, places, subjects, and PIDs.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search terms, e.g. Georadar Hemmaberg or Münzen Globasnitz.' },
        limit: { type: 'number', description: 'Maximum results (default 10, max 30).' }
      },
      required: ['query']
    }
  },
  {
    name: 'get_findspot_details',
    description: 'Retrieve findspot metadata and associated curated datasets for one of the recorded findspots in the Southern Jauntal.',
    inputSchema: {
      type: 'object',
      properties: { name_or_id: { type: 'string', description: 'Findspot name or ARCHE ID.' } },
      required: ['name_or_id']
    }
  },
  {
    name: 'get_related_resources',
    description: 'Resolve an IUENNA place, dataset, collection, or publication and return related datasets, collections, publications, and primary archived files.',
    inputSchema: {
      type: 'object',
      properties: {
        name_or_id: { type: 'string', description: 'Entity title or ARCHE ID.' },
        query: { type: 'string', description: 'Optional resource filter such as Georadar, Interpretation, Grab, or 2015.' },
        limit: { type: 'number', description: 'Maximum primary resources (default 50, max 100).' }
      },
      required: ['name_or_id']
    }
  },
  { name: 'get_geodata_catalog', description: 'List the 9 authoritative IUENNA archaeological GeoPackages.', inputSchema: { type: 'object', properties: {} } },
  { name: 'get_corpus_statistics', description: 'Retrieve high-level metrics of the IUENNA collection archived on ARCHE.', inputSchema: { type: 'object', properties: {} } },
  {
    name: 'get_project_bibliography',
    description: 'Retrieve bibliographic entries from the official IUENNA Zotero Library (Group 4910727).',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Optional author, keyword, or site filter.' },
        limit: { type: 'number', description: 'Maximum items (default 10, max 30).' }
      }
    }
  },
  {
    name: 'get_graph_neighborhood',
    description: 'Query the IUENNA Knowledge Graph (21,080 nodes, 38,696 edges) to traverse semantic relationships. Returns connected nodes, edge predicates (hasCreator, hasAuthor, hasSpatialCoverage, documents, isPartOf, isMemberOf), and neighbor entities.',
    inputSchema: {
      type: 'object',
      properties: {
        node_or_id: { type: 'string', description: "Node label, entity name (e.g. 'Franz Glaser', 'Hemmaberg', 'glo_geodaten_open.gpkg'), or ARCHE ID (e.g. '1756744', 'plc_1756734')." },
        predicate: { type: 'string', description: "Optional edge predicate filter (e.g. 'hasCreator', 'hasAuthor', 'hasSpatialCoverage', 'documents', 'isPartOf', 'isMemberOf')." },
        direction: { type: 'string', enum: ['all', 'outgoing', 'incoming'], description: "Edge direction to follow (default: 'all')." },
        limit: { type: 'number', description: 'Maximum number of connected neighbor nodes to return (default: 25, max: 100).' }
      },
      required: ['node_or_id']
    }
  }
];

let graphCache = null;

async function getGraphIndex() {
  if (graphCache) return graphCache;
  const rawGraph = await fetchJson('arche_graph.json');
  const nodesById = new Map();
  const nodesByArcheId = new Map();
  const nodesList = [];

  for (const n of (rawGraph?.elements?.nodes || [])) {
    const d = n.data || {};
    const nid = String(d.id || '').trim();
    nodesById.set(nid, d);
    if (d.arche_id) nodesByArcheId.set(String(d.arche_id), d);
    nodesList.push(d);
  }

  const adj = new Map();
  for (const e of (rawGraph?.elements?.edges || [])) {
    const ed = e.data || {};
    const src = String(ed.source || '').trim();
    const tgt = String(ed.target || '').trim();
    const lbl = ed.label || '';
    const pred = ed.predicate || '';

    if (!adj.has(src)) adj.set(src, []);
    if (!adj.has(tgt)) adj.set(tgt, []);

    adj.get(src).push({ dir: 'outgoing', neighborId: tgt, predicate: lbl, uri: pred });
    adj.get(tgt).push({ dir: 'incoming', neighborId: src, predicate: lbl, uri: pred });
  }

  graphCache = { nodesById, nodesByArcheId, nodesList, adj };
  return graphCache;
}

async function executeTool(name, args = {}) {
  if (name === 'search_iuenna_corpus') {
    const query = String(args.query ?? '').trim();
    const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
    const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
    const resources = asArray(await fetchJson('arche_corpus.json'), 'resources');
    const found = resources.filter(r => matchesTokens(r, tokens));
    return {
      query,
      total_found: found.length,
      returned: Math.min(found.length, limit),
      results: found.slice(0, limit).map(compactResource)
    };
  }

  if (name === 'get_findspot_details') {
    const target = String(args.name_or_id ?? '').trim();
    const targetId = normId(target);
    const targetLc = target.toLowerCase();
    const [placesData, datasetsData] = await Promise.all([
      fetchJson('arche_places.json'), fetchJson('arche_datasets.json')
    ]);
    const places = asArray(placesData);
    const datasets = asArray(datasetsData);
    const found = places.filter(place => {
      const title = String(place.title ?? '').toLowerCase();
      return targetId === normId(entityId(place)) || targetLc === title || title.includes(targetLc);
    }).map(place => {
      const pid = entityId(place);
      return {
        ...place,
        datasets: datasets
          .filter(d => (d.spatial_ids ?? []).map(String).includes(pid))
          .map(compactDataset)
      };
    });
    return found.length
      ? { count: found.length, findspots: found.slice(0, 5) }
      : { message: `No findspot matching "${target}" found.` };
  }

  if (name === 'get_related_resources') return await getRelatedResources(args);

  if (name === 'get_geodata_catalog') {
    const datasets = asArray(await fetchJson('arche_datasets.json'));
    return { count: datasets.length, datasets: datasets.map(compactDataset) };
  }

  if (name === 'get_corpus_statistics') {
    const [stats, corpus] = await Promise.all([
      fetchJson('arche_stats.json'), fetchJson('arche_corpus.json')
    ]);
    return { ...stats, primary_resource_corpus: corpus.metadata ?? {} };
  }

  if (name === 'get_project_bibliography') {
    const q = String(args.query ?? '').trim();
    const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
    let url = `https://api.zotero.org/groups/4910727/items?format=json&limit=${limit}`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'IUENNA-MCP-Server/1.1' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const items = await res.json();
      return {
        zotero_group_url: 'https://www.zotero.org/groups/4910727/iuenna',
        count: items.length,
        items: items.map(it => {
          const d = it.data ?? {};
          const creators = (d.creators ?? []).filter(c => c.lastName)
            .map(c => `${c.lastName} ${c.firstName ?? ''}`.trim()).join(', ');
          return {
            key: d.key,
            title: d.title,
            itemType: d.itemType,
            creators,
            date: d.date,
            publicationTitle: d.publicationTitle || d.bookTitle || null,
            doi: d.DOI || null,
            url: d.url || `https://www.zotero.org/groups/4910727/iuenna/items/${d.key}`
          };
        })
      };
    } catch (err) {
      return {
        error: `Failed to query Zotero API: ${err.message}`,
        zotero_web: 'https://www.zotero.org/groups/4910727/iuenna'
      };
    }
  }

  if (name === 'get_graph_neighborhood') {
    const target = String(args.node_or_id || '').trim();
    const predicate = String(args.predicate || '').trim().toLowerCase() || null;
    const direction = String(args.direction || 'all').trim().toLowerCase();
    const limit = Math.min(Math.max(Number(args.limit) || 25, 1), 100);

    const { nodesById, nodesByArcheId, nodesList, adj } = await getGraphIndex();
    const tLc = target.toLowerCase();
    const tNorm = normId(tLc);

    let matched = nodesById.get(tLc) || nodesByArcheId.get(tNorm);
    if (!matched) {
      for (const n of nodesList) {
        const lbl = (n.label || n.title || '').toLowerCase();
        const aid = String(n.arche_id || '').toLowerCase();
        const nid = String(n.id || '').toLowerCase();
        if (tLc === lbl || tLc === aid || tLc === nid || tNorm === aid) {
          matched = n;
          break;
        }
      }
      if (!matched) {
        for (const n of nodesList) {
          const lbl = (n.label || n.title || '').toLowerCase();
          if (lbl.includes(tLc)) {
            matched = n;
            break;
          }
        }
      }
    }

    if (!matched) {
      return { message: `Node "${target}" not found in IUENNA Knowledge Graph.` };
    }

    const nid = matched.id;
    const edges = adj.get(nid) || [];
    const predCounts = {};
    for (const e of edges) {
      predCounts[e.predicate] = (predCounts[e.predicate] || 0) + 1;
    }

    const filtered = [];
    for (const e of edges) {
      if (predicate && predicate !== e.predicate.toLowerCase()) continue;
      if ((direction === 'outgoing' || direction === 'incoming') && direction !== e.dir) continue;
      const nbNode = nodesById.get(e.neighborId) || {};
      filtered.push({
        direction: e.dir,
        predicate: e.predicate,
        neighbor: {
          id: nbNode.id,
          arche_id: nbNode.arche_id,
          label: nbNode.label || nbNode.title,
          type: nbNode.type,
          type_label: nbNode.type_label,
          pid: nbNode.pid
        }
      });
    }

    return {
      node: {
        id: matched.id,
        arche_id: matched.arche_id,
        label: matched.label || matched.title,
        type: matched.type,
        type_label: matched.type_label,
        pid: matched.pid
      },
      total_connections: edges.length,
      predicate_counts: predCounts,
      returned_count: Math.min(filtered.length, limit),
      neighbors: filtered.slice(0, limit),
      truncated: filtered.length > limit
    };
  }

  throw new Error(`Unknown tool: ${name}`);
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false });
const send = response => process.stdout.write(JSON.stringify(response) + '\n');

rl.on('line', async line => {
  if (!line.trim()) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return; }
  const { id, method, params } = msg;

  if (method === 'initialize') {
    send({
      jsonrpc: '2.0', id,
      result: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: 'iuenna-mcp', version: '1.1.0' }
      }
    });
    return;
  }
  if (method === 'notifications/initialized') return;
  if (method === 'tools/list') {
    send({ jsonrpc: '2.0', id, result: { tools: TOOLS } });
    return;
  }
  if (method === 'tools/call') {
    const { name, arguments: args } = params ?? {};
    try {
      const result = await executeTool(name, args ?? {});
      send({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] } });
    } catch (err) {
      send({ jsonrpc: '2.0', id, error: { code: -32000, message: err.message || 'Internal tool execution error' } });
    }
    return;
  }
  if (id !== undefined) send({ jsonrpc: '2.0', id, error: { code: -32601, message: `Method not found: ${method}` } });
});
