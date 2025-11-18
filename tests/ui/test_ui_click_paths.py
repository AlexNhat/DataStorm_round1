import asyncio
from html.parser import HTMLParser
from typing import List, Set

import httpx

from app.main import app

BASE_URL = "http://testserver"


class NavLinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: Set[str] = set()

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href or not href.startswith("/"):
            return
        clean = href.split("#", 1)[0].split("?", 1)[0]
        if not clean or "." in clean.split("/")[-1]:
            return
        self.links.add(clean.rstrip("/") or "/")


async def _get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as client:
        return await client.get(path)


def test_dashboard_links_resolve():
    async def runner():
        resp = await _get("/dashboard/ai")
        assert resp.status_code == 200
        collector = NavLinkCollector()
        collector.feed(resp.text)
        important_links: List[str] = sorted(
            link for link in collector.links if link in {
                "/dashboard",
                "/dashboard/ai",
                "/v8/dashboard",
                "/os/control-center",
                "/dashboard/test-report",
                "/docs",
                "/notebooks",
                "/health",
            }
        )
        assert important_links, "No nav links were captured"
        for link in important_links:
            result = await _get(link)
            assert result.status_code in (200, 302, 307), f"{link} returned {result.status_code}"

    asyncio.run(runner())
