# HƯỚNG DẪN SỬ DỤNG ML MODELS

## TỔNG QUAN

Dự án này bao gồm 3 ML models chính:
1. **Late Delivery Prediction** - Dự đoán giao hàng trễ
2. **Revenue/Demand Forecast** - Dự báo doanh thu
3. **Customer Churn Prediction** - Dự đoán khách hàng churn

Tất cả models sử dụng dataset đã được gộp và chuẩn hóa: `data/merged_supply_weather_clean.parquet`

---

## QUY TRÌNH THỰC HIỆN

### Bước 1: Merge và Chuẩn hóa Dữ liệu

**Script:** `scripts/merge_supplychain_weather.py`

```bash
python scripts/merge_supplychain_weather.py
```

**Output:**
- `data/merged_supply_weather.parquet` - Dataset đã gộp
- `data/merged_supply_weather_clean.parquet` - Dataset đã clean và chuẩn hóa ⭐

**Thời gian:** ~5-10 phút

**Chức năng:**
- Gộp supply chain + weather data
- Chuẩn hóa dates, countries, locations
- Xử lý missing values, outliers
- Tính toán features: lead_time, weather_risk_level, time features
- Hash sensitive data

---

### Bước 2: Chạy ML Models

#### Model 1: Late Delivery Prediction

**Script:** `notebooks/model_late_delivery.py`

```bash
python notebooks/model_late_delivery.py
```

**Output:**
- `models/late_delivery_xgb_model.pkl` - Trained model
- `models/late_delivery_scaler.pkl` - Scaler
- `docs/results_late_delivery.csv` - Results summary
- `docs/images/*.png` - Visualizations

**Thời gian:** ~5-10 phút

**Documentation:** `docs/model_late_delivery.md`

---

#### Model 2: Revenue Forecast

**Script:** `notebooks/model_revenue_forecast.py`

```bash
python notebooks/model_revenue_forecast.py
```

**Output:**
- `models/revenue_forecast_xgb_model.pkl` - Trained model
- `docs/results_revenue_forecast.csv` - Results summary
- `docs/images/*.png` - Visualizations

**Thời gian:** ~5-10 phút

**Documentation:** `docs/model_revenue_forecast.md`

---

#### Model 3: Customer Churn

**Script:** `notebooks/model_customer_churn.py`

```bash
python notebooks/model_customer_churn.py
```

**Output:**
- `models/churn_xgb_model.pkl` - Trained model
- `models/churn_scaler.pkl` - Scaler
- `docs/results_churn.csv` - Results summary
- `docs/images/*.png` - Visualizations

**Thời gian:** ~5-10 phút

**Documentation:** `docs/model_customer_churn.md`

---

## CẤU TRÚC THƯ MỤC

```
D:\Data_F\
├── data/
│   ├── DataCoSupplyChainDataset.csv          # Raw supply chain data
│   ├── geocoded_weather.csv                   # Raw weather data
│   ├── merged_supply_weather.parquet          # Merged dataset
│   └── merged_supply_weather_clean.parquet   # Clean dataset ⭐
│
├── scripts/
│   ├── merge_supplychain_weather.py           # Merge script
│   └── preprocess_and_build_feature_store.py  # Feature store (optional)
│
├── notebooks/
│   ├── model_late_delivery.py                  # Model 1 script
│   ├── model_revenue_forecast.py               # Model 2 script
│   └── model_customer_churn.py                 # Model 3 script
│
├── models/
│   ├── late_delivery_xgb_model.pkl            # Model 1
│   ├── revenue_forecast_xgb_model.pkl         # Model 2
│   └── churn_xgb_model.pkl                     # Model 3
│
└── docs/
    ├── model_late_delivery.md                  # Model 1 docs
    ├── model_revenue_forecast.md              # Model 2 docs
    ├── model_customer_churn.md                 # Model 3 docs
    ├── ML_MODELS_GUIDE.md                      # File này
    └── images/                                 # Visualizations
```

---

## DEPENDENCIES

Đảm bảo đã cài đặt các thư viện sau:

