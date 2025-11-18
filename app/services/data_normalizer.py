"""
Module chuẩn hóa dữ liệu: country names, dates, và các giá trị khác.
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime


# Country name mapping
COUNTRY_MAPPING = {
    'EE. UU.': 'United States',
    'U.S.A': 'United States',
    'USA': 'United States',
    'US': 'United States',
    'United States of America': 'United States',
    'UK': 'United Kingdom',
    'U.K.': 'United Kingdom',
    'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
    'Vietnam': 'Viet Nam',
    'Viet Nam': 'Viet Nam',
    'VN': 'Viet Nam',
}


def normalize_country(country_name: str) -> str:
    """
    Chuẩn hóa tên quốc gia.
    
    Args:
        country_name: Tên quốc gia cần chuẩn hóa
        
    Returns:
        Tên quốc gia đã chuẩn hóa
    """
    if not country_name or pd.isna(country_name):
        return 'Unknown'
    
    country_name = str(country_name).strip()
    
    # Check mapping
    if country_name in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[country_name]
    
    return country_name


def normalize_date(date_value) -> Optional[datetime]:
    """
    Chuẩn hóa ngày về datetime object.
    
    Args:
        date_value: Giá trị ngày (string, datetime, etc.)
        
    Returns:
        datetime object hoặc None
    """
    if pd.isna(date_value):
        return None
    
    try:
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()
        
        # Try to parse
        dt = pd.to_datetime(date_value, errors='coerce', infer_datetime_format=True)
        if pd.notna(dt):
            return dt.to_pydatetime()
        
        return None
    except:
        return None


def normalize_dataframe(df: pd.DataFrame, normalize_countries: bool = True) -> pd.DataFrame:
    """
    Chuẩn hóa toàn bộ DataFrame.
    
    Args:
        df: DataFrame cần chuẩn hóa
        normalize_countries: Có chuẩn hóa tên quốc gia không
        
    Returns:
        DataFrame đã được chuẩn hóa
    """
    df = df.copy()
    
    # Normalize country columns
    if normalize_countries:
        country_columns = ['Order Country', 'Customer Country']
        for col in country_columns:
            if col in df.columns:
                df[col] = df[col].apply(normalize_country)
    
    # Normalize date columns
    date_columns = [col for col in df.columns if 'date' in col.lower()]
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].apply(normalize_date)
    
    # Normalize numeric columns (remove negative values where not allowed)
    if 'Sales' in df.columns:
        df['Sales'] = df['Sales'].clip(lower=0)
    
    if 'Benefit per order' in df.columns:
        # Allow negative (losses are valid)
        pass
    
    return df


def validate_dataframe(df: pd.DataFrame) -> Dict:
    """
    Validate DataFrame và trả về báo cáo.
    
    Args:
        df: DataFrame cần validate
        
    Returns:
        Dictionary chứa validation results
    """
    validation_report = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }
    
    # Check required columns
    required_columns = ['Order Id', 'Sales', 'order date (DateOrders)']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation_report['is_valid'] = False
        validation_report['errors'].append(f"Missing required columns: {missing_columns}")
    
    # Check for negative sales (should not happen)
    if 'Sales' in df.columns:
        negative_sales = (df['Sales'] < 0).sum()
        if negative_sales > 0:
            validation_report['warnings'].append(f"Found {negative_sales} records with negative sales")
    
    # Check date validity
    if 'order date (DateOrders)' in df.columns:
        invalid_dates = df['order date (DateOrders)'].isna().sum()
        if invalid_dates > 0:
            validation_report['warnings'].append(f"Found {invalid_dates} records with invalid dates")
    
    # Statistics
    validation_report['stats'] = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_values': df.isnull().sum().to_dict()
    }
    
    return validation_report

