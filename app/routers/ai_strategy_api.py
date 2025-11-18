"""
Modern AI Strategy endpoints (V8+) exposed under /ai/strategy.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from modules.cognitive.strategy_engine import StrategyEngine, Strategy
from modules.cognitive.planner_agent import PlannerAgent

router = APIRouter()

PLAN_CACHE: Dict[str, Dict[str, Any]] = {}
RESULTS_DIR = Path("results")
PLAN_OUTPUT_DIR = RESULTS_DIR / "strategic_plans"


class StrategyPayload(BaseModel):
    """Request body for strategy generation."""

    objectives: List[str] = Field(default_factory=lambda: ["balance"])
    region: str = "VN"
    season: str = "summer"
    inputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_results: Dict[str, Any] = Field(default_factory=dict)


class StrategyExportRequest(BaseModel):
    """Request body for exporting a plan."""

    strategy: Dict[str, Any]
    strategies: List[Dict[str, Any]] = Field(default_factory=list)
    inputs: Optional[Dict[str, Any]] = None
    plan_token: Optional[str] = None


class ScenarioRequest(BaseModel):
    """Payload cho what-if scenario."""

    strategy_id: str
    plan_token: Optional[str] = None
    adjustments: Dict[str, float] = Field(default_factory=dict)


def _build_business_context(payload: StrategyPayload) -> Dict[str, Any]:
    """Map UI payload to StrategyEngine business context."""

    inventory_total = float(payload.inputs.get("inventory", payload.inputs.get("current_inventory", 10000)))
    inventory_split = {
        "product_a": round(inventory_total * 0.45, 2),
        "product_b": round(inventory_total * 0.35, 2),
        "product_c": round(inventory_total * 0.20, 2),
    }

    weather_risk = float(payload.inputs.get("weather_risk", 0.3))
    return {
        "current_inventory": inventory_split,
        "season": payload.season,
        "region": payload.region,
        "avg_lead_time": payload.inputs.get("avg_lead_time", 4),
        "warehouses": payload.metadata.get("warehouses", ["warehouse_hn", "warehouse_hcm"]),
        "weather_forecast": {
            "precipitation_forecast": round(weather_risk * 100, 2),
            "wind_forecast": 15,
            "temperature": payload.inputs.get("temperature", 27),
        },
        "logistics_cost": payload.inputs.get("logistics_cost"),
        "budget_ceiling": payload.inputs.get("budget_ceiling"),
    }


def _derive_service_level(kpis: Dict[str, Any]) -> float:
    """Convert KPI dictionary to service level impact (0-1)."""

    if not kpis:
        return 0.0
    if "service_level_improvement" in kpis:
        return float(kpis["service_level_improvement"]) / 100
    if "service_level" in kpis:
        return float(kpis["service_level"]) / 100
    return 0.0


def _derive_lead_time_delta(kpis: Dict[str, Any]) -> float:
    """Estimate lead time delta in days from KPI data."""

    if not kpis:
        return 0.0
    if "lead_time_buffer_increase" in kpis:
        return round(float(kpis["lead_time_buffer_increase"]) / 100, 2)
    if "lead_time_delta_days" in kpis:
        return float(kpis["lead_time_delta_days"])
    return 0.0


def _derive_risk_level(confidence: float) -> str:
    """Map confidence to qualitative risk level."""

    if confidence >= 0.78:
        return "low"
    if confidence >= 0.6:
        return "medium"
    return "high"


def _serialize_strategy(strategy: Strategy, payload: StrategyPayload) -> Dict[str, Any]:
    """Convert Strategy dataclass into UI-friendly dictionary."""

    service_level = _derive_service_level(strategy.kpis)
    lead_time_delta = _derive_lead_time_delta(strategy.kpis)
    risk_score = max(0.05, 1 - float(strategy.confidence or 0.5))
    return {
        "id": strategy.id,
        "name": strategy.name,
        "description": strategy.description,
        "kpis": strategy.kpis or {},
        "risks": strategy.risks or [],
        "confidence": float(strategy.confidence or 0.6),
        "estimated_cost": float(strategy.estimated_cost or 0),
        "estimated_revenue": float(strategy.estimated_revenue or 0),
        "estimated_profit": float(strategy.estimated_profit or 0),
        "time_horizon": strategy.time_horizon,
        "objectives": payload.objectives,
        "tags": list(dict.fromkeys(payload.objectives + [strategy.time_horizon])),
        "action_plan": strategy.actions or [],
        "service_level_impact": service_level,
        "lead_time_impact_days": lead_time_delta,
        "risk_level": _derive_risk_level(strategy.confidence or 0),
        "risk_score": risk_score,
        "simulation_scores": {
            "service_level": service_level,
            "cost_delta": float(strategy.estimated_profit or 0) / max(float(strategy.estimated_cost or 1), 1),
            "lead_time": lead_time_delta,
            "risk": risk_score,
        },
        "status": "deployed" if strategy.confidence >= 0.75 else "analysis",
        "reasoning": _build_reasoning(strategy, payload, service_level, lead_time_delta),
    }


def _build_reasoning(
    strategy: Strategy,
    payload: StrategyPayload,
    service_level: float,
    lead_time_delta: float,
) -> Dict[str, Any]:
    """Sinh cấu trúc giải thích AI cho UI."""

    kpis = strategy.kpis or {}
    raw_features: List[Dict[str, Any]] = []
    total = 0.0
    for key, value in kpis.items():
        try:
            importance = abs(float(value)) if isinstance(value, (int, float)) else 0.0
        except (TypeError, ValueError):
            importance = 0.0
        total += importance
        raw_features.append({"name": key, "raw_value": value, "importance": importance})

    if not total:
        total = 1.0

    features = [
        {
            "name": item["name"],
            "importance": round(item["importance"] / total, 3),
            "raw_value": item["raw_value"],
        }
        for item in sorted(raw_features, key=lambda x: x["importance"], reverse=True)[:5]
    ]

    recommended_action = ""
    if strategy.actions:
        first_action = strategy.actions[0]
        if isinstance(first_action, dict):
            recommended_action = first_action.get("title") or first_action.get("type", "")
        else:
            recommended_action = str(first_action)

    return {
        "proposal_id": f"{strategy.id}-reasoning",
        "strategy_id": strategy.id,
        "title": strategy.name,
        "description": strategy.description[:240] + ("..." if len(strategy.description) > 240 else ""),
        "features": features,
        "confidence": float(strategy.confidence or 0.6),
        "recommended_action": recommended_action,
        "scenario_id": f"scenario-{strategy.id}",
        "priority": "high" if (strategy.confidence or 0) >= 0.8 else "medium",
        "raw_context": {
            "service_level": service_level,
            "lead_time_delta": lead_time_delta,
            "region": payload.region,
            "season": payload.season,
            "objectives": payload.objectives,
        },
    }


def _build_plan_markdown(
    strategy: Dict[str, Any],
    inputs: Optional[Dict[str, Any]],
    all_strategies: List[Dict[str, Any]],
) -> str:
    """Generate Markdown content for the plan export."""

    inputs = inputs or {}
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    kpi_lines = "\n".join(f"- **{key}**: {value}" for key, value in (strategy.get("kpis") or {}).items())
    action_lines = "\n".join(
        f"1. {action.get('title', action.get('type', 'Action'))}: {action.get('details', action)}"
        for action in strategy.get("action_plan", [])
    ) or "1. (Chưa có action cụ thể)"

    comparison_table = "\n".join(
        f"| {item['name']} | {item.get('risk_level', '—')} | {item.get('service_level_impact', 0):.2f} | "
        f"{item.get('lead_time_impact_days', 0):.2f} | {item.get('confidence', 0):.2f} |"
        for item in all_strategies[:5]
    )
    if comparison_table:
        comparison_table = (
            "| Chiến lược | Rủi ro | Δ Service | Δ Lead Time | Tin cậy |\n"
            "|-----------|--------|-----------|-------------|---------|\n"
            + comparison_table
        )

    return f"""# Strategic Execution Plan - {strategy.get('name')}

