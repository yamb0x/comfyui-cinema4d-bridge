@echo off
echo Fixing missing dependencies...
echo.

cd /d "%~dp0"

echo Installing PySide6...
venv\Scripts\python.exe -m pip install PySide6

echo Installing qasync...
venv\Scripts\python.exe -m pip install qasync

echo Installing loguru...
venv\Scripts\python.exe -m pip install loguru

echo Installing remaining dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo Testing installation...
venv\Scripts\python.exe -c "import PySide6; print('✅ PySide6 working')"
venv\Scripts\python.exe -c "import qasync; print('✅ qasync working')"
venv\Scripts\python.exe -c "import loguru; print('✅ loguru working')"

echo.
echo Dependencies fixed! Try launch.bat now.
pause