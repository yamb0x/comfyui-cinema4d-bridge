@echo off
echo ============================================================
echo  comfy2c4d - Dependency Installation
echo ============================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ❌ ERROR: Virtual environment not found
    echo Please run setup_windows_env.bat first to create the virtual environment
    echo.
    pause
    exit /b 1
)

echo ✅ Virtual environment found
echo Using: %cd%\venv\Scripts\python.exe
echo.

echo ============================================================
echo  PHASE 1: Core Package Updates
echo ============================================================

echo [1/4] Updating pip to latest version...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upgrade pip
    goto :error_exit
)
echo ✅ pip updated successfully

echo [2/4] Updating setuptools and wheel...
venv\Scripts\python.exe -m pip install --upgrade setuptools wheel --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upgrade build tools
    goto :error_exit
)
echo ✅ Build tools updated

echo [3/4] Installing core Qt6 framework...
venv\Scripts\python.exe -m pip install "PySide6>=6.6.0"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install PySide6
    echo This is critical for the application UI
    goto :error_exit
)
echo ✅ PySide6 (Qt6) installed

echo [4/4] Installing async Qt integration...
venv\Scripts\python.exe -m pip install "qasync>=0.27.0"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install qasync
    echo This is critical for async operations
    goto :error_exit
)
echo ✅ qasync installed
echo.

echo ============================================================
echo  PHASE 2: Application Dependencies
echo ============================================================

echo [1/6] Installing enhanced logging system...
venv\Scripts\python.exe -m pip install "loguru>=0.7.2" "rich>=13.6.0"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install logging packages
    goto :error_exit
)
echo ✅ Logging packages installed

echo [2/6] Installing HTTP and async utilities...
venv\Scripts\python.exe -m pip install "httpx>=0.25.0" "websockets>=12.0" "aiofiles>=23.2.1"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install network packages
    goto :error_exit
)
echo ✅ Network packages installed

echo [3/6] Installing data validation and configuration...
venv\Scripts\python.exe -m pip install "pydantic>=2.4.0" "pydantic-settings>=2.0.3" "python-dotenv>=1.0.0"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install data packages
    goto :error_exit
)
echo ✅ Data packages installed

echo [4/6] Installing file and image processing...
venv\Scripts\python.exe -m pip install "watchdog>=3.0.0" "Pillow>=10.0.0" "numpy>=1.24.0"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install media packages
    goto :error_exit
)
echo ✅ Media packages installed

echo [5/6] Installing 3D model processing...
venv\Scripts\python.exe -m pip install "trimesh>=4.0.0"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install 3D packages
    goto :error_exit
)
echo ✅ 3D packages installed

echo [6/6] Installing system monitoring (performance features)...
venv\Scripts\python.exe -m pip install "psutil>=5.9.0"
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Failed to install psutil (performance monitoring may be limited)
    set PSUTIL_AVAILABLE=false
) else (
    echo ✅ System monitoring installed
    set PSUTIL_AVAILABLE=true
)
echo.

echo ============================================================
echo  PHASE 3: Optional Dependencies
echo ============================================================

echo [1/3] Installing GPU monitoring (optional)...
venv\Scripts\python.exe -m pip install "pynvml>=11.0.0" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  GPU monitoring not available (pynvml installation failed)
    set GPU_MONITORING=false
) else (
    echo ✅ GPU monitoring available
    set GPU_MONITORING=true
)

echo [2/3] Installing Windows Cinema4D integration...
venv\Scripts\python.exe -m pip install "pywin32>=306" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Windows COM automation limited (pywin32 installation failed)
    set WIN_INTEGRATION=false
) else (
    echo ✅ Windows integration available
    set WIN_INTEGRATION=true
)

echo [3/3] Installing testing framework...
venv\Scripts\python.exe -m pip install "pytest>=7.4.0" "pytest-asyncio>=0.21.1" "pytest-qt>=4.2.0" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Testing framework not available
    set TESTING_AVAILABLE=false
) else (
    echo ✅ Testing framework available
    set TESTING_AVAILABLE=true
)
echo.

echo ============================================================
echo  PHASE 4: Final Installation from requirements.txt
echo ============================================================

