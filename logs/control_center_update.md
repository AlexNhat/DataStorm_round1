## Control Center Update

- **Backend**: `app/routers/os_api.py`
  - Cung cấp dữ liệu thật cho `/os/actions/pending`, `/os/actions/approve`, `/os/actions/reject`, `/os/action/history` theo format chuẩn.
  - Lưu trạng thái pending và history, tính aggregations `by_hour`, `by_type`.

- **Frontend**: `app/templates/control_center.html`
  - UI glass-card mới, sử dụng dữ liệu thật cho pending list, modal phê duyệt, timeline.
  - Modal gửi payload chuẩn approve/reject, refresh list/history khi thành công.
  - Biểu đồ Chart.js (line + donut) đọc aggregations từ API history.

- **Test**:
  - GET `/os/control-center` → 200, load đầy đủ pending actions từ API.
  - POST `/os/actions/approve`/`/os/actions/reject` → trả JSON chuẩn, UI cập nhật.
  - GET `/os/action/history` → trả `history` + `aggregations` và render biểu đồ.
