"""
Supplementary APIs for AI dashboard cards: drift monitor, digital twin quick run,
and strategic reasoning recommendations.
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from modules.data_pipeline.global_dataset_loader import (
    DEFAULT_DATASET_PATH,
    load_global_dataset,
)
from modules.self_learning.drift_detector import ModelDriftDetector

router = APIRouter()

DATA_CACHE_TS: Optional[datetime] = None
DATA_CACHE: Optional[pd.DataFrame] = None
REQUIRED_DRIFT_COLS = ["Late_delivery_risk", "weather_risk_index", "temp_mean_7d"]
SAMPLE_DRIFT_FILE = Path(DEFAULT_DATASET_PATH).parents[1] / "sample" / "drift_sample.json"


def _load_dataset_cached() -> pd.DataFrame:
    global DATA_CACHE_TS, DATA_CACHE  # pylint: disable=global-statement
    if DATA_CACHE is None or DATA_CACHE_TS is None or (datetime.utcnow() - DATA_CACHE_TS).seconds > 600:
        DATA_CACHE = load_global_dataset(str(DEFAULT_DATASET_PATH))
        DATA_CACHE_TS = datetime.utcnow()
    return DATA_CACHE.copy()


def _load_drift_sample_defaults() -> Dict[str, float]:
    if SAMPLE_DRIFT_FILE.exists():
        try:
            return json.loads(SAMPLE_DRIFT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "Late_delivery_risk": 0.2,
        "weather_risk_index": 0.2,
        "temp_mean_7d": 29.5,
    }


def _ensure_required_columns(df: pd.DataFrame, defaults: Dict[str, float]) -> pd.DataFrame:
    for column, default in defaults.items():
        if column not in df.columns:
            df[column] = default
    return df


class DriftCheckRequest(BaseModel):
    region: str = "GLOBAL"
    window_hours: int = Field(72, ge=6, le=720)
    late_delivery_risk: Optional[float] = Field(None, ge=0, le=1, description="Rủi ro giao trễ (0-1)")
    weather_risk_index: Optional[float] = Field(None, ge=0, le=1, description="Chỉ số rủi ro thời tiết (0-1)")
    temp_mean_7d: Optional[float] = Field(None, description="Nhiệt độ trung bình 7 ngày (°C)")


@router.post("/monitoring/drift/check")
async def monitoring_drift_check(payload: DriftCheckRequest):
    """
    Quick drift check based on merged global dataset. Returns drift score and alerts.
    """

    defaults = _load_drift_sample_defaults()
    df = _load_dataset_cached()
    df = _ensure_required_columns(df, defaults)

    region_mask = df["Region"].fillna("GLOBAL_OTHER").str.upper() == payload.region.upper()
    region_df = df[region_mask] if region_mask.any() else df

    user_values = {
        "Late_delivery_risk": payload.late_delivery_risk,
        "weather_risk_index": payload.weather_risk_index,
        "temp_mean_7d": payload.temp_mean_7d,
    }
    missing = [col for col, value in user_values.items() if value is None]
    for col in missing:
        if col in defaults:
            user_values[col] = defaults[col]
    still_missing = [col for col, value in user_values.items() if value is None]
    if still_missing:
        return {
            "status": "invalid_input",
            "message": "Thiếu dữ liệu numeric. Vui lòng nhập các cột Late_delivery_risk, weather_risk_index, temp_mean_7d hoặc dùng chức năng 'Tải dữ liệu mẫu'.",
            "required_columns": REQUIRED_DRIFT_COLS,
        }

    by_feature: Dict[str, float] = {}
    drift_scores: List[float] = []
    detector = ModelDriftDetector(model_name=f"dashboard-{payload.region}", threshold=0.1)

    for feature in REQUIRED_DRIFT_COLS:
        series = region_df[feature].astype(float)
        baseline_mean = float(series.mean())
        baseline_std = float(series.std() or 1.0)
        recent_value = float(user_values[feature])

        detector.reference_buffer.clear()
        detector.current_buffer.clear()
        detector.reference_buffer.extend(series.head(5000).tolist())
        detector.current_buffer.extend([recent_value] * min(500, len(series) or 1))
        score = detector.detect_drift(np.array([recent_value]))
        normalized_shift = abs(recent_value - baseline_mean) / baseline_std

        feature_score = float(max(score, normalized_shift))
        drift_scores.append(feature_score)
        by_feature[feature] = round(feature_score, 3)

    overall_score = max(drift_scores) if drift_scores else 0.0
    if overall_score <= 0.02:
        drift_status = "stable"
        recommendation = "Dữ liệu ổn định, chưa cần retrain."
    elif overall_score <= 0.05:
        drift_status = "warning"
        recommendation = "Dữ liệu bắt đầu lệch nhẹ. Nên kiểm tra lại phân phối dữ liệu và cân nhắc retrain mô hình."
    else:
        drift_status = "critical"
        recommendation = "Drift mạnh, cần kích hoạt quy trình retrain và rà soát pipeline dữ liệu."

    prediction = {
        "drift_score": round(overall_score, 3),
        "status": drift_status,
        "by_feature": by_feature,
        "recommendation": recommendation,
    }
    return {"status": "success", "prediction": prediction}


class DigitalTwinRequest(BaseModel):
    scenario: str = Field("normal", description="Tên kịch bản: normal, demand_surge, weather_storm...")
    duration_days: int = Field(30, ge=1, le=180)
    region: str = "GLOBAL"


@router.post("/api/digital-twin/run")
async def digital_twin_quick_run(payload: DigitalTwinRequest):
    """
    Lightweight simulation summary for the AI dashboard.
    """

    scenario_presets = {
        "normal": {"disruption": 0.02, "risk": 0.12},
        "demand_surge": {"disruption": 0.15, "risk": 0.32},
        "weather_storm": {"disruption": 0.22, "risk": 0.41},
        "port_congestion": {"disruption": 0.18, "risk": 0.37},
        "supplier_disruption": {"disruption": 0.25, "risk": 0.45},
    }
    base = scenario_presets.get(payload.scenario, scenario_presets["normal"])
    inventory_buffer = max(0, (base["disruption"] * 100) - 5)

    scenarios = []
    for scenario_label in ["baseline", "optimistic", "worst_case"]:
        modifier = {"baseline": 0.0, "optimistic": -0.05, "worst_case": 0.08}[scenario_label]
        disruption = max(0.01, base["disruption"] + modifier)
        fulfillment = max(0.5, 0.95 - disruption * 0.5)
        scenarios.append(
            {
                "scenario": scenario_label,
                "fulfillment_rate": round(fulfillment, 3),
                "cost_impact": round(disruption * 1.8, 3),
                "risk_score": round(base["risk"] + modifier, 3),
                "explanation": "Ổn định" if scenario_label == "optimistic" else "Cần dự phòng thêm",
            }
        )

    timeline = []
    for day in range(payload.duration_days):
        rate = scenarios[0]["fulfillment_rate"] - base["disruption"] * (day / payload.duration_days) * 0.2
        timeline.append({"day": day + 1, "fulfillment_rate": round(max(0.5, rate), 3)})

    result = {
        "scenario_summary": scenarios,
        "region": payload.region,
        "duration_days": payload.duration_days,
        "recommended_buffer_percent": round(inventory_buffer, 1),
        "timeline": timeline[:30],
        "key_metrics": {
            "disruption_index": round(base["disruption"], 3),
            "supply_demand_gap": round(base["disruption"] * 0.4, 3),
            "simulated_cost_delta": round(base["disruption"] * 2.5, 2),
        },
        "recommendation": "Tăng tồn kho dự phòng và lập kế hoạch vận chuyển thay thế."
        if base["disruption"] >= 0.15
        else "Hệ thống ổn định, tiếp tục giám sát drift và tồn kho.",
    }
    return {"status": "success", "prediction": result}


class StrategyRequest(BaseModel):
    region: str = "GLOBAL"
    season: str = "all"
    inventory: float = 10000
    demand_outlook: str = Field("neutral", description="neutral / surge / slow")
    risk_focus: str = Field("balanced", description="balanced / growth / cost")


@router.post("/api/strategy/recommend")
async def quick_strategy_recommend(payload: StrategyRequest):
    """
    Return lightweight strategic recommendations for the dashboard card.
    """

    base_confidence = {"balanced": 0.72, "growth": 0.68, "cost": 0.66}.get(payload.risk_focus, 0.65)
    strategy_pool = [
        {
            "name": "Tăng tồn kho vùng EU",
            "focus": "inventory",
            "confidence": round(base_confidence + 0.05, 3),
            "reasoning": ["Dự báo demand surge EU", "Lead-time dài hơn 1.5 ngày", "Drift logistics cao"],
            "risk_score": 0.32,
            "expected_reward": 0.78,
        },
        {
            "name": "Ưu tiên vận chuyển đường biển rút gọn",
            "focus": "logistics",
            "confidence": round(base_confidence, 3),
            "reasoning": ["Chi phí vận tải tăng 3%", "Đường hàng không hạn chế slot"],
            "risk_score": 0.28,
            "expected_reward": 0.71,
        },
        {
            "name": "Tập trung khách hàng trọng điểm",
            "focus": "retention",
            "confidence": round(base_confidence - 0.02, 3),
            "reasoning": ["Churn tăng ở phân khúc cao cấp", "Margin cao có thể bù khuyến mại"],
            "risk_score": 0.21,
            "expected_reward": 0.67,
        },
    ]

    strategies = []
    for entry in strategy_pool:
        strategies.append(
            {
                "name": entry["name"],
                "focus": entry["focus"],
                "confidence": entry["confidence"],
                "summary": entry["reasoning"][0],
                "risk_score": entry["risk_score"],
                "expected_reward": entry["expected_reward"],
                "reasoning_steps": entry["reasoning"],
            }
        )

    result = {
        "region": payload.region,
        "season": payload.season,
        "inventory": payload.inventory,
        "demand_outlook": payload.demand_outlook,
        "strategies": strategies,
        "recommendation": "Ưu tiên chiến lược đầu tiên nếu confidence > 0.7, kết hợp monitoring drift & pricing.",
    }
    return {"status": "success", "prediction": result}
