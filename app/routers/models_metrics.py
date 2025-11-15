import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.templating import Jinja2Templates

BASE_DIR = Path(__file__).parent.parent.parent
SUMMARY_PATH = BASE_DIR / "results" / "metrics" / "global_dashboard_metrics.json"

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
router = APIRouter()


def load_summary() -> dict:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError("Metrics summary not found. Run scripts/generate_dashboard_metrics.py first.")
    return json.loads(SUMMARY_PATH.read_text())


@router.get("/api/models/metrics/global")
async def api_global_metrics():
    try:
        return {"status": "success", "summary": load_summary()}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@router.get("/dashboard/metrics")
async def dashboard_metrics_overview(request: Request):
    try:
        summary = load_summary()
        return templates.TemplateResponse(
            "dashboard/metrics/metrics_overview.html",
            {"request": request, "summary": summary},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/metrics/{model_slug}")
async def dashboard_metrics_model(request: Request, model_slug: str):
    template_map = {
        "inventory-rl": "dashboard/metrics/metrics_inventory_rl.html",
        "forecast": "dashboard/metrics/metrics_forecast.html",
        "delivery": "dashboard/metrics/metrics_delivery.html",
        "pricing": "dashboard/metrics/metrics_pricing.html",
    }
    template = template_map.get(model_slug)
    if not template:
        raise HTTPException(status_code=404, detail="Metrics view not found")
    try:
        summary = load_summary()
        return templates.TemplateResponse(
            template,
            {"request": request, "summary": summary},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
