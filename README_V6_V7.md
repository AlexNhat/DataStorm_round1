# 🚀 V6 + V7 QUICK START GUIDE

**Supply Chain AI - Adaptive Self-Learning + Digital Twin**

---

## 📦 CÀI ĐẶT

```bash
pip install -r requirements.txt
```

---

## 🎯 V6 - SELF-LEARNING AI

### Sử dụng Self-Learning Loop

```python
from modules.self_learning import SelfLearningLoop

# Khởi tạo
loop = SelfLearningLoop(
    model_name='logistics_delay',
    model_path='models/logistics_delay_model.pkl'
)

# Quan sát dữ liệu mới
loop.observe(X_new, y_actual)

# Kiểm tra trạng thái
status = loop.get_status()
print(status)
```

### API Endpoints

```bash
# Quan sát dữ liệu
curl -X POST http://127.0.0.1:8000/v6/observe \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "logistics_delay",
    "features": [0.5, 0.3, 0.8, ...],
    "actual_value": 1.0
  }'

# Lấy trạng thái
curl http://127.0.0.1:8000/v6/status/logistics_delay
```

---

## 🎯 V7 - DIGITAL TWIN

### Chạy Simulation

```python
from engines.digital_twin import DigitalTwinEngine

# Khởi tạo
engine = DigitalTwinEngine()

# Setup warehouses và routes
warehouses = [
    {
        'warehouse_id': 'wh1',
        'location': {'lat': 10.0, 'lon': 106.0},
        'inventory': {'product_1': 100, 'product_2': 200},
        'capacity': 10000
    }
]

routes = [
    {
        'route_id': 'route1',
        'origin': 'wh1',
        'destination': 'customer_location',
        'distance_km': 50.0
    }
]

# Initialize
engine.initialize(warehouses, routes)

# Chạy simulation (1 tuần)
results = engine.run_simulation(duration_hours=168)

# Xem kết quả
for step in results:
    print(step['state_summary'])
```

### What-If Analysis

```python
from app.services.what_if_service import WhatIfAnalyzer

analyzer = WhatIfAnalyzer(engine)

# Scenario: Mưa tăng 40%
scenario = {
    'type': 'weather_change',
    'multiplier': 1.4
}

results = analyzer.analyze(scenario)
print(results['comparison'])
print(results['recommendations'])
```

### Natural Language Query

```python
# Hỏi bằng tiếng Việt
results = analyzer.analyze_natural_language(
    "Nếu mưa tăng 40%, giao trễ tăng bao nhiêu?"
)
```

### API Endpoints

```bash
# Chạy simulation
curl -X POST http://127.0.0.1:8000/v7/digital-twin/simulate \
  -H "Content-Type: application/json" \
  -d @simulation_request.json

# What-if analysis
curl -X POST http://127.0.0.1:8000/v7/what-if/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": {
      "type": "weather_change",
      "multiplier": 1.4
    }
  }'

# Natural language
curl -X POST http://127.0.0.1:8000/v7/what-if/natural-language \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Nếu mưa tăng 40%, giao trễ tăng bao nhiêu?"
  }'
```

---

## 🤖 RL TRAINING

### Train Inventory Policy

```bash
python rl/train_multiagent_rl.py \
  --algorithm ppo \
  --agents inventory \
  --timesteps 100000
```

### Evaluate Policy

```bash
python rl/evaluate_policies.py \
  --policy rl/policies/saved/inventory_ppo \
  --env inventory \
  --episodes 10
```

---

## 📚 DOCUMENTATION

- **Kế hoạch chi tiết:** `docs/ML_IMPROVEMENTS_V6_V7.md`
- **Tóm tắt triển khai:** `docs/V6_V7_IMPLEMENTATION_SUMMARY.md`
- **API Docs:** http://127.0.0.1:8000/docs

---

## 🎯 NEXT STEPS

1. **Train models** (nếu chưa có):
   ```bash
   python scripts/train_model_logistics_delay.py
   python scripts/train_model_revenue_forecast.py
   python scripts/train_model_churn.py
   ```

2. **Start server:**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Test APIs:**
   - V6: http://127.0.0.1:8000/v6/status/logistics_delay
   - V7: http://127.0.0.1:8000/v7/digital-twin/simulate

---

**Phiên bản:** V6.0.0 + V7.0.0  
**Ngày:** 2024

