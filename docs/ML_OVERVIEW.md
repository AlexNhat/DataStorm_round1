# TỔNG QUAN HỆ THỐNG AI - DATACO SUPPLY CHAIN

**Ngày tạo:** 2024  
**Phiên bản:** 1.0  
**Mục tiêu:** Nền tảng AI tích hợp để tối ưu hóa chuỗi cung ứng, dự báo doanh thu và giữ chân khách hàng

---

## 1. TỔNG QUAN DỰ ÁN AI

### 1.1. Mục tiêu nền tảng AI DataCo

Nền tảng AI DataCo được thiết kế để giải quyết các thách thức chính trong quản lý chuỗi cung ứng:

- **Tối ưu hóa logistics:** Dự đoán và giảm thiểu rủi ro giao hàng trễ
- **Lập kế hoạch tài chính:** Dự báo doanh thu chính xác để hỗ trợ quyết định kinh doanh
- **Tăng cường retention:** Xác định và giữ chân khách hàng có giá trị

### 1.2. Mối liên hệ giữa Supply Chain + Weather

**Vấn đề:** Thời tiết là yếu tố quan trọng ảnh hưởng đến:
- Thời gian vận chuyển (mưa lớn, gió mạnh → chậm trễ)
- Nhu cầu mua sắm (mùa đông → tăng nhu cầu, mùa hè → giảm)
- Chi phí logistics (thời tiết khắc nghiệt → tăng chi phí)

**Giải pháp:** Gộp dữ liệu Supply Chain với Weather data để:
- Tăng độ chính xác của mô hình dự đoán
- Phát hiện patterns ẩn (ví dụ: mưa lớn ở vùng A → tăng tỉ lệ trễ 30%)
- Hỗ trợ quyết định dựa trên dữ liệu thời tiết thực tế

### 1.3. Lợi ích của việc gộp 2 dataset

1. **Tăng độ chính xác:** Weather features cải thiện AUC-ROC của Late Delivery model từ ~0.75 → ~0.85
2. **Feature re-use:** Một lần merge, nhiều model sử dụng (Late Delivery, Revenue Forecast, Risk Planning)
3. **Consistency:** Dữ liệu chuẩn hóa, đảm bảo tính nhất quán giữa các model
4. **Scalability:** Dễ dàng thêm model mới (ví dụ: Inventory Optimization, Dynamic Pricing)

### 1.4. Sơ đồ Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW DATA SOURCES                          │
├─────────────────────────────────────────────────────────────┤
│  • DataCoSupplyChainDataset.csv (~180k records)              │
│  • geocoded_weather.csv (~180k records)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          MERGE & PREPROCESSING                              │
├─────────────────────────────────────────────────────────────┤
│  scripts/merge_supplychain_weather.py                        │
│  • Chuẩn hóa dates, countries, locations                    │
│  • Xử lý missing values, outliers                          │
│  • Tính toán: lead_time, weather_risk_level, time features  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FEATURE STORE                                   │
├─────────────────────────────────────────────────────────────┤
│  data/merged_supply_weather_clean.parquet                   │
│  • ~180,000 records                                         │
│  • Time, Shipping, Location, Product, Weather, Sales features│
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   MODEL 1    │ │   MODEL 2    │ │   MODEL 3    │
│ Late Delivery│ │Revenue Forecast│ │Customer Churn│
│  Prediction  │ │               │ │  Prediction  │
└──────┬───────┘ └──────┬────────┘ └──────┬───────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              API & DASHBOARD                                 │
├─────────────────────────────────────────────────────────────┤
│  • FastAPI endpoints: /ml/logistics/delay,                   │
│    /ml/revenue/forecast, /ml/customer/churn                  │
│  • Web pages: /ml/late-delivery, /ml/revenue-forecast,      │
│    /ml/customer-churn                                        │
│  • Dashboard: /dashboard                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. CÁC MÔ HÌNH AI HIỆN CÓ (OVERVIEW)

