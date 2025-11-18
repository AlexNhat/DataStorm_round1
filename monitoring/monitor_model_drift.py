import json
import logging
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, f1_score

from modules.data_pipeline.global_dataset_loader import load_global_dataset

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("monitor_model_drift")

BASE_DIR = Path(__file__).resolve().parents[1]
MERGED_PATH = BASE_DIR / "data" / "merged" / "supplychain_weather_merged_global.csv"
REPORT_PATH = BASE_DIR / "results" / "logs" / "monitoring_model_drift.json"

THRESHOLDS = {
    "inventory": 0.1,
    "forecast": 0.1,
    "late_delivery": 0.1,
    "pricing": 0.1,
}

def load_model(model_path: Path):
    if model_path.exists():
        return joblib.load(model_path)
    raise FileNotFoundError(model_path)

def compute_metrics_inventory(df, model):
    y_true = df["Order Item Quantity"]
    preds = model.predict(df[model.feature_names_in_])
    mae = mean_absolute_error(y_true, preds)
    rmse = mean_squared_error(y_true, preds, squared=False)
    return {"mae": mae, "rmse": rmse}

def compute_metrics_forecast(df, model):
    y_true = df["Sales"]
    preds = model.predict(df[model.feature_names_in_])
    mae = mean_absolute_error(y_true, preds)
    rmse = mean_squared_error(y_true, preds, squared=False)
    return {"mae": mae, "rmse": rmse}

def compute_metrics_delivery(df, model):
    y_true = df["Late_delivery_risk"]
    preds = model.predict(df[model.feature_names_in_])
    f1 = f1_score(y_true, preds)
    return {"f1": f1}

def compute_metrics_pricing(df, model):
    y_true = np.log1p(df["Order Item Quantity"])
    preds = model.predict(df[model.feature_names_in_])
    mae = mean_absolute_error(y_true, preds)
    return {"mae": mae}

def monitor():
    df = load_global_dataset(str(MERGED_PATH)).sample(20000, random_state=42)
    alerts: Dict[str, Dict] = {}
    # Placeholder: actual models assumed to be saved at known paths
    models_info = {
        "inventory": (BASE_DIR / "models/inventory_rl/global/inventory_rl_global.pkl", compute_metrics_inventory),
        "forecast": (BASE_DIR / "models/forecast/global/region_model/forecast.pkl", compute_metrics_forecast),
        "late_delivery": (BASE_DIR / "models/late_delivery/global/late_delivery_global.pkl", compute_metrics_delivery),
        "pricing": (BASE_DIR / "models/pricing/global/pricing_elasticity.pkl", compute_metrics_pricing),
    }
    report = {}
    for name, (path, metric_fn) in models_info.items():
        try:
            model = load_model(path)
            metrics = metric_fn(df, model)
            report[name] = metrics
            drift_metric = next(iter(metrics.values()))
            if drift_metric > THRESHOLDS[name]:
                alerts[name] = metrics
        except Exception as exc:
            alerts[name] = {"error": str(exc)}
    REPORT_PATH.write_text(json.dumps({"metrics": report, "alerts": alerts}, indent=2))
    if alerts:
        logger.warning("Model drift alert: %s", alerts)
    else:
        logger.info("Model drift within thresholds.")

if __name__ == "__main__":
    monitor()
