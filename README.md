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

It doesn’t pretend to be universal. But for those working with Cinems4D and interested to expend their workflow for 3D models generation, that could be a good starting point.

## What This Does

- Connect ComfyUI workflows to Cinema4D scenes (Based on Yambo ComfyUI Workflows)
- Generate images -> convert to 3D models
- Applying PBR Texturees using latent space manipulations 
- Control 3D objects with natural language
- Real-time workflow from idea to scene

## Implementation

Built on MCP protocols for reliable communication.
Python/Qt6 interface, async workflow management.
Works with any ComfyUI workflow through dynamic UI generation (might have bugs but easily fixable - just data type erros sometimes that could break the comfyui json)

## Implications

**Today:** Manual pipeline from AI to 3D  
**Tomorrow:** AI-native 3D content creation  
**Future:** Neural rendering quickly integrated into 3D Workflows (neural rendering, guessian splatts)


## Setup

**Requirements:** Python 3.12+, ComfyUI, Cinema4D R2024+

```bash
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
cd comfy-to-c4d
install_dependencies.bat
# Configure paths in .env
launch.bat
```

## Status

| Feature | Status |
|---------|--------|
| **Image generation** | ✅ Working |
| **3D model creation** | ✅ Working |
| **Texture generation** | 🔄 In progress |
| **Cinema4D integration** | 🔧 50% complete |

Define Environment variables → then ready for experimentation, not production.

## Technical Details

- **Architecture:** Qt6 frontend, async Python backend
- **Protocol:** MCP for Cinema4D and ComfyUI communication  
- **Workflows:** Dynamic UI adapts to any ComfyUI node graph
- **Integration:** File monitoring, real-time status updates and loading of generated assets from ComfyUI

See [docs/](docs/) for implementation details.

## Contributing

Standard Python/Qt6 codebase.  
Issues and PRs welcome.

---

**Note:** This bridges existing tools using Yambo workflows inside ComfyUI. Not affiliated with ComfyUI or Maxon.

---

**Built by [Yambo Studio](https://www.yambo-studio.com/) - Professional 3D Content Creation**