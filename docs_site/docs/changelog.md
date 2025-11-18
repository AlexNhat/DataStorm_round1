# Changelog

## 2025-11-15
- ✅ Merged supply chain + weather dataset toàn cầu (`data/merged/supplychain_weather_merged_global.csv`).
- ✅ Retrain cả 4 mô hình (Inventory RL v5.3, Forecast v7.5, Late Delivery v4.2, Pricing v3.1) → region GLOBAL, status Success.
- ✅ Cập nhật `data/model_registry.json`, routes `/api/models`, `/api/models/metrics/global`.
- ✅ Làm mới Dashboard Model Catalog + Metrics, UI Tailwind hiện đại.
- ✅ Triển khai monitoring scripts (drift, latency, weather), auto retrain & alerting.
- ✅ Thêm docs `METRICS_DASHBOARD_GLOBAL.md`, `UI_REDESIGN_MODERN_GLOBAL.md`, docsite MkDocs.

## 2025-11-14 trở về trước
- Các bản báo cáo V6–V9, audit, control center improvements, cognitive dashboard redesign (xem thư mục `docs/`).
