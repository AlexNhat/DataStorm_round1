# Tổng quan

Tài liệu này mô tả kiến trúc dự án **DataStorm** theo cấu trúc thư mục thực tế (snapshot ngày 2025‑11‑15). Nội dung bao gồm cây thư mục, vai trò từng thư mục, mô tả chi tiết file trọng yếu và các luồng vận hành (data/model/UI/logging).

---

## Cấu trúc thư mục (tree view)

```
DataStorm/
├── agents/
│   └── environment/
├── alerts/
├── app/
│   ├── routers/
│   ├── services/
│   ├── static/
│   └── templates/
├── core/
├── data/
├── docs/
├── docs_site/
├── engines/
├── fix_logs/
├── logs/
├── models/
├── modules/
├── monitoring/
├── notebooks/
├── rl/
├── scenarios/
├── scripts/
├── tests/
└── visual_regression/
```

---

## Chi tiết từng thư mục

### 📁 agents/
- **Vai trò:** chứa môi trường mô phỏng multi-agent/RL (inventory, supply chain, transport).  
- **Nội dung:** `environment/{inventory_env.py, supply_chain_env.py, transport_env.py}` cùng `__init__.py`.  
- **Chức năng:** mô tả state/action/reward để thử nghiệm RL (ví dụ Inventory Optimizer RL).  
- **Luồng sử dụng:** scripts trong `rl/` và `scripts/train_rl_inventory.py` có thể import để mô phỏng trước khi triển khai.

### 📁 alerts/
- **Vai trò:** gửi cảnh báo (email/telegram) khi monitoring phát hiện bất thường.  
- **Nội dung:** `alert_email.py`, `alert_telegram.py`.  
- **Chức năng:** build payload (severity, message) và gọi API SMTP/Telegram.  
- **Luồng:** `monitoring/*.py` gọi khi drift/latency vượt ngưỡng.

### 📁 app/
- **Vai trò:** FastAPI application chính (routers, services, templates, static).  
- **Nội dung:** 
  - `main.py` bootstrap app.  
  - `routers/` (dashboard, cognitive_api, ml_api, os_api, …).  
  - `services/` (analytics, data loaders, ml_service).  
  - `static/` (css/js/images) và `templates/` (UI).  
- **Chức năng:** xử lý tất cả request UI/API.  
- **Luồng:** client → router → service/template → response.

### 📁 core/
- **Vai trò:** chứa cấu hình và orchestrator cho OS control center.  
- **Nội dung:** `governance/policies.yaml`, `policy_engine.py`, `safety/safety_checks.py`, `os_config.yaml`, `os_orchestrator.py`.  
- **Chức năng:** định nghĩa policy rules, safety guardrails, orchestrator logic.  
- **Luồng:** `os_api.py` nạp policy để quyết định approve/reject action.

### 📁 data/
- **Vai trò:** nơi lưu dataset raw + merged + registry.  
- **Nội dung:** `DataCoSupplyChainDataset.csv`, `geocoded_weather.csv`, `merged/supplychain_weather_merged_global.csv`, feature store parquet, `model_registry.json`.  
- **Chức năng:** input cho pipeline ETL, training và UI (registry).  
- **Luồng:** scripts/modules đọc dataset; dashboards đọc `model_registry.json`.

### 📁 docs/
- **Vai trò:** tài liệu kỹ thuật (guides, audits, model cards).  
- **Nội dung:** 40+ Markdown bao gồm `AI_MODELS_DETAIL.md`, `PROJECT_VIEWS_DETAIL.md`, `PROJECT_STRUCTURE.md` (file này).  
- **Chức năng:** onboarding, compliance, kiến trúc.  
- **Luồng:** MkDocs (`docs_site/`) build site từ thư mục này.

### 📁 docs_site/
- **Vai trò:** cấu hình MkDocs (Material theme) để publish docs.  
- **Nội dung:** `mkdocs.yml`, `docs/index.md` và các chuyên mục (models/, pipeline/, data/, ...).  
- **Luồng:** `scripts/build_docs.sh`, `scripts/serve_docs.sh`, workflow `deploy_docs.yml` dùng để build/deploy docs.

