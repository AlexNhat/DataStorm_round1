"""
Module để đọc và xử lý dữ liệu từ các file CSV.
Xử lý encoding, chuyển đổi kiểu dữ liệu, và chuẩn hoá format.
"""

import pandas as pd
import os
from typing import Tuple, Optional
from datetime import datetime
from app.services.data_normalizer import normalize_dataframe, validate_dataframe
from app.services.cache_manager import cached


# Đường dẫn file dữ liệu
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
SUPPLY_CHAIN_FILE = os.path.join(DATA_DIR, 'DataCoSupplyChainDataset.csv')
WEATHER_FILE = os.path.join(DATA_DIR, 'geocoded_weather.csv')


@cached(ttl=7200)  # Cache for 2 hours
def load_supply_chain_data(file_path: Optional[str] = None, normalize: bool = True) -> pd.DataFrame:
    """
    Đọc file CSV chuỗi cung ứng với encoding phù hợp.
    
    Args:
        file_path: Đường dẫn file, mặc định dùng SUPPLY_CHAIN_FILE
        
    Returns:
        DataFrame đã được xử lý cơ bản
    """
    if file_path is None:
        file_path = SUPPLY_CHAIN_FILE
    
    # Thử các encoding phổ biến
    encodings = ['latin-1', 'utf-8', 'iso-8859-1', 'cp1252']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
            print(f"✓ Đọc thành công với encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise ValueError(f"Không thể đọc file {file_path} với các encoding đã thử")
    
    # Chuyển đổi cột ngày tháng
    date_columns = ['order date (DateOrders)', 'shipping date (DateOrders)']
    for col in date_columns:
        if col in df.columns:
            # Thử nhiều format ngày khác nhau
            df[col] = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
    
    # Chuyển đổi các cột số
    numeric_columns = [
        'Days for shipping (real)',
        'Days for shipment (scheduled)',
        'Benefit per order',
        'Sales per customer',
        'Late_delivery_risk',
        'Category Id',
        'Customer Id',
        'Order Id',
        'Order Item Quantity',
        'Order Item Discount',
        'Order Item Discount Rate',
        'Order Item Profit Ratio',
        'Order Item Total',
        'Sales',
        'Order Profit Per Order',
        'Order Item Product Price',
        'Product Price'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Normalize data
    if normalize:
        df = normalize_dataframe(df, normalize_countries=True)
    
    # Validate data
    validation = validate_dataframe(df)
    if not validation['is_valid']:
        print(f"⚠️ Warning: Data validation issues: {validation['errors']}")
    if validation['warnings']:
        print(f"⚠️ Warnings: {validation['warnings']}")
    
    return df


@cached(ttl=7200)  # Cache for 2 hours
def load_weather_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Đọc file CSV dữ liệu thời tiết.
    
    Args:
        file_path: Đường dẫn file, mặc định dùng WEATHER_FILE
        
    Returns:
        DataFrame đã được xử lý cơ bản
    """
    if file_path is None:
        file_path = WEATHER_FILE
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
        print(f"✓ Đọc thành công file thời tiết")
    except Exception as e:
        # Thử encoding khác nếu cần
        try:
            df = pd.read_csv(file_path, encoding='latin-1', low_memory=False)
            print(f"✓ Đọc thành công file thời tiết với encoding latin-1")
        except:
            raise ValueError(f"Không thể đọc file {file_path}: {e}")
    
    # Chuyển đổi cột ngày
    if 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    
    # Chuyển đổi các cột số thời tiết
    weather_numeric_columns = [
        'lat', 'lon',
        'temperature_2m_mean',
        'temperature_2m_max',
        'temperature_2m_min',
        'relative_humidity_2m_mean',
        'wind_speed_10m_mean',
        'precipitation_sum',
        'apparent_temperature_mean',
        'dew_point_2m_mean',
        'sunshine_duration',
        'snowfall_sum',
        'precipitation_hours',
        'shortwave_radiation_sum',
        'wind_direction_10m_dominant',
        'weather_code'
    ]
    
    for col in weather_numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def get_data_summary(df: pd.DataFrame, name: str = "Dataset") -> dict:
    """
    Lấy thông tin tổng quan về dataset.
    
    Args:
        df: DataFrame cần phân tích
        name: Tên dataset
        
    Returns:
        Dictionary chứa thông tin tổng quan
    """
    summary = {
        'name': name,
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
        'dtypes': df.dtypes.astype(str).to_dict()
    }
    
    return summary


def suggest_join_keys(supply_df: pd.DataFrame, weather_df: pd.DataFrame) -> dict:
    """
    Phân tích và đề xuất cách join 2 dataset.
    
    Args:
        supply_df: DataFrame chuỗi cung ứng
        weather_df: DataFrame thời tiết
        
    Returns:
        Dictionary chứa thông tin về cách join
    """
    suggestions = {
        'possible_joins': [],
        'recommended_join': None,
        'mapping_needed': []
    }
    
    # Kiểm tra các cột có thể join
    supply_date_col = 'order date (DateOrders)'
    supply_country_col = 'Order Country'
    supply_city_col = 'Order City'
    supply_customer_id_col = 'Order Customer Id'
    
    weather_date_col = 'order_date'
    weather_country_col = 'country'
    weather_city_col = 'city'
    weather_customer_id_col = 'customer_id'
    
    # Join theo (Customer Id, Date)
    if (supply_customer_id_col in supply_df.columns and 
        weather_customer_id_col in weather_df.columns and
        supply_date_col in supply_df.columns and
        weather_date_col in weather_df.columns):
        suggestions['possible_joins'].append({
            'method': 'customer_id_and_date',
            'keys': {
                'supply': [supply_customer_id_col, supply_date_col],
                'weather': [weather_customer_id_col, weather_date_col]
            },
            'description': 'Join theo Customer ID và ngày đơn hàng'
        })
    
    # Join theo (Country, City, Date)
    if (supply_country_col in supply_df.columns and
        supply_city_col in supply_df.columns and
        weather_country_col in weather_df.columns and
        weather_city_col in weather_df.columns):
        suggestions['possible_joins'].append({
            'method': 'location_and_date',
            'keys': {
                'supply': [supply_country_col, supply_city_col, supply_date_col],
                'weather': [weather_country_col, weather_city_col, weather_date_col]
            },
            'description': 'Join theo Quốc gia, Thành phố và ngày đơn hàng'
        })
    
    # Đề xuất join tốt nhất
    if suggestions['possible_joins']:
        # Ưu tiên join theo customer_id vì chính xác hơn
        for join in suggestions['possible_joins']:
            if join['method'] == 'customer_id_and_date':
                suggestions['recommended_join'] = join
                break
        
        # Nếu không có customer_id, dùng location
        if suggestions['recommended_join'] is None:
            suggestions['recommended_join'] = suggestions['possible_joins'][0]
    
    # Kiểm tra cần mapping gì
    if supply_country_col in supply_df.columns and weather_country_col in weather_df.columns:
        supply_countries = set(supply_df[supply_country_col].dropna().astype(str).str.strip().unique())
        weather_countries = set(weather_df[weather_country_col].dropna().astype(str).str.strip().unique())
        
        if supply_countries != weather_countries:
            suggestions['mapping_needed'].append({
                'type': 'country_normalization',
                'description': 'Cần chuẩn hoá tên quốc gia (ví dụ: "EE. UU." vs "United States")',
                'supply_unique': len(supply_countries),
                'weather_unique': len(weather_countries),
                'overlap': len(supply_countries & weather_countries)
            })
    
    return suggestions

