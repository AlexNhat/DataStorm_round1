"""
Digital Twin State: Trạng thái hiện tại của supply chain.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class WarehouseState:
    """Trạng thái của một warehouse."""
    warehouse_id: str
    location: Dict[str, float]  # lat, lon
    inventory: Dict[str, int]  # product_id -> quantity
    capacity: int
    operating: bool = True
    
    def get_inventory_level(self, product_id: str) -> int:
        """Lấy inventory level của product."""
        return self.inventory.get(product_id, 0)
    
    def add_inventory(self, product_id: str, quantity: int):
        """Thêm inventory."""
        current = self.inventory.get(product_id, 0)
        self.inventory[product_id] = min(current + quantity, self.capacity)
    
    def remove_inventory(self, product_id: str, quantity: int) -> bool:
        """Xóa inventory. Returns True nếu thành công."""
        current = self.inventory.get(product_id, 0)
        if current >= quantity:
            self.inventory[product_id] = current - quantity
            return True
        return False


@dataclass
class TransportState:
    """Trạng thái của một transport route."""
    route_id: str
    origin: str  # warehouse_id
    destination: str  # warehouse_id or customer_location
    distance_km: float
    current_weather: Dict[str, float]  # temperature, precipitation, wind_speed
    congestion_level: float = 0.0  # 0-1
    estimated_duration_hours: float = 0.0
    actual_duration_hours: Optional[float] = None
    
    def calculate_duration(self) -> float:
        """Tính duration dựa trên distance, weather, congestion."""
        base_duration = self.distance_km / 60.0  # Giả sử 60 km/h
        
        # Weather impact
        weather_factor = 1.0
        if self.current_weather.get('precipitation', 0) > 10:
            weather_factor += 0.3
        if self.current_weather.get('wind_speed', 0) > 20:
            weather_factor += 0.2
        
        # Congestion impact
        congestion_factor = 1.0 + self.congestion_level * 0.5
        
        self.estimated_duration_hours = base_duration * weather_factor * congestion_factor
        return self.estimated_duration_hours


@dataclass
class OrderState:
    """Trạng thái của một order."""
    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    order_date: datetime
    expected_delivery_date: datetime
    actual_delivery_date: Optional[datetime] = None
    status: str = "pending"  # pending, in_transit, delivered, delayed, cancelled
    source_warehouse: Optional[str] = None
    transport_route: Optional[str] = None
    
    def is_late(self) -> bool:
        """Kiểm tra xem order có trễ không."""
        if self.actual_delivery_date is None:
            return datetime.now() > self.expected_delivery_date
        return self.actual_delivery_date > self.expected_delivery_date


class DigitalTwinState:
    """
    Trạng thái tổng thể của Digital Twin Supply Chain.
    """
    
    def __init__(self):
        self.timestamp = datetime.now()
        
        # Warehouses
        self.warehouses: Dict[str, WarehouseState] = {}
        
        # Transport routes
        self.transport_routes: Dict[str, TransportState] = {}
        
        # Orders
        self.orders: Dict[str, OrderState] = {}
        self.order_history: List[OrderState] = []
        
        # Weather
        self.weather: Dict[str, Dict[str, float]] = {}  # location -> weather data
        
        # Metrics
        self.metrics = {
            'total_orders': 0,
            'delivered_orders': 0,
            'late_orders': 0,
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'inventory_value': 0.0
        }
    
    def add_warehouse(self, warehouse: WarehouseState):
        """Thêm warehouse."""
        self.warehouses[warehouse.warehouse_id] = warehouse
    
    def add_transport_route(self, route: TransportState):
        """Thêm transport route."""
        self.transport_routes[route.route_id] = route
    
    def add_order(self, order: OrderState):
        """Thêm order."""
        self.orders[order.order_id] = order
        self.metrics['total_orders'] += 1
    
    def update_weather(self, location: str, weather_data: Dict[str, float]):
        """Cập nhật weather cho location."""
        self.weather[location] = weather_data
        
        # Update transport routes affected by weather
        for route in self.transport_routes.values():
            if location in [route.origin, route.destination]:
                route.current_weather = weather_data
                route.calculate_duration()
    
    def update_order_status(self, order_id: str, status: str, **kwargs):
        """Cập nhật status của order."""
        if order_id in self.orders:
            order = self.orders[order_id]
            order.status = status
            
            if status == 'delivered' and 'delivery_date' in kwargs:
                order.actual_delivery_date = kwargs['delivery_date']
                self.metrics['delivered_orders'] += 1
                
                if order.is_late():
                    self.metrics['late_orders'] += 1
            
            # Move to history if delivered or cancelled
            if status in ['delivered', 'cancelled']:
                self.order_history.append(order)
                del self.orders[order_id]
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Lấy summary của state."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'warehouses_count': len(self.warehouses),
            'transport_routes_count': len(self.transport_routes),
            'active_orders': len(self.orders),
            'total_orders': self.metrics['total_orders'],
            'delivered_orders': self.metrics['delivered_orders'],
            'late_orders': self.metrics['late_orders'],
            'on_time_rate': (
                self.metrics['delivered_orders'] - self.metrics['late_orders']
            ) / max(self.metrics['delivered_orders'], 1),
            'metrics': self.metrics
        }
    
    def reset(self):
        """Reset state về trạng thái ban đầu."""
        self.warehouses.clear()
        self.transport_routes.clear()
        self.orders.clear()
        self.order_history.clear()
        self.weather.clear()
        self.metrics = {
            'total_orders': 0,
            'delivered_orders': 0,
            'late_orders': 0,
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'inventory_value': 0.0
        }
        self.timestamp = datetime.now()

