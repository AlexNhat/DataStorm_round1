import asyncio
from typing import List, Tuple

import httpx
import pytest

from app.main import app

BASE_URL = "http://testserver"


async def _request(method: str, path: str, payload: dict | None = None) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as client:
        return await client.request(method, path, json=payload)


def test_ui_routes_exist():
    """Critical UI routes must respond without 404."""
    strategy_payload = {
        "objectives": ["balance"],
        "region": "VN",
        "season": "summer",
        "inputs": {
            "inventory": 8000,
            "demand_forecast": 9000,
            "weather_risk": 0.2,
            "avg_lead_time": 4,
            "logistics_cost": 15,
            "budget_ceiling": 30000,
            "priorities": {"cost": 5, "lead_time": 5, "service": 5},
            "risk_tolerance": "medium",
        },
        "metadata": {"warehouses": ["WH01"]},
        "model_results": {
            "forecast": {"expected_revenue": 100000, "demand_forecast": [8000, 9000, 10000]},
            "delay_risk": {"risk_score": 0.25, "high_risk_orders": 25},
        },
    }

    routes: List[Tuple[str, str, dict | None]] = [
        ("GET", "/dashboard/ai", None),
        ("GET", "/os/control-center", None),
        ("GET", "/os/actions/pending", None),
        ("GET", "/os/action/history", None),
        ("GET", "/os/status", None),
        ("GET", "/v8/dashboard", None),
        ("GET", "/dashboard/test-report", None),
        ("GET", "/favicon.ico", None),
        ("GET", "/dashboard/tests", None),
        ("POST", "/ai/strategy/generate", strategy_payload),
    ]

    async def runner():
        for method, path, payload in routes:
            resp = await _request(method, path, payload)
            assert resp.status_code == 200, f"{method} {path} failed: {resp.status_code}"

    asyncio.run(runner())
