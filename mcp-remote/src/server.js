import { McpServer } from "@modelcontextprotocol/server";
import { createMcpHandler } from "agents/mcp/server";
import { z } from "zod";

const DATA_BASE = "https://iuenna.github.io/data";
const INDEX_BASE = `${DATA_BASE}/mcp_remote`;
const VERSION = "2.0.0";
const RESOURCE_FIELDS = [
  "arche_id", "title", "filename", "type", "date", "place", "spatial_ids",
  "col", "col_id", "folder", "path", "pid", "description", "formatted_size", "size_bytes"
];

function normalize(value) {
  return String(value ?? "")
    .normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase().replace(/ß/g, "ss")
    .replace(/[^\p{L}\p{N}_]+/gu, " ").replace(/_/g, " ").trim().replace(/\s+/g, " ");
}

function fnvBucket(value) {
  let h = 0x811c9dc5;
  for (const byte of new TextEncoder().encode(String(value))) {
    h ^= byte;
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return (h & 0xff).toString(16).padStart(2, "0");
}

const prefixBucket = value => {
  const n = normalize(value);
  return fnvBucket(n.slice(0, 2) || n);
};

async function fetchJson(url, fallback = undefined) {
  const response = await fetch(url, { headers: { "User-Agent": `IUENNA-Remote-MCP/${VERSION}` } });
  if (response.status === 404 && fallback !== undefined) return fallback;
  if (!response.ok) throw new Error(`IUENNA data request failed: HTTP ${response.status} (${url})`);
  return response.json();
}
const fetchData = path => fetchJson(`${DATA_BASE}/${path}`);
const fetchIndex = (path, fallback) => fetchJson(`${INDEX_BASE}/${path}`, fallback);

function asArray(data, key = null) {
  if (key && data && typeof data === "object" && !Array.isArray(data)) data = data[key] ?? {};
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object") return Object.values(data);
  return [];
}
function normId(value) {
  let v = String(value ?? "").trim().toLowerCase();
  for (const p of ["place_", "plc_", "dts_", "col_", "pub_", "res_"]) if (v.startsWith(p)) return v.slice(p.length);
  return v;
}
const entityId = item => String(item?.arche_id ?? normId(item?.id));

async function mapLimit(items, limit, callback) {
  const out = new Array(items.length);
  let cursor = 0;
  async function runner() {
    while (true) {
      const i = cursor++;
      if (i >= items.length) return;
      out[i] = await callback(items[i], i);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, runner));
  return out;
}

function resourceFromRow(row) {
  const item = {};
  RESOURCE_FIELDS.forEach((field, i) => { if (row[i] !== null && row[i] !== undefined && row[i] !== "") item[field] = row[i]; });
  item.id = `res_${item.arche_id}`;
  item.parent_collection_id = item.col;
  item.collection_id = item.col_id;
  return item;
}

async function getNodeMeta(id) {
  const shard = await fetchIndex(`nodes/${fnvBucket(id)}.json`, { n: {} });
  const row = shard.n?.[id];
  if (!row) return null;
  return { id, arche_id: row[0], label: row[1], type: row[2], type_label: row[3], pid: row[4], parent_col: row[5] };
}

async function getNodeMetas(ids) {
  const grouped = new Map();
  for (const id of ids) {
    const bucket = fnvBucket(id);
    if (!grouped.has(bucket)) grouped.set(bucket, []);
    grouped.get(bucket).push(id);
  }
  const entries = [...grouped.entries()];
  const shards = await mapLimit(entries, 6, async ([bucket]) => fetchIndex(`nodes/${bucket}.json`, { n: {} }));
  const out = new Map();
  entries.forEach(([bucket, bucketIds], index) => {
    const records = shards[index].n ?? {};
    for (const id of bucketIds) {
      const row = records[id];
      if (row) out.set(id, { id, arche_id: row[0], label: row[1], type: row[2], type_label: row[3], pid: row[4], parent_col: row[5] });
    }
  });
  return out;
}

async function resolveNode(target) {
  const query = normalize(target);
  if (!query) return { node: null, candidateCount: 0 };
  const shard = await fetchIndex(`aliases/${prefixBucket(query)}.json`, { a: [] });
  const rows = shard.a ?? [];
  const exact = rows.filter(row => row[0] === query);
  const candidates = exact.length ? exact : rows.filter(row => row[0].startsWith(query));
  const ids = [...new Set(candidates.map(row => row[1]))];
  if (!ids.length) return { node: null, candidateCount: 0 };
  return { node: await getNodeMeta(ids[0]), candidateCount: ids.length };
}

async function searchResourceAids(query) {
  const tokens = normalize(query).split(" ").filter(t => t.length >= 2);
  if (!tokens.length) return [];
  let current = null;
  for (const token of tokens) {
    const shard = await fetchIndex(`search/${fnvBucket(token.slice(0, 2))}.json`, { t: {} });
    const union = new Set();
    for (const [term, aids] of Object.entries(shard.t ?? {})) if (term.startsWith(token)) for (const aid of aids) union.add(Number(aid));
    current = current === null ? union : new Set([...current].filter(aid => union.has(aid)));
    if (!current.size) break;
  }
  return [...(current ?? new Set())].sort((a, b) => a - b);
}

async function fetchResources(aids) {
  if (!aids.length) return [];
  const resourceMap = await fetchIndex("resource_to_collection.json");
  const groups = new Map();
  for (const aid of aids) {
    const col = resourceMap[String(aid)];
    if (!col) continue;
    if (!groups.has(col)) groups.set(col, new Set());
    groups.get(col).add(Number(aid));
  }
  const entries = [...groups.entries()];
  const shards = await mapLimit(entries, 6, async ([col]) => fetchIndex(`resources/${encodeURIComponent(col)}.json`, { r: [] }));
  const byAid = new Map();
  entries.forEach(([, wanted], index) => {
    for (const row of shards[index].r ?? []) if (wanted.has(Number(row[0]))) byAid.set(Number(row[0]), resourceFromRow(row));
  });
  return aids.map(aid => byAid.get(Number(aid))).filter(Boolean);
}

async function searchCorpus(args) {
  const query = String(args.query ?? "").trim();
  const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
  const aids = await searchResourceAids(query);
  const selected = aids.slice(0, limit);
  return { query, total_found: aids.length, returned: selected.length, results: await fetchResources(selected) };
}

async function getFindspotDetails(args) {
  const target = String(args.name_or_id ?? "").trim();
  const targetId = normId(target), targetNorm = normalize(target);
  const [placesData, datasetsData] = await Promise.all([fetchData("arche_places.json"), fetchData("arche_datasets.json")]);
  const places = asArray(placesData), datasets = asArray(datasetsData), found = [];
  for (const place of places) {
    const title = normalize(place.title ?? place.name);
    if (targetId === normId(entityId(place)) || targetNorm === title || title.startsWith(targetNorm)) {
      const pid = entityId(place);
      found.push({ ...place, datasets: datasets.filter(d => (d.spatial_ids ?? []).map(String).includes(pid)) });
    }
  }
  return found.length ? { count: found.length, findspots: found.slice(0, 5) } : { message: `No findspot matching "${target}" found.` };
}

function compactDataset(item) {
  return {
    id: item.id, arche_id: item.arche_id, title: item.title, filename: item.filename,
    description: item.description ?? "", parent_id: item.parent_id, spatial_ids: item.spatial_ids ?? [],
    documented_ids: item.documented_ids ?? [], pid: item.pid, formatted_size: item.formatted_size,
    license_summary: item.license_summary, access_restriction: item.access_restriction, citation: item.citation
  };
}
function compactCollection(item) {
  return {
    id: item.id, arche_id: item.arche_id, title: item.title, filename: item.filename,
    parent_id: item.parent_id, level: item.level, items: item.items, formatted_size: item.formatted_size,
    spatial_ids: item.spatial_ids ?? [], item_spatial_ids: item.item_spatial_ids ?? [], pid: item.pid
  };
}

async function getRelatedResources(args) {
  const target = String(args.name_or_id ?? "").trim();
  const query = String(args.query ?? "").trim();
  const limit = Math.min(Math.max(Number(args.limit) || 30, 1), 30);
  const { node, candidateCount } = await resolveNode(target);
  if (!node || !new Set(["place", "dataset", "collection", "publication"]).has(node.type)) {
    return { message: `No IUENNA place, dataset, collection, or publication matching "${target}" found.` };
  }
  const relShard = await fetchIndex(`relations/${fnvBucket(node.id)}.json`, { e: {} });
  const relation = relShard.e?.[node.id];
  if (!relation) return { message: `No IUENNA relation entry found for "${target}".` };

  const [spatialMap, collectionMap, resourceMap] = await Promise.all([
    fetchIndex("spatial_to_resources.json"), fetchIndex("collection_to_resources.json"), fetchIndex("resource_to_collection.json")
  ]);
  const related = new Set();
  for (const sid of relation.s ?? []) for (const aid of spatialMap[sid] ?? []) related.add(Number(aid));
  for (const cid of relation.c ?? []) for (const aid of collectionMap[cid] ?? []) related.add(Number(aid));

  let aids = [...related].sort((a, b) => a - b);
  if (query) {
    const matching = new Set(await searchResourceAids(query));
    aids = aids.filter(aid => matching.has(aid));
  }
  const selected = aids.slice(0, limit);
  const [datasetsData, collectionsData, publicationsData, resources] = await Promise.all([
    fetchData("arche_datasets.json"), fetchData("arche_collections_tree.json"), fetchData("arche_publications.json"), fetchResources(selected)
  ]);
  const datasetIds = new Set(relation.d ?? []), publicationIds = new Set(relation.u ?? []);
  const usedCollections = new Set(relation.c ?? []);
  for (const aid of aids) if (resourceMap[String(aid)]) usedCollections.add(resourceMap[String(aid)]);
  const datasets = asArray(datasetsData).filter(d => datasetIds.has(entityId(d))).map(compactDataset);
  const collections = asArray(collectionsData, "collections")
    .filter(c => usedCollections.has(`col_${entityId(c)}`) || usedCollections.has(entityId(c)) || usedCollections.has(c.id))
    .slice(0, 50).map(compactCollection);
  const publications = asArray(publicationsData).filter(p => publicationIds.has(entityId(p))).slice(0, 20);

  return {
    resolved_entity: { type: relation.k, arche_id: relation.a, title: relation.t, pid: relation.p, candidate_count: candidateCount },
    query: query || null,
    counts: { datasets: datasets.length, collections: collections.length, publications: publications.length, resources_total_matching: aids.length, resources_returned: selected.length },
    datasets, collections, publications, resources, truncated: aids.length > selected.length
  };
}

async function getGeodataCatalog() {
  const datasets = asArray(await fetchData("arche_datasets.json"));
  return { count: datasets.length, datasets: datasets.map(compactDataset) };
}
async function getCorpusStatistics() {
  const [stats, manifest] = await Promise.all([fetchData("arche_stats.json"), fetchIndex("manifest.json")]);
  const corpus = manifest.corpus_metadata ?? {};
  return {
    ...stats,
    count_semantics: {
      arche_collection_total_items: stats?.collection?.total_items ?? null,
      primary_resource_files: corpus.total_resources ?? manifest.resources ?? null,
      note: "ARCHE collection.total_items is a collection-wide repository item/entity count; it is not the number of primary archived files. Use primary_resource_files for the canonical file corpus."
    },
    primary_resource_corpus: corpus
  };
}
async function getProjectBibliography(args) {
  const query = String(args.query ?? "").trim();
  const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
  const url = new URL("https://api.zotero.org/groups/4910727/items");
  url.searchParams.set("format", "json"); url.searchParams.set("limit", String(limit));
  if (query) url.searchParams.set("q", query);
  const response = await fetch(url, { headers: { "User-Agent": `IUENNA-Remote-MCP/${VERSION}` } });
  if (!response.ok) throw new Error(`Zotero request failed: HTTP ${response.status}`);
  const items = await response.json();
  const results = items.map(item => {
    const d = item.data ?? {};
    return {
      key: d.key, title: d.title, itemType: d.itemType,
      creators: (d.creators ?? []).filter(c => c.lastName).map(c => `${c.lastName ?? ""} ${c.firstName ?? ""}`.trim()).join(", "),
      date: d.date, publicationTitle: d.publicationTitle || d.bookTitle, doi: d.DOI,
      url: d.url || `https://www.zotero.org/groups/4910727/iuenna/items/${d.key}`
    };
  });
  return { zotero_group_url: "https://www.zotero.org/groups/4910727/iuenna", count: results.length, items: results };
}

async function getGraphNeighborhood(args) {
  const target = String(args.node_or_id ?? "").trim();
  const predicate = String(args.predicate ?? "").trim().toLowerCase() || null;
  const direction = String(args.direction ?? "all").trim().toLowerCase();
  const limit = Math.min(Math.max(Number(args.limit) || 25, 1), 30);
  const { node } = await resolveNode(target);
  if (!node) return { message: `Node "${target}" not found in IUENNA Knowledge Graph.` };
  const shard = await fetchIndex(`graph/${fnvBucket(node.id)}.json`, { n: {} });
  const entry = shard.n?.[node.id];
  if (!entry) return { message: `Node "${target}" has no remote graph projection.` };
  const edges = entry.e ?? [], selected = [];
  let matchingCount = 0;
  for (const edge of edges) {
    const dir = edge[0] === "o" ? "outgoing" : "incoming", pred = String(edge[1] ?? "");
    if (predicate && pred.toLowerCase() !== predicate) continue;
    if ((direction === "outgoing" || direction === "incoming") && dir !== direction) continue;
    matchingCount++;
    if (selected.length < limit) selected.push({ direction: dir, predicate: pred, id: edge[2] });
  }
  const metas = await getNodeMetas(selected.map(e => e.id));
  return {
    node: { id: node.id, arche_id: node.arche_id, label: node.label, type: node.type, type_label: node.type_label, pid: node.pid },
    total_connections: edges.length, predicate_counts: entry.p ?? {}, returned_count: selected.length,
    neighbors: selected.map(e => ({ direction: e.direction, predicate: e.predicate, neighbor: metas.get(e.id) ?? { id: e.id } })),
    truncated: matchingCount > selected.length
  };
}

function toolResult(value) { return { content: [{ type: "text", text: JSON.stringify(value, null, 2) }] }; }
function createServer() {
  const server = new McpServer({ name: "IUENNA Remote MCP", version: VERSION });
  server.registerTool("search_iuenna_corpus", {
    description: "Search the authoritative IUENNA primary-resource corpus across titles, filenames, descriptions, collection paths, places, subjects, and identifiers.",
    inputSchema: { query: z.string().min(2), limit: z.number().int().min(1).max(30).optional() }
  }, async a => toolResult(await searchCorpus(a)));
  server.registerTool("get_findspot_details", {
    description: "Retrieve IUENNA findspot metadata and associated curated datasets.", inputSchema: { name_or_id: z.string().min(1) }
  }, async a => toolResult(await getFindspotDetails(a)));
  server.registerTool("get_related_resources", {
    description: "Resolve an IUENNA place, dataset, collection, or publication and return related datasets, collections, publications, and primary archived files.",
    inputSchema: { name_or_id: z.string().min(1), query: z.string().optional(), limit: z.number().int().min(1).max(30).optional() }
  }, async a => toolResult(await getRelatedResources(a)));
  server.registerTool("get_geodata_catalog", { description: "List the authoritative IUENNA archaeological GeoPackages.", inputSchema: {} }, async () => toolResult(await getGeodataCatalog()));
  server.registerTool("get_corpus_statistics", { description: "Retrieve high-level metrics of the IUENNA collection archived on ARCHE.", inputSchema: {} }, async () => toolResult(await getCorpusStatistics()));
  server.registerTool("get_project_bibliography", {
    description: "Retrieve bibliographic entries from the official IUENNA Zotero Library (Group 4910727).",
    inputSchema: { query: z.string().optional(), limit: z.number().int().min(1).max(30).optional() }
  }, async a => toolResult(await getProjectBibliography(a)));
  server.registerTool("get_graph_neighborhood", {
    description: "Traverse the IUENNA semantic knowledge graph around any indexed node.",
    inputSchema: { node_or_id: z.string().min(1), predicate: z.string().optional(), direction: z.enum(["all", "outgoing", "incoming"]).optional(), limit: z.number().int().min(1).max(30).optional() }
  }, async a => toolResult(await getGraphNeighborhood(a)));
  return server;
}

const mcpHandler = createMcpHandler(createServer);
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/mcp") return mcpHandler(request, env, ctx);
    if (url.pathname === "/" && request.method === "GET") return Response.json({
      name: "IUENNA Remote MCP", version: VERSION, status: "ok", endpoint: "/mcp",
      documentation: "https://iuenna.github.io/byoai.html", transport: "Streamable HTTP",
      authentication: "none", access: "public read-only"
    });
    return new Response("Not found", { status: 404 });
  }
};
