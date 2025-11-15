"""
What-If Analysis API: Endpoints cho what-if scenarios.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.services.what_if_service import WhatIfAnalyzer
from engines.digital_twin.core import DigitalTwinEngine

router = APIRouter()


class WhatIfScenario(BaseModel):
    """What-if scenario."""
    type: str  # 'weather_change', 'inventory_change', 'demand_change'
    multiplier: Optional[float] = None
    warehouse_id: Optional[str] = None
    location: Optional[str] = None
    params: Optional[Dict[str, Any]] = {}


class WhatIfRequest(BaseModel):
    """What-if analysis request."""
    scenario: WhatIfScenario
    simulation_duration_hours: int = 168


class NaturalLanguageQuery(BaseModel):
    """Natural language query."""
    query: str
    simulation_duration_hours: int = 168


@router.post("/analyze")
async def analyze_what_if(request: WhatIfRequest):
    """
    Phân tích what-if scenario.
    
    Returns:
        Analysis results với comparison
    """
    try:
        analyzer = WhatIfAnalyzer()
        
        # Convert scenario to dict
        scenario_dict = request.scenario.dict()
        
        # Run analysis
        results = analyzer.analyze(
            scenario=scenario_dict,
            simulation_duration_hours=request.simulation_duration_hours
        )
        
        return {
            "status": "success",
            "analysis": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analysis error: {str(e)}")


@router.post("/natural-language")
async def analyze_natural_language(request: NaturalLanguageQuery):
    """
    Phân tích what-if từ natural language query.
    
    Ví dụ:
    - "Nếu mưa tăng 40%, giao trễ tăng bao nhiêu?"
    - "Nếu tăng tồn kho ở kho A thêm 15%, chi phí thay đổi thế nào?"
    """
    try:
        analyzer = WhatIfAnalyzer()
        
        # Parse query
        scenario = analyzer.parse_natural_language_query(request.query)
        
        if not scenario:
            raise HTTPException(
                status_code=400,
                detail="Could not parse query. Please use clear language about weather, inventory, or demand changes."
            )
        
        # Run analysis
        results = analyzer.analyze(
            scenario=scenario,
            simulation_duration_hours=request.simulation_duration_hours
        )
        
        return {
            "status": "success",
            "parsed_scenario": scenario,
            "analysis": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Natural language analysis error: {str(e)}")

