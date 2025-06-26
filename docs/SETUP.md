# Detailed Setup Guide

Complete installation instructions for all platforms.

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- **ComfyUI** with required nodes:
  - ComfyUI-Hy3DWrapper
  - ComfyUI_essentials
  - was-node-suite-comfyui
- **Cinema4D 2024+** with Python API
- **8GB+ RAM**, GPU with 4GB+ VRAM

## Platform-Specific Setup

### Windows

#### Quick Setup
```bash
# Run as Administrator
setup_final.bat
launch.bat
```

#### Manual Setup
```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env with your paths
```

#### Windows Issues
- **Unix Path Contamination**: Run `setup_windows_env.bat`
- **Cloud Sync**: Move project to local drive (C:\dev\)
- **Permissions**: Run as Administrator

### Linux/macOS

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your paths
```

## MCP Server Configuration

### ComfyUI MCP (Port 8188)
```bash
# Ensure ComfyUI is running
# No additional setup needed - works out of the box
```

### Cinema4D MCP (Port 54321)
1. Open Cinema4D
2. Script → Script Manager
3. Load: `mcp_servers/cinema4d-mcp/c4d_mcp_server.py`
4. Execute script (shows confirmation)

## Environment Configuration

Edit `.env` file:
```env
COMFYUI_PATH="D:/Comfy3D_WinPortable"  # Windows
COMFYUI_PATH="/home/user/ComfyUI"      # Linux

CINEMA4D_PATH="C:/Program Files/Maxon Cinema 4D 2024"  # Windows
CINEMA4D_PATH="/Applications/Cinema 4D.app"            # macOS
```

## Verification Checklist

- [ ] ComfyUI responds at http://localhost:8188
- [ ] Cinema4D MCP script runs without errors
- [ ] Application launches successfully
- [ ] Connection indicators show green
- [ ] Can generate test image

## Troubleshooting

### Connection Failed
1. Check firewall settings
2. Verify port availability (8188, 54321)
3. Ensure services are running

### Import Errors
1. Activate virtual environment
2. Reinstall dependencies
3. Check Python version (3.10+)

### Complete Reset
```bash
# Windows
rmdir /s venv
setup_final.bat

# Linux/macOS
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Diagnostic Tools

- `verify_installation.bat` (Windows)
- `diagnose_setup.bat` (Windows)
- Check `logs/errors.log` for issues

## Next Steps

After successful setup:
1. Launch application
2. Configure paths in Settings
3. Test with sample workflow
4. Read [ARCHITECTURE.md](../ARCHITECTURE.md) for technical details