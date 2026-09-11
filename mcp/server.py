#!/usr/bin/env python3
"""
IUENNA Model Context Protocol (MCP) Server (Python)
---------------------------------------------------
Zero-dependency MCP stdio server for the IUENNA archaeological project.
Works with any MCP client (Claude Desktop, Open-WebUI, Cursor, LibreChat, Python scripts).
"""

import sys
import json
import urllib.request

BASE_URL = "https://iuenna.github.io/data"

CACHE = {}

def fetch_json(endpoint):
    if endpoint in CACHE:
        return CACHE[endpoint]
    url = f"{BASE_URL}/{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "IUENNA-MCP-Server/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        CACHE[endpoint] = data
        return data

TOOLS = [
    {
        "name": "search_iuenna_corpus",
        "description": "Search across 20,788 archived archaeological resources, excavation reports, drawings, and plans in the IUENNA Jauntal corpus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": 'Search terms, e.g. "Münzen", "Hemmaberg Doppelkirchen", "Hans Winkler", "Globasnitz".'
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10, max: 30)."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_findspot_details",
        "description": "Retrieve detailed archaeological information, coordinates, and associated datasets for one of the 219 recorded findspots in the Southern Jauntal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_or_id": {
                    "type": "string",
                    "description": 'Findspot name or ID, e.g. "Hemmaberg", "Globasnitz", "Stari Trg", or "plc_1757171".'
                }
            },
            "required": ["name_or_id"]
        }
    },
    {
        "name": "get_geodata_catalog",
        "description": "List the 9 authoritative archaeological GeoPackages (GPKG) produced and archived by the IUENNA project.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_corpus_statistics",
        "description": "Retrieve high-level metrics of the IUENNA archaeological collection archived on ARCHE.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

def execute_tool(name, args):
    if name == "search_iuenna_corpus":
        query = args.get("query", "").lower().strip()
        limit = min(max(int(args.get("limit", 10)), 1), 30)
        items = fetch_json("arche_search_index.json")
        tokens = query.split()
        matches = []
        for item in items:
            text = f"{item.get('title', '')} {item.get('breadcrumb', '')}".lower()
            if all(t in text for t in tokens):
                matches.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "breadcrumb": item.get("breadcrumb"),
                    "pid": item.get("pid", "https://hdl.handle.net/21.11115/0000-0016-7B39-F")
                })
                if len(matches) >= limit:
                    break
        return {"query": query, "total_found": len(matches), "results": matches}

    elif name == "get_findspot_details":
        target = args.get("name_or_id", "").lower().strip()
        places = fetch_json("arche_places.json")
        matches = [
            p for p in places
            if target in p.get("title", "").lower() or target == str(p.get("id", "")).lower()
        ]
        if not matches:
            return {"message": f'No findspot matching "{target}" found.'}
        return {"count": len(matches), "findspots": matches[:5]}

    elif name == "get_geodata_catalog":
        datasets = fetch_json("arche_datasets.json")
        return {"count": len(datasets), "datasets": datasets}

    elif name == "get_corpus_statistics":
        return fetch_json("arche_stats.json")

    else:
        raise ValueError(f"Unknown tool: {name}")

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "iuenna-mcp", "version": "1.0.0"}
                }
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS}
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result_content = execute_tool(tool_name, tool_args)
                res = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result_content, indent=2)}]
                    }
                }
            except Exception as e:
                res = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32000, "message": str(e)}
                }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif msg_id is not None:
            res = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
