import json
import logging
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
SUPPLY_PATH = BASE_DIR / "data" / "DataCoSupplyChainDataset.csv"
WEATHER_PATH = BASE_DIR / "data" / "geocoded_weather.csv"
MERGED_OUTPUT = BASE_DIR / "data" / "merged" / "supplychain_weather_merged_global.csv"
MISSING_LOG = BASE_DIR / "results" / "logs" / "weather_mapping_missing_global.csv"
STATS_OUTPUT = BASE_DIR / "results" / "logs" / "weather_merge_stats_global.csv"

REGION_LUT: Dict[str, List[str]] = {
    "EU": ["DE", "FR", "IT", "ES", "NL", "BE", "PL", "SE", "NO", "FI", "DK", "AT", "CH", "IE", "PT", "CZ", "GR"],
    "APAC": ["VN", "TH", "SG", "PH", "CN", "KR", "JP", "MY", "ID", "AU", "NZ", "IN"],
    "NA": ["US", "CA", "MX"],
    "LATAM": ["BR", "AR", "CL", "PE", "CO"],
    "AFRICA": ["ZA", "NG", "EG", "KE", "MA"],
    "MENA": ["AE", "SA", "QA", "KW", "BH", "OM", "TR"],
}

logger = logging.getLogger("merge_supply_weather_global")
logger.setLevel(logging.INFO)


def ensure_directories():
    MERGED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MISSING_LOG.parent.mkdir(parents=True, exist_ok=True)


def normalize_text(value: Optional[str]) -> str:
    if pd.isna(value) or value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(word.capitalize() for word in text.split())


def normalize_country(value: Optional[str]) -> str:
    text = normalize_text(value)
    return text.upper()


