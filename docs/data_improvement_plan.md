# KẾ HOẠCH CẢI TIẾN DỮ LIỆU VÀ MÔ HÌNH LƯU TRỮ

**Ngày tạo:** 2024

---

## 1. TỔNG QUAN

Tài liệu này đề xuất các phương án cải tiến dữ liệu và mô hình lưu trữ cho hệ thống phân tích chuỗi cung ứng và thời tiết. Mục tiêu là tối ưu hóa hiệu suất truy vấn, cải thiện chất lượng dữ liệu, và chuẩn bị cho các ứng dụng AI/ML trong tương lai.

---

## 2. CHUẨN HÓA & TÁI CẤU TRÚC DỮ LIỆU (DATA MODELING)

### 2.1. Mô hình Star Schema

Đề xuất chuyển đổi dữ liệu từ dạng flat table sang mô hình **Star Schema** với các bảng fact và dimension:

#### 2.1.1. Bảng Fact chính

**`fact_orders`** - Bảng fact giao dịch/đơn hàng

| Cột | Kiểu dữ liệu | Mô tả |
|-----|--------------|-------|
| `order_item_id` | BIGINT (PK) | ID duy nhất cho mỗi order item |
| `order_id` | VARCHAR | Order ID từ dữ liệu gốc |
| `date_key` | INT (FK) | Khóa ngoại đến dim_date |
| `customer_key` | INT (FK) | Khóa ngoại đến dim_customer |
| `product_key` | INT (FK) | Khóa ngoại đến dim_product |
| `location_key` | INT (FK) | Khóa ngoại đến dim_geolocation |
| `shipping_date_key` | INT (FK) | Khóa ngoại đến dim_date (ngày giao hàng) |
| `sales` | DECIMAL(18,2) | Doanh thu |
| `benefit_per_order` | DECIMAL(18,2) | Lợi nhuận |
| `order_item_quantity` | INT | Số lượng sản phẩm |
| `order_item_discount` | DECIMAL(10,2) | Giảm giá |
| `order_item_profit_ratio` | DECIMAL(5,4) | Tỉ lệ lợi nhuận |
| `days_for_shipping_real` | INT | Số ngày giao hàng thực tế |
| `days_for_shipment_scheduled` | INT | Số ngày giao hàng dự kiến |
| `late_delivery_risk` | TINYINT | 1 = trễ, 0 = không trễ |
| `delivery_status` | VARCHAR(50) | Trạng thái giao hàng |
| `order_status` | VARCHAR(50) | Trạng thái đơn hàng |
| `shipping_mode` | VARCHAR(50) | Phương thức vận chuyển |
| `type` | VARCHAR(50) | Loại giao dịch (DEBIT, CASH, etc.) |
| `lead_time` | INT | Derived: days_for_shipment_scheduled - days_for_shipping_real |

**Lợi ích:**
- Giảm redundancy: thông tin khách hàng, sản phẩm, địa điểm chỉ lưu 1 lần
- Tăng tốc truy vấn: fact table nhỏ gọn, dễ index
- Dễ dàng thêm dimension mới mà không ảnh hưởng fact table

#### 2.1.2. Các bảng Dimension

**`dim_date`** - Bảng dimension ngày tháng

| Cột | Kiểu dữ liệu | Mô tả |
|-----|--------------|-------|
| `date_key` | INT (PK) | Khóa chính (YYYYMMDD) |
| `date` | DATE | Ngày thực |
| `day` | TINYINT | Ngày trong tháng (1-31) |
| `month` | TINYINT | Tháng (1-12) |
| `quarter` | TINYINT | Quý (1-4) |
| `year` | SMALLINT | Năm |
| `day_of_week` | TINYINT | Thứ trong tuần (1=Monday) |
| `is_weekend` | BOOLEAN | Có phải cuối tuần không |
| `is_holiday` | BOOLEAN | Có phải ngày lễ không (cần bổ sung dữ liệu) |

