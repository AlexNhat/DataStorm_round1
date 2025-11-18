@echo off
REM Script để chạy toàn bộ ML pipeline: build features và train models

echo ========================================
echo ML PIPELINE - BUILD FEATURES & TRAIN MODELS
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo [1/4] Building Feature Store...
python scripts/preprocess_and_build_feature_store.py
if errorlevel 1 (
    echo ERROR: Failed to build feature store
    pause
    exit /b 1
)

echo.
echo [2/4] Training Logistics Delay Model...
python scripts/train_model_logistics_delay.py
if errorlevel 1 (
    echo WARNING: Failed to train logistics delay model
)

echo.
echo [3/4] Training Revenue Forecast Model...
python scripts/train_model_revenue_forecast.py
if errorlevel 1 (
    echo WARNING: Failed to train revenue forecast model
)

echo.
echo [4/4] Training Churn Model...
python scripts/train_model_churn.py
if errorlevel 1 (
    echo WARNING: Failed to train churn model
)

echo.
echo ========================================
echo ML PIPELINE COMPLETED!
echo ========================================
echo.
echo You can now start the server and test ML APIs:
echo   uvicorn app.main:app --reload
echo.
pause

