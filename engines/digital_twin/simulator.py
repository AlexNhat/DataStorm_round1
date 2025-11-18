"""
Event Simulator: Tạo events cho simulation.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random


class EventSimulator:
    """
    Simulate events: orders, weather changes, disruptions, etc.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: Configuration cho event generation
        """
        self.config = config or {
            'order_rate_per_hour': 10,  # Average orders per hour
            'weather_change_probability': 0.1,  # 10% chance per hour
            'disruption_probability': 0.05  # 5% chance per hour
        }
    
    def generate_events(
        self,
        state: Any,
        hour: int
    ) -> List[Dict]:
        """
        Generate events cho một hour.
        
        Args:
            state: DigitalTwinState
            hour: Current hour
            
        Returns:
            List of events
        """
        events = []
        
        # Generate orders
        num_orders = np.random.poisson(self.config['order_rate_per_hour'])
        for _ in range(num_orders):
            order_event = self._generate_order_event(state)
            if order_event:
                events.append(order_event)
        
        # Generate weather changes
        if np.random.random() < self.config['weather_change_probability']:
            weather_event = self._generate_weather_event(state)
            if weather_event:
                events.append(weather_event)
        
        # Generate disruptions
        if np.random.random() < self.config['disruption_probability']:
            disruption_event = self._generate_disruption_event(state)
            if disruption_event:
                events.append(disruption_event)
        
        return events
    
    def _generate_order_event(self, state: Any) -> Optional[Dict]:
        """Generate order event."""
        # Random customer, product, quantity
        customer_id = f"customer_{random.randint(1, 1000)}"
        product_id = f"product_{random.randint(1, 50)}"
        quantity = random.randint(1, 10)
        
        return {
            'type': 'order',
            'customer_id': customer_id,
            'product_id': product_id,
            'quantity': quantity,
            'expected_days': random.randint(2, 5)
        }
    
    def _generate_weather_event(self, state: Any) -> Optional[Dict]:
        """Generate weather change event."""
        # Random location
        locations = list(state.weather.keys()) if state.weather else ['location_1']
        if not locations:
            return None
        
        location = random.choice(locations)
        
        # Random weather change
        weather_data = {
            'temperature': np.random.normal(20, 10),
            'precipitation': max(0, np.random.exponential(5)),
            'wind_speed': max(0, np.random.exponential(10))
        }
        
        return {
            'type': 'weather_change',
            'location': location,
            'weather_data': weather_data
        }
    
    def _generate_disruption_event(self, state: Any) -> Optional[Dict]:
        """Generate disruption event."""
        disruption_type = random.choice(['warehouse_outage', 'supply_delay'])
        
        if disruption_type == 'warehouse_outage':
            warehouses = list(state.warehouses.keys())
            if warehouses:
                return {
                    'type': 'warehouse_outage',
                    'warehouse_id': random.choice(warehouses),
                    'duration_hours': random.randint(1, 24)
                }
        
        elif disruption_type == 'supply_delay':
            routes = list(state.transport_routes.keys())
            if routes:
                return {
                    'type': 'supply_delay',
                    'route_id': random.choice(routes),
                    'delay_hours': random.randint(2, 12)
                }
        
        return None

