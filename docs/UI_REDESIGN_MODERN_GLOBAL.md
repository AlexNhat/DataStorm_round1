# UI Redesign (Modern GLOBAL Layout)

## Goals
- Provide a consistent, responsive experience for `/v8/dashboard`, `/os/control-center`, `/dashboard/models`, and `/dashboard/metrics`.
- Standardize on TailwindCSS + FontAwesome with reusable macro components for cards, buttons, badges, charts, and tables.
- Ensure dark-mode friendly colors, hover animations, and responsive breakpoints (mobile → desktop).

## Layout Fundamentals
- `app/templates/base.html` hosts global shell: fixed sidebar, sticky header, dark-mode toggle, and Chart.js/Tailwind imports.
- Main content uses a 12-column responsive grid via Tailwind utilities. Sidebar hides on mobile via toggle button.
- All templates extend `base.html` and inherit fonts + theme behavior.

## Reusable Components
Located under `app/templates/components/`:
- `card.html` – glassmorphic cards with optional icon, subtitle, and body slot.
- `button.html` – gradient primary / secondary variants with hover scale animation.
- `badge_status.html` – colored pills (Success/Warn/Error) with dot indicators.
- `chart_block.html` – standardized card wrapper for Chart.js canvases.
- `table_responsive.html` – rounded tables with overflow-x handling and empty-state messaging.

## Page Updates
- **Model Catalog** (`dashboard/models_list.html`): imports table/badge components, responsive cards, tooltip-ready statuses.
- **Model Detail** (`dashboard/model_detail.html`): uses card macro + badges, provides quick artifact links and operational notes.
- **Metrics pages** (`dashboard/metrics/*`): each page relies on `chart_block` and inherits JS from overview page.
- **Control Center** (`control_center.html`): KPI grid now uses `card.card` macros; strings standardized to English to avoid encoding issues.
- **Cognitive dashboard**: safeguards (`summary_context`) prevent undefined JSON serialization.

## Visual Enhancements
- Rounded-2xl / 3xl surfaces with subtle drop shadows for depth.
- Gradient hero cards and highlight badges for statuses.
- Hover `scale-[1.02]` animations for actionable elements.
- Heatmap + chart tooltips leverage Chart.js defaults.

## Responsive / Accessibility Notes
- Tables and heatmaps include `overflow-x-auto` wrappers.
- Sidebar toggles on smaller screens via `#mobileNavToggle`.
- All controls have focus outlines (`focus-visible:ring`).
- Text content kept ASCII-first to avoid encoding drift.

## Implementation Checklist
1. Import needed macros at the top of each template (`{% import "components/card.html" as card %}` etc.).
2. Wrap hero info with `.ui-card` for consistent spacing.
3. Use `table.table([...])` when listing registry/model data to keep responsive behavior.
4. Attach JS in `{% block extra_scripts %}` with `{{ super() }}` to retain base scripts.
5. Run `scripts/generate_dashboard_metrics.py` whenever new metrics cards require fields.

## Future Enhancements
- Add Alpine.js micro-interactions for filter panels.
- Extend `button` macro with loading states for API actions.
- Bundle Tailwind via Vite for production builds if CDN becomes constrained.
