@echo off
title CleanSpot - Waste Reporter
echo ========================================================
echo Starting CleanSpot Waste Pinpoint Frontend on Localhost...
echo ========================================================
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python detected. Starting server with auto-browser launch...
    python server.py
    pause
    exit /b
)

REM Fallback if Python is not installed
echo Python not found. Trying npx serve...
npx --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    npx serve . -l 8000
    pause
    exit /b
)

echo Neither Python nor Node.js were found.
echo Opening index.html directly in your default browser...
start index.html
pause
