import hmac

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class OriginLock:
    def __init__(self, app: ASGIApp, secret: str, open_paths: tuple[str, ...] = ()):
        self.app = app
        self.secret = secret.encode()
        self.open_paths = open_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and self.secret and scope["path"] not in self.open_paths:
            provided = dict(scope["headers"]).get(b"x-origin-secret", b"")
            if not hmac.compare_digest(provided, self.secret):
                await PlainTextResponse("Forbidden", status_code=403)(scope, receive, send)
                return
        await self.app(scope, receive, send)
