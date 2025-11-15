"""
OS Integration: Tích hợp Digital Twin với OS Orchestrator.
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.os_orchestrator import OSOrchestrator
from engines.digital_twin.core import DigitalTwinEngine
from modules.cognitive.strategy_engine import StrategyEngine
from modules.cognitive.planner_agent import PlannerAgent
from core.governance.policy_engine import PolicyEngine


class OSIntegration:
    """
    Tích hợp Digital Twin với OS Orchestrator.
    
    Flow:
    1. Mỗi khi cần quyết định lớn → chạy simulation trong Digital Twin
    2. Strategy Engine + Planner Agent phân tích kết quả
    3. Policy Engine kiểm tra constraints
    4. Action được đề xuất cho Control Center
    """
    
    def __init__(
        self,
        orchestrator: Optional[OSOrchestrator] = None,
        digital_twin: Optional[DigitalTwinEngine] = None
    ):
        """
        Args:
            orchestrator: OS Orchestrator instance
            digital_twin: Digital Twin Engine instance
        """
        self.orchestrator = orchestrator or OSOrchestrator()
        self.digital_twin = digital_twin or DigitalTwinEngine()
        self.strategy_engine = StrategyEngine()
        self.planner_agent = PlannerAgent()
        self.policy_engine = PolicyEngine()
    
    def make_strategic_decision(
        self,
        decision_context: Dict[str, Any],
        simulation_duration_hours: int = 168
    ) -> Dict[str, Any]:
        """
        Đưa ra quyết định chiến lược với Digital Twin simulation.
        
        Args:
            decision_context: Context cho decision
                {
                    'model_results': {...},
                    'business_context': {...},
                    'objectives': [...]
                }
            simulation_duration_hours: Duration của simulation
            
        Returns:
            Decision result với action recommendations
        """
        # 1. Run Digital Twin simulation
        simulation_results = self._run_simulation(decision_context, simulation_duration_hours)
        
        # 2. Generate strategies
        strategies = self.strategy_engine.generate_strategies(
            model_results=decision_context.get('model_results', {}),
            business_context=decision_context.get('business_context', {}),
            objectives=decision_context.get('objectives', ['balance'])
        )
        
        # 3. Compare strategies
        comparison = self.strategy_engine.compare_strategies(strategies)
        
        # 4. Generate recommendations
        recommendations = self.planner_agent.generate_recommendations(
            strategies=strategies,
            comparison=comparison,
            context=decision_context.get('business_context', {})
        )
        
        # 5. Policy check cho mỗi recommendation
        policy_checked_recommendations = []
        for rec in recommendations['recommendations']:
            action = {
                'type': rec['action'],
                'params': rec.get('details', {}),
                'estimated_cost': rec.get('details', {}).get('cost', 0),
                'confidence': recommendations.get('confidence', 0.5)
            }
            
            policy_result = self.policy_engine.check_action(
                action=action,
                context=decision_context.get('business_context', {}),
                mode=decision_context.get('mode', 'advisory')
            )
            
            policy_checked_recommendations.append({
                'recommendation': rec,
                'policy_check': policy_result
            })
        
        # 6. Log decision
        decision_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'strategic_decision',
            'simulation_results': simulation_results,
            'strategies': [s.id for s in strategies],
            'best_strategy': comparison.get('best_strategy'),
            'recommendations': policy_checked_recommendations,
            'requires_approval': any(
                rec['policy_check']['requires_approval']
                for rec in policy_checked_recommendations
            )
        }
        
        self.orchestrator._log_decision(decision_log)
        
        return {
            'status': 'success',
            'simulation_results': simulation_results,
            'strategies': [
                {
                    'id': s.id,
                    'name': s.name,
                    'estimated_profit': s.estimated_profit,
                    'confidence': s.confidence
                }
                for s in strategies
            ],
            'best_strategy': comparison.get('best_strategy'),
            'recommendations': policy_checked_recommendations,
            'requires_approval': decision_log['requires_approval'],
            'decision_log_id': decision_log['timestamp']
        }
    
    def _run_simulation(
        self,
        context: Dict,
        duration_hours: int
    ) -> Dict[str, Any]:
        """Chạy Digital Twin simulation."""
        # Initialize Digital Twin nếu chưa có
        if not self.digital_twin.state.warehouses:
            # Setup từ context
            warehouses = context.get('business_context', {}).get('warehouses', [])
            routes = context.get('business_context', {}).get('transport_routes', [])
            self.digital_twin.initialize(warehouses, routes)
        
        # Run simulation
        results = self.digital_twin.run_simulation(duration_hours=duration_hours)
        
        # Get final state
        final_state = self.digital_twin.get_state()
        
        return {
            'simulation_duration': duration_hours,
            'total_steps': len(results),
            'final_metrics': final_state.get_state_summary(),
            'simulation_history': results[-10:]  # Last 10 steps
        }

