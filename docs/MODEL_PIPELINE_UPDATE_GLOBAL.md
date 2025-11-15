# Cập nhật pipeline mô hình với dữ liệu GLOBAL

## 1. Pipeline cũ
- Mỗi mô hình đọc riêng các file dữ liệu (SupplyChain, weather per-region).
- Inventory Optimizer RL gọi API weather EU → timeout, không hỗ trợ khu vực khác.
- Demand Forecast, Late Delivery, Pricing chỉ có feature nội bộ, không tích hợp weather toàn cầu.

## 2. Pipeline mới
1. **Merge data**: `modules/data_pipeline/merge_supply_weather.py` ghép DataCoSupplyChain + geocoded_weather toàn cầu → `data/merged/supplychain_weather_merged_global.csv`.
2. **Loader chung**: `modules/data_pipeline/global_dataset_loader.py`
   - chuẩn hóa Country/City/Region
   - parse record_date
   - fill missing weather theo Region + toàn cục
3. **Các mô hình đào tạo từ dataset GLOBAL**:
   - `scripts/train_rl_inventory.py`
   - `scripts/train_forecast.py`
   - `scripts/train_late_delivery.py`
   - `scripts/train_pricing_elasticity.py`
4. **Model Registry**: `data/model_registry.json` ghi lại version mới, trạng thái, artifact path.

## 3. Danh sách mô hình đã cập nhật
| Model | Version | Region | Bộ feature chính |
|-------|---------|--------|------------------|
| Inventory Optimizer RL | v5.3 | GLOBAL | weather_risk_index, temp/rain rolling, congestion index, workload score |
| Demand Forecast Ensemble | v7.5 | GLOBAL | sales lags, weather risk mean, extreme event flag |
| Late Delivery Classifier | v4.2 | GLOBAL | avg_weather_risk, delay_factor_global, storm flag |
| Pricing Elasticity | v3.1 | GLOBAL | price_log, weather influence, region/category one-hot |

## 4. Cách chạy lại pipeline
```bash
# Inventory Optimizer RL
python scripts/train_rl_inventory.py --data data/merged/supplychain_weather_merged_global.csv --global_mode true

# Demand Forecast
python scripts/train_forecast.py --data data/merged/supplychain_weather_merged_global.csv --global_mode true

# Late Delivery Classifier
python scripts/train_late_delivery.py --data data/merged/supplychain_weather_merged_global.csv

# Pricing Elasticity
python scripts/train_pricing_elasticity.py --data data/merged/supplychain_weather_merged_global.csv
```

Kết quả được lưu tại:
- `models/<model_name>/global/`
- `results/metrics/<model>_global.json`
- `results/logs/<log>.log`

## 5. Ghi chú
- Không còn gọi API thời tiết trực tuyến.
- Thiếu weather → log warning, không làm pipeline dừng.
- Dataset GLOBAL hỗ trợ mọi khu vực (EU, APAC, NA, LATAM, AFRICA, MENA, GLOBAL_OTHER) và làm nguồn chuẩn cho các mô hình hiện tại & tương lai.
