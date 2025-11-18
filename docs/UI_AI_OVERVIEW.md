# 🎨 UI AI OVERVIEW - Hướng Dẫn Giao Diện AI Models

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

---

## 📋 TỔNG QUAN

UI AI Overview được thiết kế để hiển thị rõ ràng tất cả các mô hình AI trong hệ thống, giúp người dùng:
- Hiểu được có những mô hình AI nào
- Biết mỗi mô hình làm nhiệm vụ gì
- Xem metrics và chất lượng của từng mô hình
- Thử dự đoán trực tiếp trên UI

---

## 🏗️ KIẾN TRÚC

### 1. Model Registry

**File:** `app/services/model_registry.py`

Registry này định nghĩa metadata của tất cả models:
- Tên, mô tả, loại model
- Metrics và targets
- API endpoints
- Form fields cho prediction
- Documentation paths

**Thêm model mới:**
1. Mở `app/services/model_registry.py`
2. Thêm entry vào `MODEL_REGISTRY` dict
3. Định nghĩa `AIModel` object với đầy đủ metadata

---

### 2. AI Dashboard Router

**File:** `app/routers/ai_dashboard.py`

**Endpoints:**
- `GET /dashboard/ai` - Overview tất cả models
- `GET /dashboard/ai/{model_id}` - Chi tiết từng model
- `GET /dashboard/ai/api/models` - API JSON list models
- `GET /dashboard/ai/api/model/{model_id}/metrics` - API JSON metrics

---

### 3. Templates

#### 3.1. AI Dashboard Overview

**File:** `app/templates/ai_dashboard.html`

**Features:**
- Hiển thị tất cả models dưới dạng cards
- Filter theo loại model (classification, regression, simulation, etc.)
- Statistics (total, deployed, analytics, etc.)
- Quick links đến chi tiết và prediction

**Layout:**
- Header với statistics
- Filter buttons
- Grid of model cards
- Each card shows: name, status, type, metrics, actions

---

#### 3.2. Model Detail Page

**File:** `app/templates/ai/model_detail.html`

**Features:**
- Tab-based navigation:
  - **Tổng quan:** Model info, quick metrics
  - **Metrics & Đánh giá:** Detailed metrics table, charts
  - **Thử dự đoán:** Prediction playground form
  - **Giải thích:** Model explanation, usage guide

**Sections:**
1. **Header:** Model name, type, status, description
2. **Tabs:** Overview, Metrics, Predict, Explain
3. **Overview Tab:**
   - Model info table
   - Quick metrics cards
4. **Metrics Tab:**
   - Detailed metrics table
   - Charts (confusion matrix, ROC curve, forecast plots, etc.)
5. **Predict Tab:**
   - Dynamic form based on model's form_fields
   - Submit button
   - Result display
6. **Explain Tab:**
   - Model purpose
   - How to use results
   - Important features
   - Limitations

---

## 🎯 CÁCH THÊM MÔ HÌNH MỚI VÀO UI

### Bước 1: Định nghĩa Model trong Registry

Mở `app/services/model_registry.py` và thêm:

```python
"new_model": AIModel(
    id="new_model",
    name="new_model",
    display_name="Tên Hiển Thị",
    type=ModelType.CLASSIFICATION,  # hoặc REGRESSION, SIMULATION, etc.
    description="Mô tả ngắn về model",
    status=ModelStatus.DEPLOYED,  # hoặc ANALYTICS, DEVELOPMENT
    version="1.0.0",
    metrics=[
        ModelMetric(name="AUC", value=None, target=0.75, unit="", description="..."),
        # ... more metrics
    ],
    api_endpoint="/ml/new-model/predict",
    api_method="POST",
    docs_path="docs/model_new_model.md",
    form_fields=[
        ModelFormField(name="feature1", label="Feature 1", type="number", required=True, default=0),
        # ... more fields
    ],
    dataset_info="Dataset description",
    model_path="models/new_model_model.pkl",
    chart_types=["confusion_matrix", "roc_curve"]
)
```

### Bước 2: Tạo API Endpoint (nếu chưa có)

Trong `app/routers/ml_api.py` hoặc router tương ứng:

