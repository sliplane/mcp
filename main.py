import httpx
from fastmcp import FastMCP

client = httpx.AsyncClient(base_url="https://ctrl.sliplane.io/v0",timeout=60.0)

openapi_spec = httpx.get("https://ctrl.sliplane.io/spec.json").json()

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Sliplane API MCP Server"
)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/")