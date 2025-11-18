"""
Utility functions for loading the merged global supply chain & weather dataset.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_PATH = BASE_DIR / "data" / "merged" / "supplychain_weather_merged_global.csv"

REQUIRED_COLUMNS = [
    "Country",
    "City",
    "record_date",
    "region_detected",
]

REGION_LUT = {
    "EU": "EU",
    "APAC": "APAC",
    "NA": "NA",
    "LATAM": "LATAM",
    "AFRICA": "AFRICA",
    "MENA": "MENA",
}

WEATHER_KEYWORDS = ["weather", "temp", "precip", "rain", "storm", "humidity", "wind", "dew", "sunshine"]

logger = logging.getLogger("global_dataset_loader")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _detect_weather_columns(columns: Iterable[str]) -> List[str]:
    weather_cols: List[str] = []
    for col in columns:
        lower = col.lower()
        if any(keyword in lower for keyword in WEATHER_KEYWORDS):
            weather_cols.append(col)
    return weather_cols


def _normalize_text(value: Optional[str]) -> str:
    if pd.isna(value) or value is None:
        return ""
    text = str(value).strip()
    return " ".join(word.capitalize() for word in text.split())


def _normalize_region(value: str) -> str:
    if not value:
        return "GLOBAL_OTHER"
    upper = value.strip().upper()
    return REGION_LUT.get(upper, "GLOBAL_OTHER")


def _parse_date_column(df: pd.DataFrame) -> pd.Series:
    if "record_date" in df.columns:
        col = "record_date"
    else:
        candidates = [c for c in df.columns if "date" in c.lower()]
        if not candidates:
            raise ValueError("Global dataset missing any date column.")
        col = candidates[0]
    return pd.to_datetime(df[col], errors="coerce")


def load_global_dataset(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the merged global dataset with schema validation, normalization and weather imputation.
    """
    dataset_path = Path(path or DEFAULT_DATASET_PATH)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Global dataset not found at {dataset_path}")

    logger.info("Loading global dataset: %s", dataset_path)
    df = pd.read_csv(dataset_path)

    missing_required = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_required:
        logger.warning("Dataset missing required columns: %s", missing_required)

    df["Country"] = df.get("Country", df.get("country_norm", "")).fillna("")
    df["City"] = df.get("City", df.get("city_norm", "")).fillna("")
    df["Region"] = df.get("region_detected", df.get("Region", ""))
    df["Region"] = df["Region"].fillna("").apply(_normalize_region)
    df["City"] = df["City"].apply(_normalize_text)

    df["record_date"] = _parse_date_column(df)
    df["record_date"] = df["record_date"].fillna(method="ffill").fillna(method="bfill")

    weather_cols = _detect_weather_columns(df.columns)
    for col in weather_cols:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            df[col] = series
        else:
            with pd.option_context("mode.use_inf_as_na", True):
                df[col] = pd.to_numeric(series, errors="coerce")

    for col in weather_cols:
        if col not in df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        df[col] = df.groupby("Region")[col].transform(lambda s: s.fillna(s.median()))
        df[col] = df[col].fillna(df[col].median())

    df.sort_values("record_date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    logger.info("Loaded %d rows with %d columns", len(df), len(df.columns))
    return df


__all__ = ["load_global_dataset", "DEFAULT_DATASET_PATH"]
