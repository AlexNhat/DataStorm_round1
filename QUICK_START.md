# 🚀 QUICK START - CHẠY DỰ ÁN

## ⚡ CÁCH NHANH NHẤT

### Option 1: Chỉ chạy Dashboard (không cần ML models)

```bash
# Windows
run_server_venv.bat

# Hoặc
venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Truy cập:** http://127.0.0.1:8000/dashboard

---

### Option 2: Chạy đầy đủ với ML Models

#### Bước 1: Cài đặt ML libraries (nếu chưa có)
```bash
venv\Scripts\activate.bat
pip install scikit-learn xgboost pyarrow joblib shap
```

#### Bước 2: Build Feature Store & Train Models
```bash
# Chạy script tự động
run_ml_pipeline.bat

# Hoặc chạy từng bước:
python scripts/preprocess_and_build_feature_store.py
python scripts/train_model_logistics_delay.py
python scripts/train_model_revenue_forecast.py
python scripts/train_model_churn.py
```

#### Bước 3: Start Server
```bash
run_server_with_ml.bat

# Hoặc
venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 📍 CÁC URL QUAN TRỌNG

- **Dashboard:** http://127.0.0.1:8000/dashboard
- **API Docs:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health
- **ML API Status:** http://127.0.0.1:8000/ml/models/status

---

## 🔍 KIỂM TRA

### Kiểm tra server đang chạy:
```bash
curl http://127.0.0.1:8000/health
```

### Kiểm tra ML models:
```bash
curl http://127.0.0.1:8000/ml/models/status
```

---

## ⚠️ LƯU Ý

1. **Dashboard hoạt động ngay** mà không cần ML models
2. **ML models cần được train trước** khi sử dụng ML APIs
3. **Feature store cần được build trước** khi train models
4. **Thời gian:** 
   - Build features: ~5-10 phút
   - Train models: ~10-15 phút tổng cộng

---

## 🐛 TROUBLESHOOTING

### Lỗi: "Module not found"
→ Cài đặt dependencies: `pip install -r requirements.txt`

### Lỗi: "Features file not found"
→ Chạy: `python scripts/preprocess_and_build_feature_store.py`

### Lỗi: "Model not found"
→ Chạy training scripts tương ứng

### Server không start
→ Kiểm tra port 8000 có bị chiếm không: `netstat -ano | findstr :8000`

---

**Server đang chạy ở background. Truy cập http://127.0.0.1:8000/dashboard để xem dashboard!**

