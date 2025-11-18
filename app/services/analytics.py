"""
Module phân tích dữ liệu và tính toán KPI.
Tính toán các thống kê mô tả, KPI kinh doanh, và phân tích tương quan.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from app.services.cache_manager import cached


def calculate_descriptive_stats(df: pd.DataFrame) -> Dict:
    """
    Tính các thống kê mô tả cơ bản cho dataset.
    
    Args:
        df: DataFrame cần phân tích
        
    Returns:
        Dictionary chứa các thống kê
    """
    stats = {
        'total_records': len(df),
        'total_columns': len(df.columns),
        'missing_values_count': df.isnull().sum().to_dict(),
        'missing_values_percentage': (df.isnull().sum() / len(df) * 100).round(2).to_dict()
    }
    
    return stats


@cached(ttl=1800)  # Cache for 30 minutes
def calculate_supply_chain_kpis(df: pd.DataFrame) -> Dict:
    """
    Tính các KPI chính của chuỗi cung ứng.
    
    Args:
        df: DataFrame chuỗi cung ứng
        
    Returns:
        Dictionary chứa các KPI
    """
    kpis = {}
    
    # Tổng doanh thu
    if 'Sales' in df.columns:
        kpis['total_sales'] = float(df['Sales'].sum())
        kpis['avg_sales_per_order'] = float(df['Sales'].mean())
    
    # Tổng lợi nhuận
    if 'Benefit per order' in df.columns:
        kpis['total_benefit'] = float(df['Benefit per order'].sum())
        kpis['avg_benefit_per_order'] = float(df['Benefit per order'].mean())
    
    if 'Order Item Profit Ratio' in df.columns:
        kpis['avg_profit_ratio'] = float(df['Order Item Profit Ratio'].mean())
    
    # Số lượng đơn hàng
    if 'Order Id' in df.columns:
        kpis['total_orders'] = int(df['Order Id'].nunique())
        kpis['total_order_items'] = len(df)
    
    # Tỉ lệ giao hàng trễ
    if 'Late_delivery_risk' in df.columns:
        late_count = int(df['Late_delivery_risk'].sum())
        total = len(df)
        kpis['late_delivery_count'] = late_count
        kpis['late_delivery_rate'] = float((late_count / total * 100) if total > 0 else 0)
        kpis['on_time_delivery_rate'] = float(100 - kpis['late_delivery_rate'])
    
    # Phân bố Delivery Status
    if 'Delivery Status' in df.columns:
        delivery_status_dist = df['Delivery Status'].value_counts().to_dict()
        kpis['delivery_status_distribution'] = {str(k): int(v) for k, v in delivery_status_dist.items()}
    
    # Số ngày giao hàng
    if 'Days for shipping (real)' in df.columns:
        kpis['avg_shipping_days'] = float(df['Days for shipping (real)'].mean())
        kpis['avg_scheduled_days'] = float(df['Days for shipment (scheduled)'].mean()) if 'Days for shipment (scheduled)' in df.columns else None
    
    return kpis


@cached(ttl=1800)  # Cache for 30 minutes
def get_top_products(df: pd.DataFrame, top_n: int = 10, by: str = 'Sales') -> List[Dict]:
    """
    Lấy top sản phẩm theo doanh thu hoặc lợi nhuận.
    
    Args:
        df: DataFrame chuỗi cung ứng
        top_n: Số lượng top sản phẩm
        by: Tiêu chí sắp xếp ('Sales' hoặc 'Benefit per order')
        
    Returns:
        List các dictionary chứa thông tin sản phẩm
    """
    if by == 'Sales' and 'Sales' not in df.columns:
        return []
    if by == 'Benefit per order' and 'Benefit per order' not in df.columns:
        return []
    
    # Nhóm theo Category Name hoặc Product Name
    group_col = 'Category Name' if 'Category Name' in df.columns else 'Product Name'
    
    if group_col not in df.columns:
        return []
    
    agg_dict = {by: 'sum'}
    if 'Sales' in df.columns and by != 'Sales':
        agg_dict['Sales'] = 'sum'
    if 'Benefit per order' in df.columns and by != 'Benefit per order':
        agg_dict['Benefit per order'] = 'sum'
    
    top_products = df.groupby(group_col).agg(agg_dict).reset_index()
    top_products = top_products.sort_values(by=by, ascending=False).head(top_n)
    
    result = []
    for _, row in top_products.iterrows():
        result.append({
            'category': str(row[group_col]),
            'sales': float(row.get('Sales', 0)),
            'benefit': float(row.get('Benefit per order', 0)),
            'value': float(row[by])
        })
    
    return result


@cached(ttl=1800)  # Cache for 30 minutes
def get_top_countries(df: pd.DataFrame, top_n: int = 10, by: str = 'Sales') -> List[Dict]:
    """
    Lấy top quốc gia theo số đơn hoặc doanh thu.
    
    Args:
        df: DataFrame chuỗi cung ứng
        top_n: Số lượng top quốc gia
        by: Tiêu chí sắp xếp ('Sales', 'Benefit per order', hoặc 'orders')
        
    Returns:
        List các dictionary chứa thông tin quốc gia
    """
    country_col = 'Order Country' if 'Order Country' in df.columns else 'Customer Country'
    
    if country_col not in df.columns:
        return []
    
    agg_dict = {}
    if 'Sales' in df.columns:
        agg_dict['Sales'] = 'sum'
    if 'Benefit per order' in df.columns:
        agg_dict['Benefit per order'] = 'sum'
    if 'Order Id' in df.columns:
        agg_dict['Order Id'] = 'nunique'
    
    top_countries = df.groupby(country_col).agg(agg_dict).reset_index()
    
    if by == 'orders' and 'Order Id' in agg_dict:
        top_countries = top_countries.sort_values(by='Order Id', ascending=False).head(top_n)
        sort_col = 'Order Id'
    elif by in agg_dict:
        top_countries = top_countries.sort_values(by=by, ascending=False).head(top_n)
        sort_col = by
    else:
        return []
    
    result = []
    for _, row in top_countries.iterrows():
        result.append({
            'country': str(row[country_col]),
            'sales': float(row.get('Sales', 0)),
            'benefit': float(row.get('Benefit per order', 0)),
            'orders': int(row.get('Order Id', 0)),
            'value': float(row[sort_col])
        })
    
    return result


@cached(ttl=1800)  # Cache for 30 minutes
def get_time_series_data(df: pd.DataFrame, freq: str = 'M') -> Dict:
    """
    Tổng hợp dữ liệu theo thời gian (theo tháng/quý).
    
    Args:
        df: DataFrame chuỗi cung ứng
        freq: Tần suất ('M' = tháng, 'Q' = quý, 'D' = ngày)
        
    Returns:
        Dictionary chứa dữ liệu time series
    """
    date_col = 'order date (DateOrders)'
    
    if date_col not in df.columns:
        return {}
    
    # Đảm bảo cột ngày là datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df_with_date = df[df[date_col].notna()].copy()
    
    if len(df_with_date) == 0:
        return {}
    
    # Set index là ngày
    df_with_date = df_with_date.set_index(date_col)
    
    # Resample theo tần suất
    time_series = {}
    
    if 'Sales' in df_with_date.columns:
        time_series['sales'] = df_with_date['Sales'].resample(freq).sum().to_dict()
        time_series['sales'] = {str(k): float(v) for k, v in time_series['sales'].items()}
    
    if 'Late_delivery_risk' in df_with_date.columns:
        late_rate = df_with_date['Late_delivery_risk'].resample(freq).apply(
            lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0
        ).to_dict()
        time_series['late_delivery_rate'] = {str(k): float(v) for k, v in late_rate.items()}
    
    if 'Order Id' in df_with_date.columns:
        orders_count = df_with_date['Order Id'].resample(freq).nunique().to_dict()
        time_series['orders_count'] = {str(k): int(v) for k, v in orders_count.items()}
    
    return time_series


def calculate_weather_stats(df: pd.DataFrame) -> Dict:
    """
    Tính thống kê về dữ liệu thời tiết.
    
    Args:
        df: DataFrame thời tiết
        
    Returns:
        Dictionary chứa thống kê thời tiết
    """
    stats = {}
    
    if 'temperature_2m_mean' in df.columns:
        stats['temperature'] = {
            'min': float(df['temperature_2m_mean'].min()),
            'max': float(df['temperature_2m_mean'].max()),
            'mean': float(df['temperature_2m_mean'].mean()),
            'std': float(df['temperature_2m_mean'].std())
        }
    
    if 'precipitation_sum' in df.columns:
        stats['precipitation'] = {
            'min': float(df['precipitation_sum'].min()),
            'max': float(df['precipitation_sum'].max()),
            'mean': float(df['precipitation_sum'].mean()),
            'std': float(df['precipitation_sum'].std())
        }
    
    if 'wind_speed_10m_mean' in df.columns:
        stats['wind_speed'] = {
            'min': float(df['wind_speed_10m_mean'].min()),
            'max': float(df['wind_speed_10m_mean'].max()),
            'mean': float(df['wind_speed_10m_mean'].mean())
        }
    
    if 'relative_humidity_2m_mean' in df.columns:
        stats['humidity'] = {
            'min': float(df['relative_humidity_2m_mean'].min()),
            'max': float(df['relative_humidity_2m_mean'].max()),
            'mean': float(df['relative_humidity_2m_mean'].mean())
        }
    
    return stats


def analyze_weather_delivery_correlation(
    supply_df: pd.DataFrame, 
    weather_df: pd.DataFrame
) -> Dict:
    """
    Phân tích tương quan giữa thời tiết và giao hàng.
    
    Args:
        supply_df: DataFrame chuỗi cung ứng
        weather_df: DataFrame thời tiết
        
    Returns:
        Dictionary chứa kết quả phân tích tương quan
    """
    # Thử join 2 dataset
    # Join theo customer_id và date
    supply_date_col = 'order date (DateOrders)'
    supply_customer_col = 'Order Customer Id'
    
    weather_date_col = 'order_date'
    weather_customer_col = 'customer_id'
    
    if (supply_date_col not in supply_df.columns or 
        supply_customer_col not in supply_df.columns or
        weather_date_col not in weather_df.columns or
        weather_customer_col not in weather_df.columns):
        return {'error': 'Thiếu cột cần thiết để join'}
    
    # Chuẩn hoá ngày
    supply_df[supply_date_col] = pd.to_datetime(supply_df[supply_date_col], errors='coerce')
    weather_df[weather_date_col] = pd.to_datetime(weather_df[weather_date_col], errors='coerce')
    
    # Chỉ lấy ngày (bỏ giờ)
    supply_df['order_date_only'] = supply_df[supply_date_col].dt.date
    weather_df['order_date_only'] = weather_df[weather_date_col].dt.date
    
    # Join
    merged = supply_df.merge(
        weather_df,
        left_on=[supply_customer_col, 'order_date_only'],
        right_on=[weather_customer_col, 'order_date_only'],
        how='inner'
    )
    
    if len(merged) == 0:
        return {'error': 'Không thể join được dữ liệu', 'suggestion': 'Kiểm tra lại format ngày và customer_id'}
    
    correlation_results = {}
    
    # Tương quan giữa nhiệt độ và tỉ lệ giao trễ
    if 'Late_delivery_risk' in merged.columns and 'temperature_2m_mean' in merged.columns:
        corr = merged['Late_delivery_risk'].corr(merged['temperature_2m_mean'])
        correlation_results['temperature_vs_late_delivery'] = float(corr) if not pd.isna(corr) else None
    
    # Tương quan giữa lượng mưa và tỉ lệ giao trễ
    if 'Late_delivery_risk' in merged.columns and 'precipitation_sum' in merged.columns:
        corr = merged['Late_delivery_risk'].corr(merged['precipitation_sum'])
        correlation_results['precipitation_vs_late_delivery'] = float(corr) if not pd.isna(corr) else None
    
    # Tương quan giữa tốc độ gió và tỉ lệ giao trễ
    if 'Late_delivery_risk' in merged.columns and 'wind_speed_10m_mean' in merged.columns:
        corr = merged['Late_delivery_risk'].corr(merged['wind_speed_10m_mean'])
        correlation_results['wind_speed_vs_late_delivery'] = float(corr) if not pd.isna(corr) else None
    
    correlation_results['merged_records'] = len(merged)
    correlation_results['merge_rate'] = float(len(merged) / len(supply_df) * 100) if len(supply_df) > 0 else 0
    
    return correlation_results


def get_sample_orders(df: pd.DataFrame, n: int = 50) -> List[Dict]:
    """
    Lấy mẫu n đơn hàng gần nhất.
    
    Args:
        df: DataFrame chuỗi cung ứng
        n: Số lượng mẫu
        
    Returns:
        List các dictionary chứa thông tin đơn hàng
    """
    date_col = 'order date (DateOrders)'
    
    if date_col not in df.columns:
        # Nếu không có ngày, lấy n dòng đầu
        sample_df = df.head(n)
    else:
        # Sắp xếp theo ngày giảm dần
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        sample_df = df.sort_values(by=date_col, ascending=False).head(n)
    
    # Chọn các cột quan trọng
    columns = ['Order Id', 'Order Country', 'Category Name', 'order date (DateOrders)', 
               'Delivery Status', 'Late_delivery_risk', 'Sales']
    
    available_columns = [col for col in columns if col in sample_df.columns]
    sample_df = sample_df[available_columns]
    
    result = []
    for _, row in sample_df.iterrows():
        record = {}
        for col in available_columns:
            value = row[col]
            if pd.isna(value):
                record[col] = None
            elif isinstance(value, (pd.Timestamp, datetime)):
                record[col] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif col == 'Sales' and pd.notna(value):
                # Đảm bảo Sales là float
                try:
                    record[col] = float(value)
                except (ValueError, TypeError):
                    record[col] = 0.0
            elif col == 'Late_delivery_risk' and pd.notna(value):
                # Đảm bảo Late_delivery_risk là int hoặc string
                try:
                    record[col] = int(value)
                except (ValueError, TypeError):
                    record[col] = str(value)
            else:
                record[col] = str(value)
        result.append(record)
    
    return result


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering: tạo các features mới từ dữ liệu hiện có.
    
    Args:
        df: DataFrame chuỗi cung ứng
        
    Returns:
        DataFrame với các features mới
    """
    df = df.copy()
    
    # Time-based features
    if 'order date (DateOrders)' in df.columns:
        df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
        df['order_year'] = df['order date (DateOrders)'].dt.year
        df['order_month'] = df['order date (DateOrders)'].dt.month
        df['order_quarter'] = df['order date (DateOrders)'].dt.quarter
        df['order_day_of_week'] = df['order date (DateOrders)'].dt.dayofweek
        df['order_is_weekend'] = df['order_day_of_week'].isin([5, 6]).astype(int)
        df['order_day_of_month'] = df['order date (DateOrders)'].dt.day
    
    # Lead time features
    if 'Days for shipment (scheduled)' in df.columns and 'Days for shipping (real)' in df.columns:
        df['lead_time'] = df['Days for shipment (scheduled)'] - df['Days for shipping (real)']
        df['lead_time_positive'] = (df['lead_time'] > 0).astype(int)
        df['lead_time_negative'] = (df['lead_time'] < 0).astype(int)
    
    # Sales features
    if 'Sales' in df.columns:
        df['sales_log'] = np.log1p(df['Sales'])  # Log transform for skewed data
        df['sales_category'] = pd.cut(
            df['Sales'],
            bins=[0, 100, 500, 1000, float('inf')],
            labels=['Low', 'Medium', 'High', 'Very High']
        )
    
    # Profit margin
    if 'Sales' in df.columns and 'Benefit per order' in df.columns:
        df['profit_margin'] = (df['Benefit per order'] / df['Sales'] * 100).fillna(0)
        df['profit_margin_category'] = pd.cut(
            df['profit_margin'],
            bins=[-float('inf'), 0, 10, 20, float('inf')],
            labels=['Loss', 'Low', 'Medium', 'High']
        )
    
    return df


