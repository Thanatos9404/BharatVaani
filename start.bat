@echo off
REM BharatVaani Startup Script for Windows
echo ========================================
echo   🇮🇳 BharatVaani News Platform
echo   Starting Application...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [!] Virtual environment not found.
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [X] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo [*] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Setup directories
echo [*] Setting up directories...
python setup_directories.py

REM Check for .env file
if not exist ".env" (
    echo.
    echo [!] WARNING: .env file not found!
    echo [!] Please create a .env file based on .env.example
    echo [!] Add your API keys before running the application.
    echo.
    pause
)

REM Download NLTK data if needed
echo [*] Checking NLTK dependencies...
python -c "import nltk; nltk.download('vader_lexicon', quiet=True)" 2>nul

REM Start the application
echo.
echo [✓] Starting BharatVaani...
echo [*] Application will be available at: http://localhost:5000
echo [*] Press Ctrl+C to stop the server
echo.
python main.py

pause
