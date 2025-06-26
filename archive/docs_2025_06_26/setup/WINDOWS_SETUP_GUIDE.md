# Windows Setup Guide - ComfyUI to Cinema4D Bridge

## 🚨 Issue: Mixed Unix/Windows Paths

The virtual environment was created on WSL/Linux and contains Unix paths (`/usr/bin/python3`) that don't work on Windows.

## 🔧 Quick Fix

### Step 1: Diagnose the Issue
Run the diagnosis script to check your setup:
```bash
diagnose_setup.bat
```

### Step 2: Fix the Environment
If you see "Virtual environment has Unix paths", run:
```bash
setup_windows_env.bat
```

This will:
- Remove the old virtual environment with Unix paths
- Create a new Windows-compatible virtual environment
- Install all required Python packages
- Set up proper Windows paths

### Step 3: Launch the Application
After setup is complete, run:
```bash
launch.bat
```

## 📋 Manual Setup (if scripts fail)

### 1. Check Python Installation
```bash
python --version
```
Should show Python 3.12 or higher. If not, install from [python.org](https://python.org).

### 2. Remove Old Virtual Environment
```bash
rmdir /s /q venv
```

### 3. Create New Virtual Environment
```bash
python -m venv venv
```

### 4. Activate Virtual Environment
```bash
venv\Scripts\activate.bat
```

### 5. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Launch Application
```bash
python main.py
```

## 🔍 Troubleshooting

### Error: "did not find executable at '/usr/bin\python.exe'"
- **Cause**: Virtual environment created on Linux/WSL
- **Fix**: Run `setup_windows_env.bat`

### Error: "Python not found"
- **Cause**: Python not installed or not in PATH
- **Fix**: Install Python from [python.org](https://python.org) and add to PATH

### Error: "No module named 'PySide6'"
- **Cause**: Dependencies not installed
- **Fix**: Run `setup_windows_env.bat` or manually install with `pip install -r requirements.txt`

### Error: Access denied when removing venv
- **Cause**: Files in use or permission issues
- **Fix**: Close all Python processes and run Command Prompt as Administrator

## 📁 Expected File Structure

After successful setup:
```
comfy-to-c4d/
├── venv/                    # Windows virtual environment
│   ├── Scripts/
│   │   ├── python.exe      # Windows Python executable
│   │   ├── activate.bat    # Windows activation script
│   │   └── ...
│   └── pyvenv.cfg          # Should have Windows paths
├── src/                    # Application source code
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── launch.bat             # Windows launcher (fixed)
├── setup_windows_env.bat  # Environment setup script
└── diagnose_setup.bat     # Diagnosis script
```

## ✅ Verification

Run this command to verify everything is working:
```bash
venv\Scripts\python.exe -c "import PySide6, loguru, qasync; print('All dependencies OK')"
```

Should output: `All dependencies OK`

## 🚀 Quick Start

1. Open Command Prompt in the project directory
2. Run: `setup_windows_env.bat`
3. Wait for installation to complete
4. Run: `launch.bat`
5. Application should start successfully!