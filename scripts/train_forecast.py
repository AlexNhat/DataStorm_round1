import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from modules.data_pipeline.global_dataset_loader import DEFAULT_DATASET_PATH, load_global_dataset
from modules.logging_utils import log_warning, update_registry_usage

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("train_forecast")


def ensure_numeric(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        df[column] = default
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(default)
    return df[column]


def add_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ensure_numeric(df, "temperature_2m_mean", 0.0)
    ensure_numeric(df, "precipitation_sum", 0.0)
    ensure_numeric(df, "wind_speed_10m_mean", 0.0)
    ensure_numeric(df, "relative_humidity_2m_mean", 50.0)
    ensure_numeric(df, "weather_code", 0.0)

    df["weather_risk_index"] = (
        0.5 * df["precipitation_sum"]
        + 0.2 * df["wind_speed_10m_mean"]
        + 0.3 * df["relative_humidity_2m_mean"]
    )
    df["extreme_event_flag"] = np.where(
        (df["weather_code"] >= 90) | (df["precipitation_sum"] > 40) | (df["wind_speed_10m_mean"] > 25),
        1,
        0,
    )
    return df


def prepare_forecast_table(df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    df = add_weather_features(df)
    ensure_numeric(df, "Sales", 0.0)
    ensure_numeric(df, "Order Item Quantity", 0.0)
    df.sort_values(group_cols + ["record_date"], inplace=True)

    agg = (
        df.groupby(group_cols + ["record_date"])
        .agg(
            Sales=("Sales", "sum"),
            Quantity=("Order Item Quantity", "sum"),
            weather_risk_index=("weather_risk_index", "mean"),
            extreme_event_flag=("extreme_event_flag", "max"),
            temp_mean=("temperature_2m_mean", "mean"),
            rain_sum=("precipitation_sum", "mean"),
        )
        .reset_index()
    )

    agg["sales_lag_7"] = agg.groupby(group_cols)["Sales"].shift(7)
    agg["sales_7d_mean"] = (
        agg.groupby(group_cols)["Sales"]
        .transform(lambda s: s.rolling(window=7, min_periods=1).mean())
    )
    agg["rain_7d_mean"] = (
        agg.groupby(group_cols)["rain_sum"]
        .transform(lambda s: s.rolling(window=7, min_periods=1).mean())
    )
    agg["temp_7d_mean"] = (
        agg.groupby(group_cols)["temp_mean"]
        .transform(lambda s: s.rolling(window=7, min_periods=1).mean())
    )
    agg.fillna(method="bfill", inplace=True)
    agg.fillna(method="ffill", inplace=True)

    feature_cols = [
        "Quantity",
        "weather_risk_index",
        "extreme_event_flag",
        "temp_mean",
        "rain_sum",
        "sales_lag_7",
        "sales_7d_mean",
        "rain_7d_mean",
        "temp_7d_mean",
    ]
    agg = agg.dropna(subset=feature_cols + ["Sales"])
    return agg, feature_cols


def train_forecast_scope(df: pd.DataFrame, group_cols: List[str], scope_name: str, model_dir: Path) -> Dict[str, float]:
    logger.info("Training forecast model for scope: %s", scope_name)
    table, feature_cols = prepare_forecast_table(df, group_cols)
    if table.empty:
        logger.warning("No data for scope %s; skipping.", scope_name)
        return {}

    X = table[feature_cols]
    y = table["Sales"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=14,
        min_samples_leaf=4,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds, squared=False)

    scope_dir = model_dir / f"{scope_name}_model"
    scope_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, scope_dir / "forecast.pkl")

    metrics = {
        "scope": scope_name,
        "rows": int(len(table)),
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
    }
    return metrics


def parse_args():
    parser = argparse.ArgumentParser(description="Train demand forecast ensemble using global dataset.")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATASET_PATH), help="Path to merged global dataset.")
    parser.add_argument("--global_mode", action="store_true", help="Enable global mode (default True).")
    parser.add_argument("--max_rows", type=int, default=None, help="Optional cap on number of rows.")
    return parser.parse_args()


def main():
    args = parse_args()
    df = load_global_dataset(args.data)
    if args.max_rows:
        df = df.head(args.max_rows)
    df["GLOBAL"] = "GLOBAL"

    model_dir = Path("models") / "forecast" / "global"
    metrics_path = Path("results") / "metrics" / "forecast_global.json"
    log_file = Path("results") / "logs" / "forecast_global.log"
    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    metrics = []
    metrics.append(train_forecast_scope(df, ["Country"], "country", model_dir))
    metrics.append(train_forecast_scope(df, ["Region"], "region", model_dir))
    metrics.append(train_forecast_scope(df, ["GLOBAL"], "global", model_dir))

    metrics = [m for m in metrics if m]
    metrics_path.write_text(json.dumps(metrics, indent=2))
    log_file.write_text(json.dumps({"message": "Forecast training complete", "scopes": metrics}, indent=2))
    logger.info("Forecast training complete.")
    dataset_version = Path(args.data).name
    update_registry_usage(
        "Demand Forecast Ensemble",
        dataset_version=dataset_version,
        model_version="v7.5",
    )
    if metrics:
        max_mae = max(scope["mae"] for scope in metrics if "mae" in scope)
        if max_mae > 10.0:
            log_warning(
                "Demand Forecast Ensemble",
                issue=f"Scope MAE up to {max_mae:.2f}",
                suggestion="Review per-region residuals and retrain if necessary",
                severity="medium",
                region="GLOBAL",
                model_version="v7.5",
                dataset_version=dataset_version,
            )


if __name__ == "__main__":
    main()
