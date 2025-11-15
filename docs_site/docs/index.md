# DataStorm – Hệ thống AI cho Chuỗi Cung Ứng

## Tổng quan
DataStorm là nền tảng AI toàn diện cho vận hành chuỗi cung ứng: dự báo nhu cầu, tối ưu tồn kho, mô phỏng digital twin và điều phối Control Center thời gian thực. Hệ thống đã được mở rộng với dataset GLOBAL hợp nhất supply chain + weather và toàn bộ mô hình (Inventory RL, Demand Forecast, Late Delivery, Pricing Elasticity) đã được train lại theo chuẩn này.

## Thành phần chính
- **FastAPI backend** (`app/`): router cho dashboard, OS, API ML.
- **AI/ML pipelines** (`scripts/`, `modules/`, `models/`): training, inference, auto-monitoring.
- **Datasets** (`data/`): gồm `merged/supplychain_weather_merged_global.csv` và registry.
- **Docs & reports** (`docs/`, `logs/`): mô tả chiến lược, pipeline, audits.

## Yêu cầu hệ thống
- Python 3.9+
- pip hoặc conda
- RAM ≥ 8GB
- PostgreSQL (nếu bật module storage)

## Cài đặt nhanh
```bash
git clone https://github.com/AlexNhat/DataStorm_round1.git
cd DataStorm_round1
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```
Tạo file `.env` cho thông số DB/API khi cần.

## Chạy ứng dụng
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Đường dẫn quan trọng:
- Dashboard quản trị: `http://localhost:8000/dashboard`
- Control Center: `http://localhost:8000/os/control-center`
- Cognitive dashboard: `http://localhost:8000/v8/dashboard`
- OpenAPI docs: `http://localhost:8000/docs`

## Chạy pipeline ML
Ví dụ train lại toàn bộ mô hình bằng dataset GLOBAL:
```bash
python scripts/train_rl_inventory.py --data data/merged/supplychain_weather_merged_global.csv --global_mode true
python scripts/train_forecast.py --data data/merged/supplychain_weather_merged_global.csv --global_mode true
python scripts/train_late_delivery.py --data data/merged/supplychain_weather_merged_global.csv
python scripts/train_pricing_elasticity.py --data data/merged/supplychain_weather_merged_global.csv
```
Auto retrain: `python scripts/auto_retrain_global.py`.

## Quy trình kiểm thử
```bash
pytest tests/unit tests/integration
pytest tests/regression tests/ui
```
Có thể dùng `scripts/run_all_tests_and_build_report.py` (nếu tồn tại) để gom báo cáo.

## Cấu trúc thư mục rút gọn
```
app/                FastAPI routers, templates, static
modules/            Data pipeline, feature store, ETL helpers
scripts/            Training/inference, monitoring, automation
models/             Artifact lưu sau mỗi lần train
data/               Dataset gốc & merged + registry
monitoring/         Script giám sát drift, latency, weather
docs/               Tài liệu chuyên sâu
results/            Metrics/logs đầu ra
logs/               Báo cáo fix theo route
```

## Tài liệu liên quan
Các chương tiếp theo trình bày chi tiết dataset, pipeline, AI models, dashboard, monitoring, UI, API và changelog.
