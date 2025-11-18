"""
RiverML Incremental Models: Online learning với River library.

Models:
- Logistic Regression (incremental)
- Random Forest (incremental)
- Adaptive Random Forest
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

try:
    from river import linear_model, ensemble, tree, metrics, compose, preprocessing
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False
    print("Warning: River library not installed. Install with: pip install river")


class IncrementalLogisticRegression:
    """
    Incremental Logistic Regression sử dụng River.
    """
    
    def __init__(self, learning_rate: float = 0.01):
        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")
        
        self.model = linear_model.LogisticRegression(learning_rate=learning_rate)
        self.metric = metrics.Accuracy()
        self.is_fitted = False
    
    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """Update model với batch mới."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            self.model.learn_one(x_dict, int(y[i]))
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict."""
        if not self.is_fitted:
            return np.zeros(len(X))
        
        predictions = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            pred = self.model.predict_one(x_dict)
            predictions.append(pred if pred is not None else 0)
        
        return np.array(predictions)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_fitted:
            return np.ones((len(X), 2)) * 0.5
        
        probabilities = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            proba = self.model.predict_proba_one(x_dict)
            if proba:
                prob_1 = proba.get(1, 0.5)
            else:
                prob_1 = 0.5
            probabilities.append([1 - prob_1, prob_1])
        
        return np.array(probabilities)


class IncrementalRandomForest:
    """
    Incremental Random Forest sử dụng River.
    """
    
    def __init__(self, n_trees: int = 10, max_depth: int = 10):
        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")
        
        self.model = ensemble.RandomForestClassifier(
            n_models=n_trees,
            max_depth=max_depth
        )
        self.metric = metrics.Accuracy()
        self.is_fitted = False
    
    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """Update model với batch mới."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            self.model.learn_one(x_dict, int(y[i]))
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict."""
        if not self.is_fitted:
            return np.zeros(len(X))
        
        predictions = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            pred = self.model.predict_one(x_dict)
            predictions.append(pred if pred is not None else 0)
        
        return np.array(predictions)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_fitted:
            return np.ones((len(X), 2)) * 0.5
        
        probabilities = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            proba = self.model.predict_proba_one(x_dict)
            if proba:
                prob_1 = proba.get(1, 0.5)
            else:
                prob_1 = 0.5
            probabilities.append([1 - prob_1, prob_1])
        
        return np.array(probabilities)
    
    def feature_importances_(self) -> np.ndarray:
        """Feature importances (average across trees)."""
        # River không có feature_importances_ trực tiếp
        # Trả về dummy values
        return np.ones(10) / 10  # Dummy


class AdaptiveRandomForest:
    """
    Adaptive Random Forest: Tự động thêm/xóa trees dựa trên performance.
    """
    
    def __init__(self, n_trees: int = 10, max_depth: int = 10):
        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")
        
        self.model = ensemble.AdaptiveRandomForestClassifier(
            n_models=n_trees,
            max_depth=max_depth
        )
        self.metric = metrics.Accuracy()
        self.is_fitted = False
    
    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """Update model với batch mới."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            self.model.learn_one(x_dict, int(y[i]))
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict."""
        if not self.is_fitted:
            return np.zeros(len(X))
        
        predictions = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            pred = self.model.predict_one(x_dict)
            predictions.append(pred if pred is not None else 0)
        
        return np.array(predictions)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_fitted:
            return np.ones((len(X), 2)) * 0.5
        
        probabilities = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            proba = self.model.predict_proba_one(x_dict)
            if proba:
                prob_1 = proba.get(1, 0.5)
            else:
                prob_1 = 0.5
            probabilities.append([1 - prob_1, prob_1])
        
        return np.array(probabilities)

