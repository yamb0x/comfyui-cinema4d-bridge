@echo off
title ComfyUI to Cinema4D Bridge - Automated Startup
color 0A

echo ========================================
echo ComfyUI to Cinema4D Bridge
echo Automated Startup v1.0
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Load configuration
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="PATHS__COMFYUI_PATH" set COMFYUI_PATH=%%b
        if "%%a"=="PATHS__CINEMA4D_PATH" set CINEMA4D_PATH=%%b
    )
    REM Remove quotes from paths
    set COMFYUI_PATH=%COMFYUI_PATH:"=%
    set CINEMA4D_PATH=%CINEMA4D_PATH:"=%
)

echo [1/6] Checking Prerequisites...
echo ----------------------------------------

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.11+
    goto :error
)
echo ✅ Python found

REM Check virtual environment
if exist "venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ Virtual environment not found, using system Python
)

REM Check MCP dependencies
pip show mcp >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Installing MCP dependencies...
    pip install mcp aiohttp websockets loguru >nul 2>&1
)
echo ✅ MCP dependencies ready

echo.
echo [2/6] Checking ComfyUI...
echo ----------------------------------------

REM Check if ComfyUI is running
python -c "import requests; requests.get('http://127.0.0.1:8188/system_stats', timeout=2)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ ComfyUI is already running
    set COMFYUI_RUNNING=1
) else (
    echo ⚠️ ComfyUI not running
    set COMFYUI_RUNNING=0
    
    if exist "%COMFYUI_PATH%" (
        echo 🚀 Starting ComfyUI...
        start "ComfyUI" /d "%COMFYUI_PATH%" run.bat
        echo ⏳ Waiting for ComfyUI to start...
        
        REM Wait up to 60 seconds for ComfyUI to start
        for /l %%i in (1,1,12) do (
            timeout /t 5 /nobreak >nul
            python -c "import requests; requests.get('http://127.0.0.1:8188/system_stats', timeout=2)" >nul 2>&1
            if !errorlevel! equ 0 (
                echo ✅ ComfyUI started successfully
                set COMFYUI_RUNNING=1
                goto :comfyui_ready
            )
            echo ⏳ Still waiting... (%%i/12)
        )
        
        echo ❌ ComfyUI failed to start within 60 seconds
        echo Please start ComfyUI manually and rerun this script
        goto :error
        
        :comfyui_ready
    ) else (
        echo ❌ ComfyUI path not found: %COMFYUI_PATH%
        echo Please update .env file with correct PATHS__COMFYUI_PATH
        goto :error
    )
)

echo.
echo [3/6] Starting ComfyUI MCP Server...
echo ----------------------------------------

REM Check if MCP server is already running (look for python process)
tasklist /fi "windowtitle eq ComfyUI MCP Server*" 2>nul | find /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo ✅ ComfyUI MCP Server already running
) else (
    echo 🚀 Starting ComfyUI MCP Server...
    start "ComfyUI MCP Server" /min cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat 2>nul && cd mcp_servers\comfyui-mcp-server && python server.py"
    timeout /t 3 /nobreak >nul
    echo ✅ ComfyUI MCP Server started
)

echo.
echo [4/6] Checking Cinema4D...
echo ----------------------------------------

REM Check if Cinema4D is running
tasklist /fi "imagename eq Cinema 4D.exe" 2>nul | find /i "Cinema 4D.exe" >nul
if %errorlevel% equ 0 (
    echo ✅ Cinema4D is running
) else (
    echo ⚠️ Cinema4D not running - please start manually
    if exist "%CINEMA4D_PATH%" (
        echo 💡 You can start it from: %CINEMA4D_PATH%
    )
)

REM Check Cinema4D MCP server
python -c "import socket; s = socket.socket(); s.settimeout(1); result = s.connect_ex(('localhost', 54321)); s.close(); exit(0 if result == 0 else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Cinema4D MCP Server is running
) else (
    echo ⚠️ Cinema4D MCP Server not detected
    echo.
    echo 📋 To start Cinema4D MCP Server:
    echo 1. Open Cinema4D
    echo 2. Press Shift+F11 (Script Manager)
    echo 3. Load: mcp_servers\cinema4d-mcp\c4d_mcp_server.py
    echo 4. Click Execute
    echo 5. Look for dialog: "Cinema4D MCP Server Started - Listening on port 54321"
    echo.
    echo Press any key when Cinema4D MCP is ready...
    pause >nul
)

echo.
echo [5/6] Final System Check...
echo ----------------------------------------

echo Verifying all connections...
python -c "import requests; requests.get('http://127.0.0.1:8188/system_stats', timeout=2)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ ComfyUI API accessible
) else (
    echo ❌ ComfyUI API not accessible
    goto :error
)

python -c "import socket; s = socket.socket(); s.settimeout(1); result = s.connect_ex(('localhost', 54321)); s.close(); exit(0 if result == 0 else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Cinema4D MCP accessible
) else (
    echo ⚠️ Cinema4D MCP not accessible (will show warning in app)
)

echo.
echo [6/6] Launching Application...
echo ----------------------------------------

echo 🚀 Starting ComfyUI to Cinema4D Bridge...
echo.
echo ========================================
echo All systems ready! 
echo ========================================
echo.

python main.py
goto :end

:error
echo.
echo ========================================
echo ❌ Startup Failed
echo ========================================
echo.
echo Please check the errors above and try again.
echo You can also run components manually:
echo 1. launch.bat (main app)
echo 2. Start ComfyUI MCP Server.bat (MCP server)
echo.
pause
goto :end

:end
echo.
echo Application closed. Press any key to exit...
pause >nul