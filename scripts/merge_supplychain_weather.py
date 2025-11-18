"""
Script để gộp và chuẩn hóa 2 dataset: Supply Chain + Weather
Tạo merged dataset sạch, chuẩn hóa để dùng cho các ML models.

Output:
- data/merged_supply_weather.parquet
- data/merged_supply_weather_clean.parquet
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Thêm thư mục app vào path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from app.services.data_loader import load_supply_chain_data, load_weather_data
from app.services.data_normalizer import normalize_country, normalize_date, COUNTRY_MAPPING

# Đường dẫn
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def normalize_date_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """Chuẩn hóa cột ngày về format YYYY-MM-DD."""
    if col_name not in df.columns:
        return df
    
    df[col_name] = pd.to_datetime(df[col_name], errors='coerce', infer_datetime_format=True)
    # Tạo cột date normalized (chỉ ngày, không giờ)
    df[f'{col_name}_norm'] = df[col_name].dt.date
    return df


def normalize_location_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa các cột địa lý (country, city)."""
    df = df.copy()
    
    # Chuẩn hóa country
    country_cols = [col for col in df.columns if 'country' in col.lower()]
    for col in country_cols:
        if col in df.columns:
            df[col] = df[col].apply(normalize_country)
            df[f'{col}_norm'] = df[col].str.strip().str.lower()
    
    # Chuẩn hóa city
    city_cols = [col for col in df.columns if 'city' in col.lower()]
    for col in city_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown').astype(str).str.strip()
            df[f'{col}_norm'] = df[col].str.lower()
    
    return df


