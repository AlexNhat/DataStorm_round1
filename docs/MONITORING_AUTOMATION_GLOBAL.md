# Monitoring & Automation (GLOBAL)

## Drift monitoring
- `monitor_data_drift.py`: compares numeric feature distributions (KS-test) between baseline and latest merged dataset. Alerts if drift > 0.2 and writes `results/logs/monitoring_data_drift.json`.
- `monitor_model_drift.py`: loads global models, evaluates on sample of merged data, flags if MAE/F1 degrade > 10%. Report: `results/logs/monitoring_model_drift.json`.
- `monitor_weather_missing.py`: checks weather feature missing-rate per region, alert if >5%.

## Latency & registry checks
- `monitor_latency.py`: calls main prediction endpoints and verifies response time against thresholds.
- `monitor_registry_sync.py`: ensures every entry in `model_registry.json` has valid artifact paths.

## Auto-retraining
- `scripts/auto_retrain_global.py`: sequentially runs all training scripts using merged dataset. Use for weekly/monthly retrain or triggered by drift alerts.

## Alerting
- `alerts/alert_email.py` & `alerts/alert_telegram.py`: placeholder hooks. Integrate with actual SMTP/Bot when deploying.
- Monitoring scripts should call these functions when alerts dict is non-empty.

## Scheduling
- Recommended cron (pseudo):
  - Daily: `monitor_data_drift.py`, `monitor_weather_missing.py`, `monitor_latency.py`.
  - Weekly: `python scripts/auto_retrain_global.py` (Forecast, Delivery).
  - Monthly: Inventory RL retrain via same script or dedicated job.
  - Event-based: trigger `auto_retrain_global` when `monitor_model_drift` raises alert.

## Logs & artifacts
- All monitoring outputs under `results/logs/`.
- Model metrics/logs under `results/metrics/` and `results/logs/`.
- Registry (`data/model_registry.json`) updated after each retrain to keep dashboard & API in sync.
