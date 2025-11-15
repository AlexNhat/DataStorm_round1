"""
Preprocessing và xây dựng Feature Store cho 3 models:
1. Logistics Delay Prediction
2. Revenue Forecast
3. Customer Churn

Tuân thủ best practices: time-based split, no leakage, RFM, weather features, etc.
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from math import radians, cos, sin, asin, sqrt
import warnings
warnings.filterwarnings('ignore')

# Thêm thư mục app vào path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from app.services.data_loader import load_supply_chain_data, load_weather_data

# Đường dẫn
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'features')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Tạo thư mục nếu chưa có
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách Haversine giữa 2 điểm (km).
    """
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return np.nan
    
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def calculate_rfm_features(df: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    """
    Tính RFM (Recency, Frequency, Monetary) features cho từng customer.
    
    Args:
        df: DataFrame với orders
        snapshot_date: Ngày snapshot để tính RFM
        
    Returns:
        DataFrame với RFM features
    """
    # Chỉ lấy orders trước snapshot_date (tránh leakage)
    df_past = df[df['order date (DateOrders)'] < snapshot_date].copy()
    
    if len(df_past) == 0:
        return pd.DataFrame()
    
    # Recency: Số ngày từ lần mua cuối đến snapshot
    recency = df_past.groupby('Order Customer Id')['order date (DateOrders)'].max()
    recency = (snapshot_date - recency).dt.days
    
    # Frequency: Số đơn hàng
    frequency = df_past.groupby('Order Customer Id')['Order Id'].nunique()
    
    # Monetary: Tổng giá trị
    monetary = df_past.groupby('Order Customer Id')['Sales'].sum()
    
    # Combine
    rfm = pd.DataFrame({
        'customer_id': recency.index,
        'rfm_recency': recency.values,
        'rfm_frequency': frequency.values,
        'rfm_monetary': monetary.values
    })
    
    # RFM Scores (1-5 scale)
    try:
        rfm['rfm_recency_score'] = pd.qcut(rfm['rfm_recency'], q=5, labels=[5,4,3,2,1], duplicates='drop')
    except:
        rfm['rfm_recency_score'] = 3  # Default
    
    try:
        rfm['rfm_frequency_score'] = pd.qcut(rfm['rfm_frequency'].rank(method='first'), q=5, labels=[1,2,3,4,5], duplicates='drop')
    except:
        rfm['rfm_frequency_score'] = 3  # Default
    
    try:
        rfm['rfm_monetary_score'] = pd.qcut(rfm['rfm_monetary'].rank(method='first'), q=5, labels=[1,2,3,4,5], duplicates='drop')
    except:
        rfm['rfm_monetary_score'] = 3  # Default
    
    # Convert to numeric
    rfm['rfm_recency_score'] = pd.to_numeric(rfm['rfm_recency_score'], errors='coerce').fillna(3)
    rfm['rfm_frequency_score'] = pd.to_numeric(rfm['rfm_frequency_score'], errors='coerce').fillna(3)
    rfm['rfm_monetary_score'] = pd.to_numeric(rfm['rfm_monetary_score'], errors='coerce').fillna(3)
    
    # RFM Segment
    rfm['rfm_score'] = rfm['rfm_recency_score'].astype(int) + rfm['rfm_frequency_score'].astype(int) + rfm['rfm_monetary_score'].astype(int)
    
    try:
        rfm['rfm_segment'] = pd.cut(rfm['rfm_score'], bins=[0, 6, 9, 12, 15], labels=['Low', 'Medium', 'High', 'VIP'])
        rfm['rfm_segment'] = rfm['rfm_segment'].astype(str)
    except:
        rfm['rfm_segment'] = 'Medium'  # Default
    
    return rfm


def add_time_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Thêm các time-based features.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['quarter'] = df[date_col].dt.quarter
    df['week'] = df[date_col].dt.isocalendar().week
    df['day_of_week'] = df[date_col].dt.dayofweek
    df['day_of_month'] = df[date_col].dt.day
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_month_start'] = (df['day_of_month'] <= 3).astype(int)
    df['is_month_end'] = (df['day_of_month'] >= 28).astype(int)
    
    # Seasonality (sin/cos encoding)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    # Holiday flags (simplified - có thể mở rộng)
    # Giả định: tháng 12 (holiday season), tháng 1 (New Year)
    df['is_holiday_season'] = df['month'].isin([12, 1]).astype(int)
    
    return df


def calculate_weather_risk_level(row: pd.Series) -> int:
    """
    Tính weather risk level (1-5) dựa trên các yếu tố thời tiết.
    """
    risk = 1  # Low risk
    
    # Precipitation risk
    if pd.notna(row.get('precipitation_sum')):
        if row['precipitation_sum'] > 50:
            risk += 2
        elif row['precipitation_sum'] > 20:
            risk += 1
    
    # Wind speed risk
    if pd.notna(row.get('wind_speed_10m_mean')):
        if row['wind_speed_10m_mean'] > 20:
            risk += 2
        elif row['wind_speed_10m_mean'] > 15:
            risk += 1
    
    # Temperature extreme risk
    if pd.notna(row.get('temperature_2m_mean')):
        if row['temperature_2m_mean'] < -10 or row['temperature_2m_mean'] > 40:
            risk += 1
    
    return min(risk, 5)  # Cap at 5


def build_logistics_delay_features(supply_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Xây dựng features cho logistics delay prediction.
    Mỗi row = 1 order item/shipment.
    """
    print("🔨 Building logistics delay features...")
    
    df = supply_df.copy()
    
    # Merge với weather data
    supply_date_col = 'order date (DateOrders)'
    supply_customer_col = 'Order Customer Id'
    weather_date_col = 'order_date'
    weather_customer_col = 'customer_id'
    
    if (supply_date_col in df.columns and weather_date_col in weather_df.columns):
        df[supply_date_col] = pd.to_datetime(df[supply_date_col], errors='coerce')
        weather_df[weather_date_col] = pd.to_datetime(weather_df[weather_date_col], errors='coerce')
        
        df['order_date_only'] = df[supply_date_col].dt.date
        weather_df['order_date_only'] = weather_df[weather_date_col].dt.date
        
        # Merge
        if supply_customer_col in df.columns and weather_customer_col in weather_df.columns:
            df = df.merge(
                weather_df,
                left_on=[supply_customer_col, 'order_date_only'],
                right_on=[weather_customer_col, 'order_date_only'],
                how='left'
            )
    
    # Time features
    df = add_time_features(df, supply_date_col)
    
    # Shipping duration features
    if 'Days for shipping (real)' in df.columns and 'Days for shipment (scheduled)' in df.columns:
        df['shipping_duration_real'] = df['Days for shipping (real)']
        df['shipping_duration_scheduled'] = df['Days for shipment (scheduled)']
        df['shipping_duration_diff'] = df['shipping_duration_real'] - df['shipping_duration_scheduled']
        df['is_late'] = (df['shipping_duration_diff'] > 0).astype(int)
        df['is_early'] = (df['shipping_duration_diff'] < 0).astype(int)
    
    # Weather risk
    df['weather_risk_level'] = df.apply(calculate_weather_risk_level, axis=1)
    
    # Distance features (nếu có lat/lon)
    if 'lat' in df.columns and 'lon' in df.columns:
        # Giả định có customer location và order location
        # Simplified: sử dụng weather lat/lon
        pass
    
    # Product/Category features
    if 'Category Name' in df.columns:
        category_counts = df['Category Name'].value_counts()
        df['category_popularity'] = df['Category Name'].map(category_counts)
    
    # Shipping mode features
    if 'Shipping Mode' in df.columns:
        shipping_mode_encoded = pd.get_dummies(df['Shipping Mode'], prefix='shipping_mode')
        df = pd.concat([df, shipping_mode_encoded], axis=1)
    
    # Rolling window features (7-day, 30-day)
    if supply_date_col in df.columns:
        df = df.sort_values(supply_date_col)
        
        # 7-day rolling average sales
        df['sales_7d_avg'] = df.groupby('Order Country')['Sales'].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        
        # 30-day rolling average sales
        df['sales_30d_avg'] = df.groupby('Order Country')['Sales'].transform(
            lambda x: x.rolling(window=30, min_periods=1).mean()
        )
        
        # 7-day order count
        df['order_count_7d'] = df.groupby('Order Country')[supply_date_col].transform(
            lambda x: x.rolling(window=7, min_periods=1).count()
        )
    
    # Target: late_delivery_risk hoặc is_late
    if 'Late_delivery_risk' in df.columns:
        df['target_late_delivery'] = df['Late_delivery_risk'].fillna(0).astype(int)
    elif 'is_late' in df.columns:
        df['target_late_delivery'] = df['is_late']
    else:
        df['target_late_delivery'] = 0
    
    # Select features
    feature_cols = [
        'Order Id', 'Order Customer Id', 'order date (DateOrders)',
        'target_late_delivery',
        # Time features
        'year', 'month', 'quarter', 'week', 'day_of_week', 'day_of_month',
        'is_weekend', 'is_month_start', 'is_month_end',
        'month_sin', 'month_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_holiday_season',
        # Shipping features
        'shipping_duration_real', 'shipping_duration_scheduled', 'shipping_duration_diff',
        'is_late', 'is_early',
        # Weather features
        'temperature_2m_mean', 'precipitation_sum', 'wind_speed_10m_mean',
        'relative_humidity_2m_mean', 'weather_risk_level',
        # Product features
        'Category Name', 'category_popularity',
        # Sales features
        'Sales', 'sales_7d_avg', 'sales_30d_avg', 'order_count_7d',
        # Location
        'Order Country', 'Order City'
    ]
    
    # Add shipping mode dummies
    shipping_mode_cols = [col for col in df.columns if col.startswith('shipping_mode_')]
    feature_cols.extend(shipping_mode_cols)
    
    # Select available columns
    available_cols = [col for col in feature_cols if col in df.columns]
    features_df = df[available_cols].copy()
    
    print(f"[OK] Logistics delay features: {len(features_df)} rows, {len(available_cols)} features")
    
    return features_df


def build_revenue_forecast_features(supply_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Xây dựng features cho revenue forecast.
    Mỗi row = 1 time-step (ngày/tuần/tháng) x region x category.
    """
    print("🔨 Building revenue forecast features...")
    
    df = supply_df.copy()
    
    # Time features
    if 'order date (DateOrders)' in df.columns:
        df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
        df = add_time_features(df, 'order date (DateOrders)')
    
    # Aggregate theo ngày + region + category
    agg_dict = {
        'Sales': 'sum',
        'Order Id': 'nunique',
        'Order Customer Id': 'nunique'
    }
    
    group_cols = ['year', 'month', 'day_of_week', 'Order Country', 'Category Name']
    available_group_cols = [col for col in group_cols if col in df.columns]
    
    if len(available_group_cols) > 0:
        forecast_df = df.groupby(available_group_cols + ['order date (DateOrders)']).agg(agg_dict).reset_index()
        forecast_df.columns = [col if col != 'Order Id' else 'order_count' 
                               for col in forecast_df.columns]
        forecast_df.columns = [col if col != 'Order Customer Id' else 'customer_count' 
                               for col in forecast_df.columns]
    else:
        # Fallback: aggregate theo ngày
        forecast_df = df.groupby('order date (DateOrders)').agg(agg_dict).reset_index()
        forecast_df['Order Country'] = 'All'
        forecast_df['Category Name'] = 'All'
    
    # Rename Sales to target
    forecast_df['target_revenue'] = forecast_df['Sales']
    
    # Time-based lag features (7-day, 30-day)
    forecast_df = forecast_df.sort_values('order date (DateOrders)')
    
    for lag in [1, 7, 30]:
        forecast_df[f'revenue_lag_{lag}d'] = forecast_df.groupby(['Order Country', 'Category Name'])['target_revenue'].shift(lag)
        forecast_df[f'order_count_lag_{lag}d'] = forecast_df.groupby(['Order Country', 'Category Name'])['order_count'].shift(lag)
    
    # Rolling statistics
    forecast_df['revenue_7d_avg'] = forecast_df.groupby(['Order Country', 'Category Name'])['target_revenue'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    forecast_df['revenue_30d_avg'] = forecast_df.groupby(['Order Country', 'Category Name'])['target_revenue'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    forecast_df['revenue_7d_std'] = forecast_df.groupby(['Order Country', 'Category Name'])['target_revenue'].transform(
        lambda x: x.rolling(window=7, min_periods=1).std()
    )
    
    # Merge với weather (aggregate weather theo ngày + country)
    if 'order_date' in weather_df.columns and 'country' in weather_df.columns:
        weather_df['order_date'] = pd.to_datetime(weather_df['order_date'], errors='coerce')
        weather_agg = weather_df.groupby(['order_date', 'country']).agg({
            'temperature_2m_mean': 'mean',
            'precipitation_sum': 'sum',
            'wind_speed_10m_mean': 'mean',
            'relative_humidity_2m_mean': 'mean'
        }).reset_index()
        
        forecast_df = forecast_df.merge(
            weather_agg,
            left_on=['order date (DateOrders)', 'Order Country'],
            right_on=['order_date', 'country'],
            how='left'
        )
    
    # Time features
    forecast_df = add_time_features(forecast_df, 'order date (DateOrders)')
    
    print(f"[OK] Revenue forecast features: {len(forecast_df)} rows")
    
    return forecast_df


def build_churn_features(supply_df: pd.DataFrame, snapshot_dates: List[pd.Timestamp] = None) -> pd.DataFrame:
    """
    Xây dựng features cho customer churn prediction.
    Mỗi row = 1 customer tại 1 snapshot_date.
    
    Churn definition: Recency > 180 days (không mua trong 180 ngày).
    """
    print("🔨 Building churn features...")
    
    df = supply_df.copy()
    
    if 'order date (DateOrders)' not in df.columns or 'Order Customer Id' not in df.columns:
        print("⚠️ Missing required columns for churn features")
        return pd.DataFrame()
    
    df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
    
    # Default snapshot dates: mỗi tháng
    if snapshot_dates is None:
        min_date = df['order date (DateOrders)'].min()
        max_date = df['order date (DateOrders)'].max()
        snapshot_dates = pd.date_range(start=min_date, end=max_date, freq='M')
    
    churn_features_list = []
    
    for snapshot_date in snapshot_dates:
        # Tính RFM tại snapshot_date
        rfm = calculate_rfm_features(df, snapshot_date)
        
        if len(rfm) == 0:
            continue
        
        # Customer history features (tính đến snapshot_date)
        df_past = df[df['order date (DateOrders)'] < snapshot_date].copy()
        
        customer_stats = df_past.groupby('Order Customer Id').agg({
            'Order Id': 'nunique',
            'Sales': ['sum', 'mean', 'std'],
            'Benefit per order': 'mean',
            'Category Name': lambda x: x.nunique(),  # Category diversity
            'Order Country': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown'  # Most frequent country
        }).reset_index()
        
        customer_stats.columns = ['customer_id', 'total_orders', 'total_sales', 'avg_order_value', 
                                  'sales_std', 'avg_profit', 'category_diversity', 'preferred_country']
        
        # Time since first order
        first_order = df_past.groupby('Order Customer Id')['order date (DateOrders)'].min()
        customer_stats['days_since_first_order'] = customer_stats['customer_id'].apply(
            lambda x: (snapshot_date - first_order[x]).days if x in first_order.index else np.nan
        )
        
        # Merge RFM với customer stats
        churn_df = rfm.merge(customer_stats, on='customer_id', how='left')
        
        # Churn label: Recency > 180 days
        churn_df['target_churn'] = (churn_df['rfm_recency'] > 180).astype(int)
        
        # Snapshot date
        churn_df['snapshot_date'] = snapshot_date
        
        churn_features_list.append(churn_df)
    
    if len(churn_features_list) == 0:
        return pd.DataFrame()
    
    churn_features = pd.concat(churn_features_list, ignore_index=True)
    
    # Fill missing values
    numeric_cols = churn_features.select_dtypes(include=[np.number]).columns
    churn_features[numeric_cols] = churn_features[numeric_cols].fillna(0)
    
    print(f"[OK] Churn features: {len(churn_features)} rows")
    
    return churn_features


def main():
    """
    Main function: Load data, build features, save to parquet.
    """
    print("=" * 60)
    print("FEATURE STORE BUILDER")
    print("=" * 60)
    
    # Load data
    print("\n[INFO] Loading data...")
    supply_df = load_supply_chain_data(normalize=True)
    weather_df = load_weather_data()
    
    print(f"[OK] Supply chain data: {len(supply_df)} rows")
    print(f"[OK] Weather data: {len(weather_df)} rows")
    
    # Build features
    print("\n[INFO] Building features...")
    
    # 1. Logistics delay features
    logistics_features = build_logistics_delay_features(supply_df, weather_df)
    logistics_path = os.path.join(OUTPUT_DIR, 'features_logistics.parquet')
    logistics_features.to_parquet(logistics_path, index=False)
    print(f"[OK] Saved: {logistics_path}")
    
    # 2. Revenue forecast features
    forecast_features = build_revenue_forecast_features(supply_df, weather_df)
    forecast_path = os.path.join(OUTPUT_DIR, 'features_forecast.parquet')
    forecast_features.to_parquet(forecast_path, index=False)
    print(f"[OK] Saved: {forecast_path}")
    
    # 3. Churn features
    churn_features = build_churn_features(supply_df)
    churn_path = os.path.join(OUTPUT_DIR, 'features_churn.parquet')
    churn_features.to_parquet(churn_path, index=False)
    print(f"[OK] Saved: {churn_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("FEATURE STORE SUMMARY")
    print("=" * 60)
    print(f"Logistics features: {len(logistics_features)} rows, {len(logistics_features.columns)} columns")
    print(f"Forecast features: {len(forecast_features)} rows, {len(forecast_features.columns)} columns")
    print(f"Churn features: {len(churn_features)} rows, {len(churn_features.columns)} columns")
    print("\n[INFO] Feature store built successfully!")


if __name__ == "__main__":
    main()

