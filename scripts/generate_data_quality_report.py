"""
Script để tạo báo cáo chất lượng dữ liệu.
Chạy script này để phân tích và tạo file data_quality_report.md
"""

import sys
import os

# Thêm thư mục app vào path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from app.services.data_loader import load_supply_chain_data, load_weather_data, suggest_join_keys
from app.services.data_profiler import check_data_quality, detect_outliers
from app.services.analytics import calculate_descriptive_stats, calculate_supply_chain_kpis
import pandas as pd


def generate_markdown_report():
    """Tạo báo cáo chất lượng dữ liệu dưới dạng Markdown."""
    
    print("Đang đọc dữ liệu...")
    try:
        supply_df = load_supply_chain_data()
        weather_df = load_weather_data()
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu: {e}")
        return
    
    print("Đang phân tích chất lượng dữ liệu...")
    
    # Phân tích chất lượng
    supply_quality = check_data_quality(supply_df, "Supply Chain Dataset")
    weather_quality = check_data_quality(weather_df, "Weather Dataset")
    
    # Phân tích outliers cho một số cột quan trọng
    supply_outliers = {}
    important_numeric_cols = ['Sales', 'Benefit per order', 'Days for shipping (real)']
    for col in important_numeric_cols:
        if col in supply_df.columns:
            supply_outliers[col] = detect_outliers(supply_df, col)
    
    # Phân tích join keys
    join_suggestions = suggest_join_keys(supply_df, weather_df)
    
    # Tạo nội dung Markdown
    markdown_content = f"""# BÁO CÁO CHẤT LƯỢNG DỮ LIỆU

**Ngày tạo:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 1. TỔNG QUAN DATASET

### 1.1. Supply Chain Dataset

- **Tổng số bản ghi:** {supply_quality['total_rows']:,}
- **Tổng số cột:** {supply_quality['total_columns']}
- **Số dòng trùng lặp:** {supply_quality['duplicate_rows']:,}

### 1.2. Weather Dataset

- **Tổng số bản ghi:** {weather_quality['total_rows']:,}
- **Tổng số cột:** {weather_quality['total_columns']}
- **Số dòng trùng lặp:** {weather_quality['duplicate_rows']:,}

---

## 2. PHÂN TÍCH MISSING VALUES

### 2.1. Supply Chain Dataset

"""
    
    if supply_quality['missing_data']:
        markdown_content += "| Cột | Số lượng missing | Tỉ lệ (%) |\n"
        markdown_content += "|-----|------------------|-----------|\n"
        for col, info in sorted(supply_quality['missing_data'].items(), 
                               key=lambda x: x[1]['percentage'], reverse=True):
            if info['percentage'] > 0:
                markdown_content += f"| {col} | {info['count']:,} | {info['percentage']:.2f}% |\n"
    else:
        markdown_content += "✓ Không có missing values đáng kể.\n"
    
    markdown_content += "\n### 2.2. Weather Dataset\n\n"
    
    if weather_quality['missing_data']:
        markdown_content += "| Cột | Số lượng missing | Tỉ lệ (%) |\n"
        markdown_content += "|-----|------------------|-----------|\n"
        for col, info in sorted(weather_quality['missing_data'].items(), 
                               key=lambda x: x[1]['percentage'], reverse=True):
            if info['percentage'] > 0:
                markdown_content += f"| {col} | {info['count']:,} | {info['percentage']:.2f}% |\n"
    else:
        markdown_content += "✓ Không có missing values đáng kể.\n"
    
    markdown_content += "\n---\n\n## 3. PHÁT HIỆN OUTLIERS\n\n"
    
    for col, outlier_info in supply_outliers.items():
        if 'error' not in outlier_info:
            markdown_content += f"### 3.1. Cột: {col}\n\n"
            markdown_content += f"- **Phương pháp:** {outlier_info['method']}\n"
            markdown_content += f"- **Số lượng outliers:** {outlier_info['outliers_count']:,} ({outlier_info['outliers_percentage']:.2f}%)\n"
            if 'bounds' in outlier_info:
                markdown_content += f"- **Giới hạn:** [{outlier_info['bounds']['lower']:.2f}, {outlier_info['bounds']['upper']:.2f}]\n"
            if outlier_info['outliers_examples']:
                markdown_content += f"- **Ví dụ outliers:** {outlier_info['outliers_examples'][:5]}\n"
            markdown_content += "\n"
    
    markdown_content += "\n---\n\n## 4. VẤN ĐỀ VỀ ĐỊNH DẠNG\n\n"
    
    if supply_quality['format_issues']:
        markdown_content += "### 4.1. Supply Chain Dataset\n\n"
        for issue in supply_quality['format_issues']:
            markdown_content += f"- **Cột:** {issue['column']}\n"
            markdown_content += f"  - **Vấn đề:** {issue['issue']}\n"
            markdown_content += f"  - **Số lượng:** {issue['count']:,}\n"
            if 'percentage' in issue:
                markdown_content += f"  - **Tỉ lệ:** {issue['percentage']:.2f}%\n"
            markdown_content += "\n"
    else:
        markdown_content += "✓ Không phát hiện vấn đề về định dạng.\n\n"
    
    markdown_content += "\n---\n\n## 5. CỘT NHẠY CẢM\n\n"
    
    if supply_quality['sensitive_columns']:
        markdown_content += "### ⚠️ Các cột chứa thông tin nhạy cảm:\n\n"
        for col in supply_quality['sensitive_columns']:
            markdown_content += f"- `{col}`\n"
        markdown_content += "\n**Khuyến nghị:** Các cột này không nên được sử dụng trực tiếp trong phân tích. Nên mã hoá hoặc loại bỏ.\n\n"
    else:
        markdown_content += "✓ Không phát hiện cột nhạy cảm.\n\n"
    
    markdown_content += "\n---\n\n## 6. VẤN ĐỀ VỀ TÍNH NHẤT QUÁN\n\n"
    
    if 'country_variations' in supply_quality:
        markdown_content += "### 6.1. Tên quốc gia không nhất quán\n\n"
        markdown_content += f"- **Số lượng biến thể:** {supply_quality['country_variations']['unique_count']}\n"
        markdown_content += "- **Ví dụ:**\n"
        for country in supply_quality['country_variations']['examples'][:10]:
            markdown_content += f"  - {country}\n"
        markdown_content += "\n**Nhận xét:** Có thể có các biến thể như 'EE. UU.' vs 'United States', cần chuẩn hoá.\n\n"
    
    markdown_content += "\n---\n\n## 7. ĐỀ XUẤT JOIN 2 DATASET\n\n"
    
    if join_suggestions['recommended_join']:
        rec_join = join_suggestions['recommended_join']
        markdown_content += f"### 7.1. Phương pháp được đề xuất: {rec_join['description']}\n\n"
        markdown_content += f"- **Keys từ Supply Chain:** {', '.join(rec_join['keys']['supply'])}\n"
        markdown_content += f"- **Keys từ Weather:** {', '.join(rec_join['keys']['weather'])}\n\n"
    
    if join_suggestions['mapping_needed']:
        markdown_content += "### 7.2. Cần mapping/chuẩn hoá:\n\n"
        for mapping in join_suggestions['mapping_needed']:
            markdown_content += f"- **{mapping['type']}:** {mapping['description']}\n"
            markdown_content += f"  - Supply Chain có {mapping['supply_unique']} giá trị unique\n"
            markdown_content += f"  - Weather có {mapping['weather_unique']} giá trị unique\n"
            markdown_content += f"  - Trùng lặp: {mapping['overlap']} giá trị\n\n"
    
    markdown_content += "\n---\n\n## 8. KẾT LUẬN VÀ KHUYẾN NGHỊ\n\n"
    
    markdown_content += "### 8.1. Vấn đề cần xử lý ngay:\n\n"
    markdown_content += "1. **Chuẩn hoá tên quốc gia:** Tạo bảng mapping để đồng nhất các tên quốc gia.\n"
    markdown_content += "2. **Xử lý missing values:** Quyết định fill, drop hoặc tạo category 'Unknown'.\n"
    markdown_content += "3. **Xử lý outliers:** Kiểm tra và quyết định giữ lại hay loại bỏ.\n"
    markdown_content += "4. **Bảo vệ dữ liệu nhạy cảm:** Mã hoá hoặc loại bỏ các cột chứa thông tin cá nhân.\n\n"
    
    markdown_content += "### 8.2. Cải tiến đề xuất:\n\n"
    markdown_content += "1. **Chuẩn hoá format ngày:** Đảm bảo tất cả ngày tháng ở format ISO 8601.\n"
    markdown_content += "2. **Tạo bảng dim_geolocation:** Mapping city/country → lat/lon để join với weather.\n"
    markdown_content += "3. **Tạo derived columns:** lead_time, weather_risk_level, etc.\n"
    markdown_content += "4. **Xây dựng star schema:** Tách fact và dimension tables để tối ưu truy vấn.\n\n"
    
    # Lưu file
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'data_quality_report.md')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"✓ Đã tạo báo cáo tại: {output_path}")


if __name__ == '__main__':
    generate_markdown_report()

