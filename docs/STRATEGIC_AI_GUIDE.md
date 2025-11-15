# 🧠 STRATEGIC AI GUIDE

**Mục đích:** Hướng dẫn sử dụng Cognitive AI (V8) để tạo và so sánh các chiến lược.

---

## 🎯 TỔNG QUAN

Strategic AI (V8) giúp:
- Tạo nhiều phương án chiến lược
- So sánh ưu/nhược điểm
- Đề xuất hành động cụ thể
- Giải thích rõ ràng quyết định

---

## 📊 WORKFLOW

### 1. Chuẩn bị Input

**Model Results:**
```python
model_results = {
    'forecast': {
        'expected_revenue': 100000,
        'demand_forecast': [100, 120, 110]
    },
    'delay_risk': {
        'risk_score': 0.3,
        'high_risk_orders': 50
    },
    'churn': {
        'churn_rate': 0.15,
        'high_value_customers': ['customer_001', 'customer_002']
    }
}
```

**Business Context:**
```python
business_context = {
    'current_inventory': {'product_a': 1000, 'product_b': 2000},
    'warehouses': ['warehouse_hn', 'warehouse_hcm'],
    'weather_forecast': {
        'precipitation_forecast': 50,
        'wind_forecast': 25
    },
    'season': 'summer',
    'region': 'VN'
}
```

### 2. Generate Strategies

```python
from modules.cognitive import StrategyEngine

engine = StrategyEngine()
strategies = engine.generate_strategies(
    model_results=model_results,
    business_context=business_context,
    objectives=['balance']  # hoặc ['min_cost', 'max_service']
)
```

### 3. Compare Strategies

```python
comparison = engine.compare_strategies(strategies)

print(f"Best strategy: {comparison['best_strategy']}")
print(f"Ranked by profit: {comparison['ranked_by_profit']}")
print(f"Ranked by confidence: {comparison['ranked_by_confidence']}")
```

### 4. Get Recommendations

```python
from modules.cognitive import PlannerAgent

planner = PlannerAgent()
recommendations = planner.generate_recommendations(
    strategies=strategies,
    comparison=comparison,
    context=business_context
)

print(recommendations['reasoning'])
for rec in recommendations['recommendations']:
    print(f"- {rec['description']}")
```

---

## 📈 STRATEGY TYPES

### Strategy A: Aggressive Inventory

**Khi nào dùng:**
- Weather forecast dự báo mưa lớn
- Forecast cho thấy nhu cầu tăng
- Delay risk cao

**Đặc điểm:**
- Tăng inventory 20-30%
- Chi phí cao
- Giảm stockout và delay risk

### Strategy B: Balanced Distribution

**Khi nào dùng:**
- Có nhiều warehouses
- Muốn cân bằng rủi ro
- Cần ổn định

**Đặc điểm:**
- Dàn đều inventory
- Tăng lead time buffer
- Chi phí trung bình

### Strategy C: Customer Segmentation

**Khi nào dùng:**
- Có nhiều VIP customers
- Churn risk cao
- Muốn tăng retention

**Đặc điểm:**
- Ưu tiên VIP
- Tăng service level cho VIP
- Giảm churn

---

## 🎯 OBJECTIVES

### Min Cost

Tối ưu chi phí:
- Giảm inventory
- Tối ưu operations
- Trade-off: Tăng stockout risk

### Max Service

Tối đa service level:
- Tăng inventory
- Cải thiện operations
- Trade-off: Tăng chi phí

### Balance

Cân bằng:
- Cân nhắc cả cost và service
- Phù hợp cho hầu hết trường hợp

---

## 📊 KPI METRICS

Mỗi strategy có các KPI:

- **Financial:**
  - Estimated Cost
  - Estimated Revenue
  - Estimated Profit

- **Operational:**
  - Inventory Level
  - Service Level
  - Stockout Risk
  - Delay Risk

- **Customer:**
  - Churn Reduction
  - Customer Satisfaction

---

## ⚠️ RISKS

Mỗi strategy có risks:

- **Overstocking:** Inventory quá cao
- **Stockout:** Hết hàng
- **Cost Overrun:** Chi phí vượt dự kiến
- **Service Degradation:** Service level giảm

---

## ✅ BEST PRACTICES

1. **Review Multiple Strategies:**
   - Không chỉ chọn strategy đầu tiên
   - So sánh tất cả options
   - Xem trade-offs

2. **Check Confidence:**
   - Confidence > 0.7: Có thể tin cậy
   - Confidence < 0.7: Cần cẩn thận

3. **Consider Context:**
   - Weather conditions
   - Seasonality
   - Business priorities

4. **Monitor Results:**
   - Track actual vs projected
   - Learn from outcomes
   - Adjust strategies

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

