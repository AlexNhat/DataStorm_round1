---
title: Project Views Detail
---

# Tổng quan
Các trang giao diện của DataStorm được xây dựng bằng FastAPI + Jinja2 templates (Tailwind). Dưới đây là danh sách chi tiết từng trang, dữ liệu sử dụng và ý nghĩa vận hành.

---

## Dashboard Tổng Quan
**Tên trang:** `templates/dashboard.html` – route `/dashboard`  
**Chức năng:** Hiển thị KPI chuỗi cung ứng, biểu đồ doanh số, phân tích thời tiết và trạng thái giao hàng.  
**Nội dung:** 
- KPI cards (`calculate_supply_chain_kpis`), bảng top sản phẩm/quốc gia, biểu đồ time-series doanh thu.
- Bảng đơn hàng mẫu, filter theo country/category/delivery status/date range.
- Biểu đồ correlation thời tiết vs giao hàng, advanced metrics & seasonality.  
**Dữ liệu sử dụng:** `app/routers/dashboard.py` tải dữ liệu qua `load_supply_chain_data()` và `load_weather_data()`. API Ajax `/dashboard/api/data` và `/dashboard/api/filter`.  
**Ý nghĩa vận hành:** Dành cho vận hành cấp cao & BI team để nhận trạng thái chung và khoanh vùng vấn đề trước khi vào các dashboard chuyên sâu.

---

## Cognitive Dashboard
**Tên trang:** `templates/cognitive_dashboard.html` – route `/v8/dashboard`  
**Chức năng:** Trung tâm hiển thị chiến lược AI, cảnh báo, hành động nhanh.  
**Nội dung:** 
- Summary cards (active models, avg accuracy, daily runs, pending actions).
- Bảng danh sách mô hình (phiên bản, dataset, used_in_pipeline, inference, warnings).
- Warning feed đọc từ `logs/warnings`.
- Chiến lược đề xuất (cards multi-agent), biểu đồ KPI (line, bar), quick actions (deploy model, weather simulation...).  
**Dữ liệu sử dụng:** `_build_dashboard_snapshot()` trong `app/routers/cognitive_api.py` đọc model_registry + logs.  
**Ý nghĩa vận hành:** Dành cho AI Ops và lãnh đạo để xem trạng thái thời gian thực của các mô hình, warnings và kích hoạt hành động.

---

## OS Control Center
**Tên trang:** `templates/control_center.html` – route `/os/control-center`  
**Chức năng:** Điều hành action queue từ mô hình (pending actions, policy check, history).  
**Nội dung:** 
- KPI cards (pending approvals, auto-applied rate, policy violations...).
- Control mode selector, filter panel (status/type/cost/confidence).
- Pending actions list (policy check, payload, reasoning, approval buttons).
- Timeline lịch sử `#action-history-list`, charts (history line & type).  
**Dữ liệu sử dụng:** `app/routers/os_api.py` endpoints `/os/actions/pending`, `/os/actions/approve`, `/os/action/history`.  
**Ý nghĩa vận hành:** Dành cho control tower/operator duyệt action, theo dõi OS tasks.

---

## Model Catalog
**Tên trang:** `templates/dashboard/models_list.html` – route `/dashboard/models`  
**Chức năng:** Liệt kê toàn bộ model registry (name, version, region, accuracy, status, notes).  
**Nội dung:** Table responsive, badge trạng thái, owner info, total count.  
**Dữ liệu sử dụng:** `app/routers/models_registry.py` đọc `data/model_registry.json`.  
**Ý nghĩa:** Đảm bảo mọi model có metadata rõ ràng (ai sở hữu, last_update, note).

### Model Detail
**Tên trang:** `templates/dashboard/model_detail.html` – route `/dashboard/models/{slug}`  
**Chức năng:** Thông tin chi tiết từng model, artifacts, operational notes.  
**Nội dung:** Cards (owner, region, version, accuracy), link metrics/log files, notes, status badge.  
**Dữ liệu:** `models_registry.py` filter registry entry.  
**Ý nghĩa:** Dành cho ML engineers kiểm tra artifacts & logs, triaging issues.

