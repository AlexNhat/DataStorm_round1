"""
Online Anomaly Detection: Phát hiện anomalies trong streaming data.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from river import anomaly
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False
    print("Warning: River library not installed. Install with: pip install river")


class OnlineIsolationForest:
    """
    Online Isolation Forest cho anomaly detection.
    """
    
    def __init__(self, n_trees: int = 10, window_size: int = 1000):
        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")
        
        self.model = anomaly.IsolationForest(n_trees=n_trees, window_size=window_size)
        self.is_fitted = False
    
    def partial_fit(self, X: np.ndarray):
        """Update model với batch mới."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            self.model.learn_one(x_dict)
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies.
        
        Returns:
            -1 = anomaly, 1 = normal
        """
        if not self.is_fitted:
            return np.ones(len(X))
        
        predictions = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            pred = self.model.score_one(x_dict)
            # Score < 0.5 = anomaly
            predictions.append(-1 if pred < 0.5 else 1)
        
        return np.array(predictions)
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """Anomaly scores (0-1, càng thấp càng bất thường)."""
        if not self.is_fitted:
            return np.ones(len(X)) * 0.5
        
        scores = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            score = self.model.score_one(x_dict)
            scores.append(score if score is not None else 0.5)
        
        return np.array(scores)


class OnlineOneClassSVM:
    """
    Online One-Class SVM (approximate với River).
    """
    
    def __init__(self, nu: float = 0.1):
        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")
        
        # River không có One-Class SVM, dùng HalfSpaceTrees thay thế
        self.model = anomaly.HalfSpaceTrees(n_trees=10, height=8, window_size=250, seed=42)
        self.nu = nu
        self.is_fitted = False
    
    def partial_fit(self, X: np.ndarray):
        """Update model với batch mới."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            self.model.learn_one(x_dict)
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies.
        
        Returns:
            -1 = anomaly, 1 = normal
        """
        if not self.is_fitted:
            return np.ones(len(X))
        
        predictions = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            score = self.model.score_one(x_dict)
            # Score < threshold = anomaly
            threshold = 0.5 - self.nu
            predictions.append(-1 if score < threshold else 1)
        
        return np.array(predictions)
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """Anomaly scores."""
        if not self.is_fitted:
            return np.ones(len(X)) * 0.5
        
        scores = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            score = self.model.score_one(x_dict)
            scores.append(score if score is not None else 0.5)
        
        return np.array(scores)

