# IUENNA Remote MCP

Public, read-only, stateless Model Context Protocol endpoint for IUENNA.

## Production endpoint

`https://iuenna-mcp.dominik-hagmann13.workers.dev/mcp`

The root URL exposes a small health response:

`https://iuenna-mcp.dominik-hagmann13.workers.dev/`

## Architecture

- **Runtime:** Cloudflare Workers Free
- **Transport:** MCP Streamable HTTP
- **Endpoint:** `/mcp`
- **Authentication:** none; IUENNA exposes only public research data
- **State:** none; no database, KV, Durable Objects, or paid services
- **Canonical data:** `https://iuenna.github.io/data/`
- **Runtime query projection:** `https://iuenna.github.io/data/mcp_remote/`

The query projection is generated reproducibly from the authoritative IUENNA corpus and knowledge graph. It is disposable and non-authoritative; the canonical research data remain the full IUENNA/ARCHE-derived files in `data/`.

IUENNA deliberately exposes **one MCP access path only**: this public Remote MCP. The former local Python/Node stdio implementations have been retired to minimise installation effort and long-term maintenance.

## Cloudflare deployment

Production uses **Cloudflare Workers Builds** connected directly to the GitHub repository. No Cloudflare API token is stored in this repository.

Current settings:

- Worker name: `iuenna-mcp`
- Production branch: `main`
- Root directory: `mcp-remote`
- Build command: empty
- Deploy command: `npx wrangler deploy`

## Local validation for development

This is only for maintaining the Worker source; it is not a second MCP distribution mode.

```bash
npm install
npm run check
npm run dry-run
```
