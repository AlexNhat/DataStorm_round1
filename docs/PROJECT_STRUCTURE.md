# PROJECT_STRUCTURE.md

Bản tóm tắt kiến trúc thư mục DataStorm giúp onboarding nhanh và định vị component khi phát triển/triển khai.

## app/
- `main.py`, `routers/`, `services/`, `templates/`, `static/`.
- Chịu trách nhiệm FastAPI endpoints (REST + HTML), render UI (Dashboard, Cognitive, Control Center) và orchestration services (analytics, caching, what-if).

## modules/
- Tập trung AI logic nâng cao: `cognitive/`, `meta_learning/`, `continual_learning/`, `self_healing/`, `self_learning/`.
- `data_pipeline/` xử lý hợp nhất dữ liệu supply/weather, `logging_utils.py` chuẩn hoá log + registry hook.
- Lưu trữ các agent, controller, planner phục vụ reasoning & automation.

## scripts/
- Bộ công cụ CLI cho training, monitoring, báo cáo và automation.
- Bao gồm `train_rl_inventory.py`, `train_forecast.py`, `train_late_delivery.py`, `train_pricing_elasticity.py`, `auto_retrain_global.py`, `run_all_tests_and_build_report.py`, `generate_dashboard_metrics.py`, `run_ui_tests.py`, v.v.
- Có folder con `online_learning/`, `rl/`, `scenarios/` phục vụ dòng công việc chuyên biệt.

## data/
- `raw/`, `merged/`, `processed/` (ví dụ `merged_supply_weather_clean.parquet`) chứa dataset đầu vào và feature store.
- Dùng chung cho pipeline training, inference sample và báo cáo dashboard.

## logs/
- `warnings/` ghi nhận cảnh báo chất lượng mô hình (drift, threshold).
- `inference/` lưu chi tiết request/response để audit.
- `audit/`, `os_decisions/`, `control_center_update.md` theo dõi orchestrator và các quyết định từ OS Control Center.

## results/
- `metrics/` (JSON) lưu KPI sau mỗi lần train/inference.
- `reports/`, `test_reports/`, `visual_regression/` tập hợp output phân tích và kiểm thử.
- Dùng để feed vào dashboard metrics & săn lỗi.

## docs/
- Tài liệu kiến trúc, hướng dẫn, báo cáo kiểm thử và kế hoạch cải tiến: `CONTROL_CENTER_GUIDE.md`, `ML_IMPLEMENTATION_OVERVIEW.md`, `OS_ARCHITECTURE.md`, `PROJECT_SUMMARY_REPORT.md`, ...
- File này (`PROJECT_STRUCTURE.md`) giúp điều hướng, các tài liệu khác đào sâu từng module.

## tests/
- Tổ chức theo `unit/`, `integration/`, `ui/`, `regression/`, kèm `conftest.py`, snapshots HTML, baseline metrics.
- Dùng pytest + Playwright/Selenium để đảm bảo độ tin cậy đầu cuối.

## Thư mục bổ trợ khác
- `core/`, `agents/`, `engines/`, `models/`, `visual_regression/`… hỗ trợ Digital Twin, RL environments, artifact lưu trữ và baseline UI.

