# 🎮 CONTROL CENTER GUIDE

**Mục đích:** Hướng dẫn sử dụng Human-in-the-Loop Control Center.

---

## 📋 TỔNG QUAN

Control Center là nơi con người giám sát và kiểm soát các hành động của AI.

---

## 🎯 CHỨC NĂNG

### 1. Xem Pending Actions

**Endpoint:** `GET /os/actions/pending`

**Hiển thị:**
- Danh sách actions đang chờ phê duyệt
- Trạng thái: Pending / Approved / Rejected
- Thông tin: Action type, cost, confidence, reasoning

### 2. Approve Action

**Endpoint:** `POST /os/actions/approve`

**Body:**
```json
{
  "action_id": "action_123",
  "approved_by": "user_001",
  "notes": "Approved after review"
}
```

**Sau khi approve:**
- Action được thực thi
- Ghi log vào audit trail
- Notification gửi đi

### 3. Reject Action

**Endpoint:** `POST /os/actions/reject`

**Body:**
```json
{
  "action_id": "action_123",
  "rejected_by": "user_001",
  "reason": "Cost too high, not justified"
}
```

**Sau khi reject:**
- Action không được thực thi
- Ghi log vào audit trail
- AI có thể học từ rejection

### 4. Xem Reasoning Log

Mỗi action có reasoning log:
- Strategy được chọn
- Lý do chọn strategy
- Policy check results
- Safety check results

### 5. Xem Policy Check Results

- Policy rules checked
- Compliance status
- Violations (nếu có)
- Approval requirements

---

## 📊 DASHBOARD UI

### Pending Actions Table

| Action ID | Type | Cost | Confidence | Status | Actions |
|-----------|------|------|------------|--------|---------|
| action_001 | increase_inventory | $30,000 | 75% | Pending | Approve / Reject |
| action_002 | prioritize_vip | $3,000 | 80% | Pending | Approve / Reject |

### Action Details Panel

Khi click vào một action:
- **Strategy:** Chiến lược được chọn
- **Reasoning:** Lý do đề xuất
- **KPIs:** KPI ước tính
- **Risks:** Rủi ro
- **Policy Check:** Kết quả kiểm tra policy
- **Safety Check:** Kết quả kiểm tra safety

---

## 🔍 FILTERS

- **By Status:** Pending / Approved / Rejected
- **By Type:** Inventory / Pricing / Priority
- **By Cost:** < $10k / $10k-$50k / > $50k
- **By Confidence:** < 0.7 / 0.7-0.9 / > 0.9
- **By Date:** Today / This Week / This Month

---

## ⚙️ SETTINGS

### Mode Selection

- **Advisory:** Tất cả actions cần approval
- **Hybrid:** Một số actions tự động
- **Autonomous:** Hầu hết actions tự động

### Notification Settings

- Email notifications
- Dashboard alerts
- High-priority only

---

## 📝 BEST PRACTICES

1. **Review Regularly:**
   - Check pending actions hàng ngày
   - Review reasoning logs
   - Monitor policy violations

2. **Understand Context:**
   - Đọc reasoning summary
   - Xem policy check results
   - Kiểm tra safety checks

3. **Provide Feedback:**
   - Ghi notes khi approve/reject
   - Giải thích lý do
   - Giúp AI học từ feedback

4. **Monitor Trends:**
   - Xem approval/rejection ratio
   - Track policy violations
   - Review performance metrics

---

**Ngày tạo:** 2024  
**Phiên bản:** 1.0

