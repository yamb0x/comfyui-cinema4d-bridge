@echo off
cls
echo.
echo    ============================================
echo       FINAL STUDIO 3D VIEWER
echo    ============================================
echo.
echo    All parameters connected and verified
echo.

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

python studio_viewer_final.py

pause