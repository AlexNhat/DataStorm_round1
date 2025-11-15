"""
Streaming Clustering: K-means và DBSCAN cho streaming data.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from river import cluster
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False
    print("Warning: River library not installed. Install with: pip install river")


class StreamingKMeans:
    """
    Streaming K-Means clustering.
    """
    
    def __init__(self, n_clusters: int = 5, halflife: float = 0.5):
        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")
        
        self.model = cluster.KMeans(n_clusters=n_clusters, halflife=halflife)
        self.n_clusters = n_clusters
        self.is_fitted = False
    
    def partial_fit(self, X: np.ndarray):
        """Update clusters với batch mới."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            self.model.learn_one(x_dict)
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels."""
        if not self.is_fitted:
            return np.zeros(len(X), dtype=int)
        
        predictions = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            pred = self.model.predict_one(x_dict)
            predictions.append(pred if pred is not None else 0)
        
        return np.array(predictions)
    
    def get_centers(self) -> np.ndarray:
        """Lấy cluster centers."""
        # River KMeans không có centers trực tiếp
        # Trả về dummy
        return np.zeros((self.n_clusters, 10))  # Dummy


class StreamingDBSCAN:
    """
    Streaming DBSCAN clustering (approximate).
    """
    
    def __init__(self, eps: float = 0.5, min_samples: int = 5):
        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")
        
        # River không có DBSCAN streaming, dùng DenStream thay thế
        self.model = cluster.DenStream(decay_factor=0.01, beta=0.5, mu=2.0, eps=eps)
        self.eps = eps
        self.min_samples = min_samples
        self.is_fitted = False
    
    def partial_fit(self, X: np.ndarray):
        """Update clusters với batch mới."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            self.model.learn_one(x_dict)
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels (-1 = noise)."""
        if not self.is_fitted:
            return np.zeros(len(X), dtype=int)
        
        predictions = []
        for i in range(len(X)):
            x_dict = {f'feature_{j}': float(X[i, j]) for j in range(X.shape[1])}
            pred = self.model.predict_one(x_dict)
            predictions.append(pred if pred is not None else -1)
        
        return np.array(predictions)

