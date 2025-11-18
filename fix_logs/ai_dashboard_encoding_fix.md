# Fix Log – AI Dashboard Encoding
- **Date:** 2025-11-15
- **Owner:** QA/Full-stack Taskforce
- **Issue:** `/dashboard/ai/{model_id}` returned `"utf-8' codec can't decode byte 0xd0..."`.
- **Root Cause:** `app/templates/ai/model_detail.html` stored as cp1252; Jinja expects UTF-8.
- **Resolution:** Converted template to UTF-8 and verified all templates decode correctly.
- **Verification:** Reloaded FastAPI server, opened `/dashboard/ai` and every model detail page; forms and tabs render without errors.
