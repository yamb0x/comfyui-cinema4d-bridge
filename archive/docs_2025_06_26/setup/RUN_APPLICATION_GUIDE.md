# ComfyUI to Cinema4D Bridge - Complete Running Guide

This guide provides step-by-step instructions to successfully run the ComfyUI to Cinema4D Bridge application.

## Prerequisites Checklist

Before starting, ensure you have:
- ✅ Windows 10/11 64-bit
- ✅ ComfyUI installed and working
- ✅ Cinema4D 2024+ installed
- ✅ Administrator privileges

## Step-by-Step Setup & Launch

### 1. Initial Setup (One-time only)

```bash
# Run as Administrator
setup_final.bat
```

**What this does:**
- Creates Python virtual environment
- Installs all Python dependencies
- Sets up directory structure
- Creates configuration files

**If you get errors:**
- Run `repair_tool.bat` as Administrator
- Check `setup_logs/setup.log` for details

### 2. Setup MCP Servers (One-time only)

```bash
Setup MCP Servers.bat
```

**What this does:**
- Installs MCP framework dependencies
- Sets up ComfyUI MCP server files
- Configures Cinema4D MCP integration

### 3. Configure Application Paths

Edit `.env` file with your actual paths:
```
COMFYUI_PATH="D:/Comfy3D_WinPortable"
CINEMA4D_PATH="C:/Program Files/Maxon Cinema 4D 2024"
```

**How to find your paths:**
- ComfyUI: Where you extracted/installed ComfyUI
- Cinema4D: Usually `C:/Program Files/Maxon Cinema 4D 2024`

## Running the Application

### Step 1: Start ComfyUI
```bash
# Navigate to your ComfyUI directory
cd "D:/Comfy3D_WinPortable"  # Use your actual path

# Start ComfyUI
run.bat
```

**Wait until you see:**
```
Starting server
To see the GUI go to: http://127.0.0.1:8188
```

### Step 2: Start ComfyUI MCP Server
```bash
# In the bridge directory
Start ComfyUI MCP Server.bat
```

**Expected output:**
```
Starting ComfyUI MCP Server...
Checking MCP server dependencies...
Connected to ComfyUI at http://localhost:8188
WebSocket connected to ComfyUI
Server listening for MCP connections...
```

### Step 3: Setup Cinema4D MCP Server

1. **Open Cinema4D**
2. **Open Script Manager:**
   - Menu: `Script → Script Manager` (Shift+F11)
3. **Load MCP Script:**
   - Click "Open" button
   - Navigate to: `mcp_servers/cinema4d-mcp/c4d_mcp_server.py`
   - Click "Open"
4. **Execute Script:**
   - Click "Execute" button
   - You should see: "Cinema4D MCP Server Started - Listening on port 54321"

### Step 4: Launch Main Application
```bash
launch.bat
```

**Expected startup sequence:**
```
Starting ComfyUI to Cinema4D Bridge...
Loading configuration...
Connecting to ComfyUI MCP Server... ✅
Connecting to Cinema4D MCP Server... ✅
Starting file monitor...
GUI initialized
Application ready!
```

## Troubleshooting Common Issues

### ComfyUI Connection Failed
**Problem:** `Failed to connect to ComfyUI`
**Solutions:**
1. Ensure ComfyUI is running at http://localhost:8188
2. Check ComfyUI console for errors
3. Try visiting http://localhost:8188 in browser
4. Restart ComfyUI and try again

### Cinema4D Connection Failed
**Problem:** `Not connected to Cinema4D`
**Solutions:**
1. Ensure Cinema4D is open
2. Re-run the MCP script in Cinema4D Script Manager
3. Check if port 54321 is blocked by firewall
4. Restart Cinema4D and try again

### Virtual Environment Issues
**Problem:** `Virtual environment not found`
**Solutions:**
1. Run `setup_final.bat` as Administrator
2. Delete `venv` folder and re-run setup
3. Check antivirus isn't blocking Python

### MCP Dependencies Missing
**Problem:** `ModuleNotFoundError: No module named 'mcp'`
**Solutions:**
1. Run `Setup MCP Servers.bat`
2. Manually install: `pip install mcp aiohttp websockets loguru`
3. Check virtual environment is active

### Permission Errors
**Problem:** `Access denied` or `Permission denied`
**Solutions:**
1. Run all batch files as Administrator
2. Check folder permissions
3. Disable antivirus temporarily during setup

## Testing the Pipeline

### Basic Connection Test
1. Launch application following steps above
2. Check status indicators in GUI:
   - ComfyUI: Green = Connected
   - Cinema4D: Green = Connected

### Image Generation Test
1. Enter prompt: "a beautiful landscape"
2. Click "Generate Images"
3. Check `images/` folder for outputs
4. Monitor console for progress

### 3D Generation Test
1. Generate images first
2. Select an image
3. Click "Generate 3D"
4. Check `3D/Hy3D/` folder for .obj files

### Cinema4D Integration Test
1. Complete 3D generation
2. Click "Send to Cinema4D"
3. Check Cinema4D scene for imported objects

## Performance Tips

### Faster Startup
- Keep ComfyUI running between sessions
- Use SSD storage for output directories
- Close unnecessary applications

### Better Results
- Use specific, detailed prompts
- Adjust generation parameters
- Select high-quality input images for 3D

### Resource Management
- Monitor GPU memory usage
- Close browser tabs while generating
- Use smaller image sizes for testing

## File Locations

### Important Directories
```
comfy-to-c4d/
├── images/              # Generated images
├── 3D/Hy3D/            # Generated 3D models
├── exports/            # Exported C4D projects
├── workflows/          # ComfyUI workflow templates
├── logs/               # Application logs
├── mcp_servers/        # MCP server implementations
└── config/             # Configuration files
```

### Configuration Files
- `.env` - Main paths and settings
- `config/app_config.json` - Detailed configuration
- `workflows/*.json` - ComfyUI workflow templates

### Log Files
- `logs/app.log` - Main application log
- `setup_logs/setup.log` - Setup process log
- Console output - Real-time status

## Advanced Usage

### Custom Workflows
1. Create/modify JSON files in `workflows/`
2. Restart application to load changes
3. Test with simple prompts first

### Batch Processing
1. Prepare list of prompts
2. Use "Queue Mode" in GUI
3. Monitor progress in console

### Export Settings
1. Configure export paths in `.env`
2. Choose Cinema4D project format
3. Enable auto-backup if desired

## Getting Help

### Check These First
1. Console output for error messages
2. Log files in `logs/` directory
3. ComfyUI console for API errors
4. Cinema4D Script Manager for C4D errors

### Useful Commands
```bash
verify_installation.bat    # Check setup status
repair_tool.bat            # Fix common issues
Setup MCP Servers.bat       # Reinstall MCP components
```

### Support Resources
- `MCP_SETUP_GUIDE.md` - Detailed MCP documentation
- `CLAUDE.md` - Technical implementation details
- Console output - Real-time debugging info

## Success Indicators

**Application is working correctly when:**
- ✅ All startup messages show "Connected" or "✅"
- ✅ GUI loads without errors
- ✅ ComfyUI generates images in `images/` folder
- ✅ 3D models appear in `3D/Hy3D/` folder
- ✅ Cinema4D shows imported objects
- ✅ No red error messages in console

**Ready for production use when:**
- ✅ Full pipeline works end-to-end
- ✅ Multiple generations complete successfully
- ✅ Cinema4D integration responds properly
- ✅ Export functionality saves projects correctly