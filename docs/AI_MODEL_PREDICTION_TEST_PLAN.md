# AI Model Prediction Test Plan

This document defines the end-to-end QA workflow for validating every model that exposes an interactive prediction form at `http://localhost:8000/dashboard/ai`. The goal is to ensure each model:

- Enforces its required input schema and value ranges.
- Returns deterministic, well-formatted responses for happy paths.
- Surfaces clear validation errors for malformed payloads.
- Logs every call in `logs/inference/` and warns via `logs/warnings/` when anomalies are detected.

The `/dashboard/ai` interface now provides:

- A dropdown to select the target model.
- Dynamic forms generated from `app/services/model_registry.py`.
- Inline tooltips that explain each field and its valid range.
- Action buttons to **Load sample data**, **Download JSON sample**, and **Download CSV sample** so QA can bootstrap test payloads instantly.

> **Tip:** Always start from the model detail page, click **Load sample data**, adjust one field at a time, then press **Thử dự đoán** (Run Prediction). Review the JSON response and check the associated inference log before moving to the next scenario.

---

## Quick Reference

| Model | Endpoint | Mandatory Fields | Output |
| --- | --- | --- | --- |
| Inventory Optimizer RL | `POST /ml/rl/inventory` | `weather_risk_index`, `temp_7d_avg`, `region_congestion_index`, `warehouse_workload_score`, `order_item_price`, `sales`, `order_item_total` | Recommended buffer action + RL reward summary |
| Demand Forecast Ensemble | `POST /ml/forecast/demand` | `forecast_date`, `region`, `category` (context) | `forecasted_revenue`, `confidence_range`, horizon metrics |
| Late Delivery Classifier | `POST /ml/logistics/delay` | `shipping_duration_scheduled` | `late_risk_prob`, `late_risk_label`, top drivers |
| Pricing Elasticity Model | `POST /ml/pricing/elasticity` | `price`, `sales` | `expected_volume_delta`, elasticity score |
| Customer Churn Classifier | `POST /ml/customer/churn` | `customer_id` | `churn_prob`, `churn_label`, feature influences |

---

## Model-Specific Test Suites

### 1. Inventory Optimizer RL

**Input Schema**

| Field | Type | Valid Range | Notes |
| --- | --- | --- | --- |
| `weather_risk_index` | float | 0 ≤ x ≤ 1 | Composite weather severity |
| `temp_7d_avg` | float | -20 to 50 °C | Rolling temperature |
| `rain_7d_avg` | float | 0 to 400 mm | Rolling rainfall |
| `storm_flag` | select {0,1} | 0 or 1 | 1 when storm expected |
| `region_congestion_index` | float | 0 to 5 | Computed by monitoring service |
| `warehouse_workload_score` | float | 0 to 1 | Utilization ratio |
| `order_item_price` | float | ≥ 0 | USD |
| `sales` | float | ≥ 0 | Daily units |
| `order_item_total` | float | ≥ 0 | USD |
| `region` | select list | GLOBAL/EU/APAC/NA/LATAM/AFRICA/MENA | Buffer target |

**Test Cases**

- **Normal**: Use the provided sample payload (risk 0.18, congestion 2.3). Expect a JSON response with `status=success`, `prediction.recommended_buffer`, and `prediction.reward`.
- **Edge**: Set `weather_risk_index=1`, `storm_flag=1`, `region_congestion_index=5`. Expect higher buffer recommendation but still `status=success`.
- **Error**: Omit `order_item_price` or send `weather_risk_index=1.5`. Expect HTTP 422 with validation message; UI should display the error banner without crashing.

**Sample Payload**

```json
{
  "weather_risk_index": 0.18,
  "temp_7d_avg": 29.5,
  "rain_7d_avg": 8.0,
  "storm_flag": 0,
  "region_congestion_index": 2.3,
  "warehouse_workload_score": 0.55,
  "order_item_price": 45.0,
  "sales": 125.0,
  "order_item_total": 5600.0,
  "region": "GLOBAL"
}
```

---

### 2. Demand Forecast Ensemble

**Input Schema**

| Field | Type | Valid Range |
| --- | --- | --- |
| `region` | select | GLOBAL/EU/APAC/NA/LATAM/AFRICA/MENA/OTHER |
| `category` | text | Business category |
| `forecast_date` | date | ISO date (YYYY-MM-DD) |
| `revenue_lag_7d` | float | ≥ 0 |
| `revenue_lag_30d` | float | ≥ 0 |
| `revenue_7d_avg` | float | ≥ 0 |
| `revenue_30d_avg` | float | ≥ 0 |
| `month` | int | 1–12 |
| `day_of_week` | int | 0–6 (0=Mon) |
| `temperature` | float | -30 to 55 °C |

**Test Cases**

- **Normal**: Sample payload (GLOBAL electronics). Expect `forecasted_revenue` positive and `confidence_range` object.
- **Edge**: Set `month=1`, `temperature=-5`, `region=AFRICA` to simulate cold snap. Forecast should still return `status=success`.
- **Error**: Provide `forecast_date` in invalid format or omit it. Expect HTTP 422 with “value is not a valid date”.

