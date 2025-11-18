# HƯỚNG DẪN CHẠY ML MODELS

## 📋 Tổng quan

Dự án này bao gồm 3 ML models:
1. **Logistics Delay Prediction** - Dự đoán giao hàng trễ
2. **Revenue Forecast** - Dự báo doanh thu
3. **Customer Churn Prediction** - Dự đoán churn khách hàng

---

## 🚀 QUY TRÌNH CHẠY

### Bước 1: Cài đặt Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate.bat  # Windows
# hoặc
source venv/bin/activate   # Linux/Mac

# Install ML libraries
pip install -r requirements.txt
```

### Bước 2: Build Feature Store

```bash
python scripts/preprocess_and_build_feature_store.py
```

**Thời gian:** ~5-10 phút  
**Output:** 
- `data/features/features_logistics.parquet`
- `data/features/features_forecast.parquet`
- `data/features/features_churn.parquet`

### Bước 3: Train Models

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
**Output:** Models và preprocessors trong `models/`

### Bước 4: Test API

```bash
# Start server
uvicorn app.main:app --reload

# Test endpoints (xem docs/ML_IMPLEMENTATION_OVERVIEW.md)
```

---

## 📊 KẾT QUẢ MONG ĐỢI

### Logistics Delay Model
- **AUC:** > 0.70
- **F1 Score:** > 0.60
- **Best Model:** XGBoost hoặc Logistic Regression

### Revenue Forecast Model
- **MAPE:** < 30%
- **RMSE:** Tùy scale của revenue
- **Best Model:** XGBoost hoặc Random Forest

### Churn Model
- **AUC:** > 0.75
- **Precision@Top100:** > 0.50
- **Best Model:** XGBoost hoặc Logistic Regression

---

## ⚠️ LƯU Ý

1. **Data Leakage:** Scripts đã implement time-based split, không dùng random split
2. **Missing Features:** Nếu thiếu features trong request, sẽ dùng default = 0
3. **Model Updates:** Cần retrain khi có dữ liệu mới
4. **Performance:** Models được cache sau lần load đầu tiên

---

## 🔍 TROUBLESHOOTING

### Lỗi: "Features file not found"
→ Chạy `preprocess_and_build_feature_store.py` trước

### Lỗi: "Model not found"
→ Chạy training script tương ứng

### Lỗi: Memory error
→ Giảm số lượng snapshot dates trong churn features hoặc sample data

---

Xem chi tiết trong `docs/ML_IMPLEMENTATION_OVERVIEW.md`

