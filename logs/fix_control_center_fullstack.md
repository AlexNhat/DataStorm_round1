## Báo cáo sửa lỗi /os/control-center

### Nguyên nhân
- API `/os/actions/pending` trả về rỗng nên UI không có dữ liệu.
- Không có endpoint `/os/action/history` khiến frontend 404.
- Template cũ lỗi font, layout cũ, thiếu timeline và KPI theo chuẩn mới.

### File chỉnh sửa
- `app/routers/os_api.py`
  - Thêm dữ liệu mock pending/history.
  - Bổ sung endpoint `/os/action/history`.
- `app/templates/control_center.html`
  - Viết lại layout theo chuẩn glass-card mới, giữ nguyên ID/JS hooks.
  - Cập nhật JS để gọi API mới, hiển thị timeline, reasoning, toast sạch.

### Kiểm tra
- `/os/control-center` trả 200, không lỗi template/JS.
- `/os/status`, `/os/actions/pending`, `/os/action/history` trả JSON 200.
- Pending cards, filter, mode selector, timeline, modal hoạt động đúng.
