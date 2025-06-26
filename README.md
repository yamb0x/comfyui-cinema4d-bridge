================================================================================
                          COMFYUI TO CINEMA4D BRIDGE
================================================================================

    Connecting AI generation workflows 
    with Cinema4D 3D world building.

--------------------------------------------------------------------------------

## Overview

This application addresses the workflow gap between AI generation tools and 
professional 3D software. Rather than manual file transfers and textures linking, 
it provides a unified interface that maintains creative momentum
across image generation, 3D modeling, texture creation, and AI tools.

The system dynamically adapts to any ComfyUI workflow through runtime analysis
and automatic UI generation, ensuring compatibility without dependencies on
custom nodes or specific configurations.

## Architecture

    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   Application   │    │   Workflow       │    │   Integration   │
    │     Layer       │────│    Manager       │────│     Layer       │
    │                 │    │                  │    │                 │
    │ • PyQt6 UI      │    │ • Dynamic UI     │    │ • ComfyUI API   │
    │ • Tab System    │    │ • Node Convert   │    │ • Cinema4D MCP  │
    │ • State Mgmt    │    │ • Parameter Map  │    │ • File System   │
    └─────────────────┘    └──────────────────┘    └─────────────────┘

## Current Status

┌─────────────────────┬───────────┬────────────────────────────────┐
│ Component           │ Status    │ Notes                          │
├─────────────────────┼───────────┼────────────────────────────────┤
│ Image Generation    │ Complete  │ Universal workflow support     │
│ 3D Model Creation   │ Complete  │ Hunyuan 3D with live preview  │
│ Texture Generation  │ Working   │ PBR pipeline implementation    │
│ Cinema4D Bridge     │ 80%       │ MCP integration active         │
│ Dynamic UI System   │ Complete  │ Runtime workflow adaptation    │
└─────────────────────┴───────────┴────────────────────────────────┘

## Features

**Image Generation**
- Universal ComfyUI workflow compatibility
- Dynamic UI generation from workflow analysis
- Automatic custom node conversion
- Cross-tab selection persistence

**3D Model Creation**  
- Hunyuan3D 2.0/Tripo3D integration 
- Real-time Three.js 3D Viewers
- Automatic custom node conversion
- Cross-tab selection persistence

**Texture Generation**
- PBR material pipeline
- Real-time Three.js 3D Viewers with PBR material support
- Procedural texture synthesis via prompt
- Cinema4D material integration

**Cinema4D Integration**
- Model Context Protocol communication
- NLP Dictionary configured
- Implementing Generated 3D models to Cinema4D

## Next Features (For a complete working bridge) by priority:

**Texture Generation**
- Fix Texture Generation Workflow (need to debug issues we have)
- Test and support batch generating texture for multiple models

**Cinema4D Integration**
- Model Context Protocol communication
- NLP Dictionary configured 80% - It was done long time ago and we need to test again that we are able to trigger all the commands in cinema4D from the NLP Dictionary
- NEW PLAN: i Want to replace the NLP system we planned initially to claude code sdk: https://docs.anthropic.com/en/docs/claude-code/sdk (a smart AI that is able to create much more complex scenes using the nlp dictionary we made and claude ai and python capabilites)

**Settings, debug, optimiziations**
- Consistet settings menu and sub-tabs working across the app
- Fixing heavy debug we having and overall optimizations for speed and performance
- fix and improve "magic prompt configuration" menu

**3D Model Creation**  
- Add different 3D View suppoort for 3d model (untextured models)


## Quick Start

### Prerequisites
- Python 3.12+
- ComfyUI running on localhost:8188
- Cinema4D R2024+ (optional)

### Installation
```bash
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
cd comfyui-cinema4d-bridge

python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
python main.py
```

### Configuration
Copy `.env.example` to `.env` and configure paths as needed.
The application will auto-detect ComfyUI on first run.

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Detailed setup guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical implementation
- [docs/](docs/) - Complete documentation index
- [CLAUDE.md](CLAUDE.md) - Development patterns

## Technical Details

**Frontend**: PyQt6 with asynchronous image loading and smart caching
**Backend**: Python with asyncio event loop management  
**3D Rendering**: Three.js integration for real-time preview
**AI Integration**: ComfyUI API with automatic node conversion
**Cinema4D**: Python API with MCP communication layer

**Key Innovations**:
- Runtime workflow analysis and UI generation
- Automatic custom node conversion to standard equivalents  
- Cross-application state synchronization
- Memory-efficient asset management with lazy loading

## Requirements

- Python 3.12+
- ComfyUI with API enabled
- 8GB+ RAM recommended
- CUDA-compatible GPU for optimal performance

--------------------------------------------------------------------------------

This project aims to bridge the gap between AI generation and professional 3D
workflows through careful engineering and minimal dependencies.

MIT License | Not affiliated with ComfyUI or Maxon