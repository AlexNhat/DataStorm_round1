# Báo cáo quét lỗi Localization UI

Ngày kiểm tra: 2025-11-14  
Người thực hiện: Codex – Senior Fullstack Engineer & Localization Specialist

## 1. Danh sách tuyến UI đã kiểm tra
| Route | Trạng thái | Ghi chú |
|-------|-----------|---------|
| `/v8/dashboard` | 200 | Phát hiện nhiều ký tự mã hóa sai tại phần tiêu đề và mô tả |
| `/os/control-center` | 200 | Không phát hiện lỗi mã hóa, tuy nhiên một số label vẫn dùng tiếng Anh (“Pending actions”) |
| `/dashboard/test-report` | 200 | Nội dung tiếng Anh mặc định (“Test Summary”, “Tests run”) |
| `/dashboard/ai` | 200 | Card vẫn thể hiện phần tiếng Anh (“Model Status”, “Confusion Matrix”) |
| `/docs`, `/notebooks` | 200 | Hiển thị danh sách file ở dạng tiếng Anh |
| `/dashboard` | 307 | Redirect – không nằm trong phạm vi localization (giữ nguyên) |

## 2. Các lỗi localization cụ thể
| Route / File | Vị trí | Hiện trạng | Đề xuất sửa |
|--------------|--------|------------|-------------|
| `/v8/dashboard` – `app/templates/cognitive_dashboard.html` | `h1`, `p` header, label input | Văn bản hiển thị dạng “dY…”, “AI phA�n tA-ch…” do dữ liệu đã bị double-encoded trước khi render | Thay thế toàn bộ chuỗi bằng tiếng Việt chuẩn, ví dụ “Đề xuất chiến lược AI”, “AI phân tích và đề xuất các chiến lược tối ưu cho chuỗi cung ứng” |
| `/v8/dashboard` – reasoning panel | Section title hiển thị “?? Đề xuất & Lý luận AI” | Ký tự emoji không hiển thị đúng, mô tả “Giải thích vì sao…” vẫn có ký tự lạ | Dùng chuỗi ASCII thuần hoặc emoji chuẩn; viết lại mô tả tiếng Việt rõ ràng |
| `/os/control-center` – `app/templates/control_center.html` | Card pending actions | Tiêu đề “Pending actions”, button “View details” (tiếng Anh) | Dịch sang “Hành động chờ duyệt”, “Xem chi tiết” |
| `/dashboard/test-report` – `app/templates/test_dashboard.html` | Heading “Test Summary”, cột “Status” | Toàn bộ trang là tiếng Anh | Việt hóa hoàn toàn hoặc thêm cảnh báo “Đang trong quá trình dịch” |
| Base navigation – `app/templates/base.html` | Navbar | Chuỗi “Dashboard”, “Test Report”, “Health”… | Dịch sang “Tổng quan”, “Báo cáo kiểm thử”, “Sức khỏe hệ thống”… |
| Component labels khác | JS/custom text | Một số tooltip (“Action plan”, “Apply Recommendation”) vẫn tiếng Anh | Duyệt toàn bộ template/scripts và dịch sang tiếng Việt |

## 3. Đề xuất hành động
1. Chuẩn hóa lại toàn bộ chuỗi tiếng Việt trong template/JS – không để chuỗi đã bị double-encoding.  
2. Tạo file resource (JSON/yaml) để quản lý chuỗi, tránh copy/paste chữ tiếng Việt sai.  
3. Với những trang chưa dịch xong (test-report), hiển thị banner “Đang Việt hóa” để người dùng không nhầm.  
4. Thêm test localization (xem bên dưới) để phát hiện lại ký tự lạ trước khi deploy.

## 4. Lưu ý cho backend & dữ liệu
- FastAPI hiện trả `Content-Type: text/html; charset=utf-8` – phù hợp.  
- Tuy nhiên dữ liệu tĩnh trong template vẫn đang ở dạng Unicode lỗi → cần sửa trực tiếp trong file `.html`.  
- Khi ghi log hoặc đọc từ file CSV, đảm bảo dùng `encoding='utf-8'`.  

## 5. Tiếp theo
Sau khi sửa toàn bộ chuỗi, chạy `tests/ui/test_ui_localization.py` để đảm bảo:
- Route trả 200.  
- Nội dung chứa một vài từ khóa tiếng Việt bắt buộc.  
- Không xuất hiện regex `Ã|Â|â€”|`.  

Việc quét định kỳ nên thực hiện trước mỗi lần release để tránh tái xuất hiện lỗi mã hóa.