**`dim_customer`** - Bảng dimension khách hàng

| Cột | Kiểu dữ liệu | Mô tả |
|-----|--------------|-------|
| `customer_key` | INT (PK) | Khóa chính |
| `customer_id` | VARCHAR | Customer ID từ dữ liệu gốc |
| `customer_segment` | VARCHAR(50) | Phân khúc khách hàng |
| `customer_city` | VARCHAR(100) | Thành phố |
| `customer_state` | VARCHAR(100) | Bang/Tỉnh |
| `customer_country` | VARCHAR(100) | Quốc gia (đã chuẩn hóa) |
| `customer_country_code` | VARCHAR(3) | Mã quốc gia ISO (cần bổ sung) |

**Lưu ý:** Không lưu thông tin nhạy cảm như email, password, địa chỉ chi tiết.

**`dim_product`** - Bảng dimension sản phẩm

| Cột | Kiểu dữ liệu | Mô tả |
|-----|--------------|-------|
| `product_key` | INT (PK) | Khóa chính |
| `product_card_id` | VARCHAR | Product Card ID |
| `category_id` | INT | Category ID |
| `category_name` | VARCHAR(100) | Tên danh mục |
| `department_id` | INT | Department ID |
| `department_name` | VARCHAR(100) | Tên phòng ban |
| `product_name` | VARCHAR(255) | Tên sản phẩm |
| `product_price` | DECIMAL(10,2) | Giá sản phẩm |
| `product_status` | VARCHAR(50) | Trạng thái sản phẩm |

**`dim_geolocation`** - Bảng dimension địa lý

| Cột | Kiểu dữ liệu | Mô tả |
|-----|--------------|-------|
| `location_key` | INT (PK) | Khóa chính |
| `city` | VARCHAR(100) | Thành phố |
| `state` | VARCHAR(100) | Bang/Tỉnh |
| `country` | VARCHAR(100) | Quốc gia (đã chuẩn hóa) |
| `country_code` | VARCHAR(3) | Mã quốc gia ISO |
| `latitude` | DECIMAL(10,7) | Vĩ độ |
| `longitude` | DECIMAL(10,7) | Kinh độ |
| `region` | VARCHAR(100) | Khu vực (ví dụ: Southeast Asia) |
| `market` | VARCHAR(100) | Thị trường |

**Lợi ích:** Cho phép join trực tiếp với dữ liệu thời tiết dựa trên lat/lon và date.

**`dim_weather`** - Bảng dimension/fact thời tiết

| Cột | Kiểu dữ liệu | Mô tả |
|-----|--------------|-------|
| `weather_key` | BIGINT (PK) | Khóa chính |
| `date_key` | INT (FK) | Khóa ngoại đến dim_date |
| `location_key` | INT (FK) | Khóa ngoại đến dim_geolocation |
| `temperature_2m_mean` | DECIMAL(5,2) | Nhiệt độ trung bình |
| `temperature_2m_max` | DECIMAL(5,2) | Nhiệt độ tối đa |
| `temperature_2m_min` | DECIMAL(5,2) | Nhiệt độ tối thiểu |
| `relative_humidity_2m_mean` | DECIMAL(5,2) | Độ ẩm trung bình (%) |
| `wind_speed_10m_mean` | DECIMAL(5,2) | Tốc độ gió trung bình |
| `precipitation_sum` | DECIMAL(10,2) | Tổng lượng mưa |
| `apparent_temperature_mean` | DECIMAL(5,2) | Nhiệt độ cảm nhận |
| `weather_code` | INT | Mã thời tiết |
| `weather_risk_level` | TINYINT | Derived: mức độ rủi ro (1-5) |

**Công thức tính `weather_risk_level`:**
- Dựa trên precipitation_sum, wind_speed, temperature extremes
- Ví dụ: precipitation > 50mm hoặc wind_speed > 20 m/s → risk_level = 5

