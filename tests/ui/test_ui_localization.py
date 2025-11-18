import asyncio
import re
from typing import Dict, List

import httpx

from app.main import app

ROUTES: Dict[str, List[str]] = {
    "/v8/dashboard": ["Đề xuất", "Chiến lược"],
    "/os/control-center": ["Hành động", "Trung tâm"],
    "/dashboard/test-report": ["Báo cáo", "Kiểm thử"],
    "/dashboard/ai": ["Mô hình", "Tồn kho"],
}

BAD_PATTERNS = re.compile(r"(Ã|Â|â€”|)")


async def fetch(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


def test_ui_localization_snapshot():
    async def runner():
        for route, expected_words in ROUTES.items():
            resp = await fetch(route)
            assert resp.status_code in (200, 302, 307), f"{route} trả về {resp.status_code}"
            content = resp.text
            for word in expected_words:
                assert word in content, f"Từ khóa '{word}' không xuất hiện trong {route}"
            assert not BAD_PATTERNS.search(content), f"Phát hiện ký tự lỗi trong {route}"
    asyncio.run(runner())
