"""
What-If Analysis Service: Phân tích "what-if" scenarios.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import sys

# Add engines to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from engines.digital_twin.core import DigitalTwinEngine
from engines.digital_twin.state import DigitalTwinState


class WhatIfAnalyzer:
    """
    Phân tích what-if scenarios.
    
    Cho phép user hỏi:
    - "Nếu mưa tăng 40%, giao trễ tăng bao nhiêu?"
    - "Nếu tăng tồn kho ở kho A thêm 15%, chi phí thay đổi thế nào?"
    - "Nếu chuyển 20% sản phẩm sang kho B, tỷ lệ giao đúng tăng thế nào?"
    """
    
    def __init__(self, digital_twin_engine: Optional[DigitalTwinEngine] = None):
        """
        Args:
            digital_twin_engine: Digital Twin Engine instance
        """
        self.engine = digital_twin_engine or DigitalTwinEngine()
        self.baseline_results = None
    
    def analyze(
        self,
        scenario: Dict[str, Any],
        baseline_state: Optional[DigitalTwinState] = None,
        simulation_duration_hours: int = 168  # 1 week
    ) -> Dict[str, Any]:
        """
        Phân tích what-if scenario.
        
        Args:
            scenario: Scenario config
            baseline_state: Baseline state để so sánh
            simulation_duration_hours: Duration của simulation
            
        Returns:
            Analysis results với comparison
        """
        # Run baseline simulation
        if baseline_state:
            self.engine.state = baseline_state
        else:
            # Use current state as baseline
            pass
        
        baseline_results = self._run_baseline_simulation(simulation_duration_hours)
        self.baseline_results = baseline_results
        
        # Apply scenario changes
        modified_state = self._apply_scenario(self.engine.state, scenario)
        self.engine.state = modified_state
        
        # Run scenario simulation
        scenario_results = self._run_scenario_simulation(scenario, simulation_duration_hours)
        
        # Compare results
        comparison = self._compare_results(baseline_results, scenario_results)
        
        return {
            'scenario': scenario,
            'baseline_results': baseline_results,
            'scenario_results': scenario_results,
            'comparison': comparison,
            'recommendations': self._generate_recommendations(comparison)
        }
    
    def _run_baseline_simulation(self, duration_hours: int) -> Dict[str, Any]:
        """Chạy baseline simulation."""
        # Reset và chạy simulation
        self.engine.reset()
        results = self.engine.run_simulation(duration_hours)
        
        # Tính metrics tổng hợp
        final_state = self.engine.get_state()
        return {
            'total_orders': final_state.metrics['total_orders'],
            'delivered_orders': final_state.metrics['delivered_orders'],
            'late_orders': final_state.metrics['late_orders'],
            'on_time_rate': (
                final_state.metrics['delivered_orders'] - final_state.metrics['late_orders']
            ) / max(final_state.metrics['delivered_orders'], 1),
            'total_revenue': final_state.metrics['total_revenue'],
            'total_cost': final_state.metrics['total_cost'],
            'inventory_value': final_state.metrics['inventory_value']
        }
    
    def _run_scenario_simulation(
        self,
        scenario: Dict[str, Any],
        duration_hours: int
    ) -> Dict[str, Any]:
        """Chạy scenario simulation."""
        # Apply scenario modifications
        # (đã apply trong analyze())
        
        # Run simulation
        results = self.engine.run_simulation(duration_hours)
        
        # Tính metrics tổng hợp
        final_state = self.engine.get_state()
        return {
            'total_orders': final_state.metrics['total_orders'],
            'delivered_orders': final_state.metrics['delivered_orders'],
            'late_orders': final_state.metrics['late_orders'],
            'on_time_rate': (
                final_state.metrics['delivered_orders'] - final_state.metrics['late_orders']
            ) / max(final_state.metrics['delivered_orders'], 1),
            'total_revenue': final_state.metrics['total_revenue'],
            'total_cost': final_state.metrics['total_cost'],
            'inventory_value': final_state.metrics['inventory_value']
        }
    
    def _apply_scenario(
        self,
        state: DigitalTwinState,
        scenario: Dict[str, Any]
    ) -> DigitalTwinState:
        """Áp dụng scenario changes vào state."""
        modified_state = state  # Shallow copy (trong thực tế nên deep copy)
        
        scenario_type = scenario.get('type')
        
        if scenario_type == 'weather_change':
            # Thay đổi weather
            multiplier = scenario.get('multiplier', 1.0)
            for location, weather_data in modified_state.weather.items():
                modified_state.update_weather(location, {
                    'precipitation': weather_data.get('precipitation', 0) * multiplier,
                    'wind_speed': weather_data.get('wind_speed', 0) * multiplier,
                    'temperature': weather_data.get('temperature', 20)
                })
        
        elif scenario_type == 'inventory_change':
            # Thay đổi inventory
            warehouse_id = scenario.get('warehouse_id')
            multiplier = scenario.get('multiplier', 1.0)
            if warehouse_id in modified_state.warehouses:
                warehouse = modified_state.warehouses[warehouse_id]
                for product_id in warehouse.inventory:
                    current = warehouse.inventory[product_id]
                    warehouse.inventory[product_id] = int(current * multiplier)
        
        elif scenario_type == 'demand_change':
            # Thay đổi demand rate
            multiplier = scenario.get('multiplier', 1.0)
            # Update event generator config
            if hasattr(self.engine.event_simulator, 'config'):
                self.engine.event_simulator.config['order_rate_per_hour'] *= multiplier
        
        return modified_state
    
    def _compare_results(
        self,
        baseline: Dict[str, Any],
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """So sánh baseline vs scenario."""
        comparison = {}
        
        for key in baseline.keys():
            if isinstance(baseline[key], (int, float)):
                baseline_val = baseline[key]
                scenario_val = scenario[key]
                
                if baseline_val != 0:
                    change_pct = ((scenario_val - baseline_val) / baseline_val) * 100
                else:
                    change_pct = 0.0
                
                comparison[key] = {
                    'baseline': baseline_val,
                    'scenario': scenario_val,
                    'change': scenario_val - baseline_val,
                    'change_pct': change_pct
                }
        
        return comparison
    
    def _generate_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """Sinh recommendations dựa trên comparison."""
        recommendations = []
        
        # Check on-time rate
        if 'on_time_rate' in comparison:
            change_pct = comparison['on_time_rate']['change_pct']
            if change_pct > 5:
                recommendations.append(
                    f"On-time delivery rate improved by {change_pct:.1f}%. "
                    "Scenario shows positive impact on delivery performance."
                )
            elif change_pct < -5:
                recommendations.append(
                    f"On-time delivery rate decreased by {abs(change_pct):.1f}%. "
                    "Consider alternative strategies to maintain delivery performance."
                )
        
        # Check cost
        if 'total_cost' in comparison:
            change_pct = comparison['total_cost']['change_pct']
            if change_pct > 10:
                recommendations.append(
                    f"Total cost increased by {change_pct:.1f}%. "
                    "Evaluate cost-benefit trade-off."
                )
            elif change_pct < -10:
                recommendations.append(
                    f"Total cost decreased by {abs(change_pct):.1f}%. "
                    "Scenario shows cost-saving potential."
                )
        
        # Check inventory
        if 'inventory_value' in comparison:
            change_pct = comparison['inventory_value']['change_pct']
            if change_pct > 20:
                recommendations.append(
                    f"Inventory value increased by {change_pct:.1f}%. "
                    "Monitor for overstocking risks."
                )
            elif change_pct < -20:
                recommendations.append(
                    f"Inventory value decreased by {abs(change_pct):.1f}%. "
                    "Monitor for stockout risks."
                )
        
        return recommendations
    
    def parse_natural_language_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query thành scenario.
        
        Ví dụ:
        - "Nếu mưa tăng 40%, giao trễ tăng bao nhiêu?"
        - "Nếu tăng tồn kho ở kho A thêm 15%, chi phí thay đổi thế nào?"
        """
        scenario = {}
        query_lower = query.lower()
        
        # Weather change
        if 'mưa' in query_lower or 'rain' in query_lower or 'precipitation' in query_lower:
            scenario['type'] = 'weather_change'
            # Extract percentage
            import re
            pct_match = re.search(r'(\d+)%', query)
            if pct_match:
                pct = float(pct_match.group(1))
                scenario['multiplier'] = 1.0 + (pct / 100.0)
        
        # Inventory change
        elif 'tồn kho' in query_lower or 'inventory' in query_lower:
            scenario['type'] = 'inventory_change'
            # Extract warehouse
            if 'kho a' in query_lower or 'warehouse a' in query_lower:
                scenario['warehouse_id'] = 'warehouse_a'
            # Extract percentage
            import re
            pct_match = re.search(r'(\d+)%', query)
            if pct_match:
                pct = float(pct_match.group(1))
                scenario['multiplier'] = 1.0 + (pct / 100.0)
        
        # Demand change
        elif 'nhu cầu' in query_lower or 'demand' in query_lower:
            scenario['type'] = 'demand_change'
            import re
            pct_match = re.search(r'(\d+)%', query)
            if pct_match:
                pct = float(pct_match.group(1))
                scenario['multiplier'] = 1.0 + (pct / 100.0)
        
        return scenario