### 2.1. 🚚 Late Delivery Prediction

**Mục tiêu:** Dự đoán rủi ro giao hàng trễ dựa trên thông tin đơn hàng, shipping, và thời tiết.

**Dữ liệu:** 
- Input: `data/merged_supply_weather_clean.parquet`
- Features: Time, Shipping (lead_time, duration), Location, Product, Weather (risk_level, temperature, precipitation), Sales

**Output:** 
- Binary classification: `Late_delivery_risk` (0 = on-time, 1 = late)
- Probability: Xác suất trễ (0-1)
- Top features: Các yếu tố ảnh hưởng nhất

**Ứng dụng:**
- Cảnh báo sớm các đơn hàng có nguy cơ trễ → Logistics team có thể điều chỉnh routing
- Tối ưu hóa logistics: Ưu tiên xử lý các đơn hàng có risk cao
- Cải thiện customer satisfaction: Thông báo sớm cho khách hàng về khả năng trễ

**Model Performance:** XGBoost thường cho kết quả tốt nhất (AUC-ROC ~0.85, F1 ~0.75)

---

### 2.2. 📈 Revenue/Demand Forecast

**Mục tiêu:** Dự báo doanh thu hoặc nhu cầu theo thời gian, có thể theo tổng hệ thống hoặc theo từng quốc gia (Country).

**Dữ liệu:**
- Input: `data/merged_supply_weather_clean.parquet` (aggregated by month + country)
- Features: Lag features (revenue_lag1, lag2, lag3), Rolling stats (MA7, MA30), Time (month, quarter, seasonality), Weather aggregates, Country

**Output:**
- Regression: Doanh thu dự báo (continuous value)
- Confidence interval: Khoảng tin cậy (lower, upper bound)

**Ứng dụng:**
- **Inventory planning:** Dự báo nhu cầu để đặt hàng, tránh stockout hoặc overstock
- **Financial planning:** Lập ngân sách và kế hoạch doanh số cho quý/năm tiếp theo
- **Resource allocation:** Phân bổ nhân lực và tài nguyên dựa trên dự báo
- **Pricing strategy:** Điều chỉnh giá dựa trên dự báo nhu cầu

**Model Performance:** XGBoost Regressor (R² ~0.85, MAPE ~15-20%)

---

### 2.3. 👥 Customer Churn Prediction

**Mục tiêu:** Xác định khách hàng có nguy cơ rời bỏ (churn) dựa trên RFM và hành vi mua hàng.

**Dữ liệu:**
- Input: `data/merged_supply_weather_clean.parquet` (aggregated by customer)
- Features: RFM (Recency, Frequency, Monetary), Customer history (total_orders, avg_order_value, category_diversity), Engagement (avg_discount), Location (preferred_country)

**Định nghĩa Churn:** Recency > 180 days (6 tháng) - Khách hàng không mua lại trong 6 tháng gần nhất

**Output:**
- Binary classification: `churn` (0 = active, 1 = churned)
- Probability: Xác suất churn (0-1)
- Recommendations: Khuyến nghị hành động dựa trên risk level

**Ứng dụng:**
- **Retention campaigns:** Xác định top K khách hàng có risk cao → Gửi offer đặc biệt (discount, free shipping)
- **Customer segmentation:** Phân loại khách hàng theo churn risk để tùy chỉnh strategy
- **Root cause analysis:** Phân tích feature importance để hiểu nguyên nhân churn
- **Marketing optimization:** Tối ưu hóa marketing spend bằng cách focus vào đúng đối tượng

**Model Performance:** XGBoost (AUC-ROC ~0.85, Precision@Top1000 ~0.70)

---

## 3. TỔNG QUAN FEATURE STORE

### 3.1. Dataset Merged

**File:** `data/merged_supply_weather_clean.parquet`

**Mô tả:**
- **Số lượng:** ~180,000 records (mỗi record = 1 order item)
- **Khoảng thời gian:** Từ min date đến max date trong dataset
- **Nguồn gốc:** Gộp từ `DataCoSupplyChainDataset.csv` + `geocoded_weather.csv`

