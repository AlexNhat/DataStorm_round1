"""
Module để phân tích chất lượng dữ liệu và tạo báo cáo.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


def detect_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> Dict:
    """
    Phát hiện outliers trong một cột.
    
    Args:
        df: DataFrame
        column: Tên cột cần kiểm tra
        method: Phương pháp ('iqr' hoặc 'zscore')
        
    Returns:
        Dictionary chứa thông tin outliers
    """
    if column not in df.columns:
        return {'error': f'Cột {column} không tồn tại'}
    
    series = df[column].dropna()
    
    if len(series) == 0:
        return {'error': 'Không có dữ liệu'}
    
    outliers_info = {
        'column': column,
        'method': method,
        'total_values': len(series),
        'outliers_count': 0,
        'outliers_percentage': 0,
        'outliers_examples': []
    }
    
    if method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        outliers_info['outliers_count'] = len(outliers)
        outliers_info['outliers_percentage'] = (len(outliers) / len(series) * 100) if len(series) > 0 else 0
        outliers_info['bounds'] = {'lower': float(lower_bound), 'upper': float(upper_bound)}
        
        if len(outliers) > 0:
            outliers_info['outliers_examples'] = outliers.head(10).tolist()
    
    elif method == 'zscore':
        z_scores = np.abs((series - series.mean()) / series.std())
        outliers = series[z_scores > 3]
        outliers_info['outliers_count'] = len(outliers)
        outliers_info['outliers_percentage'] = (len(outliers) / len(series) * 100) if len(series) > 0 else 0
        
        if len(outliers) > 0:
            outliers_info['outliers_examples'] = outliers.head(10).tolist()
    
    return outliers_info


def check_data_quality(df: pd.DataFrame, name: str = "Dataset") -> Dict:
    """
    Kiểm tra chất lượng dữ liệu tổng thể.
    
    Args:
        df: DataFrame cần kiểm tra
        name: Tên dataset
        
    Returns:
        Dictionary chứa báo cáo chất lượng
    """
    quality_report = {
        'dataset_name': name,
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_data': {},
        'duplicate_rows': int(df.duplicated().sum()),
        'data_types': {},
        'sensitive_columns': [],
        'format_issues': []
    }
    
    # Kiểm tra missing values
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    
    for col in df.columns:
        if missing[col] > 0:
            quality_report['missing_data'][col] = {
                'count': int(missing[col]),
                'percentage': float(missing_pct[col])
            }
    
    # Kiểm tra kiểu dữ liệu
    for col in df.columns:
        quality_report['data_types'][col] = str(df[col].dtype)
    
    # Tìm các cột nhạy cảm
    sensitive_keywords = ['password', 'email', 'credit', 'card', 'ssn', 'phone', 'address']
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in sensitive_keywords):
            quality_report['sensitive_columns'].append(col)
    
    # Kiểm tra format ngày tháng
    date_columns = [col for col in df.columns if 'date' in col.lower()]
    for col in date_columns:
        # Thử parse ngày
        try:
            parsed = pd.to_datetime(df[col], errors='coerce')
            invalid_count = parsed.isna().sum()
            if invalid_count > 0:
                quality_report['format_issues'].append({
                    'column': col,
                    'issue': 'invalid_date_format',
                    'count': int(invalid_count),
                    'percentage': float((invalid_count / len(df) * 100))
                })
        except:
            quality_report['format_issues'].append({
                'column': col,
                'issue': 'cannot_parse_dates',
                'count': len(df)
            })
    
    # Kiểm tra giá trị không nhất quán (ví dụ: country names)
    if 'Order Country' in df.columns:
        countries = df['Order Country'].dropna().unique()
        quality_report['country_variations'] = {
            'unique_count': len(countries),
            'examples': list(countries[:20])
        }
    
    if 'Customer Country' in df.columns:
        customer_countries = df['Customer Country'].dropna().unique()
        quality_report['customer_country_variations'] = {
            'unique_count': len(customer_countries),
            'examples': list(customer_countries[:20])
        }
    
    return quality_report

