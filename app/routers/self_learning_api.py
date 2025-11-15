"""
Self-Learning API: Endpoints cho V6 Self-Learning AI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sys
import os
import numpy as np

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from modules.self_learning.learning_loop import SelfLearningLoop
from modules.meta_learning.controller import MetaLearningController

router = APIRouter()

# Global learning loops (trong thực tế nên dùng session/state management)
_learning_loops = {}


class ObserveRequest(BaseModel):
    """Observe request."""
    model_name: str
    features: List[float]
    actual_value: Optional[float] = None


class ModelStatusRequest(BaseModel):
    """Model status request."""
    model_name: str


@router.post("/observe")
async def observe_data(request: ObserveRequest):
    """
    Quan sát dữ liệu mới và cập nhật learning loop.
    """
    try:
        model_name = request.model_name
        
        # Get or create learning loop
        if model_name not in _learning_loops:
            model_path = os.path.join('models', f'{model_name}_model.pkl')
            if not os.path.exists(model_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Model not found: {model_path}. Train the model first."
                )
            
            _learning_loops[model_name] = SelfLearningLoop(
                model_name=model_name,
                model_path=model_path
            )
        
        loop = _learning_loops[model_name]
        
        # Convert features to numpy array
        X = np.array(request.features).reshape(1, -1)
        y_actual = request.actual_value
        
        # Observe
        loop.observe(X, y_actual)
        
        return {
            "status": "success",
            "message": f"Observed data for model {model_name}",
            "buffer_size": len(loop.prediction_buffer)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Observation error: {str(e)}")


@router.get("/status/{model_name}")
async def get_model_status(model_name: str):
    """
    Lấy trạng thái của learning loop.
    """
    try:
        if model_name not in _learning_loops:
            return {
                "status": "not_initialized",
                "message": f"Learning loop for {model_name} not initialized"
            }
        
        loop = _learning_loops[model_name]
        status = loop.get_status()
        
        return {
            "status": "success",
            "model_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")


@router.get("/meta/status")
async def get_meta_learning_status():
    """
    Lấy trạng thái của Meta-Learning Controller.
    """
    try:
        # Trong thực tế, nên có global meta controller
        return {
            "status": "success",
            "message": "Meta-learning status endpoint (requires initialization)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meta-learning status error: {str(e)}")

