# Monitoring & Automation

## Thư mục `monitoring/`
- `monitor_data_drift.py`: so sánh phân phối dataset mới vs snapshot, cảnh báo khi drift > 0.2.
- `monitor_model_drift.py`: load model mới nhất trong `models/*/global`, chạy test set và đo accuracy/MAE/RL reward drift. Nếu giảm >10% → trigger retrain.
- `monitor_weather_missing.py`: kiểm tra tỉ lệ thiếu weather theo region (>5% → alert).
- `monitor_latency.py`: đo thời gian predict RL/Forecast/Delivery, alert nếu vượt threshold.
- `monitor_registry_sync.py`: đảm bảo registry JSON và artifacts đồng bộ.

## Auto retrain
- Script `scripts/auto_retrain_global.py`: chạy RL → Forecast → Delivery → Pricing với dataset merged_global, cập nhật `data/model_registry.json` + metrics/logs.

## Alerting
- Thư mục `alerts/`: `alert_email.py`, `alert_telegram.py`. Các monitoring script call khi phát hiện drift/latency/weather issues.

## Scheduling
- Khuyến nghị cron:
  - Daily: data drift + weather completeness + latency.
  - Weekly: auto-train Forecast & Delivery.
  - Monthly: auto-train Inventory RL.
  - Event-based: nếu drift > threshold.

## Logs & outputs
- Logs: `results/logs/*.log`, `monitoring/logs/*` (tùy setup).
- Metrics: `results/metrics/*_global.json`, snapshots trong `results/metrics/snapshots/YYYY-MM-DD/`.

## Deployment
- Có thể tích hợp scheduler (Airflow, Prefect) hoặc systemd timers; docs này mô tả logic, developer tự tích hợp lên môi trường thật.
