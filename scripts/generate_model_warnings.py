import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.logging_utils import log_warning

DATASET_VERSION = "supplychain_weather_merged_global.csv"


def warn_inventory():
    metrics_path = PROJECT_ROOT / "results" / "metrics" / "inventory_rl_global.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
        rmse = metrics.get("rmse", 0)
        log_warning(
            "Inventory Optimizer RL",
            issue=f"RMSE at {rmse} requires monitoring for APAC spikes",
            suggestion="Increase exploration rate for APAC warehouses",
            severity="medium",
            region="APAC",
            dataset_version=DATASET_VERSION,
            model_version="v5.3",
        )


def warn_forecast():
    metrics_path = PROJECT_ROOT / "results" / "metrics" / "forecast_global.json"
    if metrics_path.exists():
        scopes = json.loads(metrics_path.read_text())
        if scopes:
            worst_scope = max(scopes, key=lambda s: s.get("mae", 0))
            log_warning(
                "Demand Forecast Ensemble",
                issue=f"MAE {worst_scope.get('mae')} detected on scope {worst_scope.get('scope')}",
                suggestion="Re-run calibration for high-variance regions",
                severity="medium",
                region=worst_scope.get("scope", "GLOBAL"),
                dataset_version=DATASET_VERSION,
                model_version="v7.5",
            )


def warn_late_delivery():
    metrics_path = PROJECT_ROOT / "results" / "metrics" / "late_delivery_global.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
        f1 = metrics.get("f1", 0)
        log_warning(
            "Late Delivery Classifier",
            issue=f"F1 score at {f1:.3f} for MENA routes",
            suggestion="Refresh congestion features for the latest shipments",
            severity="low",
            region="MENA",
            dataset_version=DATASET_VERSION,
            model_version="v4.2",
        )


def warn_pricing():
    metrics_path = PROJECT_ROOT / "results" / "metrics" / "pricing_global.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
        mae = metrics.get("mae", 0)
        log_warning(
            "Pricing Elasticity Model",
            issue=f"MAE {mae} observed for NA electronics segment",
            suggestion="Tune alpha parameter and review promotion data",
            severity="low",
            region="NA",
            dataset_version=DATASET_VERSION,
            model_version="v3.1",
        )


def main():
    warn_inventory()
    warn_forecast()
    warn_late_delivery()
    warn_pricing()


if __name__ == "__main__":
    main()
