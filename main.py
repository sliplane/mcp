import os
from pathlib import Path

import httpx
from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken, RemoteAuthProvider, TokenVerifier
from fastmcp.server.dependencies import get_http_headers


MCP_BASE_URL = os.getenv("SLIPLANE_MCP_BASE_URL", "https://mcp.sliplane.io")
AUTH_SERVER_URL = os.getenv("SLIPLANE_AUTH_SERVER_URL", "https://api.sliplane.io")
SCOPES = ["full"]


class PassthroughTokenVerifier(TokenVerifier):
    """Require a bearer token; the Sliplane API validates it on forwarded calls."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if token.strip():
            return AccessToken(token=token, client_id="sliplane-oauth", scopes=SCOPES)
        return None


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

auth = RemoteAuthProvider(
    token_verifier=PassthroughTokenVerifier(required_scopes=SCOPES),
    authorization_servers=[AUTH_SERVER_URL],
    base_url=MCP_BASE_URL,
    scopes_supported=SCOPES,
    resource_name="Sliplane MCP Server",
)

openapi_spec = httpx.get("https://ctrl.sliplane.io/spec.json").json()

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Sliplane API MCP Server",
    auth=auth,
)

SLIPLANE_GUIDE = (
    Path(__file__).parent.joinpath("sliplane_guide.md").read_text(encoding="utf-8")
)


@mcp.tool()
def sliplane_guide() -> str:
    """Comprehensive guide explaining how Sliplane works as a platform - the mental model, architecture, and key behaviors."""
    return SLIPLANE_GUIDE

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/",
        stateless_http=True,
    )
