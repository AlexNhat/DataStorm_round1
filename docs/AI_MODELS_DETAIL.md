---
title: AI Models Detail
---

# Tổng quan
Tài liệu này mô tả chi tiết toàn bộ mô hình AI trong dự án DataStorm, bao gồm dữ liệu đầu vào, pipeline huấn luyện, API sử dụng và cảnh báo vận hành. Tất cả thông tin được tổng hợp tự động từ các script trong `scripts/`, modules trong `modules/`, metrics tại `results/metrics/` và registry `data/model_registry.json`.

---

## Inventory Optimizer RL
**Mục đích:** Ước lượng lượng tồn kho bổ sung/buffer cho từng kho trước các rủi ro thời tiết và nhu cầu đột biến. Được hiển thị trên `/v8/dashboard` và sử dụng để kích hoạt hành động trong Control Center.

**Dữ liệu đầu vào:** `data/merged/supplychain_weather_merged_global.csv` với các cột như `Order Item Quantity`, `Sales`, `Order Item Total`, `temperature_2m_mean`, `precipitation_sum`, `weather_code`, `Region`, `City`, `record_date`.

**Feature Engineering (scripts/train_rl_inventory.py):**
- Chuẩn hóa số liệu bằng `ensure_numeric`.
- Rolling 7 ngày cho nhiệt độ và lượng mưa (`temp_7d_avg`, `rain_7d_avg`).
- `storm_flag` dựa trên weather code và lượng mưa > 25mm.
- `region_congestion_index` lấy tổng qty theo ngày/region chia trung bình vùng; clip 0–5.
- `warehouse_workload_score` rolling sum 7 ngày, chuẩn hóa về 0–10.
- Target là `Order Item Quantity`.

**Cấu hình mô hình:**
- RandomForestRegressor (300 trees, depth=12, min_samples_leaf=5, random_state=42).
- Train/test split 80/20.
- Metrics: MAE và RMSE (ví dụ MAE 0.0099, RMSE 0.0678 cho 8k rows).

**Quy trình hoạt động:**
- Training script ghi kết quả vào `models/inventory_rl/global`, metrics tại `results/metrics/inventory_rl_global.json`, log `results/logs/train_inventory_rl_global.log`.
- Model registry cập nhật version `v5.3`, dataset version `supplychain_weather_merged_global.csv`.
- API inference: `POST /ml/rl/inventory` (payload gồm weather features, congestion, giá trị đơn hàng) trả về `recommended_qty_buffer`.
- Inference log: `logs/inference/inventory_optimizer_rl_inference.log`.
- Dashboard `/v8/dashboard` đọc status từ registry và hiển thị note/cảnh báo.

**Kết quả & Metrics:** MAE < 0.01, RMSE ~0.067. Mạnh ở vùng nhiều dữ liệu (APAC/EU), yếu nếu nhập thiếu weather_risk_index → logged warning.

**Cảnh báo & Lưu ý:** Warning ghi tại `logs/warnings/inventory_optimizer_rl_warnings.log` khi RMSE vượt ngưỡng hoặc inference trả về giá trị âm. Quan tâm đặc biệt tới vùng APAC khi thiếu dữ liệu thời tiết.

---

## Demand Forecast Ensemble
**Mục đích:** Dự báo doanh thu/nhu cầu 7–30 ngày theo nhiều phạm vi (theo Country, Region, Global) để phục vụ chuỗi cung ứng và planning.

**Dữ liệu đầu vào:** Dataset merged toàn cầu, các cột như `Order Country`, `Region`, `record_date`, `Sales`, `Order Item Quantity`, thời tiết. Script thêm cột GLOBAL để tạo scope.

**Feature Engineering:** 
- Tính trung bình rolling, lag doanh thu (`revenue_lag_7d`, `revenue_lag_30d`, `revenue_7d_avg`, `revenue_30d_avg`).
- Aggregation theo scope (country/region/global) bằng `train_forecast_scope`.
- Bổ sung feature thời tiết nếu có.

**Cấu hình mô hình:**
- RandomForestRegressor (n_estimators=400, max_depth=16, min_samples_leaf=5… – xem script).
- Train/test split 80/20 cho mỗi scope.
- Metrics: MAE, RMSE, sample count cho từng scope (ghi trong `results/metrics/forecast_global.json`).

