@echo off
echo ========================================
echo ComfyUI to Cinema4D Bridge - Cleanup
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

echo Cleaning up test files and organizing project...
echo.

REM Remove test files
echo Removing test files...
if exist "Test Config.bat" del "Test Config.bat"
if exist "Test MCP Connection.bat" del "Test MCP Connection.bat"
if exist "Test Cinema4D Connection.bat" del "Test Cinema4D Connection.bat"
if exist "Check MCP Files.bat" del "Check MCP Files.bat"
if exist "Install MCP Dependencies.bat" del "Install MCP Dependencies.bat"
if exist "Install Requests.bat" del "Install Requests.bat"
if exist "test_config.py" del "test_config.py"
if exist "temp_test.py" del "temp_test.py"

REM Remove redundant setup files
echo Removing redundant files...
if exist "Setup MCP Servers.bat" del "Setup MCP Servers.bat"
if exist "QUICK_START_SIMPLE.md" del "QUICK_START_SIMPLE.md"

REM Clean up logs (keep recent ones)
echo Cleaning old log files...
if exist "logs" (
    cd logs
    forfiles /m *.log /d -7 /c "cmd /c del @path" 2>nul
    cd ..
)

REM Clean up setup logs
echo Cleaning setup logs...
if exist "setup_logs" (
    cd setup_logs
    forfiles /m *.log /d -7 /c "cmd /c del @path" 2>nul
    cd ..
)

REM Remove empty temp directories
echo Removing empty temp directories...
if exist "setup_temp" rmdir "setup_temp" 2>nul

REM Clean up MCP server old files
echo Cleaning MCP server files...
if exist "mcp_servers\comfyui-mcp-server\index.js" del "mcp_servers\comfyui-mcp-server\index.js"
if exist "mcp_servers\comfyui-mcp-server\node_modules" rmdir /s /q "mcp_servers\comfyui-mcp-server\node_modules" 2>nul
if exist "mcp_servers\comfyui-mcp-server\package-lock.json" del "mcp_servers\comfyui-mcp-server\package-lock.json"

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Kept essential files:
echo - launch.bat (main application launcher)
echo - Start ComfyUI MCP Server.bat (MCP server starter)
echo - Start ComfyUI MCP.bat (alternative MCP starter)
echo - MCP_SETUP_GUIDE.md (technical documentation)
echo - RUN_APPLICATION_GUIDE.md (user guide)
echo - All core application files
echo.
echo Removed:
echo - Test and diagnostic scripts
echo - Redundant setup files
echo - Old log files (older than 7 days)
echo - Node.js artifacts
echo.

pause