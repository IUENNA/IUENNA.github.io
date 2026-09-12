import { McpServer } from "@modelcontextprotocol/server";
import { createMcpHandler } from "agents/mcp/server";
import { z } from "zod";

const DATA_BASE = "https://iuenna.github.io/data";
const INDEX_BASE = `${DATA_BASE}/mcp_remote`;
const VERSION = "2.0.0";

function normalize(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/ß/g, "ss")
    .replace(/[^\p{L}\p{N}_]+/gu, " ")
    .replace(/_/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

function fnvBucket(value) {
  let h = 0x811c9dc5;
  const bytes = new TextEncoder().encode(String(value));
  for (const byte of bytes) {
    h ^= byte;
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return (h & 0xff).toString(16).padStart(2, "0");
}

const graphBucket = value => fnvBucket(String(value));
const prefixBucket = value => {
  const n = normalize(value);
  return fnvBucket(n.slice(0, 2) || n);
};

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: { "User-Agent": `IUENNA-Remote-MCP/${VERSION}` }
  });
  if (!response.ok) throw new Error(`IUENNA data request failed: HTTP ${response.status} (${url})`);
  return response.json();
}

const fetchData = path => fetchJson(`${DATA_BASE}/${path}`);
const fetchIndex = path => fetchJson(`${INDEX_BASE}/${path}`);

function asArray(data, key = null) {
  if (key && data && typeof data === "object" && !Array.isArray(data)) data = data[key] ?? {};
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object") return Object.values(data);
  return [];
}

function normId(value) {
  let v = String(value ?? "").trim().toLowerCase();
  for (const prefix of ["place_", "plc_", "dts_", "col_", "pub_", "res_"]) {
    if (v.startsWith(prefix)) return v.slice(prefix.length);
  }
  return v;
}

const entityId = item => String(item?.arche_id ?? normId(item?.id));

async function mapLimit(items, limit, callback) {
  const out = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (true) {
      const index = cursor++;
      if (index >= items.length) return;
      out[index] = await callback(items[index], index);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => worker()));
  return out;
}

async function resolveNode(target) {
  const query = normalize(target);
  if (!query) return { node: null, candidateCount: 0 };
  const shard = await fetchIndex(`lookup/${prefixBucket(query)}.json`);
  const records = shard.aliases ?? [];
  const exact = records.filter(row => row[0] === query);
  const candidates = exact.length ? exact : records.filter(row => row[0].startsWith(query));
  if (!candidates.length) return { node: null, candidateCount: 0 };

  const unique = [];
  const seen = new Set();
  for (const row of candidates) {
    if (!seen.has(row[1])) {
      seen.add(row[1]);
      unique.push(row);
    }
  }
  const row = unique[0];
  return {
    candidateCount: unique.length,
    node: {
      alias: row[0], id: row[1], arche_id: row[2], label: row[3], type: row[4],
      type_label: row[5], pid: row[6], parent_col: row[7]
    }
  };
}

async function searchResourceIds(query) {
  const tokens = normalize(query).split(" ").filter(token => token.length >= 2);
  if (!tokens.length) return [];

  let current = null;
  for (const token of tokens) {
    const shard = await fetchIndex(`search/${fnvBucket(token.slice(0, 2))}.json`);
    const union = new Set();
    for (const [term, ids] of Object.entries(shard.terms ?? {})) {
      if (term.startsWith(token)) {
        for (const id of ids) union.add(id);
      }
    }
    if (current === null) current = union;
    else current = new Set([...current].filter(id => union.has(id)));
    if (!current.size) break;
  }
  return [...(current ?? new Set())];
}

async function fetchResources(resourceIds) {
  if (!resourceIds.length) return [];
  const resourceMap = await fetchIndex("resource_to_collection.json");
  const groups = new Map();
  for (const id of resourceIds) {
    const collectionId = resourceMap[id];
    if (!collectionId) continue;
    if (!groups.has(collectionId)) groups.set(collectionId, []);
    groups.get(collectionId).push(id);
  }

  const entries = [...groups.entries()];
  const shards = await mapLimit(entries, 6, async ([collectionId]) =>
    fetchIndex(`resources/${encodeURIComponent(collectionId)}.json`)
  );
  const byId = new Map();
  for (const shard of shards) {
    for (const resource of shard.resources ?? []) byId.set(resource.id, resource);
  }
  return resourceIds.map(id => byId.get(id)).filter(Boolean);
}

async function searchCorpus(args) {
  const query = String(args.query ?? "").trim();
  const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
  const ids = await searchResourceIds(query);
  const selected = ids.slice(0, limit);
  return {
    query,
    total_found: ids.length,
    returned: selected.length,
    results: await fetchResources(selected)
  };
}

