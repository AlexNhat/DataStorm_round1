# 📚 INDEX – DANH MỤC TÀI LIỆU & NOTEBOOK AI

**Dự án:** DataCo Supply Chain AI Platform  
**Ngày cập nhật:** 2024  
**Mục đích:** Trang mục lục giúp điều hướng nhanh đến các tài liệu, notebooks, và source code liên quan đến AI/ML

---

## 📖 TỔNG QUAN

- **[ML_OVERVIEW.md](ML_OVERVIEW.md)** - Tổng quan hệ thống AI, kiến trúc, và định hướng phát triển

---

## 1. 📊 DATA & FEATURE STORE

### 1.1. Dữ liệu Merged

- **File chính:** `data/merged_supply_weather_clean.parquet`
  - Dataset đã được gộp và chuẩn hóa từ Supply Chain + Weather
  - ~180,000 records
  - Sử dụng bởi tất cả 3 models

### 1.2. Scripts xử lý dữ liệu

- **`scripts/merge_supplychain_weather.py`**
  - Gộp 2 dataset: Supply Chain + Weather
  - Chuẩn hóa dates, countries, locations
  - Xử lý missing values, outliers
  - Tính toán derived features (lead_time, weather_risk_level, time features)
  - Output: `data/merged_supply_weather_clean.parquet`

- **`scripts/preprocess_and_build_feature_store.py`**
  - Xây dựng Feature Store cho 3 models
  - Tính toán RFM, rolling statistics, lag features
  - Output: `data/features_logistics.parquet`, `data/features_forecast.parquet`, `data/features_churn.parquet`

### 1.3. Dữ liệu gốc

- **`data/DataCoSupplyChainDataset.csv`**
  - Dữ liệu supply chain gốc (~180k records)
  - Orders, customers, products, shipping, profit, late_delivery_risk

- **`data/geocoded_weather.csv`**
  - Dữ liệu thời tiết đã geocode (~180k records)
  - Temperature, precipitation, wind speed, humidity, etc.

---

## 2. 🤖 MÔ HÌNH AI

### 🔹 2.1. 🚚 Late Delivery Prediction

**Mục tiêu:** Dự đoán rủi ro giao hàng trễ dựa trên đơn hàng, shipping, và thời tiết.

#### Tài liệu
- 📄 **[model_late_delivery.md](model_late_delivery.md)**
  - Mô tả chi tiết mô hình
  - Features, preprocessing, model selection
  - Kết quả, hạn chế, hướng phát triển

#### Notebook
- 📓 **[model_late_delivery.ipynb](../notebooks/model_late_delivery.ipynb)**
  - EDA, feature engineering, training, evaluation
  - Visualizations: ROC curves, confusion matrices, feature importance
  - Chạy độc lập, không cần server

#### Source Code
- **Training:** `scripts/train_model_logistics_delay.py`
  - Load features, train models (Logistic Regression, XGBoost)
  - Evaluate, save model + preprocessor + schema
  - Output: `models/logistics_delay_model.pkl`

- **Service:** `app/services/ml_service.py`
  - Functions: `load_logistics_delay_model()`, `predict_logistics_delay()`

- **API:** `app/routers/ml_api.py`
  - Endpoint: `POST /ml/logistics/delay`
  - Web page: `GET /ml/late-delivery`

#### Model Files
- `models/late_delivery_xgb_model.pkl` - Trained XGBoost model
- `models/late_delivery_scaler.pkl` - Scaler
- `models/late_delivery_feature_schema.json` - Feature schema

---

### 🔹 2.2. 📈 Revenue/Demand Forecast

**Mục tiêu:** Dự báo doanh thu hoặc nhu cầu theo thời gian, có thể theo tổng hệ thống hoặc theo từng quốc gia.

#### Tài liệu
- 📄 **[model_revenue_forecast.md](model_revenue_forecast.md)**
  - Mô tả chi tiết mô hình
  - Aggregation, lag features, rolling stats
  - Kết quả, hạn chế, hướng phát triển

#### Notebook
- 📓 **[model_revenue_forecast.ipynb](../notebooks/model_revenue_forecast.ipynb)**
  - Time series aggregation, feature engineering
  - Training (Linear Regression, Random Forest, XGBoost)
  - Visualizations: Actual vs Predicted, time series plots, feature importance
  - Chạy độc lập, không cần server

#### Source Code
- **Training:** `scripts/train_model_revenue_forecast.py`
  - Load features, train models (Linear Regression, XGBoost)
  - Evaluate (MAE, RMSE, MAPE, R²)
  - Output: `models/revenue_forecast_model.pkl`

