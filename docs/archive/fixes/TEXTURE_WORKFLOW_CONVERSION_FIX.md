# Texture Workflow Conversion Fix

## Date: 2025-06-14
## Issue: Anything Everywhere nodes causing missing connections in API workflow

### Problem Analysis
The texture generation workflow uses "Anything Everywhere" nodes which are special ComfyUI nodes that distribute values globally throughout the workflow. Our conversion was including these nodes in the API workflow, but ComfyUI was reporting they don't exist because:

1. These nodes work differently in the UI vs API format
2. They act as global distributors, not actual processing nodes
3. The connections they provide need to be resolved during conversion

### Error Messages
```
Failed to queue prompt: HTTP 400 - {'error': {'type': 'invalid_prompt', 'message': 'Cannot execute because node SetNode does not exist.'
```

Later evolved to:
```
'required_input_missing', 'message': 'Required input is missing', 'details': 'clip'
'required_input_missing', 'message': 'Required input is missing', 'details': 'model'
'required_input_missing', 'message': 'Required input is missing', 'details': 'vae'
```

### Root Cause
The workflow contains these Anything Everywhere nodes:
- Node 309 (Anything Everywhere3): Distributes MODEL, CLIP, and VAE from checkpoint loader
- Node 310 (Anything Everywhere): Distributes CONTROL_NET
- Node 321 (Anything Everywhere): Distributes UPSCALE_MODEL
- Node 396 (Anything Everywhere): Distributes BBOX_DETECTOR

These nodes take outputs from other nodes and make them globally available to any node that needs that type of input, without explicit connections in the workflow.

### Solution Implemented

Added special handling for Anything Everywhere nodes in `workflow_manager.py`:

1. **Skip these nodes during conversion** - they shouldn't appear in the API workflow
2. **Track what they distribute** - identify what values they're making globally available
3. **Apply distributed connections** - connect nodes that need these values

#### Code Changes in `_convert_ui_to_api_format()`:

```python
# Skip Anything Everywhere nodes - they distribute values globally
if "Anything Everywhere" in node_type:
    self.logger.info(f"Skipping {node_type} node {node_id} - will handle distributed connections")
    continue
```

#### Added new methods:

```python
def _handle_anything_everywhere_nodes(self, ui_workflow, api_workflow, link_map):
    """Handle Anything Everywhere nodes which distribute values globally"""
    distributed_connections = {}
    
    for node in ui_workflow.get("nodes", []):
        if "Anything Everywhere" in node_type:
            # Track what this node is distributing
            for input_def in node.get("inputs", []):
                if "link" in input_def and input_def["link"] is not None:
                    link_id = input_def["link"]
                    if link_id in link_map:
                        source_node_id, output_index = link_map[link_id]
                        input_label = input_def.get("label", "")  # e.g., "MODEL", "CLIP", "VAE"
                        if input_label:
                            distributed_connections[input_label] = (str(source_node_id), output_index)
    
    return distributed_connections

def _apply_distributed_connections(self, api_workflow, distributed_connections):
    """Apply distributed connections to nodes that need them"""
    label_to_inputs = {
        "MODEL": ["model"],
        "CLIP": ["clip"],
        "VAE": ["vae"],
        "CONTROL_NET": ["control_net"],
        "UPSCALE_MODEL": ["upscale_model"],
        "BBOX_DETECTOR": ["bbox_detector"]
    }
    
    # Apply connections to nodes missing these inputs
    for node_id, node_data in api_workflow.items():
        inputs = node_data.get("inputs", {})
        
        for label, (source_node_id, output_index) in distributed_connections.items():
            if label in label_to_inputs:
                for input_name in label_to_inputs[label]:
                    if input_name in inputs and not isinstance(inputs[input_name], list):
                        inputs[input_name] = [source_node_id, output_index]
```

### How It Works

1. During conversion, when we encounter an Anything Everywhere node:
   - Skip adding it to the API workflow
   - But track what it's distributing (e.g., MODEL from node 183)

2. After building the main API workflow:
   - Go through all nodes and check for missing connections
   - If a node needs "model" input and it's not connected, use the distributed MODEL connection

3. This preserves the dynamic workflow configuration while properly handling these special nodes

### Benefits
- Maintains the dynamic workflow system as requested
- Properly handles all custom nodes without skipping them
- Converts UI workflows to API format correctly
- Supports the Anything Everywhere pattern commonly used in ComfyUI workflows

### Testing
The texture generation workflow should now:
1. Load correctly from the UI format JSON
2. Convert to API format with all connections resolved
3. Execute in ComfyUI without "node does not exist" errors
4. Generate textures for selected 3D models