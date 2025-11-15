"""
Performance Monitor: Theo dõi performance của model theo thời gian.
"""

import numpy as np
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class PerformanceMonitor:
    """
    Theo dõi performance của model (accuracy, F1, AUC, RMSE, etc.).
    
    Phát hiện performance degradation và trigger retrain nếu cần.
    """
    
    def __init__(
        self,
        model_name: str,
        threshold: float = 0.05,
        window_size: int = 1000,
        baseline_performance: Optional[Dict] = None
    ):
        """
        Args:
            model_name: Tên model
            threshold: Ngưỡng degradation để trigger retrain (0.05 = 5%)
            window_size: Kích thước window để tính performance
            baseline_performance: Performance baseline (sau khi train)
        """
        self.model_name = model_name
        self.threshold = threshold
        self.window_size = window_size
        self.baseline_performance = baseline_performance or {}
        
        # Buffers
        self.predictions = deque(maxlen=window_size)
        self.actuals = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        
        # History
        self.performance_history = []
        self.latest_performance = {}
    
    def evaluate(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
        task_type: str = 'auto'
    ) -> Dict:
        """
        Đánh giá performance.
        
        Args:
            predictions: Predictions
            actuals: Actual values
            task_type: 'classification' hoặc 'regression' hoặc 'auto'
            
        Returns:
            Dict với các metrics
        """
        if len(predictions) != len(actuals):
            raise ValueError("Predictions and actuals must have same length")
        
        # Lưu vào buffer
        self.predictions.extend(predictions.tolist())
        self.actuals.extend(actuals.tolist())
        self.timestamps.extend([datetime.now().isoformat()] * len(predictions))
        
        # Xác định task type
        if task_type == 'auto':
            # Kiểm tra xem là classification hay regression
            unique_actuals = np.unique(actuals)
            if len(unique_actuals) <= 10 and all(a in [0, 1] for a in unique_actuals):
                task_type = 'classification'
            else:
                task_type = 'regression'
        
        # Tính metrics
        if task_type == 'classification':
            metrics = self._calculate_classification_metrics(predictions, actuals)
        else:
            metrics = self._calculate_regression_metrics(predictions, actuals)
        
        # So sánh với baseline
        if self.baseline_performance:
            degradation = self._calculate_degradation(metrics, self.baseline_performance)
            metrics['degradation'] = degradation
            metrics['needs_retrain'] = degradation > self.threshold
        
        # Lưu
        self.latest_performance = metrics
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        })
        
        return metrics
    
    def _calculate_classification_metrics(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray
    ) -> Dict:
        """Tính classification metrics."""
        # Accuracy
        accuracy = np.mean(predictions == actuals)
        
        # Precision, Recall, F1
        try:
            from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
            
            # Binary classification
            if len(np.unique(actuals)) == 2:
                precision = precision_score(actuals, predictions, zero_division=0)
                recall = recall_score(actuals, predictions, zero_division=0)
                f1 = f1_score(actuals, predictions, zero_division=0)
                
                # AUC (cần probabilities, giả sử predictions là probabilities)
                try:
                    auc = roc_auc_score(actuals, predictions)
                except:
                    auc = 0.5
            else:
                # Multi-class
                precision = precision_score(actuals, predictions, average='weighted', zero_division=0)
                recall = recall_score(actuals, predictions, average='weighted', zero_division=0)
                f1 = f1_score(actuals, predictions, average='weighted', zero_division=0)
                auc = 0.0  # Multi-class AUC phức tạp hơn
        except ImportError:
            # Fallback
            precision = accuracy
            recall = accuracy
            f1 = accuracy
            auc = 0.5
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'auc': float(auc),
            'task_type': 'classification'
        }
    
    def _calculate_regression_metrics(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray
    ) -> Dict:
        """Tính regression metrics."""
        # MAE
        mae = np.mean(np.abs(predictions - actuals))
        
        # RMSE
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        
        # MAPE
        mape = np.mean(np.abs((actuals - predictions) / (actuals + 1e-10))) * 100
        
        # R²
        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        r2 = 1 - (ss_res / (ss_tot + 1e-10))
        
        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'r2': float(r2),
            'task_type': 'regression'
        }
    
    def _calculate_degradation(
        self,
        current_metrics: Dict,
        baseline_metrics: Dict
    ) -> float:
        """Tính performance degradation so với baseline."""
        # Chọn metric chính để so sánh
        if current_metrics.get('task_type') == 'classification':
            # Dùng F1 hoặc Accuracy
            current_metric = current_metrics.get('f1', current_metrics.get('accuracy', 0.5))
            baseline_metric = baseline_metrics.get('f1', baseline_metrics.get('accuracy', 0.5))
        else:
            # Dùng R² hoặc RMSE
            if 'r2' in current_metrics:
                current_metric = current_metrics.get('r2', 0.0)
                baseline_metric = baseline_metrics.get('r2', 0.0)
                # R² càng cao càng tốt, nên degradation = (baseline - current) / baseline
                if baseline_metric > 0:
                    degradation = (baseline_metric - current_metric) / baseline_metric
                else:
                    degradation = 0.0
            else:
                # Dùng RMSE (càng thấp càng tốt)
                current_metric = current_metrics.get('rmse', 1.0)
                baseline_metric = baseline_metrics.get('rmse', 1.0)
                # Degradation = (current - baseline) / baseline
                if baseline_metric > 0:
                    degradation = (current_metric - baseline_metric) / baseline_metric
                else:
                    degradation = 0.0
            
            return max(0.0, degradation)
        
        # Classification: degradation = (baseline - current) / baseline
        if baseline_metric > 0:
            degradation = (baseline_metric - current_metric) / baseline_metric
        else:
            degradation = 0.0
        
        return max(0.0, degradation)
    
    def set_baseline(self, baseline_metrics: Dict):
        """Set baseline performance (sau khi train)."""
        self.baseline_performance = baseline_metrics
    
    def get_latest_performance(self) -> Dict:
        """Lấy performance mới nhất."""
        return self.latest_performance
    
    def get_performance_history(self) -> List[Dict]:
        """Lấy lịch sử performance."""
        return self.performance_history[-100:]  # Last 100 records