def calculate_advanced_metrics(df: pd.DataFrame) -> Dict:
    """
    Tính toán các metrics nâng cao.
    
    Args:
        df: DataFrame chuỗi cung ứng
        
    Returns:
        Dictionary chứa advanced metrics
    """
    metrics = {}
    
    # Customer metrics
    if 'Customer Id' in df.columns:
        metrics['unique_customers'] = int(df['Customer Id'].nunique())
        metrics['avg_orders_per_customer'] = float(len(df) / df['Customer Id'].nunique()) if df['Customer Id'].nunique() > 0 else 0
    
    # Product metrics
    if 'Category Name' in df.columns:
        metrics['unique_categories'] = int(df['Category Name'].nunique())
        metrics['category_diversity'] = float(df['Category Name'].nunique() / len(df) * 100) if len(df) > 0 else 0
    
    # Time-based metrics
    if 'order date (DateOrders)' in df.columns:
        df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
        date_range = (df['order date (DateOrders)'].max() - df['order date (DateOrders)'].min()).days
        metrics['data_span_days'] = int(date_range) if pd.notna(date_range) else 0
        metrics['avg_orders_per_day'] = float(len(df) / date_range) if date_range > 0 else 0
    
    # Delivery performance
    if 'Days for shipping (real)' in df.columns and 'Days for shipment (scheduled)' in df.columns:
        on_time = (df['Days for shipping (real)'] <= df['Days for shipment (scheduled)']).sum()
        metrics['on_time_delivery_count'] = int(on_time)
        metrics['on_time_delivery_rate'] = float((on_time / len(df) * 100) if len(df) > 0 else 0)
    
    # Revenue concentration (Gini-like)
    if 'Sales' in df.columns:
        sorted_sales = df['Sales'].sort_values(ascending=False)
        cumulative_sales = sorted_sales.cumsum()
        total_sales = sorted_sales.sum()
        if total_sales > 0:
            # Calculate what % of orders account for 80% of sales
            p80_sales = total_sales * 0.8
            p80_orders = (cumulative_sales <= p80_sales).sum()
            metrics['revenue_concentration_p80'] = float((p80_orders / len(df) * 100) if len(df) > 0 else 0)
    
    return metrics


