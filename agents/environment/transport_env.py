"""
Transport Routing RL Environment.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    print("Warning: Gymnasium not installed. Install with: pip install gymnasium")


class TransportEnv:
    """
    Transport Routing Environment.
    
    Agent quyết định:
    - Route selection
    - Vehicle assignment
    - Priority ordering
    """
    
    def __init__(
        self,
        n_routes: int = 5,
        n_orders: int = 20,
        episode_length: int = 100
    ):
        if not GYMNASIUM_AVAILABLE:
            raise ImportError("Gymnasium required. Install with: pip install gymnasium")
        
        self.n_routes = n_routes
        self.n_orders = n_orders
        self.episode_length = episode_length
        
        # Observation: [route_status, order_priorities, weather, distances]
        obs_dim = n_routes + n_orders + 3 + n_routes  # route + orders + weather + distances
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        # Action: [route_selection, order_priorities]
        action_dim = n_routes + n_orders
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(action_dim,),
            dtype=np.float32
        )
        
        # State
        self.route_status = np.ones(n_routes)  # 1 = available, 0 = busy
        self.order_priorities = np.random.uniform(0, 1, n_orders)
        self.weather = np.array([20.0, 0.0, 10.0])
        self.route_distances = np.random.uniform(10, 500, n_routes)
        self.current_step = 0
        
        # Metrics
        self.total_delivery_time = 0.0
        self.late_deliveries = 0
        self.total_cost = 0.0
    
    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict]:
        """Reset environment."""
        if seed is not None:
            np.random.seed(seed)
        
        self.route_status = np.ones(self.n_routes)
        self.order_priorities = np.random.uniform(0, 1, self.n_orders)
        self.weather = np.array([
            np.random.normal(20, 10),
            max(0, np.random.exponential(5)),
            max(0, np.random.exponential(10))
        ])
        self.route_distances = np.random.uniform(10, 500, self.n_routes)
        self.current_step = 0
        
        self.total_delivery_time = 0.0
        self.late_deliveries = 0
        self.total_cost = 0.0
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Step environment."""
        # Parse action
        route_selection = action[:self.n_routes]
        order_priorities = action[self.n_routes:]
        
        # Select route (highest value)
        selected_route = np.argmax(route_selection)
        
        # Calculate delivery time
        base_time = self.route_distances[selected_route] / 60.0  # hours at 60 km/h
        
        # Weather impact
        weather_factor = 1.0
        if self.weather[1] > 10:  # High precipitation
            weather_factor += 0.3
        if self.weather[2] > 20:  # High wind
            weather_factor += 0.2
        
        delivery_time = base_time * weather_factor
        self.total_delivery_time += delivery_time
        
        # Cost
        route_cost = self.route_distances[selected_route] * 0.5  # $0.5 per km
        self.total_cost += route_cost
        
        # Check if late (assume expected time = base_time)
        if delivery_time > base_time * 1.2:
            self.late_deliveries += 1
        
        # Update weather
        self.weather += np.random.normal(0, 1, 3)
        self.weather[1] = max(0, self.weather[1])
        self.weather[2] = max(0, self.weather[2])
        
        # Calculate reward
        reward = -self.total_cost / 1000.0 - self.late_deliveries * 0.1
        
        self.current_step += 1
        terminated = self.current_step >= self.episode_length
        truncated = False
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """Get observation."""
        obs = np.concatenate([
            self.route_status,
            self.order_priorities,
            self.weather / np.array([50.0, 100.0, 50.0]),  # Normalize
            self.route_distances / 500.0  # Normalize
        ]).astype(np.float32)
        return obs
    
    def _get_info(self) -> Dict:
        """Get info."""
        return {
            'total_delivery_time': self.total_delivery_time,
            'late_deliveries': self.late_deliveries,
            'total_cost': self.total_cost,
            'avg_delivery_time': self.total_delivery_time / max(self.current_step, 1)
        }

