# ML QUICK START GUIDE

**Ngày tạo:** 2024

---

## ⚡ QUICK START (5 BƯỚC)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Build Feature Store
```bash
python scripts/preprocess_and_build_feature_store.py
```
⏱️ Thời gian: ~5-10 phút

### 3. Train All Models
```bash
python scripts/train_model_logistics_delay.py
python scripts/train_model_revenue_forecast.py
python scripts/train_model_churn.py
```
⏱️ Thời gian: ~10-15 phút tổng cộng

### 4. Start Server
```bash
uvicorn app.main:app --reload
```

### 5. Test API
```bash
# Test logistics delay
curl -X POST "http://127.0.0.1:8000/ml/logistics/delay" \
  -H "Content-Type: application/json" \
  -d '{"shipping_duration_scheduled": 5, "temperature": 25.0, "is_weekend": 0}'

# Test revenue forecast
curl -X POST "http://127.0.0.1:8000/ml/revenue/forecast" \
  -H "Content-Type: application/json" \
  -d '{"region": "United States", "month": 7, "revenue_7d_avg": 50000.0}'

# Test churn
curl -X POST "http://127.0.0.1:8000/ml/customer/churn" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "12345", "rfm_recency": 120, "rfm_frequency": 5}'
```

---

## 📁 FILES ĐÃ TẠO

### Scripts
- ✅ `scripts/preprocess_and_build_feature_store.py` - Build feature store
- ✅ `scripts/train_model_logistics_delay.py` - Train logistics model
- ✅ `scripts/train_model_revenue_forecast.py` - Train forecast model
- ✅ `scripts/train_model_churn.py` - Train churn model

### Services
- ✅ `app/services/ml_service.py` - ML service (load & predict)

### API
- ✅ `app/routers/ml_api.py` - ML API endpoints

### Documentation
- ✅ `docs/ML_IMPLEMENTATION_OVERVIEW.md` - Chi tiết implementation
- ✅ `docs/ML_QUICK_START.md` - File này

---

## 🎯 FEATURE STORE STRUCTURE

### Logistics Features (1 row = 1 shipment)
- Time features (year, month, day_of_week, seasonality)
- Shipping features (duration, scheduled vs real)
- Weather features (temperature, precipitation, wind, risk level)
- Product features (category, popularity)
- Rolling windows (7d, 30d averages)

### Forecast Features (1 row = 1 time-step x region x category)
- Time features
- Lag features (1d, 7d, 30d)
- Rolling statistics (7d, 30d avg, std)
- Weather features
- Order counts

### Churn Features (1 row = 1 customer x snapshot_date)
- RFM features (Recency, Frequency, Monetary + scores)
- Customer history (total_orders, total_sales, avg_order_value)
- Behavior features (category_diversity, days_since_first_order)
- Snapshot date (để tính features tại thời điểm đó)

---

## 🔌 API ENDPOINTS

### POST `/ml/logistics/delay`
Predict late delivery risk

### POST `/ml/revenue/forecast`
Forecast revenue

### POST `/ml/customer/churn`
Predict customer churn

### GET `/ml/models/status`
Check model status

---

## 📊 EXPECTED PERFORMANCE

- **Logistics Delay:** AUC > 0.70
- **Revenue Forecast:** MAPE < 30%
- **Churn:** AUC > 0.75, Precision@Top100 > 0.50

---

Xem chi tiết trong `docs/ML_IMPLEMENTATION_OVERVIEW.md`

