# 🏗️ OS ARCHITECTURE

**Mục đích:** Mô tả kiến trúc của Supply Chain AI Operating System (V9).

---

## 📊 KIẾN TRÚC TỔNG THỂ

```
┌─────────────────────────────────────────────────────────────┐
│                    OS ORCHESTRATOR                           │
│  • Task Scheduling                                           │
│  • Dependency Management                                     │
│  • Decision Logging                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   SERVICES   │ │  GOVERNANCE  │ │    SAFETY    │
│              │ │              │ │              │
│ • ETL        │ │ • Policy     │ │ • Anomaly    │
│ • Models     │ │   Engine     │ │   Detection  │
│ • RL         │ │ • Compliance │ │ • Risk Check │
│ • Cognitive  │ │              │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            CONTROL CENTER (Human-in-the-Loop)                │
│  • Pending Actions                                            │
│  • Approve/Reject                                             │
│  • Reasoning Log                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 COMPONENTS

### 1. OS Orchestrator

**File:** `core/os_orchestrator.py`

**Chức năng:**
- Quản lý tasks và scheduling
- Dependency graph
- Decision logging
- Task execution

**Tasks:**
- ETL (daily 02:00)
- Feature Store (daily 03:00)
- Model Training (weekly Monday 01:00)
- Inference (daily 04:00)
- Cognitive Strategy (daily 05:00)
- Digital Twin (on-demand)

### 2. Policy Engine

**File:** `core/governance/policy_engine.py`

**Chức năng:**
- Load policies từ YAML
- Check action compliance
- Log violations
- Mode-specific rules

**Policies:**
- Inventory limits
- Pricing limits
- Cost limits
- Safety rules
- Compliance rules

### 3. Safety Checker

**File:** `core/safety/safety_checks.py`

**Chức năng:**
- Anomaly detection
- Action safety check
- Risk level assessment
- Blacklist enforcement

### 4. Cognitive Layer (V8)

**Files:**
- `modules/cognitive/strategy_engine.py`
- `modules/cognitive/planner_agent.py`

**Chức năng:**
- Generate strategies
- Compare alternatives
- Generate recommendations
- Policy compliance check

---

## 🔄 WORKFLOW

### Daily Workflow

```
02:00 - ETL
  ↓
03:00 - Feature Store
  ↓
04:00 - Inference (nếu models đã train)
  ↓
05:00 - Cognitive Strategy
  ↓
06:00 - Control Center Review
```

### Weekly Workflow

```
Monday 01:00 - Train Models
  ↓
Monday 02:00 - Feature Store (nếu cần)
  ↓
Rest of week - Daily workflow
```

### On-Demand

- Digital Twin Simulation
- What-If Analysis
- Manual Task Execution

---

## 📁 FILE STRUCTURE

```
core/
├── os_orchestrator.py      # Main orchestrator
├── os_config.yaml          # Configuration
├── governance/
│   ├── policy_engine.py    # Policy checking
│   └── policies.yaml       # Policy rules
└── safety/
    └── safety_checks.py    # Safety checks

modules/
└── cognitive/
    ├── strategy_engine.py  # Strategy generation
    └── planner_agent.py    # Action planning

app/
├── routers/
│   ├── os_api.py          # OS endpoints
│   └── cognitive_api.py   # Cognitive endpoints
└── templates/
    └── control_center.html # Control Center UI

logs/
├── os_decisions/          # Decision logs
└── audit/                 # Audit logs
```

---

## 🔐 SECURITY & SAFETY

### Safety Layers

1. **Data Anomaly Detection**
   - Z-score threshold: 3.0
   - Auto-flag suspicious inputs

2. **Action Safety Check**
   - Dangerous action detection
   - Extreme value checks
   - Cost limits

3. **Policy Compliance**
   - Pre-execution check
   - Mode-specific rules
   - Approval requirements

4. **Human Review**
   - High-risk actions
   - Policy violations
   - Anomalies

---

## 📊 MODES

### Advisory Mode

- AI chỉ đề xuất
- Mọi action cần approval
- Phù hợp cho testing và validation

### Hybrid Mode

- AI tự hành động trong vùng an toàn
- Action quan trọng cần approval
- Phù hợp cho production với supervision

### Autonomous Mode

- AI hành động toàn diện (trong policy)
- Chỉ cần approval cho actions rất lớn
- Phù hợp cho mature system

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

