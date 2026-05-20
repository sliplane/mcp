import httpx
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from pathlib import Path


async def forward_authorization(request: httpx.Request) -> None:
    headers = get_http_headers(include={"authorization", "x-organization-id"})
    if auth := headers.get("authorization"):
        request.headers["Authorization"] = auth
    if org := headers.get("x-organization-id"):
        request.headers["X-Organization-ID"] = org


client = httpx.AsyncClient(
    base_url="https://ctrl.sliplane.io/v0",
    timeout=60.0,
    event_hooks={"request": [forward_authorization]},
)

openapi_spec = httpx.get("https://ctrl.sliplane.io/spec.json").json()

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Sliplane API MCP Server"
)

SLIPLANE_GUIDE = Path(__file__).parent.joinpath("sliplane_guide.md").read_text(encoding="utf-8")

@mcp.tool()
def sliplane_guide() -> str:
    """Comprehensive guide explaining how Sliplane works as a platform - the mental model, architecture, and key behaviors."""
    return SLIPLANE_GUIDE

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/")
