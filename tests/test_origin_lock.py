import asyncio
import unittest

import httpx
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from origin_lock import OriginLock


async def _ok(_):
    return PlainTextResponse("ok")


def _get(secret, path, headers=None):
    app = Starlette(
        routes=[Route("/", _ok), Route("/health", _ok)],
        middleware=[Middleware(OriginLock, secret=secret, open_paths=("/health",))],
    )

    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return (await client.get(path, headers=headers)).status_code

    return asyncio.run(run())


class OriginLockTest(unittest.TestCase):
    def test_rejects_missing_or_wrong_secret(self):
        self.assertEqual(_get("s3cret", "/"), 403)
        self.assertEqual(_get("s3cret", "/", {"x-origin-secret": "nope"}), 403)

    def test_allows_matching_secret(self):
        self.assertEqual(_get("s3cret", "/", {"x-origin-secret": "s3cret"}), 200)

    def test_open_paths_skip_check(self):
        self.assertEqual(_get("s3cret", "/health"), 200)

    def test_disabled_without_secret(self):
        self.assertEqual(_get("", "/"), 200)


if __name__ == "__main__":
    unittest.main()
