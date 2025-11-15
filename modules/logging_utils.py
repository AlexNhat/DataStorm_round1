import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "data" / "model_registry.json"
WARNINGS_DIR = BASE_DIR / "logs" / "warnings"
INFERENCE_DIR = BASE_DIR / "logs" / "inference"


LOGGER = logging.getLogger(__name__)


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def _timestamp() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _load_registry() -> list[Dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        LOGGER.warning("Registry file missing at %s", REGISTRY_PATH)
        return []
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        LOGGER.error("Failed to decode registry JSON: %s", exc)
        return []


def _write_registry(data: list[Dict[str, Any]]) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=4), encoding="utf-8")


def get_registry_entry(model_name: str) -> Optional[Dict[str, Any]]:
    for item in _load_registry():
        if item.get("name") == model_name:
            return item
    return None


def update_registry_usage(model_name: str, *, dataset_version: Optional[str] = None, model_version: Optional[str] = None) -> None:
    data = _load_registry()
    changed = False
    timestamp = _timestamp()
    for item in data:
        if item.get("name") == model_name:
            item.setdefault("used_in_pipeline", False)
            item.setdefault("last_inference_call", None)
            item.setdefault("total_inference_calls", 0)
            item.setdefault("last_warning", None)
            item.setdefault("warnings_count", 0)
            item["used_in_pipeline"] = True
            item["last_training_run"] = timestamp
            item["last_update"] = timestamp
            if dataset_version:
                item["dataset_version"] = dataset_version
            if model_version:
                item["version"] = model_version
            changed = True
            break
    if changed:
        _write_registry(data)


def log_warning(model_name: str, issue: str, suggestion: str, *, severity: str = "medium", region: str = "GLOBAL", dataset_version: str = "merged_global_dataset", model_version: Optional[str] = None) -> None:
    WARNINGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp()
    slug = _slug(model_name)
    line = f"{timestamp} | WARNING | {model_name} | severity={severity} | region={region} | dataset={dataset_version} | model_version={model_version or 'N/A'} | issue={issue} | suggestion={suggestion}\n"
    with (WARNINGS_DIR / f"{slug}_warnings.log").open("a", encoding="utf-8") as log_file:
        log_file.write(line)

    data = _load_registry()
    changed = False
    for item in data:
        if item.get("name") == model_name:
            item["last_warning"] = {
                "timestamp": timestamp,
                "issue": issue,
                "suggestion": suggestion,
                "severity": severity,
            }
            item["warnings_count"] = item.get("warnings_count", 0) + 1
            changed = True
            break
    if changed:
        _write_registry(data)


def log_inference(model_name: str, params: Dict[str, Any], latency_ms: float, result_summary: Any, *, region: str = "GLOBAL") -> None:
    INFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp()
    slug = _slug(model_name)
    entry = f"{timestamp} | INFO | {model_name} | Predict | region={region} | latency_ms={latency_ms:.2f} | params={params} | result={result_summary}\n"
    with (INFERENCE_DIR / f"{slug}_inference.log").open("a", encoding="utf-8") as log_file:
        log_file.write(entry)

    data = _load_registry()
    changed = False
    for item in data:
        if item.get("name") == model_name:
            item["last_inference_call"] = timestamp
            item["total_inference_calls"] = item.get("total_inference_calls", 0) + 1
            item["used_in_pipeline"] = True
            changed = True
            break
    if changed:
        _write_registry(data)


def log_inference_warning(model_name: str, detail: str, *, severity: str = "medium") -> None:
    log_warning(
        model_name=model_name,
        issue=f"Inference anomaly: {detail}",
        suggestion="Inspect latest inference payload and model drift metrics.",
        severity=severity,
    )
