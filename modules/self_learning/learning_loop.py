"""
Self-Learning Loop: Autonomous ML engine that learns, adapts, and optimizes over time.

Vòng lặp:
1. Quan sát dữ liệu thực → so sánh với dự đoán model
2. Phát hiện sai lệch → tự đánh giá model drift
3. Tự điều chỉnh thông số model (online learning / incremental learning)
4. Tự quyết định lúc nào cần retrain
5. Tự ghi log vào model_metadata.json
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import joblib
import warnings
warnings.filterwarnings('ignore')

from .drift_detector import ModelDriftDetector
from .performance_monitor import PerformanceMonitor


class SelfLearningLoop:
    """
    Self-Learning Loop: Tự học, tự thay đổi, tự tối ưu.
    
    Giống như "Autonomous ML Engine" của Amazon hoặc Google DeepMind.
    """
    
    def __init__(
        self,
        model_name: str,
        model_path: str,
        metadata_path: str = None,
        drift_threshold: float = 0.1,
        performance_threshold: float = 0.05,
        min_samples_for_retrain: int = 1000,
        retrain_interval_days: int = 7
    ):
        """
        Args:
            model_name: Tên model (e.g., 'logistics_delay', 'revenue_forecast', 'churn')
            model_path: Đường dẫn đến model file (.pkl)
            metadata_path: Đường dẫn đến metadata file (mặc định: models/{model_name}_metadata.json)
            drift_threshold: Ngưỡng drift để trigger retrain (0.1 = 10% drift)
            performance_threshold: Ngưỡng performance degradation để trigger retrain (0.05 = 5% giảm)
            min_samples_for_retrain: Số samples tối thiểu để retrain
            retrain_interval_days: Khoảng thời gian tối thiểu giữa các lần retrain (ngày)
        """
        self.model_name = model_name
        self.model_path = model_path
        self.metadata_path = metadata_path or os.path.join(
            os.path.dirname(model_path),
            f'{model_name}_metadata.json'
        )
        self.drift_threshold = drift_threshold
        self.performance_threshold = performance_threshold
        self.min_samples_for_retrain = min_samples_for_retrain
        self.retrain_interval_days = retrain_interval_days
        
        # Load model
        self.model = None
        self.preprocessor = None
        self.schema = None
        self._load_model()
        
        # Initialize components
        self.drift_detector = ModelDriftDetector(
            model_name=model_name,
            threshold=drift_threshold
        )
        self.performance_monitor = PerformanceMonitor(
            model_name=model_name,
            threshold=performance_threshold
        )
        
        # Load metadata
        self.metadata = self._load_metadata()
        
        # Buffer để lưu predictions và actuals
        self.prediction_buffer = []
        self.actual_buffer = []
        self.timestamp_buffer = []
    
    def _load_model(self):
        """Load model, preprocessor, và schema."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        self.model = joblib.load(self.model_path)
        
        # Load preprocessor nếu có
        preprocessor_path = self.model_path.replace('_model.pkl', '_preprocessor.pkl')
        if os.path.exists(preprocessor_path):
            self.preprocessor = joblib.load(preprocessor_path)
        
        # Load schema nếu có
        schema_path = self.model_path.replace('_model.pkl', '_feature_schema.json')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
    
    def _load_metadata(self) -> Dict:
        """Load metadata từ file."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        else:
            # Tạo metadata mới
            metadata = {
                'model_name': self.model_name,
                'created_at': datetime.now().isoformat(),
                'version': 1,
                'last_retrain': None,
                'retrain_count': 0,
                'performance_history': [],
                'drift_history': [],
                'changes': []
            }
            self._save_metadata(metadata)
            return metadata
    
    def _save_metadata(self, metadata: Dict = None):
        """Lưu metadata vào file."""
        if metadata is None:
            metadata = self.metadata
        
        os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def observe(
        self,
        X: np.ndarray,
        y_actual: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Quan sát dữ liệu mới và so sánh với dự đoán.
        
        Args:
            X: Feature vector (1D hoặc 2D)
            y_actual: Giá trị thực tế (nếu có, để so sánh)
            timestamp: Thời gian quan sát
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Predict
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        y_pred = self.model.predict(X)[0]
        y_pred_proba = None
        if hasattr(self.model, 'predict_proba'):
            y_pred_proba = self.model.predict_proba(X)[0]
        
        # Lưu vào buffer
        self.prediction_buffer.append({
            'prediction': float(y_pred),
            'probability': y_pred_proba.tolist() if y_pred_proba is not None else None
        })
        self.timestamp_buffer.append(timestamp.isoformat())
        
        if y_actual is not None:
            self.actual_buffer.append(float(y_actual))
        
        # Kiểm tra drift và performance mỗi N samples
        if len(self.prediction_buffer) >= 100:
            self._check_and_adapt()
    
    def _check_and_adapt(self):
        """Kiểm tra drift và performance, tự điều chỉnh nếu cần."""
        if len(self.actual_buffer) < 50:
            return  # Chưa đủ data để đánh giá
        
        # 1. Phát hiện drift
        recent_X = np.array([p['prediction'] for p in self.prediction_buffer[-100:]])
        drift_score = self.drift_detector.detect_drift(recent_X)
        
        # 2. Đánh giá performance
        recent_actuals = np.array(self.actual_buffer[-100:])
        recent_predictions = np.array([p['prediction'] for p in self.prediction_buffer[-100:]])
        performance_metric = self.performance_monitor.evaluate(recent_predictions, recent_actuals)
        
        # 3. Ghi log
        self.metadata['drift_history'].append({
            'timestamp': datetime.now().isoformat(),
            'drift_score': float(drift_score),
            'performance': performance_metric
        })
        
        # 4. Quyết định retrain
        should_retrain = self._should_retrain(drift_score, performance_metric)
        
        if should_retrain:
            self._trigger_retrain(drift_score, performance_metric)
        else:
            # Incremental learning nếu có thể
            if hasattr(self.model, 'partial_fit'):
                self._incremental_update()
    
    def _should_retrain(self, drift_score: float, performance_metric: Dict) -> bool:
        """Quyết định có nên retrain hay không."""
        # Điều kiện 1: Drift quá cao
        if drift_score > self.drift_threshold:
            return True
        
        # Điều kiện 2: Performance giảm quá nhiều
        if 'degradation' in performance_metric:
            if performance_metric['degradation'] > self.performance_threshold:
                return True
        
        # Điều kiện 3: Đã đủ thời gian kể từ lần retrain cuối
        if self.metadata['last_retrain']:
            last_retrain = datetime.fromisoformat(self.metadata['last_retrain'])
            days_since_retrain = (datetime.now() - last_retrain).days
            if days_since_retrain >= self.retrain_interval_days:
                return True
        
        # Điều kiện 4: Chưa retrain lần nào
        if self.metadata['retrain_count'] == 0:
            return True
        
        return False
    
    def _trigger_retrain(self, drift_score: float, performance_metric: Dict):
        """Trigger retrain process."""
        change_log = {
            'timestamp': datetime.now().isoformat(),
            'reason': 'auto_retrain',
            'drift_score': float(drift_score),
            'performance': performance_metric,
            'version_before': self.metadata['version'],
            'version_after': self.metadata['version'] + 1
        }
        
        self.metadata['changes'].append(change_log)
        self.metadata['retrain_count'] += 1
        self.metadata['version'] += 1
        self.metadata['last_retrain'] = datetime.now().isoformat()
        
        # Ghi log
        self._save_metadata()
        
        # Note: Retrain thực tế sẽ được thực hiện bởi training script
        # Ở đây chỉ log và flag
        print(f"[Self-Learning] Model {self.model_name} flagged for retrain. "
              f"Drift: {drift_score:.3f}, Performance: {performance_metric}")
    
    def _incremental_update(self):
        """Cập nhật model incrementally (nếu model hỗ trợ)."""
        if len(self.actual_buffer) < 10:
            return
        
        try:
            # Lấy data gần đây
            recent_X = np.array([p['prediction'] for p in self.prediction_buffer[-50:]])
            recent_y = np.array(self.actual_buffer[-50:])
            
            # Reshape nếu cần
            if len(recent_X.shape) == 1:
                recent_X = recent_X.reshape(-1, 1)
            
            # Partial fit
            if hasattr(self.model, 'partial_fit'):
                self.model.partial_fit(recent_X, recent_y)
                
                # Lưu model đã update
                joblib.dump(self.model, self.model_path)
                
                change_log = {
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'incremental_update',
                    'samples_used': len(recent_y)
                }
                self.metadata['changes'].append(change_log)
                self._save_metadata()
                
                print(f"[Self-Learning] Model {self.model_name} updated incrementally with {len(recent_y)} samples")
        except Exception as e:
            print(f"[Self-Learning] Incremental update failed: {e}")
    
    def get_status(self) -> Dict:
        """Lấy trạng thái hiện tại của learning loop."""
        return {
            'model_name': self.model_name,
            'version': self.metadata['version'],
            'retrain_count': self.metadata['retrain_count'],
            'last_retrain': self.metadata['last_retrain'],
            'buffer_size': len(self.prediction_buffer),
            'drift_score': self.drift_detector.get_latest_drift(),
            'performance': self.performance_monitor.get_latest_performance(),
            'next_retrain_check': self._get_next_retrain_check()
        }
    
    def _get_next_retrain_check(self) -> Optional[str]:
        """Tính thời gian check retrain tiếp theo."""
        if self.metadata['last_retrain']:
            last_retrain = datetime.fromisoformat(self.metadata['last_retrain'])
            next_check = last_retrain + timedelta(days=self.retrain_interval_days)
            return next_check.isoformat()
        return None

