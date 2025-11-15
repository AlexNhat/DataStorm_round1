# DataStorm – Hệ thống AI cho Chuỗi Cung Ứng

## 1. Tổng quan

DataStorm là hệ thống AI Supply Chain toàn diện giúp dự báo nhu cầu, tối ưu tồn kho, giám sát rủi ro giao hàng và vận hành chiến lược thời gian thực. Kiến trúc kết hợp FastAPI, multi-agent reasoning, Digital Twin, reinforcement learning và các pipeline dữ liệu tự động, sẵn sàng để triển khai on-prem hoặc cloud.

## 2. Bộ mô hình AI chủ lực

- **Inventory Optimizer RL** – mô hình RL đa kịch bản giúp khuyến nghị buffer, phân bổ kho và tự động học theo tín hiệu thời tiết.
- **Demand Forecast Ensemble** – tổ hợp XGBoost + Prophet + LSTM phục vụ dự báo 7–30 ngày, hỗ trợ granular theo khu vực.
- **Late Delivery Classifier** – gradient boosting + weather enrichments để cảnh báo rủi ro đơn hàng trễ.
- **Pricing Elasticity Regressor** – ước lượng hệ số co giãn để điều chỉnh giá theo bối cảnh thời tiết và nhu cầu.
- **Churn & Revenue Models** – phục vụ phân khúc khách hàng, đánh giá CLV, cung cấp đầu vào cho chiến lược.
- **Digital Twin & Multi-agent Simulation** – tái tạo supply chain và cho phép what-if analysis ngay trên Control Center.

## 3. Logging & Model Registry Overhaul

