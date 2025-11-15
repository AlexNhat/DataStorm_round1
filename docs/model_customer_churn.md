# Mô hình dự đoán khách hàng churn (Customer Churn Prediction)

Dự đoán khách hàng có khả năng "không quay lại mua" (churn) hay không dựa trên RFM và lịch sử mua hàng để phục vụ chiến dịch giữ chân khách hàng, ưu tiên chăm sóc khách hàng có nguy cơ churn cao và tối ưu hóa marketing spend.

---

## 1. Dữ liệu sử dụng

### Nguồn dữ liệu
- **File gốc:** 
  - `data/DataCoSupplyChainDataset.csv` (~180,000 records)
  - `data/geocoded_weather.csv` (~180,000 records)
- **File merged:** `data/merged_supply_weather_clean.parquet`
  - Dataset đã được gộp và chuẩn hóa
  - **Aggregation:** Group by `Order Customer Id`
  - **Target:** `churn` (binary: 0 = active, 1 = churned)

### Định nghĩa Churn
- **Recency > 180 days** (6 tháng): Khách hàng không mua lại trong 6 tháng gần nhất được coi là churn
- **Snapshot date:** Ngày cuối cùng trong dataset

### Mô tả ngắn
- **Số khách hàng:** ~X customers (tùy dataset)
- **Tỉ lệ churn:** ~X% (tùy dataset và định nghĩa churn)
- **Khoảng thời gian:** Từ min date đến max date trong dataset

---

## 2. Tiền xử lý & Feature Engineering

### Các bước chính

#### 2.1. Tính toán RFM (Quan trọng nhất)
- **Recency (R):** Số ngày từ lần mua cuối đến snapshot date
- **Frequency (F):** Số đơn hàng tổng cộng
- **Monetary (M):** Tổng giá trị mua hàng

#### 2.2. Feature Engineering đặc thù

**RFM Features:**
- `rfm_recency`: Số ngày từ lần mua cuối
- `rfm_frequency`: Số đơn hàng
- `rfm_monetary`: Tổng giá trị mua hàng

**Customer History Features:**
- `total_sales`: Tổng doanh thu từ khách hàng
- `avg_order_value`: Giá trị đơn hàng trung bình
- `std_order_value`: Độ lệch chuẩn giá trị đơn hàng
- `total_orders`: Tổng số đơn hàng
- `days_since_first_order`: Số ngày từ lần mua đầu tiên

**Engagement Features:**
- `category_diversity`: Số danh mục sản phẩm khác nhau đã mua
- `avg_discount`: Giảm giá trung bình

**Location Features:**
- `preferred_country`: Quốc gia mua hàng nhiều nhất
- One-hot encoding cho top countries

#### 2.3. Xử lý class imbalance
- **SMOTE (Synthetic Minority Oversampling Technique):** Tạo synthetic samples cho class thiểu số
- **Class weights:** Sử dụng trong models

---

## 3. Thiết kế mô hình

### Loại mô hình
- **Baseline:** Logistic Regression (đơn giản, dễ interpret)
- **Tree-based:** Random Forest, XGBoost (xử lý non-linear, feature importance)

### Cách chia train/test
- **Time-based split:** 80% train (theo `last_order_date`), 20% test
- **Lý do:** Tránh data leakage, mô hình phải dự đoán tương lai dựa trên quá khứ

### Các metric đánh giá
- **Accuracy:** Tỉ lệ dự đoán đúng
- **F1 Score:** Harmonic mean của Precision và Recall
- **AUC-ROC:** Diện tích dưới đường ROC
- **Precision:** Trong số các khách dự đoán churn, bao nhiêu thực sự churn
- **Recall:** Trong số các khách thực sự churn, bao nhiêu được dự đoán đúng
- **Precision@TopK:** Precision trong top K khách hàng có risk cao nhất (quan trọng cho business)

---

## 4. Kết quả chính

### Model tốt nhất
- **XGBoost** thường cho kết quả tốt nhất (AUC-ROC cao, F1 Score tốt)

### Metrics (ví dụ)
| Model | Accuracy | F1 | AUC-ROC | Precision | Recall |
|-------|----------|----|---------|-----------|--------|
| Logistic Regression | ~0.XX | ~0.XX | ~0.XX | ~0.XX | ~0.XX |
| Random Forest | ~0.XX | ~0.XX | ~0.XX | ~0.XX | ~0.XX |
| XGBoost | ~0.XX | ~0.XX | ~0.XX | ~0.XX | ~0.XX |

### Insights
1. **RFM features** rất quan trọng: `rfm_recency` thường là feature quan trọng nhất
2. **Recency** là yếu tố quyết định: Khách hàng không mua lâu sẽ có nguy cơ churn cao
3. **Frequency và Monetary** cũng quan trọng: Khách hàng mua nhiều, giá trị cao thường ít churn
4. **Customer lifetime** có ảnh hưởng: Khách hàng mới có thể churn cao hơn

### Top Features (dựa trên XGBoost feature importance)
1. `rfm_recency` - Số ngày từ lần mua cuối (quan trọng nhất!)
2. `rfm_frequency` - Số đơn hàng
3. `rfm_monetary` - Tổng giá trị
4. `days_since_first_order` - Tuổi khách hàng
5. `avg_order_value` - Giá trị đơn trung bình

### Precision@TopK
- **Precision@Top1000:** Nếu Precision@Top1000 = 0.7, nghĩa là trong 1000 khách hàng có risk cao nhất, 700 thực sự sẽ churn
- Điều này giúp focus resources vào đúng đối tượng

---

## 5. Hạn chế & Hướng phát triển

### Hạn chế
- **Churn definition:** 180 days có thể không phù hợp với tất cả business (có thể cần điều chỉnh)
- **Thiếu behavioral features:** 
  - Website visits
  - Email opens/clicks
  - Customer support interactions
- **Thiếu external data:**
  - Competitor pricing
  - Market conditions
- **Model chưa tuning:** Hyperparameters chưa được tối ưu kỹ

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

4. **MLOps:**
   - Model monitoring (drift detection)
   - Retrain định kỳ
   - Real-time prediction API
   - Integration với CRM system

---

## 6. Liên kết tới notebook

**Notebook minh họa:** `notebooks/model_customer_churn.ipynb`

### Hướng dẫn mở notebook
1. **Với Jupyter Notebook:**
   ```bash
   jupyter notebook notebooks/model_customer_churn.ipynb
   ```

2. **Với JupyterLab:**
   ```bash
   jupyter lab notebooks/model_customer_churn.ipynb
   ```

3. **Với VS Code:**
   - Cài extension "Jupyter"
   - Mở file `.ipynb` trực tiếp trong VS Code

### Lưu ý
- Đảm bảo đã chạy `python scripts/merge_supplychain_weather.py` trước để có file `data/merged_supply_weather_clean.parquet`
- Notebook có thể chạy từ trên xuống dưới mà không cần thay đổi

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0
