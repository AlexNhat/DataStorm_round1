# TỔNG HỢP DỰ ÁN: SUPPLY CHAIN ANALYTICS DASHBOARD

**Ngày tạo:** 2024  
**Mục tiêu:** Xây dựng hệ thống dashboard phân tích chuỗi cung ứng và thời tiết

---

## 📋 TỔNG QUAN DỰ ÁN

Dự án này xây dựng một hệ thống dashboard web tương tác để phân tích dữ liệu chuỗi cung ứng kết hợp với dữ liệu thời tiết, giúp:
- Theo dõi KPI kinh doanh (doanh thu, lợi nhuận, số đơn hàng)
- Phân tích tình trạng giao hàng (on-time, late, advance)
- Khám phá tương quan giữa thời tiết và hiệu suất giao hàng
- Đánh giá chất lượng dữ liệu và đề xuất cải tiến

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

### Công nghệ sử dụng

- **Backend:** FastAPI (Python 3.8+)
- **Frontend:** HTML + TailwindCSS + Chart.js
- **Data Processing:** Pandas, NumPy
- **Templates:** Jinja2
- **Server:** Uvicorn

### Cấu trúc dự án

```
D:\Data_F\
├── app/                          # Ứng dụng chính
│   ├── main.py                  # FastAPI entry point
│   ├── routers/
│   │   └── dashboard.py        # API routes cho dashboard
│   ├── services/
│   │   ├── data_loader.py      # Đọc và xử lý CSV
│   │   ├── analytics.py        # Tính toán KPI và thống kê
│   │   └── data_profiler.py   # Phân tích chất lượng dữ liệu
│   ├── templates/
│   │   ├── base.html           # Template base
│   │   └── dashboard.html      # Dashboard chính
│   └── static/
│       └── js/
│           └── dashboard_charts.js  # JavaScript cho charts
├── data/                        # Dữ liệu CSV
│   ├── DataCoSupplyChainDataset.csv
│   └── geocoded_weather.csv
├── docs/                        # Tài liệu
│   ├── data_quality_report.md
│   ├── data_improvement_plan.md
│   ├── README_dashboard.md
│   └── PROJECT_SUMMARY.md      # File này
├── scripts/
│   └── generate_data_quality_report.py
├── venv/                        # Virtual environment
├── requirements.txt
└── README.md
```

---

## 📊 DỮ LIỆU ĐẦU VÀO

### 1. Supply Chain Dataset (`DataCoSupplyChainDataset.csv`)

**Các cột quan trọng:**
- `Order Id`, `Order Customer Id`: Định danh đơn hàng và khách hàng
- `order date (DateOrders)`: Ngày đặt hàng
- `Sales`, `Benefit per order`: Doanh thu và lợi nhuận
- `Delivery Status`, `Late_delivery_risk`: Trạng thái giao hàng
- `Order Country`, `Order City`: Vị trí đơn hàng
- `Category Name`, `Product Name`: Thông tin sản phẩm
- `Days for shipping (real)`, `Days for shipment (scheduled)`: Thời gian giao hàng

**Số lượng:** ~180,000+ bản ghi

### 2. Weather Dataset (`geocoded_weather.csv`)

**Các cột quan trọng:**
- `customer_id`, `city`, `country`, `order_date`: Thông tin liên kết
- `lat`, `lon`: Tọa độ địa lý
- `temperature_2m_mean`, `temperature_2m_max`, `temperature_2m_min`: Nhiệt độ
- `precipitation_sum`: Lượng mưa
- `wind_speed_10m_mean`: Tốc độ gió
- `relative_humidity_2m_mean`: Độ ẩm

**Số lượng:** ~180,000+ bản ghi (tương ứng với supply chain data)

---

## 🔧 CÁC MODULE ĐÃ XÂY DỰNG

### 1. Data Loader (`app/services/data_loader.py`)

**Chức năng:**
- Đọc file CSV với encoding tự động (latin-1, utf-8, iso-8859-1, cp1252)
- Chuyển đổi kiểu dữ liệu:
  - Ngày tháng → datetime
  - Số → float/int
- Xử lý lỗi encoding và missing values
- Đề xuất cách join 2 dataset

**Các hàm chính:**
- `load_supply_chain_data()`: Đọc dữ liệu chuỗi cung ứng
- `load_weather_data()`: Đọc dữ liệu thời tiết
- `get_data_summary()`: Lấy thông tin tổng quan dataset
- `suggest_join_keys()`: Phân tích và đề xuất cách join

### 2. Analytics (`app/services/analytics.py`)

**Chức năng:**
- Tính toán KPI kinh doanh
- Thống kê mô tả
- Phân tích time series
- Phân tích tương quan thời tiết

**Các hàm chính:**
- `calculate_supply_chain_kpis()`: Tính KPI (doanh thu, lợi nhuận, tỉ lệ giao trễ)
- `get_top_products()`: Top sản phẩm theo doanh thu/lợi nhuận
- `get_top_countries()`: Top quốc gia theo doanh thu/số đơn
- `get_time_series_data()`: Dữ liệu theo thời gian (tháng/quý)
- `analyze_weather_delivery_correlation()`: Tương quan thời tiết và giao hàng
- `get_sample_orders()`: Lấy mẫu đơn hàng gần nhất

