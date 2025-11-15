# DataStorm – Hệ thống AI cho Chuỗi Cung Ứng

## 1. Giới thiệu ngắn

- Hệ thống AI phân tích & dự đoán toàn bộ chuỗi cung ứng, từ kho vận tới nhu cầu.
- Tích hợp đa mô hình ML/AI:
  - Dự đoán giao hàng trễ
  - Dự báo nhu cầu
  - Phân tích churn
  - Tối ưu tồn kho bằng Reinforcement Learning
  - Mô phỏng đa tác nhân (multi-agent simulation)
  - Digital Twin engine cho supply chain
- Bao gồm Dashboard & OS Control Center phục vụ vận hành realtime.

## 2. Tính năng nổi bật

- Dự báo chính xác 7–30 ngày cho nhu cầu & tồn kho.
- Mô phỏng chuỗi cung ứng theo nhiều kịch bản (đứt gãy, mùa vụ, thiên tai).
- Tự động tối ưu chiến lược tồn kho bằng RL và meta-learning.
- Dashboard trực quan, đa biểu đồ, hỗ trợ drill-down và what-if.
- Bộ test đầy đủ (unit, integration, UI, regression) đảm bảo chất lượng bản phát hành.

## 3. Yêu cầu hệ thống

- Python 3.9+
- pip hoặc conda để quản lý môi trường
- RAM tối thiểu 8GB
- PostgreSQL (tùy chọn nếu bật các module DB/persistence)

## 4. Cách cài đặt

```bash
git clone https://github.com/AlexNhat/DataStorm_round1.git
cd DataStorm_round1
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS / Linux
pip install -r requirements.txt
```

Tạo file `.env` nếu cần tùy chỉnh (ví dụ thông số DB, API key). Có thể tham khảo `.env.example` (tự tạo).

## 5. Chạy ứng dụng

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Dashboard: http://localhost:8000/dashboard  
- Control Center: http://localhost:8000/control-center  
- API OpenAPI docs: http://localhost:8000/docs

## 6. Quy trình kiểm thử

```bash
# Unit & integration
pytest tests/unit tests/integration

# Regression & UI (sử dụng playwright/selenium giả lập)
pytest tests/regression tests/ui

# Báo cáo tổng hợp
python scripts/run_all_tests_and_build_report.py
```

Visual regression baseline nằm ở `visual_regression/baseline/`.

## 7. Cấu trúc thư mục chính

```
app/                # FastAPI app, routers, services, templates, static files
agents/             # Multi-agent & environment definitions
core/               # Orchestrator, governance, safety kiểm soát AI
data/               # Dataset & feature store (đã xử lý)
docs/               # Bộ tài liệu và báo cáo chi tiết
engines/digital_twin# Mô hình Digital Twin & simulator
models/             # Model artifacts & schema
modules/            # Cognitive, meta-learning, self-learning modules
rl/                 # Reinforcement learning training/eval scripts
scripts/            # CLI hỗ trợ ETL, training, report, UI tests
tests/              # Unit, integration, UI, regression suites
visual_regression/  # Snapshot baseline & regression runner
```

## 8. Quy trình vận hành tiêu chuẩn

1. Cập nhật dữ liệu: `python scripts/preprocess_and_build_feature_store.py`
2. Huấn luyện lại mô hình: chạy `scripts/train_model_*.py` tương ứng.
3. Đánh giá & audit: `python scripts/run_all_models_evaluation.py`
4. Triển khai / khởi động dịch vụ: `run_server_with_ml.bat` (Windows) hoặc `bash run_server.sh`
5. Theo dõi real-time qua Dashboard & Control Center.

## 9. Bộ tài liệu & resources

- Toàn bộ tài liệu nghiệp vụ và kỹ thuật nằm trong thư mục `docs/`.
- `PROJECT_SUMMARY_REPORT.md`, `QUICK_START.md`, `README_V6_V7.md`, `README_V8_V9.md`, `STATUS.md` cung cấp lịch sử phát triển & hướng dẫn nhanh.
- Báo cáo chuyên sâu: `docs/CONTROL_CENTER_GUIDE.md`, `docs/ML_IMPLEMENTATION_OVERVIEW.md`, `docs/OS_ARCHITECTURE.md`, ...

## 10. Triển khai & checklist dành cho người mới

- [x] Clone repo & tạo virtualenv
- [x] Cài dependencies từ `requirements.txt`
- [x] (Tùy chọn) Điều chỉnh `.env` cho DB/PostgreSQL
- [x] Chạy `uvicorn app.main:app --reload`
- [x] Dùng `pytest` hoặc `scripts/run_all_tests_and_build_report.py` để xác minh

Hệ thống đã được cấu hình để người mới có thể clone và chạy ngay, đồng thời có đầy đủ tài liệu và bộ test để kiểm chứng trước khi triển khai.

