"""
ML API Router: REST endpoints cho ML predictions.

Endpoints:
- POST /ml/logistics/delay
- POST /ml/revenue/forecast
- POST /ml/customer/churn
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import sys
import os

# Thêm thư mục app vào path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.services.ml_service import (
    get_logistics_service, predict_logistics_delay,
    get_revenue_service, predict_revenue,
    get_churn_service, predict_churn
)

router = APIRouter()

# Cấu hình templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
templates = Jinja2Templates(directory=templates_dir)


# Pydantic models cho request validation

class LogisticsDelayRequest(BaseModel):
    """Request model cho logistics delay prediction."""
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    order_date: Optional[str] = None
    shipping_duration_scheduled: Optional[float] = None
    shipping_duration_real: Optional[float] = None
    temperature: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    weather_risk_level: Optional[int] = None
    is_weekend: Optional[int] = None
    month: Optional[int] = None
    category_name: Optional[str] = None
    sales: Optional[float] = None
    # Có thể thêm các features khác


class RevenueForecastRequest(BaseModel):
    """Request model cho revenue forecast."""
    region: Optional[str] = None
    category: Optional[str] = None
    forecast_date: Optional[str] = None
    revenue_lag_7d: Optional[float] = None
    revenue_lag_30d: Optional[float] = None
    revenue_7d_avg: Optional[float] = None
    revenue_30d_avg: Optional[float] = None
    month: Optional[int] = None
    day_of_week: Optional[int] = None
    temperature: Optional[float] = None
    # Có thể thêm các features khác


class ChurnRequest(BaseModel):
    """Request model cho customer churn prediction."""
    customer_id: str = Field(..., description="Customer ID")
    rfm_recency: Optional[float] = None
    rfm_frequency: Optional[float] = None
    rfm_monetary: Optional[float] = None
    total_orders: Optional[int] = None
    total_sales: Optional[float] = None
    avg_order_value: Optional[float] = None
    days_since_first_order: Optional[int] = None
    # Có thể thêm các features khác


@router.post("/logistics/delay")
async def predict_logistics_delay_endpoint(request: LogisticsDelayRequest):
    """
    Predict logistics delay risk.
    
    Body: Thông tin đơn/route/time/weather tối thiểu.
    Returns: late_risk_prob, late_risk_label, top_features
    """
    try:
        service = get_logistics_service()
        
        # Convert request to dict
        payload = request.dict(exclude_none=True)
        
        # Predict
        result = predict_logistics_delay(service, payload)
        
        return {
            "status": "success",
            "prediction": result
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}. Please train the model first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/revenue/forecast")
async def predict_revenue_endpoint(request: RevenueForecastRequest):
    """
    Predict revenue forecast.
    
    Body: region/category & timestamp (hoặc context).
    Returns: forecasted_revenue, confidence_range
    """
    try:
        service = get_revenue_service()
        
        # Convert request to dict
        payload = request.dict(exclude_none=True)
        
        # Predict
        result = predict_revenue(service, payload)
        
        return {
            "status": "success",
            "prediction": result
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}. Please train the model first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/customer/churn")
async def predict_churn_endpoint(request: ChurnRequest):
    """
    Predict customer churn.
    
    Body: customer_id hoặc feature snapshot.
    Returns: churn_prob, churn_label
    """
    try:
        service = get_churn_service()
        
        # Convert request to dict
        payload = request.dict(exclude_none=True)
        
        # Predict
        result = predict_churn(service, payload)
        
        return {
            "status": "success",
            "prediction": result
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}. Please train the model first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/models/status")
async def get_models_status():
    """
    Get status of all ML models (loaded or not).
    """
    models_status = {}
    
    model_names = ['logistics_delay', 'revenue_forecast', 'churn']
    
    for model_name in model_names:
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', f'{model_name}_model.pkl')
        models_status[model_name] = {
            'loaded': os.path.exists(model_path),
            'path': model_path
        }
    
    return {
        "status": "success",
        "models": models_status
    }


# ============================================================================
# HTML PAGES FOR EACH MODEL
# ============================================================================

@router.get("/late-delivery", response_class=HTMLResponse)
async def late_delivery_page(request: Request):
    """
    Trang dự đoán Late Delivery.
    """
    return templates.TemplateResponse("ml_late_delivery.html", {"request": request})


@router.get("/revenue-forecast", response_class=HTMLResponse)
async def revenue_forecast_page(request: Request):
    """
    Trang dự báo Revenue Forecast.
    """
    return templates.TemplateResponse("ml_revenue_forecast.html", {"request": request})


@router.get("/customer-churn", response_class=HTMLResponse)
async def customer_churn_page(request: Request):
    """
    Trang dự đoán Customer Churn.
    """
    return templates.TemplateResponse("ml_customer_churn.html", {"request": request})

