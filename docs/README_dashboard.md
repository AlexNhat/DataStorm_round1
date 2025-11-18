# HƯỚNG DẪN CHẠY DỰ ÁN SUPPLY CHAIN ANALYTICS DASHBOARD

## 📋 Tổng quan

Dự án này là một hệ thống dashboard phân tích chuỗi cung ứng và thời tiết, được xây dựng bằng:
- **Backend:** FastAPI (Python)
- **Frontend:** HTML + TailwindCSS + Chart.js
- **Data:** CSV files (Supply Chain và Weather data)

---

## 🚀 Cài đặt và chạy dự án

### Yêu cầu hệ thống

- Python 3.8 trở lên
- pip (Python package manager)

### Bước 1: Cài đặt dependencies

```bash
# Di chuyển vào thư mục dự án
cd D:\Data_F

# Cài đặt các package cần thiết
pip install -r requirements.txt
```

### Bước 2: Kiểm tra dữ liệu

Đảm bảo các file CSV đã có trong thư mục `data/`:
- `data/DataCoSupplyChainDataset.csv`
- `data/geocoded_weather.csv`

### Bước 3: Chạy server

```bash
# Chạy FastAPI server với uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Hoặc:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Bước 4: Truy cập dashboard

Mở trình duyệt và truy cập:
- **Dashboard:** http://127.0.0.1:8000/dashboard
- **API Health Check:** http://127.0.0.1:8000/health
- **API Data:** http://127.0.0.1:8000/dashboard/api/data

---

## 📊 Các tính năng của Dashboard

### 1. KPI Cards (Thẻ chỉ số chính)

Dashboard hiển thị 4 KPI quan trọng:
- **Tổng doanh thu:** Tổng số tiền bán hàng
- **Tổng lợi nhuận:** Tổng lợi nhuận từ các đơn hàng
- **Tổng số đơn:** Số lượng đơn hàng duy nhất
- **Tỉ lệ giao trễ:** Phần trăm đơn hàng giao trễ

### 2. Biểu đồ tương tác

#### 📅 Xu hướng theo thời gian (Time Series)
- Line chart hiển thị:
  - Doanh thu theo tháng
  - Số đơn hàng theo tháng
  - Tỉ lệ giao trễ theo tháng

#### 📊 Phân bố trạng thái giao hàng
- Doughnut chart hiển thị tỉ lệ:
  - Late delivery
  - Advance shipping
  - Shipping on time
  - Các trạng thái khác

#### 🌍 Top 10 quốc gia theo doanh thu
- Horizontal bar chart
- Sắp xếp theo doanh thu giảm dần

#### 📦 Top 10 danh mục theo doanh thu
- Horizontal bar chart
- Sắp xếp theo doanh thu giảm dần

### 3. Tương quan thời tiết và giao hàng

Nếu dữ liệu thời tiết có thể join được với dữ liệu chuỗi cung ứng, dashboard sẽ hiển thị:
- **Hệ số tương quan** giữa:
  - Nhiệt độ và tỉ lệ giao trễ
  - Lượng mưa và tỉ lệ giao trễ
  - Tốc độ gió và tỉ lệ giao trễ
- **Tỉ lệ merge:** Phần trăm dữ liệu có thể join được

### 4. Bộ lọc (Filters)

Dashboard cung cấp các bộ lọc để phân tích chi tiết:
- **Quốc gia:** Lọc theo quốc gia đơn hàng
- **Danh mục:** Lọc theo category sản phẩm
- **Trạng thái giao hàng:** Lọc theo delivery status
- **Khoảng thời gian:** Lọc theo ngày bắt đầu và kết thúc

Sau khi chọn bộ lọc, nhấn **"Áp dụng bộ lọc"** để cập nhật KPI và biểu đồ.

### 5. Bảng mẫu đơn hàng

Hiển thị 50 đơn hàng gần nhất với các thông tin:
- Order ID
- Quốc gia
- Danh mục
- Ngày đơn hàng
- Trạng thái giao hàng
- Có giao trễ hay không
- Doanh thu

---

## 🔧 Cấu trúc dự án

```
D:\Data_F\
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app chính
│   ├── routers/
│   │   ├── __init__.py
│   │   └── dashboard.py        # Router cho dashboard
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_loader.py      # Module đọc và xử lý CSV
│   │   ├── analytics.py         # Module tính toán KPI và thống kê
│   │   └── data_profiler.py    # Module phân tích chất lượng dữ liệu
│   ├── templates/
│   │   ├── base.html           # Template base
│   │   └── dashboard.html      # Template dashboard
│   └── static/
│       └── js/
│           └── dashboard_charts.js  # JavaScript cho charts
├── data/
│   ├── DataCoSupplyChainDataset.csv
│   └── geocoded_weather.csv
├── docs/
│   ├── data_quality_report.md  # Báo cáo chất lượng dữ liệu
│   ├── data_improvement_plan.md # Kế hoạch cải tiến dữ liệu
│   └── README_dashboard.md      # File này
├── scripts/
│   └── generate_data_quality_report.py  # Script tạo báo cáo
└── requirements.txt             # Python dependencies
```

---

## 📈 API Endpoints

### 1. GET `/dashboard`
Trả về trang dashboard HTML.

### 2. GET `/dashboard/api/data`
Trả về dữ liệu JSON cho frontend:
```json
{
  "kpis": {...},
  "top_products": [...],
  "top_countries": [...],
  "time_series": {...},
  "delivery_status_dist": {...},
  "weather_stats": {...},
  "weather_correlation": {...}
}
```

### 3. GET `/dashboard/api/filter`
Lọc dữ liệu theo các tham số:
- `country`: Tên quốc gia
- `category`: Tên danh mục
- `delivery_status`: Trạng thái giao hàng
- `start_date`: Ngày bắt đầu (YYYY-MM-DD)
- `end_date`: Ngày kết thúc (YYYY-MM-DD)

Ví dụ:
```
GET /dashboard/api/filter?country=United States&category=Electronics&start_date=2018-01-01&end_date=2018-12-31
```

### 4. GET `/health`
Health check endpoint, trả về status của API.

---

## 🔍 Tạo báo cáo chất lượng dữ liệu

Để tạo báo cáo chất lượng dữ liệu:

```bash
python scripts/generate_data_quality_report.py
```

Báo cáo sẽ được lưu tại: `docs/data_quality_report.md`

---

## 💡 Các đề xuất cải tiến dữ liệu

Xem file `docs/data_improvement_plan.md` để biết chi tiết về:
1. **Chuẩn hóa & tái cấu trúc dữ liệu:** Chuyển sang mô hình Star Schema
2. **Cải thiện chất lượng dữ liệu:** Xử lý missing values, outliers, chuẩn hóa format
3. **Cải thiện khả năng phục vụ AI/ML:** Tạo Feature Store
4. **Roadmap triển khai:** Các bước thực hiện từng giai đoạn

---

## 🐛 Xử lý lỗi thường gặp

### Lỗi: ModuleNotFoundError: No module named 'pandas'
**Giải pháp:** Chạy `pip install -r requirements.txt`

### Lỗi: FileNotFoundError khi đọc CSV
**Giải pháp:** Kiểm tra đường dẫn file trong `app/services/data_loader.py` và đảm bảo file CSV tồn tại trong thư mục `data/`

### Lỗi: Encoding error khi đọc CSV
**Giải pháp:** Module `data_loader.py` đã tự động thử các encoding khác nhau. Nếu vẫn lỗi, kiểm tra encoding của file CSV và cập nhật trong code.

### Dashboard không hiển thị biểu đồ
**Giải pháp:**
- Kiểm tra console của trình duyệt (F12) để xem lỗi JavaScript
- Đảm bảo Chart.js đã load (kiểm tra Network tab)
- Kiểm tra dữ liệu từ API endpoint `/dashboard/api/data`

---

## 📝 Ghi chú

- Dữ liệu được cache trong memory sau lần load đầu tiên để tăng tốc độ. Nếu cập nhật file CSV, cần restart server.
- Dashboard hỗ trợ responsive design, có thể xem trên mobile/tablet.
- Các biểu đồ sử dụng Chart.js, hỗ trợ zoom và tương tác.

---

## 🔐 Bảo mật

- **Lưu ý:** Dashboard hiện tại chạy ở chế độ development. Khi deploy production:
  - Sử dụng HTTPS
  - Thêm authentication/authorization
  - Giới hạn rate limiting
  - Validate và sanitize input từ user

---

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs của server (terminal nơi chạy uvicorn)
2. Kiểm tra console của trình duyệt (F12)
3. Xem các file documentation trong thư mục `docs/`

---

**Chúc bạn sử dụng dashboard hiệu quả! 🚀**

