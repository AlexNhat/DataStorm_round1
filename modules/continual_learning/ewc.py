"""
Elastic Weight Consolidation (EWC): Tránh catastrophic forgetting.
"""

import numpy as np
from typing import Dict, List, Optional, Any
import torch
import torch.nn as nn


class ElasticWeightConsolidation:
    """
    Elastic Weight Consolidation: Penalize thay đổi weights quan trọng.
    
    Khi học task mới, thêm penalty cho việc thay đổi weights quan trọng từ task cũ.
    """
    
    def __init__(self, lambda_ewc: float = 0.4):
        """
        Args:
            lambda_ewc: Weight của EWC penalty
        """
        self.lambda_ewc = lambda_ewc
        self.fisher_information = {}  # Task -> Fisher information matrix
        self.optimal_params = {}  # Task -> Optimal parameters
    
    def compute_fisher_information(
        self,
        model: nn.Module,
        X: np.ndarray,
        y: np.ndarray,
        task_name: str
    ):
        """
        Tính Fisher Information Matrix cho task.
        
        Fisher Information đo độ quan trọng của từng parameter.
        """
        model.eval()
        fisher = {}
        
        # Initialize
        for name, param in model.named_parameters():
            fisher[name] = torch.zeros_like(param.data)
        
        # Compute gradients for each sample
        for i in range(len(X)):
            x = torch.FloatTensor(X[i:i+1])
            y_true = torch.LongTensor([y[i]]) if isinstance(y[i], (int, np.integer)) else torch.FloatTensor([y[i]])
            
            model.zero_grad()
            output = model(x)
            loss = nn.functional.cross_entropy(output, y_true) if len(output.shape) > 1 else nn.functional.mse_loss(output, y_true)
            loss.backward()
            
            # Accumulate squared gradients (Fisher Information)
            for name, param in model.named_parameters():
                if param.grad is not None:
                    fisher[name] += param.grad.data ** 2
        
        # Average
        for name in fisher:
            fisher[name] /= len(X)
        
        self.fisher_information[task_name] = fisher
        
        # Save optimal parameters
        optimal = {}
        for name, param in model.named_parameters():
            optimal[name] = param.data.clone()
        self.optimal_params[task_name] = optimal
    
    def compute_ewc_loss(self, model: nn.Module, task_name: str) -> torch.Tensor:
        """
        Tính EWC penalty loss.
        
        Loss = sum over tasks: lambda * Fisher * (theta - theta*)^2
        """
        if task_name not in self.fisher_information:
            return torch.tensor(0.0)
        
        fisher = self.fisher_information[task_name]
        optimal = self.optimal_params[task_name]
        
        ewc_loss = torch.tensor(0.0)
        
        for name, param in model.named_parameters():
            if name in fisher and name in optimal:
                ewc_loss += (fisher[name] * (param - optimal[name]) ** 2).sum()
        
        return self.lambda_ewc * ewc_loss
    
    def get_total_ewc_loss(self, model: nn.Module) -> torch.Tensor:
        """Tính tổng EWC loss cho tất cả tasks."""
        total_loss = torch.tensor(0.0)
        
        for task_name in self.fisher_information.keys():
            total_loss += self.compute_ewc_loss(model, task_name)
        
        return total_loss

