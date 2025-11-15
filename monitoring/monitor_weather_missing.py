import json
import logging
from pathlib import Path

import pandas as pd

from modules.data_pipeline.global_dataset_loader import load_global_dataset

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("monitor_weather_missing")

BASE_DIR = Path(__file__).resolve().parents[1]
MERGED_PATH = BASE_DIR / "data" / "merged" / "supplychain_weather_merged_global.csv"
REPORT_PATH = BASE_DIR / "results" / "logs" / "monitoring_weather_missing.json"
THRESHOLD = 0.05

WEATHER_COLS = [
    "temperature_2m_mean",
    "precipitation_sum",
    "wind_speed_10m_mean",
    "relative_humidity_2m_mean",
]

def monitor():
    df = load_global_dataset(str(MERGED_PATH))
    report = {}
    for region, group in df.groupby("Region"):
        counts = {}
        for col in WEATHER_COLS:
            missing_rate = group[col].isna().mean() if col in group.columns else 1.0
            counts[col] = missing_rate
        report[region] = counts
    alerts = {
        region: {col: rate for col, rate in stats.items() if rate > THRESHOLD}
        for region, stats in report.items()
        if any(rate > THRESHOLD for rate in stats.values())
    }
    REPORT_PATH.write_text(json.dumps({"missing_rates": report, "alerts": alerts}, indent=2))
    if alerts:
        logger.warning("Weather missing alert: %s", alerts)
    else:
        logger.info("Weather coverage OK.")

if __name__ == "__main__":
    monitor()
