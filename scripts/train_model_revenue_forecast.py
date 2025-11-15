"""
Training script cho Revenue Forecast Model (Regression/Time Series).

Target: target_revenue (doanh thu kỳ tiếp theo)
Models: XGBoost Regressor, Random Forest Regressor
Evaluation: MAPE, RMSE, MAE
"""

import pandas as pd
import numpy as np
import os
import sys
import json
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Đường dẫn
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'features')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

os.makedirs(MODELS_DIR, exist_ok=True)


def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error."""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def load_features():
    """Load revenue forecast features."""
    features_path = os.path.join(DATA_DIR, 'features_forecast.parquet')
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}. Run preprocess_and_build_feature_store.py first.")
    
    df = pd.read_parquet(features_path)
    print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def prepare_features(df: pd.DataFrame):
    """
    Prepare features for training.
    - Time-based split (train đến T, test T+1..T+k)
    - Handle missing values
    - Encode categorical variables
    """
    df = df.copy()
    
    # Drop rows with missing target
    df = df[df['target_revenue'].notna()].copy()
    df = df[df['target_revenue'] > 0].copy()  # Remove zero/negative revenue
    
    # Time-based split: Use 80% for train, 20% for test (by date)
    if 'order date (DateOrders)' in df.columns:
        df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
        df = df.sort_values('order date (DateOrders)')
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()
    else:
        # Fallback: random split
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    print(f"Train: {len(train_df)} rows, Test: {len(test_df)} rows")
    
    # Feature columns (exclude IDs, dates, target)
    exclude_cols = ['order date (DateOrders)', 'target_revenue', 
                    'Order Country', 'Category Name', 'order_date', 'country']
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Handle categorical columns
    categorical_cols = []
    for col in feature_cols:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            categorical_cols.append(col)
    
    # Encode categoricals
    label_encoders = {}
    for col in categorical_cols:
        if col in train_df.columns:
            le = LabelEncoder()
            train_df[col + '_encoded'] = le.fit_transform(train_df[col].astype(str).fillna('Unknown'))
            test_df[col + '_encoded'] = le.transform(test_df[col].astype(str).fillna('Unknown'))
            label_encoders[col] = le
            feature_cols.remove(col)
            feature_cols.append(col + '_encoded')
    
    # Select numeric features only
    numeric_feature_cols = [col for col in feature_cols if col in train_df.columns and train_df[col].dtype in [np.int64, np.float64]]
    
    # Fill missing values
    train_df[numeric_feature_cols] = train_df[numeric_feature_cols].fillna(0)
    test_df[numeric_feature_cols] = test_df[numeric_feature_cols].fillna(0)
    
    # Prepare X, y
    X_train = train_df[numeric_feature_cols].values
    y_train = train_df['target_revenue'].values
    X_test = test_df[numeric_feature_cols].values
    y_test = test_df['target_revenue'].values
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return {
        'X_train': X_train_scaled,
        'X_test': X_test_scaled,
        'y_train': y_train,
        'y_test': y_test,
        'feature_names': numeric_feature_cols,
        'scaler': scaler,
        'label_encoders': label_encoders
    }


def train_random_forest(X_train, y_train, X_test, y_test):
    """Train Random Forest Regressor."""
    print("\n📊 Training Random Forest Regressor...")
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Evaluation
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = calculate_mape(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"  MAE: ${mae:,.2f}")
    print(f"  RMSE: ${rmse:,.2f}")
    print(f"  MAPE: {mape:.2f}%")
    print(f"  R²: {r2:.4f}")
    
    return model, {
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape),
        'r2': float(r2),
        'y_pred': y_pred.tolist()
    }


def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost Regressor."""
    print("\n📊 Training XGBoost Regressor...")
    
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='rmse'
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Evaluation
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = calculate_mape(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"  MAE: ${mae:,.2f}")
    print(f"  RMSE: ${rmse:,.2f}")
    print(f"  MAPE: {mape:.2f}%")
    print(f"  R²: {r2:.4f}")
    
    # Feature importance
    feature_importance = dict(zip(range(len(model.feature_names_in_)), model.feature_importances_))
    
    return model, {
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape),
        'r2': float(r2),
        'y_pred': y_pred.tolist(),
        'feature_importance': feature_importance
    }


def save_model(model, preprocessor, feature_schema, model_name: str, metrics: dict):
    """Save model, preprocessor, and schema."""
    model_path = os.path.join(MODELS_DIR, f'{model_name}_model.pkl')
    preprocessor_path = os.path.join(MODELS_DIR, f'{model_name}_preprocessor.pkl')
    schema_path = os.path.join(MODELS_DIR, f'{model_name}_feature_schema.json')
    metrics_path = os.path.join(MODELS_DIR, f'{model_name}_metrics.json')
    
    joblib.dump(model, model_path)
    joblib.dump(preprocessor, preprocessor_path)
    
    with open(schema_path, 'w') as f:
        json.dump(feature_schema, f, indent=2)
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✓ Saved model: {model_path}")
    print(f"✓ Saved preprocessor: {preprocessor_path}")
    print(f"✓ Saved schema: {schema_path}")
    print(f"✓ Saved metrics: {metrics_path}")


def main():
    """Main training function."""
    print("=" * 60)
    print("REVENUE FORECAST MODEL TRAINING")
    print("=" * 60)
    
    # Load features
    df = load_features()
    
    # Prepare features
    data = prepare_features(df)
    
    # Train models
    print("\n" + "=" * 60)
    print("MODEL TRAINING")
    print("=" * 60)
    
    # Random Forest
    rf_model, rf_metrics = train_random_forest(
        data['X_train'], data['y_train'],
        data['X_test'], data['y_test']
    )
    
    # XGBoost
    xgb_model, xgb_metrics = train_xgboost(
        data['X_train'], data['y_train'],
        data['X_test'], data['y_test']
    )
    
    # Choose best model (based on RMSE)
    if xgb_metrics['rmse'] < rf_metrics['rmse']:
        best_model = xgb_model
        best_metrics = xgb_metrics
        model_type = 'xgboost'
        print(f"\n✅ Best model: XGBoost (RMSE: ${xgb_metrics['rmse']:,.2f})")
    else:
        best_model = rf_model
        best_metrics = rf_metrics
        model_type = 'random_forest'
        print(f"\n✅ Best model: Random Forest (RMSE: ${rf_metrics['rmse']:,.2f})")
    
    # Save best model
    preprocessor = {
        'scaler': data['scaler'],
        'label_encoders': data['label_encoders'],
        'feature_names': data['feature_names']
    }
    
    feature_schema = {
        'feature_names': data['feature_names'],
        'model_type': model_type,
        'target': 'target_revenue',
        'created_at': datetime.now().isoformat()
    }
    
    save_model(
        best_model,
        preprocessor,
        feature_schema,
        'revenue_forecast',
        best_metrics
    )
    
    print("\n✅ Training completed!")


if __name__ == "__main__":
    main()