**KPI được tính:**
- Tổng doanh thu (Sales)
- Tổng lợi nhuận (Benefit per order)
- Tổng số đơn hàng
- Tỉ lệ giao hàng trễ (%)
- Phân bố trạng thái giao hàng
- Số ngày giao hàng trung bình

### 3. Data Profiler (`app/services/data_profiler.py`)

**Chức năng:**
- Phân tích chất lượng dữ liệu
- Phát hiện outliers
- Kiểm tra missing values
- Phát hiện dữ liệu nhạy cảm

**Các hàm chính:**
- `check_data_quality()`: Kiểm tra chất lượng tổng thể
- `detect_outliers()`: Phát hiện giá trị ngoại lai (IQR, Z-score)

### 4. Dashboard Router (`app/routers/dashboard.py`)

**Endpoints:**
- `GET /dashboard`: Trang dashboard HTML
- `GET /dashboard/api/data`: API trả về dữ liệu JSON
- `GET /dashboard/api/filter`: API lọc dữ liệu theo điều kiện

**Tính năng:**
- Cache dữ liệu trong memory
- Hỗ trợ filter: country, category, delivery status, date range
- Tự động tính toán lại KPI khi filter

---

## 🎨 GIAO DIỆN DASHBOARD

### 1. KPI Cards (4 thẻ)

- 💰 **Tổng doanh thu**: Hiển thị tổng Sales
- 📈 **Tổng lợi nhuận**: Hiển thị tổng Benefit per order
- 📦 **Tổng số đơn**: Số lượng đơn hàng duy nhất
- ⚠️ **Tỉ lệ giao trễ**: Phần trăm đơn hàng giao trễ

### 2. Biểu đồ tương tác

#### 📅 Xu hướng theo thời gian (Line Chart)
- Doanh thu theo tháng
- Số đơn hàng theo tháng
- Tỉ lệ giao trễ theo tháng

#### 📊 Phân bố trạng thái giao hàng (Doughnut Chart)
- Late delivery
- Advance shipping
- Shipping on time

#### 🌍 Top 10 quốc gia theo doanh thu (Horizontal Bar Chart)
- Sắp xếp theo doanh thu giảm dần

#### 📦 Top 10 danh mục theo doanh thu (Horizontal Bar Chart)
- Sắp xếp theo doanh thu giảm dần

### 3. Bộ lọc (Filters)

- **Quốc gia**: Dropdown chọn quốc gia
- **Danh mục**: Dropdown chọn category
- **Trạng thái giao hàng**: Dropdown chọn delivery status
- **Khoảng thời gian**: Date picker (từ ngày - đến ngày)

### 4. Phân tích tương quan thời tiết

Hiển thị hệ số tương quan giữa:
- Nhiệt độ và tỉ lệ giao trễ
- Lượng mưa và tỉ lệ giao trễ
- Tốc độ gió và tỉ lệ giao trễ

### 5. Bảng mẫu đơn hàng

Hiển thị 50 đơn hàng gần nhất với:
- Order ID
- Quốc gia
- Danh mục
- Ngày đơn hàng
- Trạng thái giao hàng
- Có giao trễ hay không
- Doanh thu

---

## 📈 PHÂN TÍCH DỮ LIỆU ĐÃ THỰC HIỆN

### 1. Data Profiling

- **Missing Values Analysis**: Phát hiện các cột có nhiều missing values
- **Outliers Detection**: Phát hiện giá trị ngoại lai trong Sales, Benefit, Days for shipping
- **Data Type Validation**: Kiểm tra và chuyển đổi kiểu dữ liệu
- **Format Issues**: Phát hiện vấn đề về format ngày tháng, tên quốc gia

### 2. Join Analysis

**Phương pháp join được đề xuất:**
- Join theo `Customer ID` + `Date`: Chính xác nhất
- Join theo `Country` + `City` + `Date`: Dự phòng nếu không có Customer ID

**Vấn đề phát hiện:**
- Tên quốc gia không nhất quán (ví dụ: "EE. UU." vs "United States")
- Cần chuẩn hóa format ngày tháng

### 3. KPI Calculation

**Các metric đã tính:**
- Tổng doanh thu: Sum của cột Sales
- Tổng lợi nhuận: Sum của Benefit per order
- Tỉ lệ giao trễ: (Số đơn có Late_delivery_risk = 1) / Tổng đơn * 100
- Top products/countries: Group by và sort theo Sales

### 4. Time Series Analysis

- Resample dữ liệu theo tháng (freq='M')
- Tính tổng doanh thu, số đơn hàng, tỉ lệ giao trễ theo từng tháng
- Chuẩn bị dữ liệu cho biểu đồ xu hướng

### 5. Weather Correlation

- Join supply chain data với weather data
- Tính correlation coefficient giữa:
  - Temperature và Late_delivery_risk
  - Precipitation và Late_delivery_risk
  - Wind speed và Late_delivery_risk

---

## 🐛 CÁC VẤN ĐỀ ĐÃ GẶP VÀ GIẢI QUYẾT

