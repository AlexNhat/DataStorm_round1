"""
Model Drift Detector: Phát hiện data drift và concept drift.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from collections import deque
import warnings
warnings.filterwarnings('ignore')


class ModelDriftDetector:
    """
    Phát hiện drift trong dữ liệu và predictions.
    
    Methods:
    - Statistical tests (KS test, PSI)
    - Distribution comparison
    - Concept drift detection
    """
    
    def __init__(
        self,
        model_name: str,
        threshold: float = 0.1,
        window_size: int = 1000,
        reference_window_size: int = 5000
    ):
        """
        Args:
            model_name: Tên model
            threshold: Ngưỡng drift (0.1 = 10%)
            window_size: Kích thước window để so sánh
            reference_window_size: Kích thước reference window
        """
        self.model_name = model_name
        self.threshold = threshold
        self.window_size = window_size
        self.reference_window_size = reference_window_size
        
        # Buffers
        self.reference_buffer = deque(maxlen=reference_window_size)
        self.current_buffer = deque(maxlen=window_size)
        
        # History
        self.drift_history = []
        self.latest_drift_score = 0.0
    
    def detect_drift(self, new_data: np.ndarray) -> float:
        """
        Phát hiện drift trong data mới.
        
        Args:
            new_data: Array mới (1D hoặc 2D)
            
        Returns:
            Drift score (0-1, càng cao càng drift nhiều)
        """
        if len(new_data.shape) > 1:
            new_data = new_data.flatten()
        
        # Thêm vào current buffer
        self.current_buffer.extend(new_data.tolist())
        
        if len(self.reference_buffer) < 100:
            # Chưa đủ reference data, lưu làm reference
            self.reference_buffer.extend(new_data.tolist())
            return 0.0
        
        if len(self.current_buffer) < 50:
            # Chưa đủ current data
            return 0.0
        
        # So sánh distribution
        reference = np.array(list(self.reference_buffer))
        current = np.array(list(self.current_buffer))
        
        # Tính drift score bằng nhiều methods
        drift_scores = []
        
        # 1. Kolmogorov-Smirnov test
        ks_score = self._ks_test(reference, current)
        drift_scores.append(ks_score)
        
        # 2. Population Stability Index (PSI)
        psi_score = self._calculate_psi(reference, current)
        drift_scores.append(psi_score)
        
        # 3. Mean shift
        mean_shift = abs(np.mean(current) - np.mean(reference)) / (np.std(reference) + 1e-10)
        drift_scores.append(min(mean_shift, 1.0))
        
        # 4. Variance shift
        var_shift = abs(np.var(current) - np.var(reference)) / (np.var(reference) + 1e-10)
        drift_scores.append(min(var_shift, 1.0))
        
        # Lấy max (worst case)
        drift_score = max(drift_scores)
        self.latest_drift_score = drift_score
        
        # Ghi log
        self.drift_history.append({
            'drift_score': float(drift_score),
            'ks_score': float(ks_score),
            'psi_score': float(psi_score),
            'mean_shift': float(mean_shift),
            'var_shift': float(var_shift)
        })
        
        return drift_score
    
    def _ks_test(self, reference: np.ndarray, current: np.ndarray) -> float:
        """Kolmogorov-Smirnov test."""
        try:
            from scipy import stats
            statistic, p_value = stats.ks_2samp(reference, current)
            # Convert p-value to drift score (lower p-value = higher drift)
            return 1.0 - min(p_value, 1.0)
        except ImportError:
            # Fallback: Simple distribution comparison
            return self._simple_distribution_diff(reference, current)
    
    def _calculate_psi(self, reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Population Stability Index (PSI)."""
        try:
            # Tạo bins
            min_val = min(np.min(reference), np.min(current))
            max_val = max(np.max(reference), np.max(current))
            bin_edges = np.linspace(min_val, max_val, bins + 1)
            
            # Tính distribution
            ref_hist, _ = np.histogram(reference, bins=bin_edges)
            curr_hist, _ = np.histogram(current, bins=bin_edges)
            
            # Normalize
            ref_hist = ref_hist / (len(reference) + 1e-10)
            curr_hist = curr_hist / (len(current) + 1e-10)
            
            # Tính PSI
            psi = 0.0
            for i in range(bins):
                if ref_hist[i] > 0:
                    psi += (curr_hist[i] - ref_hist[i]) * np.log((curr_hist[i] + 1e-10) / ref_hist[i])
            
            # Normalize PSI (0-1)
            return min(psi / 2.0, 1.0)  # PSI > 0.25 is significant
        except Exception:
            return 0.0
    
    def _simple_distribution_diff(self, reference: np.ndarray, current: np.ndarray) -> float:
        """Simple distribution difference (fallback)."""
        # Tính percentiles
        ref_percentiles = np.percentile(reference, [10, 25, 50, 75, 90])
        curr_percentiles = np.percentile(current, [10, 25, 50, 75, 90])
        
        # So sánh
        diff = np.abs(ref_percentiles - curr_percentiles) / (np.abs(ref_percentiles) + 1e-10)
        return float(np.mean(diff))
    
    def update_reference(self, new_reference: np.ndarray):
        """Cập nhật reference buffer (sau khi retrain)."""
        if len(new_reference.shape) > 1:
            new_reference = new_reference.flatten()
        
        self.reference_buffer.clear()
        self.reference_buffer.extend(new_reference.tolist())
    
    def get_latest_drift(self) -> float:
        """Lấy drift score mới nhất."""
        return self.latest_drift_score
    
    def get_drift_history(self) -> List[Dict]:
        """Lấy lịch sử drift."""
        return self.drift_history[-100:]  # Last 100 records

