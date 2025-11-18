# Hướng dẫn dự đoán trên `/dashboard/ai`

Tài liệu dành cho QA/ops khi kiểm tra AI Dashboard. Với mỗi mô hình, hãy:

1. Đọc mục **Mô hình dùng để làm gì** để biết đầu ra mong đợi.
2. Ở tab **Thử dự đoán**, nhập payload theo phần **Cách nhập dữ liệu** (có thể nhấn “Điền mẫu”).
3. Sau khi chạy, đối chiếu kết quả với phần **Giải thích kết quả & tham số** để xác nhận mô hình hoạt động đúng.

---

## 1. Late Delivery Classifier
### Mô hình dùng để làm gì?
- Gradient boosting cảnh báo rủi ro đơn hàng giao trễ dựa trên thông tin logistics + thời tiết.

### Cách nhập dữ liệu
- Trường bắt buộc: `shipping_duration_scheduled` (≥1 ngày).
- Trường khuyến khích: `temperature`, `precipitation`, `wind_speed`, `weather_risk_level`, `is_weekend`, `month`, `category_name`.
- Payload mẫu có sẵn trong UI (nút **Điền mẫu**).

### Giải thích kết quả
- `late_risk_prob`: xác suất giao trễ (0-1). >0.5 → rủi ro cao.
- `late_risk_label`: 0 = an toàn, 1 = rủi ro.
- “Top features” chỉ ra yếu tố ảnh hưởng mạnh nhất (ví dụ chênh lệch thời gian giao).

---

## 2. Demand Forecast Ensemble
### Mô hình dùng để làm gì?
- Ensemble XGBoost + Prophet + LSTM dự báo doanh thu/nhu cầu theo khu vực.

### Cách nhập dữ liệu
- Bắt buộc: `forecast_date` (YYYY-MM-DD), `region`, `category`.
- Lag/rolling: `revenue_lag_7d`, `revenue_lag_30d`, `revenue_7d_avg`, `revenue_30d_avg`, `month`, `day_of_week`, `temperature`.

### Giải thích kết quả
- `forecasted_revenue`: nhu cầu kỳ vọng trong kỳ tới.
- `confidence_range`: dùng để lên kế hoạch tồn kho an toàn.

---

## 3. Inventory Optimizer RL
### Mô hình dùng để làm gì?
- Chính sách RL khuyến nghị tồn kho an toàn theo vùng dựa trên weather + congestion.

### Cách nhập dữ liệu
- `weather_risk_index`, `temp_7d_avg`, `rain_7d_avg`, `storm_flag`, `region_congestion_index`, `warehouse_workload_score`, `Order Item Product Price`, `Sales`, `Order Item Total`, `region`.

### Giải thích kết quả
- `recommended_qty_buffer`: mức buffer đề xuất. >5 → nên tăng tồn kho an toàn.

---

## 4. Pricing Elasticity Model
### Mô hình dùng để làm gì?
- Ước lượng nhu cầu tương ứng với mức giá đề xuất (có xét weather influence).

### Cách nhập dữ liệu
- `price`, `sales`, `weather_risk_index`, `weather_influence`, `region`.

### Giải thích kết quả
- `expected_quantity`: sản lượng dự kiến tương ứng mức giá nhập vào.
- `quantity_log`: giá trị logarit dùng để phân tích độ nhạy.

---

## 5. Customer Churn Classifier
### Mô hình dùng để làm gì?
- Phát hiện khách hàng có nguy cơ rời bỏ để kích hoạt chiến dịch giữ chân.

### Cách nhập dữ liệu
- `customer_id`, `rfm_recency`, `rfm_frequency`, `rfm_monetary`, `total_orders`, `avg_order_value`.

### Giải thích kết quả
- `churn_prob`: xác suất rời bỏ. >0.7 → đưa vào chiến dịch giữ chân.
- `churn_label`: 0 = ở lại, 1 = rời bỏ.

---

## 6. Data Drift Monitor
### Mô hình dùng để làm gì?
- So sánh phân phối dữ liệu gần nhất với baseline để quyết định retrain.

### Cách nhập dữ liệu
- **Bắt buộc** nhập 3 trường numeric:
  - `Late_delivery_risk` (0-1)
  - `weather_risk_index` (0-1)
  - `temp_mean_7d` (°C)
- Có thể dùng nút “Điền mẫu” để lấy giá trị mặc định nếu chưa có dữ liệu thực tế.

### Giải thích kết quả
- `drift_score`: độ lệch tối đa (0 ổn định, 0.02–0.05 cảnh báo nhẹ, >0.05 drift mạnh).
- `status`: `stable`, `warning`, `critical`.
- `by_feature`: chi tiết drift từng cột.
- `recommendation`: hành động gợi ý (ví dụ kiểm tra dữ liệu, retrain).
- Hệ thống luôn trả kết quả hợp lệ; nếu nhập thiếu sẽ hướng dẫn bổ sung hoặc tự dùng payload mẫu.

---

## 7. Digital Twin Simulation
### Mô hình dùng để làm gì?
- Mô phỏng chuỗi cung ứng dưới các kịch bản (baseline/optimistic/worst-case).

### Cách nhập dữ liệu
- `duration_days` (1-180), `scenario` (normal/demand_surge/... ), `region`.

### Giải thích kết quả
- `scenario_summary`: bảng so sánh fulfillment/risk/chi phí từng kịch bản.
- `key_metrics`: disruption index, supply-demand gap, simulated cost delta.
- `recommendation`: hành động nên thực hiện.

---

## 8. Strategic Reasoning Engine
### Mô hình dùng để làm gì?
- Tổng hợp nhiều mô hình để đề xuất chiến lược inventory/logistics/pricing.

### Cách nhập dữ liệu
- `region`, `season`, `inventory`, `demand_outlook` (neutral/surge/slow), `risk_focus` (balanced/growth/cost).

### Giải thích kết quả
- `strategies`: danh sách khuyến nghị (name, focus, confidence, risk, reward, reasoning steps).
- `recommendation`: kết luận chung (ưu tiên chiến lược đầu tiên nếu confidence > 0.7).

---

## Debug nhanh khi gặp lỗi
1. Nếu thấy thông báo “Thiếu dữ liệu numeric…” → dùng nút “Điền mẫu” hoặc nhập đủ 3 trường bắt buộc (Late_delivery_risk, weather_risk_index, temp_mean_7d).
2. Với lỗi 422/500 khác, kiểm tra payload và log `uvicorn`. Đảm bảo file model tồn tại.
3. Các mô hình đặc biệt (Drift, Digital Twin, Strategy) luôn có endpoint riêng; nếu API trả thông báo hướng dẫn thì không phải lỗi, chỉ cần nhập đủ thông tin theo doc này.
