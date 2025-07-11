# 3D Workflow Texture Saving Fix

**Date**: January 13, 2025  
**Issue**: When running 3D generation workflows through the application, textures were not being saved with GLB files, and workflows were failing with camera configuration errors.

## Problems Identified

### 1. Camera Configuration KeyError
The Hunyuan3D ComfyUI node was throwing `KeyError` exceptions when processing camera angles:
```
KeyError: 180
KeyError: 270
```

**Root Cause**: The node's internal code expects azimuth values from a specific set: `{-90, -45, -20, 0, 20, 45, 90}`, but the workflow was using values like 180 and 270.

### 2. Texture Not Saving with GLB
The generated 3D models were saved without textures when run through the application, despite working correctly in ComfyUI directly.

**Root Cause**: The workflow contained two `Hy3DExportMesh` nodes - one with texture saving enabled (node 87) and one disabled (node 88). The disabled one was being executed.

## Solutions Implemented

### 1. Camera Configuration Fix
Modified `src/core/workflow_manager.py` in the `_inject_params_3d_ui_format` method:

```python
# Fix camera values - the ComfyUI node requires specific angle values
# The node's dictionary only accepts: -90, -45, -20, 0, 20, 45, 90
if widgets and len(widgets) >= 2:
    # IMPORTANT: The Hunyuan3D node has a bug where it expects azimuth values
    # to be exactly from the set: {-90, -45, -20, 0, 20, 45, 90}
    # Using any other values (like 270, 180) causes KeyError
    
    # Use only the supported angle values for 6 views
    widgets[0] = "0, 20, 45, -20, -45, 0"      # Elevation angles
    widgets[1] = "0, 45, 90, -45, -90, 0"      # Azimuth - ONLY use supported values!
    
    # Ensure we have matching weights for 6 views
    if len(widgets) > 2:
        widgets[2] = "1, 1, 1, 1, 1, 1"  # Equal weight for all views
```

### 2. Texture Saving Fix
Added two fixes to ensure textures are always saved:

#### In UI format workflow injection:
```python
# Hy3DExportMesh nodes - ensure texture saving is enabled
elif node_type == "Hy3DExportMesh":
    if not widgets:
        widgets = ["3D/Hy3D", "glb", True]  # Default with texture saving enabled
        node["widgets_values"] = widgets
    elif len(widgets) >= 3:
        # Force texture saving to True (third parameter)
        widgets[2] = True
        self.logger.info(f"Enabled texture saving for Hy3DExportMesh node {node_id}")
```

#### In API format conversion:
```python
elif node_type == "Hy3DExportMesh" and widgets:
    # widgets: [output_path, file_format, save_texture]
    if len(widgets) >= 3:
        api_node["inputs"]["filename_prefix"] = widgets[0]
        api_node["inputs"]["file_format"] = widgets[1]
        # Always ensure texture saving is enabled
        api_node["inputs"]["save_texture"] = True
```

## Technical Details

### Camera Angle Processing Bug
The Hunyuan3D node contains code that processes camera angles:
```python
camera_info = [(((azim // 30) + 9) % 12) // {-90: 3, -45: 2, -20: 1, 0: 1, 20: 1, 45: 2, 90: 3}[...]
```

This code expects the azimuth values to be keys in the dictionary after some calculations. Using values outside the expected set causes a KeyError.

### Workflow Node Structure
- **Node 63**: Hy3DCameraConfig - Generates camera configuration
- **Node 82**: Hy3DSampleMultiView - Receives camera config and processes multiple views
- **Node 87**: Hy3DExportMesh - Has texture saving enabled
- **Node 88**: Hy3DExportMesh - Has texture saving disabled (was being executed)

## Result
After implementing these fixes:
1. 3D generation workflows complete without errors
2. Generated GLB files include textures
3. The workflow generates 6 camera views using valid angle combinations
4. Both issues are resolved without modifying the original workflow file

## Files Modified
- `src/core/workflow_manager.py` - Added camera angle fixes and texture saving enforcement