# Workflow Customization Guide

## Understanding ComfyUI Workflows

ComfyUI workflows are JSON files that define a node graph for AI generation. Each node has:
- A unique ID
- A class type (node type)
- Input connections and parameters
- Output connections

## Current Workflows

### 1. Image Generation Workflow (`generate_images.json`)

This workflow uses:
- FLUX model for high-quality image generation
- Multiple LoRA models for style control
- Advanced sampling with guidance

Key nodes to customize:
- **CheckpointLoaderSimple** (ID: 5): Change base model
- **CLIPTextEncode** (ID: 12, 13): Positive/negative prompts
- **KSampler** (ID: 10): Sampling parameters
- **EmptySD3LatentImage** (ID: 8): Image dimensions

### 2. 3D Generation Workflow (`generate_3D.json`)

This workflow uses:
- Hy3D-2 model for image-to-3D conversion
- Background removal with rembg
- Multi-view rendering and texturing

Key nodes to customize:
- **Hy3DModelLoader** (ID: 52): 3D model selection
- **Hy3DGenerateMesh** (ID: 53): Mesh generation parameters
- **Hy3DPostprocessMesh** (ID: 55): Mesh optimization
- **Hy3DExportMesh** (ID: 87, 88): Export format

## Modifying Workflows

### Adding a New Model

To use a different checkpoint model:

```json
{
  "5": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "your_model_name.safetensors"  // Change this
    }
  }
}
```

### Changing Image Resolution

Modify the EmptySD3LatentImage node:

```json
{
  "8": {
    "class_type": "EmptySD3LatentImage",
    "inputs": {
      "width": 1024,   // Change width
      "height": 1024,  // Change height
      "batch_size": 1
    }
  }
}
```

### Adding LoRA Models

To add or modify LoRA models:

```json
{
  "6": {
    "class_type": "LoraLoader",
    "inputs": {
      "model": ["5", 0],  // Connect to previous model
      "clip": ["5", 1],   // Connect to CLIP
      "lora_name": "your_lora.safetensors",
      "strength_model": 0.8,  // Model influence (0-1)
      "strength_clip": 0.8    // CLIP influence (0-1)
    }
  }
}
```

### Modifying Sampling Parameters

In the KSampler node:

```json
{
  "10": {
    "class_type": "KSampler",
    "inputs": {
      "seed": -1,           // -1 for random
      "steps": 20,          // Sampling steps (quality vs speed)
      "cfg": 7.0,           // Classifier-free guidance (1-30)
      "sampler_name": "euler",  // Algorithm
      "scheduler": "normal",    // Step scheduler
      "denoise": 1.0       // Denoising strength
    }
  }
}
```

Available samplers:
- `euler`, `euler_ancestral`
- `heun`, `dpm_2`, `dpm_2_ancestral`
- `lms`, `dpm_fast`, `dpm_adaptive`
- `dpmpp_2s_ancestral`, `dpmpp_sde`
- `dpmpp_2m`, `dpmpp_3m_sde`
- `ddim`, `uni_pc`

## Creating Custom Workflows

### Step 1: Design in ComfyUI

1. Open ComfyUI web interface
2. Create your node graph
3. Save workflow (API format)
4. Copy to `workflows/` directory

### Step 2: Prepare for Bridge

Ensure your workflow has:
1. **Text input nodes** with identifiable names:
   ```json
   "_meta": {
     "title": "CLIP Text Encode (Positive Prompt)"
   }
   ```

2. **Output nodes** saving to correct directories:
   ```json
   {
     "class_type": "Image Save",
     "inputs": {
       "images": ["previous_node", 0],
       "filename_prefix": "ComfyUI",
       "path": "D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d/images"
     }
   }
   ```

3. **Consistent node connections** using format:
   ```json
   "inputs": {
     "model": ["node_id", output_slot]
   }
   ```

### Step 3: Update Configuration

In `config/app_config.json`:

```json
{
  "workflows": {
    "image_workflow": "your_custom_workflow.json",
    "model_3d_workflow": "generate_3D.json"
  }
}
```

## Advanced Workflow Features

### Conditional Execution

Add switches for different paths:

```json
{
  "20": {
    "class_type": "ImpactSwitch",
    "inputs": {
      "input": ["previous", 0],
      "on_true": ["path_a", 0],
      "on_false": ["path_b", 0],
      "boolean": true
    }
  }
}
```

### Multi-Stage Processing

Chain multiple samplers:

```json
{
  "15": {
    "class_type": "KSampler",
    "inputs": {
      "model": ["10", 0],     // From first sampler
      "latent_image": ["10", 0],  // Previous output
      "steps": 10,
      "denoise": 0.5          // Partial denoise for refinement
    }
  }
}
```

### Batch Processing

Enable batch generation:

```json
{
  "inputs": {
    "batch_size": 4,  // Generate 4 variations
    "seed": -1        // Different seed each
  }
}
```

## Parameter Injection

The bridge automatically injects parameters into workflows:

### Supported Parameters

```python
params = {
    "positive_prompt": "your prompt",
    "negative_prompt": "avoid this",
    "width": 1024,
    "height": 1024,
    "batch_size": 1,
    "seed": 123456,
    "steps": 20,
    "cfg": 7.0,
    "sampler_name": "euler",
    "scheduler": "normal",
    "denoise": 1.0,
    "checkpoint": "model.safetensors",
    "vae": "vae.safetensors"
}
```

### Custom Parameter Mapping

To support custom nodes, modify `workflow_manager.py`:

```python
param_mapping = {
    "your_param": {
        "class_types": ["YourNodeType"],
        "input_field": "field_name"
    }
}
```

## Workflow Validation

The bridge validates workflows before execution:

1. **Structure validation**: Ensures valid JSON
2. **Node validation**: Checks required fields
3. **Connection validation**: Verifies node links exist

### Common Validation Errors

- "Node X missing 'class_type'": Add class_type field
- "Node X input connects to non-existent node": Fix node ID
- "Invalid JSON": Check syntax with JSON validator

## Best Practices

### 1. Use Descriptive Names

Add metadata to nodes:

```json
"_meta": {
  "title": "Main Image Generator"
}
```

### 2. Group Related Nodes

Use reroute nodes for organization:

```json
{
  "50": {
    "class_type": "Reroute",
    "inputs": {
      "": ["source", 0]
    }
  }
}
```

### 3. Document Parameters

Add note nodes with instructions:

```json
{
  "100": {
    "class_type": "Note",
    "widgets_values": [
      "Adjust CFG between 5-9 for best results"
    ]
  }
}
```

### 4. Test Incrementally

1. Test workflow in ComfyUI first
2. Save and validate JSON
3. Test parameter injection
4. Run through bridge

## Troubleshooting Workflows

### Debug Mode

Enable detailed logging:

```python
# In workflow_manager.py
logger.debug(f"Injecting into node {node_id}: {params}")
```

### Common Issues

1. **Prompts not updating**: Check _meta titles contain "positive"/"negative"
2. **Wrong output directory**: Verify save node paths
3. **Missing nodes**: Install required ComfyUI extensions
4. **Connection errors**: Validate node IDs and output slots

### Workflow Analysis Tool

```python
# Quick script to analyze workflow
import json

with open("workflows/your_workflow.json", "r") as f:
    workflow = json.load(f)

# List all nodes
for node_id, node in workflow.items():
    print(f"Node {node_id}: {node.get('class_type', 'Unknown')}")
    
# Find prompt nodes
for node_id, node in workflow.items():
    if node.get("class_type") == "CLIPTextEncode":
        title = node.get("_meta", {}).get("title", "")
        print(f"Prompt node {node_id}: {title}")
```