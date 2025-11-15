"""
Cognitive API: endpoints cho V8 Strategic / Cognitive dashboard.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import os
import sys

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from modules.cognitive.strategy_engine import Strategy, StrategyEngine
from modules.cognitive.planner_agent import PlannerAgent

router = APIRouter()


STRATEGY_UI_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "strategy_a": {
        "title": "Đệm tồn kho mùa mưa",
        "tag": "Service",
        "tag_color": "bg-purple-50 text-purple-700",
        "description": "Tăng tồn kho 30% tại các kho rủi ro để giảm trễ giao hàng trong mùa mưa.",
        "risks": [
            "Nguy cơ dư thừa nếu nhu cầu giảm",
            "Chi phí lưu kho tăng"
        ],
        "lead_time": "+0.5 ngày buffer",
        "service_level": "97%"
    },
    "strategy_b": {
        "title": "Cân bằng tồn kho & buffer",
        "tag": "Lead Time",
        "tag_color": "bg-sky-50 text-sky-700",
        "description": "Phân bổ lại tồn kho giữa các kho và tăng buffer lead time để bảo vệ SLA.",
        "risks": [
            "Chi phí vận chuyển nội bộ tăng",
            "Chậm trễ nếu kho không đủ công suất"
        ],
        "lead_time": "+0.7 ngày buffer",
        "service_level": "95%"
    },
    "strategy_c": {
        "title": "Ưu tiên khách VIP",
        "tag": "Customer",
        "tag_color": "bg-emerald-50 text-emerald-700",
        "description": "Ưu tiên đơn hàng VIP và phân bổ tồn kho riêng để giữ doanh thu cao.",
        "risks": [
            "Khách phổ thông có thể bị chậm đơn",
            "Cần KPI giám sát phân bổ VIP"
        ],
        "lead_time": "Ưu tiên xử lý tức thì",
        "service_level": "98% VIP"
    },
    "strategy_d": {
        "title": "Tối ưu chi phí vận hành",
        "tag": "Cost",
        "tag_color": "bg-amber-50 text-amber-700",
        "description": "Giảm tồn kho 15% ở kho dư thừa và thương lượng lại chi phí logistics.",
        "risks": ["Tăng rủi ro thiếu hàng nếu nhu cầu tăng đột ngột"],
        "lead_time": "Giảm 0.2 ngày xử lý",
        "service_level": "92%"
    },
    "strategy_e": {
        "title": "Tối đa hóa Service Level",
        "tag": "Service",
        "tag_color": "bg-rose-50 text-rose-700",
        "description": "Tăng tồn kho chiến lược và bổ sung ca vận hành để đạt SLA 98%.",
        "risks": [
            "Nhu cầu hụt gây dư kho",
            "Cần giám sát ngân sách sát sao"
        ],
        "lead_time": "+0.3 ngày buffer",
        "service_level": "98%"
    }
}


class StrategyRequest(BaseModel):
    model_results: Dict[str, Any] = Field(default_factory=dict)
    business_context: Dict[str, Any] = Field(default_factory=dict)
    objectives: List[str] = Field(default_factory=lambda: ["balance"])


class ActionTriggerRequest(BaseModel):
    action_id: str
    label: Optional[str] = None


ACTION_EFFECTS: Dict[str, Dict[str, Any]] = {
    "deploy-model": {
        "title": "Triển khai mô hình mới",
        "summary": "Mô hình sản xuất mới đã được đẩy lên cụm inference và bắt đầu nhận lưu lượng.",
        "definition": "Triển khai = chuyển weights + cấu hình inference mới vào cụm serving, chuyển 100% traffic sau 5 phút warmup.",
        "impacts": [
            "Giảm tỉ lệ dự báo trễ thêm 3.1 điểm phần trăm",
            "Service level dự kiến tăng từ 94% → 96.5% trong 24h"
        ],
        "risks": [
            "Theo dõi drift trong 48h đầu để tránh sai lệch theo mùa"
        ],
        "next_steps": [
            "Kiểm tra dashboard drift_detection trong 2 giờ nữa"
        ]
    },
    "weather-simulation": {
        "title": "Stress test thời tiết cực đoan",
        "summary": "Đã mô phỏng kịch bản mưa 120mm trong 24h tại HCM & Hải Phòng.",
        "definition": "Thời tiết cực đoan = lượng mưa >100mm + gió > 60km/h trong cùng ngày → ảnh hưởng giao thông đường bộ & cảng.",
        "impacts": [
            "Rủi ro giao trễ tăng 14% nếu không tăng buffer",
            "Kho VN-WH02 cần nâng tồn kho an toàn thêm 18%"
        ],
        "risks": [
            "Chuỗi lạnh tại khu vực HN có thể bị gián đoạn do ngập cục bộ"
        ],
        "next_steps": [
            "Gửi cảnh báo tới đội vận tải và kích hoạt kế hoạch chuyển hướng qua TH-WH01"
        ]
    },
    "warehouse-restart": {
        "title": "Khởi động lại Warehouse AI",
        "summary": "Đã khởi động lại bộ tối ưu tồn kho và tái đồng bộ tồn kho thực tế.",
        "definition": "Warehouse AI restart = làm mới bộ giải tối ưu + đồng bộ dữ liệu tồn kho trong 30 phút gần nhất.",
        "impacts": [
            "Các kế hoạch chuyển kho sẽ được tính lại với dữ liệu mới nhất",
            "Giảm độ lệch tồn kho giữa thực tế và hệ thống xuống <2%"
        ],
        "risks": [
            "Trong 5 phút đầu nên hạn chế tạo lệnh mới để tránh ghi đè dữ liệu"
        ],
        "next_steps": [
            "Xác nhận đồng bộ hoàn tất trước khi tạo thêm chiến lược phân bổ"
        ]
    }
}


def _default_model_results() -> Dict[str, Any]:
    return {
        "forecast": {
            "expected_revenue": 215000,
            "demand_volatility": 0.18,
            "regions": {"HCM": 0.35, "HN": 0.3, "SEA": 0.2, "Others": 0.15}
        },
        "delay_risk": {
            "risk_score": 0.27,
            "hotspots": ["HCM Port", "Hai Phong"]
        },
        "churn": {
            "high_value_customers": [
                {"segment": "VIP", "revenue_share": 0.38},
                {"segment": "Enterprise", "revenue_share": 0.27}
            ],
            "churn_rate": 0.13
        },
        "rl_policy": {"buffer_days": 3}
    }


def _default_business_context() -> Dict[str, Any]:
    return {
        "current_inventory": {
            "VN-WH01": 12000,
            "VN-WH02": 7000,
            "TH-WH01": 5200
        },
        "warehouses": [
            {"code": "VN-WH01", "capacity": 15000, "region": "HCM"},
            {"code": "VN-WH02", "capacity": 12000, "region": "HN"},
            {"code": "TH-WH01", "capacity": 10000, "region": "Bangkok"}
        ],
        "avg_lead_time": 3.5,
        "region": "Vietnam",
        "season": "rainy",
        "weather_forecast": {"precipitation_forecast": 42}
    }


def _format_currency(amount: float) -> str:
    return f"{amount:,.0f} USD"


def _describe_action(action: Dict[str, Any]) -> str:
    action_type = action.get("type", "")
    if action_type == "increase_inventory":
        qty = action.get("quantity") or action.get("target_increase")
        warehouse = action.get("warehouse", action.get("location", "kho trọng điểm"))
        return f"Tăng thêm {qty} đơn vị tại {warehouse} ({action.get('timeline', '2 tuần')})."
    if action_type == "monitor_weather":
        threshold = action.get("alert_threshold", 20)
        return f"Thiết lập cảnh báo thời tiết khi mưa > {threshold}mm."
    if action_type == "redistribute_inventory":
        return "Phân bổ lại tồn kho giữa các kho để đạt cân bằng 90%."
    if action_type == "increase_lead_time_buffer":
        new_buffer = action.get("new_lead_time")
        return f"Tăng buffer lead time lên {new_buffer} ngày để hấp thụ biến động."
    if action_type == "prioritize_vip_orders":
        return "Ưu tiên xử lý đơn hàng VIP và nâng SLA thêm 3 điểm."
    if action_type == "allocate_vip_inventory":
        qty = action.get("quantity_per_vip", 10)
        return f"Dành riêng {qty} đơn vị cho mỗi khách VIP trọng yếu."
    if action_type == "reduce_inventory":
        return f"Cắt giảm tồn kho {action.get('target_reduction', 10)}% tại kho dư thừa."
    return "Thực hiện tác vụ tối ưu vận hành theo khuyến nghị AI."


def _format_kpis_for_ui(kpis: Dict[str, float]) -> List[Dict[str, str]]:
    label_map = {
        "inventory_level": "Tồn kho mục tiêu",
        "inventory_increase_pct": "Tăng tồn kho",
        "stockout_risk_reduction": "Giảm rủi ro thiếu hàng",
        "delay_risk_reduction": "Giảm rủi ro trễ",
        "service_level_improvement": "Điểm SLA cải thiện",
        "lead_time_buffer_increase": "Buffer lead time",
        "vip_service_level": "SLA khách VIP",
        "vip_revenue_boost": "Doanh thu VIP tăng",
        "cost_savings": "Tiết kiệm chi phí"
    }
    formatted: List[Dict[str, str]] = []
    for key, value in kpis.items():
        label = label_map.get(key, key.replace("_", " ").title())
        unit = "%"
        if "inventory" in key and "pct" not in key:
            unit = "u"
        if "cost" in key or "revenue" in key:
            unit = " USD"

        display_value: str
        if isinstance(value, (int, float)):
            if abs(value) >= 1000 and unit == " USD":
                display_value = f"{value:,.0f}{unit}"
            elif unit == "%":
                display_value = f"{value:.1f}{unit}"
            elif unit == "u":
                display_value = f"{value:.1f}{unit}"
            else:
                display_value = f"{value:.1f}{unit}"
        else:
            display_value = str(value)

        formatted.append({"label": label, "value": display_value})
    return formatted[:4]


def _format_strategy_for_ui(strategy: Strategy) -> Dict[str, Any]:
    override = STRATEGY_UI_OVERRIDES.get(strategy.id, {})
    service_level_gain = strategy.kpis.get("service_level_improvement", 0.0)
    lead_time_buffer = strategy.kpis.get("lead_time_buffer_increase")
    metrics = [
        {"label": "Chi phí ước tính", "value": _format_currency(strategy.estimated_cost)},
        {
            "label": "Lead time kỳ vọng",
            "value": override.get("lead_time") or (f"+{lead_time_buffer:.0f}% buffer" if lead_time_buffer else "Ổn định")
        },
        {
            "label": "Service level dự đoán",
            "value": override.get("service_level") or f"+{service_level_gain:.1f} điểm"
        }
    ]
    return {
        "id": strategy.id,
        "title": override.get("title", strategy.name),
        "tag": override.get("tag", "AI"),
        "tag_color": override.get("tag_color", "bg-slate-100 text-slate-600"),
        "description": override.get("description", strategy.description),
        "confidence": round(strategy.confidence * 100, 1),
        "metrics": metrics,
        "actions": [_describe_action(action) for action in strategy.actions],
        "risks": override.get("risks", strategy.risks),
        "kpis": _format_kpis_for_ui(strategy.kpis),
        "time_horizon": override.get("time_horizon", strategy.time_horizon),
        "estimated_profit": _format_currency(strategy.estimated_profit)
    }


def _build_chart_payload() -> Dict[str, Any]:
    today = datetime.utcnow()
    labels = [(today - timedelta(days=(6 - idx))).strftime("%d/%m") for idx in range(7)]
    return {
        "accuracy": {
            "labels": labels,
            "values": [0.934, 0.928, 0.932, 0.938, 0.941, 0.939, 0.944],
            "threshold": 0.92
        },
        "system_load": {
            "labels": ["Inference", "Huấn luyện", "Mô phỏng"],
            "values": [32, 14, 8]
        }
    }


def _build_model_cards() -> List[Dict[str, Any]]:
    return [
        {"name": "Late Delivery Classifier", "version": "v9.1", "owner": "Ops Team", "status": "success", "accuracy": "92%", "updated_at": "15/11 08:05"},
        {"name": "Demand Forecast Ensemble", "version": "v7.4", "owner": "Forecast Squad", "status": "warn", "accuracy": "88%", "updated_at": "15/11 07:30"},
        {"name": "Inventory Optimizer RL", "version": "v5.2", "owner": "Warehouse AI", "status": "error", "accuracy": "85%", "updated_at": "14/11 23:10"},
        {"name": "Pricing Elasticity", "version": "v4.3", "owner": "Revenue Lab", "status": "success", "accuracy": "90%", "updated_at": "14/11 21:45"}
    ]


def _build_log_items() -> List[Dict[str, str]]:
    return [
        {"time": "08:31", "level": "Cảnh báo", "message": "Tồn kho kho HCM giảm 18%, đề nghị kiểm tra dự báo."},
        {"time": "07:48", "level": "Thông tin", "message": "Model giao trễ v9.1 tái huấn luyện thành công (F1=0.92)."},
        {"time": "07:05", "level": "Lỗi", "message": "Warehouse AI không đồng bộ được dữ liệu thời tiết EU (timeout)."},
        {"time": "06:40", "level": "Thông tin", "message": "Planner AI đã gửi 3 chiến lược mới tới Control Center."}
    ]


def _build_dashboard_snapshot() -> Dict[str, Any]:
    model_results = _default_model_results()
    business_context = _default_business_context()
    objectives = ["balance", "min_cost", "max_service"]
    strategy_engine = StrategyEngine()
    strategies = strategy_engine.generate_strategies(model_results, business_context, objectives)
    strategy_cards = [_format_strategy_for_ui(strategy) for strategy in strategies]
    return {
        "summary": {
            "active_models": 12,
            "avg_accuracy": "93%",
            "daily_runs": 48,
            "pending_actions": 5
        },
        "models": _build_model_cards(),
        "logs": _build_log_items(),
        "strategies": strategy_cards,
        "charts": _build_chart_payload(),
        "updated_at": datetime.utcnow().isoformat()
    }


def _resolve_strategy_inputs(request: StrategyRequest) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
    model_results = request.model_results or _default_model_results()
    business_context = request.business_context or _default_business_context()
    objectives = request.objectives or ["balance"]
    return model_results, business_context, objectives


def _build_action_detail(action_id: str, label: str) -> Dict[str, Any]:
    effect = ACTION_EFFECTS.get(action_id, {})
    return {
        "title": effect.get("title", label),
        "summary": effect.get("summary", "Hệ thống đã xử lý yêu cầu và cập nhật trạng thái tác vụ."),
        "definition": effect.get("definition", "Không có định nghĩa bổ sung."),
        "impacts": effect.get("impacts", []),
        "risks": effect.get("risks", []),
        "next_steps": effect.get("next_steps", [])
    }


@router.post("/strategies/generate")
async def generate_strategies(request: StrategyRequest):
    try:
        model_results, business_context, objectives = _resolve_strategy_inputs(request)
        strategy_engine = StrategyEngine()
        strategies = strategy_engine.generate_strategies(
            model_results=model_results,
            business_context=business_context,
            objectives=objectives
        )
        comparison = strategy_engine.compare_strategies(strategies)

        planner = PlannerAgent()
        recommendations = planner.generate_recommendations(
            strategies=strategies,
            comparison=comparison,
            context=business_context
        )

        return {
            "status": "success",
            "strategies": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "kpis": s.kpis,
                    "risks": s.risks,
                    "confidence": s.confidence,
                    "estimated_profit": s.estimated_profit,
                    "estimated_cost": s.estimated_cost,
                    "estimated_revenue": s.estimated_revenue,
                    "time_horizon": s.time_horizon
                }
                for s in strategies
            ],
            "comparison": comparison,
            "recommendations": recommendations,
            "ui_cards": [_format_strategy_for_ui(s) for s in strategies],
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Strategy generation error: {exc}") from exc


@router.get("/strategies/{strategy_id}")
async def get_strategy_details(strategy_id: str):
    try:
        strategy_engine = StrategyEngine()
        strategy = strategy_engine.get_strategy_details(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
        return {
            "status": "success",
            "strategy": {
                "id": strategy.id,
                "name": strategy.name,
                "description": strategy.description,
                "kpis": strategy.kpis,
                "risks": strategy.risks,
                "confidence": strategy.confidence,
                "actions": strategy.actions,
                "estimated_profit": strategy.estimated_profit,
                "estimated_cost": strategy.estimated_cost,
                "estimated_revenue": strategy.estimated_revenue
            }
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error: {exc}") from exc


@router.get("/dashboard", response_class=HTMLResponse)
async def cognitive_dashboard_page(request: Request):
    from starlette.templating import Jinja2Templates

    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    templates = Jinja2Templates(directory=templates_dir)
    snapshot = _build_dashboard_snapshot()
    return templates.TemplateResponse(
        "cognitive_dashboard.html",
        {"request": request, "dashboard_snapshot": snapshot}
    )


@router.get("/dashboard/data")
async def cognitive_dashboard_data():
    return _build_dashboard_snapshot()


@router.post("/actions/trigger")
async def trigger_quick_action(request: ActionTriggerRequest):
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    label = request.label or request.action_id.replace("_", " ").title()
    detail = _build_action_detail(request.action_id, label)
    return {
        "status": "accepted",
        "message": f"Hệ thống đã kích hoạt '{label}'.",
        "log_entry": {
            "time": timestamp,
            "level": "Thông tin",
            "message": f"AI vừa gửi yêu cầu '{label}' tới Control Center."
        },
        "detail": detail
    }
