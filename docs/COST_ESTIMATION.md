# 💰 ƯỚC TÍNH CHI PHÍ TRIỂN KHAI & VẬN HÀNH HỆ AI SUPPLY CHAIN (V1 → V9)

**Ngày ước tính:** 14/11/2025  
**Người lập:** Principal AI Architect + MLOps Director + AI Governance Specialist  
**Phạm vi:** FastAPI backend, Digital Twin (V7), Cognitive Layer (V8), Autonomous OS (V9), Self-learning V6, Multi-model catalog.

---

## 📋 MỤC LỤC
1. [Chi Phí Hạ Tầng](#1-chi-phí-hạ-tầng)
2. [Chi Phí Vận Hành](#2-chi-phí-vận-hành)
3. [Chi Phí Nhân Sự](#3-chi-phí-nhân-sự)
4. [Chi Phí Bảo Trì & Cải Tiến](#4-chi-phí-bảo-trì--cải-tiến)
5. [Dự Toán Tổng & Lộ Trình Ngân Sách](#5-dự-toán-tổng--lộ-trình-ngân-sách)

---

## 1. CHI PHÍ HẠ TẦNG

### 1.1. Tính toán mô hình / ETL / RL / Digital Twin

| Tác vụ | Cấu hình tham chiếu | Tần suất | Cloud (USD/tháng) | On-prem (khấu hao) |
|--------|--------------------|----------|--------------------|--------------------|
| Train phân loại/dự báo (3 models) | 4 vCPU, 16GB RAM (t3.xlarge) | 6-8h/tuần | $80-120 | $250-350 |
| Pipeline ETL + Feature Store | 2 vCPU, 8GB RAM (t3.large) | 8h/tuần | $40-60 | $150-200 |
| RL + Digital Twin simulation | 8 vCPU, 32GB RAM (m7i.2xlarge) | 20h/tháng | $180-260 | $450-650 |
| GPU cho RL phức tạp / LLM planner (T4) | 1x T4 (g6.xlarge) | ad-hoc | $250-320 | $600-800 |
| Online learning + drift jobs | 2 vCPU, 8GB RAM (t3.large) | 24/7 | $60-80 | $200-250 |
| **Tổng (cloud)** |  |  | **$610-840/tháng** | **$1,650-2,250/tháng** |

> Lưu ý: Có thể ghép nhiều workload lên cùng cụm Kubernetes để tối ưu.

### 1.2. Lưu trữ dữ liệu, artifacts, logs

| Hạng mục | Dung lượng hiện tại | Dự phóng 12 tháng | Cloud (USD/tháng) | On-prem |
|----------|--------------------|-------------------|--------------------|---------|
| Data raw + processed | 60 GB | 120 GB | $2-4 (S3/Blob) | $8-12 |
| Feature Store parquet | 15 GB | 40 GB | $0.5-1 | $3-5 |
| Model artifacts + registry | 8 GB | 20 GB | $0.3-0.8 | $2-4 |
| Logs (application + audit) | 30 GB/tháng | 50 GB/tháng | $1-2 | $5-8 |
| Results run (metrics/charts) | 10 GB/run | 30 GB | $0.4-0.6 | $2-3 |
| **Tổng** |  |  | **$4.2-8/tháng** | **$20-32/tháng** |

### 1.3. Streaming & cache (tuỳ mode)

| Thành phần | Cấu hình | Cloud | On-prem |
|------------|----------|-------|---------|
| Redis cache (2GB RAM) | ElastiCache / Azure Cache | $20-40 | $60-100 |
| Kafka / Redpanda (3 nodes, 4GB) | Managed MSK / Confluent Cloud | $200-320 | $350-550 |
| Feature ingestion queue (SQS/PubSub) | 1M msgs/tháng | $10-20 | N/A |
| **Tổng (nếu cần realtime)** |  | **$230-380/tháng** | **$410-650/tháng** |

### 1.4. Containerization & orchestration

| Thành phần | Cloud | On-prem |
|------------|-------|---------|
| Kubernetes control plane (EKS/GKE/AKS) | $74 (flat) | $0 (DIY) |
| Worker nodes (3x 4 vCPU/16GB) | $300-420 | $650-900 |
| Container registry (ECR/ACR) | $1-3 | $0 (self-host) |
| CI runners (GitHub Actions, GitLab) | $40-80 | $50-100 |
| **Tổng** | **$415-577/tháng** | **$700-1,000/tháng** |

> Nếu dùng Docker Compose single VM có thể giảm xuống còn ~$120/tháng nhưng giới hạn khả năng scale.

---

## 2. CHI PHÍ VẬN HÀNH

### 2.1. Monitoring + observability

| Hạng mục | Công cụ gợi ý | Chi phí cloud | Tự host |
|----------|---------------|---------------|---------|
| Metrics + dashboards | Prometheus + Grafana Cloud / Datadog | $80-250 | $40-80 |
| Log aggregation | Loki / ELK / CloudWatch | $60-180 | $50-120 |
| Error tracking | Sentry / Rollbar | $29-79 | $0-30 |
| Synthetic tests & uptime | BetterStack / Pingdom | $20-50 | $10 |
| OTEL tracing | Lightstep / NewRelic | $60-150 | $40-80 |
| **Tổng** |  | **$249-709/tháng** | **$140-320/tháng** |

### 2.2. Drift detection, fairness, explainability

- Compute để chạy Evidently + SHAP: $40-70/tháng (EC2 c7a.large ~ 4h/ngày).
- Lưu báo cáo drift/fairness (`results/run_YYYYMMDD/`): $5/tháng.
- Human review time (QA data scientist 10h/tháng): $800-1,200/tháng.

### 2.3. Auto retrain jobs + scheduling

- Compute: đã tính trong hạ tầng (mục 1.1).
- Chi phí orchestration (Prefect Cloud / Airflow managed): $300-500/tháng hoặc tự host $80-150.
- Storage/runtimes cho `logs/os_decisions`, `logs/audit`: $5-10/tháng.

### 2.4. Tổng vận hành

- **Phương án tiết kiệm (self-host phần monitoring):** $1,100-1,450/tháng.
- **Phương án fully managed:** $1,500-2,300/tháng (bao gồm observability SaaS, scheduler managed, human QA).

---

## 3. CHI PHÍ NHÂN SỰ

| Vai trò | Nhiệm vụ chính | Mô hình tối thiểu | Chi phí ước tính/tháng |
|---------|----------------|-------------------|------------------------|
| **Lead AI Engineer / Architect** | Thiết kế mô hình, mã nguồn chính, Cognitive layer | Full-time | $8,500-13,500 |
| **Data Engineer** | ETL, Feature Store, data quality, streaming | 0.6 FTE | $4,000-6,500 |
| **MLOps/DevOps** | Hạ tầng, CI/CD, monitoring, security | 0.5-1 FTE | $4,500-8,500 |
| **Frontend & UX Dashboard** | Duy trì `app/templates`, Tailwind, Chart.js | 0.4 FTE | $3,000-4,500 |
| **Domain Expert / Governance** | Policy, phê duyệt, audit, HITL | 0.3 FTE | $2,500-4,000 |
| **Data Analyst / QA** | Soát output, drift/fairness review | 0.3 FTE | $2,000-3,500 |
| **Tổng (core team 3-4 người)** |  |  | **$24,500-40,500/tháng** |

> Nếu cần tốc độ cao (train RL, digital twin phức tạp, mở rộng UI) ngân sách nhân sự có thể tăng lên $45-55K/tháng.

---

## 4. CHI PHÍ BẢO TRÌ & CẢI TIẾN

| Hạng mục | Tần suất | Ước tính/tháng |
|----------|----------|----------------|
| Refresh mô hình chu kỳ 3-6 tháng (data prep + tuning + QA) | 2 lần/năm, mỗi lần 2 tuần nhân sự | $1,200-2,000 |
| Tối ưu mã & refactor (V8/V9, orchestrator, policy engine) | 1-2 tuần/tháng | $2,000-3,000 |
| Cập nhật dependency, vá bảo mật, test môi trường (Python 3.12, requirements) | 3-4 ngày/tháng | $1,000-1,400 |
| Kiểm thử & audit (penetration, compliance, HITL drill) | hàng quý | $800-1,200 |
| **Tổng bảo trì/cải tiến** |  | **$5,000-7,600/tháng** |

---

## 5. DỰ TOÁN TỔNG & LỘ TRÌNH NGÂN SÁCH

### 5.1. Tổng hợp theo cấu hình

| Cấu hình | Hạ tầng | Vận hành | Nhân sự | Bảo trì | Tổng / tháng |
|----------|---------|----------|---------|---------|--------------|
| **Minimal (Pilot)** | $650 | $1,100 | $18,000 | $3,500 | **$23,250** |
| **Core Production (khuyến nghị)** | $900-1,200 | $1,500-2,000 | $24,500-33,000 | $5,000-6,000 | **$31,900-42,200** |
| **Full Enterprise (HA + realtime + RL/GPU)** | $1,600-2,300 | $2,000-3,000 | $35,000-50,000 | $6,000-8,000 | **$44,600-63,300** |

### 5.2. Chi phí 1/6/12 tháng (core production)

- **1 tháng:** $32K - $42K  
- **6 tháng:** $192K - $252K  
- **12 tháng:** $384K - $504K

### 5.3. Phân bổ %

- Nhân sự & vận hành: ~80% (do yêu cầu chuyên môn cao, HITL, governance)  
- Hạ tầng: 5-7%  
- Observability & bảo trì: 13-15%

### 5.4. Khuyến nghị tối ưu chi phí
1. **Ưu tiên cloud spot / saving plan** cho RL & Digital Twin (tiết kiệm 30-40%).  
2. **Gom workload lên Kubernetes auto-scale** → giảm idle.  
3. **Tự host monitoring** giai đoạn đầu (Prometheus/Grafana + Loki).  
4. **Chuẩn hóa pipeline** (scripts/run_all_models_evaluation.py, `results/run_YYYYMMDD/`) để giảm nhân công thủ công.  
5. **Gradual LLM integration**: dùng LLM hosted (Azure OpenAI pay-per-use) thay vì GPU liên tục.

### 5.5. ROI & Break-even
- Nếu hệ thống giúp giảm 5% chi phí supply chain và doanh thu hiện ~20M USD/năm, tiết kiệm ~1M USD → hoàn vốn sau 1-2 quý.  
- Đo tác động qua KPIs: tồn kho, lead time, churn, độ chính xác forecast, tốc độ ra quyết định.

---

**Ngày cập nhật:** 14/11/2025  
**Phiên bản tài liệu:** 2.0  
**Lộ trình tiếp theo:** cập nhật lại khi kết quả `results/run_YYYYMMDD/` có dữ liệu chi tiết về compute time & nhân sự thực tế. 

