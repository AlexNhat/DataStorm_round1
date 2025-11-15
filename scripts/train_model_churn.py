"""
Training script cho Customer Churn Prediction Model (Classification).

Target: target_churn (Recency > 180 days)
Models: Logistic Regression, XGBoost
Evaluation: AUC, F1, Precision@TopK
"""

import pandas as pd
import numpy as np
import os
import sys
import json
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    classification_report, precision_recall_curve
)
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Đường dẫn
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'features')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

os.makedirs(MODELS_DIR, exist_ok=True)


def to_serializable(value):
    """Recursively convert numpy/pandas objects to built-in Python types for JSON."""
    if isinstance(value, dict):
        return {k: to_serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_serializable(v) for v in value]
    if isinstance(value, tuple):
        return [to_serializable(v) for v in value]
    if isinstance(value, set):
        return [to_serializable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def precision_at_topk(y_true, y_pred_proba, k: int = 100):
    """
    Calculate precision at top-K predictions.
    """
    # Get top-K indices by probability
    top_k_indices = np.argsort(y_pred_proba)[-k:]
    top_k_true = y_true[top_k_indices]
    return top_k_true.sum() / k if k > 0 else 0.0


def load_features():
    """Load churn features."""
    features_path = os.path.join(DATA_DIR, 'features_churn.parquet')
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}. Run preprocess_and_build_feature_store.py first.")
    
    df = pd.read_parquet(features_path)
    print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def prepare_features(df: pd.DataFrame):
    """
    Prepare features for training.
    - Time-based split (by snapshot_date)
    - Handle missing values
    - Encode categorical variables
    """
    df = df.copy()
    
    # Drop rows with missing target
    df = df[df['target_churn'].notna()].copy()
    
    # Time-based split: Use 80% for train, 20% for test (by snapshot_date)
    if 'snapshot_date' in df.columns:
        df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], errors='coerce')
        df = df.sort_values('snapshot_date')
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()
    else:
        # Fallback: random split
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['target_churn'])
    
    print(f"Train: {len(train_df)} rows, Test: {len(test_df)} rows")
    print(f"Train churn rate: {train_df['target_churn'].mean():.2%}")
    print(f"Test churn rate: {test_df['target_churn'].mean():.2%}")
    
    # Feature columns (exclude IDs, dates, target)
    exclude_cols = ['customer_id', 'snapshot_date', 'target_churn', 
                    'preferred_country', 'rfm_segment']
    
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
    y_train = train_df['target_churn'].values
    X_test = test_df[numeric_feature_cols].values
    y_test = test_df['target_churn'].values
    
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


def train_logistic_regression(X_train, y_train, X_test, y_test):
    """Train Logistic Regression model."""
    print("\n📊 Training Logistic Regression...")
    
    # Handle class imbalance
    from sklearn.utils.class_weight import compute_class_weight
    classes = np.unique(y_train)
    class_weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weight_dict = dict(zip(classes, class_weights))
    
    model = LogisticRegression(
        max_iter=1000,
        class_weight=class_weight_dict,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Evaluation
    auc = roc_auc_score(y_test, y_pred_proba)
    pr_auc = average_precision_score(y_test, y_pred_proba)
    f1 = f1_score(y_test, y_pred)
    precision_top100 = precision_at_topk(y_test, y_pred_proba, k=100)
    precision_top1000 = precision_at_topk(y_test, y_pred_proba, k=1000)
    
    print(f"  AUC: {auc:.4f}")
    print(f"  PR-AUC: {pr_auc:.4f}")
    print(f"  F1: {f1:.4f}")
    print(f"  Precision@Top100: {precision_top100:.4f}")
    print(f"  Precision@Top1000: {precision_top1000:.4f}")
    
    return model, {
        'auc': float(auc),
        'pr_auc': float(pr_auc),
        'f1': float(f1),
        'precision_top100': float(precision_top100),
        'precision_top1000': float(precision_top1000),
        'y_pred': y_pred.tolist(),
        'y_pred_proba': y_pred_proba.tolist()
    }


def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost model."""
    print("\n📊 Training XGBoost...")
    
    # Handle class imbalance
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum() if (y_train == 1).sum() > 0 else 1.0
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='auc'
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Evaluation
    auc = roc_auc_score(y_test, y_pred_proba)
    pr_auc = average_precision_score(y_test, y_pred_proba)
    f1 = f1_score(y_test, y_pred)
    precision_top100 = precision_at_topk(y_test, y_pred_proba, k=100)
    precision_top1000 = precision_at_topk(y_test, y_pred_proba, k=1000)
    
    print(f"  AUC: {auc:.4f}")
    print(f"  PR-AUC: {pr_auc:.4f}")
    print(f"  F1: {f1:.4f}")
    print(f"  Precision@Top100: {precision_top100:.4f}")
    print(f"  Precision@Top1000: {precision_top1000:.4f}")
    
    # Feature importance
    feature_importance = dict(zip(range(len(model.feature_names_in_)), model.feature_importances_))
    
    return model, {
        'auc': float(auc),
        'pr_auc': float(pr_auc),
        'f1': float(f1),
        'precision_top100': float(precision_top100),
        'precision_top1000': float(precision_top1000),
        'y_pred': y_pred.tolist(),
        'y_pred_proba': y_pred_proba.tolist(),
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
        json.dump(to_serializable(feature_schema), f, indent=2)
    
    with open(metrics_path, 'w') as f:
        json.dump(to_serializable(metrics), f, indent=2)
    
    print(f"✓ Saved model: {model_path}")
    print(f"✓ Saved preprocessor: {preprocessor_path}")
    print(f"✓ Saved schema: {schema_path}")
    print(f"✓ Saved metrics: {metrics_path}")


def main():
    """Main training function."""
    print("=" * 60)
    print("CUSTOMER CHURN PREDICTION MODEL TRAINING")
    print("=" * 60)
    
    # Load features
    df = load_features()
    
    # Prepare features
    data = prepare_features(df)
    
    # Train models
    print("\n" + "=" * 60)
    print("MODEL TRAINING")
    print("=" * 60)
    
    # Logistic Regression
    lr_model, lr_metrics = train_logistic_regression(
        data['X_train'], data['y_train'],
        data['X_test'], data['y_test']
    )
    
    # XGBoost
    xgb_model, xgb_metrics = train_xgboost(
        data['X_train'], data['y_train'],
        data['X_test'], data['y_test']
    )
    
    # Choose best model (based on AUC)
    if xgb_metrics['auc'] > lr_metrics['auc']:
        best_model = xgb_model
        best_metrics = xgb_metrics
        model_type = 'xgboost'
        print(f"\n✅ Best model: XGBoost (AUC: {xgb_metrics['auc']:.4f})")
    else:
        best_model = lr_model
        best_metrics = lr_metrics
        model_type = 'logistic_regression'
        print(f"\n✅ Best model: Logistic Regression (AUC: {lr_metrics['auc']:.4f})")
    
    # Classification report
    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(data['y_test'], best_metrics['y_pred']))
    
    # Save best model
    preprocessor = {
        'scaler': data['scaler'],
        'label_encoders': data['label_encoders'],
        'feature_names': data['feature_names']
    }
    
    feature_schema = {
        'feature_names': data['feature_names'],
        'model_type': model_type,
        'target': 'target_churn',
        'churn_definition': 'Recency > 180 days',
        'created_at': datetime.now().isoformat()
    }
    
    save_model(
        best_model,
        preprocessor,
        feature_schema,
        'churn',
        best_metrics
    )
    
    print("\n✅ Training completed!")


if __name__ == "__main__":
    main()