- **logs/warnings/** lưu toàn bộ cảnh báo chất lượng mô hình (RL, Forecast, Late Delivery, Pricing).
- **logs/inference/** ghi lại từng request/response cho mục đích audit, đồng thời đồng bộ với `results/metrics` để so khớp drift.
- **Model Registry (`app/services/model_registry.py`)** theo dõi: `status`, `version`, `api_endpoint`, `api_method`, `docs_path`, `chart_types`, `form_fields`, `dataset_info`, `last_trained`, `model_path` và `metrics`. Tất cả hiển thị trong Dashboard `/dashboard/models` và APIs `/dashboard/models/status`.
- **Registry-driven routing** bảo đảm mỗi mô hình đều có metadata, auto-link tới tài liệu và forms UI.

## 4. Cognitive Dashboard & v8 UI

- `/dashboard` cung cấp overview KPI + filter nâng cao; `/dashboard/models` để duyệt chi tiết từng mô hình.
- `/v8/dashboard` là Cognitive Dashboard thế hệ mới: hiển thị chiến lược đề xuất, mô phỏng multi-agent, scenario triggers.
- `/os/control-center` hiển thị hàng đợi hành động, trạng thái orchestration, approval flow cho self-healing actions.
- `/dashboard/ai` + `/dashboard/tests` giúp team ML & QA theo dõi health liên tục.

## 5. Yêu cầu hệ thống

- Python 3.9+
- pip hoặc conda
- RAM ≥ 8 GB, khuyến nghị 16 GB khi huấn luyện lại
- PostgreSQL (tuỳ chọn, nếu bật persistence cho Control Center / registry)

## 6. Cài đặt

```bash
git clone https://github.com/AlexNhat/DataStorm_round1.git
cd DataStorm_round1
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS / Linux
pip install -r requirements.txt
```

Khởi tạo `.env` (DB URI, feature flags, API key) dựa trên `docs/OS_ARCHITECTURE.md`.

## 7. Chạy hệ thống

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- `/dashboard` – KPI & phân tích vận hành.
- `/dashboard/models` – Model Registry UI.
- `/v8/dashboard` – Cognitive dashboard (chiến lược, multi-agent).
- `/os/control-center` – Orchestration & approval center.
- `/dashboard/models/status` – JSON health check cho CI/CD.
- `/docs` – OpenAPI.

## 8. Huấn luyện mô hình

Các script nằm trong `scripts/` (sử dụng dataset đã merge trong `data/`):

```bash
python scripts/train_rl_inventory.py --data data/merged_supply_weather_clean.parquet
python scripts/train_forecast.py --data data/merged_supply_weather_clean.parquet
python scripts/train_late_delivery.py --data data/merged_supply_weather_clean.parquet
python scripts/train_pricing_elasticity.py --data data/merged_supply_weather_clean.parquet
```

- Kết quả được ghi vào `models/` và `results/metrics/`.
- Có thể chạy `python scripts/auto_retrain_global.py` để retrain hàng loạt.
- Pipeline dữ liệu chuẩn bị qua `python scripts/preprocess_and_build_feature_store.py`.

## 9. Inference & API Endpoints

FastAPI router `app/routers/ml_api.py` cung cấp các endpoint:

- `POST /ml/logistics/delay`
- `POST /ml/revenue/forecast` và alias `POST /ml/forecast/demand`
- `POST /ml/rl/inventory`
- `POST /ml/customer/churn`
- `POST /ml/pricing/elasticity`

Payload mẫu nằm trong docstring từng Pydantic schema. Response luôn có `status`, `prediction`, `top_features` hoặc confidence tương ứng. Có thể gọi thử bằng `python scripts/run_inference_samples.py`.

## 10. Kiểm thử & chất lượng

```bash
pytest tests/unit tests/integration
pytest tests/regression tests/ui
python scripts/run_all_tests_and_build_report.py   # tổng hợp + báo cáo HTML
```

- Visual/UI snapshots ở `tests/ui/snapshots/`.
- Báo cáo regression lưu tại `results/test_reports/`.
- `scripts/run_ui_tests.py` có thể dùng cho CI headless.

## 11. Cấu trúc dự án

Tóm tắt nhanh: `app/` (FastAPI & UI), `modules/` (cognitive, meta-learning, data_pipeline, logging_utils), `scripts/` (training, monitoring, automation), `data/`, `logs/`, `results/`, `docs/`, `tests/`.  
👉 Xem cấu trúc chi tiết tại [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

## 12. GitFlow nhanh

1. Tạo nhánh `feature/*` từ `main`.
2. Commit nhỏ, mô tả rõ (ví dụ `feat`, `fix`, `docs`).
3. `git push -u origin feature/<name>` và mở Pull Request → review → merge `main`.
4. Xoá nhánh khi đã merge để giữ repo sạch.

## 13. Tài liệu & hỗ trợ

- `docs/CONTROL_CENTER_GUIDE.md`, `docs/ML_IMPLEMENTATION_OVERVIEW.md`, `docs/OS_ARCHITECTURE.md` giải thích kiến trúc.
- `PROJECT_SUMMARY_REPORT.md`, `QUICK_START.md`, `README_V6_V7.md`, `README_V8_V9.md`, `STATUS.md` lưu lịch sử release.
- Các báo cáo nâng cao: `docs/STRATEGIC_AI_GUIDE.md`, `docs/AI_UI_IMPLEMENTATION_SUMMARY.md`, `docs/RISK_ANALYSIS.md`.

Hệ thống sẵn sàng để người mới clone, cài đặt và chạy ngay, đồng thời cung cấp đầy đủ logging, registry metadata và UI để vận hành ở quy mô doanh nghiệp.

## 14. Tài liệu chi tiết

- [docs/AI_MODELS_DETAIL.md](docs/AI_MODELS_DETAIL.md) – mô tả đầy đủ từng mô hình, dữ liệu, pipeline.
- [docs/PROJECT_VIEWS_DETAIL.md](docs/PROJECT_VIEWS_DETAIL.md) – mô tả cấu trúc và dữ liệu của tất cả trang UI.
- [docs/AI_MODEL_PREDICTION_GUIDE.md](docs/AI_MODEL_PREDICTION_GUIDE.md) – hướng dẫn nhập dữ liệu, chạy dự đoán và diễn giải kết quả trên `/dashboard/ai`.
- [docs/AI_MODEL_EXPLANATION.md](docs/AI_MODEL_EXPLANATION.md) – giải thích chi tiết input/output và khuyến nghị hành động cho từng mô hình.

## 14. Tài liệu chi tiết

- [docs/AI_MODELS_DETAIL.md](docs/AI_MODELS_DETAIL.md) – mô tả đầy đủ từng mô hình, dữ liệu, pipeline.
- [docs/PROJECT_VIEWS_DETAIL.md](docs/PROJECT_VIEWS_DETAIL.md) – mô tả cấu trúc và dữ liệu của tất cả trang UI.
- [docs/AI_MODEL_PREDICTION_GUIDE.md](docs/AI_MODEL_PREDICTION_GUIDE.md) – hướng dẫn nhập dữ liệu, chạy dự đoán và diễn giải kết quả trên `/dashboard/ai`.

## QA Prediction Testing

- /dashboard/ai/{model_id} sinh form d?a tr�n pp/services/model_registry.py, k�m tooltip gi?i th�ch tru?ng, n�t **Load sample data** v� t?i JSON/CSV m?u d? QA g� th? ngay.
- B? test normal/edge/error v� sample payload ch�nh th?c n?m trong [docs/AI_MODEL_PREDICTION_TEST_PLAN.md](docs/AI_MODEL_PREDICTION_TEST_PLAN.md); h�y tham chi?u t�i li?u n�y tru?c khi ch?y regression cho t?ng m� h�nh.

