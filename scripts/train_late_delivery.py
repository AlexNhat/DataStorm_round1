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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split

from modules.data_pipeline.global_dataset_loader import DEFAULT_DATASET_PATH, load_global_dataset
from modules.logging_utils import log_warning, update_registry_usage

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("train_late_delivery")


def ensure_numeric(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        df[column] = default
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(default)
    return df[column]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ensure_numeric(df, "Late_delivery_risk", 0.0)
    ensure_numeric(df, "Days for shipping (real)", 0.0)
    ensure_numeric(df, "Days for shipment (scheduled)", 0.0)
    ensure_numeric(df, "temperature_2m_mean", 0.0)
    ensure_numeric(df, "precipitation_sum", 0.0)
    ensure_numeric(df, "wind_speed_10m_mean", 0.0)
    ensure_numeric(df, "relative_humidity_2m_mean", 50.0)

    df["weather_risk_index"] = (
        0.5 * df["precipitation_sum"]
        + 0.2 * df["wind_speed_10m_mean"]
        + 0.3 * df["relative_humidity_2m_mean"]
    )
    df["avg_weather_risk"] = df.groupby("Region")["weather_risk_index"].transform("mean")

    df["storm_flag"] = np.where(
        (df.get("weather_code", 0) >= 90) | (df["precipitation_sum"] > 30),
        1,
        0,
    )
    df["region_delay_baseline"] = df.groupby("Region")["Late_delivery_risk"].transform("mean")
    df["delay_factor_global"] = df.groupby("record_date")["Late_delivery_risk"].transform("mean")
    df["region_congestion_index"] = (
        df.groupby(["Region", "record_date"])["Order Item Quantity"].transform("sum")
        / (df.groupby("Region")["Order Item Quantity"].transform("mean").replace(0, np.nan).fillna(1.0))
    ).clip(0, 5)

    feature_cols = [
        "weather_risk_index",
        "avg_weather_risk",
        "storm_flag",
        "region_delay_baseline",
        "delay_factor_global",
        "region_congestion_index",
        "Days for shipping (real)",
        "Days for shipment (scheduled)",
    ]
    df = df.dropna(subset=feature_cols)
    X = df[feature_cols]
    y = df["Late_delivery_risk"].astype(int)
    return X, y


def parse_args():
    parser = argparse.ArgumentParser(description="Train Late Delivery Classifier using global dataset.")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--max_rows", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    df = load_global_dataset(args.data)
    if args.max_rows:
        df = df.head(args.max_rows)

    X, y = engineer_features(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = RandomForestClassifier(
        n_estimators=400,
        max_depth=16,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    f1 = f1_score(y_test, preds)
    report = classification_report(y_test, preds, output_dict=True)

    model_dir = Path("models") / "late_delivery" / "global"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, model_dir / "late_delivery_global.pkl")

    metrics_path = Path("results") / "metrics" / "late_delivery_global.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps({"f1": round(float(f1), 4), "report": report}, indent=2))

    log_file = Path("results") / "logs" / "late_delivery_global.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps({"message": "Late delivery model trained", "metrics": {"f1": f1}}, indent=2))
    logger.info("Late delivery classifier trained. F1=%.3f", f1)

    dataset_version = Path(args.data).name
    update_registry_usage(
        "Late Delivery Classifier",
        dataset_version=dataset_version,
        model_version="v4.2",
    )
    if f1 < 0.9:
        log_warning(
            "Late Delivery Classifier",
            issue=f"F1 score {f1:.3f} below desired threshold",
            suggestion="Review congestion features and retrain with balanced samples",
            severity="medium",
            region="GLOBAL",
            model_version="v4.2",
            dataset_version=dataset_version,
        )


if __name__ == "__main__":
    main()
