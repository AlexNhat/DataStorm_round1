# Mô hình dự báo doanh thu (Revenue/Demand Forecast)

Dự báo doanh thu (hoặc số lượng đơn) theo thời gian, có thể theo tổng hệ thống hoặc theo từng quốc gia (Country) để phục vụ kế hoạch doanh số, tối ưu hóa inventory và phân bổ resources.

---

## 1. Dữ liệu sử dụng

### Nguồn dữ liệu
- **File gốc:** 
  - `data/DataCoSupplyChainDataset.csv` (~180,000 records)
  - `data/geocoded_weather.csv` (~180,000 records)
- **File merged:** `data/merged_supply_weather_clean.parquet`
  - Dataset đã được gộp và chuẩn hóa
  - **Aggregation:** Group by `year_month` + `Order Country`
  - **Target:** `revenue` (tổng Sales trong tháng)

### Mô tả ngắn
- **Số dòng gốc:** ~180,000 records
- **Số time periods sau aggregation:** ~X records (tùy số tháng và số quốc gia)
- **Khoảng thời gian:** Từ min date đến max date trong dataset
- **Mức độ chi tiết:** Doanh thu theo tháng cho mỗi Country

---

## 2. Tiền xử lý & Feature Engineering

### Các bước chính

#### 2.1. Aggregation
- Group by `year_month` + `Order Country`
- Aggregate: `Sales` → sum (revenue), `Order Id` → count, weather → mean

#### 2.2. Feature Engineering đặc thù

**Lag Features (Quan trọng nhất):**
- `revenue_lag1`: Doanh thu tháng trước
- `revenue_lag2`: Doanh thu 2 tháng trước
- `revenue_lag3`: Doanh thu 3 tháng trước
- **Lý do:** Doanh thu có tính tự tương quan (autocorrelation), tháng trước ảnh hưởng đến tháng sau

**Rolling Statistics:**
- `revenue_ma7`: Moving average 7 tháng
- `revenue_ma30`: Moving average 30 tháng
- `revenue_std7`: Standard deviation 7 tháng
- **Lý do:** Nắm bắt xu hướng dài hạn và biến động

**Time Features:**
- `month`, `quarter`, `year`
- `month_sin`, `month_cos` (cyclical encoding)
- **Lý do:** Seasonality - doanh thu thay đổi theo mùa

**Weather Features:**
- `avg_temperature`: Nhiệt độ trung bình trong tháng
- `avg_precipitation`: Lượng mưa trung bình
- `avg_weather_risk`: Mức độ rủi ro thời tiết
- **Lý do:** Thời tiết ảnh hưởng đến nhu cầu mua sắm

**Order Count:**
- `order_count`: Số đơn hàng trong tháng

**Country Features:**
- One-hot encoding cho top 10 countries

---

## 3. Thiết kế mô hình

### Loại mô hình
- **Baseline:** Linear Regression (đơn giản, dễ interpret)
- **Tree-based:** Random Forest Regressor, XGBoost Regressor (xử lý non-linear, feature importance)

### Cách chia train/test
- **Time-based split:** 80% train (dữ liệu đầu tiên), 20% test (dữ liệu cuối cùng)
- **Lý do:** Tránh data leakage, mô hình phải dự đoán tương lai dựa trên quá khứ

### Các metric đánh giá
- **MAE (Mean Absolute Error):** Lỗi trung bình tuyệt đối
- **RMSE (Root Mean Squared Error):** Lỗi bình phương trung bình (penalize lỗi lớn hơn)
- **MAPE (Mean Absolute Percentage Error):** Lỗi phần trăm trung bình
- **R² (R-squared):** Tỉ lệ phương sai được giải thích

---

## 4. Kết quả chính

### Model tốt nhất
- **XGBoost Regressor** thường cho kết quả tốt nhất (R² cao, MAPE thấp)

### Metrics (ví dụ)
| Model | MAE | RMSE | MAPE | R² |
|-------|-----|------|------|-----|
| Linear Regression | ~XX,XXX | ~XX,XXX | ~X% | ~0.XX |
| Random Forest | ~XX,XXX | ~XX,XXX | ~X% | ~0.XX |
| XGBoost | ~XX,XXX | ~XX,XXX | ~X% | ~0.XX |

### Insights
1. **Lag features** rất quan trọng: `revenue_lag1` thường là feature quan trọng nhất
2. **Seasonality** có ảnh hưởng: doanh thu thay đổi theo mùa (ví dụ: cao vào cuối năm)
3. **Weather** có tác động: thời tiết khắc nghiệt có thể làm giảm doanh thu
4. **Country patterns** khác nhau: mỗi quốc gia có pattern doanh thu riêng

### Top Features (dựa trên XGBoost feature importance)
1. `revenue_lag1` - Doanh thu tháng trước
2. `revenue_ma7` - Moving average 7 tháng
3. `revenue_ma30` - Moving average 30 tháng
4. `month_sin`, `month_cos` - Seasonality
5. `avg_weather_risk` - Weather impact

---

## 5. Hạn chế & Hướng phát triển

### Hạn chế
- **Chưa xử lý trend:** Có thể dùng differencing để loại bỏ trend
- **Thiếu external features:** 
  - Marketing spend
  - Promotions, events
  - Economic indicators (GDP, inflation)
- **Chưa có hyperparameter tuning:** Model chưa được tối ưu kỹ
- **Chưa xử lý outliers:** Một số tháng có doanh thu bất thường

### Hướng phát triển
1. **Time Series Methods:**
   - ARIMA, SARIMA (cho seasonality)
   - Prophet (Facebook)
   - LSTM (Deep Learning)

2. **Feature Engineering:**
   - Trend features (linear, polynomial)
   - Holiday features
   - Economic indicators (GDP, inflation)
   - Marketing spend, promotions

3. **Ensemble:**
   - Combine time series models với tree-based models
   - Stacking

4. **MLOps:**
   - Model monitoring (drift detection)
   - Retrain định kỳ
   - Real-time forecasting API

---

## 6. Liên kết tới notebook

**Notebook minh họa:** `notebooks/model_revenue_forecast.ipynb`

### Hướng dẫn mở notebook
1. **Với Jupyter Notebook:**
   ```bash
   jupyter notebook notebooks/model_revenue_forecast.ipynb
   ```

2. **Với JupyterLab:**
   ```bash
   jupyter lab notebooks/model_revenue_forecast.ipynb
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