---

## Metrics Dashboard
**Tên trang:** `templates/dashboard/metrics/metrics_overview.html` – route `/dashboard/metrics`  
**Chức năng:** Tổng quan metrics của tất cả mô hình (RL reward, forecast MAE, delivery delay, pricing heatmap).  
**Nội dung:** Chart.js line/bar + heatmap, cards hiển thị accuracy/MAE.  
**Dữ liệu:** `app/routers/models_metrics.py` đọc `results/metrics/global_dashboard_metrics.json`.  
**Ý nghĩa:** Monitoring chất lượng mô hình theo thời gian.

### Metrics Detail Pages
- `metrics_inventory_rl.html` – `/dashboard/metrics/inventory-rl`: Reward curve + regional workload.
- `metrics_forecast.html` – `/dashboard/metrics/forecast`: MAE by scope + sales horizon.
- `metrics_delivery.html` – `/dashboard/metrics/delivery`: Region delay bar chart + key metrics (accuracy, F1).
- `metrics_pricing.html` – `/dashboard/metrics/pricing`: Pricing elasticity heatmap.
Mỗi trang dùng Chart.js, hiển thị data subset từ summary JSON.

---

## AI Model Interaction Pages
**Tên trang:** 
- `templates/ml_late_delivery.html` – route `/ml/late-delivery`.
- `templates/ml_revenue_forecast.html` – route `/ml/revenue-forecast`.
- `templates/ml_customer_churn.html` – route `/ml/customer-churn`.
**Chức năng:** Form tương tác để gọi API inference cho từng mô hình.  
**Dữ liệu:** Xử lý trong `app/routers/ml_api.py`.  
**Ý nghĩa:** Dành cho data scientist hoặc QA test input/outcome trước khi tích hợp.

---

## AI Dashboard (Legacy)
**Tên trang:** `templates/ai_dashboard.html` – route `/dashboard/ai`  
**Chức năng:** Hiển thị danh sách mô hình AI, pipeline tasks và quick insights (trước khi Cognitive dashboard triển khai).  
**Nội dung:** Cards tasks, status, charts placeholder.  
**Dữ liệu:** Router `app/routers/ai_dashboard.py`.  
**Ý nghĩa:** Đang sử dụng cho stakeholders quen layout cũ.

---

## Test Dashboard & Utilities
- `templates/test_dashboard.html` – route `/dashboard/test` (nếu enable) hiển thị mock charts cho QA.
- `templates/tests_overview.html` – route `/tests` summary test suites.
- `templates/doc_files_index.html`, `doc_file_view.html` – route `/docs/view/*` hiển thị tài liệu Markdown từ repo.
- `templates/notebook_files_index.html`, `notebook_file_view.html` – route `/notebooks/*`.
Các trang này phục vụ QA, documentation viewer, developer onboarding.

---

## Page Usage Summary Table
| Route | Template | Người dùng chính | Dữ liệu chính |
| --- | --- | --- | --- |
| `/dashboard` | dashboard.html | Ops/BI | Supply & weather dataset via analytics services |
| `/dashboard/models` | dashboard/models_list.html | MLOps | data/model_registry.json |
| `/dashboard/models/{slug}` | dashboard/model_detail.html | ML Engineer | Registry entry |
| `/dashboard/metrics` | metrics_overview.html | MLOps/QA | results/metrics/global_dashboard_metrics.json |
| `/dashboard/metrics/*` | metrics_* | Specialist | Same summary JSON |
| `/v8/dashboard` | cognitive_dashboard.html | Exec/AI Ops | Registry + logs/warnings |
| `/os/control-center` | control_center.html | Control Tower | /os/actions APIs |
| `/ml/...` | ml_* templates | Data scientist | ml_api endpoints |
| `/dashboard/ai` | ai_dashboard.html | Legacy users | service placeholders |
| `/docs/*` | doc_* | Everyone | Markdown viewer |
| `/tests` | tests_overview.html | QA | CI test reports |

---

Tài liệu này sẽ được cập nhật khi thêm route hoặc template mới.