echo Installing any remaining dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Some additional dependencies may have failed
) else (
    echo ✅ Additional dependencies installed
)
echo.

echo ============================================================
echo  VERIFICATION: Testing Critical Dependencies
echo ============================================================

set CRITICAL_ERRORS=0

echo Testing core Qt6 framework...
venv\Scripts\python.exe -c "import PySide6.QtWidgets; print('✅ PySide6 working')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ PySide6 not working - APPLICATION WILL NOT START
    set /a CRITICAL_ERRORS+=1
)

echo Testing async Qt integration...
venv\Scripts\python.exe -c "import qasync; print('✅ qasync working')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ qasync not working - ASYNC OPERATIONS WILL FAIL
    set /a CRITICAL_ERRORS+=1
)

echo Testing logging system...
venv\Scripts\python.exe -c "import loguru; print('✅ loguru working')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ loguru not working - LOGGING WILL BE LIMITED
    set /a CRITICAL_ERRORS+=1
)

echo Testing HTTP client...
venv\Scripts\python.exe -c "import httpx; print('✅ httpx working')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ httpx not working - COMFYUI CONNECTION WILL FAIL
    set /a CRITICAL_ERRORS+=1
)

echo Testing data validation...
venv\Scripts\python.exe -c "import pydantic; print('✅ pydantic working')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ pydantic not working - CONFIGURATION SYSTEM WILL FAIL
    set /a CRITICAL_ERRORS+=1
)

echo Testing image processing...
venv\Scripts\python.exe -c "import PIL; print('✅ Pillow working')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Pillow not working - IMAGE PROCESSING WILL FAIL
    set /a CRITICAL_ERRORS+=1
)

echo Testing file monitoring...
venv\Scripts\python.exe -c "import watchdog; print('✅ watchdog working')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ watchdog not working - FILE MONITORING WILL FAIL
    set /a CRITICAL_ERRORS+=1
)

echo.
echo ============================================================
echo  OPTIONAL FEATURES VERIFICATION
echo ============================================================

if "%PSUTIL_AVAILABLE%"=="true" (
    venv\Scripts\python.exe -c "import psutil; print('✅ System monitoring available')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ⚠️  psutil import failed - Performance monitoring limited
    )
) else (
    echo ⚠️  System monitoring not available
)

if "%GPU_MONITORING%"=="true" (
    venv\Scripts\python.exe -c "import pynvml; print('✅ GPU monitoring available')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ⚠️  GPU monitoring import failed
    )
) else (
    echo ⚠️  GPU monitoring not available
)

if "%TESTING_AVAILABLE%"=="true" (
    venv\Scripts\python.exe -c "import pytest; print('✅ Testing framework available')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ⚠️  Testing framework import failed
    )
) else (
    echo ⚠️  Testing framework not available
)

echo.
echo ============================================================
echo  INSTALLATION SUMMARY
echo ============================================================

if %CRITICAL_ERRORS% EQU 0 (
    echo ✅ SUCCESS: All critical dependencies installed correctly!
    echo.
    echo 🚀 You can now run the application with: launch.bat
    echo 📚 Or run tests with: venv\Scripts\python.exe -m pytest
    echo ⚙️  Check settings for optional features in the application
    echo.
    echo Ready to bridge AI workflows with Cinema4D! 🎨➡️🎬
) else (
    echo ❌ CRITICAL ERRORS: %CRITICAL_ERRORS% critical dependencies failed
    echo.
    echo The application may not work correctly. Please:
    echo 1. Check your internet connection
    echo 2. Try running this script as Administrator
    echo 3. Check that you have the latest Python version
    echo 4. Consider recreating the virtual environment
    echo.
    echo If problems persist, check the GitHub issues or documentation.
)

echo.
echo ============================================================
pause
exit /b %CRITICAL_ERRORS%

:error_exit
echo.
echo ❌ INSTALLATION FAILED
echo.
echo Possible solutions:
echo 1. Check your internet connection
echo 2. Run this script as Administrator
echo 3. Recreate virtual environment: del /s /q venv ^& setup_windows_env.bat
echo 4. Check Windows Defender isn't blocking pip
echo.
pause
exit /b 1