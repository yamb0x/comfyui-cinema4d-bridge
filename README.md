# ComfyUI Cinema4D Bridge

Direct integration of AI latent space models into professional 3D workflows.

## Problem

AI models generate content in isolation. 3D artists manually bridge this gap.
This breaks creative flow and limits what's possible.

## Solution

A bridge that puts AI generation directly inside Cinema4D.
Latent space models become native 3D tools.

## What This Does

- Connect ComfyUI workflows to Cinema4D scenes
- Generate images, convert to 3D models, apply textures  
- Control 3D objects with natural language
- Real-time workflow from idea to scene

## Implementation

Built on MCP protocol for reliable communication.
Python/Qt6 interface, async workflow management.
Works with any ComfyUI workflow through dynamic UI generation.

## Implications

**Today:** Manual pipeline from AI to 3D  
**Tomorrow:** AI-native 3D content creation  
**Future:** Neural rendering integrated into professional tools  

This is infrastructure for that future.

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

**Image generation:** Working  
**3D model creation:** Working  
**Texture generation:** In progress  
**Cinema4D integration:** 80% complete  

Ready for experimentation, not production.

## Technical Details

- **Architecture:** Qt6 frontend, async Python backend
- **Protocol:** MCP for Cinema4D communication  
- **Workflows:** Dynamic UI adapts to any ComfyUI node graph
- **Integration:** File monitoring, real-time status updates

See [docs/](docs/) for implementation details.

## Contributing

Standard Python/Qt6 codebase.  
Issues and PRs welcome.

---

**Note:** This bridges existing tools. Not affiliated with ComfyUI or Maxon.