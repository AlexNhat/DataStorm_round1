## AUTO TUNING SUMMARY

**Run:** `run_20251114_1902`  
**Ngày:** 14/11/2025

### 1. Mô hình đã tinh chỉnh
| Model | Phiên bản mới | Mô tả |
| --- | --- | --- |
| Late Delivery | v2 – XGBoost tuned | Thử max_depth 5–8, subsample 0.75–0.9; mục tiêu giữ AUC/F1 ổn định. |
| Revenue Forecast | v2 – RandomForest tuned | RF depth 12 / 350 trees giảm MAE & RMSE; thử cả XGB. |
| Customer Churn | v2 – XGBoost tuned | Các cấu hình mới vẫn đạt ~1.0 ⇒ nghi ngờ leakage. |

### 2. So sánh metrics
| Model | Metric | Trước | Sau | Thay đổi |
| --- | --- | --- | --- | --- |
| Late Delivery | AUC | 0.97045 | 0.97023 | ~0 |
| Revenue Forecast | MAE | 0.8952 | 0.8057 | -0.0895 |
| Revenue Forecast | RMSE | 10.44 | 10.15 | -0.29 |
| Revenue Forecast | MAPE (%) | 0.486 | 0.182 | -0.304 |
| Customer Churn | AUC | ~1.0 | ~1.0 | 0 |

### 3. Thay đổi dữ liệu
- Chạy lại `generate_data_quality_report.py` + auto checks → `results/run_20251114_1902/data_checks/*`.
- Sinh biểu đồ phân bố `data_plots/sales_distribution.png`.

### 4. Phiên bản / metadata
- Model artifacts: `models/*_v2_(model|preprocessor|feature_schema|metrics).json`.
- Log tuning: `results/run_20251114_1902/tuning_logs/*.json`.
- Model cards mới: `docs/model_cards/*_v2.md`.

### 5. Hạn chế
- Churn quá hoàn hảo ⇒ phải kiểm tra target/feature leakage.
- Chưa tuning RL/Digital Twin; chưa cập nhật UI/test suite.

### 6. Gợi ý tiếp theo
1. Bổ sung unit/integration/regression tests → chạy sau mỗi tuning.
2. Điều tra nguyên nhân leakage cho churn (kiểm tra RFM snapshot, target label).
3. Thêm predictions_samples, charts (confusion matrix, actual vs predicted).
4. Cập nhật UI/metadata tự động đọc v2 metrics.
