@echo off
chcp 65001 > nul
title AI Debug Tool
echo ==========================================
echo    AI Debug Tool Launcher
echo ==========================================
echo.

set VENV_DIR=venv
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo.
    pause
    exit /b 1
)

echo [INFO] Python detected:
python --version
echo.

if not exist "%PYTHON_EXE%" (
    echo [INFO] Creating virtual environment...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
    echo.
)

echo [INFO] Checking dependencies...
"%PYTHON_EXE%" -c "import requests, pydantic" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    "%PYTHON_EXE%" -m pip install --upgrade pip -q
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed
    echo.
)

echo [INFO] Starting AI Debug Tool...
echo ==========================================
echo.
"%PYTHON_EXE%" ai_debug_tool.py

if errorlevel 1 (
    echo.
    echo [ERROR] Program exited with error
    pause
)
