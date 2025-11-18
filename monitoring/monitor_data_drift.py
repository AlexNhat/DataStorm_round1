import json
import logging
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from modules.data_pipeline.global_dataset_loader import load_global_dataset

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("monitor_data_drift")

BASE_DIR = Path(__file__).resolve().parents[1]
MERGED_PATH = BASE_DIR / "data" / "merged" / "supplychain_weather_merged_global.csv"
DRIFT_REPORT = BASE_DIR / "results" / "logs" / "monitoring_data_drift.json"
THRESHOLD = 0.2

def ks_pvalue(a: pd.Series, b: pd.Series) -> float:
    a = a.dropna()
    b = b.dropna()
    if a.empty or b.empty:
        return 1.0
    from scipy.stats import ks_2samp
    return ks_2samp(a, b).pvalue

def load_baseline(path: Path, feature_cols: List[str]) -> pd.DataFrame:
    baseline_path = path.with_name(path.stem + "_baseline.csv")
    if baseline_path.exists():
        return pd.read_csv(baseline_path)[feature_cols]
    df = load_global_dataset(str(path))
    baseline = df[feature_cols].sample(min(5000, len(df)), random_state=42)
    baseline.to_csv(baseline_path, index=False)
    return baseline

def monitor():
    df = load_global_dataset(str(MERGED_PATH))
    feature_cols = [col for col in df.columns if df[col].dtype != "object"]
    baseline = load_baseline(MERGED_PATH, feature_cols)
    alerts: Dict[str, float] = {}
    for col in feature_cols:
        pvalue = ks_pvalue(df[col], baseline[col])
        drift = 1 - pvalue
        if drift > THRESHOLD:
            alerts[col] = drift
    report = {"total_features": len(feature_cols), "drift_alerts": alerts, "threshold": THRESHOLD}
    DRIFT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DRIFT_REPORT.write_text(json.dumps(report, indent=2))
    if alerts:
        logger.warning("Data drift detected: %s", alerts)
    else:
        logger.info("No significant data drift.")

if __name__ == "__main__":
    monitor()