```bash
pip install pandas numpy scikit-learn xgboost matplotlib seaborn pyarrow joblib imbalanced-learn
```

Hoặc:

```bash
pip install -r requirements.txt
```

---

## CHẠY TẤT CẢ MODELS

### Script tự động (Windows)

Tạo file `run_all_models.bat`:

```batch
@echo off
echo ========================================
echo RUNNING ALL ML MODELS
echo ========================================

call venv\Scripts\activate.bat

echo [1/4] Merging datasets...
python scripts/merge_supplychain_weather.py
if errorlevel 1 (
    echo ERROR: Failed to merge datasets
    pause
    exit /b 1
)

echo.
echo [2/4] Training Late Delivery Model...
python notebooks/model_late_delivery.py

echo.
echo [3/4] Training Revenue Forecast Model...
python notebooks/model_revenue_forecast.py

echo.
echo [4/4] Training Churn Model...
python notebooks/model_customer_churn.py

echo.
echo ========================================
echo ALL MODELS COMPLETED!
echo ========================================
pause
```

### Script tự động (Linux/Mac)

Tạo file `run_all_models.sh`:

```bash
#!/bin/bash

echo "========================================"
echo "RUNNING ALL ML MODELS"
echo "========================================"

# Activate virtual environment
source venv/bin/activate

echo "[1/4] Merging datasets..."
python scripts/merge_supplychain_weather.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to merge datasets"
    exit 1
fi

echo ""
echo "[2/4] Training Late Delivery Model..."
python notebooks/model_late_delivery.py

echo ""
echo "[3/4] Training Revenue Forecast Model..."
python notebooks/model_revenue_forecast.py

echo ""
echo "[4/4] Training Churn Model..."
python notebooks/model_customer_churn.py

echo ""
echo "========================================"
echo "ALL MODELS COMPLETED!"
echo "========================================"
```

---

## SỬ DỤNG TRONG JUPYTER NOTEBOOK

Nếu muốn chạy trong Jupyter Notebook:

1. Convert Python scripts sang `.ipynb`:
   ```bash
   # Sử dụng jupytext hoặc manual conversion
   ```

2. Hoặc tạo notebook mới và import code từ scripts

3. Đảm bảo đã chạy merge script trước:
   ```python
   # In notebook
   !python scripts/merge_supplychain_weather.py
   ```

---

## TROUBLESHOOTING

### Lỗi: "File not found: merged_supply_weather_clean.parquet"

**Giải pháp:** Chạy merge script trước:
```bash
python scripts/merge_supplychain_weather.py
```

### Lỗi: "Module not found"

**Giải pháp:** Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

### Lỗi: "Out of memory"

**Giải pháp:**
- Giảm số lượng records (sample data)
- Tăng RAM hoặc sử dụng cloud

### Lỗi: "Class imbalance too severe"

**Giải pháp:**
- Điều chỉnh churn threshold (Model 3)
- Sử dụng SMOTE (đã có trong code)
- Điều chỉnh class weights

---

## KẾT QUẢ VÀ VISUALIZATIONS

Sau khi chạy models, kiểm tra:

1. **Results CSV:** `docs/results_*.csv`
2. **Visualizations:** `docs/images/*.png`
3. **Trained Models:** `models/*.pkl`

---

## NEXT STEPS

1. **Hyperparameter Tuning:**
   - Sử dụng GridSearchCV hoặc RandomSearchCV
   - Tối ưu hóa performance

2. **Model Deployment:**
   - Tích hợp vào FastAPI (đã có sẵn trong `app/services/ml_service.py`)
   - Tạo API endpoints (đã có sẵn trong `app/routers/ml_api.py`)

3. **Monitoring:**
   - Track model performance over time
   - Detect data drift
   - Retrain periodically

---

## TÀI LIỆU THAM KHẢO

- **Model 1:** `docs/model_late_delivery.md`
- **Model 2:** `docs/model_revenue_forecast.md`
- **Model 3:** `docs/model_customer_churn.md`
- **Feature Store:** `docs/ML_IMPLEMENTATION_OVERVIEW.md`

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