### 📁 engines/
- **Vai trò:** engine Digital Twin mô phỏng supply chain.  
- **Nội dung:** `digital_twin/{__init__.py, runner.py, scenario_config.json}`.  
- **Chức năng:** chạy simulation dựa trên scenario; `digital_twin_api.py` gọi.  
- **Luồng:** Control Center hoặc what-if API có thể kích hoạt engine này để dự báo ảnh hưởng.

### 📁 fix_logs/
- **Vai trò:** lưu các báo cáo sửa lỗi (markdown) cho từng lần fix.  
- **Nội dung:** `ui_docfiles_notebooks_report.md`, …  
- **Luồng:** tham khảo khi cần lịch sử fix UI/Backend; không dùng runtime.

### 📁 logs/
- **Vai trò:** toàn bộ log runtime.  
- **Nội dung:** 
  - `warnings/<model>_warnings.log` (chuẩn `timestamp | WARNING | ...`).  
  - `inference/<model>_inference.log`.  
  - legacy `audit/`, `os_decisions/`.  
- **Chức năng:** cung cấp feed cho cognitive dashboard, audit.  
- **Luồng:** `modules/logging_utils.py` ghi log; `/v8/dashboard` đọc log để hiển thị.

### 📁 models/
- **Vai trò:** artefact lưu mô hình đã train.  
- **Nội dung:** 
  - `inventory_rl/global/inventory_rl_global.pkl`, `feature_schema.json`.  
  - `forecast/global/region_model/*.pkl`.  
  - `late_delivery/global/late_delivery_global.pkl`.  
  - `pricing/global/pricing_elasticity.pkl`.  
  - legacy models (`churn`, `logistics_delay`, `revenue_forecast`).  
- **Luồng:** `app/services/ml_service` load model tại runtime; training scripts ghi vào đây.

### 📁 modules/
- **Vai trò:** thư viện dùng chung (cognitive, data_pipeline, logging utilities, self-learning...).  
- **Nội dung:** 
  - `cognitive/strategy_engine.py`, `planner_agent.py`.  
  - `data_pipeline/merge_supply_weather.py`, `global_dataset_loader.py`.  
  - `logging_utils.py`.  
  - `self_learning`, `meta_learning`, `continual_learning`, `self_healing`.  
- **Luồng:** routers/services/scripts import từ đây.

### 📁 monitoring/
- **Vai trò:** scripts kiểm soát drift/latency/weather completeness/registry sync.  
- **Nội dung:** `monitor_data_drift.py`, `monitor_model_drift.py`, `monitor_latency.py`, `monitor_weather_missing.py`, `monitor_registry_sync.py`.  
- **Luồng:** chạy theo lịch (cron/GitHub Action) → gọi alerts → trigger auto retrain.

### 📁 notebooks/
- **Vai trò:** Jupyter notebooks tham khảo, thử nghiệm.  
- **Nội dung:** notebook skeletons (không liệt kê chi tiết).  
- **Luồng:** không chạy trong production, dùng cho data exploration.

### 📁 rl/
- **Vai trò:** chứa policy, config và scripts RL nâng cao.  
- **Nội dung:** thư mục `policies/`, script `evaluate_policies.py`, `train_multiagent_rl.py`.  
- **Luồng:** training RL chi tiết; liên hệ với `agents/` và `scripts/train_rl_inventory.py`.

### 📁 scenarios/
- **Vai trò:** JSON mô tả các tình huống what-if (nhu cầu tăng, cổng tắc, bão…).  
- **Nội dung:** `demand_surge_30pct.json`, `holiday_season_spike.json`, `port_congestion.json`, `supplier_disruption.json`, `weather_storm.json`.  
- **Luồng:** `digital_twin_api.py`, `what_if_api.py` nạp scenario này để mô phỏng.

### 📁 scripts/
- **Vai trò:** CLI cho training, ETL, docs, testing.  
- **Nội dung nổi bật:** 
  - Training: `train_rl_inventory.py`, `train_forecast.py`, `train_late_delivery.py`, `train_pricing_elasticity.py`, `train_model_*`.  
  - Automation: `auto_retrain_global.py`, `generate_model_warnings.py`, `run_inference_samples.py`, `generate_dashboard_metrics.py`.  
  - Data pipeline: `merge_supplychain_weather.py`, `preprocess_and_build_feature_store.py`.  
