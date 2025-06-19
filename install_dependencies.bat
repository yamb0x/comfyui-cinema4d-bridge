@echo off
echo Installing dependencies for ComfyUI to Cinema4D Bridge...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please run setup_windows_env.bat first
    pause
    exit /b 1
)

echo Using virtual environment Python...
echo.

echo Installing core dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip

echo Installing PySide6 (Qt6 for Python)...
venv\Scripts\python.exe -m pip install PySide6>=6.6.0

echo Installing qasync (Qt async integration)...
venv\Scripts\python.exe -m pip install qasync>=0.27.0

echo Installing loguru (logging)...
venv\Scripts\python.exe -m pip install loguru>=0.7.2

echo Installing remaining dependencies from requirements.txt...
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo Testing installation...
echo.

venv\Scripts\python.exe -c "import PySide6; print('✅ PySide6 OK')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ PySide6 not working
) else (
    echo ✅ PySide6 working
)

venv\Scripts\python.exe -c "import qasync; print('✅ qasync OK')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ qasync not working
) else (
    echo ✅ qasync working
)

venv\Scripts\python.exe -c "import loguru; print('✅ loguru OK')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ loguru not working
) else (
    echo ✅ loguru working
)

echo.
echo Dependency installation complete!
echo Try running launch.bat now
echo.
pause