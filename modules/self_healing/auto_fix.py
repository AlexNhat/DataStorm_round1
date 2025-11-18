"""
Auto Fix: Tự động sửa lỗi schema, preprocessing, feature engineering.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json
import os

from .validator import SchemaValidator


class AutoPreprocessor:
    """
    Tự động tạo preprocessor cho data mới.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema_validator = SchemaValidator(schema_path)
        self.preprocessor_config = {}
    
    def auto_preprocess(
        self,
        data: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Tự động preprocess data.
        
        Args:
            data: Raw DataFrame
            target_column: Target column (nếu có)
            
        Returns:
            Preprocessed DataFrame
        """
        df = data.copy()
        
        # 1. Validate schema
        is_valid, issues = self.schema_validator.validate(df, strict=False)
        
        # 2. Fix missing columns
        if issues.get('missing_columns'):
            df = self._fix_missing_columns(df, issues['missing_columns'])
        
        # 3. Fix type mismatches
        if issues.get('type_mismatches'):
            df = self._fix_type_mismatches(df, issues['type_mismatches'])
        
        # 4. Fix null values
        if issues.get('null_violations'):
            df = self._fix_null_values(df, issues['null_violations'])
        
        # 5. Handle extra columns (drop hoặc keep)
        if issues.get('extra_columns'):
            # Giữ lại extra columns (có thể là features mới)
            pass
        
        return df
    
    def _fix_missing_columns(self, df: pd.DataFrame, missing_cols: List[str]) -> pd.DataFrame:
        """Thêm missing columns với default values."""
        for col in missing_cols:
            # Kiểm tra xem có phải numeric không (dựa vào tên)
            if any(keyword in col.lower() for keyword in ['count', 'amount', 'price', 'value', 'num', 'id']):
                df[col] = 0.0
            else:
                df[col] = "Unknown"
        
        return df
    
    def _fix_type_mismatches(self, df: pd.DataFrame, mismatches: List[Dict]) -> pd.DataFrame:
        """Sửa type mismatches."""
        for mismatch in mismatches:
            col = mismatch['column']
            target_type = mismatch['expected']
            
            try:
                if 'int' in target_type.lower():
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                elif 'float' in target_type.lower():
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
                elif 'str' in target_type.lower() or 'object' in target_type.lower():
                    df[col] = df[col].astype(str)
            except Exception as e:
                print(f"Warning: Could not convert {col} to {target_type}: {e}")
        
        return df
    
    def _fix_null_values(self, df: pd.DataFrame, violations: List[Dict]) -> pd.DataFrame:
        """Sửa null values."""
        for violation in violations:
            col = violation['column']
            
            if df[col].dtype in ['int64', 'float64']:
                # Numeric: fill với median
                df[col] = df[col].fillna(df[col].median())
            else:
                # Categorical: fill với mode
                mode_value = df[col].mode()[0] if len(df[col].mode()) > 0 else "Unknown"
                df[col] = df[col].fillna(mode_value)
        
        return df


class FeatureEngineeringAdapter:
    """
    Điều chỉnh feature engineering khi data thay đổi.
    """
    
    def __init__(self):
        self.feature_config = {}
    
    def adapt_features(
        self,
        data: pd.DataFrame,
        feature_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Adapt features dựa trên config.
        
        Args:
            data: DataFrame
            feature_config: Config cho feature engineering
            
        Returns:
            DataFrame với features đã adapt
        """
        df = data.copy()
        
        # 1. Time features
        if feature_config.get('create_time_features', False):
            df = self._create_time_features(df, feature_config.get('date_column'))
        
        # 2. Lag features
        if feature_config.get('create_lag_features', False):
            df = self._create_lag_features(df, feature_config.get('lag_config', {}))
        
        # 3. Rolling features
        if feature_config.get('create_rolling_features', False):
            df = self._create_rolling_features(df, feature_config.get('rolling_config', {}))
        
        # 4. Categorical encoding
        if feature_config.get('encode_categorical', False):
            df = self._encode_categorical(df, feature_config.get('categorical_columns', []))
        
        return df
    
    def _create_time_features(self, df: pd.DataFrame, date_column: Optional[str]) -> pd.DataFrame:
        """Tạo time features."""
        if date_column and date_column in df.columns:
            try:
                df[date_column] = pd.to_datetime(df[date_column])
                df['year'] = df[date_column].dt.year
                df['month'] = df[date_column].dt.month
                df['day'] = df[date_column].dt.day
                df['day_of_week'] = df[date_column].dt.dayofweek
                df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            except Exception as e:
                print(f"Warning: Could not create time features: {e}")
        
        return df
    
    def _create_lag_features(self, df: pd.DataFrame, lag_config: Dict) -> pd.DataFrame:
        """Tạo lag features."""
        target_col = lag_config.get('target_column')
        lags = lag_config.get('lags', [1, 2, 3])
        
        if target_col and target_col in df.columns:
            for lag in lags:
                df[f'{target_col}_lag{lag}'] = df[target_col].shift(lag)
        
        return df
    
    def _create_rolling_features(self, df: pd.DataFrame, rolling_config: Dict) -> pd.DataFrame:
        """Tạo rolling features."""
        target_col = rolling_config.get('target_column')
        windows = rolling_config.get('windows', [7, 30])
        
        if target_col and target_col in df.columns:
            for window in windows:
                df[f'{target_col}_ma{window}'] = df[target_col].rolling(window=window).mean()
                df[f'{target_col}_std{window}'] = df[target_col].rolling(window=window).std()
        
        return df
    
    def _encode_categorical(self, df: pd.DataFrame, categorical_columns: List[str]) -> pd.DataFrame:
        """Encode categorical columns."""
        for col in categorical_columns:
            if col in df.columns:
                # One-hot encoding cho top categories
                top_categories = df[col].value_counts().head(10).index.tolist()
                for cat in top_categories:
                    df[f'{col}_{cat}'] = (df[col] == cat).astype(int)
        
        return df


class PipelineRepairer:
    """
    Sửa lỗi pipeline tự động.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema_validator = SchemaValidator(schema_path)
        self.auto_preprocessor = AutoPreprocessor(schema_path)
        self.feature_adapter = FeatureEngineeringAdapter()
    
    def repair_pipeline(
        self,
        data: pd.DataFrame,
        feature_config: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Sửa pipeline tự động.
        
        Returns:
            (repaired_data, repair_log)
        """
        repair_log = {
            'issues_found': [],
            'fixes_applied': [],
            'warnings': []
        }
        
        # 1. Validate
        is_valid, issues = self.schema_validator.validate(data, strict=False)
        repair_log['issues_found'] = issues
        
        # 2. Auto preprocess
        repaired_data = self.auto_preprocessor.auto_preprocess(data)
        
        # 3. Adapt features
        if feature_config:
            repaired_data = self.feature_adapter.adapt_features(repaired_data, feature_config)
        
        # 4. Log fixes
        if issues.get('missing_columns'):
            repair_log['fixes_applied'].append(f"Added {len(issues['missing_columns'])} missing columns")
        
        if issues.get('type_mismatches'):
            repair_log['fixes_applied'].append(f"Fixed {len(issues['type_mismatches'])} type mismatches")
        
        if issues.get('null_violations'):
            repair_log['fixes_applied'].append(f"Fixed {len(issues['null_violations'])} null violations")
        
        return repaired_data, repair_log

