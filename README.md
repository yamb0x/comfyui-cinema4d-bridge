# comfy2c4d

[![Status](https://img.shields.io/badge/Status-Active%20Development-orange?style=flat-square)](https://github.com/yamb0x/comfyui-cinema4d-bridge)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-6-green?style=flat-square&logo=qt)](https://www.qt.io/)
[![Cinema4D](https://img.shields.io/badge/Cinema4D-R2024+-red?style=flat-square)](https://www.maxon.net/)

Direct integration of AI latent space models into professional 3D workflows.

## Problem

AI models generate content in isolation. 3D artists manually bridge this gap.
This breaks creative flow and limits understanding what's possible with latest models and PBR texture generation.

## Solution

A focused interface for generating images, 3D meshes, and textures through connected tabs, each triggering ComfyUI workflows while maintaining creative momentum.

- **Image Generation**: Flux, SD 3.5, and any ComfyUI-compatible model
- **3D Generation**: Hunyuan 2.0 mesh creation with direct carryover
- **Texture Generation**: Experimental prompt-driven PBR pipeline
- **Cinema4D Integration**: Natural language control via MCP

## Current Status

| Feature | Status | Notes |
|---------|--------|-------|
| **Image generation** | ✅ Working | Flux + SD 3.5 |
| **3D model creation** | ✅ Working | Hunyuan 2.0 |
| **Texture generation** | ✅ Working | Experimental PBR |
| **Cinema4D integration** | ✅ Working | MCP + NLP commands |

## Quick Links

- **[QUICKSTART.md](QUICKSTART.md)** - Get up and running
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical details
- **[CLAUDE.md](CLAUDE.md)** - AI development guide
- **[Documentation Index](docs/INDEX.md)** - All documentation

## Dependencies

- Python 3.12+
- ComfyUI (localhost:8188)
- Cinema4D R2024+ with Python API
- [ComfyUI MCP Server](https://github.com/joenorton/comfyui-mcp-server)
- [Cinema4D MCP](https://github.com/ttiimmaacc/cinema4d-mcp)

---

Built by [Yambo Studio](https://yambo-studio.com) | Not affiliated with ComfyUI or Maxon