- **Luồng:** DevOps hoặc monitoring gọi các script này; log/metrics ghi vào `results/` và `logs/`.

### 📁 tests/
- **Vai trò:** đảm bảo chất lượng (unit/integration/regression/UI).  
- **Nội dung:** 
  - `unit/test_data_validation.py`, `test_feature_engineering.py`.  
  - `integration/test_forecast_inference.py`, `test_late_delivery_end_to_end.py`.  
  - `regression/test_model_metrics_threshold.py`.  
  - `ui/test_ui_*` và snapshots.  
- **Luồng:** chạy với `pytest`; CI references `tests/README_TESTING.md`.

### 📁 visual_regression/
- **Vai trò:** baseline screenshot + test script để phát hiện sai lệch UI.  
- **Nội dung:** `baseline/dashboard.png`, `test_visual_regression.py`.  
- **Luồng:** pipeline UI regression chạy script này sau khi render trang.

---

## Chi tiết file quan trọng

### Backend & Registry
#### 📄 app/main.py
- **Loại:** Python entry point.  
- **Mục đích:** khởi tạo FastAPI, include routers, mount static/templates.  
- **Luồng:** Uvicorn import app.main → tạo FastAPI instance → serve.

#### 📄 data/model_registry.json
- **Loại:** JSON metadata.  
- **Mục đích:** registry cho toàn bộ mô hình.  
- **Chức năng:** chứa name, version, status, dataset_version, used_in_pipeline, last_inference_call, warnings_count, artifacts, last_training_run.  
- **Luồng:** training scripts và logging_utils cập nhật; `/dashboard/models`, `/v8/dashboard`, `/api/models` đọc.

### Routers
#### 📄 app/routers/dashboard.py
- **Loại:** Router (Python).  
- **Mục đích:** render `/dashboard`, cung cấp API JSON `/dashboard/api/*`.  
- **Chức năng:** load dữ liệu supply & weather, tính KPI, top products/countries, time-series.  
- **Luồng:** GET `/dashboard` → get_cached_data() → template `dashboard.html`.  
- **Liên kết:** `app/services/analytics.py`, `data_loader.py`, templates/dashboard.html.

#### 📄 app/routers/cognitive_api.py
- **Mục đích:** cung cấp dữ liệu cho `/v8/dashboard`.  
- **Chức năng:** `_build_model_cards()` đọc registry, `_build_log_items()` parse `logs/warnings`, generate strategy cards via `modules/cognitive`.  
- **Luồng:** GET `/v8/dashboard`/`data` → snapshot → template `cognitive_dashboard.html`.  
- **Liên kết:** `modules/cognitive`, `logs/`, `data/model_registry.json`.

#### 📄 app/routers/os_api.py
- **Mục đích:** Control Center API (`/os/control-center`, `/os/actions/pending|approve|history`).  
- **Chức năng:** manage action queues, policy checks, history aggregations.  
- **Luồng:** Control Center JS fetch → router → orchestrator/policy engine.

#### 📄 app/routers/ml_api.py
- **Mục đích:** ML inference endpoints.  
- **Chức năng:** Pydantic models `LogisticsDelayRequest`, `InventoryRLRequest`, `RevenueForecastRequest`, `PricingElasticityRequest`, `ChurnRequest`. Endpoints call `ml_service` functions (`predict_logistics_delay`, `predict_revenue`, `predict_inventory_rl`, `predict_pricing_elasticity`, `predict_churn`).  
- **Luồng:** POST `/ml/...` → service → logging_utils (inference & warning).  
- **Liên kết:** `app/services/ml_service.py`, `logs/inference`, `modules/logging_utils`.

#### 📄 app/routers/models_registry.py / models_metrics.py
- **Chức năng:** render `/dashboard/models`, `/dashboard/models/{slug}`, `/dashboard/metrics`, `/dashboard/metrics/<model>`, API `/api/models`.  
- **Dữ liệu:** `data/model_registry.json`, `results/metrics/global_dashboard_metrics.json`.

#### 📄 app/routers/ai_strategy_api.py / digital_twin_api.py / what_if_api.py
- **Chức năng:** API cho chiến lược AI, digital twin, what-if scenario (dùng `engines/`, `scenarios/`).

