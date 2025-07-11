# MCP Servers Setup Guide

This guide explains how to set up and use the MCP (Model Context Protocol) servers for ComfyUI and Cinema4D integration.

## Overview

The application uses two MCP servers:
1. **ComfyUI MCP Server**: Interfaces with ComfyUI for image generation
2. **Cinema4D MCP Server**: Executes Python scripts in Cinema4D

## Prerequisites

- ComfyUI running at `http://localhost:8188`
- Cinema4D 2024+ installed
- Python virtual environment set up (run `setup_final.bat` first)

## Quick Setup

### 1. Install MCP Dependencies
```bash
Setup MCP Servers.bat
```

### 2. Start ComfyUI MCP Server
```bash
Start ComfyUI MCP Server.bat
```

### 3. Setup Cinema4D MCP Server
1. Open Cinema4D
2. Go to **Script → Script Manager**
3. Load file: `mcp_servers/cinema4d-mcp/c4d_mcp_server.py`
4. Click **Execute** to start the socket server

### 4. Launch Main Application
```bash
launch.bat
```

## Detailed Setup

### ComfyUI MCP Server

The ComfyUI MCP server provides these tools:
- `generate_image`: Generate images using ComfyUI workflows
- `get_models`: List available models
- `get_queue_status`: Check generation queue
- `interrupt_execution`: Stop current generation

**Files:**
- `mcp_servers/comfyui-mcp-server/server.py` - Main MCP server
- `mcp_servers/comfyui-mcp-server/comfyui_client.py` - ComfyUI API client
- `mcp_servers/comfyui-mcp-server/requirements.txt` - Dependencies

**Configuration:**
The server connects to ComfyUI at `http://localhost:8188` by default.

### Cinema4D MCP Server

The Cinema4D MCP server provides these tools:
- `execute_python`: Execute arbitrary Python in C4D
- `import_object`: Import 3D files (OBJ, FBX, etc.)
- `create_primitive`: Create basic shapes
- `create_material`: Create materials
- `assign_material`: Apply materials to objects
- `create_light`: Add lighting
- `save_project`: Save C4D project
- `get_scene_objects`: List scene contents
- `get_status`: Check connection status

**Files:**
- `mcp_servers/cinema4d-mcp/server.py` - Main MCP server
- `mcp_servers/cinema4d-mcp/c4d_mcp_server.py` - Cinema4D plugin script
- `mcp_servers/cinema4d-mcp/c4d_plugin.py` - Alternative plugin version

**Configuration:**
The server uses socket communication on port `54321`.

## Usage

### Starting the Servers

1. **ComfyUI MCP Server**:
   - Automatically starts when running `Start ComfyUI MCP Server.bat`
   - Requires ComfyUI to be running first

2. **Cinema4D MCP Server**:
   - Must be manually started in Cinema4D Script Manager
   - Load and execute `c4d_mcp_server.py`
   - Shows confirmation dialog when started

### Testing the Connection

The main application will show connection status in the console:
- ✅ Green: Connected successfully
- ❌ Red: Connection failed
- ⚠️ Yellow: Partial connection

### Troubleshooting

#### ComfyUI MCP Server Issues:
- **"Failed to connect to ComfyUI"**: Make sure ComfyUI is running at localhost:8188
- **"Workflow file not found"**: Check that workflow JSON files exist in `workflows/` directory
- **"Failed to queue prompt"**: Verify ComfyUI is accepting API requests

#### Cinema4D MCP Server Issues:
- **"Not connected to Cinema4D"**: Load and run the C4D script manually
- **"Socket connection failed"**: Check if port 54321 is available
- **"Script execution failed"**: Verify Python syntax in C4D scripts

#### General Issues:
- **"Virtual environment not found"**: Run `setup_final.bat` first
- **"MCP dependencies missing"**: Run `Setup MCP Servers.bat`
- **"Permission denied"**: Run as administrator

## Advanced Configuration

### Custom Workflows

Place custom ComfyUI workflow JSON files in:
- `workflows/` (main directory)
- `mcp_servers/comfyui-mcp-server/workflows/`

### Port Configuration

To change the Cinema4D socket port:
1. Edit `mcp_servers/cinema4d-mcp/c4d_mcp_server.py` line 91
2. Edit `src/mcp/cinema4d_client.py` line 52
3. Update `.env` file if needed

### Development Mode

For development, you can run the MCP servers directly:

```bash
# ComfyUI MCP Server
cd mcp_servers/comfyui-mcp-server
python server.py

# Cinema4D MCP Server (run in C4D)
# Load and execute c4d_mcp_server.py in Script Manager
```

## Architecture

```
Main Application
    ├── ComfyUI Client ──→ ComfyUI MCP Server ──→ ComfyUI API
    └── Cinema4D Client ──→ Cinema4D Socket Server ──→ Cinema4D
```

The MCP servers act as bridges between the main application and the target applications, providing a standardized interface for complex operations.

## Dependencies

### Python Packages
- `mcp>=0.5.0` - Model Context Protocol framework
- `aiohttp>=3.8.0` - HTTP client for ComfyUI
- `websockets>=11.0.0` - WebSocket support
- `loguru>=0.7.0` - Logging

### External Applications
- ComfyUI (with API enabled)
- Cinema4D 2024+

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all prerequisites are installed
3. Run `verify_installation.bat` to check setup
4. Try `repair_tool.bat` for common fixes

For development questions, refer to:
- [ComfyUI MCP Server](https://github.com/joenorton/comfyui-mcp-server)
- [Cinema4D MCP](https://github.com/ttiimmaacc/cinema4d-mcp)