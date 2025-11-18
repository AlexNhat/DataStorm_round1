"""
Safety Checks: Kiểm tra data anomalies và actions nguy hiểm.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime


class SafetyChecker:
    """
    Safety Checker: Phát hiện anomalies và actions nguy hiểm.
    """
    
    def __init__(self, anomaly_threshold: float = 3.0):
        """
        Args:
            anomaly_threshold: Z-score threshold cho anomaly detection
        """
        self.anomaly_threshold = anomaly_threshold
        self.anomaly_log = []
    
    def check_data_anomalies(
        self,
        data: np.ndarray,
        historical_mean: Optional[float] = None,
        historical_std: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Kiểm tra data anomalies.
        
        Args:
            data: Data array
            historical_mean: Mean lịch sử (nếu có)
            historical_std: Std lịch sử (nếu có)
            
        Returns:
            {
                'anomaly_detected': bool,
                'anomaly_score': float,
                'anomalies': [...]
            }
        """
        if historical_mean is None:
            historical_mean = np.mean(data) if len(data) > 0 else 0
        
        if historical_std is None:
            historical_std = np.std(data) if len(data) > 0 else 1
        
        if historical_std == 0:
            historical_std = 1
        
        # Calculate Z-scores
        z_scores = np.abs((data - historical_mean) / historical_std)
        
        # Find anomalies
        anomalies = np.where(z_scores > self.anomaly_threshold)[0]
        anomaly_detected = len(anomalies) > 0
        max_z_score = np.max(z_scores) if len(z_scores) > 0 else 0
        
        result = {
            'anomaly_detected': anomaly_detected,
            'anomaly_score': float(max_z_score),
            'anomalies': anomalies.tolist(),
            'threshold': self.anomaly_threshold
        }
        
        if anomaly_detected:
            self.anomaly_log.append({
                'timestamp': datetime.now().isoformat(),
                'anomaly_score': float(max_z_score),
                'anomalies_count': len(anomalies)
            })
        
        return result
    
    def check_action_safety(
        self,
        action: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Kiểm tra action có an toàn không.
        
        Args:
            action: Action dict
            context: Context
            
        Returns:
            {
                'safe': bool,
                'risk_level': 'low' | 'medium' | 'high',
                'risks': [...],
                'requires_review': bool
            }
        """
        risks = []
        risk_level = 'low'
        requires_review = False
        
        action_type = action.get('type')
        params = action.get('params', {})
        
        # Check dangerous actions
        dangerous_patterns = [
            ('decrease_inventory', lambda p: abs(p.get('change_pct', 0)) > 50),
            ('set_price', lambda p: p.get('price', 0) < 0.01),
            ('delete_inventory', lambda p: True),
            ('disable_warehouse', lambda p: True)
        ]
        
        for pattern_type, check_func in dangerous_patterns:
            if action_type == pattern_type and check_func(params):
                risks.append({
                    'type': 'dangerous_action',
                    'action': action_type,
                    'severity': 'high'
                })
                risk_level = 'high'
                requires_review = True
        
        # Check extreme values
        if 'change_pct' in params:
            change_pct = abs(params['change_pct'])
            if change_pct > 50:
                risks.append({
                    'type': 'extreme_change',
                    'value': change_pct,
                    'severity': 'high'
                })
                risk_level = 'high'
                requires_review = True
            elif change_pct > 30:
                risks.append({
                    'type': 'large_change',
                    'value': change_pct,
                    'severity': 'medium'
                })
                if risk_level == 'low':
                    risk_level = 'medium'
        
        # Check cost
        estimated_cost = action.get('estimated_cost', 0)
        if estimated_cost > 100000:
            risks.append({
                'type': 'high_cost',
                'value': estimated_cost,
                'severity': 'high'
            })
            if risk_level != 'high':
                risk_level = 'high'
            requires_review = True
        
        return {
            'safe': len(risks) == 0,
            'risk_level': risk_level,
            'risks': risks,
            'requires_review': requires_review,
            'checked_at': datetime.now().isoformat()
        }
    
    def get_anomaly_log(self, limit: int = 10) -> List[Dict]:
        """Lấy anomaly log gần đây."""
        return self.anomaly_log[-limit:]

