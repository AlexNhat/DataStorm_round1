# Global AI Models

| Model | Version | Region | Accuracy | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Inventory Optimizer RL | v5.3 | GLOBAL | 0.9988 | Success | Updated using global merged supplychain-weather dataset. Fixed previous EU weather timeout. |
| Demand Forecast Ensemble | v7.5 | GLOBAL | 0.79 | Success | Updated using global merged supplychain-weather dataset. Fixed previous EU weather timeout. |
| Late Delivery Classifier | v4.2 | GLOBAL | 0.9807 | Success | Updated using global merged supplychain-weather dataset. Fixed previous EU weather timeout. |
| Pricing Elasticity Model | v3.1 | GLOBAL | 0.9853 | Success | Updated using global merged supplychain-weather dataset. Fixed previous EU weather timeout. |

## Training commands
```bash
python scripts/train_rl_inventory.py --data data/merged/supplychain_weather_merged_global.csv --global_mode true
python scripts/train_forecast.py --data data/merged/supplychain_weather_merged_global.csv --global_mode true
python scripts/train_late_delivery.py --data data/merged/supplychain_weather_merged_global.csv
python scripts/train_pricing_elasticity.py --data data/merged/supplychain_weather_merged_global.csv
```

## Metrics artifacts
- RL: `results/metrics/inventory_rl_global.json`
- Forecast: `results/metrics/forecast_global.json`
- Late Delivery: `results/metrics/late_delivery_global.json`
- Pricing: `results/metrics/pricing_global.json`

## Registry
Nguồn dữ liệu: `data/model_registry.json`. API: `GET /api/models`.

## Deployment status
Tất cả mô hình đã sync với Control Center và dashboard Model Catalog; status = Success.
