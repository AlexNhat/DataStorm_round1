# Quy trình Merge Supply Chain & Weather Global

## Mục tiêu
- Ghép dữ liệu supply chain (`DataCoSupplyChainDataset.csv`) với thời tiết (`geocoded_weather.csv`) trên phạm vi toàn cầu.
- Bổ sung vùng (EU, APAC, NA, LATAM, AFRICA, MENA, GLOBAL_OTHER) để phục vụ mọi mô hình AI.
- Đảm bảo pipeline không timeout, có log cảnh báo khi thiếu weather mà không dừng toàn bộ ETL.

## Khóa mapping ưu tiên
1. **Exact (country, city, date)** – ghép dựa trên quốc gia, thành phố, ngày.
2. **Fallback (country, state/province, date)** – dùng khi city không khớp.
3. **Geolocation grid (country, lat_round, lon_round, date)** – dùng khi dữ liệu có tọa độ.
4. **Nếu không khớp** → ghi vào `results/logs/weather_mapping_missing_global.csv` và tiếp tục.

## Chuẩn hóa dữ liệu đầu vào
- Chuẩn hóa tên quốc gia/city/state bằng `unidecode`, title-case city/state, uppercase country.
- Chuẩn hóa ngày về ISO `YYYY-MM-DD`.
- Tạo `country_norm`, `city_norm`, `state_norm`, `record_date`, `lat_round`, `lon_round`.
- Xác định `region_detected` dựa trên country code với LUT toàn cầu.

## Pipeline
1. Đọc supply chain dataset → chuẩn hóa.
2. Đọc weather dữ liệu theo `chunksize=100000` để tránh memory/timeouts.
3. Với mỗi chunk:
   - Chuẩn hóa weather.
   - Merge lần lượt theo 3 khóa ưu tiên (city → state → geo).
   - Những dòng đã map sẽ được loại khỏi tập còn lại để tăng hiệu suất.
4. Sau khi hết chunk, ghi các dòng còn thiếu vào log.
5. Gộp kết quả (`data/merged/supplychain_weather_merged_global.csv`) và thống kê (`results/logs/weather_merge_stats_global.csv`).

## Chạy script
```bash
python modules/data_pipeline/merge_supply_weather.py
```

Output:
- `data/merged/supplychain_weather_merged_global.csv`
- `results/logs/weather_mapping_missing_global.csv`
- `results/logs/weather_merge_stats_global.csv`

Các file này sẽ được dùng cho mọi mô hình AI (Inventory Optimizer RL, Demand Forecast, Late Delivery, Pricing, …).