- **Service:** `app/services/ml_service.py`
  - Functions: `load_revenue_forecast_model()`, `predict_revenue()`

- **API:** `app/routers/ml_api.py`
  - Endpoint: `POST /ml/revenue/forecast`
  - Web page: `GET /ml/revenue-forecast`

#### Model Files
- `models/revenue_forecast_xgb_model.pkl` - Trained XGBoost Regressor
- `models/revenue_forecast_feature_schema.json` - Feature schema

---

### 🔹 2.3. 👥 Customer Churn Prediction

**Mục tiêu:** Xác định khách hàng có nguy cơ rời bỏ (churn) dựa trên RFM và hành vi mua hàng.

#### Tài liệu
- 📄 **[model_customer_churn.md](model_customer_churn.md)**
  - Mô tả chi tiết mô hình
  - RFM calculation, churn definition (Recency > 180 days)
  - Kết quả, hạn chế, hướng phát triển

#### Notebook
- 📓 **[model_customer_churn.ipynb](../notebooks/model_customer_churn.ipynb)**
  - RFM calculation, customer features
  - Training với SMOTE (xử lý class imbalance)
  - Visualizations: ROC curves, confusion matrices, Precision@TopK
  - Chạy độc lập, không cần server

#### Source Code
- **Training:** `scripts/train_model_churn.py`
  - Load features, train models (Logistic Regression, XGBoost)
  - Evaluate (AUC, F1, Precision@TopK)
  - Output: `models/churn_model.pkl`

- **Service:** `app/services/ml_service.py`
  - Functions: `load_churn_model()`, `predict_churn()`

- **API:** `app/routers/ml_api.py`
  - Endpoint: `POST /ml/customer/churn`
  - Web page: `GET /ml/customer-churn`

#### Model Files
- `models/churn_xgb_model.pkl` - Trained XGBoost model
- `models/churn_scaler.pkl` - Scaler
- `models/churn_feature_schema.json` - Feature schema

---

## 3. 💻 SOURCE CODE (SCRIPTS)

### 3.1. ETL & Data Processing

- **`scripts/merge_supplychain_weather.py`**
  - Gộp và chuẩn hóa 2 dataset
  - Output: `data/merged_supply_weather_clean.parquet`

- **`scripts/preprocess_and_build_feature_store.py`**
  - Xây dựng Feature Store cho 3 models
  - Tính toán RFM, rolling stats, lag features
  - Output: 3 parquet files (logistics, forecast, churn)

### 3.2. Model Training

- **`scripts/train_model_logistics_delay.py`**
  - Train Late Delivery Prediction model
  - Models: Logistic Regression, XGBoost
  - Output: Model files + evaluation results

- **`scripts/train_model_revenue_forecast.py`**
  - Train Revenue Forecast model
  - Models: Linear Regression, Random Forest, XGBoost
  - Output: Model files + evaluation results

- **`scripts/train_model_churn.py`**
  - Train Customer Churn model
  - Models: Logistic Regression, XGBoost (với SMOTE)
  - Output: Model files + evaluation results

### 3.3. Utilities

- **`scripts/generate_data_quality_report.py`**
  - Phân tích chất lượng dữ liệu
  - Output: `docs/data_quality_report.md`

- **`scripts/convert_py_to_notebook.py`**
  - Convert Python scripts thành Jupyter notebooks
  - (Utility script)

---

## 4. 🌐 DASHBOARD & API

### 4.1. FastAPI Application

- **`app/main.py`**
  - FastAPI app chính
  - Đăng ký routers (dashboard, ml_api)
  - Static files, templates config

### 4.2. ML API

- **`app/routers/ml_api.py`**
  - REST API endpoints:
    - `POST /ml/logistics/delay` - Dự đoán late delivery
    - `POST /ml/revenue/forecast` - Dự báo doanh thu
    - `POST /ml/customer/churn` - Dự đoán churn
    - `GET /ml/models/status` - Trạng thái models
  - Web pages:
    - `GET /ml/late-delivery` - Trang Late Delivery
    - `GET /ml/revenue-forecast` - Trang Revenue Forecast
    - `GET /ml/customer-churn` - Trang Customer Churn

### 4.3. ML Service

- **`app/services/ml_service.py`**
  - Functions để load models và make predictions:
    - `get_logistics_service()`, `predict_logistics_delay()`
    - `get_revenue_service()`, `predict_revenue()`
    - `get_churn_service()`, `predict_churn()`

