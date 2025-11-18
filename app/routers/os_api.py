"""
OS API: Endpoints cho Operating System control center.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from core.os_orchestrator import OSOrchestrator
from core.governance.policy_engine import PolicyEngine
from core.safety.safety_checks import SafetyChecker

router = APIRouter()

_orchestrator: Optional[OSOrchestrator] = None
_policy_engine: Optional[PolicyEngine] = None
_safety_checker: Optional[SafetyChecker] = None


def get_orchestrator() -> OSOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OSOrchestrator()
    return _orchestrator


def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine


def get_safety_checker() -> SafetyChecker:
    global _safety_checker
    if _safety_checker is None:
        _safety_checker = SafetyChecker()
    return _safety_checker


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_pending_actions() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "ACT-2025-001",
            "type": "increase_inventory",
            "title": "Bổ sung tồn kho vùng HCM",
            "description": "Tăng thêm 1.800 pallet tại VN-WH01 do thời tiết ảnh hưởng tuyến HCM.",
            "priority": "high",
            "estimated_cost": 28000,
            "confidence": 0.82,
            "status": "pending",
            "created_at": (now - timedelta(minutes=18)).isoformat(),
            "source_strategy": "strategy_a",
            "policy_check": {
                "compliant": False,
                "requires_approval": True,
                "violations": [
                    {"code": "BUDGET_THRESHOLD", "message": "Chi phí vượt ngưỡng $25k"},
                    {"code": "BUFFER_LEADTIME", "message": "Cần xác nhận buffer tuyến HCM"}
                ]
            },
            "safety_check": {
                "safe": True,
                "requires_review": False,
                "notes": "Không có cảnh báo safety"
            },
            "reasoning": "Weather risk score 0.72 → đề xuất tăng tồn kho để giữ SLA.",
            "payload": {
                "warehouse": "VN-WH01",
                "products": ["SKU-ICE-42", "SKU-COOL-18"],
                "target_increase_pct": 0.25,
                "duration_days": 7
            }
        },
        {
            "id": "ACT-2025-002",
            "type": "redistribute_inventory",
            "title": "Phân bổ hàng sang TH-WH01",
            "description": "Chuyển 12% hàng từ VN-WH02 sang TH-WH01 để giảm áp lực kho miền Bắc.",
            "priority": "medium",
            "estimated_cost": 12000,
            "confidence": 0.74,
            "status": "pending",
            "created_at": (now - timedelta(minutes=42)).isoformat(),
            "source_strategy": "strategy_b",
            "policy_check": {
                "compliant": True,
                "requires_approval": False,
                "violations": []
            },
            "safety_check": {
                "safe": True,
                "requires_review": False,
                "notes": ""
            },
            "reasoning": "Cầu khu vực Bangkok tăng 14%, kho TH-WH01 còn 30% sức chứa.",
            "payload": {
                "origin": "VN-WH02",
                "destination": "TH-WH01",
                "volume": 920,
                "transport_mode": "road"
            }
        }
    ]


def _seed_history() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "HIST-991",
            "timestamp": (now - timedelta(hours=1, minutes=10)).isoformat(),
            "status": "auto-applied",
            "actor": "AI Orchestrator",
            "summary": "Tăng buffer lead time tuyến HN → HCM thêm 0.5 ngày.",
            "result": "Giảm dự báo trễ xuống 9.4%, SLA duy trì 95%.",
            "confidence": 0.88,
            "category": "lead_time"
        },
        {
            "id": "HIST-990",
            "timestamp": (now - timedelta(hours=2, minutes=5)).isoformat(),
            "status": "approved",
            "actor": "ops.linh",
            "summary": "Chuyển 600 pallet dược phẩm sang kho lạnh HN-WH03.",
            "result": "Hoàn tất sau 45 phút, giảm tải kho HCM 7%.",
            "confidence": 0.79,
            "category": "redistribution"
        },
        {
            "id": "HIST-986",
            "timestamp": (now - timedelta(hours=4)).isoformat(),
            "status": "rejected",
            "actor": "ops.long",
            "summary": "Yêu cầu giảm tồn kho VN-WH02 20%.",
            "result": "Từ chối do nhu cầu khu vực miền Bắc đang tăng.",
            "confidence": 0.55,
            "category": "cost"
        }
    ]


_pending_actions_store: List[Dict[str, Any]] = _seed_pending_actions()
_history_store: List[Dict[str, Any]] = _seed_history()


def _filter_pending(actions: List[Dict[str, Any]], params: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    filtered = actions
    if params.get("model_id"):
        filtered = [a for a in filtered if a.get("source_strategy") == params["model_id"]]
    if params.get("action_type"):
        filtered = [a for a in filtered if a.get("type") == params["action_type"]]
    if params.get("priority"):
        filtered = [a for a in filtered if a.get("priority") == params["priority"]]
    if params.get("status"):
        filtered = [a for a in filtered if a.get("status") == params["status"]]
    return filtered


def _filter_history(records: List[Dict[str, Any]], params: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    filtered = records
    if params.get("status"):
        filtered = [r for r in filtered if r.get("status") == params["status"]]
    if params.get("type"):
        filtered = [r for r in filtered if r.get("category") == params["type"]]
    if params.get("model_id"):
        filtered = [r for r in filtered if r.get("source_strategy") == params["model_id"]]
    if params.get("category"):
        filtered = [r for r in filtered if r.get("category") == params["category"]]

    from_ts = params.get("from")
    to_ts = params.get("to")
    if from_ts:
        from_dt = datetime.fromisoformat(from_ts)
        filtered = [r for r in filtered if datetime.fromisoformat(r["timestamp"]) >= from_dt]
    if to_ts:
        to_dt = datetime.fromisoformat(to_ts)
        filtered = [r for r in filtered if datetime.fromisoformat(r["timestamp"]) <= to_dt]
    return filtered


def _compute_aggregations(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_hour: Dict[str, Dict[str, int]] = {}
    by_type: Dict[str, int] = {}
    for rec in records:
        ts = datetime.fromisoformat(rec["timestamp"])
        bucket = ts.replace(minute=0, second=0, microsecond=0).isoformat()
        if bucket not in by_hour:
            by_hour[bucket] = {"approved": 0, "rejected": 0, "auto": 0}
        status = rec.get("status")
        if status == "approved":
            by_hour[bucket]["approved"] += 1
        elif status == "rejected":
            by_hour[bucket]["rejected"] += 1
        else:
            by_hour[bucket]["auto"] += 1

        category = rec.get("category") or "other"
        by_type[category] = by_type.get(category, 0) + 1

    agg_hour = [
        {"bucket": bucket, "approved": counts["approved"], "rejected": counts["rejected"], "auto": counts["auto"]}
        for bucket, counts in sorted(by_hour.items())
    ]
    agg_type = [{"type": k, "count": v} for k, v in by_type.items()]
    return {"by_hour": agg_hour, "by_type": agg_type}


class ActionRequest(BaseModel):
    action: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    mode: str = "advisory"


class ApproveActionRequest(BaseModel):
    action_id: str
    approved_by: str
    notes: Optional[str] = None


class RejectActionRequest(BaseModel):
    action_id: str
    rejected_by: str
    reason: str


@router.get("/status")
async def get_os_status():
    orchestrator = get_orchestrator()
    return orchestrator.get_status()


@router.post("/actions/check")
async def check_action(request: ActionRequest):
    policy_engine = get_policy_engine()
    safety_checker = get_safety_checker()

    policy_result = policy_engine.check_action(
        request.action,
        request.context,
        request.mode
    )

    safety_result = safety_checker.check_action_safety(
        request.action,
        request.context
    )

    return {
        "status": "success",
        "policy_check": policy_result,
        "safety_check": safety_result,
        "overall_safe": policy_result["compliant"] and safety_result["safe"],
        "requires_approval": policy_result["requires_approval"] or safety_result["requires_review"]
    }


@router.get("/actions/pending")
async def get_pending_actions(
    model_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None)
):
    params = {
        "model_id": model_id,
        "action_type": action_type,
        "priority": priority,
        "status": status
    }
    filtered = _filter_pending(_pending_actions_store, params)
    if offset:
        filtered = filtered[offset:]
    if limit:
        filtered = filtered[:limit]
    return {"status": "success", "pending_actions": filtered}


def _handle_action_decision(action_id: str, decision: str, actor: str, notes: Optional[str] = None) -> Dict[str, Any]:
    action = next((a for a in _pending_actions_store if a["id"] == action_id), None)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action not found: {action_id}")
    _pending_actions_store.remove(action)
    history_record = {
        "id": f"HIST-{action_id}",
        "timestamp": _now_ts(),
        "status": decision,
        "actor": actor,
        "summary": action.get("title") or action.get("description"),
        "result": notes or "",
        "confidence": action.get("confidence"),
        "category": action.get("type")
    }
    _history_store.insert(0, history_record)
    return history_record


@router.post("/actions/approve")
async def approve_action(request: ApproveActionRequest):
    record = _handle_action_decision(request.action_id, "approved", request.approved_by, request.notes)
    return {
        "status": "success",
        "action_id": request.action_id,
        "decision": "approved",
        "message": "Action approved",
        "processed_at": record["timestamp"]
    }


@router.post("/actions/reject")
async def reject_action(request: RejectActionRequest):
    record = _handle_action_decision(request.action_id, "rejected", request.rejected_by, request.reason or request.notes)
    return {
        "status": "success",
        "action_id": request.action_id,
        "decision": "rejected",
        "message": "Action rejected",
        "processed_at": record["timestamp"]
    }


@router.get("/action/history")
async def get_action_history(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None)
):
    params = {
        "from": from_date,
        "to": to_date,
        "status": status,
        "type": type,
        "model_id": model_id,
        "category": category
    }
    filtered = _filter_history(_history_store, params)
    if offset:
        filtered = filtered[offset:]
    if limit:
        filtered = filtered[:limit]
    aggregations = _compute_aggregations(_history_store)
    return {"status": "success", "history": filtered, "aggregations": aggregations}


@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str, force: bool = False):
    orchestrator = get_orchestrator()
    return orchestrator.run_task(task_id, force=force)


@router.get("/tasks")
async def get_tasks():
    orchestrator = get_orchestrator()
    return {
        "status": "success",
        "tasks": {
            task_id: {
                "name": task.name,
                "status": task.status,
                "enabled": task.enabled,
                "dependencies": task.dependencies
            }
            for task_id, task in orchestrator.tasks.items()
        }
    }


@router.get("/control-center", response_class=HTMLResponse)
async def control_center_page(request: Request):
    from starlette.templating import Jinja2Templates

    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    templates = Jinja2Templates(directory=templates_dir)
    return templates.TemplateResponse("control_center.html", {"request": request})
