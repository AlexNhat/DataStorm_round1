# JUPYTER NOTEBOOKS

Thư mục này chứa các notebook và script để phân tích dữ liệu.

## Cách sử dụng

### Option 1: Sử dụng script Python

File `analysis_script.py` chứa tất cả các cell code. Bạn có thể:

1. Mở Jupyter Notebook:
   ```bash
   jupyter notebook
   ```

2. Tạo notebook mới và copy từng cell từ `analysis_script.py` vào notebook

3. Hoặc chạy trực tiếp script:
   ```bash
   python notebooks/analysis_script.py
   ```

### Option 2: Tạo notebook từ đầu

1. Mở Jupyter Notebook:
   ```bash
   jupyter notebook
   ```

2. Tạo notebook mới: `New > Python 3`

3. Copy và paste từng phần từ `analysis_script.py` vào các cell

## Nội dung phân tích

Script bao gồm các phần:

1. **Import thư viện**: Pandas, NumPy, Matplotlib, Seaborn
2. **Đọc dữ liệu**: Load Supply Chain và Weather data
3. **Tổng quan dữ liệu**: Thông tin cơ bản về datasets
4. **Tính toán KPI**: Doanh thu, lợi nhuận, tỉ lệ giao trễ
5. **Top Products & Countries**: Phân tích top performers
6. **Time Series Analysis**: Xu hướng theo thời gian
7. **Weather Correlation**: Tương quan thời tiết và giao hàng
8. **Delivery Status Distribution**: Phân bố trạng thái giao hàng
9. **Kết luận**: Insights và đề xuất

## Yêu cầu

Đảm bảo đã cài đặt:
- Jupyter Notebook: `pip install jupyter`
- Các thư viện trong `requirements.txt`

## Lưu ý

- Script sử dụng các module từ `app/services/`, đảm bảo chạy từ thư mục gốc dự án
- Một số visualization có thể cần điều chỉnh tùy vào dữ liệu thực tế

