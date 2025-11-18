"""
Inventory Optimization RL Environment.
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


class InventoryEnv:
    """
    Inventory Optimization Environment.
    
    Agent quyết định:
    - Reorder point
    - Order quantity
    - Safety stock level
    """
    
    def __init__(
        self,
        n_products: int = 10,
        max_inventory: int = 1000,
        episode_length: int = 100
    ):
        if not GYMNASIUM_AVAILABLE:
            raise ImportError("Gymnasium required. Install with: pip install gymnasium")
        
        self.n_products = n_products
        self.max_inventory = max_inventory
        self.episode_length = episode_length
        
        # Observation: [current_inventory, demand_rate, lead_time, cost]
        obs_dim = n_products * 4
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        # Action: [reorder_point, order_quantity] per product
        action_dim = n_products * 2
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(action_dim,),
            dtype=np.float32
        )
        
        # State
        self.inventory = np.zeros(n_products, dtype=np.int32)
        self.demand_rate = np.random.uniform(10, 50, n_products)
        self.lead_time = np.random.uniform(1, 7, n_products)
        self.unit_cost = np.random.uniform(5, 20, n_products)
        self.current_step = 0
        
        # Metrics
        self.total_cost = 0.0
        self.stockouts = 0
        self.orders_placed = 0
    
    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict]:
        """Reset environment."""
        if seed is not None:
            np.random.seed(seed)
        
        self.inventory = np.random.randint(0, self.max_inventory // 2, self.n_products)
        self.demand_rate = np.random.uniform(10, 50, self.n_products)
        self.lead_time = np.random.uniform(1, 7, self.n_products)
        self.unit_cost = np.random.uniform(5, 20, self.n_products)
        self.current_step = 0
        
        self.total_cost = 0.0
        self.stockouts = 0
        self.orders_placed = 0
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Step environment."""
        # Parse action
        action_reshaped = action.reshape(self.n_products, 2)
        reorder_points = (action_reshaped[:, 0] * self.max_inventory).astype(int)
        order_quantities = (action_reshaped[:, 1] * self.max_inventory).astype(int)
        
        # Check if need to reorder
        for p in range(self.n_products):
            if self.inventory[p] <= reorder_points[p]:
                # Place order
                order_qty = order_quantities[p]
                self.inventory[p] += order_qty
                self.orders_placed += 1
                # Ordering cost
                self.total_cost += 100.0 + order_qty * self.unit_cost[p]  # Fixed + variable
        
        # Generate demand
        demand = np.random.poisson(self.demand_rate)
        
        # Fulfill demand
        for p in range(self.n_products):
            if self.inventory[p] >= demand[p]:
                self.inventory[p] -= demand[p]
            else:
                # Stockout
                self.stockouts += 1
                self.inventory[p] = 0
        
        # Holding cost
        holding_cost = np.sum(self.inventory) * 0.1
        self.total_cost += holding_cost
        
        # Calculate reward
        reward = -self.total_cost / 1000.0  # Negative cost (minimize)
        
        self.current_step += 1
        terminated = self.current_step >= self.episode_length
        truncated = False
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """Get observation."""
        obs = np.concatenate([
            self.inventory / self.max_inventory,
            self.demand_rate / 100.0,
            self.lead_time / 10.0,
            self.unit_cost / 50.0
        ]).astype(np.float32)
        return obs
    
    def _get_info(self) -> Dict:
        """Get info."""
        return {
            'total_cost': self.total_cost,
            'stockouts': self.stockouts,
            'orders_placed': self.orders_placed,
            'avg_inventory': np.mean(self.inventory)
        }

