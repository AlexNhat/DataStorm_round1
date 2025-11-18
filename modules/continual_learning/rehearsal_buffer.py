"""
Rehearsal Buffer: Lưu samples quan trọng để retrain và tránh catastrophic forgetting.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
import random


class RehearsalBuffer:
    """
    Rehearsal Buffer: Lưu samples quan trọng để retrain.
    
    Kỹ thuật: Khi học task mới, trộn với samples từ task cũ để model không quên.
    """
    
    def __init__(self, max_size: int = 1000, strategy: str = 'random'):
        """
        Args:
            max_size: Kích thước tối đa của buffer
            strategy: 'random', 'fifo', 'importance' (chọn samples quan trọng)
        """
        self.max_size = max_size
        self.strategy = strategy
        self.buffer = deque(maxlen=max_size)
        self.importance_scores = {}  # Sample ID -> importance score
    
    def add_samples(self, X: np.ndarray, y: np.ndarray, sample_ids: Optional[List[str]] = None):
        """
        Thêm samples vào buffer.
        
        Args:
            X: Features
            y: Labels
            sample_ids: Optional sample IDs
        """
        if sample_ids is None:
            sample_ids = [f'sample_{i}' for i in range(len(X))]
        
        for i, (x, y_val, sid) in enumerate(zip(X, y, sample_ids)):
            sample = {
                'id': sid,
                'X': x,
                'y': y_val,
                'importance': self._calculate_importance(x, y_val)
            }
            
            if len(self.buffer) >= self.max_size:
                # Remove least important if using importance strategy
                if self.strategy == 'importance':
                    self._remove_least_important()
                # Otherwise, FIFO (deque tự động xử lý)
            
            self.buffer.append(sample)
            self.importance_scores[sid] = sample['importance']
    
    def get_samples(self, n: int, include_new: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Lấy samples từ buffer (trộn với new samples nếu có).
        
        Args:
            n: Số samples cần lấy
            include_new: (X_new, y_new) nếu muốn trộn với new data
            
        Returns:
            (X_combined, y_combined)
        """
        if self.strategy == 'random':
            selected = random.sample(list(self.buffer), min(n, len(self.buffer)))
        elif self.strategy == 'importance':
            # Chọn samples có importance cao nhất
            sorted_samples = sorted(self.buffer, key=lambda s: s['importance'], reverse=True)
            selected = sorted_samples[:min(n, len(sorted_samples))]
        else:  # FIFO
            selected = list(self.buffer)[-min(n, len(self.buffer)):]
        
        X_buffer = np.array([s['X'] for s in selected])
        y_buffer = np.array([s['y'] for s in selected])
        
        if include_new:
            X_new, y_new = include_new
            X_combined = np.vstack([X_buffer, X_new])
            y_combined = np.hstack([y_buffer, y_new])
            return X_combined, y_combined
        
        return X_buffer, y_buffer
    
    def _calculate_importance(self, x: np.ndarray, y: Any) -> float:
        """
        Tính importance của sample.
        
        Có thể dựa trên:
        - Loss (samples khó predict = quan trọng)
        - Uncertainty
        - Distance từ decision boundary
        """
        # Simple heuristic: variance của features (samples đa dạng = quan trọng)
        if isinstance(x, np.ndarray):
            return float(np.var(x))
        return 1.0
    
    def _remove_least_important(self):
        """Xóa sample có importance thấp nhất."""
        if not self.buffer:
            return
        
        min_importance = min(s['importance'] for s in self.buffer)
        for i, sample in enumerate(self.buffer):
            if sample['importance'] == min_importance:
                del self.buffer[i]
                break
    
    def clear(self):
        """Xóa toàn bộ buffer."""
        self.buffer.clear()
        self.importance_scores.clear()
    
    def size(self) -> int:
        """Lấy kích thước buffer."""
        return len(self.buffer)