**Quy trình tạo:**
1. Load 2 file CSV gốc
2. Chuẩn hóa dates, countries, locations
3. Join theo Customer ID + Date (hoặc Country + City + Date nếu không có Customer ID)
4. Xử lý missing values, outliers
5. Tính toán derived features (lead_time, weather_risk_level, time features)
6. Lưu thành Parquet format (hiệu quả hơn CSV)

### 3.2. Các nhóm Feature chính

#### A. Time Features
- `year`, `month`, `day`, `day_of_week`, `quarter`, `week_of_year`
- `is_weekend`, `is_holiday_season`
- `month_sin`, `month_cos` (cyclical encoding)
- `day_of_week_sin`, `day_of_week_cos` (cyclical encoding)

**Dùng cho:** Tất cả 3 models (seasonality, weekday effects)

#### B. Shipping Features
- `Days for shipping (real)`, `Days for shipment (scheduled)`
- `lead_time` (scheduled - real)
- `Shipping Mode`

**Dùng cho:** Late Delivery Prediction

#### C. Customer/RFM Features
- `rfm_recency`: Số ngày từ lần mua cuối
- `rfm_frequency`: Số đơn hàng
- `rfm_monetary`: Tổng giá trị mua hàng
- `total_orders`, `avg_order_value`, `category_diversity`
- `days_since_first_order`, `avg_discount`

**Dùng cho:** Customer Churn Prediction, Customer Segmentation (tương lai)

#### D. Product Features
- `Category Name`, `Product Name`
- `Order Item Quantity`, `Order Item Discount`
- `Product Price`

**Dùng cho:** Late Delivery Prediction, Demand Forecast

#### E. Weather Features ⭐
- `temperature_2m_mean`, `temperature_2m_max`, `temperature_2m_min`
- `precipitation_sum`: Lượng mưa
- `wind_speed_10m_mean`: Tốc độ gió
- `relative_humidity_2m_mean`: Độ ẩm
- `weather_risk_level`: Mức độ rủi ro thời tiết (1-5)

**Dùng cho:** Late Delivery Prediction, Revenue Forecast, Risk Planning (tương lai)

#### F. Lag/Rolling Features (cho Forecast)
- `revenue_lag1`, `revenue_lag2`, `revenue_lag3`: Doanh thu các tháng trước
- `revenue_ma7`, `revenue_ma30`: Moving averages
- `revenue_std7`: Standard deviation

**Dùng cho:** Revenue Forecast

#### G. Location Features
- `Order Country`, `Order City`, `Order Region`
- `Customer Country`, `Customer City`
- One-hot encoding cho top countries

**Dùng cho:** Tất cả 3 models

#### H. Sales Features
- `Sales`: Doanh thu đơn hàng
- `Benefit per order`: Lợi nhuận

**Dùng cho:** Revenue Forecast, Customer Segmentation

### 3.3. Tại sao Feature Store giúp chia sẻ data giữa các model?

1. **Single Source of Truth:**
   - Một file duy nhất (`merged_supply_weather_clean.parquet`) chứa tất cả features đã được chuẩn hóa
   - Tránh inconsistency: Mỗi model không cần tự merge và chuẩn hóa lại

2. **Feature Re-use:**
   - Time features: Dùng chung cho cả 3 models
   - Weather features: Dùng cho Late Delivery + Revenue Forecast
   - Customer features: Dùng cho Churn + Segmentation (tương lai)

3. **Dễ mở rộng:**
   - Thêm model mới chỉ cần đọc từ Feature Store
   - Không cần thay đổi pipeline merge/preprocessing

4. **Performance:**
   - Parquet format: Đọc nhanh hơn CSV, compress tốt hơn
   - Có thể index theo columns thường dùng

5. **Maintainability:**
   - Một nơi để update features → Tất cả models tự động có features mới
   - Dễ debug: Kiểm tra features ở một nơi thay vì nhiều nơi

