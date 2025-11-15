# ⚠️ PHÂN TÍCH RỦI RO HỆ THỐNG AI V1 → V9

**Ngày phân tích:** 14/11/2025  
**Phân tích bởi:** Principal AI Architect + MLOps Director + AI Governance Specialist  
**Phiên bản hệ thống:** V9.0.0 (FastAPI + Digital Twin + Cognitive OS)

---

## 📋 MỤC LỤC
1. [Rủi Ro Kỹ Thuật](#1-rủi-ro-kỹ-thuật)
2. [Rủi Ro Vận Hành](#2-rủi-ro-vận-hành)
3. [Rủi Ro Kinh Doanh](#3-rủi-ro-kinh-doanh)
4. [Rủi Ro Đạo Đức](#4-rủi-ro-đạo-đức)
5. [Rủi Ro Pháp Lý](#5-rủi-ro-pháp-lý)
6. [Tổng Kết & Khuyến Nghị](#6-tổng-kết--khuyến-nghị)

---

## 1. RỦI RO KỸ THUẬT

### 1.1. Data Leakage
- **Mức độ:** 🔴 **CAO**
- **Mô tả:** Dữ liệu logistics + weather được merge thủ công, nếu dùng sai khóa hoặc tạo rolling feature không đúng sẽ lộ thông tin tương lai cho model (đặc biệt trong `scripts/preprocess_and_build_feature_store.py`). Các file ở `notebooks/` vẫn còn code random split.
- **Tác động:** Model báo hiệu suất cao giả tạo, dự báo sai, gây mất niềm tin.
- **Giảm thiểu hiện tại:** Train scripts chính đã dùng time-based split.
- **Khuyến nghị:** Thêm automated leakage checks, lint notebooks, dùng feature store versioning (DVC/Feast), enforce review domain expert trước khi thêm feature mới.

### 1.2. Model Drift
- **Mức độ:** 🔴 **CAO**
- **Mô tả:** Hệ thống phục vụ supply chain, data drift diễn ra hàng tuần. Module V6 (drift detection, continual learning) mới ở mức code, chưa nối pipeline thực sự.
- **Tác động:** Forecast, churn, late delivery giảm chính xác → quyết định kinh doanh sai.
- **Giảm thiểu hiện tại:** Có module River/online learning, script `scripts/online_learning/*`.
- **Khuyến nghị:** Tích hợp drift score vào orchestrator (`core/os_orchestrator.py`), cấu hình cảnh báo, auto-retrain với guardrails và human approval.

### 1.3. Quá Nhiều Models → Khó Maintain
- **Mức độ:** 🟡 **TRUNG BÌNH**
- **Mô tả:** V1–V9 gồm >10 models (Forecast, Churn, Delay, RL, Digital Twin, Cognitive...). Model Registry (`app/services/model_registry.py`) mới chỉ giữ metadata tĩnh.
- **Tác động:** Khó theo dõi version, metrics, chi phí compute; khi một model lỗi kéo theo pipeline khác.
- **Khuyến nghị:** Triển khai MLflow/Weights & Biases, chuẩn hóa logging metrics JSON trong `results/`, xây dashboard giám sát model lifecycle, gom dependencies để tránh drift thư viện.

### 1.4. RL / Digital Twin Sai Thực Tế
- **Mức độ:** 🟡 **TRUNG BÌNH-CAO**
- **Mô tả:** RL và Digital Twin nằm ở `rl/` và `engines/digital_twin/`. Chưa có checkpoint, reward/cost chưa calibrate, Digital Twin chưa so với dữ liệu thật.
- **Tác động:** OS Orchestrator dựa vào kết quả mô phỏng sai → đề xuất chiến lược tệ hoặc tốn kém.
- **Khuyến nghị:** Calibrate scenario JSON bằng dữ liệu lịch sử, ghi nhận KPI thực tế để so sánh, thêm sensitivity analysis, log reward curve/simulation accuracy vào `results/`.

### 1.5. Latency Inference & Dashboard
- **Mức độ:** 🟢 **THẤP-TRUNG BÌNH**
- **Mô tả:** FastAPI + CPU inference khá nhanh nhưng khi chạy SHAP/RL/Digital Twin thì request blocking. UI (`app/templates/ai/model_detail.html`) render nhiều chart giả lập.
- **Tác động:** Người dùng phải chờ lâu hoặc request timeout khi call /os hành động phức tạp.
- **Khuyến nghị:** Thêm worker async (Celery/BackgroundTasks), caching (Redis), queue action trong orchestrator, preload model vào memory.

---

## 2. RỦI RO VẬN HÀNH

### 2.1. Thiếu Nhân Sự Vận Hành Pipeline
- **Mức độ:** 🟡 **TRUNG BÌNH**
- `core/os_orchestrator.py` chỉ chạy khi khởi động thủ công, chưa có scheduler thực (Airflow/Prefect). Khi pipeline fail không ai giám sát.
- **Khuyến nghị:** Thiết lập scheduler chính thức, runbook + on-call rotation, dashboard trạng thái pipeline.

### 2.2. Human-in-the-Loop Chưa Đủ Chặt
- **Mức độ:** 🟡 **TRUNG BÌNH**
- Control Center hiển thị pending actions nhưng chưa có workflow bắt buộc (ví dụ C-level duyệt > $1M). Autonomous mode có nguy cơ bỏ qua review.
- **Khuyến nghị:** Áp chính sách approval matrix, log người duyệt, enforce Hybrid mode cho high risk SKUs, training đội vận hành đọc reasoning logs.

### 2.3. Thiếu Monitoring/Alerting
- **Mức độ:** 🔴 **CAO**
- Chưa có Sentry, Prometheus, log aggregation; file log nằm trong `logs/` rời rạc.
- **Khuyến nghị:** Triển khai stack quan sát (Grafana + Loki hoặc ELK), health check endpoints, cảnh báo Slack/email.

---

## 3. RỦI RO KINH DOANH

### 3.1. Model Sai → Ảnh Hưởng Supply Chain
- **Mức độ:** 🔴 **CAO**
- Nếu dự báo giao hàng trễ sai → không điều phối vận tải; revenue forecast sai → tồn kho lệch; churn sai → lãng phí marketing.
- **Khuyến nghị:** Thiết lập SLA cho model, gắn confidence interval vào dashboard, fallback rule-based khi model dưới chuẩn, human review output quan trọng.

### 3.2. Forecast Sai → Overstock/Stockout
- **Mức độ:** 🔴 **CAO**
- Chưa có uncertainty quantification, scenario planning mới dừng ở JSON manual.
- **Khuyến nghị:** Bổ sung fan-chart/interval, scenario stress test tự động, Digital Twin phải chạy song song để xác nhận.

### 3.3. Churn Model Sai → Marketing Lãng Phí
- **Mức độ:** 🟡 **TRUNG BÌNH**
- Thiếu cost-sensitive metric, ROI tracking.
- **Khuyến nghị:** Tính LTV/CPA, threshold động, gắn pipeline marketing automation với guardrail.

---

## 4. RỦI RO ĐẠO ĐỨC

### 4.1. Bias Theo Region/Country
- **Mức độ:** 🟡 **TRUNG BÌNH**
- Dataset logistics không cân bằng vùng; rule OS có thể ưu ái khu vực có dữ liệu nhiều hơn.
- **Khuyến nghị:** Chạy fairness audit (equalized odds), log demographic attributes (ẩn danh), cho phép override policy khi bias phát hiện.

### 4.2. AI Vượt Policy/Hạn Mức
- **Mức độ:** 🟡 **TRUNG BÌNH**
- `core/governance/policies.yaml` chưa bao phủ tất cả edge cases (ví dụ dynamic pricing > ±5%).
- **Khuyến nghị:** Mở rộng rule base, thêm unit test cho policy engine, schedule review với legal/compliance.

### 4.3. Explainability / Accountability
- **Mức độ:** 🟡 **TRUNG BÌNH**
- V8 reasoning báo cáo bằng tiếng Việt thân thiện nhưng chưa liên kết SHAP/feature importance thực tế.
- **Khuyến nghị:** Tạo SHAP pipeline, hiển thị top features trong Control Center, lưu lại explanation cùng action log.

---

## 5. RỦI RO PHÁP LÝ

### 5.1. Dữ Liệu Cá Nhân & Quy Định
- **Mức độ:** 🟡 **TRUNG BÌNH**
- Data chứa ID khách hàng, địa lý; chưa có quy trình ẩn danh, consent, data residency.
- **Khuyến nghị:** Áp dụng tokenization, lưu consent metadata, rà soát GDPR/CCPA; cập nhật `docs/ETHICS_AND_COMPLIANCE.md` theo chính sách mới.

### 5.2. Data Retention & Audit
- **Mức độ:** 🟢 **THẤP-TRUNG BÌNH**
- Chưa có policy auto-delete logs/results; audit log JSON chưa immutable.
- **Khuyến nghị:** Định nghĩa retention (12/24 tháng), tự động xóa/archival, lưu audit log vào storage chỉ ghi (S3 versioned, Azure Blob WORM).

### 5.3. Nghĩa Vụ Audit Khi Sự Cố
- **Mức độ:** 🟡 **TRUNG BÌNH**
- `logs/audit/*.json` + `docs/AUDIT_OVERVIEW.md` mới ở mức mô tả; chưa có công cụ tìm kiếm, không ghi người duyệt/LLM prompt.
- **Khuyến nghị:** Triển khai kho audit (Elasticsearch/Delta), lưu metadata (model version, data hash, rationale, approver), cung cấp dashboard truy vấn.

---

## 6. TỔNG KẾT & KHUYẾN NGHỊ

### Risk Matrix
| Rủi ro | Xác suất | Tác động | Mức độ | Ưu tiên |
|--------|----------|----------|--------|---------|
| Model drift & thiếu monitoring | Cao | Cao | 🔴 | P0 |
| Data leakage | Trung bình | Cao | 🔴 | P0 |
| Forecast sai → supply chain | Trung bình | Rất cao | 🔴 | P0 |
| Thiếu monitoring/alerting | Cao | Cao | 🔴 | P0 |
| RL/Digital Twin không chuẩn | Thấp-Trung bình | Cao | 🟡 | P1 |
| Thiếu HITL & policy coverage | Trung bình | Cao | 🟡 | P1 |
| Bias vùng | Trung bình | Trung bình | 🟡 | P1 |
| Latency/scale | Thấp | Trung bình | 🟢 | P2 |
| Data retention/audit tooling | Thấp | Trung bình | 🟢 | P2 |

### Hành động ưu tiên
1. **Quan trắc & Drift:** Triển khai monitoring real-time, alert, drift dashboard, auto-retrain guardrail.
2. **Governance:** Mở rộng policy YAML + unit test, enforce human approval cho action > ngưỡng.
3. **Digital Twin/RL Validation:** Calibrate, log reward/simulation accuracy, so sánh KPI thực tế.
4. **Explainability & Bias:** Thêm SHAP/LIME, fairness audit, log explanation kèm mọi quyết định.
5. **Legal & Audit:** Xây retention policy, lưu audit immutable, chuẩn bị gói chứng cứ khi incident.

### Lộ trình khuyến nghị
- **Trong 1 tuần:** Bật monitoring/alert cơ bản, đảm bảo HITL bắt buộc, rà soát feature leakage.
- **Trong 1 tháng:** Tích hợp drift detection vào orchestrator, cập nhật policy engine, triển khai fairness + explainability tối thiểu.
- **Trong 3 tháng:** Calibrate Digital Twin/RL, dựng MLflow registry, hoàn thiện audit store, thực thi data retention và privacy review định kỳ.

---

**Ngày cập nhật:** 14/11/2025  
**Phiên bản tài liệu:** 2.0

