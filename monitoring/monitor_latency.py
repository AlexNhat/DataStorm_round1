import json
import logging
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("monitor_latency")

BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_PATH = BASE_DIR / "results" / "logs" / "monitoring_latency.json"

ENDPOINTS = {
    "inventory_rl": ("POST", "http://localhost:8000/ml/inventory/optimize"),
    "forecast": ("POST", "http://localhost:8000/ml/revenue/forecast"),
    "late_delivery": ("POST", "http://localhost:8000/ml/logistics/delay"),
}

THRESHOLDS = {
    "inventory_rl": 1.5,
    "forecast": 1.0,
    "late_delivery": 0.8,
}

def measure_latency(method: str, url: str, payload: dict) -> float:
    start = time.perf_counter()
    try:
        response = requests.request(method, url, json=payload, timeout=5)
        response.raise_for_status()
    except Exception as exc:
        logger.error("Latency check failed for %s: %s", url, exc)
        return float("inf")
    return time.perf_counter() - start

def monitor():
    payload = {}  # placeholder synthetic payload
    results = {}
    alerts = {}
    for name, (method, url) in ENDPOINTS.items():
        latency = measure_latency(method, url, payload)
        results[name] = latency
        if latency > THRESHOLDS.get(name, 1.0):
            alerts[name] = latency
    REPORT_PATH.write_text(json.dumps({"latency": results, "alerts": alerts}, indent=2))
    if alerts:
        logger.warning("Latency alerts detected.")
    else:
        logger.info("Latency within thresholds.")

if __name__ == "__main__":
    monitor()
