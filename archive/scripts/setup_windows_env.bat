@echo off
echo Setting up Windows Python environment for ComfyUI to Cinema4D Bridge...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://python.org
    pause
    exit /b 1
)

echo Current Python version:
python --version

REM Remove existing venv if it has issues
if exist "venv" (
    echo Checking existing virtual environment...
    if exist "venv\pyvenv.cfg" (
        findstr /C:"home = /usr/bin" "venv\pyvenv.cfg" >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo Found virtual environment with Unix paths, removing...
            rmdir /s /q venv 2>nul
            if exist "venv" (
                echo Warning: Could not fully remove old venv. Some files may be in use.
                echo Please close any Python processes and try again.
                pause
                exit /b 1
            )
        ) else (
            echo Existing virtual environment looks OK, removing to recreate...
            rmdir /s /q venv 2>nul
        )
    )
)

echo Creating new Windows virtual environment...
python -m venv venv

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create virtual environment
    echo Make sure you have the latest Python version installed
    pause
    exit /b 1
)

echo Verifying virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment creation failed
    echo venv\Scripts\python.exe not found
    pause
    exit /b 1
)

echo Virtual environment created successfully!
echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo Installing required packages...
echo This may take a few minutes...
echo.

venv\Scripts\python.exe -m pip install PySide6>=6.6.0
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install PySide6
    pause
    exit /b 1
)

venv\Scripts\python.exe -m pip install qasync>=0.27.0
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install qasync
    pause
    exit /b 1
)

venv\Scripts\python.exe -m pip install loguru>=0.7.2
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install loguru
    pause
    exit /b 1
)

echo Installing remaining dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo Testing installation...
venv\Scripts\python.exe -c "import PySide6; print('✅ PySide6 installed successfully')"
venv\Scripts\python.exe -c "import qasync; print('✅ qasync installed successfully')"
venv\Scripts\python.exe -c "import loguru; print('✅ loguru installed successfully')"

echo.
echo Setup complete! You can now run the application with launch.bat
echo.
pause