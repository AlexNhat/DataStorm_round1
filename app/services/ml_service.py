"""
ML Service: Load models và thực hiện predictions.

Cung cấp các hàm:
- load_logistics_delay_model(), predict_logistics_delay(payload)
- load_revenue_forecast_model(), predict_revenue(payload)
- load_churn_model(), predict_churn(payload)
"""

import os
import json
import math
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from modules.logging_utils import log_inference, log_inference_warning

# Đường dẫn
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BASE_DIR_PATH = Path(BASE_DIR)
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODELS_PATH = BASE_DIR_PATH / "models"

_inventory_rl_model = None
_inventory_rl_features: Optional[List[str]] = None
_pricing_model = None
_pricing_feature_names: Optional[List[str]] = None

INVENTORY_DEFAULTS = {
    "weather_risk_index": 0.0,
    "temp_7d_avg": 0.0,
    "rain_7d_avg": 0.0,
    "storm_flag": 0.0,
    "region_congestion_index": 1.0,
    "warehouse_workload_score": 0.0,
    "Order Item Product Price": 0.0,
    "Sales": 0.0,
    "Order Item Total": 0.0,
}
PRICING_BASE_FEATURES = ["price_log", "sales_log", "weather_risk_index", "weather_influence"]


class MLModelService:
    """Service class để quản lý ML models."""
    
    def __init__(self):
        self.models = {}
        self.preprocessors = {}
        self.schemas = {}
    
    def _load_model_artifacts(self, model_name: str):
        """Load model, preprocessor, và schema."""
        if model_name in self.models:
            return  # Already loaded
        
        model_path = os.path.join(MODELS_DIR, f'{model_name}_model.pkl')
        preprocessor_path = os.path.join(MODELS_DIR, f'{model_name}_preprocessor.pkl')
        schema_path = os.path.join(MODELS_DIR, f'{model_name}_feature_schema.json')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}. Train the model first.")
        
        self.models[model_name] = joblib.load(model_path)
        self.preprocessors[model_name] = joblib.load(preprocessor_path)
        
        with open(schema_path, 'r') as f:
            self.schemas[model_name] = json.load(f)
    
    def _prepare_features(self, payload: Dict, model_name: str) -> np.ndarray:
        """
        Prepare features từ payload theo schema của model.
        """
        preprocessor = self.preprocessors[model_name]
        schema = self.schemas[model_name]
        feature_names = schema['feature_names']
        
        # Tạo feature vector
        feature_vector = []
        
        for feature_name in feature_names:
            if feature_name in payload:
                value = payload[feature_name]
            elif feature_name.replace('_encoded', '') in payload:
                # Encode categorical
                original_col = feature_name.replace('_encoded', '')
                if original_col in preprocessor.get('label_encoders', {}):
                    le = preprocessor['label_encoders'][original_col]
                    try:
                        value = le.transform([str(payload[original_col])])[0]
                    except:
                        value = 0  # Unknown category
                else:
                    value = payload[original_col]
            else:
                # Missing feature - use default
                value = 0
            
            feature_vector.append(float(value))
        
        feature_array = np.array(feature_vector).reshape(1, -1)
        
        # Scale
        if 'scaler' in preprocessor:
            feature_array = preprocessor['scaler'].transform(feature_array)
        
        return feature_array


def load_logistics_delay_model() -> MLModelService:
    """
    Load logistics delay prediction model.
    """
    service = MLModelService()
    service._load_model_artifacts('logistics_delay')
    return service


def predict_logistics_delay(service: MLModelService, payload: Dict) -> Dict:
    """
    Predict logistics delay risk.
    
    Args:
        service: MLModelService instance
        payload: Dict với features cần thiết
        
    Returns:
        Dict với late_risk_prob, late_risk_label, top_features
    """
    start_time = time.perf_counter()
    try:
        # Prepare features
        X = service._prepare_features(payload, 'logistics_delay')
        
        # Predict
        model = service.models['logistics_delay']
        prob = model.predict_proba(X)[0, 1]  # Probability of late delivery
        label = 1 if prob > 0.5 else 0
        
        # Feature importance (nếu có)
        top_features = None
        if hasattr(model, 'feature_importances_'):
            feature_names = service.schemas['logistics_delay']['feature_names']
            importances = model.feature_importances_
            top_indices = np.argsort(importances)[-5:][::-1]
            top_features = [
                {'feature': feature_names[i], 'importance': float(importances[i])}
                for i in top_indices
            ]
        
        result = {
            'late_risk_prob': float(prob),
            'late_risk_label': int(label),
            'top_features': top_features
        }
        latency_ms = (time.perf_counter() - start_time) * 1000
        log_inference(
            "Late Delivery Classifier",
            params=payload,
            latency_ms=latency_ms,
            result_summary={"late_risk_prob": result["late_risk_prob"], "late_risk_label": result["late_risk_label"]},
        )
        if prob > 0.85:
            log_inference_warning(
                "Late Delivery Classifier",
                detail=f"High late risk probability ({prob:.2f}) detected",
                severity="high",
            )
        return result
    except Exception as e:
        log_inference_warning("Late Delivery Classifier", detail=f"Prediction failure: {e}", severity="high")
        raise ValueError(f"Error in prediction: {str(e)}")


