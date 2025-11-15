import argparse
import json
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from modules.data_pipeline.global_dataset_loader import (
    DEFAULT_DATASET_PATH,
    load_global_dataset,
)
from modules.logging_utils import log_warning, update_registry_usage

logger = logging.getLogger("train_rl_inventory")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ensure_numeric(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        df[column] = default
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(default)
    return df[column]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.sort_values("record_date", inplace=True)

    ensure_numeric(df, "Order Item Quantity", 0.0)
    ensure_numeric(df, "Order Item Product Price", 0.0)
    ensure_numeric(df, "Sales", 0.0)
    ensure_numeric(df, "Order Item Total", 0.0)
    ensure_numeric(df, "temperature_2m_mean", df["temperature_2m_mean"].median() if "temperature_2m_mean" in df.columns else 0.0)
    ensure_numeric(df, "precipitation_sum", 0.0)
    ensure_numeric(df, "wind_speed_10m_mean", 0.0)
    ensure_numeric(df, "relative_humidity_2m_mean", 50.0)

    df["weather_risk_index"] = (
        0.4 * df["precipitation_sum"]
        + 0.3 * df["wind_speed_10m_mean"]
        + 0.3 * df["relative_humidity_2m_mean"]
    )

    df["temp_7d_avg"] = (
        df.groupby("City")["temperature_2m_mean"]
        .transform(lambda s: s.fillna(method="ffill").rolling(window=7, min_periods=1).mean())
        .fillna(df["temperature_2m_mean"])
    )

    df["rain_7d_avg"] = (
        df.groupby("City")["precipitation_sum"]
        .transform(lambda s: s.fillna(method="ffill").rolling(window=7, min_periods=1).mean())
        .fillna(df["precipitation_sum"])
    )

    storm_codes = {95, 96, 99}
    if "weather_code" in df.columns:
        ensure_numeric(df, "weather_code", 0.0)
        df["storm_flag"] = np.where(df["weather_code"].isin(storm_codes) | (df["precipitation_sum"] > 25), 1, 0)
    else:
        df["storm_flag"] = np.where(df["precipitation_sum"] > 25, 1, 0)

    region_daily_qty = df.groupby(["Region", "record_date"])["Order Item Quantity"].transform("sum")
    region_baseline = (
        df.groupby("Region")["Order Item Quantity"].transform("mean").replace(0, np.nan).fillna(1.0)
    )
    df["region_congestion_index"] = (region_daily_qty / region_baseline).clip(0, 5).fillna(0)

    df["warehouse_workload_score"] = (
        df.groupby("City")["Order Item Quantity"]
        .transform(lambda s: s.rolling(window=7, min_periods=1).sum())
        .fillna(0)
    )
    max_score = df["warehouse_workload_score"].quantile(0.95) or 1.0
    df["warehouse_workload_score"] = (df["warehouse_workload_score"] / max_score).clip(0, 10)

    df["target_order_qty"] = df["Order Item Quantity"]

    feature_cols = [
        "weather_risk_index",
        "temp_7d_avg",
        "rain_7d_avg",
        "storm_flag",
        "region_congestion_index",
        "warehouse_workload_score",
        "Order Item Product Price",
        "Sales",
        "Order Item Total",
    ]
    df = df.dropna(subset=feature_cols + ["target_order_qty"])
    return df[feature_cols], df["target_order_qty"]


def train_model(df: pd.DataFrame, output_dir: Path, log_file: Path, metrics_path: Path, dataset_version: str):
    X, y = engineer_features(df)
    if X.empty:
        raise RuntimeError("Global dataset does not contain enough rows for RL training.")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds, squared=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_dir / "inventory_rl_global.pkl")
    schema_path = output_dir / "feature_schema.json"
    schema_path.write_text(json.dumps({"feature_names": X.columns.tolist()}, indent=2))

    metrics = {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "samples": int(len(df)),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2))
    log_file.write_text(
        json.dumps(
            {
                "message": "Inventory RL training complete",
                "rows": int(len(df)),
                "features": X.columns.tolist(),
                "metrics": metrics,
            },
            indent=2,
        )
    )
    logger.info("Inventory RL model saved to %s", output_dir)
    logger.info("Metrics: %s", metrics)
    update_registry_usage(
        "Inventory Optimizer RL",
        dataset_version=dataset_version,
        model_version="v5.3",
    )
    if mae > 5.0:
        log_warning(
            "Inventory Optimizer RL",
            issue=f"MAE {mae:.2f} exceeds threshold",
            suggestion="Review feature engineering and retrain with tuned hyperparameters",
            severity="medium",
            region="GLOBAL",
            model_version="v5.3",
            dataset_version=dataset_version,
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Train Inventory Optimizer RL using global dataset.")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATASET_PATH), help="Path to merged global dataset.")
    parser.add_argument("--global_mode", action="store_true", help="Flag to indicate global mode training.")
    parser.add_argument("--max_rows", type=int, default=None, help="Optional cap on number of rows for quick runs.")
    return parser.parse_args()


def main():
    args = parse_args()
    df = load_global_dataset(args.data)
    if args.max_rows:
        df = df.head(args.max_rows)

    output_dir = Path("models") / "inventory_rl" / "global"
    log_file = Path("results") / "logs" / "train_inventory_rl_global.log"
    metrics_path = Path("results") / "metrics" / "inventory_rl_global.json"
    train_model(df, output_dir, log_file, metrics_path, dataset_version=Path(args.data).name)


if __name__ == "__main__":
    main()