### 2.2. Sơ đồ quan hệ

```
fact_orders
├── date_key → dim_date
├── customer_key → dim_customer
├── product_key → dim_product
├── location_key → dim_geolocation
└── shipping_date_key → dim_date

dim_geolocation ↔ dim_weather (qua location_key + date_key)
```

---

## 3. CẢI THIỆN CHẤT LƯỢNG DỮ LIỆU

### 3.1. Chuẩn hóa format ngày tháng

**Vấn đề hiện tại:**
- Format ngày không nhất quán: "1/31/2018 22:56", "2018-01-31", etc.
- Một số giá trị có thể không parse được

**Giải pháp:**
1. Chuẩn hóa tất cả ngày về format ISO 8601: `YYYY-MM-DD HH:MM:SS`
2. Tạo bảng `dim_date` với tất cả ngày từ min đến max date trong dataset
3. Validate và clean dữ liệu ngày trước khi import

**Code mẫu:**
```python
def normalize_date(date_str):
    """Chuẩn hóa ngày về ISO 8601."""
    try:
        dt = pd.to_datetime(date_str, errors='coerce', infer_datetime_format=True)
        return dt.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(dt) else None
    except:
        return None
```

### 3.2. Chuẩn hóa tên quốc gia

**Vấn đề hiện tại:**
- "EE. UU." vs "United States"
- "UK" vs "United Kingdom"
- Các biến thể khác

**Giải pháp:**
1. Tạo bảng mapping `country_mapping`:

| Tên gốc | Tên chuẩn | Mã ISO |
|---------|-----------|--------|
| EE. UU. | United States | USA |
| U.S.A | United States | USA |
| UK | United Kingdom | GBR |
| ... | ... | ... |

2. Áp dụng mapping khi load dữ liệu
3. Sử dụng mã ISO 3 ký tự làm chuẩn

**Code mẫu:**
```python
COUNTRY_MAPPING = {
    'EE. UU.': 'United States',
    'U.S.A': 'United States',
    'USA': 'United States',
    'UK': 'United Kingdom',
    # ... thêm các mapping khác
}

def normalize_country(country_name):
    """Chuẩn hóa tên quốc gia."""
    if not country_name:
        return None
    country_name = str(country_name).strip()
    return COUNTRY_MAPPING.get(country_name, country_name)
```

### 3.3. Xử lý Missing Values

**Chiến lược theo từng cột:**

| Cột | Chiến lược | Lý do |
|-----|------------|-------|
| `Sales`, `Benefit per order` | Fill = 0 hoặc drop | Dữ liệu số, không thể suy luận |
| `Customer Country`, `Order Country` | Fill = "Unknown" | Có thể phân tích riêng |
| `Category Name` | Fill = "Unknown" hoặc drop | Tùy vào mục đích phân tích |
| `Days for shipping (real)` | Fill = median hoặc drop | Có thể tính từ scheduled |
| `Latitude`, `Longitude` | Geocode lại hoặc drop | Cần để join với weather |

**Code mẫu:**
```python
def handle_missing_values(df):
    """Xử lý missing values theo chiến lược."""
    # Fill numeric với 0 nếu là doanh thu/lợi nhuận
    df['Sales'] = df['Sales'].fillna(0)
    df['Benefit per order'] = df['Benefit per order'].fillna(0)
    
    # Fill categorical với "Unknown"
    df['Customer Country'] = df['Customer Country'].fillna('Unknown')
    df['Order Country'] = df['Order Country'].fillna('Unknown')
    
    # Drop nếu missing quá nhiều (>50%)
    threshold = len(df) * 0.5
    for col in df.columns:
        if df[col].isnull().sum() > threshold:
            df = df.drop(columns=[col])
    
    return df
```

### 3.4. Xử lý Outliers

