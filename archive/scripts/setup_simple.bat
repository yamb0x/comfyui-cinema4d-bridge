@echo off
echo Simple Windows Setup for ComfyUI to Cinema4D Bridge
echo.

cd /d "%~dp0"

echo Removing old virtual environment...
if exist "venv" rmdir /s /q venv

echo Creating virtual environment...
python -m venv venv

echo Installing core dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install PySide6
venv\Scripts\python.exe -m pip install qasync
venv\Scripts\python.exe -m pip install loguru

echo Testing installation...
venv\Scripts\python.exe -c "import PySide6; print('PySide6 OK')"
venv\Scripts\python.exe -c "import qasync; print('qasync OK')"
venv\Scripts\python.exe -c "import loguru; print('loguru OK')"

echo Installing all dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo Setup complete! Run launch.bat to start the application.
pause