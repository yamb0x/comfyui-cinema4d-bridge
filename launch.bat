@echo off
echo Starting ComfyUI to Cinema4D Bridge...
echo.

REM Change to script directory first
cd /d "%~dp0"

REM Check if virtual environment exists and use it, otherwise use system Python
if exist "venv\Scripts\python.exe" (
    echo Activating virtual environment...
    set PYTHON_EXECUTABLE=venv\Scripts\python.exe
) else (
    echo Virtual environment not found, using system Python
    set PYTHON_EXECUTABLE=python
)

echo.
echo Current directory: %CD%

REM Set UTF-8 encoding
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

echo Launching application...
echo Using Python: %PYTHON_EXECUTABLE%
%PYTHON_EXECUTABLE% main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred while running the application.
    echo Error code: %ERRORLEVEL%
    echo.
    echo Troubleshooting:
    echo 1. Make sure Python is installed and added to PATH
    echo 2. Check if all dependencies are installed: pip install -r requirements.txt
    echo 3. Try recreating the virtual environment
)

pause
