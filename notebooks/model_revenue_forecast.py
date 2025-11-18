"""
MODEL 2: REVENUE/DEMAND FORECAST
Notebook script để dự báo doanh thu theo thời gian

Chạy: python notebooks/model_revenue_forecast.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import xgboost as xgb
import os
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("=" * 60)
print("MODEL 2: REVENUE/DEMAND FORECAST")
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

# ============================================================================
# 2. AGGREGATE DATA BY TIME PERIOD
# ============================================================================
print("\n[2/7] Aggregating data by time period...")

# Aggregate revenue by month and country
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

print(f"✓ Aggregated to {len(revenue_ts):,} time periods")
print(f"Date range: {revenue_ts['date'].min()} to {revenue_ts['date'].max()}")

# Visualize time series
plt.figure(figsize=(14, 6))
for country in revenue_ts['country'].value_counts().head(5).index:
    country_data = revenue_ts[revenue_ts['country'] == country]
    plt.plot(country_data['date'], country_data['revenue'], label=country, linewidth=2)

plt.title('Revenue Time Series by Country (Top 5)')
plt.xlabel('Date')
plt.ylabel('Revenue')
plt.legend()
plt.grid(alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
os.makedirs('../docs/images', exist_ok=True)
plt.savefig('../docs/images/revenue_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/revenue_timeseries.png")

# ============================================================================
# 3. FEATURE ENGINEERING
# ============================================================================
print("\n[3/7] Feature Engineering...")

# Create lag features
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

print(f"✓ Created {len(revenue_ts.columns)} features")

# ============================================================================
# 4. PREPARE FEATURES
# ============================================================================
print("\n[4/7] Preparing features...")

# Select features
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

print(f"✓ Feature matrix: {X.shape}")
print(f"✓ Target: {y.shape}")

# ============================================================================
# 5. TRAIN/TEST SPLIT (TIME-BASED)
# ============================================================================
print("\n[5/7] Train/Test Split (Time-based)...")

# Sort by date
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
print(f"Train date range: {revenue_ts_clean.loc[train_mask, 'date'].min()} to {revenue_ts_clean.loc[train_mask, 'date'].max()}")
print(f"Test date range: {revenue_ts_clean.loc[test_mask, 'date'].min()} to {revenue_ts_clean.loc[test_mask, 'date'].max()}")

# ============================================================================
# 6. MODEL TRAINING
# ============================================================================
print("\n[6/7] Training Models...")

models = {}
predictions = {}

# 6.1. Linear Regression
print("\n--- Linear Regression ---")
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
y_pred_lr = lr_model.predict(X_test)

models['Linear Regression'] = lr_model
predictions['Linear Regression'] = y_pred_lr

mae_lr = mean_absolute_error(y_test, y_pred_lr)
rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
mape_lr = mean_absolute_percentage_error(y_test, y_pred_lr)
r2_lr = r2_score(y_test, y_pred_lr)

print(f"MAE: {mae_lr:,.2f}")
print(f"RMSE: {rmse_lr:,.2f}")
print(f"MAPE: {mape_lr:.2f}%")
print(f"R²: {r2_lr:.4f}")

# 6.2. Random Forest
print("\n--- Random Forest ---")
rf_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)

models['Random Forest'] = rf_model
predictions['Random Forest'] = y_pred_rf

mae_rf = mean_absolute_error(y_test, y_pred_rf)
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
mape_rf = mean_absolute_percentage_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)

print(f"MAE: {mae_rf:,.2f}")
print(f"RMSE: {rmse_rf:,.2f}")
print(f"MAPE: {mape_rf:.2f}%")
print(f"R²: {r2_rf:.4f}")

# 6.3. XGBoost
print("\n--- XGBoost ---")
xgb_model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)
xgb_model.fit(X_train, y_train)
y_pred_xgb = xgb_model.predict(X_test)

models['XGBoost'] = xgb_model
predictions['XGBoost'] = y_pred_xgb

mae_xgb = mean_absolute_error(y_test, y_pred_xgb)
rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred_xgb))
mape_xgb = mean_absolute_percentage_error(y_test, y_pred_xgb)
r2_xgb = r2_score(y_test, y_pred_xgb)

print(f"MAE: {mae_xgb:,.2f}")
print(f"RMSE: {rmse_xgb:,.2f}")
print(f"MAPE: {mape_xgb:.2f}%")
print(f"R²: {r2_xgb:.4f}")

# ============================================================================
# 7. EVALUATION & VISUALIZATION
# ============================================================================
print("\n[7/7] Evaluation & Visualization...")

# Compare models
results = []
for name in models.keys():
    pred = predictions[name]
    results.append({
        'Model': name,
        'MAE': mean_absolute_error(y_test, pred),
        'RMSE': np.sqrt(mean_squared_error(y_test, pred)),
        'MAPE': mean_absolute_percentage_error(y_test, pred),
        'R²': r2_score(y_test, pred)
    })

results_df = pd.DataFrame(results)
print("\n=== MODEL COMPARISON ===")
print(results_df.to_string(index=False))

# Visualization: Actual vs Predicted
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for idx, name in enumerate(models.keys()):
    pred = predictions[name]
    axes[idx].scatter(y_test, pred, alpha=0.5, s=20)
    axes[idx].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    axes[idx].set_xlabel('Actual Revenue')
    axes[idx].set_ylabel('Predicted Revenue')
    axes[idx].set_title(f'{name}\nR² = {r2_score(y_test, pred):.3f}')
    axes[idx].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('../docs/images/revenue_forecast_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/revenue_forecast_scatter.png")

# Time series plot: Actual vs Predicted
test_dates = revenue_ts_clean.loc[test_mask, 'date']
test_countries = revenue_ts_clean.loc[test_mask, 'country'].unique()[:3]  # Top 3 countries

fig, axes = plt.subplots(len(test_countries), 1, figsize=(14, 5*len(test_countries)))
if len(test_countries) == 1:
    axes = [axes]

for idx, country in enumerate(test_countries):
    country_mask = revenue_ts_clean.loc[test_mask, 'country'] == country
    country_dates = test_dates[country_mask]
    country_actual = y_test[country_mask]
    country_pred = predictions['XGBoost'][country_mask]
    
    axes[idx].plot(country_dates, country_actual, label='Actual', linewidth=2, marker='o')
    axes[idx].plot(country_dates, country_pred, label='Predicted (XGBoost)', linewidth=2, marker='s', linestyle='--')
    axes[idx].set_title(f'Revenue Forecast: {country}')
    axes[idx].set_xlabel('Date')
    axes[idx].set_ylabel('Revenue')
    axes[idx].legend()
    axes[idx].grid(alpha=0.3)
    axes[idx].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('../docs/images/revenue_forecast_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: docs/images/revenue_forecast_timeseries.png")

# Feature Importance (XGBoost)
if hasattr(xgb_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False).head(15)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(data=feature_importance, y='feature', x='importance', palette='viridis')
    plt.title('Top 15 Feature Importances (XGBoost)')
    plt.xlabel('Importance')
    plt.tight_layout()
    plt.savefig('../docs/images/feature_importance_revenue.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved: docs/images/feature_importance_revenue.png")
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))

# Save results
import joblib
os.makedirs('../models', exist_ok=True)
joblib.dump(xgb_model, '../models/revenue_forecast_xgb_model.pkl')
results_df.to_csv('../docs/results_revenue_forecast.csv', index=False)

print("\n" + "=" * 60)
print("✅ COMPLETED!")
print("=" * 60)
print(f"\nBest Model: XGBoost")
best_row = results_df.loc[results_df['Model']=='XGBoost']
print(f"  - MAE: {best_row['MAE'].values[0]:,.2f}")
print(f"  - RMSE: {best_row['RMSE'].values[0]:,.2f}")
print(f"  - MAPE: {best_row['MAPE'].values[0]:.2f}%")
print(f"  - R²: {best_row['R²'].values[0]:.4f}")