### 1. Lỗi Encoding

**Vấn đề:** File CSV có encoding không chuẩn (latin-1)  
**Giải pháp:** Tự động thử nhiều encoding (latin-1, utf-8, iso-8859-1, cp1252)

### 2. Lỗi Template: 'float' is undefined

**Vấn đề:** Jinja2 không có hàm `float()` built-in  
**Giải pháp:** 
- Convert giá trị sang float trong Python code trước khi truyền vào template
- Sửa template để format trực tiếp giá trị đã là số

### 3. Missing Values

**Vấn đề:** Một số cột có missing values  
**Giải pháp:** 
- Xử lý trong data_loader: fill hoặc drop tùy trường hợp
- Đảm bảo tính toán KPI không bị lỗi khi có NaN

### 4. Date Format

**Vấn đề:** Format ngày không nhất quán  
**Giải pháp:** Dùng `pd.to_datetime()` với `errors='coerce'` và `infer_datetime_format=True`

---

## 📝 TÀI LIỆU ĐÃ TẠO

### 1. `docs/data_quality_report.md`

Báo cáo chi tiết về:
- Tổng quan dataset
- Phân tích missing values
- Phát hiện outliers
- Vấn đề về định dạng
- Cột nhạy cảm
- Đề xuất join 2 dataset
- Kết luận và khuyến nghị

### 2. `docs/data_improvement_plan.md`

Kế hoạch cải tiến bao gồm:
- Chuẩn hóa & tái cấu trúc dữ liệu (Star Schema)
- Cải thiện chất lượng dữ liệu
- Cải thiện khả năng phục vụ AI/ML (Feature Store)
- Roadmap triển khai (5 bước)

### 3. `docs/README_dashboard.md`

Hướng dẫn sử dụng:
- Cài đặt và chạy dự án
- Các tính năng của dashboard
- API endpoints
- Xử lý lỗi thường gặp

---

## 🚀 CÁCH CHẠY DỰ ÁN

### 1. Tạo virtual environment

```bash
python -m venv venv
```

### 2. Kích hoạt virtual environment

**Windows:**
```bash
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Chạy server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Hoặc dùng script:
```bash
run_server_venv.bat  # Windows
```

### 5. Truy cập dashboard

Mở trình duyệt: http://127.0.0.1:8000/dashboard

---

## 📊 KẾT QUẢ ĐẠT ĐƯỢC

### ✅ Đã hoàn thành

1. ✅ Xây dựng hệ thống đọc và xử lý dữ liệu CSV
2. ✅ Tính toán các KPI quan trọng
3. ✅ Xây dựng dashboard web tương tác
4. ✅ Tích hợp biểu đồ Chart.js
5. ✅ Hỗ trợ filter dữ liệu
6. ✅ Phân tích tương quan thời tiết
7. ✅ Tạo báo cáo chất lượng dữ liệu
8. ✅ Đề xuất kế hoạch cải tiến

### 📈 Metrics Dashboard

- **4 KPI cards** hiển thị metrics chính
- **4 biểu đồ** tương tác (line, bar, doughnut)
- **Bộ lọc** 4 tiêu chí (country, category, status, date)
- **Bảng dữ liệu** 50 đơn hàng mẫu
- **Phân tích tương quan** thời tiết

---

## 🔮 HƯỚNG PHÁT TRIỂN

### Ngắn hạn

1. **Cải thiện join dữ liệu thời tiết:**
   - Chuẩn hóa tên quốc gia
   - Tạo bảng mapping city/country → lat/lon
   - Tăng tỉ lệ merge thành công

2. **Thêm biểu đồ:**
   - Heatmap tương quan thời tiết
   - Geographic map với markers
   - Forecast/prediction charts

3. **Tối ưu performance:**
   - Database thay vì CSV
   - Caching với Redis
   - Pagination cho bảng dữ liệu

### Dài hạn

1. **Star Schema Migration:**
   - Tách fact và dimension tables
   - Tối ưu truy vấn
   - Dễ dàng mở rộng

2. **Feature Store:**
   - Tạo bảng feature engineering
   - Chuẩn bị cho ML models

3. **ML Models:**
   - Dự đoán giao hàng trễ
   - Dự báo nhu cầu sản phẩm
   - Phân khúc khách hàng

4. **Real-time Dashboard:**
   - WebSocket cho real-time updates
   - Streaming data processing

---

## 📚 KIẾN THỨC ÁP DỤNG

- **Data Engineering:** ETL, data profiling, data quality
- **Web Development:** FastAPI, Jinja2, JavaScript
- **Data Visualization:** Chart.js, responsive design
- **Data Analysis:** Pandas, NumPy, statistical analysis
- **Software Engineering:** Clean code, modular design, documentation

---

## 👥 ĐÓNG GÓP

Dự án này được xây dựng với mục tiêu:
- Phân tích hiệu quả chuỗi cung ứng
- Khám phá tác động của thời tiết
- Cung cấp insights cho quyết định kinh doanh
- Chuẩn bị nền tảng cho AI/ML

---

**Tài liệu này được tạo tự động và cập nhật theo tiến độ dự án.**

