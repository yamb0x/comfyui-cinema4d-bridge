@echo off
echo Starting ComfyUI MCP Server...
echo.

REM Try to activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found - using system Python
)

REM Check if ComfyUI MCP server dependencies are installed
echo Checking MCP server dependencies...
pip show mcp >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing MCP server dependencies...
    pip install mcp aiohttp websockets loguru
)

REM Start ComfyUI MCP Server
echo.
echo Starting ComfyUI MCP Server...
echo Make sure ComfyUI is running at http://127.0.0.1:8188
echo.

REM Change to script directory first
cd /d "%~dp0"
cd mcp_servers\comfyui-mcp-server
python server.py

pause