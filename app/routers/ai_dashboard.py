"""
AI Dashboard Router: Hiển thị overview và chi tiết của tất cả AI models.

Endpoints:
- GET /dashboard/ai - Overview tất cả models
- GET /dashboard/ai/{model_id} - Chi tiết từng model
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Thêm thư mục app vào path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.services.model_registry import (
    get_all_models, get_model, get_models_by_type, 
    get_models_by_status, check_model_exists, 
    get_model_metrics_summary, check_model_files,
    ModelType, ModelStatus
)

router = APIRouter()

# Cấu hình templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
templates = Jinja2Templates(directory=templates_dir)

BASE_DIR = Path(__file__).parent.parent.parent


@router.get("/ai", response_class=HTMLResponse)
async def ai_dashboard_overview(request: Request):
    """
    Trang tổng quan tất cả AI models.
    """
    try:
        # Lấy tất cả models
        all_models = get_all_models()
        
        # Check model files
        model_files_status = check_model_files()
        
        # Group models by type
        models_by_type = {
            "classification": get_models_by_type(ModelType.CLASSIFICATION),
            "regression": get_models_by_type(ModelType.REGRESSION),
            "reinforcement_learning": get_models_by_type(ModelType.RL),
            "simulation": get_models_by_type(ModelType.SIMULATION),
            "cognitive": get_models_by_type(ModelType.COGNITIVE),
            "online_learning": get_models_by_type(ModelType.ONLINE_LEARNING),
        }
        
        # Group models by status
        models_by_status = {
            "deployed": get_models_by_status(ModelStatus.DEPLOYED),
            "analytics": get_models_by_status(ModelStatus.ANALYTICS),
            "development": get_models_by_status(ModelStatus.DEVELOPMENT),
            "not_trained": get_models_by_status(ModelStatus.NOT_TRAINED),
        }
        
        # Prepare context
        context = {
            "request": request,
            "all_models": all_models,
            "models_by_type": models_by_type,
            "models_by_status": models_by_status,
            "model_files_status": model_files_status,
            "total_models": len(all_models),
            "deployed_count": len(models_by_status["deployed"]),
            "analytics_count": len(models_by_status["analytics"]),
        }
        
        return templates.TemplateResponse("ai_dashboard.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading AI dashboard: {str(e)}")


@router.get("/ai/{model_id}", response_class=HTMLResponse)
async def ai_model_detail(request: Request, model_id: str):
    """
    Trang chi tiết của một AI model.
    """
    try:
        # Kiểm tra model có tồn tại không
        if not check_model_exists(model_id):
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        
        # Lấy model metadata
        model = get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        
        # Lấy metrics summary
        metrics_summary = get_model_metrics_summary(model_id)
        
        # Check model file exists
        model_file_exists = False
        if model.model_path:
            model_file = BASE_DIR / model.model_path
            model_file_exists = model_file.exists()
        
        # Try to load actual metrics from results directory (if available)
        results_dir = BASE_DIR / "results"
        actual_metrics = None
        if results_dir.exists():
            # Look for latest run
            run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("run_")], reverse=True)
            if run_dirs:
                latest_run = run_dirs[0]
                metrics_file = latest_run / "metrics" / f"{model_id}_metrics.json"
                if metrics_file.exists():
                    import json
                    try:
                        with open(metrics_file, 'r', encoding='utf-8') as f:
                            actual_metrics = json.load(f)
                    except:
                        pass
        
        # Prepare context
        context = {
            "request": request,
            "model": model,
            "metrics_summary": metrics_summary,
            "actual_metrics": actual_metrics,
            "model_file_exists": model_file_exists,
            "model_file_path": model.model_path,
            "form_fields": model.form_fields,
            "chart_types": model.chart_types,
        }
        
        # Use a generic template or model-specific template
        template_name = f"ai/model_{model_id}.html"
        template_path = Path(templates_dir) / template_name
        
        # If model-specific template doesn't exist, use generic template
        if not template_path.exists():
            template_name = "ai/model_detail.html"
        
        return templates.TemplateResponse(template_name, context)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model detail: {str(e)}")


@router.get("/ai/api/models", response_class=HTMLResponse)
async def ai_models_api(request: Request):
    """
    API endpoint để lấy danh sách models (JSON).
    """
    from fastapi.responses import JSONResponse
    
    try:
        all_models = get_all_models()
        model_files_status = check_model_files()
        
        models_data = []
        for model in all_models:
            model_data = {
                "id": model.id,
                "name": model.name,
                "display_name": model.display_name,
                "type": model.type.value,
                "description": model.description,
                "status": model.status.value,
                "version": model.version,
                "api_endpoint": model.api_endpoint,
                "docs_path": model.docs_path,
                "model_file_exists": model_files_status.get(model.id, False),
                "metrics": [
                    {
                        "name": metric.name,
                        "value": metric.value,
                        "target": metric.target,
                        "unit": metric.unit,
                        "description": metric.description
                    }
                    for metric in model.metrics
                ]
            }
            models_data.append(model_data)
        
        return JSONResponse(content={
            "status": "success",
            "total_models": len(models_data),
            "models": models_data
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.get("/ai/api/model/{model_id}/metrics", response_class=HTMLResponse)
async def ai_model_metrics_api(request: Request, model_id: str):
    """
    API endpoint để lấy metrics của một model (JSON).
    """
    from fastapi.responses import JSONResponse
    
    try:
        if not check_model_exists(model_id):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Model '{model_id}' not found"}
            )
        
        metrics_summary = get_model_metrics_summary(model_id)
        
        return JSONResponse(content={
            "status": "success",
            "model_id": model_id,
            "metrics": metrics_summary
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

