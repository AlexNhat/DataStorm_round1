"""
Train Multi-Agent RL Policies.
"""

import os
import sys
import argparse
import numpy as np
from typing import Dict, List, Optional, Any

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.environment.supply_chain_env import SupplyChainEnv
from agents.environment.inventory_env import InventoryEnv
from agents.environment.transport_env import TransportEnv
from rl.policies.ppo import PPOPolicy

try:
    from stable_baselines3 import PPO, A2C, SAC
    from stable_baselines3.common.env_util import make_vec_env
    STABLE_BASELINES3_AVAILABLE = True
except ImportError:
    STABLE_BASELINES3_AVAILABLE = False
    print("Warning: stable-baselines3 not installed")


def train_inventory_policy(
    total_timesteps: int = 100000,
    save_path: str = "rl/policies/saved/inventory_ppo"
):
    """Train inventory optimization policy."""
    print("Training Inventory Optimization Policy...")
    
    env = InventoryEnv(n_products=10, max_inventory=1000, episode_length=100)
    
    if STABLE_BASELINES3_AVAILABLE:
        model = PPO('MlpPolicy', env, verbose=1)
        model.learn(total_timesteps=total_timesteps)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        model.save(save_path)
        print(f"Policy saved to {save_path}")
    else:
        print("stable-baselines3 not available. Skipping training.")


def train_transport_policy(
    total_timesteps: int = 100000,
    save_path: str = "rl/policies/saved/transport_ppo"
):
    """Train transport routing policy."""
    print("Training Transport Routing Policy...")
    
    env = TransportEnv(n_routes=5, n_orders=20, episode_length=100)
    
    if STABLE_BASELINES3_AVAILABLE:
        model = PPO('MlpPolicy', env, verbose=1)
        model.learn(total_timesteps=total_timesteps)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        model.save(save_path)
        print(f"Policy saved to {save_path}")
    else:
        print("stable-baselines3 not available. Skipping training.")


def train_supply_chain_policy(
    total_timesteps: int = 100000,
    save_path: str = "rl/policies/saved/supply_chain_ppo"
):
    """Train supply chain policy."""
    print("Training Supply Chain Policy...")
    
    env = SupplyChainEnv(n_warehouses=3, n_products=10, max_inventory=1000, episode_length=100)
    
    if STABLE_BASELINES3_AVAILABLE:
        model = PPO('MlpPolicy', env, verbose=1)
        model.learn(total_timesteps=total_timesteps)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        model.save(save_path)
        print(f"Policy saved to {save_path}")
    else:
        print("stable-baselines3 not available. Skipping training.")


def main():
    parser = argparse.ArgumentParser(description='Train Multi-Agent RL Policies')
    parser.add_argument('--algorithm', type=str, default='ppo', choices=['ppo', 'a2c', 'sac'])
    parser.add_argument('--agents', type=str, nargs='+', default=['inventory', 'transport', 'supply_chain'])
    parser.add_argument('--episodes', type=int, default=10000)
    parser.add_argument('--timesteps', type=int, default=100000)
    
    args = parser.parse_args()
    
    print(f"Training {args.algorithm} policies for agents: {args.agents}")
    print(f"Total timesteps: {args.timesteps}")
    
    if 'inventory' in args.agents:
        train_inventory_policy(total_timesteps=args.timesteps)
    
    if 'transport' in args.agents:
        train_transport_policy(total_timesteps=args.timesteps)
    
    if 'supply_chain' in args.agents:
        train_supply_chain_policy(total_timesteps=args.timesteps)
    
    print("Training completed!")


if __name__ == '__main__':
    main()

