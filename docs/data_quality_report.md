# BÁO CÁO CHẤT LƯỢNG DỮ LIỆU

**Ngày tạo:** 2025-11-14 19:02:26

---

## 1. TỔNG QUAN DATASET

### 1.1. Supply Chain Dataset

- **Tổng số bản ghi:** 180,519
- **Tổng số cột:** 53
- **Số dòng trùng lặp:** 0

### 1.2. Weather Dataset

- **Tổng số bản ghi:** 180,519
- **Tổng số cột:** 21
- **Số dòng trùng lặp:** 114,769

---

## 2. PHÂN TÍCH MISSING VALUES

### 2.1. Supply Chain Dataset

| Cột | Số lượng missing | Tỉ lệ (%) |
|-----|------------------|-----------|
| Product Description | 180,519 | 100.00% |
| Order Zipcode | 155,679 | 86.24% |

### 2.2. Weather Dataset

| Cột | Số lượng missing | Tỉ lệ (%) |
|-----|------------------|-----------|
| lat | 468 | 0.26% |
| lon | 468 | 0.26% |
| sunshine_duration | 468 | 0.26% |
| snowfall_sum | 468 | 0.26% |
| precipitation_hours | 468 | 0.26% |
| shortwave_radiation_sum | 468 | 0.26% |
| wind_direction_10m_dominant | 468 | 0.26% |
| weather_code | 468 | 0.26% |
| temperature_2m_mean | 468 | 0.26% |
| dew_point_2m_mean | 468 | 0.26% |
| relative_humidity_2m_mean | 468 | 0.26% |
| wind_speed_10m_mean | 468 | 0.26% |
| precipitation_sum | 468 | 0.26% |
| apparent_temperature_mean | 468 | 0.26% |
| temperature_2m_max | 468 | 0.26% |
| temperature_2m_min | 468 | 0.26% |

---

## 3. PHÁT HIỆN OUTLIERS

### 3.1. Cột: Sales

- **Phương pháp:** iqr
- **Số lượng outliers:** 488 (0.27%)
- **Giới hạn:** [-149.98, 569.91]
- **Ví dụ outliers:** [1500.0, 1500.0, 1500.0, 1500.0, 999.9899902]

### 3.1. Cột: Benefit per order

- **Phương pháp:** iqr
- **Số lượng outliers:** 18,942 (10.49%)
- **Giới hạn:** [-79.70, 151.50]
- **Ví dụ outliers:** [-249.0899963, -247.7799988, -259.5799866, -246.3600006, 154.8600006]

### 3.1. Cột: Days for shipping (real)

- **Phương pháp:** iqr
- **Số lượng outliers:** 0 (0.00%)
- **Giới hạn:** [-2.50, 9.50]


---

## 4. VẤN ĐỀ VỀ ĐỊNH DẠNG

✓ Không phát hiện vấn đề về định dạng.


---

## 5. CỘT NHẠY CẢM

### ⚠️ Các cột chứa thông tin nhạy cảm:

- `Customer Email`
- `Customer Password`
- `Order Item Cardprod Id`
- `Product Card Id`

**Khuyến nghị:** Các cột này không nên được sử dụng trực tiếp trong phân tích. Nên mã hoá hoặc loại bỏ.


---

## 6. VẤN ĐỀ VỀ TÍNH NHẤT QUÁN

### 6.1. Tên quốc gia không nhất quán

- **Số lượng biến thể:** 164
- **Ví dụ:**
  - Indonesia
  - India
  - Australia
  - China
  - Japón
  - Corea del Sur
  - Singapur
  - Turquía
  - Mongolia
  - Estados Unidos

**Nhận xét:** Có thể có các biến thể như 'EE. UU.' vs 'United States', cần chuẩn hoá.


---

## 7. ĐỀ XUẤT JOIN 2 DATASET

### 7.1. Phương pháp được đề xuất: Join theo Customer ID và ngày đơn hàng

- **Keys từ Supply Chain:** Order Customer Id, order date (DateOrders)
- **Keys từ Weather:** customer_id, order_date

### 7.2. Cần mapping/chuẩn hoá:

- **country_normalization:** Cần chuẩn hoá tên quốc gia (ví dụ: "EE. UU." vs "United States")
  - Supply Chain có 164 giá trị unique
  - Weather có 164 giá trị unique
  - Trùng lặp: 163 giá trị


---

## 8. KẾT LUẬN VÀ KHUYẾN NGHỊ

### 8.1. Vấn đề cần xử lý ngay:

1. **Chuẩn hoá tên quốc gia:** Tạo bảng mapping để đồng nhất các tên quốc gia.
2. **Xử lý missing values:** Quyết định fill, drop hoặc tạo category 'Unknown'.
3. **Xử lý outliers:** Kiểm tra và quyết định giữ lại hay loại bỏ.
4. **Bảo vệ dữ liệu nhạy cảm:** Mã hoá hoặc loại bỏ các cột chứa thông tin cá nhân.

### 8.2. Cải tiến đề xuất:

1. **Chuẩn hoá format ngày:** Đảm bảo tất cả ngày tháng ở format ISO 8601.
2. **Tạo bảng dim_geolocation:** Mapping city/country → lat/lon để join với weather.
3. **Tạo derived columns:** lead_time, weather_risk_level, etc.
4. **Xây dựng star schema:** Tách fact và dimension tables để tối ưu truy vấn.

