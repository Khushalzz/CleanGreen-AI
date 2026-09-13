@echo off
title Clean and Green Tech - Vision AI Server
echo ======================================================================
echo Starting Clean and Green Tech (Backend + Vision AI Engine)...
echo ======================================================================
cd /d "%~dp0"

python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python detected. Starting server with headless agy AI pipeline...
    python server.py
    pause
    exit /b
)

echo Python was not found in your PATH.
pause
