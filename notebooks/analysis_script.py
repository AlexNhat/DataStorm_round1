"""
Python script để chạy trong Jupyter Notebook
Copy và paste từng cell vào Jupyter để chạy
"""

# ============================================================================
# CELL 1: IMPORT THƯ VIỆN
# ============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Cấu hình hiển thị
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

print("✓ Đã import các thư viện cần thiết")

# ============================================================================
# CELL 2: ĐỌC DỮ LIỆU
# ============================================================================
import os
import sys

# Thêm thư mục app vào path
sys.path.insert(0, os.path.join('..', 'app'))

from services.data_loader import load_supply_chain_data, load_weather_data

print("Đang đọc dữ liệu...")

# Đọc dữ liệu
supply_df = load_supply_chain_data()
weather_df = load_weather_data()

print(f"\n✓ Đã đọc Supply Chain data: {len(supply_df):,} bản ghi")
print(f"✓ Đã đọc Weather data: {len(weather_df):,} bản ghi")

# ============================================================================
# CELL 3: TỔNG QUAN DỮ LIỆU
# ============================================================================
print("=== TỔNG QUAN SUPPLY CHAIN DATASET ===")
print(f"Số dòng: {len(supply_df):,}")
print(f"Số cột: {len(supply_df.columns)}")
print(f"\nCác cột quan trọng:")
important_cols = ['Order Id', 'Sales', 'Benefit per order', 'Delivery Status', 
                  'Late_delivery_risk', 'Order Country', 'Category Name', 
                  'order date (DateOrders)']
for col in important_cols:
    if col in supply_df.columns:
        print(f"  - {col}")

print("\n=== 5 DÒNG ĐẦU TIÊN ===")
display(supply_df.head())

# ============================================================================
# CELL 4: TÍNH TOÁN KPI
# ============================================================================
from services.analytics import calculate_supply_chain_kpis

# Tính KPI
kpis = calculate_supply_chain_kpis(supply_df)

print("=== CÁC KPI CHÍNH ===")
print(f"Tổng doanh thu: ${kpis.get('total_sales', 0):,.2f}")
print(f"Tổng lợi nhuận: ${kpis.get('total_benefit', 0):,.2f}")
print(f"Tổng số đơn hàng: {kpis.get('total_orders', 0):,}")
print(f"Tỉ lệ giao trễ: {kpis.get('late_delivery_rate', 0):.2f}%")
print(f"Tỉ lệ giao đúng hạn: {kpis.get('on_time_delivery_rate', 0):.2f}%")
print(f"Số ngày giao hàng trung bình: {kpis.get('avg_shipping_days', 0):.2f} ngày")

# ============================================================================
# CELL 5: TOP PRODUCTS VÀ COUNTRIES
# ============================================================================
from services.analytics import get_top_products, get_top_countries

# Top products
top_products = get_top_products(supply_df, top_n=10, by='Sales')
top_countries = get_top_countries(supply_df, top_n=10, by='Sales')

print("=== TOP 10 SẢN PHẨM THEO DOANH THU ===")
for i, product in enumerate(top_products, 1):
    print(f"{i}. {product['category']}: ${product['sales']:,.2f}")

print("\n=== TOP 10 QUỐC GIA THEO DOANH THU ===")
for i, country in enumerate(top_countries, 1):
    print(f"{i}. {country['country']}: ${country['sales']:,.2f} ({country['orders']:,} đơn)")

# Visualization
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Top Products
products_df = pd.DataFrame(top_products)
axes[0].barh(products_df['category'], products_df['sales'] / 1e6)
axes[0].set_xlabel('Doanh thu (Triệu USD)')
axes[0].set_title('Top 10 Sản phẩm theo Doanh thu')
axes[0].grid(axis='x', alpha=0.3)

# Top Countries
countries_df = pd.DataFrame(top_countries)
axes[1].barh(countries_df['country'], countries_df['sales'] / 1e6)
axes[1].set_xlabel('Doanh thu (Triệu USD)')
axes[1].set_title('Top 10 Quốc gia theo Doanh thu')
axes[1].grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.show()

# ============================================================================
# CELL 6: TIME SERIES ANALYSIS
# ============================================================================
from services.analytics import get_time_series_data

# Lấy dữ liệu time series theo tháng
time_series = get_time_series_data(supply_df, freq='M')

print("=== TIME SERIES DATA ===")
print(f"Số tháng có dữ liệu: {len(time_series.get('sales', {}))}")

