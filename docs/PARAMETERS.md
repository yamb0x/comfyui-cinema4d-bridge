# Parameter Extraction and UI Generation Guide

How the dynamic UI system adapts to any ComfyUI workflow.

## Overview

The application automatically generates UI widgets based on ComfyUI workflow nodes, eliminating hardcoded interfaces. This system allows compatibility with any workflow without code changes.

## System Components

```
Workflow JSON → Parameter Extractor → Widget Factory → Dynamic UI
                        ↓                    ↓              ↓
                  Node Analysis      Widget Creation   User Input
                        ↓                    ↓              ↓
                Parameter Config → Workflow Injection → ComfyUI
```

## Parameter Extraction Process

### 1. Workflow Loading
```python
# workflow_manager.py
workflow = load_workflow("workflow.json")
nodes = workflow.get("nodes", [])
```

### 2. Node Analysis
The system identifies:
- Node types and IDs
- Input parameters (widgets)
- Default values
- Connection points

### 3. Node Filtering Rules

**Hidden Nodes** (not shown in UI):
- Utility nodes: Reroute, Note, PrimitiveNode
- Internal nodes: KJNodes, efficiency loaders
- Output nodes: SaveImage, PreviewImage

**Shown Nodes**:
- Model loaders (checkpoint, LoRA, VAE)
- Sampling nodes (KSampler)
- Conditioning nodes (CLIP text encode)
- Control nodes (user-defined parameters)

## Widget Generation Rules

### Widget Type Mapping

| ComfyUI Type | UI Widget | Notes |
|--------------|-----------|-------|
| STRING | QLineEdit or QComboBox | Combo if choices provided |
| INT | QSpinBox | With min/max constraints |
| FLOAT | QDoubleSpinBox | Precision based on step |
| BOOLEAN | QCheckBox | True/False toggle |
| COMBO | QComboBox | Predefined options |
| SEED | QSpinBox | Special handling for -1 |

### Dynamic Widget Creation
```python
def create_widget_for_input(input_type, default_value, constraints):
    if input_type == "INT":
        widget = QSpinBox()
        widget.setRange(constraints.get("min", 0), 
                       constraints.get("max", 99999))
    elif input_type == "FLOAT":
        widget = QDoubleSpinBox()
        widget.setDecimals(3)
    elif input_type == "STRING" and "choices" in constraints:
        widget = QComboBox()
        widget.addItems(constraints["choices"])
    # ... more types
```

## Parameter Injection

### Workflow Update Process
1. Collect values from UI widgets
2. Map to node IDs in workflow
3. Update node inputs
4. Preserve connections
5. Submit to ComfyUI

### Special Handling

**Prompt Injection**:
```python
# Positive prompt goes to specific nodes
if node_type == "CLIPTextEncode" and is_positive_prompt(node):
    node["inputs"]["text"] = positive_prompt
```

**Image/Model Selection**:
```python
# Cross-tab data flow
selected_images = self.unified_object_selector.get_selected_images()
node["inputs"]["images"] = selected_images
```

## Node Parameter Definitions

### Standard Nodes

**CheckpointLoaderSimple**:
- ckpt_name: Model file selection

**KSampler**:
- seed: Random seed (-1 for random)
- steps: Sampling steps (1-150)
- cfg: Guidance scale (1.0-30.0)
- sampler_name: Sampling method
- scheduler: Scheduling algorithm
- denoise: Denoising strength

**CLIPTextEncode**:
- text: Prompt text (multiline)

**EmptyLatentImage**:
- width: Image width (64-8192)
- height: Image height (64-8192)
- batch_size: Batch count (1-64)

## Advanced Features

### Cross-Tab Persistence
Parameters persist across tabs using `unified_parameters_state.json`:
- Positive/negative prompts
- Selected images/models
- Generation settings

### Model Scanning
Dynamic discovery of available models:
```python
# Scans ComfyUI model directories
models = scan_model_directory(comfyui_path + "/models/checkpoints/")
dropdown.addItems(models)
```

### Workflow Compatibility

**Node Conversion**:
```python
# Convert custom nodes to standard
if node["class_type"] == "Image Save":
    node["class_type"] = "SaveImage"
```

**Version Handling**:
- Supports both legacy and current node formats
- Automatic migration of old workflows

## Best Practices

1. **Widget Naming**: Use node_id in widget names for tracking
2. **Value Validation**: Respect min/max constraints from workflow
3. **Default Values**: Always provide sensible defaults
4. **Error Handling**: Gracefully handle missing nodes
5. **Performance**: Lazy load widgets only for visible nodes

## Troubleshooting

### Widget Not Appearing
- Check if node is in hidden list
- Verify node has input parameters
- Ensure workflow JSON is valid

### Values Not Persisting
- Check parameter config file
- Verify widget has proper node_id
- Ensure save is called on changes

### Workflow Execution Fails
- Validate all required inputs filled
- Check node connections preserved
- Verify ComfyUI compatibility

## Extending the System

To add new node support:
1. No code changes needed!
2. System auto-detects from workflow
3. Widgets generated automatically
4. Just ensure node follows ComfyUI standards

The beauty of this system is its flexibility - any valid ComfyUI workflow works without modification.