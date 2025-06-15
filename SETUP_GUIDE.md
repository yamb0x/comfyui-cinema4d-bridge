# ComfyUI to Cinema4D Bridge - Complete Setup Guide

This comprehensive guide covers the complete installation and setup process for the ComfyUI to Cinema4D Bridge application.

## 🚀 Quick Start

### **Option 1: Automated Setup (Recommended)**
```bash
# Run as Administrator
setup_final.bat
Setup MCP Servers.bat
```

### **Option 2: Manual Setup**
Follow the detailed instructions below.

---

## 📋 Prerequisites

### **Required Software**
✅ **Python 3.10+**
- Download from https://www.python.org/
- ⚠️ **CRITICAL**: Check "Add Python to PATH" during installation

✅ **ComfyUI**
- Recommended installation: `D:\Comfy3D_WinPortable`
- Must have required custom nodes:
  - ComfyUI-Hy3DWrapper
  - ComfyUI_essentials
  - was-node-suite-comfyui

✅ **Cinema4D 2024+**
- Default installation: `C:\Program Files\Maxon Cinema 4D 2024`
- Python API must be enabled

### **System Requirements**
- Windows 10/11 64-bit
- 8GB+ RAM recommended
- GPU with 4GB+ VRAM for 3D viewing
- Administrator privileges

---

## 🛠️ Installation Steps

### **1. Clone Repository**
```bash
cd "D:\Yambo Studio Dropbox\Admin\_studio-dashboard-app-dev"
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git comfy-to-c4d
cd comfy-to-c4d
```

### **2. Setup Python Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Configure Environment**
```bash
# Copy environment template
copy .env.example .env
```

Edit `.env` file with your actual paths:
```env
COMFYUI_PATH="D:/Comfy3D_WinPortable"
CINEMA4D_PATH="C:/Program Files/Maxon Cinema 4D 2024"
```

### **4. Setup MCP Servers**

#### **ComfyUI MCP Server**
```bash
# Install MCP dependencies
Setup MCP Servers.bat

# Start ComfyUI MCP Server
Start ComfyUI MCP Server.bat
```

#### **Cinema4D MCP Server**
1. Open Cinema4D
2. Go to **Script → Script Manager**
3. Load file: `mcp_servers/cinema4d-mcp/c4d_mcp_server.py`
4. Click **Execute** to start the socket server

### **5. Verify Workflow Files**
Ensure these files exist in the `workflows/` directory:
- `generate_images.json` - FLUX image generation workflow
- `generate_3D.json` - Hy3D 3D generation workflow

---

## 🚀 First Launch

### **Step 1: Start ComfyUI**
```bash
cd D:\Comfy3D_WinPortable
run.bat
```
Wait for message: "To see the GUI go to: http://127.0.0.1:8188"

### **Step 2: Start Cinema4D**
- Launch Cinema4D 2024
- Load and execute MCP server script in Script Manager
- Verify socket server confirmation dialog

### **Step 3: Launch Bridge Application**
```bash
# From project directory
launch.bat
```

### **Step 4: Verify Connections**
Check status indicators in application:
- 🟢 Green: Connected successfully
- ❌ Red: Connection failed
- ⚠️ Yellow: Partial connection

Console should show:
- "Connected to ComfyUI"
- "Connected to Cinema4D"

---

## 🔧 MCP Server Architecture

```
Main Application
    ├── ComfyUI Client ──→ ComfyUI MCP Server ──→ ComfyUI API
    └── Cinema4D Client ──→ Cinema4D Socket Server ──→ Cinema4D
```

### **ComfyUI MCP Server Tools**
- `generate_image`: Generate images using ComfyUI workflows
- `get_models`: List available models
- `get_queue_status`: Check generation queue
- `interrupt_execution`: Stop current generation

### **Cinema4D MCP Server Tools**
- `execute_python`: Execute arbitrary Python in C4D
- `import_object`: Import 3D files (OBJ, FBX, etc.)
- `create_primitive`: Create basic shapes
- `create_material`: Create materials
- `assign_material`: Apply materials to objects
- `create_light`: Add lighting
- `save_project`: Save C4D project
- `get_scene_objects`: List scene contents

