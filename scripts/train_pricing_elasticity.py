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
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from modules.data_pipeline.global_dataset_loader import DEFAULT_DATASET_PATH, load_global_dataset
from modules.logging_utils import log_warning, update_registry_usage

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("train_pricing")


def ensure_numeric(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        df[column] = default
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(default)
    return df[column]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ensure_numeric(df, "Order Item Quantity", 0.0)
    ensure_numeric(df, "Product Price", 0.0)
    ensure_numeric(df, "Sales", 0.0)
    ensure_numeric(df, "temperature_2m_mean", 0.0)
    ensure_numeric(df, "precipitation_sum", 0.0)
    ensure_numeric(df, "relative_humidity_2m_mean", 50.0)

    df["weather_risk_index"] = (
        0.4 * df["precipitation_sum"]
        + 0.2 * df["relative_humidity_2m_mean"]
        + 0.4 * df["temperature_2m_mean"].abs()
    )

    df["weather_influence"] = (
        df.groupby("Region")["weather_risk_index"].transform("mean").fillna(df["weather_risk_index"])
    )

    df["price_log"] = np.log1p(df["Product Price"])
    df["sales_log"] = np.log1p(df["Sales"])
    df["quantity_log"] = np.log1p(df["Order Item Quantity"])

    category_encoded = pd.get_dummies(df.get("Category Name", ""), prefix="cat", dummy_na=False)
    region_encoded = pd.get_dummies(df["Region"], prefix="region", dummy_na=False)
    features = pd.concat(
        [
            df[["price_log", "sales_log", "weather_risk_index", "weather_influence"]],
            category_encoded,
            region_encoded,
        ],
        axis=1,
    )
    target = df["quantity_log"]
    features, target = features.align(target, join="inner", axis=0)
    return features, target

def parse_args():
    parser = argparse.ArgumentParser(description="Train pricing elasticity model using global dataset.")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--max_rows", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    df = load_global_dataset(args.data)
    if args.max_rows:
        df = df.head(args.max_rows)

    X, y = engineer_features(df)
    feature_names = X.columns.tolist()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = ElasticNet(alpha=0.0005, l1_ratio=0.3, max_iter=5000, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    model_dir = Path("models") / "pricing" / "global"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "pricing_elasticity.pkl")

    metrics_path = Path("results") / "metrics" / "pricing_global.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps({"mae": round(float(mae), 4), "rows": int(len(df))}, indent=2))

    schema_path = model_dir / "feature_columns.json"
    schema_path.write_text(json.dumps({"feature_names": feature_names}, indent=2))

    log_file = Path("results") / "logs" / "pricing_global.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(
        json.dumps({"message": "Pricing elasticity model trained", "mae": float(mae), "features": int(X.shape[1])}, indent=2)
    )
    logger.info("Pricing elasticity model trained. MAE=%.4f", mae)

    dataset_version = Path(args.data).name
    update_registry_usage(
        "Pricing Elasticity Model",
        dataset_version=dataset_version,
        model_version="v3.1",
    )
    if mae > 0.15:
        log_warning(
            "Pricing Elasticity Model",
            issue=f"MAE {mae:.3f} indicates weak elasticity fit",
            suggestion="Consider recalibrating alpha/l1_ratio and rebalancing training data",
            severity="low",
            region="GLOBAL",
            model_version="v3.1",
            dataset_version=dataset_version,
        )


if __name__ == "__main__":
    main()
