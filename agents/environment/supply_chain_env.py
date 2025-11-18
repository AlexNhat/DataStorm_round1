"""
Supply Chain RL Environment: Gymnasium environment cho supply chain optimization.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

try:
    import gymnasium as gym
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    print("Warning: Gymnasium not installed. Install with: pip install gymnasium")


class SupplyChainEnv:
    """
    Supply Chain RL Environment.
    
    Observation Space:
    - Current inventory levels (per warehouse, per product)
    - Pending orders
    - Weather conditions
    - Transport status
    - Demand forecast
    
    Action Space:
    - Reorder quantities (per warehouse, per product)
    - Route selection
    - Priority assignment
    
    Reward:
    - Profit (revenue - cost)
    - Service level (on-time delivery rate)
    - Inventory holding cost
    - Stockout penalty
    """
    
    def __init__(
        self,
        n_warehouses: int = 3,
        n_products: int = 10,
        max_inventory: int = 1000,
        episode_length: int = 100
    ):
        """
        Args:
            n_warehouses: Số warehouses
            n_products: Số products
            max_inventory: Inventory tối đa
            episode_length: Độ dài episode
        """
        if not GYMNASIUM_AVAILABLE:
            raise ImportError("Gymnasium required. Install with: pip install gymnasium")
        
        self.n_warehouses = n_warehouses
        self.n_products = n_products
        self.max_inventory = max_inventory
        self.episode_length = episode_length
        
        # Observation space
        # [inventory (n_warehouses * n_products), pending_orders, weather, demand_forecast]
        obs_dim = (
            n_warehouses * n_products +  # Inventory
            n_products +  # Pending orders
            3 +  # Weather (temp, precip, wind)
            n_products  # Demand forecast
        )
        
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        # Action space
        # [reorder_quantities (n_warehouses * n_products), route_selection]
        action_dim = n_warehouses * n_products + 1  # +1 for route selection
        
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(action_dim,),
            dtype=np.float32
        )
        
        # State
        self.inventory = np.zeros((n_warehouses, n_products), dtype=np.int32)
        self.pending_orders = np.zeros(n_products, dtype=np.int32)
        self.weather = np.array([20.0, 0.0, 10.0])  # temp, precip, wind
        self.demand_forecast = np.zeros(n_products, dtype=np.float32)
        self.current_step = 0
        
        # Metrics
        self.total_revenue = 0.0
        self.total_cost = 0.0
        self.delivered_orders = 0
        self.late_orders = 0
        self.stockouts = 0
    
    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict]:
        """Reset environment."""
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize inventory (random)
        self.inventory = np.random.randint(0, self.max_inventory // 2, (self.n_warehouses, self.n_products))
        self.pending_orders = np.zeros(self.n_products, dtype=np.int32)
        self.weather = np.array([
            np.random.normal(20, 10),  # temp
            max(0, np.random.exponential(5)),  # precip
            max(0, np.random.exponential(10))  # wind
        ])
        self.demand_forecast = np.random.uniform(0, 100, self.n_products)
        self.current_step = 0
        
        # Reset metrics
        self.total_revenue = 0.0
        self.total_cost = 0.0
        self.delivered_orders = 0
        self.late_orders = 0
        self.stockouts = 0
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Step environment.
        
        Args:
            action: Action vector
            
        Returns:
            (observation, reward, terminated, truncated, info)
        """
        # Parse action
        reorder_actions = action[:-1].reshape(self.n_warehouses, self.n_products)
        route_selection = int(action[-1] * self.n_warehouses)  # Convert to warehouse index
        
        # Execute actions
        # 1. Reorder inventory
        reorder_quantities = (reorder_actions * self.max_inventory).astype(int)
        for w in range(self.n_warehouses):
            for p in range(self.n_products):
                current = self.inventory[w, p]
                reorder = reorder_quantities[w, p]
                self.inventory[w, p] = min(current + reorder, self.max_inventory)
                # Cost: ordering cost
                self.total_cost += reorder * 0.5  # $0.5 per unit
        
        # 2. Process orders
        self._process_orders(route_selection)
        
        # 3. Generate new demand
        new_demand = self._generate_demand()
        self.pending_orders += new_demand
        
        # 4. Update weather (random walk)
        self.weather += np.random.normal(0, 1, 3)
        self.weather[1] = max(0, self.weather[1])  # Precip >= 0
        self.weather[2] = max(0, self.weather[2])  # Wind >= 0
        
        # 5. Update demand forecast
        self.demand_forecast = 0.9 * self.demand_forecast + 0.1 * new_demand
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Update step
        self.current_step += 1
        terminated = self.current_step >= self.episode_length
        truncated = False
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward, terminated, truncated, info
    
    def _process_orders(self, selected_warehouse: int):
        """Process pending orders."""
        for p in range(self.n_products):
            if self.pending_orders[p] > 0:
                # Try to fulfill from selected warehouse
                if self.inventory[selected_warehouse, p] >= self.pending_orders[p]:
                    # Fulfill order
                    self.inventory[selected_warehouse, p] -= self.pending_orders[p]
                    self.delivered_orders += 1
                    self.total_revenue += self.pending_orders[p] * 10.0  # $10 per unit
                    self.pending_orders[p] = 0
                else:
                    # Stockout
                    self.stockouts += 1
                    # Partial fulfillment
                    fulfilled = self.inventory[selected_warehouse, p]
                    self.inventory[selected_warehouse, p] = 0
                    self.pending_orders[p] -= fulfilled
                    if fulfilled > 0:
                        self.delivered_orders += 1
                        self.total_revenue += fulfilled * 10.0
    
    def _generate_demand(self) -> np.ndarray:
        """Generate new demand."""
        # Base demand + noise
        base_demand = self.demand_forecast * 0.1  # 10% of forecast
        noise = np.random.poisson(5, self.n_products)
        return (base_demand + noise).astype(int)
    
    def _calculate_reward(self) -> float:
        """Calculate reward."""
        # Reward = profit - penalties
        profit = self.total_revenue - self.total_cost
        
        # Inventory holding cost
        holding_cost = np.sum(self.inventory) * 0.1
        
        # Stockout penalty
        stockout_penalty = self.stockouts * 50.0
        
        # Late delivery penalty (if any)
        late_penalty = self.late_orders * 20.0
        
        reward = profit - holding_cost - stockout_penalty - late_penalty
        
        # Normalize
        return float(reward / 1000.0)
    
    def _get_observation(self) -> np.ndarray:
        """Get current observation."""
        # Flatten inventory
        inv_flat = self.inventory.flatten() / self.max_inventory  # Normalize
        
        # Normalize other features
        pending_norm = self.pending_orders / 100.0  # Assume max 100
        weather_norm = np.array([
            self.weather[0] / 50.0,  # temp / 50
            self.weather[1] / 100.0,  # precip / 100
            self.weather[2] / 50.0  # wind / 50
        ])
        forecast_norm = self.demand_forecast / 100.0
        
        obs = np.concatenate([
            inv_flat,
            pending_norm,
            weather_norm,
            forecast_norm
        ]).astype(np.float32)
        
        return obs
    
    def _get_info(self) -> Dict:
        """Get info dict."""
        return {
            'total_revenue': self.total_revenue,
            'total_cost': self.total_cost,
            'profit': self.total_revenue - self.total_cost,
            'delivered_orders': self.delivered_orders,
            'stockouts': self.stockouts,
            'inventory_level': np.sum(self.inventory)
        }
    
    def render(self, mode: str = 'human'):
        """Render environment."""
        if mode == 'human':
            print(f"Step: {self.current_step}")
            print(f"Inventory: {np.sum(self.inventory)}")
            print(f"Pending Orders: {np.sum(self.pending_orders)}")
            print(f"Revenue: {self.total_revenue:.2f}, Cost: {self.total_cost:.2f}")
            print(f"Profit: {self.total_revenue - self.total_cost:.2f}")