def detect_region(country_code: str) -> str:
    code = country_code.upper()
    for region, codes in REGION_LUT.items():
        if code in codes:
            return region
    return "GLOBAL_OTHER"


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    lower_map = {col.lower(): col for col in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def standardize_supply_chain(df: pd.DataFrame) -> pd.DataFrame:
    supply = df.copy()
    country_col = _find_column(supply, ["Order Country", "Customer Country", "Country"])
    city_col = _find_column(supply, ["Order City", "Customer City", "City"])
    state_col = _find_column(supply, ["Order State", "Customer State", "State"])
    date_col = _find_column(
        supply,
        [
            "order date (DateOrders)",
            "order date",
            "shipping date (DateOrders)",
            "date",
        ],
    )
    if not country_col or not city_col or not date_col:
        raise ValueError("Supply chain dataset missing location/date columns.")

    supply["country_norm"] = supply[country_col].apply(normalize_country)
    supply["city_norm"] = supply[city_col].apply(normalize_text)
    if state_col:
        supply["state_norm"] = supply[state_col].apply(normalize_text)
    else:
        supply["state_norm"] = ""
    supply["record_date"] = pd.to_datetime(supply[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
    supply["region_detected"] = supply["country_norm"].apply(detect_region)
    if "Latitude" in supply.columns and "Longitude" in supply.columns:
        supply["lat_round"] = supply["Latitude"].round(1)
        supply["lon_round"] = supply["Longitude"].round(1)
    else:
        supply["lat_round"] = np.nan
        supply["lon_round"] = np.nan
    return supply


def preprocess_weather_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    weather = chunk.copy()
    country_weather_col = _find_column(weather, ["country"])
    city_weather_col = _find_column(weather, ["city"])
    state_weather_col = _find_column(weather, ["state", "province"])
    date_weather_col = _find_column(weather, ["record_date", "date", "datetime", "order_date"])

    if not country_weather_col or not city_weather_col or not date_weather_col:
        raise ValueError("Weather dataset missing required columns.")

    weather["country_norm"] = weather[country_weather_col].apply(normalize_country)
    weather["city_norm"] = weather[city_weather_col].apply(normalize_text)
    if state_weather_col:
        weather["state_norm"] = weather[state_weather_col].apply(normalize_text)
    else:
        weather["state_norm"] = ""
    weather["record_date"] = pd.to_datetime(weather[date_weather_col], errors="coerce").dt.strftime("%Y-%m-%d")
    lat_col = _find_column(weather, ["latitude", "lat"])
    lon_col = _find_column(weather, ["longitude", "lon"])
    if lat_col and lon_col:
        weather["lat_round"] = weather[lat_col].round(1)
        weather["lon_round"] = weather[lon_col].round(1)
    else:
        weather["lat_round"] = np.nan
        weather["lon_round"] = np.nan
    return weather


def merge_stage(
    supply_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    keys: List[str],
    stage_name: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    merge_cols = [col for col in weather_df.columns if col not in keys]
    subset_weather = weather_df[keys + merge_cols].drop_duplicates(subset=keys)
    merged = supply_df.merge(subset_weather, on=keys, how="left", indicator=True, suffixes=("", f"_w_{stage_name}"))
    matched = merged[merged["_merge"] == "both"].drop(columns=["_merge"])
    if not matched.empty:
        matched["weather_match_stage"] = stage_name
        matched["weather_matched"] = True
    remaining_cols = [col for col in supply_df.columns]
    unmatched = merged[merged["_merge"] == "left_only"][remaining_cols]
    return matched, unmatched


def merge_supply_weather() -> None:
    ensure_directories()
    supply_df = pd.read_csv(SUPPLY_PATH, encoding="latin-1")
    supply_norm = standardize_supply_chain(supply_df)
    unmatched = supply_norm.copy()
    merged_rows: List[pd.DataFrame] = []
    missing_records: List[Dict[str, Any]] = []

    for chunk in pd.read_csv(WEATHER_PATH, chunksize=100_000, encoding="utf-8"):
        weather_norm = preprocess_weather_chunk(chunk)
        if unmatched.empty:
            break

        # Stage 1: exact city
        matched_city, unmatched = merge_stage(
            unmatched,
            weather_norm,
            keys=["country_norm", "city_norm", "record_date"],
            stage_name="city",
        )
        merged_rows.append(matched_city)
        if unmatched.empty:
            continue

        # Stage 2: state/province
        matched_state, unmatched = merge_stage(
            unmatched,
            weather_norm,
            keys=["country_norm", "state_norm", "record_date"],
            stage_name="state",
        )
        merged_rows.append(matched_state)
        if unmatched.empty:
            continue

        # Stage 3: geolocation grid (if lat/lon available)
        if unmatched["lat_round"].notna().any() and weather_norm["lat_round"].notna().any():
            matched_geo, unmatched = merge_stage(
                unmatched,
                weather_norm,
                keys=["country_norm", "lat_round", "lon_round", "record_date"],
                stage_name="geo",
            )
            merged_rows.append(matched_geo)

    if unmatched.empty:
        merged_df = pd.concat(merged_rows, ignore_index=True)
    else:
        merged_df = pd.concat(
            merged_rows + [unmatched.assign(weather_matched=False, weather_match_stage="missing")],
            ignore_index=True,
        )
        missing_records = unmatched[["Country", "City", "State", "record_date", "region_detected"]].to_dict("records")

    merged_df["region_detected"] = merged_df["region_detected"].fillna(
        merged_df["country_norm"].apply(detect_region)
    )
    if "weather_matched" not in merged_df.columns:
        merged_df["weather_matched"] = False
    merged_df.to_csv(MERGED_OUTPUT, index=False, encoding="utf-8")

    if missing_records:
        pd.DataFrame(missing_records).to_csv(MISSING_LOG, index=False, encoding="utf-8")
    else:
        pd.DataFrame(columns=["Country", "City", "State", "record_date", "region_detected"]).to_csv(
            MISSING_LOG, index=False, encoding="utf-8"
        )

    stats = merged_df.groupby("region_detected").agg(
        total_rows=pd.NamedAgg(column="region_detected", aggfunc="size"),
        mapped_rows=pd.NamedAgg(column="weather_matched", aggfunc=lambda s: int(s.fillna(False).sum())),
    ).reset_index()
    stats["missing_rows"] = stats["total_rows"] - stats["mapped_rows"]
    stats["success_rate_pct"] = np.where(
        stats["total_rows"] > 0,
        (stats["mapped_rows"] / stats["total_rows"]) * 100,
        0.0,
    )
    stats.to_csv(STATS_OUTPUT, index=False, encoding="utf-8")
    logger.info("Merged dataset written to %s", MERGED_OUTPUT)
    logger.info("Missing log written to %s", MISSING_LOG)
    logger.info("Stats written to %s", STATS_OUTPUT)


if __name__ == "__main__":
    merge_supply_weather()
