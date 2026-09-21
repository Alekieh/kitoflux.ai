@echo off
title KITOFLUX.AI - Real-Time Stealth Copilot
echo ===================================================
echo   KITOFLUX.AI | FLOW. ADAPT. EXECUTE.
echo ===================================================
echo [1/3] Checking environment...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ is required. Please install Python from python.org.
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is required. Please install Node.js from nodejs.org.
    pause
    exit /b 1
)

echo [2/3] Initializing Python backend...
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt --quiet

echo Launching Python Kernel on http://127.0.0.1:8765...
start /b python main.py

cd ..\frontend
echo [3/3] Launching Electron Stealth HUD...
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install --quiet
)

npm run electron:dev
pause
