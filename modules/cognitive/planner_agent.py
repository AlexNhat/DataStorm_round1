"""
LLM-based Planner Agent: Đề xuất hành động cụ thể từ strategies.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .strategy_engine import Strategy, StrategyEngine


class PlannerAgent:
    """
    LLM-based Planner Agent.
    
    Nhiệm vụ:
    - Đọc kết quả từ strategy_engine
    - Tóm tắt và đề xuất hành động cụ thể
    - Lý luận step-by-step (chain-of-thought)
    - Tránh đề xuất trái chính sách
    """
    
    def __init__(self, policy_constraints: Optional[Dict] = None):
        """
        Args:
            policy_constraints: Policy constraints để kiểm tra
                {
                    'max_inventory_change_pct': 30,
                    'max_price_change_pct': 10,
                    'min_service_level': 0.85
                }
        """
        self.policy_constraints = policy_constraints or {
            'max_inventory_change_pct': 30,
            'max_price_change_pct': 10,
            'min_service_level': 0.85,
            'max_cost_per_action': 100000
        }
        self.reasoning_log = []
    
    def generate_recommendations(
        self,
        strategies: List[Strategy],
        comparison: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Sinh recommendations từ strategies.
        
        Args:
            strategies: List of Strategy objects
            comparison: Comparison results từ strategy_engine
            context: Additional context
            
        Returns:
            Dict với recommendations, reasoning, policy_check
        """
        # Chain-of-thought reasoning (internal)
        reasoning_steps = self._reason_about_strategies(strategies, comparison, context)
        
        # Chọn best strategy
        best_strategy_id = comparison.get('best_strategy')
        best_strategy = next((s for s in strategies if s.id == best_strategy_id), None)
        
        if not best_strategy:
            return {
                'recommendations': [],
                'reasoning': 'Không có strategy phù hợp',
                'policy_compliant': False
            }
        
        # Generate actionable recommendations
        recommendations = self._generate_actionable_recommendations(best_strategy, context)
        
        # Policy check
        policy_check = self._check_policy_compliance(recommendations, best_strategy)
        
        # Summary reasoning (output)
        reasoning_summary = self._summarize_reasoning(reasoning_steps, best_strategy, policy_check)
        
        # Log reasoning
        self.reasoning_log.append({
            'timestamp': datetime.now().isoformat(),
            'strategies_considered': [s.id for s in strategies],
            'best_strategy': best_strategy_id,
            'reasoning_steps': reasoning_steps,
            'recommendations': recommendations,
            'policy_check': policy_check
        })
        
        return {
            'recommendations': recommendations,
            'reasoning': reasoning_summary,
            'policy_compliant': policy_check['compliant'],
            'policy_violations': policy_check.get('violations', []),
            'best_strategy': best_strategy_id,
            'confidence': best_strategy.confidence
        }
    
    def _reason_about_strategies(
        self,
        strategies: List[Strategy],
        comparison: Dict,
        context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Chain-of-thought reasoning về strategies.
        
        Returns:
            List of reasoning steps
        """
        reasoning_steps = []
        
        # Step 1: Analyze objectives
        reasoning_steps.append({
            'step': 1,
            'type': 'objective_analysis',
            'content': 'Phân tích mục tiêu kinh doanh và context hiện tại'
        })
        
        # Step 2: Evaluate each strategy
        for strategy in strategies:
            reasoning_steps.append({
                'step': len(reasoning_steps) + 1,
                'type': 'strategy_evaluation',
                'strategy_id': strategy.id,
                'content': f"Đánh giá {strategy.name}: Profit={strategy.estimated_profit:.0f}, "
                          f"Confidence={strategy.confidence:.2f}, Risks={len(strategy.risks)}"
            })
        
        # Step 3: Compare strategies
        reasoning_steps.append({
            'step': len(reasoning_steps) + 1,
            'type': 'comparison',
            'content': f"So sánh các strategies: Best by profit={comparison.get('ranked_by_profit', [])[0] if comparison.get('ranked_by_profit') else 'N/A'}"
        })
        
        # Step 4: Consider trade-offs
        reasoning_steps.append({
            'step': len(reasoning_steps) + 1,
            'type': 'trade_off_analysis',
            'content': 'Phân tích trade-offs giữa profit, confidence, và risk'
        })
        
        return reasoning_steps
    
    def _generate_actionable_recommendations(
        self,
        strategy: Strategy,
        context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Sinh actionable recommendations từ strategy.
        
        Returns:
            List of specific actions
        """
        recommendations = []
        
        # Convert strategy actions to specific recommendations
        for action in strategy.actions:
            action_type = action.get('type')
            
            if action_type == 'increase_inventory':
                recommendation = {
                    'action': 'increase_inventory',
                    'description': (
                        f"Tuần tới, hãy tăng {action.get('quantity', 0)} đơn vị "
                        f"{action.get('product', 'sản phẩm')} tại {action.get('warehouse', 'kho')}. "
                        f"Timeline: {action.get('timeline', '2 tuần')}"
                    ),
                    'details': action,
                    'priority': 'high' if strategy.confidence > 0.7 else 'medium'
                }
                recommendations.append(recommendation)
            
            elif action_type == 'redistribute_inventory':
                recommendation = {
                    'action': 'redistribute_inventory',
                    'description': (
                        f"Phân bổ lại tồn kho giữa các warehouses để đạt balance {action.get('target_balance', 0.9)}. "
                        f"Timeline: {action.get('timeline', '1 tuần')}"
                    ),
                    'details': action,
                    'priority': 'medium'
                }
                recommendations.append(recommendation)
            
            elif action_type == 'increase_lead_time_buffer':
                recommendation = {
                    'action': 'increase_lead_time_buffer',
                    'description': (
                        f"Tăng lead time buffer từ {action.get('current_lead_time', 3)} ngày "
                        f"lên {action.get('new_lead_time', 4)} ngày. Timeline: {action.get('timeline', 'immediate')}"
                    ),
                    'details': action,
                    'priority': 'high'
                }
                recommendations.append(recommendation)
            
            elif action_type == 'prioritize_vip_orders':
                recommendation = {
                    'action': 'prioritize_vip_orders',
                    'description': (
                        f"Ưu tiên xử lý đơn hàng của {len(action.get('vip_customers', []))} khách hàng VIP "
                        f"với priority boost {action.get('priority_boost', 0.3)*100:.0f}%. "
                        f"Timeline: {action.get('timeline', 'immediate')}"
                    ),
                    'details': action,
                    'priority': 'high'
                }
                recommendations.append(recommendation)
            
            elif action_type == 'monitor_weather':
                recommendation = {
                    'action': 'monitor_weather',
                    'description': (
                        f"Theo dõi thời tiết tại {action.get('location', 'khu vực')} "
                        f"với alert threshold {action.get('alert_threshold', 20)}mm mưa"
                    ),
                    'details': action,
                    'priority': 'medium'
                }
                recommendations.append(recommendation)
            
            else:
                # Generic action
                recommendation = {
                    'action': action_type,
                    'description': f"Thực hiện hành động: {action_type}",
                    'details': action,
                    'priority': 'medium'
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def _check_policy_compliance(
        self,
        recommendations: List[Dict],
        strategy: Strategy
    ) -> Dict[str, Any]:
        """
        Kiểm tra policy compliance.
        
        Returns:
            Dict với compliant flag và violations
        """
        violations = []
        compliant = True
        
        # Check inventory changes
        for rec in recommendations:
            if rec['action'] == 'increase_inventory':
                details = rec.get('details', {})
                quantity = details.get('quantity', 0)
                # Assume current inventory from context (simplified)
                current_inv = 1000  # Placeholder
                if current_inv > 0:
                    change_pct = (quantity / current_inv) * 100
                    max_change = self.policy_constraints.get('max_inventory_change_pct', 30)
                    if change_pct > max_change:
                        violations.append({
                            'type': 'inventory_change_exceeded',
                            'value': change_pct,
                            'limit': max_change,
                            'action': rec['action']
                        })
                        compliant = False
            
            # Check cost
            estimated_cost = strategy.estimated_cost
            max_cost = self.policy_constraints.get('max_cost_per_action', 100000)
            if estimated_cost > max_cost:
                violations.append({
                    'type': 'cost_exceeded',
                    'value': estimated_cost,
                    'limit': max_cost,
                    'action': 'strategy_execution'
                })
                compliant = False
        
        # Check service level
        service_level = strategy.kpis.get('service_level_improvement', 0)
        min_service = self.policy_constraints.get('min_service_level', 0.85)
        if service_level < min_service * 100:
            violations.append({
                'type': 'service_level_below_minimum',
                'value': service_level,
                'limit': min_service * 100,
                'action': 'strategy_execution'
            })
            # Warning, not blocking
            # compliant = False  # Uncomment if strict
        
        return {
            'compliant': compliant,
            'violations': violations,
            'checked_at': datetime.now().isoformat()
        }
    
    def _summarize_reasoning(
        self,
        reasoning_steps: List[Dict],
        best_strategy: Strategy,
        policy_check: Dict
    ) -> str:
        """
        Tóm tắt reasoning thành text dễ hiểu.
        """
        summary = f"Dựa trên phân tích {len(reasoning_steps)} bước, "
        summary += f"chiến lược được đề xuất là: **{best_strategy.name}**.\n\n"
        
        summary += f"**Lý do:**\n"
        summary += f"- Ước tính lợi nhuận: ${best_strategy.estimated_profit:,.0f}\n"
        summary += f"- Độ tin cậy: {best_strategy.confidence*100:.0f}%\n"
        summary += f"- Rủi ro: {len(best_strategy.risks)} điểm cần lưu ý\n\n"
        
        if policy_check['compliant']:
            summary += "✅ **Policy Compliance:** Tất cả hành động đều tuân thủ policy.\n\n"
        else:
            summary += "⚠️ **Policy Compliance:** Có một số vi phạm policy cần xem xét:\n"
            for violation in policy_check.get('violations', []):
                summary += f"  - {violation['type']}: {violation['value']:.2f} vượt quá limit {violation['limit']:.2f}\n"
            summary += "\n"
        
        summary += f"**Hành động cụ thể:**\n"
        for i, action in enumerate(best_strategy.actions, 1):
            summary += f"{i}. {action.get('type', 'action')} - {action.get('timeline', 'timeline')}\n"
        
        return summary
    
    def get_reasoning_log(self, limit: int = 10) -> List[Dict]:
        """Lấy reasoning log gần đây."""
        return self.reasoning_log[-limit:]

