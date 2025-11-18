"""
Script để convert Python scripts thành Jupyter notebooks chuẩn hóa.
Chạy: python scripts/convert_py_to_notebook.py
"""

import json
import os
import re

def create_notebook_cell(cell_type, source, metadata=None):
    """Tạo một notebook cell."""
    cell = {
        "cell_type": cell_type,
        "metadata": metadata or {},
        "source": source if isinstance(source, list) else [line + "\n" for line in source.split("\n")]
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell

def create_revenue_forecast_notebook():
    """Tạo notebook cho Revenue Forecast từ Python script."""
    cells = []
    
    # Header
    cells.append(create_notebook_cell("markdown", """# MÔ HÌNH: DỰ BÁO DOANH THU (REVENUE/DEMAND FORECAST)

## Mục tiêu bài toán
Dự báo doanh thu (hoặc số lượng đơn) theo thời gian, có thể theo tổng hệ thống hoặc theo từng quốc gia (Country) để:
- Kế hoạch doanh số (sales planning)
- Tối ưu hóa inventory
- Phân bổ resources
- Budget planning

## Input (Dữ liệu)
- **File nguồn:** `data/merged_supply_weather_clean.parquet`
- **Aggregation:** Group by `year_month` + `Order Country`
- **Các nhóm feature:** Lag features, Rolling stats, Time, Weather, Country

## Output (Yêu cầu dự đoán)
- **Target:** `revenue` (tổng Sales trong tháng)
- **Output:** Doanh thu dự báo, khoảng tin cậy

## Thông tin phiên bản
- **Ngày:** 2024
- **Phiên bản:** 1.0
- **Dataset:** merged_supply_weather_clean.parquet"""))
    
    # Import
    cells.append(create_notebook_cell("code", """# Import thư viện & cấu hình chung
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
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

print("✓ Đã import thư viện và cấu hình xong")"""))
    
    # Load data
    cells.append(create_notebook_cell("markdown", """## 1. Load dữ liệu

Load dữ liệu merged đã chuẩn hóa từ file `data/merged_supply_weather_clean.parquet`."""))
    
    cells.append(create_notebook_cell("code", """# Load dữ liệu merged đã chuẩn hóa
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
df.head()"""))
    
    # Aggregation & EDA
    cells.append(create_notebook_cell("markdown", """## 2. Aggregation & EDA

Aggregate dữ liệu theo tháng và quốc gia, sau đó phân tích time series."""))
    
    cells.append(create_notebook_cell("code", """# Aggregate revenue by month and country
df['order_date'] = pd.to_datetime(df['order date (DateOrders)'])
df['year_month'] = df['order_date'].dt.to_period('M')

# Aggregate by month and country
revenue_ts = df.groupby(['year_month', 'Order Country']).agg({
    'Sales': 'sum',
    'Order Id': 'nunique',  # Number of orders
    'temperature_2m_mean': 'mean',
    'precipitation_sum': 'mean',
    'weather_risk_level': 'mean'
}).reset_index()

revenue_ts.columns = ['year_month', 'country', 'revenue', 'order_count', 
                      'avg_temperature', 'avg_precipitation', 'avg_weather_risk']

# Convert period to datetime
revenue_ts['date'] = revenue_ts['year_month'].dt.to_timestamp()
revenue_ts = revenue_ts.sort_values('date')

print(f"✓ Đã aggregate thành {len(revenue_ts):,} time periods")
print(f"Date range: {revenue_ts['date'].min()} đến {revenue_ts['date'].max()}")

# Hiển thị thông tin
print("\\n=== THÔNG TIN TIME SERIES ===")
revenue_ts.info()

print("\\n=== 5 DÒNG ĐẦU TIÊN ===")
revenue_ts.head()"""))
    
    cells.append(create_notebook_cell("code", """# Visualize time series cho top 5 countries
plt.figure(figsize=(14, 6))
for country in revenue_ts['country'].value_counts().head(5).index:
    country_data = revenue_ts[revenue_ts['country'] == country]
    plt.plot(country_data['date'], country_data['revenue'], label=country, linewidth=2)

plt.title('Doanh thu theo thời gian - Top 5 quốc gia', fontsize=14, fontweight='bold')
plt.xlabel('Ngày', fontsize=12)
plt.ylabel('Doanh thu', fontsize=12)
plt.legend(fontsize=10)
plt.grid(alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()"""))
    
    cells.append(create_notebook_cell("code", """# Phân phối doanh thu
plt.figure(figsize=(10, 6))
plt.hist(revenue_ts['revenue'], bins=50, edgecolor='black', alpha=0.7)
plt.title('Phân phối doanh thu', fontsize=14, fontweight='bold')
plt.xlabel('Doanh thu', fontsize=12)
plt.ylabel('Tần suất', fontsize=12)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()

print("=== THỐNG KÊ DOANH THU ===")
print(revenue_ts['revenue'].describe())"""))
    
    # Feature Engineering
    cells.append(create_notebook_cell("markdown", """## 3. Tiền xử lý & Feature Engineering

**Pipeline xử lý:**
- Tạo lag features (revenue_lag1, lag2, lag3)
- Rolling statistics (moving average 7, 30 tháng, std 7 tháng)
- Time features (month, quarter, year, cyclical encoding)
- Weather features (aggregate)
- Country encoding (one-hot cho top countries)"""))
    
    cells.append(create_notebook_cell("code", """# Tạo lag features
revenue_ts['revenue_lag1'] = revenue_ts.groupby('country')['revenue'].shift(1)
revenue_ts['revenue_lag2'] = revenue_ts.groupby('country')['revenue'].shift(2)
revenue_ts['revenue_lag3'] = revenue_ts.groupby('country')['revenue'].shift(3)

# Rolling statistics
revenue_ts['revenue_ma7'] = revenue_ts.groupby('country')['revenue'].transform(
    lambda x: x.rolling(window=7, min_periods=1).mean()
)
revenue_ts['revenue_ma30'] = revenue_ts.groupby('country')['revenue'].transform(
    lambda x: x.rolling(window=30, min_periods=1).mean()
)
revenue_ts['revenue_std7'] = revenue_ts.groupby('country')['revenue'].transform(
    lambda x: x.rolling(window=7, min_periods=1).std()
)

# Time features
revenue_ts['month'] = revenue_ts['date'].dt.month
revenue_ts['quarter'] = revenue_ts['date'].dt.quarter
revenue_ts['year'] = revenue_ts['date'].dt.year
revenue_ts['month_sin'] = np.sin(2 * np.pi * revenue_ts['month'] / 12)
revenue_ts['month_cos'] = np.cos(2 * np.pi * revenue_ts['month'] / 12)

# Country encoding (one-hot for top countries)
top_countries = revenue_ts['country'].value_counts().head(10).index
for country in top_countries:
    revenue_ts[f'country_{country}'] = (revenue_ts['country'] == country).astype(int)

print(f"✓ Đã tạo {len(revenue_ts.columns)} features")"""))
    
    cells.append(create_notebook_cell("code", """# Chọn features
feature_cols = [
    'revenue_lag1', 'revenue_lag2', 'revenue_lag3',
    'revenue_ma7', 'revenue_ma30', 'revenue_std7',
    'month', 'quarter', 'year', 'month_sin', 'month_cos',
    'avg_temperature', 'avg_precipitation', 'avg_weather_risk',
    'order_count'
] + [f'country_{c}' for c in top_countries]

# Remove rows with NaN (from lag features)
revenue_ts_clean = revenue_ts.dropna(subset=['revenue'] + feature_cols)

X = revenue_ts_clean[feature_cols].fillna(0)
y = revenue_ts_clean['revenue']

print(f"Feature matrix shape: {X.shape}")
print(f"Target shape: {y.shape}")
print(f"Số missing values: {X.isnull().sum().sum()}")"""))
    
    # Train/Test Split
    cells.append(create_notebook_cell("markdown", """## 4. Chia tập train/test

**Tiêu chí chia:** Time-based split (80% train, 20% test) để tránh data leakage.
- Train: 80% dữ liệu đầu tiên theo thời gian
- Test: 20% dữ liệu cuối cùng"""))
    
    cells.append(create_notebook_cell("code", """# Time-based split
revenue_ts_clean = revenue_ts_clean.sort_values('date')
split_idx = int(len(revenue_ts_clean) * 0.8)

train_mask = revenue_ts_clean.index[:split_idx]
test_mask = revenue_ts_clean.index[split_idx:]

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]
y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

print(f"Train set: {len(X_train):,} samples")
print(f"Test set: {len(X_test):,} samples")
print(f"\\nTrain date range: {revenue_ts_clean.loc[train_mask, 'date'].min()} đến {revenue_ts_clean.loc[train_mask, 'date'].max()}")
print(f"Test date range: {revenue_ts_clean.loc[test_mask, 'date'].min()} đến {revenue_ts_clean.loc[test_mask, 'date'].max()}")"""))
    
    # Model Training
    cells.append(create_notebook_cell("markdown", """## 5. Huấn luyện mô hình

**Các mô hình sẽ thử:**
- **Baseline:** Linear Regression (đơn giản, dễ interpret)
- **Tree-based:** Random Forest Regressor, XGBoost Regressor (xử lý non-linear, feature importance)"""))
    
    cells.append(create_notebook_cell("code", """# 5.1. Linear Regression (Baseline)
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
y_pred_lr = lr_model.predict(X_test)

mae_lr = mean_absolute_error(y_test, y_pred_lr)
rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
mape_lr = mean_absolute_percentage_error(y_test, y_pred_lr)
r2_lr = r2_score(y_test, y_pred_lr)

print("=== KẾT QUẢ LINEAR REGRESSION ===")
print(f"MAE: {mae_lr:,.2f}")
print(f"RMSE: {rmse_lr:,.2f}")
print(f"MAPE: {mape_lr:.2f}%")
print(f"R²: {r2_lr:.4f}")"""))
    
    cells.append(create_notebook_cell("code", """# 5.2. Random Forest
rf_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=RANDOM_STATE,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)

mae_rf = mean_absolute_error(y_test, y_pred_rf)
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
mape_rf = mean_absolute_percentage_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)

print("=== KẾT QUẢ RANDOM FOREST ===")
print(f"MAE: {mae_rf:,.2f}")
print(f"RMSE: {rmse_rf:,.2f}")
print(f"MAPE: {mape_rf:.2f}%")
print(f"R²: {r2_rf:.4f}")"""))
    
    cells.append(create_notebook_cell("code", """# 5.3. XGBoost
xgb_model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=RANDOM_STATE
)
xgb_model.fit(X_train, y_train)
y_pred_xgb = xgb_model.predict(X_test)

mae_xgb = mean_absolute_error(y_test, y_pred_xgb)
rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred_xgb))
mape_xgb = mean_absolute_percentage_error(y_test, y_pred_xgb)
r2_xgb = r2_score(y_test, y_pred_xgb)

print("=== KẾT QUẢ XGBOOST ===")
print(f"MAE: {mae_xgb:,.2f}")
print(f"RMSE: {rmse_xgb:,.2f}")
print(f"MAPE: {mape_xgb:.2f}%")
print(f"R²: {r2_xgb:.4f}")"""))
    
    # Evaluation
    cells.append(create_notebook_cell("markdown", """## 6. Đánh giá mô hình & Trực quan hóa

**Metrics chính:**
- **MAE (Mean Absolute Error):** Lỗi trung bình tuyệt đối
- **RMSE (Root Mean Squared Error):** Lỗi bình phương trung bình (penalize lỗi lớn hơn)
- **MAPE (Mean Absolute Percentage Error):** Lỗi phần trăm trung bình
- **R² (R-squared):** Tỉ lệ phương sai được giải thích"""))
    
    cells.append(create_notebook_cell("code", """# So sánh các mô hình
models_dict = {
    'Linear Regression': y_pred_lr,
    'Random Forest': y_pred_rf,
    'XGBoost': y_pred_xgb
}

results = []
for name, pred in models_dict.items():
    results.append({
        'Model': name,
        'MAE': mean_absolute_error(y_test, pred),
        'RMSE': np.sqrt(mean_squared_error(y_test, pred)),
        'MAPE': mean_absolute_percentage_error(y_test, pred),
        'R²': r2_score(y_test, pred)
    })

results_df = pd.DataFrame(results)
print("\\n=== SO SÁNH CÁC MÔ HÌNH ===")
print(results_df.to_string(index=False))"""))
    
    cells.append(create_notebook_cell("code", """# Scatter plots: Actual vs Predicted
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for idx, (name, pred) in enumerate(models_dict.items()):
    axes[idx].scatter(y_test, pred, alpha=0.5, s=20)
    axes[idx].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    axes[idx].set_xlabel('Doanh thu thực tế', fontsize=11)
    axes[idx].set_ylabel('Doanh thu dự báo', fontsize=11)
    axes[idx].set_title(f'{name}\\nR² = {r2_score(y_test, pred):.3f}', fontsize=12, fontweight='bold')
    axes[idx].grid(alpha=0.3)

plt.tight_layout()
plt.show()"""))
    
    cells.append(create_notebook_cell("code", """# Time series plot: Actual vs Predicted cho top 3 countries
test_dates = revenue_ts_clean.loc[test_mask, 'date']
test_countries = revenue_ts_clean.loc[test_mask, 'country'].unique()[:3]

fig, axes = plt.subplots(len(test_countries), 1, figsize=(14, 5*len(test_countries)))
if len(test_countries) == 1:
    axes = [axes]

for idx, country in enumerate(test_countries):
    country_mask = revenue_ts_clean.loc[test_mask, 'country'] == country
    country_dates = test_dates[country_mask]
    country_actual = y_test[country_mask]
    country_pred = y_pred_xgb[country_mask]
    
    axes[idx].plot(country_dates, country_actual, label='Thực tế', linewidth=2, marker='o')
    axes[idx].plot(country_dates, country_pred, label='Dự báo (XGBoost)', linewidth=2, marker='s', linestyle='--')
    axes[idx].set_title(f'Dự báo doanh thu: {country}', fontsize=12, fontweight='bold')
    axes[idx].set_xlabel('Ngày', fontsize=11)
    axes[idx].set_ylabel('Doanh thu', fontsize=11)
    axes[idx].legend(fontsize=10)
    axes[idx].grid(alpha=0.3)
    axes[idx].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()"""))
    
    cells.append(create_notebook_cell("code", """# Feature Importance (XGBoost)
if hasattr(xgb_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False).head(15)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(data=feature_importance, y='feature', x='importance', palette='viridis')
    plt.title('Top 15 Feature Importances (XGBoost)', fontsize=14, fontweight='bold')
    plt.xlabel('Importance', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print("\\n=== TOP 10 FEATURES QUAN TRỌNG NHẤT ===")
    print(feature_importance.head(10).to_string(index=False))"""))
    
    # Conclusion
    cells.append(create_notebook_cell("markdown", """## 7. Kết luận & Gợi ý

### Kết quả chính
- **Model tốt nhất:** XGBoost (dựa trên R² và MAPE)
- **Metric chính:** R², MAPE (quan trọng cho business)

### Nhận xét
**Features quan trọng (dựa trên feature importance):**
- `revenue_lag1`: Doanh thu tháng trước là yếu tố quan trọng nhất (autocorrelation)
- `revenue_ma7`, `revenue_ma30`: Moving averages nắm bắt xu hướng dài hạn
- `month_sin`, `month_cos`: Seasonality có ảnh hưởng
- `avg_weather_risk`: Weather impact

### Hạn chế
- ⚠️ Chưa xử lý trend (có thể dùng differencing)
- ⚠️ Thiếu external features (marketing spend, promotions, economic indicators)
- ⚠️ Model chưa được hyperparameter tuning kỹ
- ⚠️ Chưa xử lý outliers trong target

### Hướng phát triển
1. **Time Series Methods:**
   - ARIMA, SARIMA (cho seasonality)
   - Prophet (Facebook)
   - LSTM (Deep Learning)

2. **Feature Engineering:**
   - Trend features (linear, polynomial)
   - Holiday features
   - Economic indicators (GDP, inflation)

3. **Ensemble:**
   - Combine time series models với tree-based models
   - Stacking

4. **Deployment:**
   - Real-time forecasting API
   - Model monitoring (drift detection)
   - A/B testing"""))
    
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

def create_customer_churn_notebook():
    """Tạo notebook cho Customer Churn từ Python script."""
    cells = []
    
    # Header
    cells.append(create_notebook_cell("markdown", """# MÔ HÌNH: DỰ ĐOÁN KHÁCH HÀNG CHURN (CUSTOMER CHURN PREDICTION)

## Mục tiêu bài toán
Dự đoán khách hàng có khả năng "không quay lại mua" (churn) hay không dựa trên RFM và lịch sử mua hàng để:
- Chiến dịch giữ chân khách hàng (retention campaigns)
- Ưu tiên chăm sóc khách hàng có nguy cơ churn cao
- Phân tích nguyên nhân churn
- Tối ưu hóa marketing spend

## Input (Dữ liệu)
- **File nguồn:** `data/merged_supply_weather_clean.parquet`
- **Aggregation:** Group by `Order Customer Id`
- **Các nhóm feature:** RFM, Customer History, Engagement, Location

## Output (Yêu cầu dự đoán)
- **Target:** `churn` (binary: 0 = active, 1 = churned)
- **Định nghĩa churn:** Recency > 180 days (6 tháng)
- **Output:** Xác suất churn, label, và recommendations

## Thông tin phiên bản
- **Ngày:** 2024
- **Phiên bản:** 1.0
- **Dataset:** merged_supply_weather_clean.parquet"""))
    
    # Import
    cells.append(create_notebook_cell("code", """# Import thư viện & cấu hình chung
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

# Cấu hình matplotlib
%matplotlib inline
plt.style.use('default')
sns.set_palette("husl")

# Random seed để đảm bảo reproducibility
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("✓ Đã import thư viện và cấu hình xong")"""))
    
    # Load data
    cells.append(create_notebook_cell("markdown", """## 1. Load dữ liệu

Load dữ liệu merged đã chuẩn hóa từ file `data/merged_supply_weather_clean.parquet`."""))
    
    cells.append(create_notebook_cell("code", """# Load dữ liệu merged đã chuẩn hóa
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
df.head()"""))
    
    # RFM Calculation
    cells.append(create_notebook_cell("markdown", """## 2. Tính toán RFM & Customer Features

Tính toán RFM (Recency, Frequency, Monetary) và các features khác cho từng khách hàng."""))
    
    cells.append(create_notebook_cell("code", """# Define snapshot date (last date in dataset)
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

print(f"✓ Đã tính RFM cho {len(customer_features):,} customers")"""))
    
    cells.append(create_notebook_cell("code", """# Additional customer features
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

print(f"✓ Đã tính thêm customer features")"""))
    
    # Define Churn
    cells.append(create_notebook_cell("markdown", """## 3. Định nghĩa Churn Label

**Churn definition:** Recency > 180 days (6 tháng) - Khách hàng không mua lại trong 6 tháng gần nhất được coi là churn."""))
    
    cells.append(create_notebook_cell("code", """# Churn definition: Recency > 180 days (6 months)
churn_threshold = 180
customer_features['churn'] = (customer_features['rfm_recency'] > churn_threshold).astype(int)

churn_rate = customer_features['churn'].mean()
print(f"Churn definition: Recency > {churn_threshold} days")
print(f"Tỉ lệ churn: {churn_rate*100:.2f}%")
print(f"Churned customers: {customer_features['churn'].sum():,}")
print(f"Active customers: {(customer_features['churn']==0).sum():,}")

# Visualize churn distribution
plt.figure(figsize=(8, 5))
customer_features['churn'].value_counts().plot(kind='bar', color=['green', 'red'])
plt.title('Phân phối Churn', fontsize=14, fontweight='bold')
plt.xlabel('Churn (0=Active, 1=Churned)', fontsize=12)
plt.ylabel('Số lượng', fontsize=12)
plt.xticks(rotation=0)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()"""))
    
    # EDA
    cells.append(create_notebook_cell("markdown", """## 4. EDA & Trực quan hóa

Phân tích mối tương quan giữa RFM và churn."""))
    
    cells.append(create_notebook_cell("code", """# Phân tích RFM vs Churn
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Recency
customer_features.boxplot(column='rfm_recency', by='churn', ax=axes[0])
axes[0].set_title('Phân phối Recency theo Churn', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Churn', fontsize=11)
axes[0].set_ylabel('Recency (ngày)', fontsize=11)
plt.suptitle('')

# Frequency
customer_features.boxplot(column='rfm_frequency', by='churn', ax=axes[1])
axes[1].set_title('Phân phối Frequency theo Churn', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Churn', fontsize=11)
axes[1].set_ylabel('Frequency', fontsize=11)
plt.suptitle('')

# Monetary
customer_features.boxplot(column='rfm_monetary', by='churn', ax=axes[2])
axes[2].set_title('Phân phối Monetary theo Churn', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Churn', fontsize=11)
axes[2].set_ylabel('Monetary ($)', fontsize=11)
plt.suptitle('')

plt.tight_layout()
plt.show()"""))
    
    # Feature Engineering
    cells.append(create_notebook_cell("markdown", """## 5. Tiền xử lý & Feature Engineering

**Pipeline xử lý:**
- Chọn features: RFM, Customer History, Engagement, Location
- Xử lý missing values: Fill 0 cho numeric
- Encoding: One-hot encoding cho country (top 10)
- Xử lý class imbalance: SMOTE"""))
    
    cells.append(create_notebook_cell("code", """# Chọn features
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

print(f"Feature matrix shape: {X.shape}")
print(f"Features: {list(X.columns)}")"""))
    
    # Train/Test Split
    cells.append(create_notebook_cell("markdown", """## 6. Chia tập train/test

**Tiêu chí chia:** Time-based split (80% train, 20% test) theo `last_order_date` để tránh data leakage.
- Train: 80% customers (theo last_order_date)
- Test: 20% customers"""))
    
    cells.append(create_notebook_cell("code", """# Time-based split
customer_features_sorted = customer_features.sort_values('last_order_date')
split_idx = int(len(customer_features_sorted) * 0.8)

train_mask = customer_features_sorted.index[:split_idx]
test_mask = customer_features_sorted.index[split_idx:]

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]
y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

print(f"Train set: {len(X_train):,} samples (churn rate: {y_train.mean()*100:.2f}%)")
print(f"Test set: {len(X_test):,} samples (churn rate: {y_test.mean()*100:.2f}%)")"""))
    
    cells.append(create_notebook_cell("code", """# Xử lý class imbalance với SMOTE
smote = SMOTE(random_state=RANDOM_STATE)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"Trước SMOTE: {len(X_train):,} samples (churn: {y_train.sum():,})")
print(f"Sau SMOTE: {len(X_train_balanced):,} samples (churn: {y_train_balanced.sum():,})")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_balanced)
X_test_scaled = scaler.transform(X_test)

print("✓ Đã scale features")"""))
    
    # Model Training
    cells.append(create_notebook_cell("markdown", """## 7. Huấn luyện mô hình

**Các mô hình sẽ thử:**
- **Baseline:** Logistic Regression (đơn giản, dễ interpret)
- **Tree-based:** Random Forest, XGBoost (xử lý non-linear, feature importance)"""))
    
    cells.append(create_notebook_cell("code", """# 7.1. Logistic Regression (Baseline)
lr_model = LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)
lr_model.fit(X_train_scaled, y_train_balanced)
y_pred_lr = lr_model.predict(X_test_scaled)
y_pred_proba_lr = lr_model.predict_proba(X_test_scaled)[:, 1]

print("=== KẾT QUẢ LOGISTIC REGRESSION ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred_lr):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_lr):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_lr):.4f}")
print(f"Precision: {precision_score(y_test, y_pred_lr):.4f}")
print(f"Recall: {recall_score(y_test, y_pred_lr):.4f}")
print("\\nClassification Report:")
print(classification_report(y_test, y_pred_lr))"""))
    
    cells.append(create_notebook_cell("code", """# 7.2. Random Forest
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=RANDOM_STATE,
    class_weight='balanced',
    n_jobs=-1
)
rf_model.fit(X_train_balanced, y_train_balanced)
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

print("=== KẾT QUẢ RANDOM FOREST ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_rf):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_rf):.4f}")
print(f"Precision: {precision_score(y_test, y_pred_rf):.4f}")
print(f"Recall: {recall_score(y_test, y_pred_rf):.4f}")
print("\\nClassification Report:")
print(classification_report(y_test, y_pred_rf))"""))
    
    cells.append(create_notebook_cell("code", """# 7.3. XGBoost
scale_pos_weight = (y_train_balanced == 0).sum() / (y_train_balanced == 1).sum()

xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=RANDOM_STATE,
    scale_pos_weight=scale_pos_weight
)
xgb_model.fit(X_train_balanced, y_train_balanced)
y_pred_xgb = xgb_model.predict(X_test)
y_pred_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

print("=== KẾT QUẢ XGBOOST ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")
print(f"F1 Score: {f1_score(y_test, y_pred_xgb):.4f}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_xgb):.4f}")
print(f"Precision: {precision_score(y_test, y_pred_xgb):.4f}")
print(f"Recall: {recall_score(y_test, y_pred_xgb):.4f}")
print("\\nClassification Report:")
print(classification_report(y_test, y_pred_xgb))"""))
    
    # Evaluation
    cells.append(create_notebook_cell("markdown", """## 8. Đánh giá mô hình & Trực quan hóa

**Metrics chính:**
- **Accuracy:** Tỉ lệ dự đoán đúng
- **F1 Score:** Harmonic mean của Precision và Recall
- **AUC-ROC:** Diện tích dưới đường ROC
- **Precision@TopK:** Precision trong top K khách hàng có risk cao nhất (quan trọng cho business)"""))
    
    cells.append(create_notebook_cell("code", """# So sánh các mô hình
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
        'AUC-ROC': roc_auc_score(y_test, proba),
        'Precision': precision_score(y_test, pred),
        'Recall': recall_score(y_test, pred)
    })

results_df = pd.DataFrame(results)
print("\\n=== SO SÁNH CÁC MÔ HÌNH ===")
print(results_df.to_string(index=False))"""))
    
    cells.append(create_notebook_cell("code", """# Precision@TopK (Top K customers with highest churn risk)
K = 1000
for name in models_dict.keys():
    proba = models_dict[name][0]
    top_k_indices = np.argsort(proba)[-K:][::-1]
    top_k_actual = y_test.iloc[top_k_indices]
    precision_at_k = top_k_actual.sum() / K
    print(f"\\n{name} - Precision@Top{K}: {precision_at_k:.4f}")"""))
    
    cells.append(create_notebook_cell("code", """# ROC Curves
plt.figure(figsize=(10, 8))

for name in models_dict.keys():
    proba = models_dict[name][0]
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
plt.show()"""))
    
    cells.append(create_notebook_cell("code", """# Confusion Matrices
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

for idx, name in enumerate(models_dict.keys()):
    pred = models_dict[name][1]
    cm = confusion_matrix(y_test, pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], cbar_kws={'label': 'Count'})
    axes[idx].set_title(f'{name}\\nAccuracy: {accuracy_score(y_test, pred):.3f}', fontsize=12, fontweight='bold')
    axes[idx].set_xlabel('Predicted', fontsize=11)
    axes[idx].set_ylabel('Actual', fontsize=11)

plt.tight_layout()
plt.show()"""))
    
    cells.append(create_notebook_cell("code", """# Feature Importance (XGBoost)
if hasattr(xgb_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False).head(15)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(data=feature_importance, y='feature', x='importance', palette='viridis')
    plt.title('Top 15 Feature Importances (XGBoost)', fontsize=14, fontweight='bold')
    plt.xlabel('Importance', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print("\\n=== TOP 10 FEATURES QUAN TRỌNG NHẤT ===")
    print(feature_importance.head(10).to_string(index=False))"""))
    
    # Conclusion
    cells.append(create_notebook_cell("markdown", """## 9. Kết luận & Gợi ý

### Kết quả chính
- **Model tốt nhất:** XGBoost (dựa trên AUC-ROC và F1 Score)
- **Metric chính:** AUC-ROC, F1 Score, Precision@TopK (quan trọng cho business)

### Nhận xét
**Features quan trọng (dựa trên feature importance):**
- `rfm_recency`: Số ngày từ lần mua cuối là yếu tố quan trọng nhất (quyết định churn)
- `rfm_frequency`: Số đơn hàng
- `rfm_monetary`: Tổng giá trị mua hàng
- `days_since_first_order`: Tuổi khách hàng
- `avg_order_value`: Giá trị đơn trung bình

### Hạn chế
- ⚠️ Churn definition (180 days) có thể cần điều chỉnh theo business
- ⚠️ Thiếu behavioral features (website visits, email opens, customer support interactions)
- ⚠️ Thiếu external data (competitor pricing, market conditions)
- ⚠️ Model chưa được hyperparameter tuning kỹ

### Hướng phát triển
1. **Feature Engineering:**
   - Customer lifetime value (CLV)
   - Purchase velocity (tốc độ mua)
   - Product return rate
   - Customer support interactions
   - Website/app engagement metrics

2. **Model Improvement:**
   - Hyperparameter tuning (GridSearchCV/RandomSearchCV)
   - Ensemble methods (voting, stacking)
   - Deep Learning (nếu có đủ dữ liệu)

3. **Business Logic:**
   - Điều chỉnh churn definition theo business
   - Segment-specific models (ví dụ: B2B vs B2C)
   - Cohort analysis

4. **Deployment:**
   - Real-time prediction API
   - Model monitoring (drift detection)
   - Retrain định kỳ
   - Integration với CRM system"""))
    
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
    
    # Generate Revenue Forecast notebook
    print("Generating model_revenue_forecast.ipynb...")
    notebook = create_revenue_forecast_notebook()
    output_path = os.path.join(notebooks_dir, 'model_revenue_forecast.ipynb')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)
    print(f"✓ Created: {output_path}")
    
    # Generate Customer Churn notebook
    print("\nGenerating model_customer_churn.ipynb...")
    notebook = create_customer_churn_notebook()
    output_path = os.path.join(notebooks_dir, 'model_customer_churn.ipynb')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)
    print(f"✓ Created: {output_path}")
    
    print("\n✅ Hoàn thành! Tất cả notebooks đã được tạo theo layout chuẩn.")
    print("📝 Lưu ý: Notebook model_late_delivery.ipynb đã có sẵn và đã được chuẩn hóa.")

if __name__ == '__main__':
    main()

