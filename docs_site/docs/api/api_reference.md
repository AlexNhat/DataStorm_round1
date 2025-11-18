# API Reference

## Model Registry
### `GET /api/models`
- Returns model registry list (name, version, accuracy, region, status, artifacts).
- Source: `app/routers/models_registry.py`.

### Response
```json
{
  "status": "success",
  "models": [
    {
      "name": "Inventory Optimizer RL",
      "version": "v5.3",
      "region": "GLOBAL",
      "accuracy": 0.9988,
      "status": "Success",
      "note": "Updated using global merged supplychain-weather dataset..."
    }
  ]
}
```

## Model Metrics
### `GET /api/models/metrics/global`
- Summary JSON cho dashboard metrics (`results/metrics/global_dashboard_metrics.json`).

## Cognitive dashboard
- `GET /v8/dashboard` → Template.
- `GET /v8/dashboard/data` → snapshot summary.
- `POST /v8/strategies/generate` → sinh chiến lược, trả danh sách card.
- `POST /v8/actions/trigger` → thực thi quick action.

## Control Center / OS
### Pending actions
`GET /os/actions/pending?model_id=&action_type=&priority=&status=&limit=&offset=`
→ trả JSON `{ status, pending_actions: [...] }` (bao gồm policy_check, safety_check, reasoning, payload).

### Approve/Reject
`POST /os/actions/approve`
```json
{
  "action_id": "ACT-2025-001",
  "approved_by": "ops_lead",
  "notes": "Ready to execute"
}
```
`POST /os/actions/reject`
```json
{
  "action_id": "ACT-2025-001",
  "rejected_by": "ops_lead",
  "reason": "Budget exceeded",
  "notes": "Hold for Q2"
}
```
Response chung:
```json
{
  "status": "success",
  "action_id": "ACT-2025-001",
  "decision": "approved",
  "message": "Action approved",
  "processed_at": "2025-11-15T03:12:00Z"
}
```

### History
`GET /os/action/history?from=&to=&status=&type=&model_id=&category=&limit=&offset=`
→ trả `{ status, history: [...], aggregations: { by_hour: [...], by_type: [...] } }`.

## Dashboard/AI
- `/dashboard`, `/dashboard/ai`, `/dashboard/models`, `/dashboard/metrics` → template responses.
- `/dashboard/models/{slug}` → chi tiết model.

## Health endpoints
- `/health` (simple status).
- `/os/status`, `/os/actions/pending`, `/os/actions/approve`, `/os/actions/reject` (xem trên).

## Notes
- Backend dùng FastAPI; check Swagger tại `/docs` hoặc `/redoc`.
- Các endpoint ML khác (digital twin, self-learning, etc.) nằm trong `app/routers/` tương ứng (ai_dashboard, ml_api, digital_twin_api...).
