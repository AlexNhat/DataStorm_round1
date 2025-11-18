"""
MODEL 1: LATE DELIVERY PREDICTION
Notebook script để dự đoán Late_delivery_risk

Chạy: python notebooks/model_late_delivery.py
Hoặc convert sang .ipynb để chạy trong Jupyter
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, 
    roc_curve, f1_score, accuracy_score
)
import xgboost as xgb
import os
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("=" * 60)
print("MODEL 1: LATE DELIVERY PREDICTION")
print("=" * 60)

# ============================================================================
# 1. LOAD DATA
# ============================================================================
print("\n[1/7] Loading data...")
data_path = os.path.join('..', 'data', 'merged_supply_weather_clean.parquet')

if not os.path.exists(data_path):
    print(f"⚠️ File not found: {data_path}")
    print("Please run: python scripts/merge_supplychain_weather.py first")
    exit(1)

df = pd.read_parquet(data_path)
print(f"✓ Loaded {len(df):,} records")
print(f"✓ Columns: {len(df.columns)}")

# ============================================================================
# 2. EDA
# ============================================================================
print("\n[2/7] Exploratory Data Analysis...")

# Target distribution
if 'Late_delivery_risk' in df.columns:
    target_dist = df['Late_delivery_risk'].value_counts()
    print(f"\nTarget Distribution:")
    print(target_dist)
    print(f"Late delivery rate: {df['Late_delivery_risk'].mean()*100:.2f}%")
    
    # Visualize
    plt.figure(figsize=(8, 5))
    target_dist.plot(kind='bar', color=['green', 'red'])
    plt.title('Late Delivery Risk Distribution')
    plt.xlabel('Late Delivery Risk')
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('../docs/images/late_delivery_dist.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved: docs/images/late_delivery_dist.png")

# Weather correlation
if 'weather_risk_level' in df.columns and 'Late_delivery_risk' in df.columns:
    weather_corr = df.groupby('weather_risk_level')['Late_delivery_risk'].mean()
    
    plt.figure(figsize=(10, 6))
    weather_corr.plot(kind='bar', color='coral')
    plt.title('Late Delivery Rate by Weather Risk Level')
    plt.xlabel('Weather Risk Level')
    plt.ylabel('Late Delivery Rate')
    plt.xticks(rotation=0)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('../docs/images/weather_late_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved: docs/images/weather_late_correlation.png")
    
    print("\nLate Delivery Rate by Weather Risk:")
    print(weather_corr)

# ============================================================================
# 3. FEATURE ENGINEERING
# ============================================================================
print("\n[3/7] Feature Engineering...")

feature_groups = {
    'time_features': ['year', 'month', 'day_of_week', 'is_weekend', 'is_holiday_season', 
                      'month_sin', 'month_cos', 'day_of_week_sin', 'day_of_week_cos'],
    'shipping_features': ['Days for shipping (real)', 'Days for shipment (scheduled)', 
                          'lead_time', 'Shipping Mode'],
    'location_features': ['Order Country', 'Order City'],
    'product_features': ['Category Name', 'Order Item Quantity', 'Order Item Discount'],
    'weather_features': ['temperature_2m_mean', 'precipitation_sum', 'wind_speed_10m_mean',
                        'relative_humidity_2m_mean', 'weather_risk_level'],
    'sales_features': ['Sales', 'Benefit per order']
}

# Collect all available features
all_features = []
for group, features in feature_groups.items():
    available = [f for f in features if f in df.columns]
    all_features.extend(available)
    print(f"✓ {group}: {len(available)}/{len(features)} features available")

print(f"\nTotal features to use: {len(all_features)}")

# Prepare feature matrix
X = df[all_features].copy()
y = df['Late_delivery_risk'].copy() if 'Late_delivery_risk' in df.columns else None

# Handle missing values
X = X.fillna(X.median(numeric_only=True))
for col in X.select_dtypes(include=['object']).columns:
    X[col] = X[col].fillna('Unknown')

print(f"Feature matrix shape: {X.shape}")

# Encode categorical variables
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()

X_encoded = X[numeric_cols].copy()

for col in categorical_cols:
    top_cats = X[col].value_counts().head(10).index.tolist()
    for cat in top_cats:
        X_encoded[f'{col}_{cat}'] = (X[col] == cat).astype(int)
    X_encoded[f'{col}_Other'] = (~X[col].isin(top_cats)).astype(int)

print(f"Encoded feature matrix shape: {X_encoded.shape}")

# ============================================================================
# 4. TRAIN/TEST SPLIT (TIME-BASED)
# ============================================================================
print("\n[4/7] Train/Test Split (Time-based)...")

if 'order date (DateOrders)' in df.columns:
    df_sorted = df.sort_values('order date (DateOrders)')
    split_idx = int(len(df_sorted) * 0.8)
    
    train_mask = df_sorted.index[:split_idx]
    test_mask = df_sorted.index[split_idx:]
    
    X_train = X_encoded.loc[train_mask]
    X_test = X_encoded.loc[test_mask]
    y_train = y.loc[train_mask] if y is not None else None
    y_test = y.loc[test_mask] if y is not None else None
    
    print(f"Train set: {len(X_train):,} samples")
    print(f"Test set: {len(X_test):,} samples")
else:
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42, stratify=y
    )
    print("⚠️ Using random split (date column not found)")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 5. MODEL TRAINING
# ============================================================================
print("\n[5/7] Training Models...")

models = {}
predictions = {}
probabilities = {}

# 5.1. Logistic Regression
print("\n--- Logistic Regression ---")
lr_model = LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')
lr_model.fit(X_train_scaled, y_train)
y_pred_lr = lr_model.predict(X_test_scaled)
y_pred_proba_lr = lr_model.predict_proba(X_test_scaled)[:, 1]

models['Logistic Regression'] = lr_model
predictions['Logistic Regression'] = y_pred_lr
probabilities['Logistic Regression'] = y_pred_proba_lr

print(f"Accuracy: {accuracy_score(y_test, y_pred_lr):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_lr):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_lr):.4f}")

# 5.2. Random Forest
print("\n--- Random Forest ---")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

models['Random Forest'] = rf_model
predictions['Random Forest'] = y_pred_rf
probabilities['Random Forest'] = y_pred_proba_rf

print(f"Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_rf):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_rf):.4f}")

# 5.3. XGBoost
print("\n--- XGBoost ---")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum() if y_train.sum() > 0 else 1
xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    scale_pos_weight=scale_pos_weight
)
xgb_model.fit(X_train, y_train)
y_pred_xgb = xgb_model.predict(X_test)
y_pred_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

models['XGBoost'] = xgb_model
predictions['XGBoost'] = y_pred_xgb
probabilities['XGBoost'] = y_pred_proba_xgb

print(f"Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_xgb):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_xgb):.4f}")

# ============================================================================
# 6. EVALUATION & VISUALIZATION
# ============================================================================
print("\n[6/7] Evaluation & Visualization...")

# Compare models
results = []
for name in models.keys():
    pred = predictions[name]
    proba = probabilities[name]
    results.append({
        'Model': name,
        'Accuracy': accuracy_score(y_test, pred),
        'F1': f1_score(y_test, pred),
        'AUC-ROC': roc_auc_score(y_test, proba)
    })

results_df = pd.DataFrame(results)
print("\n=== MODEL COMPARISON ===")
print(results_df.to_string(index=False))

# ROC Curves
plt.figure(figsize=(10, 8))
for name in models.keys():
    proba = probabilities[name]
    fpr, tpr, _ = roc_curve(y_test, proba)
    auc = roc_auc_score(y_test, proba)
    plt.plot(fpr, tpr, label=f'{name} (AUC={auc:.3f})', linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', label='Random')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curves Comparison')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
os.makedirs('../docs/images', exist_ok=True)
plt.savefig('../docs/images/roc_curves_late_delivery.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/roc_curves_late_delivery.png")

# Confusion Matrices
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for idx, name in enumerate(models.keys()):
    pred = predictions[name]
    cm = confusion_matrix(y_test, pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx])
    axes[idx].set_title(f'{name}\nAccuracy: {accuracy_score(y_test, pred):.3f}')
    axes[idx].set_xlabel('Predicted')
    axes[idx].set_ylabel('Actual')

plt.tight_layout()
plt.savefig('../docs/images/confusion_matrices_late_delivery.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/confusion_matrices_late_delivery.png")

# Feature Importance (XGBoost)
if hasattr(xgb_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False).head(20)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(data=feature_importance, y='feature', x='importance', palette='viridis')
    plt.title('Top 20 Feature Importances (XGBoost)')
    plt.xlabel('Importance')
    plt.tight_layout()
    plt.savefig('../docs/images/feature_importance_late_delivery.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved: docs/images/feature_importance_late_delivery.png")
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))

# ============================================================================
# 7. SAVE RESULTS
# ============================================================================
print("\n[7/7] Saving Results...")

# Save best model (XGBoost)
import joblib
os.makedirs('../models', exist_ok=True)
joblib.dump(xgb_model, '../models/late_delivery_xgb_model.pkl')
joblib.dump(scaler, '../models/late_delivery_scaler.pkl')
print("✓ Saved models to models/")

# Save results summary
results_df.to_csv('../docs/results_late_delivery.csv', index=False)
print("✓ Saved results to docs/results_late_delivery.csv")

print("\n" + "=" * 60)
print("✅ COMPLETED!")
print("=" * 60)
print(f"\nBest Model: XGBoost")
print(f"  - Accuracy: {results_df.loc[results_df['Model']=='XGBoost', 'Accuracy'].values[0]:.4f}")
print(f"  - F1 Score: {results_df.loc[results_df['Model']=='XGBoost', 'F1'].values[0]:.4f}")
print(f"  - AUC-ROC: {results_df.loc[results_df['Model']=='XGBoost', 'AUC-ROC'].values[0]:.4f}")

