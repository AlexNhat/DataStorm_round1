# Global Pipeline Overview

## Dataset merge (PROMPT 1)
- Script: `modules/data_pipeline/merge_supply_weather.py`.
- Đầu vào: `data/DataCoSupplyChainDataset.csv`, `data/geocoded_weather.csv`.
- Chuẩn hóa country/city/state, chuẩn ISO date, mapping multi-region (EU/APAC/NA/LATAM/AFRICA/MENA/OTHER).
- Mapping priority: `(country, city, date)` → `(country, state, date)` → geo grid ±δ → log missing.
- Output chính: `data/merged/supplychain_weather_merged_global.csv`, thống kê mapping, log missing `results/logs/weather_mapping_missing_global.csv`.

## Feature engineering
- Weather risk index, storm flag, humidity, rolling windows (temp_7d_avg, rain_7d_avg).
- Region tag cho RL reward + logistic features.
- Region congestion index & warehouse workload score cho RL & Late Delivery.

## Model pipeline (PROMPT 2)
1. **Inventory Optimizer RL**: load global dataset, build RL state-space (inventory, demand, weather features). Output `models/inventory_rl/global/*` và log `results/logs/train_inventory_rl_global.log`.
2. **Demand Forecast Ensemble**: multi-granularity (country, region, global). Rolling weather features + horizon metrics. Artifact `models/forecast/global/*`.
3. **Late Delivery Classifier**: weather + logistics features, region congestion baseline. Artifact `models/late_delivery/global/*`.
4. **Pricing Elasticity**: optional weather influences per region. Artifact `models/pricing/global/*`.

## Automation
- `scripts/auto_retrain_global.py`: sequentially retrain RL → Forecast → Delivery → Pricing, update registry.
- Monitoring triggers (drift, latency) gọi auto retrain nếu vượt threshold.

## Outputs
- Metrics JSON dưới `results/metrics/*_global.json`.
- Registry update `data/model_registry.json` (version, accuracy, last_update, status=Success).
- Dashboard metrics summary `results/metrics/global_dashboard_metrics.json` phục vụ `/dashboard/metrics` & `/api/models/metrics/global`.
