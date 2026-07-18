# Sliplane MCP Server

MCP (Model Context Protocol) server for the [Sliplane API](https://ctrl.sliplane.io).

> **Warning**: You can execute destructive commands against your deployments. Use with caution and always double check your commands before executing them.

## Prerequisites

- **OAuth**: Recommended. Your MCP client opens Sliplane auth and receives a scoped Sliplane API token.
- **API key**: Still supported for clients that do not support OAuth.

## Installation

The server is hosted at `https://mcp.sliplane.io` - no self-hosting required for normal usage.

### Claude Code

```bash
claude mcp add --transport http \
  --client-id sliplane-mcp \
  sliplane https://mcp.sliplane.io
```

For API key auth:

```bash
claude mcp add --transport http \
  -H "Authorization: Bearer yourapikeyhere" \
  sliplane https://mcp.sliplane.io
```

### Codex

```bash
codex mcp add sliplane \
  --url https://mcp.sliplane.io \
  --oauth-client-id sliplane-mcp
```

For API key auth:

```bash
export SLIPLANE_API_KEY=yourapikeyhere

codex mcp add sliplane \
  --url https://mcp.sliplane.io \
  --bearer-token-env-var SLIPLANE_API_KEY
```

### Cursor

```json
{
  "mcpServers": {
    "sliplane-local": {
      "url": "https://mcp.sliplane.io",
      "auth": {
        "CLIENT_ID": "sliplane-mcp",
        "scopes": ["full"]
      }
    }
  }
}
```

For API key auth:

```json
{
  "mcpServers": {
    "sliplane": {
      "url": "https://mcp.sliplane.io",
      "headers": {
        "Authorization": "Bearer yourapikeyhere"
      }
    }
  }
}
```

### opencode

Run the interactive setup so opencode can store the pre-registered OAuth client ID:

```text
$ opencode mcp add

Add MCP server

Enter MCP server name
sliplane

Select MCP server type
Remote

Enter MCP server URL
https://mcp.sliplane.io

Does this server require OAuth authentication?
Yes

Do you have a pre-registered client ID?
Yes

Enter client ID
sliplane-mcp

Do you have a client secret?
No
```

Then authenticate:

```bash
opencode mcp auth
```

### VS Code

Create `.vscode/mcp.json` in your repository:

```json
{
  "servers": {
    "sliplane": {
      "type": "http",
      "url": "https://mcp.sliplane.io",
      "headers": {
        "Authorization": "Bearer yourapikeyhere"
      }
    }
  }
}
```

### Other Tools

- **URL**: `https://mcp.sliplane.io`
- **Type**: `StreamableHTTP`
- **OAuth Client ID**: `sliplane-mcp`
- **OAuth scopes**: `full`
- **API key header**:
  - `Authorization: Bearer yourapikeyhere`

## What You Can Do

The MCP server mirrors the Sliplane public API. You can:

- Manage deployments
- Access project information
- Monitor application status
- Execute deployment operations

Moreover, you can discover and deploy all services with presets through the `sliplane_preset_guide` tool.

## Self-Hosting (Optional)

Only needed if you want to modify the server. For normal usage, use the hosted version above.

```bash
uv sync
uv run main.py
```

The OAuth integration is configured with environment variables:

```bash
SLIPLANE_MCP_BASE_URL=http://localhost:8000
SLIPLANE_AUTH_SERVER_URL=http://localhost:3000
```

Or with Docker:

```bash
docker build -t sliplane-mcp .
docker run -p 8000:8000 sliplane-mcp
```

[<img src="https://sliplane.io/deploy-with-sliplane.svg" width=200>](https://sliplane.io?utm_source=mcp-github)
