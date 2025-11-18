# ML IMPLEMENTATION OVERVIEW

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

---

## 📋 TỔNG QUAN

Tài liệu này mô tả việc triển khai 3 model ML lõi cho dự án Supply Chain Analytics:

1. **Logistics Delay Prediction** (Classification)
2. **Revenue Forecast** (Regression/Time Series)
3. **Customer Churn Prediction** (Classification)

Tất cả models sử dụng **Feature Store dùng chung** để tối ưu hóa việc tái sử dụng features và dễ dàng mở rộng.

---

## 🏗️ KIẾN TRÚC FEATURE STORE

### Cấu trúc Feature Store

Feature Store được lưu dưới dạng Parquet files trong `data/features/`:

```
data/features/
├── features_logistics.parquet      # Features cho logistics delay (1 row = 1 shipment)
├── features_forecast.parquet      # Features cho revenue forecast (1 row = 1 time-step x region x category)
└── features_churn.parquet          # Features cho churn (1 row = 1 customer x snapshot_date)
```

### Features Dùng Chung

#### 1. Time-based Features (dùng cho cả 3 models)
- `year`, `month`, `quarter`, `week`, `day_of_week`, `day_of_month`
- `is_weekend`, `is_month_start`, `is_month_end`
- `month_sin`, `month_cos` (sin/cos encoding cho seasonality)
- `day_of_week_sin`, `day_of_week_cos`
- `is_holiday_season`

#### 2. Weather Features (dùng cho logistics + forecast)
- `temperature_2m_mean`
- `precipitation_sum`
- `wind_speed_10m_mean`
- `relative_humidity_2m_mean`
- `weather_risk_level` (1-5, calculated)

#### 3. Customer Features (dùng cho churn + recommender)
- `rfm_recency`, `rfm_frequency`, `rfm_monetary`
- `rfm_recency_score`, `rfm_frequency_score`, `rfm_monetary_score`
- `rfm_score`, `rfm_segment`
- `total_orders`, `total_sales`, `avg_order_value`
- `category_diversity`, `days_since_first_order`

#### 4. Product/Location Features
- `category_popularity`
- `Order Country`, `Order City`
- `shipping_mode_*` (one-hot encoded)

---

## 📊 MODEL 1: LOGISTICS DELAY PREDICTION

### Mục tiêu
Dự đoán xác suất giao hàng trễ cho mỗi shipment/order item.

### Target
- `target_late_delivery`: Binary (0 = on-time, 1 = late)
- Định nghĩa: `shipping_duration_real > shipping_duration_scheduled` hoặc `Late_delivery_risk = 1`

### Features Chính
- **Time features:** month, day_of_week, is_weekend, seasonality
- **Shipping features:** shipping_duration_scheduled, shipping_duration_real, shipping_duration_diff
- **Weather features:** temperature, precipitation, wind_speed, weather_risk_level
- **Product features:** category_popularity, Category Name
- **Location features:** Order Country, Order City
- **Rolling window:** sales_7d_avg, sales_30d_avg, order_count_7d

### Models
- **Logistic Regression** (baseline)
- **XGBoost** (best performance)

### Evaluation Metrics
- **AUC-ROC**
- **PR-AUC** (Precision-Recall AUC)
- **F1 Score**
- **Classification Report**

### Training Script
```bash
python scripts/train_model_logistics_delay.py
```

### Output Files
- `models/logistics_delay_model.pkl`
- `models/logistics_delay_preprocessor.pkl`
- `models/logistics_delay_feature_schema.json`
- `models/logistics_delay_metrics.json`

---

## 📈 MODEL 2: REVENUE FORECAST

### Mục tiêu
Dự báo doanh thu cho kỳ tiếp theo (theo region/category hoặc tổng thể).

### Target
- `target_revenue`: Doanh thu tại time-step T
- Aggregation: Theo ngày + region + category

### Features Chính
- **Time features:** year, month, quarter, day_of_week, seasonality
- **Lag features:** revenue_lag_1d, revenue_lag_7d, revenue_lag_30d
- **Rolling statistics:** revenue_7d_avg, revenue_30d_avg, revenue_7d_std
- **Weather features:** temperature, precipitation, wind_speed
- **Order features:** order_count, customer_count

### Models
- **Random Forest Regressor**
- **XGBoost Regressor**

### Evaluation Metrics
- **MAE** (Mean Absolute Error)
- **RMSE** (Root Mean Squared Error)
- **MAPE** (Mean Absolute Percentage Error)
- **R²** (R-squared)

### Training Script
```bash
python scripts/train_model_revenue_forecast.py
```

### Output Files
- `models/revenue_forecast_model.pkl`
- `models/revenue_forecast_preprocessor.pkl`
- `models/revenue_forecast_feature_schema.json`
- `models/revenue_forecast_metrics.json`

---

## 👥 MODEL 3: CUSTOMER CHURN PREDICTION

### Mục tiêu
Dự đoán xác suất khách hàng churn (không mua lại).

### Target
- `target_churn`: Binary (0 = active, 1 = churn)
- **Định nghĩa churn:** `rfm_recency > 180 days` (không mua trong 180 ngày)

