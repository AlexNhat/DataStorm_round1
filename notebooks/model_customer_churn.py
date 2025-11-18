"""
MODEL 3: CUSTOMER CHURN PREDICTION
Notebook script để dự đoán khách hàng có khả năng churn

Chạy: python notebooks/model_customer_churn.py
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
    roc_curve, f1_score, accuracy_score, precision_score, recall_score
)
import xgboost as xgb
from imblearn.over_sampling import SMOTE
import os
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("=" * 60)
print("MODEL 3: CUSTOMER CHURN PREDICTION")
print("=" * 60)

# ============================================================================
# 1. LOAD DATA
# ============================================================================
print("\n[1/8] Loading data...")
data_path = os.path.join('..', 'data', 'merged_supply_weather_clean.parquet')

if not os.path.exists(data_path):
    print(f"⚠️ File not found: {data_path}")
    print("Please run: python scripts/merge_supplychain_weather.py first")
    exit(1)

df = pd.read_parquet(data_path)
print(f"✓ Loaded {len(df):,} records")

# ============================================================================
# 2. CALCULATE RFM & CUSTOMER FEATURES
# ============================================================================
print("\n[2/8] Calculating RFM and customer features...")

# Define snapshot date (last date in dataset)
snapshot_date = df['order date (DateOrders)'].max()
print(f"Snapshot date: {snapshot_date}")

# Calculate RFM for each customer
df['order_date'] = pd.to_datetime(df['order date (DateOrders)'])

# Recency: Days since last order
last_order = df.groupby('Order Customer Id')['order_date'].max()
recency = (snapshot_date - last_order).dt.days

# Frequency: Number of orders
frequency = df.groupby('Order Customer Id')['Order Id'].nunique()

# Monetary: Total sales
monetary = df.groupby('Order Customer Id')['Sales'].sum()

# Combine RFM
customer_features = pd.DataFrame({
    'customer_id': recency.index,
    'rfm_recency': recency.values,
    'rfm_frequency': frequency.values,
    'rfm_monetary': monetary.values
})

# Additional customer features
customer_stats = df.groupby('Order Customer Id').agg({
    'Sales': ['sum', 'mean', 'std'],
    'Order Id': 'nunique',
    'Category Name': 'nunique',  # Category diversity
    'Order Country': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown',  # Most common country
    'order_date': ['min', 'max']  # First and last order dates
}).reset_index()

customer_stats.columns = [
    'customer_id', 'total_sales', 'avg_order_value', 'std_order_value',
    'total_orders', 'category_diversity', 'preferred_country',
    'first_order_date', 'last_order_date'
]

# Merge
customer_features = customer_features.merge(customer_stats, on='customer_id', how='left')

# Days since first order
customer_features['days_since_first_order'] = (
    snapshot_date - pd.to_datetime(customer_features['first_order_date'])
).dt.days

# Average discount
customer_discount = df.groupby('Order Customer Id')['Order Item Discount'].mean()
customer_features = customer_features.merge(
    customer_discount.rename('avg_discount'),
    left_on='customer_id',
    right_index=True,
    how='left'
)

print(f"✓ Calculated features for {len(customer_features):,} customers")

# ============================================================================
# 3. DEFINE CHURN LABEL
# ============================================================================
print("\n[3/8] Defining churn label...")

# Churn definition: Recency > 180 days (6 months)
churn_threshold = 180
customer_features['churn'] = (customer_features['rfm_recency'] > churn_threshold).astype(int)

churn_rate = customer_features['churn'].mean()
print(f"Churn definition: Recency > {churn_threshold} days")
print(f"Churn rate: {churn_rate*100:.2f}%")
print(f"Churned customers: {customer_features['churn'].sum():,}")
print(f"Active customers: {(customer_features['churn']==0).sum():,}")

# Visualize churn distribution
plt.figure(figsize=(10, 6))
customer_features['churn'].value_counts().plot(kind='bar', color=['green', 'red'])
plt.title('Churn Distribution')
plt.xlabel('Churn (0=Active, 1=Churned)')
plt.ylabel('Count')
plt.xticks(rotation=0)
plt.tight_layout()
os.makedirs('../docs/images', exist_ok=True)
plt.savefig('../docs/images/churn_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/churn_distribution.png")

# ============================================================================
# 4. FEATURE ENGINEERING
# ============================================================================
print("\n[4/8] Feature Engineering...")

# Select features
feature_cols = [
    'rfm_recency', 'rfm_frequency', 'rfm_monetary',
    'total_sales', 'avg_order_value', 'std_order_value',
    'total_orders', 'category_diversity',
    'days_since_first_order', 'avg_discount'
]

# Handle missing values
customer_features[feature_cols] = customer_features[feature_cols].fillna(0)

# Country encoding (one-hot for top countries)
top_countries = customer_features['preferred_country'].value_counts().head(10).index
for country in top_countries:
    customer_features[f'country_{country}'] = (
        customer_features['preferred_country'] == country
    ).astype(int)

# Prepare feature matrix
X = customer_features[feature_cols + [f'country_{c}' for c in top_countries]].copy()
y = customer_features['churn'].copy()

print(f"✓ Feature matrix: {X.shape}")
print(f"✓ Features: {list(X.columns)}")

# ============================================================================
# 5. TRAIN/TEST SPLIT (TIME-BASED)
# ============================================================================
print("\n[5/8] Train/Test Split...")

# Use last_order_date for time-based split
customer_features_sorted = customer_features.sort_values('last_order_date')
split_idx = int(len(customer_features_sorted) * 0.8)

train_mask = customer_features_sorted.index[:split_idx]
test_mask = customer_features_sorted.index[split_idx:]

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]
y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

print(f"Train set: {len(X_train):,} samples (churn rate: {y_train.mean()*100:.2f}%)")
print(f"Test set: {len(X_test):,} samples (churn rate: {y_test.mean()*100:.2f}%)")

# ============================================================================
# 6. HANDLE CLASS IMBALANCE
# ============================================================================
print("\n[6/8] Handling class imbalance...")

# Apply SMOTE
smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"Before SMOTE: {len(X_train):,} samples (churn: {y_train.sum():,})")
print(f"After SMOTE: {len(X_train_balanced):,} samples (churn: {y_train_balanced.sum():,})")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_balanced)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 7. MODEL TRAINING
# ============================================================================
print("\n[7/8] Training Models...")

models = {}
predictions = {}
probabilities = {}

# 7.1. Logistic Regression
print("\n--- Logistic Regression ---")
lr_model = LogisticRegression(random_state=42, max_iter=1000)
lr_model.fit(X_train_scaled, y_train_balanced)
y_pred_lr = lr_model.predict(X_test_scaled)
y_pred_proba_lr = lr_model.predict_proba(X_test_scaled)[:, 1]

models['Logistic Regression'] = lr_model
predictions['Logistic Regression'] = y_pred_lr
probabilities['Logistic Regression'] = y_pred_proba_lr

print(f"Accuracy: {accuracy_score(y_test, y_pred_lr):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_lr):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_lr):.4f}")
print(f"Precision: {precision_score(y_test, y_pred_lr):.4f}")
print(f"Recall: {recall_score(y_test, y_pred_lr):.4f}")

# 7.2. Random Forest
print("\n--- Random Forest ---")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)
rf_model.fit(X_train_balanced, y_train_balanced)
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

models['Random Forest'] = rf_model
predictions['Random Forest'] = y_pred_rf
probabilities['Random Forest'] = y_pred_proba_rf

print(f"Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_rf):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_rf):.4f}")
print(f"Precision: {precision_score(y_test, y_pred_rf):.4f}")
print(f"Recall: {recall_score(y_test, y_pred_rf):.4f}")

# 7.3. XGBoost
print("\n--- XGBoost ---")
scale_pos_weight = (y_train_balanced == 0).sum() / (y_train_balanced == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    scale_pos_weight=scale_pos_weight
)
xgb_model.fit(X_train_balanced, y_train_balanced)
y_pred_xgb = xgb_model.predict(X_test)
y_pred_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

models['XGBoost'] = xgb_model
predictions['XGBoost'] = y_pred_xgb
probabilities['XGBoost'] = y_pred_proba_xgb

print(f"Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_xgb):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_xgb):.4f}")
print(f"Precision: {precision_score(y_test, y_pred_xgb):.4f}")
print(f"Recall: {recall_score(y_test, y_pred_xgb):.4f}")

# ============================================================================
# 8. EVALUATION & VISUALIZATION
# ============================================================================
print("\n[8/8] Evaluation & Visualization...")

# Compare models
results = []
for name in models.keys():
    pred = predictions[name]
    proba = probabilities[name]
    results.append({
        'Model': name,
        'Accuracy': accuracy_score(y_test, pred),
        'F1': f1_score(y_test, pred),
        'AUC-ROC': roc_auc_score(y_test, proba),
        'Precision': precision_score(y_test, pred),
        'Recall': recall_score(y_test, pred)
    })

results_df = pd.DataFrame(results)
print("\n=== MODEL COMPARISON ===")
print(results_df.to_string(index=False))

# Precision@K (Top K customers with highest churn risk)
K = 1000
for name in models.keys():
    proba = probabilities[name]
    top_k_indices = np.argsort(proba)[-K:][::-1]
    top_k_actual = y_test.iloc[top_k_indices]
    precision_at_k = top_k_actual.sum() / K
    print(f"\n{name} - Precision@Top{K}: {precision_at_k:.4f}")

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
plt.title('ROC Curves Comparison - Churn Prediction')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('../docs/images/roc_curves_churn.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/roc_curves_churn.png")

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
plt.savefig('../docs/images/confusion_matrices_churn.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/confusion_matrices_churn.png")

# Feature Importance (XGBoost)
if hasattr(xgb_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False).head(15)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(data=feature_importance, y='feature', x='importance', palette='viridis')
    plt.title('Top 15 Feature Importances (XGBoost) - Churn Prediction')
    plt.xlabel('Importance')
    plt.tight_layout()
    plt.savefig('../docs/images/feature_importance_churn.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved: docs/images/feature_importance_churn.png")
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))

# Top customers at risk
xgb_proba = probabilities['XGBoost']
top_risk_customers = customer_features.loc[X_test.index].copy()
top_risk_customers['churn_probability'] = xgb_proba
top_risk_customers = top_risk_customers.sort_values('churn_probability', ascending=False).head(20)

print("\n=== TOP 20 CUSTOMERS AT RISK ===")
print(top_risk_customers[['customer_id', 'rfm_recency', 'rfm_frequency', 'rfm_monetary', 
                          'churn_probability', 'churn']].to_string(index=False))

# Save results
import joblib
os.makedirs('../models', exist_ok=True)
joblib.dump(xgb_model, '../models/churn_xgb_model.pkl')
joblib.dump(scaler, '../models/churn_scaler.pkl')
results_df.to_csv('../docs/results_churn.csv', index=False)

print("\n" + "=" * 60)
print("✅ COMPLETED!")
print("=" * 60)
print(f"\nBest Model: XGBoost")
best_row = results_df.loc[results_df['Model']=='XGBoost']
print(f"  - Accuracy: {best_row['Accuracy'].values[0]:.4f}")
print(f"  - F1 Score: {best_row['F1'].values[0]:.4f}")
print(f"  - AUC-ROC: {best_row['AUC-ROC'].values[0]:.4f}")
print(f"  - Precision: {best_row['Precision'].values[0]:.4f}")
print(f"  - Recall: {best_row['Recall'].values[0]:.4f}")