async function getFindspotDetails(args) {
  const target = String(args.name_or_id ?? "").trim();
  const targetId = normId(target);
  const targetNorm = normalize(target);
  const [placesData, datasetsData] = await Promise.all([
    fetchData("arche_places.json"),
    fetchData("arche_datasets.json")
  ]);
  const places = asArray(placesData);
  const datasets = asArray(datasetsData);
  const found = [];
  for (const place of places) {
    const title = normalize(place.title ?? place.name);
    if (targetId === normId(entityId(place)) || targetNorm === title || title.startsWith(targetNorm)) {
      const item = { ...place };
      const pid = entityId(place);
      item.datasets = datasets.filter(d => (d.spatial_ids ?? []).map(String).includes(pid));
      found.push(item);
    }
  }
  return found.length
    ? { count: found.length, findspots: found.slice(0, 5) }
    : { message: `No findspot matching "${target}" found.` };
}

async function getRelatedResources(args) {
  const target = String(args.name_or_id ?? "").trim();
  const query = String(args.query ?? "").trim();
  const limit = Math.min(Math.max(Number(args.limit) || 30, 1), 30);
  const { node, candidateCount } = await resolveNode(target);
  const allowed = new Set(["place", "dataset", "collection", "publication"]);
  if (!node || !allowed.has(node.type)) {
    return { message: `No IUENNA place, dataset, collection, or publication matching "${target}" found.` };
  }

  const shard = await fetchIndex(`relations/${graphBucket(node.id)}.json`);
  const relation = shard.entities?.[node.id];
  if (!relation) return { message: `No precomputed IUENNA relation entry found for "${target}".` };

  let ids = relation.resource_ids ?? [];
  if (query) {
    const matching = new Set(await searchResourceIds(query));
    ids = ids.filter(id => matching.has(id));
  }
  const selected = ids.slice(0, limit);
  return {
    resolved_entity: { ...relation.resolved_entity, candidate_count: candidateCount },
    query: query || null,
    counts: {
      datasets: (relation.datasets ?? []).length,
      collections: (relation.collections ?? []).length,
      publications: (relation.publications ?? []).length,
      resources_total_matching: ids.length,
      resources_returned: selected.length
    },
    datasets: relation.datasets ?? [],
    collections: relation.collections ?? [],
    publications: relation.publications ?? [],
    resources: await fetchResources(selected),
    truncated: ids.length > selected.length
  };
}

async function getGeodataCatalog() {
  const datasets = asArray(await fetchData("arche_datasets.json"));
  return { count: datasets.length, datasets };
}

async function getCorpusStatistics() {
  const [stats, manifest] = await Promise.all([
    fetchData("arche_stats.json"),
    fetchIndex("manifest.json")
  ]);
  return { ...stats, primary_resource_corpus: manifest.corpus_metadata ?? {} };
}

async function getProjectBibliography(args) {
  const query = String(args.query ?? "").trim();
  const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
  const url = new URL("https://api.zotero.org/groups/4910727/items");
  url.searchParams.set("format", "json");
  url.searchParams.set("limit", String(limit));
  if (query) url.searchParams.set("q", query);
  const response = await fetch(url, { headers: { "User-Agent": `IUENNA-Remote-MCP/${VERSION}` } });
  if (!response.ok) throw new Error(`Zotero request failed: HTTP ${response.status}`);
  const items = await response.json();
  const results = items.map(item => {
    const data = item.data ?? {};
    const creators = (data.creators ?? [])
      .filter(c => c.lastName)
      .map(c => `${c.lastName ?? ""} ${c.firstName ?? ""}`.trim())
      .join(", ");
    return {
      key: data.key, title: data.title, itemType: data.itemType, creators,
      date: data.date, publicationTitle: data.publicationTitle || data.bookTitle,
      doi: data.DOI,
      url: data.url || `https://www.zotero.org/groups/4910727/iuenna/items/${data.key}`
    };
  });
  return {
    zotero_group_url: "https://www.zotero.org/groups/4910727/iuenna",
    count: results.length,
    items: results
  };
}

