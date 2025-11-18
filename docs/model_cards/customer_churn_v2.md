# Model Card: Customer Churn v2
- **Phiên bản:** v2 (XGBoost tuned)
- **Ngày train:** 2025-11-14
- **Metrics:** AUC ~1.0, PR-AUC ~1.0, F1 ~1.0 (cần kiểm tra leakage)
- **Data:** features_churn.parquet (~20k khách hàng)
- **Ghi chú:** Model saturate → cần kiểm tra target/feature leakage.
