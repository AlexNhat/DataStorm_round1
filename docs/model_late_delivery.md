# Mô hình dự đoán giao hàng trễ (Late Delivery Prediction)

Dự đoán `Late_delivery_risk` (0/1) dựa trên thông tin đơn hàng, shipping, và thời tiết để cảnh báo sớm các đơn hàng có nguy cơ giao trễ, tối ưu hóa logistics và cải thiện customer satisfaction.

---

## 1. Dữ liệu sử dụng

### Nguồn dữ liệu
- **File gốc:** 
  - `data/DataCoSupplyChainDataset.csv` (~180,000 records)
  - `data/geocoded_weather.csv` (~180,000 records)
- **File merged:** `data/merged_supply_weather_clean.parquet`
  - Dataset đã được gộp và chuẩn hóa
  - Khoảng thời gian: từ min date đến max date trong dataset
  - Các cột quan trọng: Order Id, Customer Id, order date, Sales, Delivery Status, Late_delivery_risk, weather features

### Mô tả ngắn
- **Số dòng:** ~180,000 records
- **Target:** `Late_delivery_risk` (binary: 0 = on-time, 1 = late)
- **Tỉ lệ giao trễ:** ~X% (tùy dataset)

---

## 2. Tiền xử lý & Feature Engineering

### Các bước chính

#### 2.1. Chuẩn hóa dữ liệu
- **Ngày tháng:** Chuẩn hóa `order date (DateOrders)` về datetime, tạo các feature: year, month, day_of_week, is_weekend, is_holiday_season
- **Country/City:** Chuẩn hóa tên quốc gia (EE. UU. → United States, UK → United Kingdom)
- **Join supply & weather:** Merge theo Customer ID + Date hoặc Country + City + Date

#### 2.2. Xử lý missing values & outliers
- **Numeric:** Fill với median (cho weather) hoặc 0 (cho Sales/Benefit)
- **Categorical:** Fill với "Unknown"
- **Outliers:** Phát hiện và cap values cho Sales, Benefit, lead_time

#### 2.3. Feature Engineering đặc thù

**Time Features:**
- `year`, `month`, `day_of_week`, `is_weekend`, `is_holiday_season`
- `month_sin`, `month_cos` (cyclical encoding)
- `day_of_week_sin`, `day_of_week_cos` (cyclical encoding)

**Shipping Features:**
- `Days for shipping (real)`: Số ngày giao hàng thực tế
- `Days for shipment (scheduled)`: Số ngày giao hàng dự kiến
- `lead_time`: Chênh lệch = scheduled - real

**Weather Features:**
- `temperature_2m_mean`, `precipitation_sum`, `wind_speed_10m_mean`
- `weather_risk_level`: Mức độ rủi ro thời tiết (1-5) dựa trên precipitation, wind, temperature extremes

**Location & Product Features:**
- `Order Country`, `Order City`, `Category Name`
- `Order Item Quantity`, `Order Item Discount`

**Sales Features:**
- `Sales`, `Benefit per order`

---

## 3. Thiết kế mô hình

### Loại mô hình
- **Baseline:** Logistic Regression (đơn giản, dễ interpret)
- **Tree-based:** Random Forest, XGBoost (xử lý non-linear, feature importance)

### Cách chia train/test
- **Time-based split:** 80% train (dữ liệu đầu tiên), 20% test (dữ liệu cuối cùng)
- **Lý do:** Tránh data leakage, mô hình phải dự đoán tương lai dựa trên quá khứ

### Các metric đánh giá
- **Accuracy:** Tỉ lệ dự đoán đúng
- **F1 Score:** Harmonic mean của Precision và Recall (quan trọng với class imbalance)
- **AUC-ROC:** Diện tích dưới đường ROC (đánh giá khả năng phân loại)
- **Precision/Recall:** 
  - Precision: Trong số các đơn dự đoán trễ, bao nhiêu thực sự trễ
  - Recall: Trong số các đơn thực sự trễ, bao nhiêu được dự đoán đúng

### Xử lý class imbalance
- **Logistic Regression:** `class_weight='balanced'`
- **Random Forest:** `class_weight='balanced'`
- **XGBoost:** `scale_pos_weight` = ratio của negative/positive

---

## 4. Kết quả chính

### Model tốt nhất
- **XGBoost** thường cho kết quả tốt nhất (AUC-ROC cao nhất, F1 Score tốt)

### Metrics (ví dụ)
| Model | Accuracy | F1 Score | AUC-ROC |
|-------|----------|----------|---------|
| Logistic Regression | ~0.XX | ~0.XX | ~0.XX |
| Random Forest | ~0.XX | ~0.XX | ~0.XX |
| XGBoost | ~0.XX | ~0.XX | ~0.XX |

### Insights
1. **Weather risk level** có tương quan mạnh với late delivery: mưa lớn, gió mạnh làm tăng tỉ lệ trễ
2. **Lead time** là feature quan trọng nhất: chênh lệch giữa scheduled và real shipping time
3. **Time features** (weekend, holiday season) có ảnh hưởng đến logistics
4. **Shipping mode** và **Order Country** cũng là yếu tố quan trọng

### Top Features (dựa trên XGBoost feature importance)
1. `lead_time` - Chênh lệch thời gian giao hàng
2. `weather_risk_level` - Mức độ rủi ro thời tiết
3. `Days for shipping (real)` - Thời gian giao hàng thực tế
4. `Shipping Mode` - Phương thức vận chuyển
5. `Order Country` - Quốc gia đơn hàng

---

## 5. Hạn chế & Hướng phát triển

### Hạn chế
- **Dữ liệu bias:** Có thể thiên về một số vùng/quốc gia nhất định
- **Thiếu features:** 
  - Không có distance chính xác từ warehouse đến customer
  - Không có traffic conditions, road quality
  - Không có event/holiday đầy đủ
- **Class imbalance:** Có thể ảnh hưởng đến performance
- **Model chưa tuning:** Hyperparameters chưa được tối ưu kỹ

### Hướng phát triển
1. **Feature Engineering:**
   - Rolling statistics (7-day, 30-day averages của số đơn trễ)
   - Lag features (số đơn trễ trong 7 ngày trước)
   - Distance features (khoảng cách từ warehouse đến customer)
   - External data: traffic, road conditions, events

2. **Model Improvement:**
   - Hyperparameter tuning (GridSearchCV/RandomSearchCV)
   - Ensemble methods (voting, stacking)
   - Deep Learning (nếu có đủ dữ liệu)

3. **MLOps:**
   - Model monitoring (drift detection)
   - Retrain định kỳ
   - A/B testing
   - Real-time prediction API

---

## 6. Liên kết tới notebook

**Notebook minh họa:** `notebooks/model_late_delivery.ipynb`

### Hướng dẫn mở notebook
1. **Với Jupyter Notebook:**
   ```bash
   jupyter notebook notebooks/model_late_delivery.ipynb
   ```

2. **Với JupyterLab:**
   ```bash
   jupyter lab notebooks/model_late_delivery.ipynb
   ```

3. **Với VS Code:**
   - Cài extension "Jupyter"
   - Mở file `.ipynb` trực tiếp trong VS Code

### Lưu ý
- Đảm bảo đã chạy `python scripts/merge_supplychain_weather.py` trước để có file `data/merged_supply_weather_clean.parquet`
- Notebook có thể chạy từ trên xuống dưới mà không cần thay đổi

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0
