#!/usr/bin/env node

/**
 * IUENNA Model Context Protocol (MCP) Server
 * -------------------------------------------
 * An open-standard Model Context Protocol server exposing authoritative
 * archaeological data from the IUENNA research project (Southern Jauntal, Carinthia).
 * 
 * Works out-of-the-box with:
 * - Claude Desktop
 * - Open-WebUI
 * - LibreChat
 * - Cursor, Zed & Antigravity
 * - Custom LangChain / LlamaIndex / Python agents
 * 
 * Protocol: JSON-RPC 2.0 over Stdio (zero third-party dependencies required).
 */

import * as readline from 'node:readline';

const BASE_URL = 'https://iuenna.github.io/data';

// Cache in-memory
let placesCache = null;
let searchIndexCache = null;
let datasetsCache = null;
let collectionsTreeCache = null;

async function fetchJson(endpoint) {
  const res = await fetch(`${BASE_URL}/${endpoint}`);
  if (!res.ok) throw new Error(`Failed to fetch ${endpoint}: HTTP ${res.status}`);
  return await res.json();
}

async function getPlaces() {
  if (!placesCache) placesCache = await fetchJson('arche_places.json');
  return placesCache;
}

async function getSearchIndex() {
  if (!searchIndexCache) searchIndexCache = await fetchJson('arche_search_index.json');
  return searchIndexCache;
}

async function getDatasets() {
  if (!datasetsCache) datasetsCache = await fetchJson('arche_datasets.json');
  return datasetsCache;
}

async function getCollectionsTree() {
  if (!collectionsTreeCache) collectionsTreeCache = await fetchJson('arche_collections_tree.json');
  return collectionsTreeCache;
}

// Tool Definitions
const TOOLS = [
  {
    name: 'search_iuenna_corpus',
    description: 'Search across 20,788 archived archaeological resources, excavation reports, drawings, and plans in the IUENNA Jauntal corpus.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search terms, e.g. "Münzen", "Hemmaberg Doppelkirchen", "Hans Winkler", "Globasnitz".'
        },
        limit: {
          type: 'number',
          description: 'Maximum number of results to return (default: 10, max: 30).'
        }
      },
      required: ['query']
    }
  },
  {
    name: 'get_findspot_details',
    description: 'Retrieve detailed archaeological information, WKT geographic coordinates, and associated datasets for one of the 219 recorded findspots in the Southern Jauntal.',
    inputSchema: {
      type: 'object',
      properties: {
        name_or_id: {
          type: 'string',
          description: 'Findspot name or ID, e.g. "Hemmaberg", "Globasnitz", "Stari Trg", or "plc_1757171".'
        }
      },
      required: ['name_or_id']
    }
  },
  {
    name: 'get_geodata_catalog',
    description: 'List the 9 authoritative archaeological GeoPackages (GPKG) produced and archived by the IUENNA project, including tal_bda_fsdb_2023.gpkg.',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'get_corpus_statistics',
    description: 'Retrieve high-level metrics of the IUENNA archaeological collection archived on ARCHE (total files, collections, places, storage volume).',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'get_project_bibliography',
    description: 'Retrieve authoritative bibliographic entries, academic publications, and excavation literature from the official IUENNA Zotero Library (Group 4910727). Supports filtering by author, keyword, or site.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Optional search term to filter bibliography (e.g. "Hagmann", "Glaser", "Hemmaberg", "Vibe Coding", "AI").'
        },
        limit: {
          type: 'number',
          description: 'Maximum number of bibliographic items to return (default: 10, max: 30).'
        }
      }
    }
  }
];

