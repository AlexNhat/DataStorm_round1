import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("monitor_registry_sync")

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "data" / "model_registry.json"
REPORT_PATH = BASE_DIR / "results" / "logs" / "monitoring_registry_sync.json"

def monitor():
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(REGISTRY_PATH)
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    issues = []
    for model in data:
        if not model.get("artifacts", {}).get("model_path"):
            issues.append({"model": model["name"], "issue": "Missing model path"})
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({"issues": issues}, indent=2))
    if issues:
        logger.warning("Registry sync issues: %s", issues)
    else:
        logger.info("Registry synchronized with artifacts.")

if __name__ == "__main__":
    monitor()
