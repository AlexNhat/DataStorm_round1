# 🚀 V8 + V9 QUICK START GUIDE

**Supply Chain AI - Cognitive + Autonomous OS**

---

## 📦 CÀI ĐẶT

```bash
pip install -r requirements.txt
```

---

## 🎯 V8 - COGNITIVE AI

### Generate Strategies

```python
from modules.cognitive import StrategyEngine

engine = StrategyEngine()
strategies = engine.generate_strategies(
    model_results={
        'forecast': {'expected_revenue': 100000},
        'delay_risk': {'risk_score': 0.3},
        'churn': {'churn_rate': 0.15}
    },
    business_context={
        'current_inventory': {'product_a': 1000},
        'warehouses': ['warehouse_hn']
    },
    objectives=['balance']
)

comparison = engine.compare_strategies(strategies)
```

### Get Recommendations

```python
from modules.cognitive import PlannerAgent

planner = PlannerAgent()
recommendations = planner.generate_recommendations(
    strategies=strategies,
    comparison=comparison
)

print(recommendations['reasoning'])
```

### API Endpoints

```bash
# Generate strategies
curl -X POST http://127.0.0.1:8000/v8/strategies/generate \
  -H "Content-Type: application/json" \
  -d @strategy_request.json

# View dashboard
http://127.0.0.1:8000/v8/dashboard
```

---

## 🎯 V9 - AUTONOMOUS OS

### Check Action

```python
from core.governance import PolicyEngine

policy_engine = PolicyEngine()
result = policy_engine.check_action(
    action={
        'type': 'increase_inventory',
        'params': {'change_pct': 25},
        'estimated_cost': 30000,
        'confidence': 0.75
    },
    mode='hybrid'
)

print(result['compliant'])
print(result['requires_approval'])
```

### Run OS Orchestrator

```python
from core.os_orchestrator import OSOrchestrator

orchestrator = OSOrchestrator()
orchestrator.start()  # Runs in background
```

### API Endpoints

```bash
# Check action
curl -X POST http://127.0.0.1:8000/os/actions/check \
  -H "Content-Type: application/json" \
  -d '{
    "action": {"type": "increase_inventory", ...},
    "mode": "hybrid"
  }'

# Approve action
curl -X POST http://127.0.0.1:8000/os/actions/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "action_123",
    "approved_by": "user_001"
  }'

# View control center
http://127.0.0.1:8000/os/control-center
```

---

## 📚 DOCUMENTATION

- **Kế hoạch:** `docs/ML_IMPROVEMENTS_V8_V9_PLAN.md`
- **Tổng quan:** `docs/ML_SYSTEM_V8_V9_OVERVIEW.md`
- **OS Architecture:** `docs/OS_ARCHITECTURE.md`
- **Control Center:** `docs/CONTROL_CENTER_GUIDE.md`
- **Strategic AI:** `docs/STRATEGIC_AI_GUIDE.md`
- **Audit:** `docs/AUDIT_OVERVIEW.md`
- **Ethics:** `docs/ETHICS_AND_COMPLIANCE.md`

---

**Phiên bản:** V8.0.0 + V9.0.0  
**Ngày:** 2024