**Quy trình hoạt động:**
- Training script `scripts/train_forecast.py` chạy 3 scope, lưu model vào `models/forecast/global/region_model/*.pkl`, log `results/logs/forecast_global.log`.
- API inference: `POST /ml/revenue/forecast` (alias `/ml/forecast/demand`) với fields region/category/time + lag features.
- Inference log: `logs/inference/demand_forecast_ensemble_inference.log`.
- Dashboard `/dashboard/metrics` hiển thị MAE theo scope (Chart.js bar) và `/dashboard/models` hiển thị status.

**Kết quả & Metrics:** Ví dụ MAE scope region ~1026.32. Bền vững toàn cầu, cần chú ý region có MAPE cao (LATAM). Cảnh báo trong `logs/warnings/demand_forecast_ensemble_warnings.log`.

**Cảnh báo & Lưu ý:** Theo dõi MAPE per region, warning ghi nhận khi MAE > 10% hoặc negative forecast. Khi warning, Control Center highlight scope tương ứng.

---

## Late Delivery Classifier
**Mục đích:** Dự đoán rủi ro đơn hàng giao trễ để kích hoạt cảnh báo trong Control Center và /v8 dashboard.

**Dữ liệu đầu vào:** Merge dataset với cột `Late_delivery_risk`, `Days for shipping (real/scheduled)`, weather metrics, qty, region info.

**Feature Engineering:** 
- `weather_risk_index`, `avg_weather_risk`.
- `storm_flag` theo weather_code/lượng mưa.
- `region_delay_baseline`, `delay_factor_global`.
- `region_congestion_index`.
- Target: `Late_delivery_risk` (int).

**Cấu hình mô hình:**
- RandomForestClassifier (n_estimators=400, depth=16, class_weight='balanced').
- Train/test split stratified 80/20.
- Metrics: F1 score (~0.994) + classification report stored in `results/metrics/late_delivery_global.json`.

**Quy trình hoạt động:**
- Training log `results/logs/late_delivery_global.log`.
- API inference: `POST /ml/logistics/delay`.
- Inference log: `logs/inference/late_delivery_classifier_inference.log`.
- Dashboard `/dashboard/ai` và `/v8/dashboard` hiển thị status + warnings.

**Cảnh báo & Lưu ý:** F1 < 0.9 triggers warning (region-specific). Drift detection: `logs/warnings/late_delivery_classifier_warnings.log`.

---

## Pricing Elasticity Model
**Mục đích:** Đo độ co giãn nhu cầu theo giá, phục vụ chính sách giá theo vùng, hiển thị trong dashboard metrics.

**Dữ liệu đầu vào:** Global merged dataset, cột `Order Item Quantity`, `Product Price`, `Sales`, thời tiết, `Category Name`, `Region`.

**Feature Engineering:** 
- Weather risk & influence (mean per region).
- Log transform: `price_log`, `sales_log`, `quantity_log`.
- One-hot cho category và region, metadata lưu trong `feature_columns.json`.

**Cấu hình mô hình:** ElasticNet(alpha=0.0005, l1_ratio=0.3, max_iter=5000).
- Train/test split 80/20.
- Metrics: MAE (~0.0161) + rows count (`results/metrics/pricing_global.json`).

**Quy trình hoạt động:**
- Training log `results/logs/pricing_global.log`.
- API inference: `POST /ml/pricing/elasticity` (payload price, sales, weather_risk_index + overrides) → quantity_log & expected_quantity.
- Inference log: `logs/inference/pricing_elasticity_model_inference.log`.
- Dashboard metrics view hiển thị heatmap theo region/category.

**Cảnh báo & Lưu ý:** Warning khi MAE > 0.15 hoặc inference trả quantity âm (`logs/warnings/pricing_elasticity_model_warnings.log`). Cần đảm bảo features encode khớp schema.

---

## Logistics Delay Model (Production Inference)
**Mục đích:** Từ API `/ml/logistics/delay` dự đoán xác suất đơn hàng trễ (late_risk_prob, label). Dùng cho Logistics Ops & Control Center.

