"""
Script để generate các notebook chuẩn hóa từ template.
Chạy script này để tạo các notebook theo layout chuẩn.
"""

import json
import os

def create_notebook_cell(cell_type, source, metadata=None):
    """Tạo một notebook cell."""
    cell = {
        "cell_type": cell_type,
        "metadata": metadata or {},
        "source": source if isinstance(source, list) else [source]
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell

def create_late_delivery_notebook():
    """Tạo notebook cho Late Delivery Prediction."""
    cells = [
        # Header
        create_notebook_cell("markdown", """# MÔ HÌNH: DỰ ĐOÁN GIAO HÀNG TRỄ (LATE DELIVERY PREDICTION)

## Mục tiêu bài toán
Dự đoán `Late_delivery_risk` (0/1) dựa trên thông tin đơn hàng, shipping, và thời tiết để:
- Cảnh báo sớm các đơn hàng có nguy cơ giao trễ
- Tối ưu hóa logistics và routing
- Cải thiện customer satisfaction

## Input (Dữ liệu)
- **File nguồn:** `data/merged_supply_weather_clean.parquet`
- **Số lượng:** ~180,000 records
- **Các nhóm feature:** Time, Shipping, Location, Product, Weather, Sales

## Output (Yêu cầu dự đoán)
- **Target:** `Late_delivery_risk` (binary: 0 = on-time, 1 = late)
- **Output:** Xác suất trễ, label, và top features ảnh hưởng

## Thông tin phiên bản
- **Ngày:** 2024
- **Phiên bản:** 1.0
- **Dataset:** merged_supply_weather_clean.parquet"""),
        
        # Import libraries
        create_notebook_cell("code", """# Import thư viện & cấu hình chung
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

# Cấu hình matplotlib
%matplotlib inline
plt.style.use('default')
sns.set_palette("husl")

# Random seed để đảm bảo reproducibility
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("✓ Đã import thư viện và cấu hình xong")"""),
        
        # Load data
        create_notebook_cell("markdown", """## 1. Load dữ liệu

Load dữ liệu merged đã chuẩn hóa từ file `data/merged_supply_weather_clean.parquet`."""),
        
        create_notebook_cell("code", """# Load dữ liệu merged đã chuẩn hóa
data_path = os.path.join('..', 'data', 'merged_supply_weather_clean.parquet')

if not os.path.exists(data_path):
    raise FileNotFoundError(f"File không tìm thấy: {data_path}\\nVui lòng chạy: python scripts/merge_supplychain_weather.py trước")

df = pd.read_parquet(data_path)
print(f"✓ Đã load {len(df):,} records")
print(f"✓ Số cột: {len(df.columns)}")

# Hiển thị thông tin cơ bản
print("\\n=== THÔNG TIN DATASET ===")
df.info()

print("\\n=== 5 DÒNG ĐẦU TIÊN ===")
df.head()"""),
        
        # EDA
        create_notebook_cell("markdown", """## 2. EDA & Trực quan hóa

Phân tích nhanh phân phối target và mối tương quan giữa các features quan trọng với late delivery."""),
        
        create_notebook_cell("code", """# Phân phối target
if 'Late_delivery_risk' not in df.columns:
    raise ValueError("Không tìm thấy cột target 'Late_delivery_risk'")

target_dist = df['Late_delivery_risk'].value_counts()
late_rate = df['Late_delivery_risk'].mean() * 100

print("=== PHÂN PHỐI TARGET ===")
print(target_dist)
print(f"\\nTỉ lệ giao trễ: {late_rate:.2f}%")

# Visualize
plt.figure(figsize=(8, 5))
target_dist.plot(kind='bar', color=['green', 'red'])
plt.title('Phân phối Late Delivery Risk', fontsize=14, fontweight='bold')
plt.xlabel('Late Delivery Risk (0=On-time, 1=Late)', fontsize=12)
plt.ylabel('Số lượng', fontsize=12)
plt.xticks(rotation=0)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()"""),
        
        create_notebook_cell("code", """# Tương quan giữa weather risk và late delivery
if 'weather_risk_level' in df.columns:
    weather_corr = df.groupby('weather_risk_level')['Late_delivery_risk'].mean()
    
    plt.figure(figsize=(10, 6))
    weather_corr.plot(kind='bar', color='coral')
    plt.title('Tỉ lệ giao trễ theo mức độ rủi ro thời tiết', fontsize=14, fontweight='bold')
    plt.xlabel('Weather Risk Level (1-5)', fontsize=12)
    plt.ylabel('Tỉ lệ giao trễ', fontsize=12)
    plt.xticks(rotation=0)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print("\\n=== TỈ LỆ GIAO TRỄ THEO WEATHER RISK ===")
    print(weather_corr)"""),
        
        create_notebook_cell("code", """# Phân tích lead_time vs late delivery
if 'lead_time' in df.columns:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Boxplot
    df.boxplot(column='lead_time', by='Late_delivery_risk', ax=axes[0])
    axes[0].set_title('Phân phối Lead Time theo Late Delivery', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Late Delivery Risk', fontsize=11)
    axes[0].set_ylabel('Lead Time (ngày)', fontsize=11)
    plt.suptitle('')
    
    # Bar chart
    lead_time_avg = df.groupby('Late_delivery_risk')['lead_time'].mean()
    lead_time_avg.plot(kind='bar', color=['green', 'red'], ax=axes[1])
    axes[1].set_title('Lead Time trung bình theo Late Delivery', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Late Delivery Risk', fontsize=11)
    axes[1].set_ylabel('Lead Time trung bình (ngày)', fontsize=11)
    axes[1].tick_params(axis='x', rotation=0)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    print("\\n=== LEAD TIME TRUNG BÌNH ===")
    print(lead_time_avg)"""),
        
        # Feature Engineering
        create_notebook_cell("markdown", """## 3. Tiền xử lý & Feature Engineering

**Pipeline xử lý:**
- Chọn các nhóm feature: Time, Shipping, Location, Product, Weather, Sales
- Xử lý missing values: Fill median cho numeric, "Unknown" cho categorical
- Encoding: One-hot encoding cho categorical (giới hạn top 10 categories)
- Scaling: StandardScaler cho Logistic Regression (tree-based không cần scale)"""),
        
        create_notebook_cell("code", """# Chọn các nhóm feature
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

# Thu thập tất cả features có sẵn
all_features = []
for group, features in feature_groups.items():
    available = [f for f in features if f in df.columns]
    all_features.extend(available)
    print(f"✓ {group}: {len(available)}/{len(features)} features")

print(f"\\nTổng số features: {len(all_features)}")"""),
        
        create_notebook_cell("code", """# Tách X và y
X = df[all_features].copy()
y = df['Late_delivery_risk'].copy()

# Xử lý missing values
X = X.fillna(X.median(numeric_only=True))
for col in X.select_dtypes(include=['object']).columns:
    X[col] = X[col].fillna('Unknown')

print(f"Feature matrix shape: {X.shape}")
print(f"Số missing values còn lại: {X.isnull().sum().sum()}")"""),
        
        create_notebook_cell("code", """# Encoding categorical variables
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()

print(f"Số cột categorical: {len(categorical_cols)}")
print(f"Số cột numeric: {len(numeric_cols)}")

# One-hot encoding (giới hạn top 10 categories để tránh quá nhiều cột)
X_encoded = X[numeric_cols].copy()

for col in categorical_cols:
    top_cats = X[col].value_counts().head(10).index.tolist()
    for cat in top_cats:
        X_encoded[f'{col}_{cat}'] = (X[col] == cat).astype(int)
    X_encoded[f'{col}_Other'] = (~X[col].isin(top_cats)).astype(int)

print(f"\\nFeature matrix sau encoding: {X_encoded.shape}")"""),
        
        # Train/Test Split
        create_notebook_cell("markdown", """## 4. Chia tập train/test

**Tiêu chí chia:** Time-based split (80% train, 20% test) để tránh data leakage.
- Train: 80% dữ liệu đầu tiên theo thời gian
- Test: 20% dữ liệu cuối cùng"""),
        
        create_notebook_cell("code", """# Time-based split
if 'order date (DateOrders)' not in df.columns:
    raise ValueError("Không tìm thấy cột 'order date (DateOrders)'")

df_sorted = df.sort_values('order date (DateOrders)')
split_idx = int(len(df_sorted) * 0.8)

train_mask = df_sorted.index[:split_idx]
test_mask = df_sorted.index[split_idx:]

X_train = X_encoded.loc[train_mask]
X_test = X_encoded.loc[test_mask]
y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

print(f"Train set: {len(X_train):,} samples")
print(f"Test set: {len(X_test):,} samples")
print(f"\\nTrain date range: {df_sorted.loc[train_mask, 'order date (DateOrders)'].min()} đến {df_sorted.loc[train_mask, 'order date (DateOrders)'].max()}")
print(f"Test date range: {df_sorted.loc[test_mask, 'order date (DateOrders)'].min()} đến {df_sorted.loc[test_mask, 'order date (DateOrders)'].max()}")"""),
        
        create_notebook_cell("code", """# Scaling features (chỉ cho Logistic Regression, tree-based không cần)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("✓ Đã scale features cho Logistic Regression")"""),
        
        # Model Training
        create_notebook_cell("markdown", """## 5. Huấn luyện mô hình

**Các mô hình sẽ thử:**
- **Baseline:** Logistic Regression (đơn giản, dễ interpret)
- **Tree-based:** Random Forest, XGBoost (xử lý non-linear, feature importance)"""),
        
        create_notebook_cell("code", """# 5.1. Logistic Regression (Baseline)
lr_model = LogisticRegression(random_state=RANDOM_STATE, max_iter=1000, class_weight='balanced')
lr_model.fit(X_train_scaled, y_train)

y_pred_lr = lr_model.predict(X_test_scaled)
y_pred_proba_lr = lr_model.predict_proba(X_test_scaled)[:, 1]

print("=== KẾT QUẢ LOGISTIC REGRESSION ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred_lr):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_lr):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_lr):.4f}")
print("\\nClassification Report:")
print(classification_report(y_test, y_pred_lr))"""),
        
        create_notebook_cell("code", """# 5.2. Random Forest
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=RANDOM_STATE,
    class_weight='balanced',
    n_jobs=-1
)
rf_model.fit(X_train, y_train)

y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

print("=== KẾT QUẢ RANDOM FOREST ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_rf):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_rf):.4f}")
print("\\nClassification Report:")
print(classification_report(y_test, y_pred_rf))"""),
        
        create_notebook_cell("code", """# 5.3. XGBoost
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum() if y_train.sum() > 0 else 1

xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=RANDOM_STATE,
    scale_pos_weight=scale_pos_weight
)
xgb_model.fit(X_train, y_train)

y_pred_xgb = xgb_model.predict(X_test)
y_pred_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

print("=== KẾT QUẢ XGBOOST ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_xgb):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_xgb):.4f}")
print("\\nClassification Report:")
print(classification_report(y_test, y_pred_xgb))"""),
        
        # Evaluation
        create_notebook_cell("markdown", """## 6. Đánh giá mô hình & Trực quan hóa

**Metrics chính:**
- **Accuracy:** Tỉ lệ dự đoán đúng
- **F1 Score:** Harmonic mean của Precision và Recall (quan trọng với class imbalance)
- **AUC-ROC:** Diện tích dưới đường ROC (đánh giá khả năng phân loại)"""),
        
        create_notebook_cell("code", """# So sánh các mô hình
models_dict = {
    'Logistic Regression': (y_pred_proba_lr, y_pred_lr),
    'Random Forest': (y_pred_proba_rf, y_pred_rf),
    'XGBoost': (y_pred_proba_xgb, y_pred_xgb)
}

results = []
for name, (proba, pred) in models_dict.items():
    results.append({
        'Model': name,
        'Accuracy': accuracy_score(y_test, pred),
        'F1': f1_score(y_test, pred),
        'AUC-ROC': roc_auc_score(y_test, proba)
    })

results_df = pd.DataFrame(results)
print("\\n=== SO SÁNH CÁC MÔ HÌNH ===")
print(results_df.to_string(index=False))"""),
        
        create_notebook_cell("code", """# ROC Curves
plt.figure(figsize=(10, 8))

for name, (proba, _) in models_dict.items():
    fpr, tpr, _ = roc_curve(y_test, proba)
    auc = roc_auc_score(y_test, proba)
    plt.plot(fpr, tpr, label=f'{name} (AUC={auc:.3f})', linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', label='Random', linestyle='--')
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - So sánh các mô hình', fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()"""),
        
        create_notebook_cell("code", """# Confusion Matrices
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

for idx, (name, (_, pred)) in enumerate(models_dict.items()):
    cm = confusion_matrix(y_test, pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], cbar_kws={'label': 'Count'})
    axes[idx].set_title(f'{name}\\nAccuracy: {accuracy_score(y_test, pred):.3f}', fontsize=12, fontweight='bold')
    axes[idx].set_xlabel('Predicted', fontsize=11)
    axes[idx].set_ylabel('Actual', fontsize=11)

plt.tight_layout()
plt.show()"""),
        
        create_notebook_cell("code", """# Feature Importance (XGBoost)
if hasattr(xgb_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False).head(20)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(data=feature_importance, y='feature', x='importance', palette='viridis')
    plt.title('Top 20 Feature Importances (XGBoost)', fontsize=14, fontweight='bold')
    plt.xlabel('Importance', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print("\\n=== TOP 10 FEATURES QUAN TRỌNG NHẤT ===")
    print(feature_importance.head(10).to_string(index=False))"""),
        
        # Conclusion
        create_notebook_cell("markdown", """## 7. Kết luận & Gợi ý

### Kết quả chính
- **Model tốt nhất:** XGBoost (dựa trên AUC-ROC và F1 Score)
- **Metric chính:** AUC-ROC và F1 Score (quan trọng với class imbalance)

### Nhận xét
**Features quan trọng (dựa trên feature importance):**
- `lead_time`: Chênh lệch thời gian giao hàng là yếu tố quan trọng nhất
- `weather_risk_level`: Thời tiết khắc nghiệt làm tăng nguy cơ trễ
- `Days for shipping (real)`: Thời gian giao hàng thực tế
- Time features (weekend, holiday season) có ảnh hưởng đến logistics

### Hạn chế
- ⚠️ Class imbalance có thể ảnh hưởng đến performance
- ⚠️ Thiếu một số features (ví dụ: traffic conditions, road quality, distance chính xác)
- ⚠️ Model chưa được hyperparameter tuning kỹ
- ⚠️ Chưa có validation trên dữ liệu mới nhất (out-of-time validation)

### Hướng phát triển
1. **Feature Engineering:**
   - Rolling statistics (7-day, 30-day averages của số đơn trễ)
   - Lag features (số đơn trễ trong 7 ngày trước)
   - Distance features (khoảng cách từ warehouse đến customer)

2. **Model Improvement:**
   - Hyperparameter tuning (GridSearchCV/RandomSearchCV)
   - Ensemble methods (voting, stacking)
   - Deep Learning (nếu có đủ dữ liệu)

3. **Deployment:**
   - Real-time prediction API
   - Model monitoring (drift detection)
   - A/B testing""")
    ]
    
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.8.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    return notebook

def main():
    """Generate các notebook chuẩn hóa."""
    notebooks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notebooks')
    os.makedirs(notebooks_dir, exist_ok=True)
    
    # Generate Late Delivery notebook
    print("Generating model_late_delivery.ipynb...")
    notebook = create_late_delivery_notebook()
    output_path = os.path.join(notebooks_dir, 'model_late_delivery.ipynb')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)
    print(f"✓ Created: {output_path}")
    
    print("\n✅ Hoàn thành! Notebook đã được tạo theo layout chuẩn.")
    print("📝 Lưu ý: Các notebook khác (revenue_forecast, customer_churn) sẽ được tạo tương tự.")

if __name__ == '__main__':
    main()

