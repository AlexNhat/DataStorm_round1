# AI Dashboard Encoding Fix

## Background
- Routes affected: `GET /dashboard/ai`, `GET /dashboard/ai/{model_id}`, and their dependent APIs under `/dashboard/ai/api/*`.
- The model detail screen consistently crashed with:
  ```
  "detail": "Error loading model detail: 'utf-8' codec can't decode byte 0xd0 in position 3488: invalid continuation byte"
  ```
- Root cause: `app/templates/ai/model_detail.html` had been saved in Windows-1252 (cp1252). FastAPI/Jinja always opens templates in UTF-8, so every request to `/dashboard/ai/{model_id}` failed while loading the template.

## Fix
1. Scanned every file under `app/templates/` to detect decode failures. Only `app/templates/ai/model_detail.html` raised a UnicodeDecodeError.
2. Converted the template to UTF-8 by reading the raw bytes with cp1252 and re-saving them with UTF-8 encoding. Verified that the entire template tree now loads through `path.read_text(encoding="utf-8")`.
3. No additional code changes were required because the registry/data files already use UTF-8.

## Verification
1. Ran `python -c "from pathlib import Path; [Path(p).read_text(encoding='utf-8') for p in Path('app/templates').rglob('*.html')]"` to confirm every template decodes without errors.
2. Started the FastAPI server (`uvicorn app.main:app --reload`) and loaded:
   - `/dashboard/ai` – overview renders without stack traces.
   - `/dashboard/ai/late_delivery`, `/dashboard/ai/inventory_rl`, `/dashboard/ai/pricing_elasticity`, etc. – each detail page renders metadata, tabs, and prediction form correctly.
3. Triggered the prediction form “Load sample data” on each page to ensure scripts still execute normally.

## How to Prevent Regression
- Always save templates and documentation files in UTF-8. Visual Studio Code and most IDEs support `File → Save with Encoding → UTF-8`.
- During code review, run a quick encoding check: `python -c "from pathlib import Path; Path('app/templates').rglob('*.html')"` to ensure no file raises `UnicodeDecodeError`.
- Add encoding validations to CI by running the same script above as part of lint/testing steps.