### Services
#### 📄 app/services/ml_service.py
- **Loại:** Python service.  
- **Mục đích:** load models, preprocess payload, log inference/warnings.  
- **Chức năng:** 
  - `MLModelService` cho legacy models (logistics delay, revenue, churn).  
  - Helper `predict_inventory_rl`, `predict_pricing_elasticity`.  
  - Ghi log bằng `log_inference`, update registry.  
- **Luồng:** API request → service → model → log → response.  
- **Liên kết:** `models/`, `modules/logging_utils.py`.

#### 📄 app/services/analytics.py
- **Mục đích:** tính KPI, top sản phẩm, weather stats, advanced metrics.  
- **Luồng:** `dashboard.py` gọi cho mỗi request `/dashboard`.

#### 📄 app/services/model_registry.py
- **Mục đích:** helper cho trang Model Catalog (caching, formatting).  
- **Luồng:** routers/models_registry đọc metadata (legacy fallback).

### Modules / Pipeline
#### 📄 modules/data_pipeline/merge_supply_weather.py
- **Loại:** ETL Python.  
- **Mục đích:** hợp nhất supply chain CSV với weather CSV toàn cầu.  
- **Luồng:** raw CSVs → mapping priority (country/city/date, state/province, lat/lon) → log missing rows → output `data/merged/supplychain_weather_merged_global.csv`.  
- **Liên kết:** `scripts/merge_supplychain_weather.py`.

#### 📄 modules/data_pipeline/global_dataset_loader.py
- **Mục đích:** Load dataset, xử lý ngữ cảnh (dates, numeric, weather).  
- **Luồng:** training scripts & dashboards import `load_global_dataset`.

#### 📄 modules/cognitive/strategy_engine.py, planner_agent.py
- **Mục đích:** sinh chiến lược, gợi ý hiển thị trên cognitive dashboard; multi-agent reasoning.  
- **Luồng:** `cognitive_api.py` gọi generate/comparison.

#### 📄 modules/logging_utils.py
- **Chức năng:** `log_warning`, `log_inference`, `update_registry_usage`. Ghi log text và cập nhật registry fields.  
- **Liên kết:** training scripts, ml_service, monitoring.

### Training Scripts
#### 📄 scripts/train_rl_inventory.py
- **Mục đích:** train Inventory RL surrogate (RandomForest).  
- **Luồng:** load dataset → engineer features → train → save model + feature schema → record metrics → update registry & warnings.

#### 📄 scripts/train_forecast.py
- **Mục đích:** train Demand Forecast Ensemble (per scope).  
- **Luồng:** aggregate data per scope → train models → metrics JSON → warnings if MAE high.

#### 📄 scripts/train_late_delivery.py
- **Mục đích:** train Late Delivery Classifier (RandomForestClassifier).  
- **Chức năng:** features weather risk, congestion; log metrics.

#### 📄 scripts/train_pricing_elasticity.py
- **Mục đích:** train ElasticNet pricing model; log metrics & warnings.

#### 📄 scripts/train_model_{logistics_delay,revenue_forecast,churn}.py
- **Mục đích:** legacy training pipeline cho logistics/churn/revenue (dùng feature store).

#### 📄 scripts/auto_retrain_global.py
- **Mục đích:** orchestrate sequential training cho 4 model chính + update registry/logs.

#### 📄 scripts/run_inference_samples.py
- **Mục đích:** gọi inference tất cả model, ghi log thật (test smoke).

#### 📄 scripts/generate_model_warnings.py
- **Mục đích:** đọc metrics JSON và sinh warnings (inventory RMSE, forecast MAE, late delivery F1, pricing MAE).

### Monitoring
#### 📄 monitoring/monitor_data_drift.py
- **Mục đích:** so sánh phân phối dataset mới vs baseline, cảnh báo drift > threshold.  
- **Liên kết:** logs/warnings, alerts.

#### 📄 monitoring/monitor_model_drift.py
- **Mục đích:** đánh giá accuracy/MAE/Reward drift so với metric baseline.  
- **Luồng:** load `results/metrics/*`, update warnings, trigger retrain.

#### 📄 monitoring/monitor_latency.py
- **Mục đích:** gọi inference và đo latency, log warning nếu vượt threshold.  

