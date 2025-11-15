"""
Strategic Reasoning Layer: Tạo và so sánh các phương án chiến lược.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class Strategy:
    """Một phương án chiến lược."""
    id: str
    name: str
    description: str  # Mô tả định tính
    kpis: Dict[str, float]  # KPI ước tính
    risks: List[str]  # Rủi ro chính
    confidence: float  # Độ tin cậy (0-1)
    actions: List[Dict[str, Any]]  # Các hành động cụ thể
    estimated_cost: float
    estimated_revenue: float
    estimated_profit: float
    time_horizon: str  # "short_term", "medium_term", "long_term"


class StrategyEngine:
    """
    Strategic Reasoning Engine: Tạo và so sánh các phương án chiến lược.
    
    Nhận input:
    - Kết quả từ các model (forecast, delay risk, churn, RL policy)
    - Bối cảnh: mục tiêu kinh doanh (min cost, max service level, balance)
    
    Tạo ra:
    - 2-5 phương án chiến lược
    - So sánh ưu/nhược
    - Tính chi phí, rủi ro, lợi nhuận
    """
    
    def __init__(self):
        self.strategies = []
    
    def generate_strategies(
        self,
        model_results: Dict[str, Any],
        business_context: Dict[str, Any],
        objectives: List[str] = None
    ) -> List[Strategy]:
        """
        Tạo các phương án chiến lược.
        
        Args:
            model_results: Dict với kết quả từ các models
                {
                    'forecast': {...},
                    'delay_risk': {...},
                    'churn': {...},
                    'rl_policy': {...}
                }
            business_context: Context kinh doanh
                {
                    'current_inventory': {...},
                    'warehouses': [...],
                    'weather_forecast': {...},
                    'season': 'summer',
                    'region': 'VN'
                }
            objectives: List mục tiêu ['min_cost', 'max_service', 'balance']
            
        Returns:
            List of Strategy objects
        """
        if objectives is None:
            objectives = ['balance']
        
        strategies = []
        
        # Strategy A: Aggressive Inventory (Tăng tồn kho khu vực X trước mùa mưa)
        strategy_a = self._create_strategy_a(model_results, business_context, objectives)
        strategies.append(strategy_a)
        
        # Strategy B: Balanced Distribution (Dàn đều tồn kho + tăng lead time buffer)
        strategy_b = self._create_strategy_b(model_results, business_context, objectives)
        strategies.append(strategy_b)
        
        # Strategy C: Customer Segmentation (Ưu tiên đơn hàng theo phân khúc VIP)
        strategy_c = self._create_strategy_c(model_results, business_context, objectives)
        strategies.append(strategy_c)
        
        # Strategy D: Cost Optimization (Tối ưu chi phí)
        if 'min_cost' in objectives:
            strategy_d = self._create_strategy_d(model_results, business_context, objectives)
            strategies.append(strategy_d)
        
        # Strategy E: Service Level Maximization (Tối đa service level)
        if 'max_service' in objectives:
            strategy_e = self._create_strategy_e(model_results, business_context, objectives)
            strategies.append(strategy_e)
        
        self.strategies = strategies
        return strategies
    
    def _create_strategy_a(
        self,
        model_results: Dict,
        context: Dict,
        objectives: List[str]
    ) -> Strategy:
        """Strategy A: Aggressive Inventory (Tăng tồn kho khu vực X trước mùa mưa)."""
        forecast = model_results.get('forecast', {})
        delay_risk = model_results.get('delay_risk', {})
        weather = context.get('weather_forecast', {})
        
        # Tính toán KPI
        current_inventory = sum(context.get('current_inventory', {}).values())
        target_increase = 0.3  # Tăng 30%
        new_inventory = current_inventory * (1 + target_increase)
        
        # Chi phí
        inventory_cost = new_inventory * 10.0  # $10 per unit
        holding_cost = new_inventory * 0.1 * 30  # $0.1 per unit per day, 30 days
        
        # Lợi ích
        # Giảm stockout risk
        stockout_reduction = 0.2  # Giảm 20% stockout
        revenue_protection = forecast.get('expected_revenue', 100000) * stockout_reduction * 0.1
        
        # Giảm delay risk
        delay_reduction = delay_risk.get('risk_score', 0.3) * 0.15  # Giảm 15% delay risk
        delay_cost_savings = delay_reduction * 5000  # $5000 per 1% delay reduction
        
        estimated_revenue = forecast.get('expected_revenue', 100000) + revenue_protection
        estimated_cost = inventory_cost + holding_cost
        estimated_profit = estimated_revenue - estimated_cost + delay_cost_savings
        
        # Confidence
        confidence = 0.75 if weather.get('precipitation_forecast', 0) > 20 else 0.6
        
        return Strategy(
            id='strategy_a',
            name='Tăng Tồn Kho Khu Vực X Trước Mùa Mưa',
            description=(
                "Chiến lược này đề xuất tăng tồn kho lên 30% tại các khu vực có nguy cơ mưa lớn "
                "trong 2-4 tuần tới. Mục tiêu là giảm thiểu rủi ro stockout và delay khi thời tiết "
                "xấu ảnh hưởng đến logistics. Chiến lược phù hợp khi forecast cho thấy nhu cầu cao "
                "và weather forecast dự báo mưa lớn."
            ),
            kpis={
                'inventory_level': float(new_inventory),
                'inventory_increase_pct': 30.0,
                'stockout_risk_reduction': float(stockout_reduction * 100),
                'delay_risk_reduction': float(delay_reduction * 100),
                'service_level_improvement': 5.0  # +5%
            },
            risks=[
                "Rủi ro overstocking nếu forecast không chính xác",
                "Chi phí holding inventory tăng",
                "Vốn bị 'đóng băng' trong inventory"
            ],
            confidence=confidence,
            actions=[
                {
                    'type': 'increase_inventory',
                    'warehouse': 'warehouse_x',
                    'product': 'product_a',
                    'quantity': int(current_inventory * 0.3),
                    'timeline': '2_weeks'
                },
                {
                    'type': 'monitor_weather',
                    'location': context.get('region', 'VN'),
                    'alert_threshold': 20  # mm precipitation
                }
            ],
            estimated_cost=estimated_cost,
            estimated_revenue=estimated_revenue,
            estimated_profit=estimated_profit,
            time_horizon='short_term'
        )
    
    def _create_strategy_b(
        self,
        model_results: Dict,
        context: Dict,
        objectives: List[str]
    ) -> Strategy:
        """Strategy B: Balanced Distribution (Dàn đều tồn kho + tăng lead time buffer)."""
        forecast = model_results.get('forecast', {})
        delay_risk = model_results.get('delay_risk', {})
        
        # Tính toán
        current_inventory = sum(context.get('current_inventory', {}).values())
        warehouses = context.get('warehouses', [])
        n_warehouses = len(warehouses) if warehouses else 3
        
        # Dàn đều inventory
        balanced_inventory = current_inventory / n_warehouses
        
        # Tăng lead time buffer
        current_lead_time = context.get('avg_lead_time', 3)  # days
        new_lead_time = current_lead_time * 1.2  # Tăng 20%
        
        # Chi phí
        redistribution_cost = current_inventory * 0.05  # 5% cost để redistribute
        holding_cost = balanced_inventory * 0.1 * 30 * n_warehouses
        
        # Lợi ích
        # Giảm delay risk nhờ lead time buffer
        delay_reduction = delay_risk.get('risk_score', 0.3) * 0.1
        delay_cost_savings = delay_reduction * 5000
        
        # Cải thiện service level nhờ balanced distribution
        service_improvement = 0.03  # +3%
        revenue_improvement = forecast.get('expected_revenue', 100000) * service_improvement
        
        estimated_revenue = forecast.get('expected_revenue', 100000) + revenue_improvement
        estimated_cost = redistribution_cost + holding_cost
        estimated_profit = estimated_revenue - estimated_cost + delay_cost_savings
        
        confidence = 0.7
        
        return Strategy(
            id='strategy_b',
            name='Dàn Đều Tồn Kho + Tăng Lead Time Buffer',
            description=(
                "Chiến lược này đề xuất phân bổ lại tồn kho một cách đồng đều giữa các warehouses "
                "và tăng lead time buffer lên 20% để giảm thiểu rủi ro delay. Chiến lược phù hợp "
                "khi có nhiều warehouses và muốn cân bằng rủi ro giữa các khu vực."
            ),
            kpis={
                'inventory_per_warehouse': float(balanced_inventory),
                'lead_time_buffer_increase': 20.0,
                'delay_risk_reduction': float(delay_reduction * 100),
                'service_level_improvement': float(service_improvement * 100),
                'geographic_balance': 0.9  # 0.9 = very balanced
            },
            risks=[
                "Chi phí redistribution có thể cao",
                "Có thể không tối ưu cho từng khu vực cụ thể"
            ],
            confidence=confidence,
            actions=[
                {
                    'type': 'redistribute_inventory',
                    'warehouses': warehouses,
                    'target_balance': 0.9,
                    'timeline': '1_week'
                },
                {
                    'type': 'increase_lead_time_buffer',
                    'current_lead_time': current_lead_time,
                    'new_lead_time': new_lead_time,
                    'timeline': 'immediate'
                }
            ],
            estimated_cost=estimated_cost,
            estimated_revenue=estimated_revenue,
            estimated_profit=estimated_profit,
            time_horizon='medium_term'
        )
    
    def _create_strategy_c(
        self,
        model_results: Dict,
        context: Dict,
        objectives: List[str]
    ) -> Strategy:
        """Strategy C: Customer Segmentation (Ưu tiên đơn hàng theo phân khúc VIP)."""
        churn = model_results.get('churn', {})
        forecast = model_results.get('forecast', {})
        
        # Phân khúc khách hàng
        vip_customers = churn.get('high_value_customers', [])
        n_vip = len(vip_customers) if isinstance(vip_customers, list) else 100
        
        # Ưu tiên VIP
        vip_priority_boost = 0.3  # +30% priority
        vip_service_level = 0.98  # 98% service level cho VIP
        regular_service_level = 0.90  # 90% cho regular
        
        # Chi phí
        vip_inventory_cost = n_vip * 50.0  # $50 per VIP customer
        priority_handling_cost = n_vip * 10.0  # $10 per order
        
        # Lợi ích
        # Giảm churn của VIP customers
        churn_reduction = churn.get('churn_rate', 0.15) * 0.2  # Giảm 20% churn rate
        vip_lifetime_value = n_vip * 5000  # $5000 per VIP
        churn_savings = vip_lifetime_value * churn_reduction
        
        # Tăng revenue từ VIP
        vip_revenue_boost = forecast.get('expected_revenue', 100000) * 0.15  # +15%
        
        estimated_revenue = forecast.get('expected_revenue', 100000) + vip_revenue_boost
        estimated_cost = vip_inventory_cost + priority_handling_cost
        estimated_profit = estimated_revenue - estimated_cost + churn_savings
        
        confidence = 0.8 if n_vip > 50 else 0.6
        
        return Strategy(
            id='strategy_c',
            name='Ưu Tiên Đơn Hàng Theo Phân Khúc VIP',
            description=(
                "Chiến lược này đề xuất ưu tiên xử lý đơn hàng của khách hàng VIP (high-value customers) "
                "để giảm thiểu churn risk và tăng customer lifetime value. Chiến lược phù hợp khi "
                "churn model cho thấy có nhiều VIP customers có nguy cơ churn cao."
            ),
            kpis={
                'vip_customers': n_vip,
                'vip_service_level': float(vip_service_level * 100),
                'regular_service_level': float(regular_service_level * 100),
                'churn_reduction': float(churn_reduction * 100),
                'vip_revenue_boost': float(vip_revenue_boost)
            },
            risks=[
                "Có thể làm giảm service level cho regular customers",
                "Chi phí priority handling tăng"
            ],
            confidence=confidence,
            actions=[
                {
                    'type': 'prioritize_vip_orders',
                    'vip_customers': vip_customers[:10] if isinstance(vip_customers, list) else [],
                    'priority_boost': vip_priority_boost,
                    'timeline': 'immediate'
                },
                {
                    'type': 'allocate_vip_inventory',
                    'products': ['product_a', 'product_b'],
                    'quantity_per_vip': 10,
                    'timeline': '1_week'
                }
            ],
            estimated_cost=estimated_cost,
            estimated_revenue=estimated_revenue,
            estimated_profit=estimated_profit,
            time_horizon='long_term'
        )
    
    def _create_strategy_d(
        self,
        model_results: Dict,
        context: Dict,
        objectives: List[str]
    ) -> Strategy:
        """Strategy D: Cost Optimization."""
        forecast = model_results.get('forecast', {})
        
        # Tối ưu chi phí
        current_inventory = sum(context.get('current_inventory', {}).values())
        optimal_inventory = current_inventory * 0.85  # Giảm 15%
        
        # Chi phí giảm
        inventory_reduction = current_inventory - optimal_inventory
        cost_savings = inventory_reduction * 10.0  # $10 per unit
        
        # Rủi ro
        stockout_risk_increase = 0.05  # +5% stockout risk
        
        estimated_revenue = forecast.get('expected_revenue', 100000) * 0.98  # -2% do stockout
        estimated_cost = (optimal_inventory * 10.0) + (optimal_inventory * 0.1 * 30)
        estimated_profit = estimated_revenue - estimated_cost + cost_savings
        
        return Strategy(
            id='strategy_d',
            name='Tối Ưu Chi Phí',
            description="Chiến lược tối ưu chi phí bằng cách giảm inventory và tối ưu hóa operations.",
            kpis={
                'inventory_reduction': float(inventory_reduction),
                'cost_savings': float(cost_savings),
                'stockout_risk_increase': float(stockout_risk_increase * 100)
            },
            risks=["Tăng stockout risk", "Có thể ảnh hưởng service level"],
            confidence=0.65,
            actions=[{
                'type': 'reduce_inventory',
                'target_reduction': 15.0,
                'timeline': '2_weeks'
            }],
            estimated_cost=estimated_cost,
            estimated_revenue=estimated_revenue,
            estimated_profit=estimated_profit,
            time_horizon='medium_term'
        )
    
    def _create_strategy_e(
        self,
        model_results: Dict,
        context: Dict,
        objectives: List[str]
    ) -> Strategy:
        """Strategy E: Service Level Maximization."""
        forecast = model_results.get('forecast', {})
        
        # Tối đa service level
        current_inventory = sum(context.get('current_inventory', {}).values())
        target_inventory = current_inventory * 1.25  # Tăng 25%
        
        # Chi phí
        inventory_cost = target_inventory * 10.0
        holding_cost = target_inventory * 0.1 * 30
        
        # Lợi ích
        service_level_improvement = 0.08  # +8%
        revenue_improvement = forecast.get('expected_revenue', 100000) * service_level_improvement
        
        estimated_revenue = forecast.get('expected_revenue', 100000) + revenue_improvement
        estimated_cost = inventory_cost + holding_cost
        estimated_profit = estimated_revenue - estimated_cost
        
        return Strategy(
            id='strategy_e',
            name='Tối Đa Service Level',
            description="Chiến lược tối đa hóa service level bằng cách tăng inventory và cải thiện operations.",
            kpis={
                'inventory_increase': 25.0,
                'service_level_improvement': float(service_level_improvement * 100),
                'revenue_improvement': float(revenue_improvement)
            },
            risks=["Chi phí inventory tăng", "Rủi ro overstocking"],
            confidence=0.7,
            actions=[{
                'type': 'increase_inventory',
                'target_increase': 25.0,
                'timeline': '2_weeks'
            }],
            estimated_cost=estimated_cost,
            estimated_revenue=estimated_revenue,
            estimated_profit=estimated_profit,
            time_horizon='medium_term'
        )
    
    def compare_strategies(self, strategies: List[Strategy] = None) -> Dict[str, Any]:
        """
        So sánh các chiến lược.
        
        Returns:
            Comparison dict với rankings, trade-offs, recommendations
        """
        if strategies is None:
            strategies = self.strategies
        
        if not strategies:
            return {}
        
        # Rank theo profit
        ranked_by_profit = sorted(strategies, key=lambda s: s.estimated_profit, reverse=True)
        
        # Rank theo confidence
        ranked_by_confidence = sorted(strategies, key=lambda s: s.confidence, reverse=True)
        
        # Rank theo risk (thấp risk = tốt)
        ranked_by_risk = sorted(strategies, key=lambda s: len(s.risks))
        
        # Tính trade-offs
        trade_offs = []
        for i, s1 in enumerate(strategies):
            for s2 in strategies[i+1:]:
                trade_off = {
                    'strategy_1': s1.id,
                    'strategy_2': s2.id,
                    'profit_diff': s1.estimated_profit - s2.estimated_profit,
                    'confidence_diff': s1.confidence - s2.confidence,
                    'risk_diff': len(s1.risks) - len(s2.risks)
                }
                trade_offs.append(trade_off)
        
        # Recommendation
        best_strategy = ranked_by_profit[0] if ranked_by_profit else None
        
        return {
            'ranked_by_profit': [s.id for s in ranked_by_profit],
            'ranked_by_confidence': [s.id for s in ranked_by_confidence],
            'ranked_by_risk': [s.id for s in ranked_by_risk],
            'best_strategy': best_strategy.id if best_strategy else None,
            'trade_offs': trade_offs,
            'summary': {
                'total_strategies': len(strategies),
                'highest_profit': best_strategy.estimated_profit if best_strategy else 0,
                'highest_confidence': ranked_by_confidence[0].confidence if ranked_by_confidence else 0
            }
        }
    
    def get_strategy_details(self, strategy_id: str) -> Optional[Strategy]:
        """Lấy chi tiết một chiến lược."""
        for strategy in self.strategies:
            if strategy.id == strategy_id:
                return strategy
        return None

