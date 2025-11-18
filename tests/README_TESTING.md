# Hệ thống kiểm thử Supply Chain AI

## 1. Tổng quan
- **Unit tests**: kiểm tra logic xử lý dữ liệu, feature engineering.
- **Integration tests**: pipeline nhỏ (ETL → feature store → train), API response format.
- **Regression (ML) tests**: so sánh metric mới với baseline (`tests/metrics_baseline.json`).
- **UI tests**: kiểm tra layout, prediction form, snapshot, visual diff.
- **Visual regression**: so sánh ảnh screenshot baseline vs current.
- **Smoke tests**: phần mở rộng (đặt tại `tests/smoke/`).

## 2. Cấu trúc thư mục tests/
```
unit/                  # data validation, feature engineering
integration/           # pipeline & API
regression/            # ML metric thresholds
smoke/                 # có thể thêm smoke scenario
ui/                    # toàn bộ UI tests + snapshots
visual_regression/     # baseline screenshot + test script
conftest.py            # HTTP client fixture (ASGI)
data_samples/          # dữ liệu mẫu phục vụ test
metrics_baseline.json  # baseline metrics cho regression
README_TESTING.md      # tài liệu này
```

## 3. Mocking strategy
- Sử dụng `httpx.ASGITransport` để gọi trực tiếp app FastAPI -> không cần server thật.
- Test data nạp từ các file mẫu trong `tests/data_samples` (dự kiến mở rộng).

## 4. UI Snapshot Strategy
- Snapshot HTML nằm tại `tests/ui/snapshots/dashboard.html`.
- Khi UI thay đổi hợp lệ: chạy script cập nhật snapshot rồi commit.
- Test `test_dashboard_snapshot` so sánh HTML mới với baseline.

## 5. Visual Regression Testing
- Ảnh baseline: `visual_regression/baseline/dashboard.png`.
- Test `visual_regression/test_visual_regression.py` tạo ảnh mới và so sánh diff (ngưỡng trung bình ≤ 1.0).
- Ảnh diff latest: `results/test_reports/ui_visual_diff.png`.

## 6. Chạy test
```
python scripts/run_all_tests_and_build_report.py
```
- Kết quả: `results/test_reports/test_report.json` + `full_test_log.txt`.
- UI Dashboard: `/dashboard/test-report` hiển thị báo cáo trực quan.
- Có thể gọi API `GET /test/run` để chạy lại từ giao diện.

## 7. Đọc báo cáo
- API: `/test/report` trả JSON đầy đủ.
- UI: `/dashboard/test-report` hiển thị summary, bảng chi tiết, biểu đồ, gallery.
- Ảnh snapshot & diff hiển thị trong gallery.

## 8. Best practice viết test mới
- Đặt test đúng thư mục (unit/integration/ui/...).
- Đặt tên file & hàm rõ ràng, gắn với category.
- Sử dụng fixture `http_client` nếu cần gọi API.
- Cập nhật `tests/metrics_baseline.json` nếu metric baseline thay đổi.
- Nếu thêm UI component mới → tạo snapshot/visual baseline tương ứng.

