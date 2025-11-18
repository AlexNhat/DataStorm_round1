"""
Models registry endpoints for dashboard and API.
"""

from pathlib import Path
from typing import List, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.templating import Jinja2Templates
import json

BASE_DIR = Path(__file__).parent.parent.parent
REGISTRY_PATH = BASE_DIR / "data" / "model_registry.json"
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

router = APIRouter()


def load_registry() -> List[Dict]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry file not found at {REGISTRY_PATH}")
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid registry JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("Registry file must contain list of models.")
    return data


@router.get("/api/models")
async def api_models():
    try:
        return {"status": "success", "models": load_registry()}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@router.get("/dashboard/models")
async def dashboard_models(request: Request):
    try:
        models = load_registry()
        return templates.TemplateResponse(
            "dashboard/models_list.html",
            {"request": request, "models": models, "total": len(models)},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/models/{model_name}")
async def dashboard_model_detail(request: Request, model_name: str):
    try:
        models = load_registry()
        model = next((m for m in models if m["name"].lower().replace(" ", "-") == model_name.lower().replace(" ", "-")), None)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        return templates.TemplateResponse(
            "dashboard/model_detail.html",
            {"request": request, "model": model},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