### 4.4. Templates (Web Pages)

- **`app/templates/ml_late_delivery.html`**
  - Form nhập thông tin đơn hàng
  - Hiển thị kết quả prediction

- **`app/templates/ml_revenue_forecast.html`**
  - Form nhập thông tin dự báo
  - Hiển thị forecasted revenue + confidence interval

- **`app/templates/ml_customer_churn.html`**
  - Form nhập thông tin khách hàng
  - Hiển thị churn probability + recommendations

### 4.5. Dashboard

- **`app/routers/dashboard.py`**
  - Dashboard chính với KPI, biểu đồ, filters
  - Endpoint: `GET /dashboard`

- **`app/templates/dashboard.html`**
  - Giao diện dashboard

---

## 5. 📚 TÀI LIỆU BỔ SUNG

### 5.1. Tài liệu dự án

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**
  - Tổng hợp toàn bộ dự án
  - Kiến trúc, modules, cách chạy

- **[data_improvement_plan.md](data_improvement_plan.md)**
  - Kế hoạch cải tiến dữ liệu
  - Star Schema, Feature Store design

- **[README_dashboard.md](README_dashboard.md)**
  - Hướng dẫn sử dụng dashboard

### 5.2. Tài liệu ML

- **[ML_IMPLEMENTATION_OVERVIEW.md](ML_IMPLEMENTATION_OVERVIEW.md)**
  - Chi tiết implementation của 3 models
  - Feature building, execution steps

- **[ML_QUICK_START.md](ML_QUICK_START.md)** (nếu có)
  - Quick start guide cho ML workflow

- **[ML_MODELS_GUIDE.md](ML_MODELS_GUIDE.md)** (nếu có)
  - Hướng dẫn sử dụng ML models

### 5.3. Báo cáo

- **[data_quality_report.md](data_quality_report.md)**
  - Báo cáo chất lượng dữ liệu
  - Missing values, outliers, format issues

---

## 6. 🚀 GỢI Ý MỞ RỘNG AI

### 6.1. Models tương lai

**Inventory Optimization:**
- Dự đoán nhu cầu sản phẩm để tối ưu hóa inventory
- Reinforcement Learning cho policy optimization
- Multi-objective: Minimize cost + Maximize service level

**Dynamic Pricing:**
- Điều chỉnh giá dựa trên demand forecast, competitor pricing
- Price elasticity models
- Revenue optimization

**Product Recommendation:**
- Collaborative filtering, content-based filtering
- Cross-sell, up-sell opportunities
- Personalization dựa trên purchase history

**Anomaly Detection:**
- Phát hiện đơn hàng bất thường (fraud, errors)
- Phát hiện outliers trong revenue, churn rate
- Real-time alerting

**Generative Supply Chain Planning:**
- Sử dụng LLM để generate scenarios và recommendations
- "What-if" analysis
- Natural language queries về supply chain

### 6.2. MLOps & Infrastructure

**Model Monitoring:**
- Drift detection (data drift, concept drift)
- Performance tracking dashboard
- Alerting khi model performance giảm

**AutoML Pipeline:**
- Tự động tìm best model và hyperparameters
- Auto-retrain khi có dữ liệu mới
- A/B testing framework

**Feature Store nâng cao:**
- Real-time feature serving
- Feature versioning
- Feature lineage tracking

**Model Serving:**
- Batch predictions (scheduled jobs)
- Real-time predictions (API)
- Model versioning và rollback

### 6.3. Chuẩn hóa scale MLOps

**CI/CD cho ML:**
- Automated testing (unit tests, integration tests)
- Model validation trước khi deploy
- Automated deployment pipeline

**Infrastructure:**
- Containerization (Docker)
- Orchestration (Kubernetes)
- Distributed training (nếu cần)

**Monitoring & Observability:**
- Model performance metrics
- Prediction latency
- Error tracking
- Business metrics (revenue impact, cost savings)

---

## 7. 🔗 LIÊN KẾT NOTEBOOK & API

