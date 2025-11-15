# Dashboard & Model Registry – Global Update

## Tổng quan
- Registry chuyển sang sử dụng `data/model_registry.json` làm nguồn duy nhất.
- API mới `/api/models` cùng dashboard `/dashboard/models` đọc trực tiếp JSON này.
- UI thể hiện rõ region GLOBAL, version mới và trạng thái Success sau khi fix pipeline weather.

## Model Registry
- File: `data/model_registry.json`
- Mỗi entry gồm: `name`, `version`, `owner`, `region`, `accuracy`, `last_update`, `status`, `note`, `artifacts`.
- Dữ liệu cập nhật sau các lần train dùng merged dataset toàn cầu.
- Ghi chú mặc định: “Updated using global merged supplychain-weather dataset. Fixed previous EU weather timeout.”

## API
- Router: `app/routers/models_registry.py`
- `GET /api/models` → trả danh sách models JSON.
- `GET /dashboard/models` → render bảng tổng quan.
- `GET /dashboard/models/{slug}` → chi tiết từng model với link metrics/logs.

## UI
- Template: `app/templates/dashboard/models_list.html` (bảng danh sách) và `model_detail.html` (chi tiết).
- Navigation trong `base.html` đã thêm link “Danh sách mô hình”.
- Status badge dùng màu:
  - Success: #CCFBE1
  - Warn: #FFE8B3
  - Error: #FFCCCC

## Workflow cập nhật
1. Train mô hình → sinh metrics/logs dưới `models/**/global` và `results/**`.
2. Cập nhật `data/model_registry.json` với version/accuracy mới.
3. UI/API tự động phản ánh thay đổi; không cần sửa code thêm.

## Hướng dẫn cho model mới
- Thêm entry vào `model_registry.json` với đầy đủ trường, region = GLOBAL.
- Cung cấp đường dẫn metrics/logs để trang chi tiết hiển thị đúng.
