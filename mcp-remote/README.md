# IUENNA Remote MCP

Public, read-only, stateless Model Context Protocol endpoint for IUENNA.

## Architecture

- **Runtime:** Cloudflare Workers Free
- **Transport:** MCP Streamable HTTP
- **Endpoint:** `/mcp`
- **Authentication:** none; IUENNA exposes only public research data
- **State:** none; no database, KV, Durable Objects, or paid services
- **Canonical data:** `https://iuenna.github.io/data/`
- **Runtime query projection:** `https://iuenna.github.io/data/mcp_remote/`

The query projection is generated from the authoritative IUENNA corpus and knowledge graph. It is disposable and non-authoritative; the canonical research data remain the full IUENNA/ARCHE-derived files in `data/`.

## Cloudflare deployment

The intended production setup uses **Cloudflare Workers Builds** connected directly to the GitHub repository. No Cloudflare API token needs to be stored in this repository.

Recommended settings:

- Worker name: `iuenna-mcp`
- Production branch: `main`
- Root directory: `mcp-remote`
- Build command: leave empty
- Deploy command: `npx wrangler deploy`

Cloudflare then provides a free `*.workers.dev` URL. The MCP endpoint is the resulting URL plus `/mcp`.

## Local validation

```bash
npm install
npm run check
npm run dry-run
```

## Migration note

The existing stdio MCP remains available only until this Remote MCP is deployed and verified. After successful production verification, the old Python/Node stdio implementations and their setup instructions can be removed so IUENNA exposes one public MCP access path.