def analyze_seasonality(df: pd.DataFrame) -> Dict:
    """
    Phân tích tính thời vụ trong dữ liệu.
    
    Args:
        df: DataFrame chuỗi cung ứng
        
    Returns:
        Dictionary chứa seasonality analysis
    """
    if 'order date (DateOrders)' not in df.columns:
        return {}
    
    df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
    df_with_date = df[df['order date (DateOrders)'].notna()].copy()
    
    if len(df_with_date) == 0:
        return {}
    
    seasonality = {}
    
    # Monthly seasonality
    if 'Sales' in df_with_date.columns:
        monthly_sales = df_with_date.groupby(df_with_date['order date (DateOrders)'].dt.month)['Sales'].sum()
        seasonality['monthly_sales'] = {int(k): float(v) for k, v in monthly_sales.items()}
        seasonality['best_month'] = int(monthly_sales.idxmax()) if len(monthly_sales) > 0 else None
        seasonality['worst_month'] = int(monthly_sales.idxmin()) if len(monthly_sales) > 0 else None
    
    # Day of week seasonality
    if 'Sales' in df_with_date.columns:
        dow_sales = df_with_date.groupby(df_with_date['order date (DateOrders)'].dt.dayofweek)['Sales'].sum()
        seasonality['day_of_week_sales'] = {int(k): float(v) for k, v in dow_sales.items()}
        seasonality['best_day'] = int(dow_sales.idxmax()) if len(dow_sales) > 0 else None
    
    # Quarterly seasonality
    if 'Sales' in df_with_date.columns:
        quarterly_sales = df_with_date.groupby(df_with_date['order date (DateOrders)'].dt.quarter)['Sales'].sum()
        seasonality['quarterly_sales'] = {int(k): float(v) for k, v in quarterly_sales.items()}
    
    return seasonality