### Features Chính
- **RFM features:** rfm_recency, rfm_frequency, rfm_monetary, rfm_scores
- **Customer history:** total_orders, total_sales, avg_order_value, sales_std
- **Behavior features:** category_diversity, days_since_first_order
- **Snapshot date:** snapshot_date (để tính features tại thời điểm đó)

### Models
- **Logistic Regression** (baseline)
- **XGBoost** (best performance)

### Evaluation Metrics
- **AUC-ROC**
- **PR-AUC**
- **F1 Score**
- **Precision@TopK** (Precision ở top-K khách có nguy cơ churn cao nhất)

### Training Script
```bash
python scripts/train_model_churn.py
```

### Output Files
- `models/churn_model.pkl`
- `models/churn_preprocessor.pkl`
- `models/churn_feature_schema.json`
- `models/churn_metrics.json`

---

## 🔄 WORKFLOW TRIỂN KHAI

### Bước 1: Build Feature Store

```bash
python scripts/preprocess_and_build_feature_store.py
```

**Chức năng:**
- Đọc raw data (supply chain + weather)
- Thực hiện preprocessing:
  - Chuẩn hóa ngày tháng
  - Tính RFM features
  - Tính distance (nếu có lat/lon)
  - Resample time series
  - Xử lý missing values
  - Tính skew và transform
  - Tránh data leakage
- Sinh ra 3 bộ features:
  - `features_logistics.parquet`
  - `features_forecast.parquet`
  - `features_churn.parquet`

**Thời gian:** ~5-10 phút (tùy dataset size)

### Bước 2: Train Models

#### Train Logistics Delay Model
```bash
python scripts/train_model_logistics_delay.py
```

#### Train Revenue Forecast Model
```bash
python scripts/train_model_revenue_forecast.py
```

#### Train Churn Model
```bash
python scripts/train_model_churn.py
```

**Thời gian:** ~2-5 phút mỗi model

### Bước 3: Test API Endpoints

Sau khi train xong, models sẽ được load tự động khi gọi API.

```bash
# Start server
uvicorn app.main:app --reload

# Test endpoints
curl -X POST "http://127.0.0.1:8000/ml/logistics/delay" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_duration_scheduled": 5,
    "temperature": 25.0,
    "precipitation": 10.0,
    "is_weekend": 0,
    "month": 6
  }'
```

---

## 🔌 API ENDPOINTS

### 1. POST `/ml/logistics/delay`

**Mục đích:** Dự đoán rủi ro giao hàng trễ

**Request Body:**
```json
{
  "order_id": "12345",
  "customer_id": "67890",
  "shipping_duration_scheduled": 5,
  "temperature": 25.0,
  "precipitation": 10.0,
  "wind_speed": 15.0,
  "weather_risk_level": 2,
  "is_weekend": 0,
  "month": 6,
  "category_name": "Electronics",
  "sales": 500.0
}
```

**Response:**
```json
{
  "status": "success",
  "prediction": {
    "late_risk_prob": 0.35,
    "late_risk_label": 0,
    "top_features": [
      {"feature": "weather_risk_level", "importance": 0.25},
      {"feature": "shipping_duration_scheduled", "importance": 0.20}
    ]
  }
}
```

### 2. POST `/ml/revenue/forecast`

**Mục đích:** Dự báo doanh thu

**Request Body:**
```json
{
  "region": "United States",
  "category": "Electronics",
  "forecast_date": "2024-07-01",
  "revenue_lag_7d": 50000.0,
  "revenue_lag_30d": 200000.0,
  "revenue_7d_avg": 55000.0,
  "revenue_30d_avg": 52000.0,
  "month": 7,
  "day_of_week": 1,
  "temperature": 28.0
}
```

**Response:**
```json
{
  "status": "success",
  "prediction": {
    "forecasted_revenue": 58000.0,
    "confidence_range": {
      "lower": 46400.0,
      "upper": 69600.0
    }
  }
}
```

### 3. POST `/ml/customer/churn`

**Mục đích:** Dự đoán churn khách hàng

**Request Body:**
```json
{
  "customer_id": "12345",
  "rfm_recency": 120,
  "rfm_frequency": 5,
  "rfm_monetary": 5000.0,
  "total_orders": 10,
  "total_sales": 5000.0,
  "avg_order_value": 500.0,
  "days_since_first_order": 365
}
```

**Response:**
```json
{
  "status": "success",
  "prediction": {
    "churn_prob": 0.15,
    "churn_label": 0
  }
}
```

### 4. GET `/ml/models/status`

**Mục đích:** Kiểm tra trạng thái models

**Response:**
```json
{
  "status": "success",
  "models": {
    "logistics_delay": {
      "loaded": true,
      "path": "models/logistics_delay_model.pkl"
    },
    "revenue_forecast": {
      "loaded": true,
      "path": "models/revenue_forecast_model.pkl"
    },
    "churn": {
      "loaded": true,
      "path": "models/churn_model.pkl"
    }
  }
}
```

---

## 🎯 BEST PRACTICES ĐÃ ÁP DỤNG

