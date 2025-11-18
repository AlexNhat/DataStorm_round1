# UI Components

## Base layout
- File: `app/templates/base.html`
- Bao gồm TailwindCDN, Chart.js, FontAwesome, dark-mode toggle, sidebar nav, sticky header.

## Components macro (Jinja)
| File | Mục đích |
| --- | --- |
| `components/card.html` | Card glassmorphic, title + subtitle + icon slot |
| `components/button.html` | Button variants (primary gradient, secondary glass) với hover scale |
| `components/badge_status.html` | Badge Success/Warn/Error + dot màu |
| `components/chart_block.html` | Khung Chart.js chuẩn |
| `components/table_responsive.html` | Table responsive + empty-state |

## Pages sử dụng
- `dashboard/models_list.html`, `model_detail.html`
- `dashboard/metrics/*.html`
- `control_center.html`, `cognitive_dashboard.html`

## Styling
- Border radius lớn (rounded-2xl / 3xl), shadow sâu, gradient subtle trong hero.
- Animation: `.ui-card:hover` translate/scale nhẹ; button ripple qua CSS transitions.
- Responsive: grid `grid-cols-1 md:grid-cols-2 xl:grid-cols-4`, table `overflow-x-auto`.

## Dark mode
- `body` class `dark` toggle via `localStorage`. Colors `dark:bg-slate-900`, etc.

## Assets
- Fonts: Inter (Google Fonts).
- Icons: FontAwesome 6.5.1.

## Best practices
- Import macro ở đầu template: `{% import "components/card.html" as card %}`.
- Khi render data table, dùng macro `table.table(headers, rows)` để đảm bảo responsive.
- Tải JS trong `{% block extra_scripts %}` và gọi `{{ super() }}` để giữ script chung.
