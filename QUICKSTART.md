# Quick Start Guide

Get comfy2c4d running in under 10 minutes.

## Prerequisites

- Python 3.12+ installed
- ComfyUI running at `http://localhost:8188`
- Cinema4D R2024+ with Python API (optional)
- 8GB+ RAM recommended
- CUDA-compatible GPU for optimal performance

## Installation Steps

### 1. Clone and Setup

```bash
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
cd comfy-to-c4d

# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure MCP Servers

**ComfyUI** - No additional setup needed, just ensure it's running at localhost:8188

**Cinema4D MCP**:
1. Clone: `git clone https://github.com/ttiimmaacc/cinema4d-mcp.git`
2. In Cinema4D: Script → Script Manager
3. Load and execute: `c4d_mcp_server.py`
4. Confirm the server started dialog

### 3. Launch Application

```bash
# Windows
python main.py

# Linux/macOS  
python3 main.py
```

### 4. Configure Paths

1. Go to File → Settings → Paths
2. Set your ComfyUI directory
3. Set your Cinema4D directory
4. Save and restart

## First Workflow

1. **Image Tab**: Enter a prompt, click Generate
2. **3D Tab**: Select generated images, click "Generate 3D"
3. **Texture Tab**: Apply textures to your models
4. **Cinema4D Tab**: Use natural language to control objects

## Common Issues

**Port already in use**: Change port in `config/.env`
**Import errors**: Ensure virtual environment is activated
**MCP connection failed**: Check both servers are running
**Black UI elements**: Update Qt6 to latest version

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [CLAUDE.md](CLAUDE.md) for development patterns
- See [docs/](docs/) for detailed guides