### 1. Preprocessing
- ✅ **Chuẩn hóa ngày tháng:** ISO 8601 format
- ✅ **RFM Analysis:** Recency, Frequency, Monetary với scores
- ✅ **Distance calculation:** Haversine formula (nếu có lat/lon)
- ✅ **Time-series resample:** Aggregation theo ngày/tuần/tháng
- ✅ **Missing value handling:** Fill với 0 hoặc median
- ✅ **Skew handling:** Log transform cho skewed features
- ✅ **Categorical encoding:** Label encoding

### 2. Data Leakage Prevention
- ✅ **Time-based split:** Train đến T, test T+1..T+k
- ✅ **RFM tính tại snapshot_date:** Chỉ dùng dữ liệu trước snapshot
- ✅ **Lag features:** Chỉ dùng past data
- ✅ **Rolling windows:** Tính từ past data

### 3. Feature Engineering
- ✅ **Time features:** Year, month, quarter, day_of_week, seasonality
- ✅ **Weather risk level:** Calculated từ precipitation, wind, temperature
- ✅ **Rolling statistics:** 7-day, 30-day averages
- ✅ **Lag features:** 1-day, 7-day, 30-day lags

### 4. Model Training
- ✅ **Class imbalance handling:** Class weights, scale_pos_weight
- ✅ **Multiple models:** Logistic Regression + XGBoost/Random Forest
- ✅ **Model selection:** Chọn best model dựa trên metrics
- ✅ **Feature importance:** Track và return top features

### 5. Evaluation
- ✅ **Time-based split:** Không dùng random split
- ✅ **Multiple metrics:** AUC, PR-AUC, F1, MAPE, RMSE, etc.
- ✅ **Classification reports:** Chi tiết cho classification models

---

## 📁 CẤU TRÚC FILES

```
D:\Data_F\
├── scripts/
│   ├── preprocess_and_build_feature_store.py    # Build feature store
│   ├── train_model_logistics_delay.py           # Train logistics model
│   ├── train_model_revenue_forecast.py          # Train forecast model
│   └── train_model_churn.py                     # Train churn model
├── app/
│   ├── services/
│   │   └── ml_service.py                        # ML service (load & predict)
│   └── routers/
│       └── ml_api.py                            # ML API endpoints
├── data/
│   └── features/
│       ├── features_logistics.parquet
│       ├── features_forecast.parquet
│       └── features_churn.parquet
├── models/
│   ├── logistics_delay_model.pkl
│   ├── logistics_delay_preprocessor.pkl
│   ├── logistics_delay_feature_schema.json
│   ├── logistics_delay_metrics.json
│   ├── revenue_forecast_model.pkl
│   ├── revenue_forecast_preprocessor.pkl
│   ├── revenue_forecast_feature_schema.json
│   ├── revenue_forecast_metrics.json
│   ├── churn_model.pkl
│   ├── churn_preprocessor.pkl
│   ├── churn_feature_schema.json
│   └── churn_metrics.json
└── docs/
    └── ML_IMPLEMENTATION_OVERVIEW.md            # File này
```

---

## 🚀 HƯỚNG MỞ RỘNG

Feature Store hiện tại đã được thiết kế để dễ dàng mở rộng cho các use cases khác:

### 1. Product Recommendation
- **Features:** Customer RFM, category preferences, purchase history
- **Reuse:** RFM features từ churn, category features từ logistics

### 2. Inventory Optimization
- **Features:** Demand forecast, lead time, seasonality
- **Reuse:** Revenue forecast features, time features

### 3. Dynamic Pricing
- **Features:** Demand, competition, seasonality, weather
- **Reuse:** Revenue forecast features, weather features

### 4. Digital Twin & Generative Risk Planning
- **Features:** Historical patterns, weather, logistics performance
- **Reuse:** Tất cả features từ 3 models hiện tại

---

## ⚠️ LƯU Ý QUAN TRỌNG

1. **Data Leakage:** Luôn đảm bảo time-based split, không dùng future data
2. **Missing Features:** Nếu thiếu features trong request, sẽ dùng default value = 0
3. **Model Updates:** Cần retrain models khi có dữ liệu mới
4. **Feature Drift:** Monitor feature distributions để phát hiện drift
5. **Performance:** Models được cache trong memory sau lần load đầu tiên

---

## 📞 TROUBLESHOOTING

### Lỗi: "Model not found"
**Giải pháp:** Chạy training script tương ứng trước

### Lỗi: "Features file not found"
**Giải pháp:** Chạy `preprocess_and_build_feature_store.py` trước

### Lỗi: "Missing required features"
**Giải pháp:** Kiểm tra request body có đủ features theo schema

### Performance chậm
**Giải pháp:** 
- Models được cache sau lần load đầu tiên
- Có thể optimize bằng cách pre-load models khi start server

---

## ✅ CHECKLIST TRIỂN KHAI

- [x] Feature Store preprocessing script
- [x] Logistics delay training script
- [x] Revenue forecast training script
- [x] Churn training script
- [x] ML service với load & predict functions
- [x] ML API router với endpoints
- [x] Documentation

---

**Tài liệu này sẽ được cập nhật khi có thêm models hoặc features mới.**

