"""
FastAPI application chính.
Khởi tạo app và cấu hình routing, templates, static files.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

from app.routers import (
    dashboard,
    ml_api,
    digital_twin_api,
    what_if_api,
    self_learning_api,
    os_api,
    cognitive_api,
    ai_dashboard,
    models_registry,
    models_metrics,
    ai_models_api,
    ai_strategy_api,
)

# Khởi tạo FastAPI app
app = FastAPI(
    title="Supply Chain Analytics Dashboard",
    description="Dashboard phân tích chuỗi cung ứng và thời tiết với ML predictions (V6 + V7 + V8 + V9)",
    version="9.0.0"
)

# Cấu hình templates
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
templates = Jinja2Templates(directory=templates_dir)

# Cấu hình static files
static_dir = os.path.join(os.path.dirname(__file__), 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Đăng ký routers
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(ai_dashboard.router, prefix="/dashboard", tags=["ai-dashboard"])
app.include_router(models_registry.router, tags=["model-registry"])
app.include_router(models_metrics.router, tags=["model-metrics"])
app.include_router(ml_api.router, prefix="/ml", tags=["ml"])
app.include_router(ai_models_api.router, tags=["ai-models"])
app.include_router(ai_strategy_api.router, prefix="/ai/strategy", tags=["strategy"])

# V6 + V7 routers
app.include_router(self_learning_api.router, prefix="/v6", tags=["v6-self-learning"])
app.include_router(digital_twin_api.router, prefix="/v7/digital-twin", tags=["v7-digital-twin"])
app.include_router(what_if_api.router, prefix="/v7/what-if", tags=["v7-what-if"])

# V8 + V9 routers
app.include_router(cognitive_api.router, prefix="/v8", tags=["v8-cognitive"])
app.include_router(os_api.router, prefix="/os", tags=["v9-os"])


@app.get("/", response_class=HTMLResponse)
async def root():
    """Trang chủ, redirect đến dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Supply Chain Analytics API is running"}
