# Utility Nodes Skip Fix

## Date: 2025-06-14
## Issue: SetNode/GetNode causing "node does not exist" errors

### Problem
ComfyUI was returning errors like:
```
Cannot execute because node SetNode does not exist.
Cannot execute because node Label (rgthree) does not exist.
```

### Root Cause
These nodes ARE installed and working in ComfyUI when running workflows directly, but they're **utility nodes** meant for workflow organization, not execution:

- **SetNode/GetNode**: Variable storage and retrieval within workflows
- **Label (rgthree)**: Visual labels for workflow organization
- **Anything Everywhere**: Value distribution nodes

These nodes work in the ComfyUI UI but should not be included in the API execution format.

### Solution
Skip these utility nodes during workflow conversion:

```python
# Skip SetNode/GetNode - these are workflow utility nodes for variable storage
if node_type in ["SetNode", "GetNode"]:
    self.logger.info(f"Skipping {node_type} node {node_id} - workflow utility node")
    continue

# Skip Label nodes - these are just UI labels
if "Label" in node_type:
    self.logger.info(f"Skipping {node_type} node {node_id} - UI label node")
    continue
```

### Why This Works
1. These nodes provide UI/workflow functionality but don't process data
2. They're meant to enhance the workflow editing experience
3. The actual data flow happens through the regular processing nodes
4. ComfyUI's API execution doesn't need these utility nodes

### Important Note
This maintains the dynamic workflow system - we're just excluding non-executable utility nodes from the API format while keeping all actual processing nodes.