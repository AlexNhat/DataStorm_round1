"""
Router cung cấp API & UI cho Test Dashboard.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORT_JSON = BASE_DIR / "results" / "test_reports" / "test_report.json"
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

router = APIRouter()


def load_report():
    if not REPORT_JSON.exists():
        return {
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": "0s",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "categories": {},
            "tests": [],
            "coverage": {"percent": 0, "generated_file": ""},
        }
    return json.loads(REPORT_JSON.read_text(encoding="utf-8"))


@router.get("/test/report")
async def get_test_report():
    return JSONResponse(load_report())


@router.get("/test/report/detail/{test_name}")
async def get_test_detail(test_name: str):
    report = load_report()
    for test in report.get("tests", []):
        if test["name"] == test_name:
            return JSONResponse(test)
    raise HTTPException(status_code=404, detail="Test không tồn tại trong báo cáo")


@router.get("/test/run")
async def run_full_test_suite():
    script_path = BASE_DIR / "scripts" / "run_all_tests_and_build_report.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr or result.stdout)
    return JSONResponse(load_report())


@router.get("/dashboard/tests")
async def legacy_redirect(request: Request):
    """Giữ tương thích cũ: render test dashboard."""
    report = load_report()
    return templates.TemplateResponse(
        "test_dashboard.html",
        {"request": request, "report": report, "report_json_path": "/test/report"},
    )


@router.get("/dashboard/test-report")
async def test_dashboard_page(request: Request):
    report = load_report()
    return templates.TemplateResponse(
        "test_dashboard.html",
        {
            "request": request,
            "report": report,
            "report_json_path": "/test/report",
        },
    )
