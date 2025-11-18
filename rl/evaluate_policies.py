"""
Evaluate RL Policies.
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

try:
    from stable_baselines3 import PPO, A2C, SAC
    from stable_baselines3.common.evaluation import evaluate_policy
    STABLE_BASELINES3_AVAILABLE = True
except ImportError:
    STABLE_BASELINES3_AVAILABLE = False
    print("Warning: stable-baselines3 not installed")


def evaluate_policy_file(
    policy_path: str,
    env_type: str = 'inventory',
    n_episodes: int = 10
) -> Dict[str, float]:
    """
    Evaluate a saved policy.
    
    Args:
        policy_path: Path to saved policy
        env_type: 'inventory', 'transport', or 'supply_chain'
        n_episodes: Number of evaluation episodes
        
    Returns:
        Evaluation metrics
    """
    if not STABLE_BASELINES3_AVAILABLE:
        print("stable-baselines3 not available. Cannot evaluate.")
        return {}
    
    # Create environment
    if env_type == 'inventory':
        env = InventoryEnv(n_products=10, max_inventory=1000, episode_length=100)
    elif env_type == 'transport':
        env = TransportEnv(n_routes=5, n_orders=20, episode_length=100)
    elif env_type == 'supply_chain':
        env = SupplyChainEnv(n_warehouses=3, n_products=10, max_inventory=1000, episode_length=100)
    else:
        raise ValueError(f"Unknown env_type: {env_type}")
    
    # Load policy
    try:
        model = PPO.load(policy_path, env=env)
    except:
        try:
            model = A2C.load(policy_path, env=env)
        except:
            model = SAC.load(policy_path, env=env)
    
    # Evaluate
    mean_reward, std_reward = evaluate_policy(
        model,
        env,
        n_eval_episodes=n_episodes,
        deterministic=True
    )
    
    return {
        'mean_reward': float(mean_reward),
        'std_reward': float(std_reward),
        'n_episodes': n_episodes
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate RL Policies')
    parser.add_argument('--policy', type=str, required=True, help='Path to policy file')
    parser.add_argument('--env', type=str, default='inventory', choices=['inventory', 'transport', 'supply_chain'])
    parser.add_argument('--episodes', type=int, default=10)
    parser.add_argument('--scenarios', type=str, nargs='+', default=['all'])
    
    args = parser.parse_args()
    
    print(f"Evaluating policy: {args.policy}")
    print(f"Environment: {args.env}")
    print(f"Episodes: {args.episodes}")
    
    results = evaluate_policy_file(
        policy_path=args.policy,
        env_type=args.env,
        n_episodes=args.episodes
    )
    
    print("\nEvaluation Results:")
    print(f"Mean Reward: {results.get('mean_reward', 0):.2f}")
    print(f"Std Reward: {results.get('std_reward', 0):.2f}")


if __name__ == '__main__':
    main()