---

## 🐛 Troubleshooting

### **ComfyUI Issues**
❌ **"Failed to connect to ComfyUI"**
- Check ComfyUI is running on http://localhost:8188
- Verify no firewall blocking
- Ensure API is enabled in ComfyUI

❌ **"Workflow file not found"**
- Check workflow JSON files exist in `workflows/` directory
- Validate JSON syntax
- Ensure all required nodes are installed in ComfyUI

❌ **"Failed to queue prompt"**
- Verify ComfyUI is accepting API requests
- Check ComfyUI console for errors

### **Cinema4D Issues**
❌ **"Not connected to Cinema4D"**
- Load and run the C4D script manually in Script Manager
- Check port 54321 is available
- Verify C4D Python preferences

❌ **"Socket connection failed"**
- Check if port 54321 is in use by another application
- Restart Cinema4D and reload MCP script
- Run as administrator if needed

❌ **"Script execution failed"**
- Verify Python syntax in C4D scripts
- Check Cinema4D Python console for error details

### **General Issues**
❌ **"Virtual environment not found"**
- Run `setup_final.bat` as administrator
- Manually create venv if automated setup fails

❌ **"MCP dependencies missing"**
- Run `Setup MCP Servers.bat`
- Manually install: `pip install mcp aiohttp websockets loguru`

❌ **File Permission Errors**
- Run as administrator
- Check write permissions on output directories:
  - `images/` - Generated images
  - `3D/Hy3D/` - 3D models
  - `config/` - Settings
  - `logs/` - Application logs
  - `exports/` - C4D projects

---

## 🔧 Advanced Configuration

### **Custom Workflows**
Place custom ComfyUI workflow JSON files in:
- `workflows/` (main directory)
- `mcp_servers/comfyui-mcp-server/workflows/`

### **Port Configuration**
To change Cinema4D socket port:
1. Edit `mcp_servers/cinema4d-mcp/c4d_mcp_server.py` line 91
2. Edit `src/mcp/cinema4d_client.py` line 52
3. Update `.env` file if needed

### **Development Mode**
Run MCP servers directly for development:
```bash
# ComfyUI MCP Server
cd mcp_servers/comfyui-mcp-server
python server.py

# Cinema4D MCP Server (run in C4D Script Manager)
# Load and execute c4d_mcp_server.py
```

---

## 📦 Dependencies

### **Python Packages**
- `mcp>=0.5.0` - Model Context Protocol framework
- `aiohttp>=3.8.0` - HTTP client for ComfyUI
- `websockets>=11.0.0` - WebSocket support
- `loguru>=0.7.0` - Logging
- `PyQt6>=6.7.0` - UI framework
- `vispy>=0.14.1` - 3D visualization
- `trimesh>=4.3.2` - 3D mesh processing

### **External Applications**
- ComfyUI (with API enabled)
- Cinema4D 2024+ (with Python API)

---

## 🆘 Support

### **Diagnostic Tools**
```bash
# Check installation
verify_installation.bat

# Repair common issues
repair_tool.bat

# View detailed logs
check logs/errors.log
```

### **Common Solutions**
1. **Complete Reinstall**: Delete `venv/` folder and run `setup_final.bat`
2. **Reset Configuration**: Delete `.env` file and recopy from `.env.example`
3. **Clear Cache**: Delete `config/` folder contents (keeps logs)

### **Getting Help**
- Check console output for specific error messages
- Review `logs/errors.log` for detailed error information
- Ensure all prerequisites are correctly installed
- Try running components separately to isolate issues

---

## ✅ Verification Checklist

After setup, verify all systems are working:

- [ ] ComfyUI responds at http://127.0.0.1:8188
- [ ] Cinema4D MCP script executes without errors
- [ ] Bridge application launches successfully
- [ ] Both connection indicators show green
- [ ] Can generate a test image
- [ ] Can create a test 3D model
- [ ] Can create Cinema4D primitives

**🎉 Setup Complete!** You're ready to use the ComfyUI to Cinema4D Bridge.