async function getGraphNeighborhood(args) {
  const target = String(args.node_or_id ?? "").trim();
  const predicate = String(args.predicate ?? "").trim().toLowerCase() || null;
  const direction = String(args.direction ?? "all").trim().toLowerCase();
  const limit = Math.min(Math.max(Number(args.limit) || 25, 1), 100);
  const { node } = await resolveNode(target);
  if (!node) return { message: `Node "${target}" not found in IUENNA Knowledge Graph.` };

  const shard = await fetchIndex(`graph/${graphBucket(node.id)}.json`);
  const entry = shard.nodes?.[node.id];
  if (!entry) return { message: `Node "${target}" has no remote graph projection.` };
  const edges = entry.e ?? [];
  const filtered = [];
  let matchingCount = 0;
  for (const edge of edges) {
    const dir = edge[0] === "o" ? "outgoing" : "incoming";
    const pred = String(edge[1] ?? "");
    if (predicate && pred.toLowerCase() !== predicate) continue;
    if ((direction === "outgoing" || direction === "incoming") && dir !== direction) continue;
    matchingCount += 1;
    if (filtered.length < limit) {
      filtered.push({
        direction: dir,
        predicate: pred,
        neighbor: {
          id: edge[2], arche_id: edge[3], label: edge[4], type: edge[5],
          type_label: edge[6], pid: edge[7]
        }
      });
    }
  }

  return {
    node: {
      id: entry.n?.[0], arche_id: entry.n?.[1], label: entry.n?.[2],
      type: entry.n?.[3], type_label: entry.n?.[4], pid: entry.n?.[5]
    },
    total_connections: edges.length,
    predicate_counts: entry.pc ?? {},
    returned_count: filtered.length,
    neighbors: filtered,
    truncated: matchingCount > filtered.length
  };
}

function toolResult(value) {
  return { content: [{ type: "text", text: JSON.stringify(value, null, 2) }] };
}

function createServer() {
  const server = new McpServer({ name: "IUENNA Remote MCP", version: VERSION });

  server.registerTool("search_iuenna_corpus", {
    description: "Search the authoritative IUENNA primary-resource corpus across titles, filenames, descriptions, collection paths, places, subjects, and identifiers.",
    inputSchema: {
      query: z.string().min(2).describe("Search terms, e.g. Georadar Hemmaberg or Münzen Globasnitz."),
      limit: z.number().int().min(1).max(30).optional().describe("Maximum results; default 10, max 30.")
    }
  }, async args => toolResult(await searchCorpus(args)));

  server.registerTool("get_findspot_details", {
    description: "Retrieve IUENNA findspot metadata and associated curated datasets.",
    inputSchema: { name_or_id: z.string().min(1).describe("Findspot name or ARCHE ID.") }
  }, async args => toolResult(await getFindspotDetails(args)));

  server.registerTool("get_related_resources", {
    description: "Resolve an IUENNA place, dataset, collection, or publication and return related datasets, collections, publications, and primary archived files.",
    inputSchema: {
      name_or_id: z.string().min(1).describe("Entity title or ARCHE ID."),
      query: z.string().optional().describe("Optional resource filter such as Georadar, Interpretation, Grab, or 2015."),
      limit: z.number().int().min(1).max(30).optional().describe("Maximum primary resources; default/max 30 for remote MCP efficiency.")
    }
  }, async args => toolResult(await getRelatedResources(args)));

  server.registerTool("get_geodata_catalog", {
    description: "List the authoritative IUENNA archaeological GeoPackages.",
    inputSchema: {}
  }, async () => toolResult(await getGeodataCatalog()));

  server.registerTool("get_corpus_statistics", {
    description: "Retrieve high-level metrics of the IUENNA collection archived on ARCHE.",
    inputSchema: {}
  }, async () => toolResult(await getCorpusStatistics()));

  server.registerTool("get_project_bibliography", {
    description: "Retrieve bibliographic entries from the official IUENNA Zotero Library (Group 4910727).",
    inputSchema: {
      query: z.string().optional().describe("Optional author, keyword, or site filter."),
      limit: z.number().int().min(1).max(30).optional().describe("Maximum items; default 10, max 30.")
    }
  }, async args => toolResult(await getProjectBibliography(args)));

  server.registerTool("get_graph_neighborhood", {
    description: "Traverse the IUENNA semantic knowledge graph around an entity, place, person, dataset, publication, collection, or primary resource.",
    inputSchema: {
      node_or_id: z.string().min(1).describe("Node label, entity name, file name, node ID, or ARCHE ID."),
      predicate: z.string().optional().describe("Optional edge predicate filter, e.g. hasCreator or hasSpatialCoverage."),
      direction: z.enum(["all", "outgoing", "incoming"]).optional().describe("Edge direction; default all."),
      limit: z.number().int().min(1).max(100).optional().describe("Maximum neighbors; default 25, max 100.")
    }
  }, async args => toolResult(await getGraphNeighborhood(args)));

  return server;
}

const mcpHandler = createMcpHandler(createServer);

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/mcp") return mcpHandler(request, env, ctx);
    if (url.pathname === "/" && request.method === "GET") {
      return Response.json({
        name: "IUENNA Remote MCP",
        version: VERSION,
        status: "ok",
        endpoint: "/mcp",
        documentation: "https://iuenna.github.io/byoai.html",
        transport: "Streamable HTTP",
        authentication: "none",
        access: "public read-only"
      });
    }
    return new Response("Not found", { status: 404 });
  }
};