def create_join_keys(df: pd.DataFrame, is_supply: bool = True) -> pd.DataFrame:
    """Tạo các key để join."""
    df = df.copy()
    
    if is_supply:
        # Key 1: Customer ID + Date
        df['join_key_customer_date'] = (
            df['Order Customer Id'].astype(str) + '_' + 
            df['order date (DateOrders)_norm'].astype(str)
        )
        
        # Key 2: Country + City + Date (fallback)
        df['join_key_location_date'] = (
            df.get('Order Country_norm', '') + '_' +
            df.get('Order City_norm', '') + '_' +
            df['order date (DateOrders)_norm'].astype(str)
        )
    else:
        # Weather data
        if 'customer_id' in df.columns:
            df['join_key_customer_date'] = (
                df['customer_id'].astype(str) + '_' +
                df['order_date_norm'].astype(str)
            )
        else:
            df['join_key_customer_date'] = None
        
        # Key 2: Country + City + Date
        df['join_key_location_date'] = (
            df.get('country_norm', '') + '_' +
            df.get('city_norm', '') + '_' +
            df['order_date_norm'].astype(str)
        )
    
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Xử lý missing values theo chiến lược."""
    df = df.copy()
    
    # Numeric columns - fill với 0 hoặc median
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if 'Sales' in col or 'Benefit' in col or 'profit' in col.lower():
            df[col] = df[col].fillna(0)
        elif 'temperature' in col.lower() or 'precipitation' in col.lower() or 'wind' in col.lower():
            # Weather: fill với median
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna(df[col].median())
    
    # Categorical - fill với "Unknown"
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if col.endswith('_norm') or 'key' in col.lower():
            continue
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna('Unknown')
    
    return df


def detect_and_handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Phát hiện và xử lý outliers."""
    df = df.copy()
    
    # Chỉ xử lý các cột quan trọng
    outlier_cols = ['Sales', 'Benefit per order', 'Days for shipping (real)', 
                    'Days for shipment (scheduled)']
    
    for col in outlier_cols:
        if col not in df.columns:
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Tạo flag
        df[f'{col}_is_outlier'] = (df[col] < lower_bound) | (df[col] > upper_bound)
        
        # Cap extreme values (giữ lại nhưng cap)
        df[col] = df[col].clip(lower=max(0, lower_bound), upper=upper_bound)
    
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Thêm các feature về thời gian."""
    df = df.copy()
    
    date_col = 'order date (DateOrders)'
    if date_col not in df.columns:
        return df
    
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['day'] = df[date_col].dt.day
    df['day_of_week'] = df[date_col].dt.dayofweek  # 0=Monday
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['quarter'] = df[date_col].dt.quarter
    df['week_of_year'] = df[date_col].dt.isocalendar().week
    
    # Cyclical encoding cho month và day_of_week
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    # Holiday season (simplified - có thể cải thiện)
    df['is_holiday_season'] = df['month'].isin([11, 12]).astype(int)  # Nov-Dec
    
    return df


def calculate_weather_risk_level(row: pd.Series) -> int:
    """Tính weather risk level từ các chỉ số thời tiết."""
    risk = 1  # Default low risk
    
    # Precipitation risk
    precip = row.get('precipitation_sum', 0) or 0
    if precip > 50:
        risk += 2
    elif precip > 20:
        risk += 1
    
    # Wind risk
    wind = row.get('wind_speed_10m_mean', 0) or 0
    if wind > 20:
        risk += 2
    elif wind > 10:
        risk += 1
    
    # Temperature extreme risk
    temp_max = row.get('temperature_2m_max', 0) or 0
    temp_min = row.get('temperature_2m_min', 0) or 0
    if temp_max > 40 or temp_min < -10:
        risk += 1
    
    return min(risk, 5)  # Cap at 5


def calculate_lead_time(df: pd.DataFrame) -> pd.DataFrame:
    """Tính lead_time = scheduled - real."""
    df = df.copy()
    
    real_col = 'Days for shipping (real)'
    scheduled_col = 'Days for shipment (scheduled)'
    
    if real_col in df.columns and scheduled_col in df.columns:
        df['lead_time'] = df[scheduled_col] - df[real_col]
        df['lead_time'] = df['lead_time'].fillna(0)
    
    return df


def hash_sensitive_data(df: pd.DataFrame) -> pd.DataFrame:
    """Hash hoặc loại bỏ dữ liệu nhạy cảm."""
    df = df.copy()
    
    import hashlib
    
    # Hash email nếu có
    if 'Customer Email' in df.columns:
        df['Customer Email'] = df['Customer Email'].apply(
            lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:16] 
            if pd.notna(x) and str(x) != 'nan' else None
        )
    
    # Loại bỏ password
    if 'Customer Password' in df.columns:
        df = df.drop(columns=['Customer Password'])
    
    return df


def merge_datasets(supply_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """Gộp 2 dataset với nhiều chiến lược join."""
    print("\n=== MERGING DATASETS ===")
    
    # Strategy 1: Join theo Customer ID + Date
    merged = supply_df.merge(
        weather_df,
        left_on='join_key_customer_date',
        right_on='join_key_customer_date',
        how='left',
        suffixes=('', '_weather')
    )
    
    print(f"✓ Join theo Customer ID + Date: {merged['join_key_customer_date'].notna().sum():,} matches")
    
    # Strategy 2: Fill missing với Location + Date
    missing_mask = merged['join_key_customer_date'].isna()
    if missing_mask.sum() > 0:
        print(f"  → Còn {missing_mask.sum():,} records chưa match, thử join theo Location + Date...")
        
        # Join theo location cho các record chưa match
        location_merge = supply_df[missing_mask].merge(
            weather_df,
            left_on='join_key_location_date',
            right_on='join_key_location_date',
            how='left',
            suffixes=('', '_weather_loc')
        )
        
        # Update các cột weather từ location merge
        weather_cols = [col for col in weather_df.columns if col not in ['join_key_customer_date', 'join_key_location_date']]
        for col in weather_cols:
            if f'{col}_weather' in location_merge.columns:
                merged.loc[missing_mask, f'{col}_weather'] = location_merge[f'{col}_weather'].values
        
        print(f"  → Thêm {location_merge[weather_cols[0] if weather_cols else 'lat'].notna().sum():,} matches từ Location + Date")
    
    return merged


def main():
    """Main function."""
    print("=" * 60)
    print("MERGE SUPPLY CHAIN + WEATHER DATASETS")
    print("=" * 60)
    
    # 1. Load data
    print("\n[1/7] Loading datasets...")
    supply_df = load_supply_chain_data()
    weather_df = load_weather_data()
    
    print(f"✓ Supply Chain: {len(supply_df):,} records")
    print(f"✓ Weather: {len(weather_df):,} records")
    
    # 2. Normalize dates
    print("\n[2/7] Normalizing dates...")
    supply_df = normalize_date_column(supply_df, 'order date (DateOrders)')
    if 'shipping date (DateOrders)' in supply_df.columns:
        supply_df = normalize_date_column(supply_df, 'shipping date (DateOrders)')
    
    weather_df = normalize_date_column(weather_df, 'order_date')
    
    # 3. Normalize locations
    print("\n[3/7] Normalizing locations...")
    supply_df = normalize_location_columns(supply_df)
    weather_df = normalize_location_columns(weather_df)
    
    # 4. Create join keys
    print("\n[4/7] Creating join keys...")
    supply_df = create_join_keys(supply_df, is_supply=True)
    weather_df = create_join_keys(weather_df, is_supply=False)
    
    # 5. Merge datasets
    print("\n[5/7] Merging datasets...")
    merged_df = merge_datasets(supply_df, weather_df)
    
    # Calculate join statistics
    total_supply = len(supply_df)
    matched = merged_df['lat'].notna().sum() if 'lat' in merged_df.columns else 0
    match_rate = (matched / total_supply * 100) if total_supply > 0 else 0
    
    print(f"\n📊 JOIN STATISTICS:")
    print(f"  Total Supply Chain records: {total_supply:,}")
    print(f"  Matched with Weather: {matched:,}")
    print(f"  Match rate: {match_rate:.2f}%")
    
    # Save intermediate merged file
    output_file = os.path.join(DATA_DIR, 'merged_supply_weather.parquet')
    merged_df.to_parquet(output_file, index=False, engine='pyarrow')
    print(f"\n✓ Saved: {output_file}")
    
    # 6. Clean and enhance
    print("\n[6/7] Cleaning and enhancing data...")
    
    # Handle missing values
    merged_df = handle_missing_values(merged_df)
    
    # Detect outliers
    merged_df = detect_and_handle_outliers(merged_df)
    
    # Add time features
    merged_df = add_time_features(merged_df)
    
    # Calculate lead time
    merged_df = calculate_lead_time(merged_df)
    
    # Calculate weather risk
    if 'precipitation_sum' in merged_df.columns:
        merged_df['weather_risk_level'] = merged_df.apply(calculate_weather_risk_level, axis=1)
    
    # Hash sensitive data
    merged_df = hash_sensitive_data(merged_df)
    
    # 7. Save clean dataset
    print("\n[7/7] Saving clean dataset...")
    clean_output_file = os.path.join(DATA_DIR, 'merged_supply_weather_clean.parquet')
    merged_df.to_parquet(clean_output_file, index=False, engine='pyarrow')
    
    print(f"\n✅ SUCCESS!")
    print(f"  ✓ Merged dataset: {output_file}")
    print(f"  ✓ Clean dataset: {clean_output_file}")
    print(f"  ✓ Total records: {len(merged_df):,}")
    print(f"  ✓ Total columns: {len(merged_df.columns)}")
    print(f"\n📊 Final Statistics:")
    print(f"  - Records with weather data: {merged_df['lat'].notna().sum() if 'lat' in merged_df.columns else 0:,}")
    print(f"  - Records with late delivery risk: {merged_df['Late_delivery_risk'].sum() if 'Late_delivery_risk' in merged_df.columns else 0:,}")
    print(f"  - Date range: {merged_df['order date (DateOrders)'].min()} to {merged_df['order date (DateOrders)'].max()}")


if __name__ == '__main__':
    main()

