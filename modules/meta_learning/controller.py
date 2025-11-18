"""
Meta-Learning Controller: Theo dõi và quản lý tất cả models.

Nhiệm vụ:
- Theo dõi tất cả model
- Xác định model nào đang kém → đề xuất thay đổi
- Tự chọn model phù hợp theo từng season/region
- Sinh reasoning report
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .model_selector import ModelSelector
from .reasoning_engine import ReasoningEngine


class MetaLearningController:
    """
    Meta-Learning Controller: Quản lý và tối ưu hóa models.
    """
    
    def __init__(
        self,
        models_config: Dict[str, Dict],
        reports_dir: str = "meta_learning_reports"
    ):
        """
        Args:
            models_config: Dict với config của từng model
                {
                    'logistics_delay': {
                        'model_path': '...',
                        'regions': ['US', 'EU', 'ASIA'],
                        'seasons': ['spring', 'summer', 'fall', 'winter']
                    },
                    ...
                }
            reports_dir: Thư mục lưu reports
        """
        self.models_config = models_config
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        
        # Initialize components
        self.model_selector = ModelSelector(models_config)
        self.reasoning_engine = ReasoningEngine()
        
        # Performance tracking
        self.performance_history = {}
        for model_name in models_config.keys():
            self.performance_history[model_name] = []
    
    def observe_performance(
        self,
        model_name: str,
        context: Dict[str, Any],
        performance: Dict[str, float]
    ):
        """
        Quan sát performance của model trong một context cụ thể.
        
        Args:
            model_name: Tên model
            context: Context (region, season, time_period, etc.)
            performance: Performance metrics (accuracy, f1, rmse, etc.)
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'performance': performance
        }
        
        if model_name not in self.performance_history:
            self.performance_history[model_name] = []
        
        self.performance_history[model_name].append(record)
    
    def select_best_model(
        self,
        context: Dict[str, Any],
        task_type: str = 'auto'
    ) -> Tuple[str, Dict]:
        """
        Chọn best model cho context cụ thể.
        
        Args:
            context: Context (region, season, etc.)
            task_type: 'classification' hoặc 'regression'
            
        Returns:
            (best_model_name, reasoning_report)
        """
        best_model, reasoning = self.model_selector.select(
            context=context,
            performance_history=self.performance_history,
            task_type=task_type
        )
        
        # Sinh reasoning report
        report = self.reasoning_engine.generate_report(
            selected_model=best_model,
            context=context,
            reasoning=reasoning,
            alternatives=self.model_selector.get_alternatives(context)
        )
        
        # Lưu report
        self._save_report(report, context)
        
        return best_model, report
    
    def analyze_model_health(self) -> Dict[str, Any]:
        """
        Phân tích sức khỏe của tất cả models.
        
        Returns:
            Dict với health status của từng model
        """
        health_report = {}
        
        for model_name, history in self.performance_history.items():
            if len(history) == 0:
                health_report[model_name] = {
                    'status': 'unknown',
                    'reason': 'No performance data'
                }
                continue
            
            # Phân tích performance trend
            recent_performance = [h['performance'] for h in history[-10:]]
            
            # Tính average performance
            if task_type := self._infer_task_type(recent_performance):
                if task_type == 'classification':
                    avg_metric = np.mean([p.get('f1', p.get('accuracy', 0.5)) for p in recent_performance])
                else:
                    avg_metric = np.mean([p.get('r2', 1 - p.get('rmse', 1.0)) for p in recent_performance])
            else:
                avg_metric = 0.5
            
            # Đánh giá health
            if avg_metric > 0.8:
                status = 'healthy'
            elif avg_metric > 0.6:
                status = 'degrading'
            else:
                status = 'unhealthy'
            
            health_report[model_name] = {
                'status': status,
                'average_performance': float(avg_metric),
                'data_points': len(history),
                'recommendation': self._get_recommendation(status, avg_metric)
            }
        
        return health_report
    
    def _infer_task_type(self, performance_list: List[Dict]) -> Optional[str]:
        """Infer task type từ performance metrics."""
        if not performance_list:
            return None
        
        first = performance_list[0]
        if 'f1' in first or 'accuracy' in first:
            return 'classification'
        elif 'rmse' in first or 'r2' in first:
            return 'regression'
        return None
    
    def _get_recommendation(self, status: str, performance: float) -> str:
        """Đề xuất hành động dựa trên health status."""
        if status == 'healthy':
            return "Model is performing well. Continue monitoring."
        elif status == 'degrading':
            return "Model performance is degrading. Consider retraining or switching model."
        else:
            return "Model is unhealthy. Immediate retraining or model replacement recommended."
    
    def _save_report(self, report: Dict, context: Dict):
        """Lưu reasoning report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_str = "_".join([f"{k}_{v}" for k, v in context.items()])
        filename = f"report_{timestamp}_{context_str}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    def get_status(self) -> Dict:
        """Lấy trạng thái tổng quan."""
        health = self.analyze_model_health()
        
        return {
            'models_tracked': list(self.models_config.keys()),
            'total_observations': sum(len(h) for h in self.performance_history.values()),
            'health_summary': health,
            'reports_generated': len(os.listdir(self.reports_dir)) if os.path.exists(self.reports_dir) else 0
        }

