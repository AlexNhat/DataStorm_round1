# Global Dataset

## File
`data/merged/supplychain_weather_merged_global.csv`

## Schema chính (đề xuất)
- `order_id`, `order_date`, `ship_mode`, `segment`
- `country`, `region`, `city`, `state`, `warehouse_id`
- `product_category`, `sales`, `quantity`, `profit`
- `delivery_status`, `late_flag`, `delay_minutes`
- `weather_temp_c`, `weather_rain_mm`, `weather_storm_flag`, `weather_risk_index`
- `temp_7d_avg`, `rain_7d_avg`, `extreme_event_flag`
- `region_congestion_index`, `warehouse_workload_score`

## Region mapping
```
EU: DE, FR, IT, ES, NL, ...
APAC: VN, TH, SG, PH, CN, KR, JP, ...
NA: US, CA, MX
LATAM: BR, AR, CL, ...
AFRICA: ZA, NG, ...
MENA: AE, SA, QA, ...
GLOBAL_OTHER: còn lại
```
Mapping fallback theo thứ tự ưu tiên + geo radius, ghi log missing.

## Weather coverage
- Merge weather theo `(country, city, date)`;
- fallback state/province và geo grid;
- ghi log missing vào `results/logs/weather_mapping_missing_global.csv` (không làm fail pipeline).

## Thống kê
- Mapping success theo vùng được lưu trong file thống kê (xem output script merge).
- Dùng cho tất cả mô hình RL/Forecast/Delivery/Pricing.

## Sử dụng
```python
from modules.data_pipeline.global_dataset_loader import load_global_dataset
df = load_global_dataset('data/merged/supplychain_weather_merged_global.csv')
```
Loader đảm bảo schema validation, fill weather missing hợp lý, log warning thay vì crash.
