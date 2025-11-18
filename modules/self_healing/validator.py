"""
Schema Validator: Validate và phát hiện schema mismatch.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np


class SchemaValidator:
    """
    Validate schema và phát hiện missing columns, type mismatches.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Args:
            schema_path: Đường dẫn đến schema file (JSON)
        """
        self.schema_path = schema_path
        self.schema = None
        
        if schema_path and os.path.exists(schema_path):
            self.load_schema(schema_path)
    
    def load_schema(self, schema_path: str):
        """Load schema từ file."""
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def validate(
        self,
        data: pd.DataFrame,
        strict: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate data theo schema.
        
        Args:
            data: DataFrame cần validate
            strict: Nếu True, raise error nếu không match
            
        Returns:
            (is_valid, issues_dict)
        """
        if self.schema is None:
            return True, {}
        
        issues = {
            'missing_columns': [],
            'extra_columns': [],
            'type_mismatches': [],
            'null_violations': []
        }
        
        expected_columns = set(self.schema.get('feature_names', []))
        actual_columns = set(data.columns)
        
        # Missing columns
        missing = expected_columns - actual_columns
        if missing:
            issues['missing_columns'] = list(missing)
        
        # Extra columns (không bắt buộc, chỉ warning)
        extra = actual_columns - expected_columns
        if extra:
            issues['extra_columns'] = list(extra)
        
        # Type mismatches (nếu schema có type info)
        if 'column_types' in self.schema:
            for col, expected_type in self.schema['column_types'].items():
                if col in data.columns:
                    actual_type = str(data[col].dtype)
                    if not self._type_compatible(actual_type, expected_type):
                        issues['type_mismatches'].append({
                            'column': col,
                            'expected': expected_type,
                            'actual': actual_type
                        })
        
        # Null violations (nếu schema có null constraints)
        if 'null_constraints' in self.schema:
            for col, allow_null in self.schema['null_constraints'].items():
                if col in data.columns and not allow_null:
                    null_count = data[col].isnull().sum()
                    if null_count > 0:
                        issues['null_violations'].append({
                            'column': col,
                            'null_count': int(null_count)
                        })
        
        is_valid = (
            len(issues['missing_columns']) == 0 and
            len(issues['type_mismatches']) == 0 and
            len(issues['null_violations']) == 0
        )
        
        if strict and not is_valid:
            raise ValueError(f"Schema validation failed: {issues}")
        
        return is_valid, issues
    
    def _type_compatible(self, actual_type: str, expected_type: str) -> bool:
        """Kiểm tra type có compatible không."""
        # Simple type checking
        numeric_types = ['int', 'float', 'int64', 'float64']
        if expected_type in numeric_types:
            return any(t in actual_type.lower() for t in numeric_types)
        
        if expected_type == 'object' or expected_type == 'str':
            return 'object' in actual_type.lower() or 'str' in actual_type.lower()
        
        return actual_type.lower() == expected_type.lower()
    
    def suggest_fixes(self, issues: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Đề xuất cách sửa issues."""
        fixes = []
        
        # Fix missing columns
        for col in issues.get('missing_columns', []):
            fixes.append({
                'issue': f'Missing column: {col}',
                'fix': f'Add column {col} with default value (0 for numeric, "Unknown" for categorical)',
                'action': 'add_column',
                'column': col
            })
        
        # Fix type mismatches
        for mismatch in issues.get('type_mismatches', []):
            fixes.append({
                'issue': f'Type mismatch: {mismatch["column"]}',
                'fix': f'Convert {mismatch["column"]} from {mismatch["actual"]} to {mismatch["expected"]}',
                'action': 'convert_type',
                'column': mismatch['column'],
                'target_type': mismatch['expected']
            })
        
        # Fix null violations
        for violation in issues.get('null_violations', []):
            fixes.append({
                'issue': f'Null values in {violation["column"]}',
                'fix': f'Fill null values in {violation["column"]} (median for numeric, mode for categorical)',
                'action': 'fill_null',
                'column': violation['column']
            })
        
        return fixes

