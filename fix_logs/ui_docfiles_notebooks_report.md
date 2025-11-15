# Báo cáo sửa lỗi UI doc-files & notebooks

## Vấn đề phát hiện
- Truy cập `/docs/...` và `/notebooks/...` trả 404 vì không có router phục vụ.
- UI vẫn trỏ vào đường dẫn cũ nên người dùng gặp `{"detail": "Not Found"}`.
- Chưa có trang danh sách/doc viewer/notebook preview.

## Thay đổi chính
1. Tạo router `app/routers/docs_viewer.py` với các endpoint:
   - `/doc-files/` (list) + `/doc-files/{file}` (view/download)
   - `/notebooks/` (list) + `/notebooks/{file}` (view/download)
2. Tạo template mới:
   - `doc_files_index.html`, `doc_file_view.html`
   - `notebook_files_index.html`, `notebook_file_view.html`
3. Cập nhật `app/main.py`:
   - Import và include router mới.
   - Loại bỏ route cũ chồng chéo, giữ mount static.
4. Cập nhật UI dashboard (`app/templates/ai_dashboard.html`): thêm nút truy cập Doc/Notebook.
5. Self-validation: dùng httpx ASGI client gọi lần lượt `/doc-files/`, `/doc-files/model_late_delivery.md`, `/notebooks/`, `/notebooks/model_late_delivery.ipynb`, `/dashboard/tests` → tất cả trả 200 OK.

## Kết quả
- Không còn lỗi 404 khi truy cập tài liệu/notebook.
- Có trang UI hiển thị danh sách file, xem nội dung và tải xuống.
- Dashboard hiển thị link “Tài liệu Docs” và “Notebooks”.
