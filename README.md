# Sliplane API MCP

This is the MCP (Model Context Protocol) Server for the [Sliplane API](https://ctrl.sliplane.io)

## Local Development

```bash
uv sync
uv run main.py
```

Or with Docker:

```bash
docker build -t sliplane-api-mcp .
docker run -p 8000:8000 sliplane-api-mcp
```

## Deployment

Available on [mcp.sliplane.io](https://mcp.sliplane.io). Deployed on [Sliplane](https://sliplane.io)

## Usage

Checkout [Usage Docs](https://docs.sliplane.io/mcp/getting-started)
