@echo off
REM Script để chạy server với ML endpoints

echo ========================================
echo STARTING SERVER WITH ML ENDPOINTS
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Starting FastAPI server...
echo Dashboard: http://127.0.0.1:8000/dashboard
echo ML API Docs: http://127.0.0.1:8000/docs
echo.

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

