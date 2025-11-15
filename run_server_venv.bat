@echo off
echo ========================================
echo Supply Chain Analytics Dashboard
echo ========================================
echo.
echo Kich hoat virtual environment...
call venv\Scripts\activate.bat
echo.
echo Dang khoi dong server...
echo.
echo Dashboard se chay tai: http://127.0.0.1:8000/dashboard
echo.
echo Nhan Ctrl+C de dung server
echo.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause

