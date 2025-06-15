# KJNodes SetNode/GetNode Fix

## Date: 2025-06-14
## Issue: SetNode/GetNode from KJNodes causing "node does not exist" errors

### Background
KJNodes provides SetNode and GetNode which are JavaScript-based UI nodes that allow "wireless" connections in ComfyUI workflows. They work in the ComfyUI web interface but aren't registered as traditional Python nodes, so they can't be executed via the API.

### Problem
```
Cannot execute because node SetNode does not exist.
Cannot execute because node GetNode does not exist.
Cannot execute because node Label (rgthree) does not exist.
```

### Solution
Since these nodes are essential for the workflow's data flow, we:

1. **Skip these nodes during conversion** - they don't execute, they just pass data
2. **Track their connections** - identify what SetNode stores and what GetNode retrieves
3. **Resolve the connections** - connect nodes directly, bypassing Set/Get nodes

### Implementation

#### 1. Skip UI-only nodes:
```python
# Skip KJNodes SetNode/GetNode - JavaScript-based UI nodes
if node_type in ["SetNode", "GetNode"]:
    self.logger.info(f"Skipping {node_type} node {node_id} - KJNodes JavaScript-based UI node")
    continue

# Skip Label nodes - they're UI-only
if "Label" in node_type:
    self.logger.info(f"Skipping {node_type} node {node_id} - UI-only label node")
    continue
```

#### 2. Track SetNode/GetNode connections:
```python
def _handle_setnode_getnode(self, ui_workflow, api_workflow, link_map):
    """Handle SetNode/GetNode connections by tracking what connects through them"""
    set_nodes = {}  # key -> (source_node_id, output_index)
    get_nodes = {}  # node_id -> key
    
    # Find all SetNodes and what they store
    for node in ui_workflow.get("nodes", []):
        if node_type == "SetNode" and widgets:
            key = widgets[0]  # The storage key
            # Track what connects TO this SetNode
            # That's what needs to connect to GetNodes with same key
```

#### 3. Apply resolved connections:
```python
def _apply_setget_connections(self, api_workflow, connections):
    """Replace GetNode connections with direct connections"""
    # Find inputs connected to GetNodes
    # Replace with the actual source that connected to the SetNode
```

### How It Works

1. **Workflow has**: NodeA → SetNode("size") → ... → GetNode("size") → NodeB
2. **Conversion creates**: NodeA → NodeB (direct connection)
3. **Result**: Same data flow without the UI-only nodes

### Benefits
- Maintains full workflow functionality
- Supports KJNodes' wireless connection pattern
- Works with any key names used in Set/Get nodes
- Preserves all other nodes and connections