- Generated at: {now}
- Objectives: {', '.join(strategy.get('objectives', []))}
- Region / Season: {inputs.get('region', 'N/A')} / {inputs.get('season', 'N/A')}
- Budget ceiling: {inputs.get('budget_ceiling', 'N/A')}

## 1. Business Context
- Inventory snapshot: {inputs.get('inventory', inputs.get('current_inventory', 'N/A'))}
- Demand forecast: {inputs.get('demand_forecast', 'N/A')}
- Weather risk: {inputs.get('weather_risk', 'N/A')}
- Risk tolerance: {inputs.get('risk_tolerance', 'medium')}

## 2. Selected Strategy
- Estimated cost: {strategy.get('estimated_cost')}
- Estimated revenue: {strategy.get('estimated_revenue')}
- Confidence: {strategy.get('confidence')}
- Risk level: {strategy.get('risk_level')}

### KPI Highlights
{kpi_lines or '- (Chưa có KPI)'}

## 3. Action Plan
{action_lines}

## 4. KPI Comparison
{comparison_table or 'Chưa có dữ liệu so sánh.'}

## 5. 30-60-90 Day Roadmap
- **30 ngày**: Khởi động action ưu tiên và thiết lập monitoring.
- **60 ngày**: Đánh giá lại KPI, cập nhật dự báo supply/demand.
- **90 ngày**: Chuẩn bị vòng chiến lược tiếp theo và cập nhật ngân sách.

