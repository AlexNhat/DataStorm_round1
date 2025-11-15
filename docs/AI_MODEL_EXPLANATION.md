# Giải thích chi tiết các mô hình AI trên `/dashboard/ai`

Tài liệu này tổng hợp mục đích, input/output và hướng dẫn sử dụng kết quả cho mọi mô hình xuất hiện trong AI Dashboard. Kết hợp tài liệu này với UI để đào tạo người dùng mới hoặc viết test automation.

---

## 1. Late Delivery Classifier

- **Mục đích**: dự báo xác suất đơn hàng giao trễ dựa trên thông tin logistics + thời tiết.
- **Input chính**:
  | Trường | Kiểu | Miền giá trị | Ý nghĩa | Ví dụ |
  | --- | --- | --- | --- | --- |
  | shipping_duration_scheduled | int | ≥1 ngày | Lead time kế hoạch | 5 |
  | weather_risk_level | int | 1-5 | Chỉ số rủi ro thời tiết | 2 |
  | is_weekend | select {0,1} | 0/1 | Giao cuối tuần | 0 |
  | month | int | 1-12 | Tháng giao hàng | 6 |
  | category_name | text | Tự do | Loại sản phẩm | “Electronics” |
- **Output**:
  | Trường | Ý nghĩa |
  | --- | --- |
  | late_risk_prob | xác suất giao trễ 0-1 |
  | late_risk_label | 0 = an toàn, 1 = rủi ro |
  | top_features | yếu tố ảnh hưởng lớn nhất (ví dụ chênh lệch thời gian) |
- **Ý nghĩa**: nếu `late_risk_prob > 0.7` thì Team Logistics cần tăng buffer thời gian hoặc đổi tuyến vận chuyển.
- **Ví dụ**: `late_risk_prob = 0.82` → ưu tiên phân bổ nguồn lực, cảnh báo khách hàng.

---

## 2. Demand Forecast Ensemble

- **Mục đích**: dự báo doanh thu/nhu cầu toàn cầu bằng XGBoost + Prophet + LSTM.
- **Input**: region, category, forecast_date (YYYY-MM-DD), revenue_lag_7d, revenue_lag_30d, rolling 7/30, month, day_of_week, temperature.
- **Output**: `forecasted_revenue`, `confidence_range`.
- **Ý nghĩa**: so sánh với tồn kho hiện có để quyết định nhập hàng; dùng cho kế hoạch tài chính.
- **Ví dụ**: `forecasted_revenue = 125000` → cần ít nhất 125k đơn vị hàng / kỳ.

---

## 3. Inventory Optimizer RL

- **Mục đích**: chính sách RL khuyến nghị tồn kho an toàn theo vùng dựa trên tín hiệu weather + congestion.
- **Input**: weather_risk_index (0-1), temp_7d_avg, rain_7d_avg, storm_flag, region_congestion_index (0-5), warehouse_workload_score (0-1), Order Item Product Price, Sales, Order Item Total, region.
- **Output**: `recommended_qty_buffer` (mức buffer đề xuất).
- **Ý nghĩa**: buffer >5 → kho nên bổ sung; buffer thấp → có thể giữ mức hiện tại.
- **Ví dụ**: `recommended_qty_buffer = 6.8` cho EU → tăng tồn kho an toàn 6.8% trong tuần tới.

---

## 4. Pricing Elasticity Model

- **Mục đích**: ước lượng nhu cầu tương ứng với mức giá đề xuất (kèm weather influence).
- **Input**: price, sales, weather_risk_index, weather_influence, region.
- **Output**: `expected_quantity`, `quantity_log`.
- **Ý nghĩa**: nếu expected_quantity giảm mạnh → cân nhắc giảm giá hoặc chạy promotion.
- **Ví dụ**: Giảm giá xuống 45 USD tạo `expected_quantity = 2600`, so sánh với baseline để lấy quyết định.

---

## 5. Customer Churn Classifier

- **Mục đích**: phân loại khách hàng có nguy cơ rời bỏ (dựa trên RFM + order history).
- **Input**: customer_id, rfm_recency, rfm_frequency, rfm_monetary, total_orders, avg_order_value.
- **Output**: `churn_prob`, `churn_label`.
- **Ý nghĩa**: `churn_prob > 0.7` → đưa khách vào chiến dịch giữ chân (tặng voucher, gọi chăm sóc).

---

## 6. Data Drift Monitor

- **Mục đích**: kiểm tra drift giữa dữ liệu gần nhất và baseline để trigger retrain.
- **Input**:
  - region (GLOBAL/EU/…)
  - window_hours (6-720)
  - features (chuỗi cột numeric, ví dụ `weather_risk_index,temp_mean_7d`)
- **Output**: `drift_score`, `drift_flag`, `feature_shift` (mỗi cột có KS, PSI, mean shift), `recommendation`.
- **Ý nghĩa**:
  - drift_score < 0.02 → ổn định
  - 0.02–0.1 → warning
  - >0.1 → critical → cần retrain.

---

## 7. Digital Twin Simulation

- **Mục đích**: mô phỏng chuỗi cung ứng theo kịch bản (doanh số surge, tắc cảng, mưa bão, …).
- **Input**: duration_days (1-180), scenario (normal/demand_surge/weather_storm/port_congestion/supplier_disruption), region.
- **Output**:
  - `scenario_summary`: baseline/optimistic/worst_case (fulfillment, risk, chi phí)
  - `timeline`: fulfillment theo ngày
  - `key_metrics`: disruption index, supply-demand gap, chi phí dự kiến
  - `recommendation`: hành động gợi ý.
- **Ý nghĩa**: so sánh các scenario để chuẩn bị tồn kho, điều chỉnh lưu tuyến, booking slot.

---

## 8. Strategic Reasoning Engine

- **Mục đích**: tổng hợp kết quả từ nhiều mô hình để đề xuất chiến lược inventory/logistics/pricing.
- **Input**: region, season, inventory, demand_outlook (neutral/surge/slow), risk_focus (balanced/growth/cost).
- **Output**:
  - `strategies`: danh sách chiến lược (name, focus, confidence, risk, reward, reasoning_steps)
  - `recommendation`: kịch bản được ưu tiên.
- **Ý nghĩa**: Ban điều hành dùng để chọn phương án (tăng tồn kho EU, ưu tiên tuyến vận chuyển, tập trung khách hàng trọng điểm…).

---

## Sử dụng tài liệu

- Khi viết automation tests cho `/dashboard/ai`, lấy payload mẫu trong từng mục.
- Khi training user mới, dùng bảng input/output để giải thích ý nghĩa từng trường.
- Khi có drift/giải thích bất thường: đối chiếu `feature_shift` trong logs và doc này để xác định bộ phận chịu trách nhiệm (logistics, planning, pricing, retention…).