// Tool Executors
async function executeTool(name, args = {}) {
  switch (name) {
    case 'search_iuenna_corpus': {
      const q = (args.query || '').toLowerCase().trim();
      const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
      const index = await getSearchIndex();
      
      const tokens = q.split(/\s+/).filter(t => t.length > 0);
      const matches = [];

      for (const item of index) {
        const title = (item.title || item.name || '').toLowerCase();
        const breadcrumb = (item.breadcrumb || '').toLowerCase();
        const text = `${title} ${breadcrumb}`;
        
        const allTokensMatch = tokens.every(tok => text.includes(tok));
        if (allTokensMatch) {
          matches.push({
            id: item.id,
            title: item.title || item.name,
            breadcrumb: item.breadcrumb,
            pid: item.pid || `https://hdl.handle.net/21.11115/0000-0016-7B39-F`,
            parent_id: item.parent_id || item.parent
          });
          if (matches.length >= limit) break;
        }
      }

      return {
        total_found: matches.length,
        query: args.query,
        results: matches
      };
    }

    case 'get_findspot_details': {
      const target = (args.name_or_id || '').toLowerCase().trim();
      const places = await getPlaces();
      
      const matches = places.filter(p => {
        const title = (p.title || p.name || '').toLowerCase();
        const id = (p.id || '').toLowerCase();
        return title.includes(target) || id === target;
      });

      if (matches.length === 0) {
        return { message: `No findspot matching "${args.name_or_id}" found among the 219 recorded sites.` };
      }

      return {
        count: matches.length,
        findspots: matches.slice(0, 5)
      };
    }

    case 'get_geodata_catalog': {
      const datasets = await getDatasets();
      return {
        count: datasets.length,
        datasets: datasets
      };
    }

    case 'get_corpus_statistics': {
      const stats = await fetchJson('arche_stats.json');
      return stats;
    }

    case 'get_project_bibliography': {
      const q = (args.query || '').trim();
      const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 30);
      let url = `https://api.zotero.org/groups/4910727/items?format=json&limit=${limit}`;
      if (q) {
        url += `&q=${encodeURIComponent(q)}`;
      }
      try {
        const res = await fetch(url, { headers: { 'User-Agent': 'IUENNA-MCP-Server/1.0' } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const items = await res.json();
        const results = items.map(it => {
          const d = it.data || {};
          const creators = (d.creators || [])
            .filter(c => c.lastName)
            .map(c => `${c.lastName} ${c.firstName || ''}`.trim())
            .join(', ');
          return {
            key: d.key,
            title: d.title,
            itemType: d.itemType,
            creators: creators,
            date: d.date,
            publicationTitle: d.publicationTitle || d.bookTitle || null,
            doi: d.DOI || null,
            url: d.url || `https://www.zotero.org/groups/4910727/iuenna/items/${d.key}`
          };
        });
        return {
          zotero_group_url: 'https://www.zotero.org/groups/4910727/iuenna',
          count: results.length,
          items: results
        };
      } catch (err) {
        return {
          error: `Failed to query Zotero API: ${err.message}`,
          zotero_web: 'https://www.zotero.org/groups/4910727/iuenna'
        };
      }
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// JSON-RPC Stdio Loop
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function sendResponse(response) {
  process.stdout.write(JSON.stringify(response) + '\n');
}

rl.on('line', async (line) => {
  if (!line.trim()) return;
  let msg;
  try {
    msg = JSON.parse(line);
  } catch (e) {
    return;
  }

  const { id, method, params } = msg;

  if (method === 'initialize') {
    sendResponse({
      jsonrpc: '2.0',
      id,
      result: {
        protocolVersion: '2024-11-05',
        capabilities: {
          tools: {}
        },
        serverInfo: {
          name: 'iuenna-mcp',
          version: '1.0.0'
        }
      }
    });
    return;
  }

  if (method === 'notifications/initialized') {
    // Client initialized confirmation
    return;
  }

  if (method === 'tools/list') {
    sendResponse({
      jsonrpc: '2.0',
      id,
      result: {
        tools: TOOLS
      }
    });
    return;
  }

  if (method === 'tools/call') {
    const { name, arguments: args } = params || {};
    try {
      const resultData = await executeTool(name, args);
      sendResponse({
        jsonrpc: '2.0',
        id,
        result: {
          content: [
            {
              type: 'text',
              text: JSON.stringify(resultData, null, 2)
            }
          ]
        }
      });
    } catch (err) {
      sendResponse({
        jsonrpc: '2.0',
        id,
        error: {
          code: -32000,
          message: err.message || 'Internal tool execution error'
        }
      });
    }
    return;
  }

  // Fallback for unhandled method
  if (id !== undefined) {
    sendResponse({
      jsonrpc: '2.0',
      id,
      error: {
        code: -32601,
        message: `Method not found: ${method}`
      }
    });
  }
});