**Sample Payload**

```json
{
  "region": "GLOBAL",
  "category": "Electronics",
  "forecast_date": "2025-05-01",
  "revenue_lag_7d": 52000.0,
  "revenue_lag_30d": 208000.0,
  "revenue_7d_avg": 54000.0,
  "revenue_30d_avg": 215000.0,
  "month": 5,
  "day_of_week": 2,
  "temperature": 30.0
}
```

---

### 3. Late Delivery Classifier

**Input Schema**

| Field | Type | Notes |
| --- | --- | --- |
| `shipping_duration_scheduled` | int | Required; 1–120 days |
| `temperature` | float | Optional; -30 to 55 °C |
| `precipitation` | float | Optional; 0–500 mm |
| `wind_speed` | float | Optional; 0–60 m/s |
| `weather_risk_level` | int | 1–5 |
| `is_weekend` | select {0,1} | Delivery date on weekend |
| `month` | int | 1–12 |
| `category_name` | text | Product category |

**Test Cases**

- **Normal**: Sample payload yields `late_risk_prob` and textual explanation of top features.
- **Edge**: Set `shipping_duration_scheduled=1` with `weather_risk_level=5`. Expect probability > baseline but still numeric.
- **Error**: Submit negative `shipping_duration_scheduled`. API should reject with validation error.

**Sample Payload**

```json
{
  "shipping_duration_scheduled": 5,
  "temperature": 27.5,
  "precipitation": 3.2,
  "wind_speed": 8.1,
  "weather_risk_level": 2,
  "is_weekend": 0,
  "month": 6,
  "category_name": "Electronics"
}
```

---

### 4. Pricing Elasticity Model

**Input Schema**

| Field | Type | Range |
| --- | --- | --- |
| `price` | float | ≥ 0 |
| `sales` | float | ≥ 0 |
| `weather_risk_index` | float | 0–1 |
| `weather_influence` | float | -1 to 1 |
| `region` | select | GLOBAL/EU/APAC/NA/LATAM/AFRICA/MENA |

**Test Cases**

- **Normal**: Use default payload; expect `prediction.elasticity` and projected demand impact.
- **Edge**: Set `weather_influence=-0.9` to simulate adverse weather; ensure output remains finite.
- **Error**: Remove `price` or pass string for `sales`; must return HTTP 422.

**Sample Payload**

```json
{
  "price": 49.0,
  "sales": 120.0,
  "weather_risk_index": 0.2,
  "weather_influence": 0.1,
  "region": "GLOBAL"
}
```

---

### 5. Customer Churn Classifier

**Input Schema**

| Field | Type | Notes |
| --- | --- | --- |
| `customer_id` | text | Required |
| `rfm_recency` | float | Days since last order |
| `rfm_frequency` | float | Orders in last 12 months |
| `rfm_monetary` | float | Spend (USD) |
| `total_orders` | int | Lifetime |
| `avg_order_value` | float | USD |

**Test Cases**

- **Normal**: Sample payload returns `churn_prob` between 0 and 1.
- **Edge**: Set `rfm_recency=365`, `rfm_frequency=0`. Expect high churn probability but no crash.
- **Error**: Leave `customer_id` blank. UI should highlight the required field.

**Sample Payload**

```json
{
  "customer_id": "C123456",
  "rfm_recency": 30,
  "rfm_frequency": 8,
  "rfm_monetary": 1200.0,
  "total_orders": 15,
  "avg_order_value": 85.0
}
```

---

## UI Testing Workflow

1. Navigate to `/dashboard/ai` and select the target model card.
2. On the model detail page, review the **Overview** and **Metrics** tabs to understand expected behavior.
3. Switch to the **Thử dự đoán** tab.
4. Click **Load sample data** to pre-populate the form or download JSON/CSV templates for automated testing.
5. Adjust the inputs according to the scenario being validated (normal, edge, or error).
6. Press **Thử dự đoán** and capture:
   - HTTP response code and body.
   - System toast/snackbar (if any).
   - Entries written to `logs/inference/<model>_inference.log`.
7. For warning scenarios (drift, weather coverage, etc.) ensure `logs/warnings/<model>_warnings.log` records a structured warning and that the dashboard warning feed refreshes.

## Additional Notes

- 2025-11-15 fix: UI now strips empty fields before sending payloads. Previously blank numeric inputs were serialized as empty strings, causing the FastAPI validators to reject every request with 422 errors. Make sure future UI changes continue dropping empty values.
- Always keep model_registry metadata in sync with the test plan; QA relies on those definitions to know valid ranges.
- When automating through Selenium or Playwright, leverage the **Download JSON sample** button to feed canonical payloads into API tests.
- Negative tests should confirm that backend validation errors are surfaced in the UI (red alert block) without exposing stack traces.
- After completing all scenarios, update the QA checklist and attach logs/screenshots for auditing.