**Chiến lược:**
1. **Phát hiện:** Sử dụng IQR method hoặc Z-score
2. **Quyết định:**
   - Nếu outlier hợp lý (ví dụ: đơn hàng lớn thực sự) → giữ lại
   - Nếu outlier do lỗi (ví dụ: số âm cho Sales) → loại bỏ hoặc cap
   - Nếu outlier ảnh hưởng phân tích → tạo flag `is_outlier`

**Code mẫu:**
```python
def detect_and_handle_outliers(df, column, method='iqr'):
    """Phát hiện và xử lý outliers."""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Tạo flag
    df['is_outlier'] = (df[column] < lower_bound) | (df[column] > upper_bound)
    
    # Cap values (hoặc drop tùy yêu cầu)
    # df[column] = df[column].clip(lower=lower_bound, upper=upper_bound)
    
    return df
```

### 3.5. Bảo vệ dữ liệu nhạy cảm

**Các cột cần xử lý:**
- `Customer Email` → Hash hoặc loại bỏ
- `Customer Password` → Loại bỏ hoàn toàn
- `Customer Street`, `Customer Zipcode` → Có thể giữ nếu cần phân tích, nhưng nên hash nếu có yêu cầu bảo mật

**Giải pháp:**
```python
import hashlib

def hash_sensitive_data(df):
    """Hash dữ liệu nhạy cảm."""
    if 'Customer Email' in df.columns:
        df['Customer Email'] = df['Customer Email'].apply(
            lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:16] if pd.notna(x) else None
        )
    
    # Loại bỏ password
    if 'Customer Password' in df.columns:
        df = df.drop(columns=['Customer Password'])
    
    return df
```

---

## 4. CẢI THIỆN KHẢ NĂNG PHỤC VỤ AI/ML

### 4.1. Feature Store

Tạo bảng `feature_store` để lưu các features đã engineering sẵn cho ML:

**Bảng `feature_store`:**

| Cột | Kiểu dữ liệu | Mô tả |
|-----|--------------|-------|
| `feature_key` | BIGINT (PK) | Khóa chính |
| `date_key` | INT (FK) | Ngày |
| `location_key` | INT (FK) | Vị trí |
| `customer_key` | INT (FK) | Khách hàng |
| `product_key` | INT (FK) | Sản phẩm |
| `target_late_delivery` | TINYINT | Target: có giao trễ không (0/1) |
| `feature_sales_7d_avg` | DECIMAL(18,2) | Doanh thu trung bình 7 ngày |
| `feature_sales_30d_avg` | DECIMAL(18,2) | Doanh thu trung bình 30 ngày |
| `feature_order_count_7d` | INT | Số đơn 7 ngày gần nhất |
| `feature_weather_risk_level` | TINYINT | Mức độ rủi ro thời tiết |
| `feature_temperature` | DECIMAL(5,2) | Nhiệt độ |
| `feature_precipitation` | DECIMAL(10,2) | Lượng mưa |
| `feature_lead_time_avg` | INT | Lead time trung bình theo location |
| `feature_is_weekend` | BOOLEAN | Có phải cuối tuần |
| `feature_is_holiday` | BOOLEAN | Có phải ngày lễ |
| `feature_category_popularity` | DECIMAL(5,4) | Độ phổ biến của category |

### 4.2. Phân loại Features

**Features tĩnh (Dimension):**
- Customer segment
- Product category
- Location (country, region)
- Shipping mode

**Features động (Fact):**
- Weather metrics (temperature, precipitation, wind)
- Sales trends (7d, 30d averages)
- Order frequency
- Lead time patterns

### 4.3. Use Cases cho ML

**1. Dự đoán giao hàng trễ:**
- **Target:** `late_delivery_risk` (binary classification)
- **Features:** weather_risk_level, lead_time_avg, is_weekend, order_count_7d, etc.
- **Model:** Random Forest, XGBoost, hoặc Neural Network