def load_revenue_forecast_model() -> MLModelService:
    """
    Load revenue forecast model.
    """
    service = MLModelService()
    service._load_model_artifacts('revenue_forecast')
    return service


def predict_revenue(service: MLModelService, payload: Dict) -> Dict:
    """
    Predict revenue forecast.
    
    Args:
        service: MLModelService instance
        payload: Dict với features cần thiết
        
    Returns:
        Dict với forecasted_revenue, confidence_range
    """
    start_time = time.perf_counter()
    try:
        # Prepare features
        X = service._prepare_features(payload, 'revenue_forecast')
        
        # Predict
        model = service.models['revenue_forecast']
        prediction = model.predict(X)[0]
        
        # Confidence range (simplified: ±20% của prediction)
        confidence_lower = prediction * 0.8
        confidence_upper = prediction * 1.2
        
        result = {
            'forecasted_revenue': float(prediction),
            'confidence_range': {
                'lower': float(confidence_lower),
                'upper': float(confidence_upper)
            }
        }
        latency_ms = (time.perf_counter() - start_time) * 1000
        log_inference(
            "Demand Forecast Ensemble",
            params=payload,
            latency_ms=latency_ms,
            result_summary={"forecasted_revenue": result["forecasted_revenue"]},
        )
        if prediction < 0:
            log_inference_warning(
                "Demand Forecast Ensemble",
                detail="Negative revenue forecast detected",
                severity="medium",
            )
        return result
    except Exception as e:
        log_inference_warning("Demand Forecast Ensemble", detail=f"Prediction failure: {e}", severity="high")
        raise ValueError(f"Error in prediction: {str(e)}")


def load_churn_model() -> MLModelService:
    """
    Load customer churn prediction model.
    """
    service = MLModelService()
    service._load_model_artifacts('churn')
    return service


def predict_churn(service: MLModelService, payload: Dict) -> Dict:
    """
    Predict customer churn.
    
    Args:
        service: MLModelService instance
        payload: Dict với features cần thiết (có thể chỉ cần customer_id)
        
    Returns:
        Dict với churn_prob, churn_label
    """
    start_time = time.perf_counter()
    try:
        # Prepare features
        X = service._prepare_features(payload, 'churn')
        
        # Predict
        model = service.models['churn']
        prob = model.predict_proba(X)[0, 1]  # Probability of churn
        label = 1 if prob > 0.5 else 0
        
        result = {
            'churn_prob': float(prob),
            'churn_label': int(label)
        }
        latency_ms = (time.perf_counter() - start_time) * 1000
        log_inference(
            "Customer Churn Model",
            params=payload,
            latency_ms=latency_ms,
            result_summary={"churn_prob": result["churn_prob"], "churn_label": result["churn_label"]},
        )
        if prob > 0.85:
            log_inference_warning(
                "Customer Churn Model",
                detail=f"High churn probability ({prob:.2f}) detected",
                severity="medium",
            )
        return result
    except Exception as e:
        log_inference_warning("Customer Churn Model", detail=f"Prediction failure: {e}", severity="high")
        raise ValueError(f"Error in prediction: {str(e)}")


def _load_inventory_rl_artifacts():
    global _inventory_rl_model, _inventory_rl_features
    if _inventory_rl_model is None:
        model_path = MODELS_PATH / "inventory_rl" / "global" / "inventory_rl_global.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Inventory RL model not found: {model_path}")
        _inventory_rl_model = joblib.load(model_path)
        schema_path = model_path.with_name("feature_schema.json")
        if schema_path.exists():
            schema = json.loads(schema_path.read_text())
            _inventory_rl_features = schema.get("feature_names") or list(INVENTORY_DEFAULTS.keys())
        else:
            _inventory_rl_features = list(INVENTORY_DEFAULTS.keys())
    return _inventory_rl_model, _inventory_rl_features or list(INVENTORY_DEFAULTS.keys())


