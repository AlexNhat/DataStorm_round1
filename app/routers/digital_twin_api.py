"""
Digital Twin API: Endpoints cho Digital Twin simulation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from engines.digital_twin.core import DigitalTwinEngine
from engines.digital_twin.state import WarehouseState, TransportState

router = APIRouter()


class WarehouseConfig(BaseModel):
    """Warehouse configuration."""
    warehouse_id: str
    location: Dict[str, float]  # lat, lon
    inventory: Dict[str, int] = {}
    capacity: int = 10000
    operating: bool = True


class TransportRouteConfig(BaseModel):
    """Transport route configuration."""
    route_id: str
    origin: str
    destination: str
    distance_km: float
    weather: Dict[str, float] = {}


class SimulationRequest(BaseModel):
    """Simulation request."""
    warehouses: List[WarehouseConfig]
    transport_routes: List[TransportRouteConfig]
    duration_hours: int = 168  # 1 week
    initial_weather: Optional[Dict[str, Dict[str, float]]] = None


@router.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """
    Chạy Digital Twin simulation.
    
    Returns:
        Simulation results
    """
    try:
        engine = DigitalTwinEngine()
        
        # Convert to dict format
        warehouses = [wh.dict() for wh in request.warehouses]
        routes = [route.dict() for route in request.transport_routes]
        
        # Initialize
        engine.initialize(
            warehouses=warehouses,
            transport_routes=routes,
            initial_weather=request.initial_weather
        )
        
        # Run simulation
        results = engine.run_simulation(duration_hours=request.duration_hours)
        
        # Get final state
        final_state = engine.get_state()
        
        return {
            "status": "success",
            "simulation_results": results,
            "final_state": final_state.get_state_summary(),
            "total_steps": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.get("/state")
async def get_state():
    """
    Lấy current state của Digital Twin.
    
    Note: Cần có engine instance đang chạy (trong thực tế nên dùng session/state management)
    """
    return {
        "status": "success",
        "message": "State endpoint - requires active simulation session"
    }


@router.post("/reset")
async def reset_simulation():
    """Reset simulation."""
    return {
        "status": "success",
        "message": "Simulation reset"
    }