#### 📄 monitoring/monitor_weather_missing.py
- **Mục đích:** kiểm tra tỷ lệ missing weather per region; log warning khi >5%.  

#### 📄 monitoring/monitor_registry_sync.py
- **Mục đích:** đảm bảo registry và logs nhất quán (fields used_in_pipeline, last_inference_call).

### Templates (UI Views)
#### 📄 templates/dashboard.html
- **Loại:** Template Tailwind.  
- **Mục đích:** hiển thị KPI, bảng top, biểu đồ supply/weather.  
- **Dữ liệu:** context từ `dashboard.py`.

#### 📄 templates/cognitive_dashboard.html
- **Mục đích:** hiển thị summary, model status (dataset, used_in_pipeline, warnings), warning feed, chiến lược.  
- **JS:** fetch `/v8/dashboard/data`, render Chart.js.

#### 📄 templates/control_center.html
- **Mục đích:** trang `/os/control-center` (pending actions, filters, history, charts).  
- **JS:** gọi `/os/actions/pending`, `/os/action/history`, `/os/actions/approve|reject`.

#### 📄 templates/dashboard/models_list.html, model_detail.html
- **Mục đích:** Model Catalog + detail view.  
- **Dữ liệu:** `models_registry.py` context (registry entries).

#### 📄 templates/dashboard/metrics/*.html
- **Mục đích:** Metrics overview + per-model detail (inventory RL, forecast, delivery, pricing).  
- **Data:** Chart.js render `results/metrics/global_dashboard_metrics.json`.

#### 📄 templates/ml_*.html
- **Mục đích:** Form tương tác cho ML inference (late delivery, revenue forecast, churn).  
- **Luồng:** user input → JS POST `/ml/...`.

#### 📄 templates/doc_files_index.html, doc_file_view.html
- **Mục đích:** file browser cho docs (via `docs_viewer.py`).

#### 📄 templates/tests_overview.html, test_dashboard.html
- **Mục đích:** QA/training view của hệ thống test.

### Visual Regression
#### 📄 visual_regression/test_visual_regression.py
- **Mục đích:** so sánh screenshot hiện tại vs baseline (`baseline/dashboard.png`), fail nếu lệch quá ngưỡng.

---

## 🔁 Luồng hoạt động tổng thể

### 1️⃣ Data Flow
```
Raw CSVs (data/DataCoSupplyChainDataset.csv, geocoded_weather.csv)
    ↓ merge_supply_weather.py (modules/data_pipeline + scripts/merge_supplychain_weather.py)
Merged dataset (data/merged/supplychain_weather_merged_global.csv) + feature store parquet
    ↓ Training scripts (scripts/train_*)
Model artifacts (models/*) + metrics JSON (results/metrics/*) + logs/results
    ↓ Dashboards & monitoring đọc metrics/logs để hiển thị/cảnh báo
```

### 2️⃣ AI / ML Flow
```
scripts/train_*  →  models/<model>/global/*.pkl  →  modules/logging_utils.update_registry_usage()
    ↓
app/services/ml_service.py load model & schema  →  app/routers/ml_api endpoints
    ↓
UI (cognitive dashboard, control center, AI forms) gọi API → hiển thị kết quả
```

### 3️⃣ UI Flow
```
Người dùng (browser) → app/routers/* → templates/*.html (Tailwind + Jinja2)
    ↓
JS fetch API JSON (/dashboard/api/*, /v8/dashboard/data, /os/actions/*, /api/models, /api/models/metrics/global)
    ↓
Chart.js / components render data → user thao tác (approve actions, run quick actions, gọi inference)
```

### 4️⃣ Logging & Monitoring Flow
```
Training / inference / monitoring scripts
    ↓ modules/logging_utils.log_warning / log_inference
logs/warnings/*.log + logs/inference/*.log
    ↓ cognitive dashboard warning feed + registry (warnings_count, last_warning, used_in_pipeline, last_inference_call)
monitoring/*.py đọc metrics/logs → alerts (alerts/), auto retrain (scripts/auto_retrain_global.py) nếu cần
```

---

Tài liệu này phản ánh cấu trúc thực tế của dự án. Khi thêm thư mục hoặc file mới, hãy cập nhật `docs/PROJECT_STRUCTURE.md` tương ứng.***
