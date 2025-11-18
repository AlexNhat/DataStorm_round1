"""
PPO (Proximal Policy Optimization) Policy.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    STABLE_BASELINES3_AVAILABLE = True
except ImportError:
    STABLE_BASELINES3_AVAILABLE = False
    print("Warning: stable-baselines3 not installed. Install with: pip install stable-baselines3")


class PPOPolicy:
    """
    PPO Policy cho supply chain optimization.
    """
    
    def __init__(
        self,
        env,
        learning_rate: float = 3e-4,
        n_steps: int = 2048,
        batch_size: int = 64,
        n_epochs: int = 10,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_range: float = 0.2,
        ent_coef: float = 0.01,
        vf_coef: float = 0.5
    ):
        """
        Args:
            env: Gymnasium environment
            learning_rate: Learning rate
            n_steps: Steps per update
            batch_size: Batch size
            n_epochs: Epochs per update
            gamma: Discount factor
            gae_lambda: GAE lambda
            clip_range: PPO clip range
            ent_coef: Entropy coefficient
            vf_coef: Value function coefficient
        """
        if not STABLE_BASELINES3_AVAILABLE:
            raise ImportError("stable-baselines3 required. Install with: pip install stable-baselines3")
        
        self.env = env
        self.model = PPO(
            'MlpPolicy',
            env,
            learning_rate=learning_rate,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            gae_lambda=gae_lambda,
            clip_range=clip_range,
            ent_coef=ent_coef,
            vf_coef=vf_coef,
            verbose=1
        )
    
    def train(self, total_timesteps: int = 100000, log_interval: int = 10):
        """Train policy."""
        self.model.learn(total_timesteps=total_timesteps, log_interval=log_interval)
    
    def predict(self, observation: np.ndarray, deterministic: bool = True) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Predict action."""
        return self.model.predict(observation, deterministic=deterministic)
    
    def save(self, path: str):
        """Save policy."""
        self.model.save(path)
    
    def load(self, path: str):
        """Load policy."""
        self.model = PPO.load(path, env=self.env)
    
    def evaluate(self, n_episodes: int = 10) -> Dict[str, float]:
        """Evaluate policy."""
        from stable_baselines3.common.evaluation import evaluate_policy
        
        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.env,
            n_eval_episodes=n_episodes,
            deterministic=True
        )
        
        return {
            'mean_reward': float(mean_reward),
            'std_reward': float(std_reward)
        }

