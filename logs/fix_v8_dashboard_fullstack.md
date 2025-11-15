## Báo cáo sửa lỗi /v8/dashboard

### Nguyên nhân lỗi ban đầu
- Route `/v8/dashboard` nhận context trống nên template cố render biến không tồn tại → 500.
- Frontend chỉ hiển thị placeholder, nút gọi API chưa có → người dùng không biết chiến lược sinh ra thế nào.
- JSON dump các metric model huấn luyện dùng `numpy.float32` gây `TypeError` khi lưu.

### File đã chỉnh sửa
- `app/routers/cognitive_api.py`: bổ sung snapshot dữ liệu mặc định, endpoints `/v8/dashboard/data`, `/v8/actions/trigger`, trả `ui_cards` cho FE.
- `app/templates/cognitive_dashboard.html`: viết lại layout sử dụng cùng pattern với dashboard chính, hiển thị KPI, chart, thẻ chiến lược, bảng model, log, action + JS tương tác.
- `scripts/train_model_logistics_delay.py`, `scripts/train_model_churn.py`: thêm helper `to_serializable` và dùng khi ghi JSON.

### Tối ưu backend
- Chuẩn hoá dữ liệu fallback, định dạng KPI/metric/risks, đảm bảo tất cả biến template luôn có.
- Thêm API snapshot/trigger để FE làm mới dữ liệu, xử lý phản hồi nút hành động.
- Tránh lỗi float32 JSON ở script train → pipeline không còn crash.

### Cải tiến frontend
- Layout mới theo base dashboard: glass-card, chart placeholder Chart.js, thẻ chiến lược chi tiết, log, bảng model, quick action.
- JS hydrate dữ liệu ban đầu, gọi `/v8/dashboard/data` refresh, `/v8/strategies/generate` sinh chiến lược và cập nhật UI, `/v8/actions/trigger` log hành động.

### Kết quả kiểm tra
- `/v8/dashboard` trả 200 với snapshot mặc định, không lỗi template/JS.
- Button refresh, tạo chiến lược, quick action đều gọi API thật và cập nhật UI/log.
- Huấn luyện model ghi log JSON thành công, không còn `float32` serialization error.
