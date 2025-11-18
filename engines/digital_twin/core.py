"""
Digital Twin Engine: Core engine cho Digital Twin Supply Chain.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os

from .state import DigitalTwinState, WarehouseState, TransportState, OrderState
from .simulator import EventSimulator


class DigitalTwinEngine:
    """
    Digital Twin Engine: Mô phỏng toàn bộ supply chain.
    
    Phạm vi mô phỏng:
    - Inventory across warehouses
    - Transport networks
    - Weather impacts
    - Lead times
    - Customer demand behavior
    - Supply delays
    - Churn dynamics
    - Pricing elasticity
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.state = DigitalTwinState()
        self.event_simulator = EventSimulator()
        self.simulation_history = []
        self.current_step = 0
    
    def initialize(
        self,
        warehouses: List[Dict],
        transport_routes: List[Dict],
        initial_weather: Optional[Dict] = None
    ):
        """
        Khởi tạo Digital Twin với warehouses và routes.
        
        Args:
            warehouses: List of warehouse configs
            transport_routes: List of route configs
            initial_weather: Initial weather data
        """
        # Initialize warehouses
        for wh_config in warehouses:
            warehouse = WarehouseState(
                warehouse_id=wh_config['warehouse_id'],
                location=wh_config['location'],
                inventory=wh_config.get('inventory', {}),
                capacity=wh_config.get('capacity', 10000),
                operating=wh_config.get('operating', True)
            )
            self.state.add_warehouse(warehouse)
        
        # Initialize transport routes
        for route_config in transport_routes:
            route = TransportState(
                route_id=route_config['route_id'],
                origin=route_config['origin'],
                destination=route_config['destination'],
                distance_km=route_config['distance_km'],
                current_weather=route_config.get('weather', {})
            )
            route.calculate_duration()
            self.state.add_transport_route(route)
        
        # Initialize weather
        if initial_weather:
            for location, weather_data in initial_weather.items():
                self.state.update_weather(location, weather_data)
    
    def simulate_step(self, events: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Chạy một step simulation.
        
        Args:
            events: List of events to simulate (orders, weather changes, etc.)
            
        Returns:
            Step results
        """
        self.current_step += 1
        self.state.timestamp += timedelta(hours=1)  # Advance time by 1 hour
        
        # Process events
        if events:
            for event in events:
                self._process_event(event)
        
        # Update orders in transit
        self._update_orders_in_transit()
        
        # Calculate metrics
        self._update_metrics()
        
        # Save step state
        step_result = {
            'step': self.current_step,
            'timestamp': self.state.timestamp.isoformat(),
            'state_summary': self.state.get_state_summary(),
            'events_processed': len(events) if events else 0
        }
        
        self.simulation_history.append(step_result)
        return step_result
    
    def _process_event(self, event: Dict):
        """Xử lý một event."""
        event_type = event.get('type')
        
        if event_type == 'order':
            self._process_order_event(event)
        elif event_type == 'weather_change':
            self._process_weather_event(event)
        elif event_type == 'warehouse_outage':
            self._process_warehouse_outage(event)
        elif event_type == 'supply_delay':
            self._process_supply_delay(event)
        elif event_type == 'demand_surge':
            self._process_demand_surge(event)
    
    def _process_order_event(self, event: Dict):
        """Xử lý order event."""
        order = OrderState(
            order_id=event.get('order_id', f'order_{len(self.state.orders)}'),
            customer_id=event['customer_id'],
            product_id=event['product_id'],
            quantity=event['quantity'],
            order_date=self.state.timestamp,
            expected_delivery_date=self.state.timestamp + timedelta(days=event.get('expected_days', 3))
        )
        
        # Find source warehouse
        source_warehouse = self._find_source_warehouse(order.product_id, order.quantity)
        if source_warehouse:
            order.source_warehouse = source_warehouse.warehouse_id
            
            # Remove inventory
            if source_warehouse.remove_inventory(order.product_id, order.quantity):
                order.status = 'in_transit'
                
                # Find transport route
                route = self._find_transport_route(
                    source_warehouse.warehouse_id,
                    event.get('destination', 'customer_location')
                )
                if route:
                    order.transport_route = route.route_id
                    # Estimate delivery based on route duration
                    order.expected_delivery_date = self.state.timestamp + timedelta(hours=route.estimated_duration_hours)
        
        self.state.add_order(order)
    
    def _process_weather_event(self, event: Dict):
        """Xử lý weather change event."""
        location = event['location']
        weather_data = event['weather_data']
        self.state.update_weather(location, weather_data)
    
    def _process_warehouse_outage(self, event: Dict):
        """Xử lý warehouse outage."""
        warehouse_id = event['warehouse_id']
        if warehouse_id in self.state.warehouses:
            self.state.warehouses[warehouse_id].operating = False
    
    def _process_supply_delay(self, event: Dict):
        """Xử lý supply delay."""
        # Update transport routes affected
        route_id = event.get('route_id')
        if route_id and route_id in self.state.transport_routes:
            route = self.state.transport_routes[route_id]
            route.congestion_level = min(route.congestion_level + 0.3, 1.0)
            route.calculate_duration()
    
    def _process_demand_surge(self, event: Dict):
        """Xử lý demand surge."""
        # Increase order frequency temporarily
        # This will be handled by event generator
        pass
    
    def _find_source_warehouse(self, product_id: str, quantity: int) -> Optional[WarehouseState]:
        """Tìm warehouse có đủ inventory."""
        for warehouse in self.state.warehouses.values():
            if warehouse.operating and warehouse.get_inventory_level(product_id) >= quantity:
                return warehouse
        return None
    
    def _find_transport_route(self, origin: str, destination: str) -> Optional[TransportState]:
        """Tìm transport route."""
        for route in self.state.transport_routes.values():
            if route.origin == origin and route.destination == destination:
                return route
        return None
    
    def _update_orders_in_transit(self):
        """Cập nhật orders đang vận chuyển."""
        for order_id, order in list(self.state.orders.items()):
            if order.status == 'in_transit':
                # Check if delivery time reached
                if self.state.timestamp >= order.expected_delivery_date:
                    self.state.update_order_status(order_id, 'delivered', delivery_date=self.state.timestamp)
                elif self.state.timestamp > order.expected_delivery_date:
                    self.state.update_order_status(order_id, 'delayed')
    
    def _update_metrics(self):
        """Cập nhật metrics."""
        # Calculate inventory value
        total_inventory_value = 0.0
        for warehouse in self.state.warehouses.values():
            for product_id, quantity in warehouse.inventory.items():
                # Assume product value (should be in config)
                product_value = self.config.get('product_values', {}).get(product_id, 10.0)
                total_inventory_value += quantity * product_value
        
        self.state.metrics['inventory_value'] = total_inventory_value
    
    def run_simulation(
        self,
        duration_hours: int,
        event_generator: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chạy simulation trong một khoảng thời gian.
        
        Args:
            duration_hours: Số giờ simulation
            event_generator: Generator để tạo events
            
        Returns:
            List of step results
        """
        results = []
        
        for hour in range(duration_hours):
            # Generate events
            events = []
            if event_generator:
                events = event_generator.generate_events(self.state, hour)
            
            # Simulate step
            step_result = self.simulate_step(events)
            results.append(step_result)
        
        return results
    
    def get_state(self) -> DigitalTwinState:
        """Lấy current state."""
        return self.state
    
    def reset(self):
        """Reset simulation."""
        self.state.reset()
        self.simulation_history.clear()
        self.current_step = 0

