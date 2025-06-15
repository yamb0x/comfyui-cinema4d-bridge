# 3D Image Injection Fix

## Issue
The selected image from tab 1 (Image Generation) was not being passed to the LoadImage node in the 3D workflow.

## Root Cause
The code was hardcoded to look for LoadImage node with ID 93, but the actual workflow uses node ID 92. Different workflows might use different node IDs.

## Fix Implementation

### 1. Made LoadImage Node Detection Dynamic
Instead of hardcoding node IDs, the code now:
- **UI Format**: Searches for any node with `type == "LoadImage"`
- **API Format**: Searches for any node with `class_type == "LoadImage"`

### 2. Enhanced ComfyUI Input Directory Detection
The code now tries multiple possible ComfyUI input directories:
- `D:/Comfy3D_WinPortable/ComfyUI/input`
- `D:/ComfyUI_windows_portable/ComfyUI/input`
- `C:/ComfyUI/input`
- `{user_home}/ComfyUI/input`

### 3. Added Comprehensive Logging
- Logs when LoadImage node is found and its ID
- Logs the image path being injected
- Logs which ComfyUI input directory is found
- Logs success/failure of image copy operation
- Warns if no LoadImage node is found
- Warns if no image path is provided

## Code Changes

### workflow_manager.py - UI Format Injection
```python
# Old: if node_id == 93 and node_type == "LoadImage" and image_path:
# New: if node_type == "LoadImage" and image_path:
```

### workflow_manager.py - API Format Injection
```python
# Old: if "93" in workflow_copy and image_path:
# New: Find LoadImage node dynamically
load_image_node_id = None
for node_id, node_data in workflow_copy.items():
    if isinstance(node_data, dict) and node_data.get("class_type") == "LoadImage":
        load_image_node_id = node_id
        break
```

## Testing
To verify the fix works:
1. Select images in the Image Generation tab
2. Switch to 3D Generation tab
3. Click "Generate 3D Models"
4. Check logs for:
   - "Found LoadImage node {id}, injecting image: {path}"
   - "Injected image path into LoadImage node {id}: {filename}"
5. Verify the 3D generation uses the selected image