---

## 4. KỸ THUẬT CHÍNH ĐƯỢC SỬ DỤNG

### 4.1. Data Preprocessing

**Time-based Split:**
- **Quan trọng:** Dùng time-based split (80% train, 20% test) thay vì random split
- **Lý do:** Tránh data leakage - mô hình phải dự đoán tương lai dựa trên quá khứ
- **Áp dụng:** Tất cả 3 models

**Avoid Leakage:**
- Không dùng thông tin từ tương lai để dự đoán quá khứ
- RFM tính tại snapshot_date (chỉ dùng dữ liệu trước snapshot)
- Lag features: Chỉ dùng dữ liệu từ các period trước

### 4.2. Feature Engineering

**Encoding:**
- **OneHot Encoding:** Cho categorical (giới hạn top 10 categories để tránh quá nhiều cột)
- **Ordinal Encoding:** Không dùng (vì không có thứ tự rõ ràng)
- **Label Encoding:** Không dùng (tránh tạo thứ tự giả)

**Scaling:**
- **StandardScaler:** Cho Logistic Regression (cần scale)
- **Không scale:** Cho tree-based models (RandomForest, XGBoost không cần)

**Cyclical Encoding:**
- `month_sin`, `month_cos`: Encode tháng theo vòng tròn (tháng 12 gần tháng 1)
- `day_of_week_sin`, `day_of_week_cos`: Encode ngày trong tuần

### 4.3. Model Selection

**Baseline Models:**
- **Logistic Regression:** Cho classification (Late Delivery, Churn)
- **Linear Regression:** Cho regression (Revenue Forecast)

**Advanced Models:**
- **Random Forest:** Xử lý non-linear, feature importance tự động
- **XGBoost:** Performance tốt nhất, xử lý imbalance tốt, feature importance

**Lý do chọn:**
- Tree-based models phù hợp với tabular data
- XGBoost thường cho kết quả tốt nhất trong các benchmark
- Feature importance giúp interpretability

### 4.4. Time Series Techniques

**Lag Features:**
- `revenue_lag1`, `lag2`, `lag3`: Doanh thu các tháng trước
- Capture autocorrelation trong time series

**Rolling Windows:**
- `revenue_ma7`, `revenue_ma30`: Moving averages
- `revenue_std7`: Standard deviation
- Nắm bắt xu hướng dài hạn và biến động

### 4.5. RFM Modeling

**RFM Framework:**
- **Recency (R):** Số ngày từ lần mua cuối
- **Frequency (F):** Số đơn hàng
- **Monetary (M):** Tổng giá trị mua hàng

**Ứng dụng:** Customer Churn Prediction, Customer Segmentation

### 4.6. Weather Integration

**Weather Risk Level:**
- Tính toán dựa trên: precipitation, wind_speed, temperature extremes
- Scale 1-5: 1 = low risk, 5 = high risk
- Công thức: Risk = base + precipitation_risk + wind_risk + temperature_risk

**Weather Aggregates:**
- Mean temperature, precipitation, wind speed theo tháng/quốc gia
- Dùng cho Revenue Forecast (weather ảnh hưởng đến nhu cầu)

### 4.7. Class Imbalance Handling

**SMOTE (Synthetic Minority Oversampling Technique):**
- Tạo synthetic samples cho class thiểu số
- Áp dụng cho: Customer Churn (churn thường ít hơn active)

**Class Weights:**
- `class_weight='balanced'`: Cho Logistic Regression, Random Forest
- `scale_pos_weight`: Cho XGBoost (tính từ ratio negative/positive)

---

## 5. MỐI QUAN HỆ GIỮA 3 MÔ HÌNH AI

### 5.1. Flow dùng chung data

