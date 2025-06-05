@echo off
echo ========================================
echo Cleaning Root Directory
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

echo Removing redundant and test files...

REM Remove redundant documentation
if exist ".env.example" del ".env.example"
if exist "CHANGELOG.md" del "CHANGELOG.md"
if exist "INSTALLER_README.md" del "INSTALLER_README.md"
if exist "QUICK_START.md" del "QUICK_START.md"
if exist "QUICK_START_ENHANCED.md" del "QUICK_START_ENHANCED.md"
if exist "README.md" del "README.md"

REM Remove git-related files
if exist ".gitignore" del ".gitignore"
if exist "git_init.bat" del "git_init.bat"
if exist "prepare_for_github.bat" del "prepare_for_github.bat"

REM Remove setup markers and old scripts
if exist ".setup_complete" del ".setup_complete"
if exist "cleanup_final.bat" del "cleanup_final.bat"
if exist "Fix ComfyUI Path.bat" del "Fix ComfyUI Path.bat"
if exist "repair_tool.bat" del "repair_tool.bat"
if exist "setup.ps1" del "setup.ps1"
if exist "verify_installation.bat" del "verify_installation.bat"

REM Remove duplicate MCP starter
if exist "Start ComfyUI MCP.bat" del "Start ComfyUI MCP.bat"

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Removed redundant files. Essential files kept:
echo ✅ .env (configuration)
echo ✅ CLAUDE.md (main documentation)
echo ✅ PROJECT_STATUS.md (status summary)
echo ✅ main.py (application)
echo ✅ startup_automated.bat (launcher)
echo ✅ launch.bat (manual launcher)
echo ✅ All src/ and mcp_servers/ directories
echo.

pause