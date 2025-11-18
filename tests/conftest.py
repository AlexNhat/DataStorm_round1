# -*- coding: utf-8 -*-
import anyio
import httpx
import pytest
from types import SimpleNamespace
from pathlib import Path

from app.main import app

class ASGIHttpClient:
    def __init__(self):
        self.transport = httpx.ASGITransport(app=app)
        self.base_url = 'http://testserver'

    def request(self, method: str, url: str, **kwargs):
        async def _call():
            async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
                return await client.request(method, url, **kwargs)
        return anyio.run(_call)

    def get(self, url: str, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request('POST', url, **kwargs)

@pytest.fixture(scope='session')
def http_client():
    return ASGIHttpClient()

@pytest.fixture(scope='session')
def snapshot_baseline():
    path = Path('tests/ui/snapshots/dashboard.html')
    return path.read_text(encoding='utf-8') if path.exists() else ''