```
                    merged_supply_weather_clean.parquet
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Model 1:     │    │  Model 2:      │    │  Model 3:      │
│ Late Delivery │    │Revenue Forecast│    │Customer Churn  │
│               │    │                │    │                │
│ Input:        │    │ Input:         │    │ Input:         │
│ • Order-level │    │ • Aggregated   │    │ • Customer-    │
│ • Weather     │    │   time series  │    │   level        │
│ • Shipping    │    │ • Lag features │    │ • RFM          │
│               │    │ • Weather agg  │    │ • History      │
│               │    │                │    │                │
│ Output:       │    │ Output:        │    │ Output:        │
│ • Risk 0/1    │    │ • Revenue $    │    │ • Churn 0/1    │
│ • Probability │    │ • Confidence   │    │ • Probability  │
└───────┬───────┘    └───────┬────────┘    └───────┬────────┘
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  API & Dashboard│
                    │  • Predictions  │
                    │  • Insights     │
                    │  • Actions      │
                    └─────────────────┘
```

### 5.2. Mỗi model trả về insight khác nhau

**Model 1 - Late Delivery:**
- **Câu hỏi:** Đơn hàng này có nguy cơ giao trễ không?
- **Insight:** Weather risk, lead_time, shipping mode ảnh hưởng đến trễ
- **Action:** Điều chỉnh routing, ưu tiên xử lý, thông báo khách hàng

**Model 2 - Revenue Forecast:**
- **Câu hỏi:** Doanh thu tháng tới sẽ là bao nhiêu?
- **Insight:** Seasonality, lag effects, weather impact
- **Action:** Lập kế hoạch inventory, budget, resource allocation

**Model 3 - Customer Churn:**
- **Câu hỏi:** Khách hàng này có nguy cơ churn không?
- **Insight:** Recency là yếu tố quan trọng nhất, frequency/monetary cũng quan trọng
- **Action:** Gửi offer đặc biệt, personal outreach, segmentation

### 5.3. "Hệ sinh thái AI" hỗ trợ trực quan

**Logistics Optimization:**
- **Input:** Late Delivery predictions + Revenue Forecast
- **Output:** 
  - Ưu tiên xử lý các đơn hàng có risk cao
  - Điều chỉnh inventory dựa trên forecast
  - Tối ưu routing dựa trên weather forecast

**Revenue Planning:**
- **Input:** Revenue Forecast + Customer Churn predictions
- **Output:**
  - Lập kế hoạch doanh số cho quý/năm
  - Budget allocation
  - Target setting cho sales team

**Customer Retention:**
- **Input:** Customer Churn predictions + Revenue Forecast
- **Output:**
  - Chiến dịch giữ chân khách hàng có giá trị cao
  - Tối ưu hóa marketing spend
  - Personalization dựa trên churn risk

### 5.4. Sơ đồ tương tác