```python
@router.post("/new-model/predict")
async def predict_new_model(request: NewModelRequest):
    # Implementation
    pass
```

### Bước 3: Tạo Documentation (optional)

Tạo `docs/model_new_model.md` với:
- Mô tả model
- Dataset info
- Features
- Metrics
- Usage

### Bước 4: Test UI

1. Start server: `uvicorn app.main:app --reload`
2. Truy cập: `http://127.0.0.1:8000/dashboard/ai`
3. Kiểm tra model mới xuất hiện trong list
4. Click vào model để xem chi tiết
5. Test prediction form (nếu có)

---

## 📊 HIỂN THỊ METRICS

### Metrics được hiển thị ở đâu?

1. **Overview Page (`/dashboard/ai`):**
   - Top 3 metrics trong model card
   - Dạng badges với target values

2. **Detail Page (`/dashboard/ai/{model_id}`):**
   - **Overview Tab:** Quick metrics cards với gradient background
   - **Metrics Tab:** Full metrics table với values, targets, descriptions

### Load Actual Metrics

Metrics có thể được load từ:
1. **Model Registry:** Target values (default)
2. **Results Directory:** `results/run_YYYYMMDD/metrics/{model_id}_metrics.json`
3. **API Endpoint:** `/dashboard/ai/api/model/{model_id}/metrics`

**Format JSON:**
```json
{
  "model_id": "late_delivery",
  "metrics": [
    {
      "name": "AUC-ROC",
      "value": 0.75,
      "target": 0.70,
      "unit": "",
      "description": "Area Under ROC Curve"
    }
  ]
}
```

---

## 🎨 STYLING

### Color Scheme

- **Classification:** Green (`#10b981`)
- **Regression:** Orange (`#f59e0b`)
- **RL:** Purple (`#8b5cf6`)
- **Simulation:** Red (`#ef4444`)
- **Cognitive:** Cyan (`#06b6d4`)
- **Online Learning:** Indigo (`#6366f1`)

### Status Badges

- **Deployed:** Green background
- **Analytics:** Blue background
- **Development:** Yellow background
- **Not Trained:** Red background

### Metric Badges

- **Good:** Green (meets target)
- **Warning:** Yellow (close to target)
- **Poor:** Red (below target)

---

## 🔧 CUSTOMIZATION

### Thêm Chart Type Mới

1. Thêm chart type vào `model.chart_types` trong registry
2. Template sẽ tự động render placeholder
3. Implement JavaScript để load chart data từ API hoặc results

### Customize Form Fields

Form fields được render tự động từ `model.form_fields`. Các types hỗ trợ:
- `text` - Text input
- `number` - Number input
- `select` - Dropdown với options
- `date` - Date picker

### Customize Prediction Result Display

Trong `model_detail.html`, function `displayPredictionResult()` có thể được customize để hiển thị kết quả theo format phù hợp với từng loại model.

---

## 📱 RESPONSIVE DESIGN

UI được thiết kế responsive:
- **Desktop:** 3 columns grid cho model cards
- **Tablet:** 2 columns
- **Mobile:** 1 column

Sử dụng TailwindCSS responsive classes:
- `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`

---

## ✅ CHECKLIST KHI THÊM MODEL MỚI

- [ ] Định nghĩa model trong `model_registry.py`
- [ ] Tạo API endpoint (nếu cần)
- [ ] Tạo documentation file (optional)
- [ ] Test model xuất hiện trong overview
- [ ] Test detail page
- [ ] Test prediction form (nếu có)
- [ ] Test metrics display
- [ ] Verify responsive design

---

## 🚀 NEXT STEPS

### Cải tiến có thể thêm:

1. **Real-time Metrics:**
   - Load metrics từ production monitoring
   - Auto-refresh metrics

2. **Model Comparison:**
   - So sánh metrics giữa các models
   - Side-by-side comparison view

3. **Model Versioning:**
   - Hiển thị multiple versions
   - Version comparison

4. **A/B Testing:**
   - Track A/B test results
   - Performance comparison

5. **SHAP Integration:**
   - Feature importance visualization
   - Explainability charts

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

