# comfy2c4d

[![Status](https://img.shields.io/badge/Status-Active%20Development-orange?style=flat-square)](https://github.com/yamb0x/comfyui-cinema4d-bridge)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-6-green?style=flat-square&logo=qt)](https://www.qt.io/)
[![Cinema4D](https://img.shields.io/badge/Cinema4D-R2024+-red?style=flat-square)](https://www.maxon.net/)

Direct integration of AI latent space models into professional 3D workflows.

## Problem

AI models generate content in isolation. 3D artists manually bridge this gap manually
This breaks creative flow and limit understanding what's possible with latest models and PBR texture generation.

## Solution

This tool is a response to friction—a way to streamline a process that’s become too fragmented. It introduces a focused interface for generating images, 3D meshes, and textures through a series of connected tabs, each designed to trigger comfyui workflows and carry forward the creative momentum without breaking flow.

The image generation tab is built on top of Flux, supporting SD 3.5 and any model your ComfyUI setup can run. The logic is simple: if your ComfyUI works, the app works. You iterate through prompts, explore results, and select your favorites. Those then feed into mesh generation—currently tailored for Hunyuan 2.0—with direct carryover into a third stage for texturing.

Texture generation here doesn’t follow a standard path. It regenerates visual surfaces through prompt-driven processes, relying on experimental workflows that bend traditional PBR pipelines. Parameters are surfaced selectively, allowing high-level control without micromanaging the graph. This design approach takes cues from procedural thinking—letting complexity exist under the hood, while the user shapes the outcome from above.

It doesn’t pretend to be universal. But for those working with Cinema4D and interested to expand their workflow for 3D models generation, that could be a good starting point.

## What This Does

- Connect ComfyUI workflows to Cinema4D scenes (Based on Yambo ComfyUI Workflows)
- Generate images -> convert to 3D models
- Applying PBR Textures using latent space manipulations 
- Control 3D objects with natural language
- Real-time workflow from idea to scene

## Implementation

Built on MCP protocols for reliable communication.
Python/Qt6 interface, async workflow management.
Works with any ComfyUI workflow through dynamic UI generation (might have bugs but easily fixable - just data type errors sometimes that could break the comfyui json)

## Implications

**Today:** Manual pipeline from AI to 3D  
**Tomorrow:** AI-native 3D content creation  
**Future:** Neural rendering quickly integrated into 3D Workflows (neural rendering, gaussian splats)


```ascii
    ╔═══════════════════════════════════════╗
    ║               S E T U P               ║
    ╚═══════════════════════════════════════╝
```

### Prerequisites
- **Python 3.12+** (tested with 3.12.0)
- **ComfyUI** running at `http://localhost:8188` 
- **Cinema4D R2024+** with Python API enabled
- **Git** for cloning and 16GB+ RAM recommended

### Installation

#### 1. Clone & Install Dependencies
```bash
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
cd comfy-to-c4d
install_dependencies.bat  # Comprehensive dependency installation
```

#### 2. Setup MCP Servers (CRITICAL - App won't work without these)

**ComfyUI MCP Server:**
```bash
# No additional setup needed - ComfyUI works out of the box
# Just ensure ComfyUI is running at localhost:8188
```

**Cinema4D MCP Server:**
```bash
# 1. Install Cinema4D MCP
git clone https://github.com/ttiimmaacc/cinema4d-mcp.git
cd cinema4d-mcp && pip install -r requirements.txt

# 2. In Cinema4D: Script → Script Manager
# 3. Load: mcp_servers/cinema4d-mcp/c4d_mcp_server.py
# 4. Execute to start socket server (shows confirmation dialog)
```

#### 3. Configure Application Paths
```bash
launch.bat  # Opens app
# Go to: Settings → Paths → Configure ComfyUI and Cinema4D paths
# Set your installation directories and save
```

#### 4. Verify Everything Works
```bash
# Check MCP connection status in app console:
# ✅ ComfyUI MCP: Connected
# ✅ Cinema4D MCP: Connected  
# 🚀 Ready to generate!
```

> **Pro Tip:** If MCP servers fail to connect, check the console output for specific error messages and ensure both ComfyUI and Cinema4D are running with the MCP scripts loaded.

**Links:**
- [ComfyUI MCP Server](https://github.com/joenorton/comfyui-mcp-server)
- [Cinema4D MCP](https://github.com/ttiimmaacc/cinema4d-mcp)

```ascii
    ╔═══════════════════════════════════════╗
    ║              S T A T U S              ║
    ╚═══════════════════════════════════════╝
```

| Feature | Status | Notes |
|---------|--------|-------|
| **Image generation** | `[████████████████████] 100%` | Flux + SD 3.5 working |
| **3D model creation** | `[████████████████████] 100%` | Hunyuan 2.0 integration |
| **Texture generation** | `[████████████▒▒▒▒▒▒▒▒] 70%` | PBR workflows experimental |
| **Cinema4D integration** | `[██████████▒▒▒▒▒▒▒▒▒▒] 50%` | MCP + NLP command system |

```bash
$ export COMFYUI_PATH="/path/to/comfyui"
$ export CINEMA4D_PATH="/path/to/c4d"  
$ ./comfy2c4d --mode=experimental
# Ready for AI-native 3D workflow experiments
```

```ascii
    ╔═══════════════════════════════════════╗
    ║         T E C H   S P E C S           ║
    ╚═══════════════════════════════════════╝
```

```yaml
architecture:
  frontend: Qt6 + async Python backend
  protocol: MCP (Model Context Protocol) 
  comms: WebSocket + REST API integration
  
workflow_engine:
  dynamic_ui: Adapts to any ComfyUI node graph
  monitoring: Real-time asset loading & status
  experimental: Yambo's custom PBR pipeline
  
integrations:
  - comfyui: flux, sd3.5, hunyuan2.0  
  - cinema4d: python API + MCP bridge
  - latent_space: prompt-driven texture gen
```

See [docs/](docs/) for implementation details.

## Contributing

Standard Python/Qt6 codebase.  
Issues and PRs welcome.

---

**Note:** This bridges existing tools using Yambo workflows inside ComfyUI. Not affiliated with ComfyUI or Maxon.

---

```ascii
    ╭──────────────────────────────────────╮
    │  Built by Yambo (yambo-studio.com)   │
    │     + Multi-Agent Cloud Workflow     │
    ╰──────────────────────────────────────╯
```