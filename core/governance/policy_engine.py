"""
Policy Engine: Kiểm duyệt mọi action do AI đề xuất.
"""

import yaml
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class PolicyEngine:
    """
    Policy Engine: Kiểm tra policy compliance cho mọi action.
    """
    
    def __init__(self, policies_path: Optional[str] = None):
        """
        Args:
            policies_path: Đường dẫn đến policies.yaml
        """
        if policies_path is None:
            policies_path = os.path.join(
                os.path.dirname(__file__),
                'policies.yaml'
            )
        
        self.policies_path = policies_path
        self.policies = self._load_policies()
        self.violation_log = []
    
    def _load_policies(self) -> Dict:
        """Load policies từ YAML."""
        if os.path.exists(self.policies_path):
            with open(self.policies_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default policies
            return {
                'inventory': {
                    'min_days_cover': 7,
                    'max_inventory_change_pct': 30
                },
                'actions': {
                    'max_cost_per_action': 100000,
                    'min_confidence_for_auto': 0.7
                }
            }
    
    def check_action(
        self,
        action: Dict[str, Any],
        context: Optional[Dict] = None,
        mode: str = 'advisory'
    ) -> Dict[str, Any]:
        """
        Kiểm tra một action có tuân thủ policy không.
        
        Args:
            action: Action dict
                {
                    'type': 'increase_inventory',
                    'params': {...},
                    'estimated_cost': 50000,
                    'confidence': 0.8
                }
            context: Additional context
            mode: 'advisory', 'hybrid', 'autonomous'
            
        Returns:
            {
                'compliant': bool,
                'violations': [...],
                'requires_approval': bool,
                'approval_reason': str
            }
        """
        violations = []
        requires_approval = False
        approval_reason = None
        
        action_type = action.get('type')
        params = action.get('params', {})
        estimated_cost = action.get('estimated_cost', 0)
        confidence = action.get('confidence', 0.5)
        
        # Check inventory policies
        if action_type in ['increase_inventory', 'decrease_inventory', 'redistribute_inventory']:
            change_pct = params.get('change_pct', 0)
            max_change = self.policies.get('inventory', {}).get('max_inventory_change_pct', 30)
            
            if abs(change_pct) > max_change:
                violations.append({
                    'type': 'inventory_change_exceeded',
                    'value': change_pct,
                    'limit': max_change,
                    'policy': 'inventory.max_inventory_change_pct'
                })
                requires_approval = True
                approval_reason = f"Inventory change {change_pct}% exceeds limit {max_change}%"
        
        # Check cost policies
        max_cost = self.policies.get('actions', {}).get('max_cost_per_action', 100000)
        if estimated_cost > max_cost:
            violations.append({
                'type': 'cost_exceeded',
                'value': estimated_cost,
                'limit': max_cost,
                'policy': 'actions.max_cost_per_action'
            })
            requires_approval = True
            approval_reason = f"Cost ${estimated_cost} exceeds limit ${max_cost}"
        
        # Check confidence
        min_confidence = self.policies.get('actions', {}).get('min_confidence_for_auto', 0.7)
        if confidence < min_confidence:
            violations.append({
                'type': 'confidence_below_threshold',
                'value': confidence,
                'limit': min_confidence,
                'policy': 'actions.min_confidence_for_auto'
            })
            requires_approval = True
            approval_reason = f"Confidence {confidence:.2f} below threshold {min_confidence:.2f}"
        
        # Check mode-specific policies
        mode_policies = self.policies.get('modes', {}).get(mode, {})
        auto_execute = mode_policies.get('auto_execute', False)
        
        if not auto_execute:
            requires_approval = True
            approval_reason = f"Mode {mode} requires approval for all actions"
        
        # Check require_approval conditions
        require_approval_conditions = mode_policies.get('require_approval', [])
        for condition in require_approval_conditions:
            if self._check_condition(condition, action, context):
                requires_approval = True
                approval_reason = f"Condition '{condition}' requires approval"
                break
        
        # Check safety policies
        safety_check = self._check_safety(action, context)
        if not safety_check['safe']:
            violations.extend(safety_check.get('violations', []))
            requires_approval = True
            approval_reason = "Safety check failed"
        
        # Log violations
        if violations:
            self.violation_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'violations': violations,
                'mode': mode
            })
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'requires_approval': requires_approval,
            'approval_reason': approval_reason,
            'checked_at': datetime.now().isoformat()
        }
    
    def _check_condition(
        self,
        condition: str,
        action: Dict,
        context: Optional[Dict]
    ) -> bool:
        """Kiểm tra một condition."""
        if condition == 'cost_above_50000':
            return action.get('estimated_cost', 0) > 50000
        
        elif condition == 'inventory_change_above_20pct':
            params = action.get('params', {})
            change_pct = abs(params.get('change_pct', 0))
            return change_pct > 20
        
        elif condition == 'price_change_above_5pct':
            params = action.get('params', {})
            change_pct = abs(params.get('price_change_pct', 0))
            return change_pct > 5
        
        elif condition == 'cost_above_100000':
            return action.get('estimated_cost', 0) > 100000
        
        elif condition == 'inventory_change_above_30pct':
            params = action.get('params', {})
            change_pct = abs(params.get('change_pct', 0))
            return change_pct > 30
        
        elif condition == 'anomaly_detected':
            return context and context.get('anomaly_detected', False)
        
        return False
    
    def _check_safety(
        self,
        action: Dict,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Kiểm tra safety."""
        violations = []
        safe = True
        
        action_type = action.get('type')
        
        # Check blacklist
        blacklist = self.policies.get('safety', {}).get('blacklist_actions', [])
        if action_type in blacklist:
            violations.append({
                'type': 'blacklisted_action',
                'action': action_type,
                'policy': 'safety.blacklist_actions'
            })
            safe = False
        
        # Check anomaly
        if context and context.get('anomaly_detected', False):
            require_review = self.policies.get('safety', {}).get('require_review_for_anomalies', True)
            if require_review:
                violations.append({
                    'type': 'anomaly_detected',
                    'policy': 'safety.require_review_for_anomalies'
                })
                safe = False
        
        # Check risk score
        risk_score = action.get('risk_score', 0)
        max_risk = self.policies.get('safety', {}).get('max_risk_score', 0.8)
        if risk_score > max_risk:
            violations.append({
                'type': 'risk_score_exceeded',
                'value': risk_score,
                'limit': max_risk,
                'policy': 'safety.max_risk_score'
            })
            safe = False
        
        return {
            'safe': safe,
            'violations': violations
        }
    
    def get_violation_log(self, limit: int = 10) -> List[Dict]:
        """Lấy violation log gần đây."""
        return self.violation_log[-limit:]