**2. Dự báo nhu cầu sản phẩm:**
- **Target:** `order_item_quantity` (regression hoặc time series)
- **Features:** sales_7d_avg, sales_30d_avg, category_popularity, seasonality
- **Model:** ARIMA, Prophet, hoặc LSTM

**3. Phân khúc khách hàng:**
- **Target:** Customer segments (clustering)
- **Features:** purchase_frequency, avg_order_value, preferred_categories
- **Model:** K-Means, DBSCAN

---

## 5. ROADMAP TRIỂN KHAI

### Bước 1: Làm sạch & chuẩn hóa dữ liệu hiện tại (Tuần 1-2)

**Tasks:**
- [ ] Tạo script chuẩn hóa ngày tháng
- [ ] Tạo bảng mapping quốc gia
- [ ] Xử lý missing values
- [ ] Phát hiện và xử lý outliers
- [ ] Hash/loại bỏ dữ liệu nhạy cảm
- [ ] Validate dữ liệu sau khi clean

**Deliverables:**
- Script Python để clean data
- File CSV đã được clean
- Báo cáo validation

### Bước 2: Thiết kế & migrate sang Star Schema (Tuần 3-4)

**Tasks:**
- [ ] Thiết kế schema chi tiết (ERD)
- [ ] Tạo các bảng dimension (dim_date, dim_customer, dim_product, dim_geolocation)
- [ ] Tạo bảng fact_orders
- [ ] Tạo script ETL để migrate dữ liệu
- [ ] Tạo indexes cho các foreign keys
- [ ] Validate referential integrity

**Deliverables:**
- SQL scripts để tạo tables
- ETL script (Python hoặc SQL)
- Database schema documentation

### Bước 3: Tích hợp dữ liệu thời tiết vào pipeline ETL (Tuần 5-6)

**Tasks:**
- [ ] Tạo bảng dim_weather
- [ ] Tạo script join weather data với geolocation
- [ ] Tính toán weather_risk_level
- [ ] Tạo pipeline ETL tự động (có thể dùng Airflow)
- [ ] Validate join quality

**Deliverables:**
- ETL pipeline script
- Documentation về cách join
- Validation report

### Bước 4: Xây dựng Feature Store & Dashboard BI nâng cao (Tuần 7-8)

**Tasks:**
- [ ] Tạo bảng feature_store
- [ ] Tính toán các features đã engineering
- [ ] Tạo dashboard BI với các metrics nâng cao
- [ ] Tích hợp ML model predictions vào dashboard
- [ ] Tối ưu performance (materialized views, caching)

**Deliverables:**
- Feature store với các features đã tính
- Dashboard BI nâng cao
- Documentation về features

### Bước 5: Xây dựng mô hình AI/ML (Tuần 9-12)

**Tasks:**
- [ ] Chọn use case đầu tiên (ví dụ: dự đoán giao trễ)
- [ ] Feature engineering và selection
- [ ] Train và evaluate models
- [ ] Deploy model (có thể dùng FastAPI endpoint riêng)
- [ ] Tích hợp predictions vào dashboard
- [ ] Monitor model performance

**Deliverables:**
- Trained ML models
- Model evaluation report
- API endpoint để serve predictions
- Documentation về model

---

## 6. KẾT LUẬN

Việc cải tiến dữ liệu và mô hình lưu trữ sẽ mang lại các lợi ích:

1. **Hiệu suất:** Truy vấn nhanh hơn nhờ star schema và indexes
2. **Chất lượng:** Dữ liệu sạch, chuẩn hóa, dễ bảo trì
3. **Mở rộng:** Dễ dàng thêm dimension và fact mới
4. **AI/ML Ready:** Feature store sẵn sàng cho các mô hình ML
5. **Bảo mật:** Dữ liệu nhạy cảm được bảo vệ

**Ưu tiên:** Bắt đầu với Bước 1 và 2, sau đó từng bước triển khai các bước tiếp theo tùy vào nguồn lực và yêu cầu kinh doanh.

