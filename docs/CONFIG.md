# Configuration Files Guide

Complete reference for all JSON configuration files.

## Overview

The application uses JSON files to store configuration, state, and reference data. All config files are located in the `/config/` directory.

## Core Configuration Files

### app_config.json
**Purpose**: Master application configuration

```json
{
  "paths": {
    "comfyui_path": "D:/Comfy3D_WinPortable",
    "cinema4d_path": "C:/Program Files/Maxon Cinema 4D 2024"
  },
  "workflows": {
    "image_workflow": "image_generation_flux_v01.json",
    "model_3d_workflow": "3D_gen_Hunyuan2_onlymesh_v04.json"
  },
  "mcp": {
    "comfyui_server_url": "http://127.0.0.1:8188",
    "cinema4d_port": 54321,
    "timeout": 30,
    "max_retries": 3
  },
  "ui": {
    "theme": "dark",
    "grid_columns": 4,
    "preview_size": 256
  }
}
```

**Key Fields**:
- `paths`: Software installation directories
- `workflows`: Default workflow files
- `mcp`: Server connection settings
- `ui`: Interface preferences

### 3d_parameters_config.json / image_parameters_config.json
**Purpose**: Store workflow parameter states

```json
{
  "selected_nodes": ["37", "9", "11"],
  "node_info": {
    "37": {
      "type": "LLMInferencing",
      "id": "37",
      "title": "LLM Inferencing",
      "supported": true,
      "widgets_values": ["a 3d model of a dragon", 1234]
    }
  },
  "workflow_file": "3D_gen_Hunyuan2_onlymesh_v04.json"
}
```

**Key Fields**:
- `selected_nodes`: Active nodes shown in UI
- `node_info`: Parameter values per node
- `workflow_file`: Current workflow reference

### discovered_node_types.json
**Purpose**: Registry of all ComfyUI nodes found in workflows

```json
{
  "KSampler": {
    "first_seen": "2024-06-10T12:30:00Z",
    "description": "Dynamically discovered from workflow"
  },
  "SaveImage": {
    "first_seen": "2024-06-10T12:30:00Z",
    "description": "Dynamically discovered from workflow"
  }
}
```

## Reference Data Files

### primitive_defaults.json
**Purpose**: Default parameters for Cinema4D primitives

```json
{
  "sphere": {
    "pos_x": 0, "pos_y": 0, "pos_z": 0,
    "radius": 200,
    "segments": 24,
    "type": 0
  },
  "cube": {
    "pos_x": 0, "pos_y": 0, "pos_z": 0,
    "size_x": 200, "size_y": 200, "size_z": 200,
    "segments_x": 1, "segments_y": 1, "segments_z": 1
  }
}
```

### magic_prompts_positive.json / magic_prompts_negative.json
**Purpose**: Pre-defined prompt templates

```json
{
  "Photorealistic": "photorealistic, highly detailed, 8k resolution",
  "Artistic": "artistic, painterly, impressionist style",
  "Low Quality": "blurry, low resolution, pixelated, artifacts"
}
```

### unified_parameters_state.json
**Purpose**: Cross-tab parameter persistence

```json
{
  "positive_prompt": "a beautiful landscape",
  "negative_prompt": "ugly, distorted",
  "selected_images": ["image_001.png", "image_002.png"],
  "last_workflow": "image_generation_flux_v01.json"
}
```

## Workflow Files

Located in `/workflows/` subdirectories:
- `/image_generation/` - 2D image workflows
- `/3d_generation/` - 3D model workflows
- `/texture_generation/` - Texture application workflows

## Configuration Relationships

```
app_config.json
    ├── References workflow files
    ├── Defines directory paths
    └── Sets server endpoints
    
parameter_configs (3d/image)
    ├── Store runtime state
    ├── Reference workflow files
    └── Track selected nodes
    
discovered_node_types.json
    └── Registry populated from workflows
    
Reference files (prompts/primitives)
    └── Standalone UI data
```

## Best Practices

1. **Backup Before Editing**: Keep copies of working configs
2. **Path Formats**: Use forward slashes even on Windows
3. **JSON Validation**: Ensure valid JSON syntax
4. **Workflow Compatibility**: Parameter configs must match workflow structure
5. **Version Control**: Track config changes in git

## Common Issues

### Missing Nodes
If UI shows "unsupported node":
1. Check node exists in workflow file
2. Verify node type in discovered_node_types.json
3. Restart app to re-parse workflows

### Parameter Persistence
If parameters reset:
1. Check unified_parameters_state.json
2. Verify workflow_file matches actual file
3. Ensure write permissions on config directory

### Path Errors
If files not found:
1. Use absolute paths in app_config.json
2. Verify paths exist and are accessible
3. Check forward slash usage

## Environment Variables

Additional configuration via `.env` file:
```env
COMFYUI_PATH="D:/Comfy3D_WinPortable"
CINEMA4D_PATH="C:/Program Files/Maxon Cinema 4D 2024"
COMFY_C4D_DEBUG=1  # Enable debug logging
```