# Chuyển đổi sang DataFrame để dễ visualize
if time_series.get('sales'):
    ts_df = pd.DataFrame({
        'Date': pd.to_datetime(list(time_series['sales'].keys())),
        'Sales': list(time_series['sales'].values()),
        'Orders': list(time_series.get('orders_count', {}).values()) if time_series.get('orders_count') else [0] * len(time_series['sales']),
        'Late Rate': list(time_series.get('late_delivery_rate', {}).values()) if time_series.get('late_delivery_rate') else [0] * len(time_series['sales'])
    })
    ts_df = ts_df.sort_values('Date')
    
    # Visualization
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    
    # 1. Doanh thu theo tháng
    axes[0].plot(ts_df['Date'], ts_df['Sales'] / 1e6, marker='o', linewidth=2)
    axes[0].set_ylabel('Doanh thu (Triệu USD)')
    axes[0].set_title('Xu hướng Doanh thu theo Tháng')
    axes[0].grid(True, alpha=0.3)
    axes[0].tick_params(axis='x', rotation=45)
    
    # 2. Số đơn hàng theo tháng
    axes[1].plot(ts_df['Date'], ts_df['Orders'], marker='s', color='green', linewidth=2)
    axes[1].set_ylabel('Số đơn hàng')
    axes[1].set_title('Xu hướng Số Đơn hàng theo Tháng')
    axes[1].grid(True, alpha=0.3)
    axes[1].tick_params(axis='x', rotation=45)
    
    # 3. Tỉ lệ giao trễ theo tháng
    axes[2].plot(ts_df['Date'], ts_df['Late Rate'], marker='^', color='red', linewidth=2)
    axes[2].set_ylabel('Tỉ lệ giao trễ (%)')
    axes[2].set_xlabel('Tháng')
    axes[2].set_title('Xu hướng Tỉ lệ Giao trễ theo Tháng')
    axes[2].grid(True, alpha=0.3)
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()

# ============================================================================
# CELL 7: PHÂN TÍCH TƯƠNG QUAN THỜI TIẾT
# ============================================================================
from services.analytics import analyze_weather_delivery_correlation, calculate_weather_stats

# Phân tích tương quan
correlation = analyze_weather_delivery_correlation(supply_df, weather_df)

print("=== KẾT QUẢ PHÂN TÍCH TƯƠNG QUAN ===")
if 'error' not in correlation:
    print(f"Số bản ghi đã merge: {correlation.get('merged_records', 0):,}")
    print(f"Tỉ lệ merge: {correlation.get('merge_rate', 0):.2f}%")
    print(f"\nHệ số tương quan:")
    if correlation.get('temperature_vs_late_delivery'):
        print(f"  - Nhiệt độ vs Giao trễ: {correlation.get('temperature_vs_late_delivery'):.4f}")
    if correlation.get('precipitation_vs_late_delivery'):
        print(f"  - Lượng mưa vs Giao trễ: {correlation.get('precipitation_vs_late_delivery'):.4f}")
    if correlation.get('wind_speed_vs_late_delivery'):
        print(f"  - Tốc độ gió vs Giao trễ: {correlation.get('wind_speed_vs_late_delivery'):.4f}")
else:
    print(f"Lỗi: {correlation.get('error')}")
    if 'suggestion' in correlation:
        print(f"Gợi ý: {correlation.get('suggestion')}")

# Thống kê thời tiết
weather_stats = calculate_weather_stats(weather_df)

print("\n=== THỐNG KÊ THỜI TIẾT ===")
if 'temperature' in weather_stats:
    print(f"\nNhiệt độ:")
    print(f"  - Min: {weather_stats['temperature']['min']:.2f}°C")
    print(f"  - Max: {weather_stats['temperature']['max']:.2f}°C")
    print(f"  - Mean: {weather_stats['temperature']['mean']:.2f}°C")

if 'precipitation' in weather_stats:
    print(f"\nLượng mưa:")
    print(f"  - Min: {weather_stats['precipitation']['min']:.2f} mm")
    print(f"  - Max: {weather_stats['precipitation']['max']:.2f} mm")
    print(f"  - Mean: {weather_stats['precipitation']['mean']:.2f} mm")

# ============================================================================
# CELL 8: PHÂN BỐ DELIVERY STATUS
# ============================================================================
if 'Delivery Status' in supply_df.columns:
    delivery_dist = supply_df['Delivery Status'].value_counts()
    
    print("=== PHÂN BỐ TRẠNG THÁI GIAO HÀNG ===")
    print(delivery_dist)
    
    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Bar chart
    axes[0].bar(delivery_dist.index, delivery_dist.values)
    axes[0].set_ylabel('Số lượng')
    axes[0].set_title('Phân bố Trạng thái Giao hàng (Bar Chart)')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].grid(axis='y', alpha=0.3)
    
    # Pie chart
    axes[1].pie(delivery_dist.values, labels=delivery_dist.index, autopct='%1.1f%%', startangle=90)
    axes[1].set_title('Phân bố Trạng thái Giao hàng (Pie Chart)')
    
    plt.tight_layout()
    plt.show()

# ============================================================================
# CELL 9: KẾT LUẬN
# ============================================================================
print("""
=== KẾT LUẬN VÀ INSIGHTS ===

1. KPI Tổng quan:
   - Tổng doanh thu và lợi nhuận
   - Tỉ lệ giao hàng trễ
   - Số đơn hàng

2. Top Performers:
   - Top sản phẩm và quốc gia theo doanh thu
   - Phân tích xu hướng

3. Time Series:
   - Xu hướng doanh thu, số đơn hàng, tỉ lệ giao trễ theo thời gian
   - Phát hiện patterns và seasonality

4. Weather Impact:
   - Tương quan giữa thời tiết và giao hàng
   - Phân tích tác động của nhiệt độ, lượng mưa, tốc độ gió

=== ĐỀ XUẤT CẢI TIẾN ===

1. Chuẩn hóa dữ liệu: Tên quốc gia, format ngày tháng, missing values
2. Cải thiện join: Tạo bảng mapping city/country → lat/lon
3. Star Schema: Tách fact và dimension tables
4. Feature Store: Chuẩn bị cho ML models

Xem chi tiết trong file docs/data_improvement_plan.md
""")

