import httpx
from fastmcp import FastMCP
from fastmcp.server.transforms import PromptsAsTools
from pathlib import Path

client = httpx.AsyncClient(base_url="https://ctrl.sliplane.io/v0",timeout=60.0)

openapi_spec = httpx.get("https://ctrl.sliplane.io/spec.json").json()

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Sliplane API MCP Server"
)

SLIPLANE_GUIDE = Path(__file__).parent.joinpath("sliplane_guide.md").read_text()

@mcp.prompt()
def sliplane_guide() -> str:
    """Comprehensive guide explaining how Sliplane works as a platform - the mental model, architecture, and key behaviors."""
    return SLIPLANE_GUIDE

mcp.add_transform(PromptsAsTools(mcp))

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/")
