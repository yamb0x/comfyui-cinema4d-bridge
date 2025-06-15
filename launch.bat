@echo off
echo Starting ComfyUI to Cinema4D Bridge...
echo.

REM Change to script directory first
cd /d "%~dp0"

REM Try to activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Using system Python
)

echo.
echo Current directory: %CD%

REM Set UTF-8 encoding
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

echo Launching application...
python main.py
pause