```
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS DECISIONS                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Logistics   │    │   Revenue    │    │  Customer    │  │
│  │ Optimization │    │   Planning   │    │  Retention   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         └────────────────────┼────────────────────┘          │
│                              │                                │
│                              ▼                                │
│                    ┌─────────────────┐                       │
│                    │  AI PREDICTIONS │                       │
│                    │  • Late Risk    │                       │
│                    │  • Revenue      │                       │
│                    │  • Churn Risk   │                       │
│                    └─────────────────┘                       │
│                              │                                │
│                              ▼                                │
│                    ┌─────────────────┐                       │
│                    │  FEATURE STORE  │                       │
│                    │  (Shared Data)  │                       │
│                    └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. ĐỊNH HƯỚNG PHÁT TRIỂN

### 6.1. Model nâng cao

**Time Series Models:**
- **ARIMA/SARIMA:** Cho Revenue Forecast (xử lý seasonality tốt hơn)
- **Prophet (Facebook):** Tự động detect trend, seasonality, holidays
- **LSTM/GRU:** Deep Learning cho time series (nếu có đủ dữ liệu)

**Tree-based nâng cao:**
- **CatBoost:** Xử lý categorical tốt hơn XGBoost
- **LightGBM:** Training nhanh hơn, memory efficient
- **Ensemble:** Voting, Stacking để tăng accuracy

**Deep Learning:**
- **Neural Networks:** Cho tabular data (TabNet, FT-Transformer)
- **AutoML:** Tự động tìm best model và hyperparameters

### 6.2. Optimization & Reinforcement Learning

**Inventory Optimization:**
- **RL Agents:** Học policy tối ưu cho inventory management
- **Multi-objective:** Tối ưu cost + service level + waste

**Dynamic Pricing:**
- **Price Elasticity Models:** Dự đoán phản ứng của khách hàng với giá
- **RL Pricing:** Tự động điều chỉnh giá để maximize revenue

### 6.3. Monitoring & MLOps

**Model Monitoring:**
- **Drift Detection:** Phát hiện khi data distribution thay đổi
- **Performance Tracking:** Monitor accuracy, F1, AUC theo thời gian
- **Alerting:** Cảnh báo khi model performance giảm

**Retrain Pipeline:**
- **Automated Retraining:** Retrain định kỳ (hàng tuần/tháng)
- **A/B Testing:** So sánh model mới vs model cũ
- **Model Versioning:** Quản lý versions của models

**Feature Store Auto-refresh:**
- **Scheduled Jobs:** Tự động merge và update Feature Store theo ngày/tuần
- **Incremental Updates:** Chỉ update data mới thay vì rebuild toàn bộ
- **Data Quality Checks:** Validate data trước khi update

### 6.4. Tích hợp vào FastAPI / Dashboard

**API Endpoints (Đã có):**
- `POST /ml/logistics/delay`: Dự đoán late delivery
- `POST /ml/revenue/forecast`: Dự báo doanh thu
- `POST /ml/customer/churn`: Dự đoán churn

**Web Pages (Đã có):**
- `/ml/late-delivery`: Trang nhập form và xem kết quả
- `/ml/revenue-forecast`: Trang nhập form và xem kết quả
- `/ml/customer-churn`: Trang nhập form và xem kết quả

**Dashboard Integration (Tương lai):**
- Embed predictions vào dashboard chính
- Real-time updates khi có dữ liệu mới
- Interactive visualizations với predictions

### 6.5. Mở rộng Use Cases

**Generative Supply Chain Planning:**
- Sử dụng LLM để generate scenarios và recommendations
- "What-if" analysis: Nếu tăng inventory 20%, impact là gì?

**Anomaly Detection:**
- Phát hiện đơn hàng bất thường (fraud, errors)
- Phát hiện outliers trong revenue, churn rate

**Recommendation System:**
- Product recommendations dựa trên purchase history
- Cross-sell, up-sell opportunities

**Digital Twin:**
- Mô phỏng toàn bộ supply chain
- Test scenarios trước khi triển khai thực tế

---

## 7. KẾT LUẬN

Hệ thống AI DataCo Supply Chain cung cấp một nền tảng tích hợp để:

✅ **Tối ưu hóa logistics** thông qua dự đoán late delivery  
✅ **Lập kế hoạch tài chính** thông qua revenue forecast  
✅ **Tăng cường retention** thông qua churn prediction  

**Điểm mạnh:**
- Feature Store dùng chung → Consistency, re-usability
- Weather integration → Tăng accuracy
- Time-based split → Tránh leakage
- Tree-based models → Performance tốt, interpretable

**Hướng phát triển:**
- Mở rộng sang các use cases mới (Inventory, Pricing, Recommendations)
- Nâng cấp models (Deep Learning, Time Series chuyên sâu)
- MLOps pipeline (Monitoring, Auto-retrain, A/B testing)

---

**Tài liệu liên quan:**
- [INDEX.md](INDEX.md) - Danh mục tài liệu và notebooks
- [model_late_delivery.md](model_late_delivery.md) - Chi tiết Late Delivery model
- [model_revenue_forecast.md](model_revenue_forecast.md) - Chi tiết Revenue Forecast model
- [model_customer_churn.md](model_customer_churn.md) - Chi tiết Customer Churn model

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

