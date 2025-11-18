# Dashboard UI

## Trang chính
- **/v8/dashboard**: Cognitive dashboard, quick actions, strategy generation (`/v8/strategies/generate`), summary cards với fallback context.
- **/os/control-center**: lấy pending actions từ `/os/actions/pending`, approve/reject `/os/actions/approve|reject`, history `/os/action/history`.
- **/dashboard/models**: Model Catalog đọc `GET /api/models` (model_registry.json) hiển thị badges, responsive table.
- **/dashboard/metrics**: đọc `results/metrics/global_dashboard_metrics.json` qua `/api/models/metrics/global`, hiển thị Chart.js cards + heatmap.

## Thành phần UI
- Layout dùng Tailwind + FontAwesome (xem `app/templates/base.html`).
- Component macro trong `app/templates/components/`: `card.html`, `button.html`, `badge_status.html`, `chart_block.html`, `table_responsive.html`.
- Dark mode toggle `#themeToggle`, sidebar responsive.

## Data binding
- Model Catalog & detail: `app/routers/models_registry.py` load registry.
- Metrics pages: `app/routers/models_metrics.py` + templates trong `app/templates/dashboard/metrics/`.
- Control Center: template `app/templates/control_center.html` + JS fetch `/os/actions/pending` & `/os/action/history`.

## API liên quan
- `/api/models` → JSON registry.
- `/api/models/metrics/global` → metrics summary.
- `/os/actions/pending`, `/os/actions/approve`, `/os/actions/reject`, `/os/action/history`.
- `/v8/dashboard/data`, `/v8/actions/trigger`, `/v8/strategies/generate`.

## UX highlight
- Card glassmorphism, hover `scale-105`, responsive grid 1-4 cột.
- Status badge: màu Success=green (#CCFBE1), Warn=#FFE8B3, Error=#FFCCCC.
- Heatmap & charts load sau khi trang render (Chart.js deferred script).
