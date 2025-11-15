"""
Reasoning Engine: Sinh reasoning reports cho quyết định của Meta-Learning.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class ReasoningEngine:
    """
    Sinh reasoning reports giải thích tại sao chọn model này.
    """
    
    def generate_report(
        self,
        selected_model: str,
        context: Dict[str, Any],
        reasoning: Dict[str, Any],
        alternatives: List[str]
    ) -> Dict[str, Any]:
        """
        Sinh reasoning report.
        
        Returns:
            Dict với report chi tiết
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'selected_model': selected_model,
            'context': context,
            'reasoning': {
                'main_reason': reasoning.get('reason', 'No reason provided'),
                'confidence': reasoning.get('confidence', 0.0),
                'performance_comparison': reasoning.get('scores', {})
            },
            'alternatives': alternatives,
            'recommendations': self._generate_recommendations(selected_model, reasoning, context),
            'next_steps': self._generate_next_steps(selected_model, reasoning)
        }
        
        return report
    
    def _generate_recommendations(
        self,
        selected_model: str,
        reasoning: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Sinh recommendations."""
        recommendations = []
        
        confidence = reasoning.get('confidence', 0.0)
        scores = reasoning.get('scores', {})
        
        if confidence < 0.5:
            recommendations.append(
                "Low confidence in model selection. Consider collecting more performance data."
            )
        
        if selected_model in scores:
            trend = scores[selected_model].get('recent_trend', 'stable')
            if trend == 'degrading':
                recommendations.append(
                    f"Model {selected_model} is showing degrading performance. "
                    "Consider retraining or switching to alternative model."
                )
            elif trend == 'improving':
                recommendations.append(
                    f"Model {selected_model} is improving. Continue monitoring."
                )
        
        # Recommendations dựa trên context
        if 'region' in context:
            recommendations.append(
                f"Model selected for region {context['region']}. "
                "Consider region-specific fine-tuning if performance is suboptimal."
            )
        
        if 'season' in context:
            recommendations.append(
                f"Model selected for {context['season']} season. "
                "Seasonal patterns may require periodic model updates."
            )
        
        return recommendations
    
    def _generate_next_steps(
        self,
        selected_model: str,
        reasoning: Dict[str, Any]
    ) -> List[str]:
        """Sinh next steps."""
        next_steps = [
            f"Deploy model {selected_model} for predictions",
            "Continue monitoring performance",
            "Collect feedback and update performance history"
        ]
        
        confidence = reasoning.get('confidence', 0.0)
        if confidence < 0.7:
            next_steps.append("Run A/B test with alternative models")
        
        return next_steps

