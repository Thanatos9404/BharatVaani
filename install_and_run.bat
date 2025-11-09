@echo off
echo ========================================
echo BharatVaani - Installation and Startup
echo ========================================
echo.

echo [1/3] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Could not activate virtual environment
    echo Please create venv first: python -m venv venv
    pause
    exit /b 1
)

echo [2/3] Installing Google Translate dependency...
pip install googletrans==4.0.0rc1
if errorlevel 1 (
    echo ERROR: Could not install googletrans
    pause
    exit /b 1
)

echo [3/3] Starting BharatVaani server...
echo.
echo ========================================
echo Server starting at http://localhost:5000
echo Press Ctrl+C to stop
echo ========================================
echo.

python main.py

pause