## 6. Risk Assessment
- Weather risk: {inputs.get('weather_risk', 'N/A')}
- Logistics cost: {inputs.get('logistics_cost', 'N/A')}
- Mitigation: Ưu tiên warehouses có buffer, phối hợp Control Center để giám sát action.

"""


@router.post("/generate")
async def generate_strategies(payload: StrategyPayload):
    """Generate enriched strategies plus recommendations."""

    try:
        strategy_engine = StrategyEngine()
        planner = PlannerAgent()

        business_context = _build_business_context(payload)
        strategies = strategy_engine.generate_strategies(
            model_results=payload.model_results,
            business_context=business_context,
            objectives=payload.objectives,
        )
        comparison = strategy_engine.compare_strategies(strategies)
        recommendations = planner.generate_recommendations(
            strategies=strategies,
            comparison=comparison,
            context=business_context,
        )

        serialized = [_serialize_strategy(strategy, payload) for strategy in strategies]
        plan_token = uuid4().hex
        PLAN_CACHE[plan_token] = {
            "strategies": serialized,
            "strategies_map": {item["id"]: item for item in serialized},
            "inputs": {
                **payload.dict(exclude={"model_results"}),
                "region": payload.region,
                "season": payload.season,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        return {
            "status": "success",
            "plan_token": plan_token,
            "generated_at": PLAN_CACHE[plan_token]["generated_at"],
            "strategies": serialized,
            "comparison": comparison,
            "reasoning": [item["reasoning"] for item in serialized],
            "recommendations": recommendations,
        }
    except Exception as error:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Strategy generation error: {error}") from error


@router.post("/export")
async def export_plan(payload: StrategyExportRequest):
    """Generate markdown plan and stream the file back to the UI."""

    if payload.plan_token and payload.plan_token in PLAN_CACHE:
        cached = PLAN_CACHE[payload.plan_token]
        strategies = payload.strategies or cached["strategies"]
        inputs = payload.inputs or cached["inputs"]
    else:
        strategies = payload.strategies
        inputs = payload.inputs or {}

    if not strategies:
        raise HTTPException(status_code=400, detail="Không có dữ liệu chiến lược để xuất.")

    primary_strategy = payload.strategy or strategies[0]
    PLAN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"PLAN_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.md"
    plan_path = PLAN_OUTPUT_DIR / filename

    markdown_body = _build_plan_markdown(primary_strategy, inputs, strategies)
    plan_path.write_text(markdown_body, encoding="utf-8")

    response = FileResponse(plan_path, media_type="text/markdown", filename=filename)
    response.headers["X-Plan-Filename"] = filename
    return response


@router.post("/scenario")
async def simulate_scenario(request: ScenarioRequest):
    """Simple what-if simulator dựa trên adjustments."""

    base_strategy: Optional[Dict[str, Any]] = None
    if request.plan_token and request.plan_token in PLAN_CACHE:
        base_strategy = PLAN_CACHE[request.plan_token]["strategies_map"].get(request.strategy_id)

    if base_strategy is None:
        # Search globally as fallback
        for cache in PLAN_CACHE.values():
            base_strategy = cache["strategies_map"].get(request.strategy_id)
            if base_strategy:
                break

    if base_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found for scenario simulation.")

    adjustments = request.adjustments or {}
    weather_delta = float(adjustments.get("weather_risk_delta", 0.0))
    lead_delta = float(adjustments.get("lead_time_delta", 0.0))
    demand_delta = float(adjustments.get("demand_delta", 0.0))

    base_service = float(base_strategy.get("service_level_impact", 0.85))
    base_lead = float(base_strategy.get("lead_time_impact_days", 0.0))
    base_cost = float(base_strategy.get("estimated_cost", 0.0))

    new_service = max(0.1, min(0.99, base_service - weather_delta * 0.15 + demand_delta * 0.05))
    new_lead = base_lead + lead_delta + weather_delta * 0.5
    new_cost = base_cost * (1 + demand_delta * 0.03 + weather_delta * 0.04)

    chart_points = [
        {"label": "Service level", "value": round(new_service * 100, 2)},
        {"label": "Lead time Δ", "value": round(new_lead, 2)},
        {"label": "Cost", "value": round(new_cost, 2)},
    ]

    return {
        "status": "success",
        "strategy_id": request.strategy_id,
        "scenario_summary": {
            "service_level": new_service,
            "lead_time_impact_days": new_lead,
            "estimated_cost": new_cost,
            "notes": f"Weather Δ {weather_delta:+.2f}, Lead Δ {lead_delta:+.2f}, Demand Δ {demand_delta:+.2f}",
        },
        "chart_points": chart_points,
    }