def predict_inventory_rl(payload: Dict[str, Any]) -> Dict[str, float]:
    model, feature_names = _load_inventory_rl_artifacts()
    start_time = time.perf_counter()
    try:
        vector = []
        for feature in feature_names:
            value = payload.get(feature, INVENTORY_DEFAULTS.get(feature, 0.0))
            vector.append(float(value))
        X = np.array(vector, dtype=float).reshape(1, -1)
        prediction = float(model.predict(X)[0])
        result = {"recommended_qty_buffer": prediction}
        latency_ms = (time.perf_counter() - start_time) * 1000
        log_inference(
            "Inventory Optimizer RL",
            params=payload,
            latency_ms=latency_ms,
            result_summary=result,
            region=payload.get("region", "GLOBAL"),
        )
        if prediction < 0:
            log_inference_warning("Inventory Optimizer RL", detail="Negative buffer recommendation", severity="medium")
        return result
    except Exception as exc:  # pylint: disable=broad-except
        log_inference_warning("Inventory Optimizer RL", detail=f"Prediction failure: {exc}", severity="high")
        raise


def _load_pricing_elasticity_artifacts():
    global _pricing_model, _pricing_feature_names
    if _pricing_model is None:
        model_path = MODELS_PATH / "pricing" / "global" / "pricing_elasticity.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Pricing elasticity model not found: {model_path}")
        _pricing_model = joblib.load(model_path)
        schema_path = model_path.with_name("feature_columns.json")
        if schema_path.exists():
            schema = json.loads(schema_path.read_text())
            _pricing_feature_names = schema.get("feature_names") or PRICING_BASE_FEATURES
        else:
            _pricing_feature_names = PRICING_BASE_FEATURES
    return _pricing_model, _pricing_feature_names or PRICING_BASE_FEATURES


def predict_pricing_elasticity(payload: Dict[str, Any]) -> Dict[str, float]:
    model, feature_names = _load_pricing_elasticity_artifacts()
    start_time = time.perf_counter()
    try:
        vector = []
        for feature in feature_names:
            if feature == "price_log":
                base_price = payload.get("price", payload.get("price_log", 0.0))
                value = math.log1p(float(base_price))
            elif feature == "sales_log":
                base_sales = payload.get("sales", payload.get("sales_log", 0.0))
                value = math.log1p(float(base_sales))
            elif feature == "weather_risk_index":
                value = payload.get("weather_risk_index", 0.0)
            elif feature == "weather_influence":
                value = payload.get("weather_influence", payload.get("weather_risk_index", 0.0))
            else:
                value = payload.get(feature, 0.0)
            vector.append(float(value))
        X = np.array(vector, dtype=float).reshape(1, -1)
        prediction = float(model.predict(X)[0])
        expected_quantity = math.expm1(prediction)
        result = {
            "quantity_log": prediction,
            "expected_quantity": expected_quantity,
        }
        latency_ms = (time.perf_counter() - start_time) * 1000
        log_inference(
            "Pricing Elasticity Model",
            params=payload,
            latency_ms=latency_ms,
            result_summary=result,
            region=payload.get("region", "GLOBAL"),
        )
        if expected_quantity < 0:
            log_inference_warning("Pricing Elasticity Model", detail="Negative quantity projection", severity="medium")
        return result
    except Exception as exc:  # pylint: disable=broad-except
        log_inference_warning("Pricing Elasticity Model", detail=f"Prediction failure: {exc}", severity="high")
        raise


# Global service instances (lazy loading)
_logistics_service = None
_revenue_service = None
_churn_service = None


def get_logistics_service() -> MLModelService:
    """Get or create logistics delay service."""
    global _logistics_service
    if _logistics_service is None:
        _logistics_service = load_logistics_delay_model()
    return _logistics_service


def get_revenue_service() -> MLModelService:
    """Get or create revenue forecast service."""
    global _revenue_service
    if _revenue_service is None:
        _revenue_service = load_revenue_forecast_model()
    return _revenue_service


def get_churn_service() -> MLModelService:
    """Get or create churn service."""
    global _churn_service
    if _churn_service is None:
        _churn_service = load_churn_model()
    return _churn_service