**Dữ liệu đầu vào:** Feature store `data/features/features_logistics.parquet`. Bao gồm order_id, shipping durations, weather, customer segments.

**Modeling:** Trong `scripts/train_model_logistics_delay.py` (không chạy mặc định) dùng Logistic Regression, RandomForest, XGBoost; cân bằng bằng class weights và scaler.

**Pipeline:** Pydantic `LogisticsDelayRequest`, service `ml_service.predict_logistics_delay` -> service `_prepare_features` dùng schema + label encoders. Inference log `logs/inference/late_delivery_classifier_inference.log`.

**Cảnh báo:** API ghi warning khi prob > 0.85 (High risk).

---

## Revenue Forecast Model (Legacy)
**Mục đích:** Từ `scripts/train_model_revenue_forecast.py`, multi-model (RF + XGBoost) dự báo doanh thu (target_revenue). Dữ liệu `data/features/features_forecast.parquet`.

**Status:** Nhiều logic đã nhập vào Demand Forecast Ensemble; file vẫn tham chiếu qua ml_service `get_revenue_service`.

**Features:** Time-based split, label encoding, scaler. Metrics: MAPE, MAE, RMSE. Warnings khi MAPE cao.

---

## Customer Churn Model
**Mục đích:** Đánh giá xác suất khách hàng rời bỏ (API `/ml/customer/churn`).

**Dữ liệu:** Feature store (customer RFM, orders) – xem `scripts/train_model_churn.py`.

**Model:** Gradient-based classifier (RandomForest/XGBoost). Metrics: AUC, F1, stored trong log.

**Cảnh báo:** Warning khi churn_prob > 0.85 hoặc inference lỗi.

---

# System Pipelines

## Data Pipeline
- **Input:** `data/DataCoSupplyChainDataset.csv`, `data/geocoded_weather.csv`.
- **Process:** `modules/data_pipeline/merge_supply_weather.py` + `scripts/preprocess_and_build_feature_store.py` chuẩn hóa country/city, mapping weather multi-region, rolling stats, logging missing entries.
- **Output:** `data/merged/supplychain_weather_merged_global.csv`, `results/logs/weather_mapping_missing_global.csv`, feature store parquet.
- **Usage:** Toàn bộ training script & dashboards sử dụng dataset này.

## Logging Pipeline
- **Modules:** `modules/logging_utils.py`.
- **Inputs:** Training scripts + inference services.
- **Process:** Format `timestamp | WARNING | model | severity=... | issue=...`, update registry counters.
- **Outputs:** `logs/warnings/<model>_warnings.log`, `logs/inference/<model>_inference.log`.
- **Usage:** Dashboard warning feed, audit trail.

## Monitoring Pipeline
- **Scripts:** `monitoring/monitor_data_drift.py`, `monitor_model_drift.py`, `monitor_latency.py`, `monitor_weather_missing.py`, `monitor_registry_sync.py`.
- **Function:** Scheduled to read merged dataset & registry, trigger auto retrain (`scripts/auto_retrain_global.py`) and send alerts (email/telegram) when thresholds exceeded.

## Model Registry Pipeline
- **File:** `data/model_registry.json`.
- **Writers:** `update_registry_usage()` in training scripts, inference logging, warning logging.
- **Fields:** name, version, dataset_version, used_in_pipeline, last_inference_call, total_inference_calls, last_warning, warnings_count, artifacts.
- **Consumers:** `/dashboard/models`, `/v8/dashboard`, APIs `/api/models`, `/api/models/metrics/global`.

## Dashboard Pipeline
- **Routers/Templates:** `app/routers/cognitive_api.py`, `dashboard.py`, `models_registry.py`, `models_metrics.py`.
- **Inputs:** Model registry, warning logs, aggregated metrics.
- **Outputs:** HTML pages (Cognitive dashboard, Control Center, metrics detail, AI forms), Chart.js visualizations.
- **Usage:** Ops teams monitor KPIs, warnings, take actions directly from UI.

---

## References
- Training scripts: `scripts/train_*`.
- Metrics: `results/metrics/*`.
- Logging: `logs/warnings`, `logs/inference`.
- APIs: `app/routers/ml_api.py`, `app/services/ml_service.py`.
