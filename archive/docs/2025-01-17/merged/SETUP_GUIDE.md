# Setup Guide

## Prerequisites

### Required Software
1. **Python 3.10+**
   - Download from https://www.python.org/
   - Ensure "Add Python to PATH" is checked during installation

2. **ComfyUI**
   - Should be installed at `D:\Comfy3D_WinPortable`
   - Must have the following custom nodes:
     - ComfyUI-Hy3DWrapper
     - ComfyUI_essentials
     - was-node-suite-comfyui

3. **Cinema4D 2024**
   - Default installation at `C:\Program Files\Maxon Cinema 4D 2024`
   - Python API must be enabled

### MCP Servers
1. **ComfyUI MCP Server**
   ```bash
   git clone https://github.com/joenorton/comfyui-mcp-server
   cd comfyui-mcp-server
   npm install
   npm start
   ```

2. **Cinema4D MCP Server**
   ```bash
   git clone https://github.com/ttiimmaacc/cinema4d-mcp
   cd cinema4d-mcp
   python install.py
   ```

## Installation Steps

### 1. Clone the Repository
```bash
cd "D:\Yambo Studio Dropbox\Admin\_studio-dashboard-app-dev"
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git comfy-to-c4d
cd comfy-to-c4d
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and update paths:
   ```env
   COMFYUI_PATH="D:/Comfy3D_WinPortable"
   CINEMA4D_PATH="C:/Program Files/Maxon Cinema 4D 2024"
   ```

### 5. Verify Workflow Files
Ensure these files exist in the `workflows/` directory:
- `generate_images.json` - FLUX image generation workflow
- `generate_3D.json` - Hy3D 3D generation workflow

## First Run

### 1. Start ComfyUI
```bash
cd D:\Comfy3D_WinPortable
run.bat
```
Wait for "To see the GUI go to: http://127.0.0.1:8188"

### 2. Start Cinema4D
- Launch Cinema4D 2024
- Open Script Manager (Script > Script Manager)
- Run the MCP server script

### 3. Launch the Bridge
```bash
cd "D:\Yambo Studio Dropbox\Admin\_studio-dashboard-app-dev\comfy-to-c4d"
launch.bat
```

### 4. Verify Connections
- Check that both status indicators show green (🟢)
- Console should show "Connected to ComfyUI" and "Connected to Cinema4D"

## Troubleshooting

### ComfyUI Connection Failed
1. Check ComfyUI is running on http://localhost:8188
2. Verify no firewall blocking
3. Check console for specific error messages

### Cinema4D Connection Failed
1. Ensure MCP server script is running in C4D
2. Check port 5000 is not in use
3. Verify C4D Python preferences

### Workflow Loading Failed
1. Check workflow JSON files exist
2. Validate JSON syntax
3. Ensure all required nodes are installed in ComfyUI

### File Permission Errors
1. Run as administrator if needed
2. Check write permissions on output directories
3. Ensure no files are locked by other applications

## Directory Permissions
Ensure write access to:
- `images/` - For generated images
- `3D/Hy3D/` - For 3D models
- `config/` - For settings
- `logs/` - For application logs
- `exports/` - For C4D projects