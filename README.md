# Sliplane MCP Server

MCP (Model Context Protocol) server for the [Sliplane API](https://ctrl.sliplane.io).

> **Warning**: You can execute destructive commands against your deployments. Use with caution and always double check your commands before executing them.

## Prerequisites

- **API Key**: Your personal API key from your Sliplane account

You can create an API key in your [Sliplane team settings](https://sliplane.io).

## Installation

The server is hosted at `https://mcp.sliplane.io` - no self-hosting required for normal usage.

### Claude Code

```bash
claude mcp add sliplane https://mcp.sliplane.io \
    -t sse \
    -H "Authorization: Bearer yourapikeyhere"
```

### Cursor

Go to Cursor Settings → Tools & Integrations → MCP Tools and add:

```json
{
  "mcpServers": {
    "sliplane": {
      "url": "https://mcp.sliplane.io",
      "type": "sse",
      "headers": {
        "Authorization": "Bearer yourapikeyhere"
      }
    }
  }
}
```

### VS Code

Create `.vscode/mcp.json` in your repository:

```json
{
  "servers": {
    "sliplane": {
      "type": "sse",
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
- **Headers**:
  - `Authorization: Bearer yourapikeyhere`

## What You Can Do

The MCP server mirrors the Sliplane public API. You can:

- Manage deployments
- Access project information
- Monitor application status
- Execute deployment operations

## Self-Hosting (Optional)

Only needed if you want to modify the server. For normal usage, use the hosted version above.

```bash
uv sync
uv run main.py
```

Or with Docker:

```bash
docker build -t sliplane-mcp .
docker run -p 8000:8000 sliplane-mcp
```



[<img src="https://sliplane.io/deploy-with-sliplane.svg" width=200>](https://sliplane.io?utm_source=mcp-github)
