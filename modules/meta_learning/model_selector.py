"""
Model Selector: Chọn best model cho từng context.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta


class ModelSelector:
    """
    Chọn model tốt nhất cho từng context (region, season, etc.).
    """
    
    def __init__(self, models_config: Dict[str, Dict]):
        """
        Args:
            models_config: Config của các models
        """
        self.models_config = models_config
    
    def select(
        self,
        context: Dict[str, Any],
        performance_history: Dict[str, List[Dict]],
        task_type: str = 'auto'
    ) -> Tuple[str, Dict]:
        """
        Chọn best model.
        
        Returns:
            (best_model_name, reasoning_dict)
        """
        # Lọc performance history theo context
        filtered_history = self._filter_by_context(performance_history, context)
        
        if not filtered_history:
            # Không có data, chọn model mặc định
            default_model = list(self.models_config.keys())[0]
            return default_model, {
                'reason': 'No performance data for this context. Using default model.',
                'confidence': 0.0
            }
        
        # Tính average performance cho từng model
        model_scores = {}
        for model_name, history in filtered_history.items():
            if len(history) == 0:
                continue
            
            # Tính average performance
            performances = [h['performance'] for h in history]
            
            if task_type == 'classification' or self._is_classification(performances):
                # Dùng F1 hoặc Accuracy
                scores = [p.get('f1', p.get('accuracy', 0.5)) for p in performances]
            else:
                # Dùng R² hoặc (1 - normalized RMSE)
                scores = []
                for p in performances:
                    if 'r2' in p:
                        scores.append(p['r2'])
                    elif 'rmse' in p:
                        # Normalize RMSE (giả sử max RMSE = 1000)
                        normalized = 1 - min(p['rmse'] / 1000.0, 1.0)
                        scores.append(normalized)
                    else:
                        scores.append(0.5)
            
            model_scores[model_name] = {
                'average': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'count': len(history),
                'recent_trend': self._calculate_trend(scores)
            }
        
        if not model_scores:
            default_model = list(self.models_config.keys())[0]
            return default_model, {'reason': 'No valid performance data', 'confidence': 0.0}
        
        # Chọn model có score cao nhất
        best_model = max(model_scores.items(), key=lambda x: x[1]['average'])[0]
        
        # Tạo reasoning
        reasoning = {
            'selected_model': best_model,
            'scores': model_scores,
            'reason': self._generate_reason(best_model, model_scores, context),
            'confidence': self._calculate_confidence(model_scores[best_model], model_scores)
        }
        
        return best_model, reasoning
    
    def _filter_by_context(
        self,
        performance_history: Dict[str, List[Dict]],
        context: Dict[str, Any]
    ) -> Dict[str, List[Dict]]:
        """Lọc performance history theo context."""
        filtered = {}
        
        for model_name, history in performance_history.items():
            filtered_history = []
            for record in history:
                record_context = record.get('context', {})
                
                # Kiểm tra match context
                match = True
                for key, value in context.items():
                    if key in record_context:
                        if record_context[key] != value:
                            match = False
                            break
                
                if match:
                    filtered_history.append(record)
            
            if filtered_history:
                filtered[model_name] = filtered_history
        
        return filtered
    
    def _is_classification(self, performances: List[Dict]) -> bool:
        """Kiểm tra xem có phải classification task không."""
        if not performances:
            return False
        
        first = performances[0]
        return 'f1' in first or 'accuracy' in first or 'precision' in first
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Tính trend (improving, stable, degrading)."""
        if len(scores) < 2:
            return 'stable'
        
        recent = scores[-5:] if len(scores) >= 5 else scores
        older = scores[:-5] if len(scores) > 5 else []
        
        if not older:
            return 'stable'
        
        recent_avg = np.mean(recent)
        older_avg = np.mean(older)
        
        diff = recent_avg - older_avg
        
        if diff > 0.05:
            return 'improving'
        elif diff < -0.05:
            return 'degrading'
        else:
            return 'stable'
    
    def _generate_reason(
        self,
        selected_model: str,
        model_scores: Dict[str, Dict],
        context: Dict[str, Any]
    ) -> str:
        """Sinh lý do chọn model."""
        selected_score = model_scores[selected_model]
        
        # So sánh với các models khác
        alternatives = [m for m in model_scores.keys() if m != selected_model]
        
        if not alternatives:
            return f"Model {selected_model} is the only available model for this context."
        
        # Tìm model tốt thứ 2
        second_best = max(alternatives, key=lambda m: model_scores[m]['average'])
        second_score = model_scores[second_best]
        
        diff = selected_score['average'] - second_score['average']
        
        reason = f"Model {selected_model} selected because: "
        reason += f"1) It has the highest average performance ({selected_score['average']:.3f}) "
        reason += f"2) Performance difference vs {second_best}: {diff:.3f} "
        reason += f"3) Recent trend: {selected_score['recent_trend']} "
        reason += f"4) Based on {selected_score['count']} observations in this context"
        
        return reason
    
    def _calculate_confidence(
        self,
        selected_score: Dict,
        all_scores: Dict[str, Dict]
    ) -> float:
        """Tính confidence (0-1) cho selection."""
        # Confidence dựa trên:
        # 1. Số lượng observations
        # 2. Độ chênh lệch với models khác
        # 3. Độ ổn định (std)
        
        count_factor = min(selected_score['count'] / 100.0, 1.0)
        
        # Tính max difference với models khác
        alternatives = [s for m, s in all_scores.items() if m != list(all_scores.keys())[0]]
        if alternatives:
            max_diff = max([selected_score['average'] - s['average'] for s in alternatives])
            diff_factor = min(max_diff / 0.2, 1.0)  # 0.2 = 20% difference
        else:
            diff_factor = 0.5
        
        # Stability factor (lower std = higher confidence)
        std_factor = 1.0 - min(selected_score['std'] / 0.3, 1.0)
        
        confidence = (count_factor * 0.4 + diff_factor * 0.4 + std_factor * 0.2)
        return float(confidence)
    
    def get_alternatives(self, context: Dict[str, Any]) -> List[str]:
        """Lấy danh sách alternative models cho context."""
        # Trả về tất cả models ngoài best model
        return list(self.models_config.keys())