### 7.1. Flow: Notebook → Model → API → Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: NOTEBOOK (Exploration & Development)              │
├─────────────────────────────────────────────────────────────┤
│  notebooks/model_*.ipynb                                    │
│  • EDA, feature engineering                                 │
│  • Model training, evaluation                              │
│  • Visualizations                                           │
│  • Chạy độc lập, không cần server                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: TRAINING SCRIPT (Production Training)             │
├─────────────────────────────────────────────────────────────┤
│  scripts/train_model_*.py                                  │
│  • Load features từ Feature Store                          │
│  • Train models với hyperparameters đã tune                │
│  • Save: model.pkl, preprocessor.pkl, schema.json          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: ML SERVICE (Model Loading & Prediction)           │
├─────────────────────────────────────────────────────────────┤
│  app/services/ml_service.py                                 │
│  • load_*_model(): Load model + preprocessor + schema      │
│  • predict_*(): Nhận payload, build features, predict     │
│  • Return: prediction + probability + metadata             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: API ENDPOINTS (REST API)                           │
├─────────────────────────────────────────────────────────────┤
│  app/routers/ml_api.py                                      │
│  • POST /ml/logistics/delay                                 │
│  • POST /ml/revenue/forecast                                │
│  • POST /ml/customer/churn                                  │
│  • Validation với Pydantic                                  │
│  • Error handling                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: WEB PAGES (User Interface)                        │
├─────────────────────────────────────────────────────────────┤
│  app/templates/ml_*.html                                    │
│  • Form nhập input                                          │
│  • Gọi API endpoints                                        │
│  • Hiển thị kết quả với visualizations                     │
│  • URL: /ml/late-delivery, /ml/revenue-forecast, etc.       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2. Cách sử dụng

**1. Development (Notebook):**
```bash
# Mở notebook trong Jupyter
jupyter notebook notebooks/model_late_delivery.ipynb

# Chạy từng cell để:
# - Explore data
# - Engineer features
# - Train models
# - Evaluate results
```

**2. Production Training:**
```bash
# Chạy training script
python scripts/train_model_late_delivery.py

# Output: models/late_delivery_xgb_model.pkl
```

**3. API Usage:**
```bash
# Start server
uvicorn app.main:app --reload

# Test API
curl -X POST http://127.0.0.1:8000/ml/logistics/delay \
  -H "Content-Type: application/json" \
  -d '{"order_date": "2024-01-15", "temperature": 25.5, ...}'
```

**4. Web Interface:**
```
# Truy cập trong browser
http://127.0.0.1:8000/ml/late-delivery
http://127.0.0.1:8000/ml/revenue-forecast
http://127.0.0.1:8000/ml/customer-churn
```

---

## 8. 📋 QUICK REFERENCE

### 8.1. File paths quan trọng

| Loại | Đường dẫn |
|------|----------|
| **Data** | `data/merged_supply_weather_clean.parquet` |
| **Notebooks** | `notebooks/model_*.ipynb` |
| **Training Scripts** | `scripts/train_model_*.py` |
| **Models** | `models/*_model.pkl` |
| **Docs** | `docs/model_*.md` |
| **API** | `app/routers/ml_api.py` |
| **Service** | `app/services/ml_service.py` |
| **Templates** | `app/templates/ml_*.html` |

### 8.2. API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/ml/logistics/delay` | POST | Dự đoán late delivery |
| `/ml/revenue/forecast` | POST | Dự báo doanh thu |
| `/ml/customer/churn` | POST | Dự đoán churn |
| `/ml/models/status` | GET | Trạng thái models |
| `/ml/late-delivery` | GET | Web page Late Delivery |
| `/ml/revenue-forecast` | GET | Web page Revenue Forecast |
| `/ml/customer-churn` | GET | Web page Customer Churn |

### 8.3. Execution Order

**Lần đầu setup:**
1. `python scripts/merge_supplychain_weather.py` → Tạo merged dataset
2. `python scripts/preprocess_and_build_feature_store.py` → Tạo Feature Store (optional)
3. `python scripts/train_model_*.py` → Train 3 models
4. `uvicorn app.main:app --reload` → Start server
5. Truy cập web pages hoặc gọi API

**Sử dụng hàng ngày:**
- Chỉ cần start server và sử dụng API/web pages
- Models đã được train và lưu sẵn

---

## 9. 📞 HỖ TRỢ & TÀI LIỆU THAM KHẢO

### 9.1. Tài liệu tham khảo

- **Scikit-learn:** https://scikit-learn.org/
- **XGBoost:** https://xgboost.readthedocs.io/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Pandas:** https://pandas.pydata.org/

### 9.2. Best Practices

- **Time-based split:** Luôn dùng cho time series và churn prediction
- **Avoid leakage:** Không dùng thông tin từ tương lai
- **Feature Store:** Dùng chung dataset merged để đảm bảo consistency
- **Model versioning:** Lưu model + preprocessor + schema cùng nhau

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0  
**Cập nhật lần cuối:** 2024

