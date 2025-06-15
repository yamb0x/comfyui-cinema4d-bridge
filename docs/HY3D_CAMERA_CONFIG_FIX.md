# Hy3DCameraConfig Validation Error Fix

## Issue
ComfyUI was failing with validation errors when processing 3D generation:
```
Failed to validate prompt for output 89:
* Hy3DCameraConfig 63:
  - Failed to convert an input value to a FLOAT value: camera_distance, 0, 90, 180, 270, 0, 180, could not convert string to float: '0, 90, 180, 270, 0, 180'
  - Failed to convert an input value to a FLOAT value: ortho_scale, 0, 0, 0, 0, 90, -90, could not convert string to float: '0, 0, 0, 0, 90, -90'
```

## Root Cause
The Hy3DCameraConfig node widget values were in a different order than expected by the code:

**Actual order in workflow:**
1. camera_elevations (string): "0, 90, 180, 270, 0, 180"
2. camera_azimuths (string): "0, 0, 0, 0, 90, -90"
3. view_weights (string): "1, 0.1, 0.5, 0.1, 0.05, 0.05"
4. camera_distance (float): 1.45
5. ortho_scale (float): 1.2

**Expected order in code (incorrect):**
1. camera_distance
2. ortho_scale
3. camera_elevations
4. camera_azimuths
5. view_weights

This caused string values to be assigned to float parameters, resulting in validation errors.

## Solution
Fixed the parameter mapping in three places:

### 1. workflow_manager.py - UI to API conversion
```python
# Fixed order: [camera_elevations, camera_azimuths, view_weights, camera_distance, ortho_scale]
api_node["inputs"]["camera_elevations"] = widgets[0]
api_node["inputs"]["camera_azimuths"] = widgets[1]
api_node["inputs"]["view_weights"] = widgets[2]
api_node["inputs"]["camera_distance"] = widgets[3]
api_node["inputs"]["ortho_scale"] = widgets[4]
```

### 2. workflow_manager.py - UI format injection
```python
# Preserve existing string values, only update numeric parameters
if "camera_distance" in params:
    widgets[3] = params["camera_distance"]
if "ortho_scale" in params:
    widgets[4] = params["ortho_scale"]
```

### 3. app.py - Camera params UI creation
```python
# Camera Distance (index 3)
distance_spin.setValue(float(widgets_values[3]) if len(widgets_values) > 3 else 1.5)

# Ortho Scale (index 4)
ortho_spin.setValue(float(widgets_values[4]) if len(widgets_values) > 4 else 1.0)
```

## Result
- Camera distance and ortho scale now correctly map to float values
- String parameters (elevations, azimuths, weights) remain as strings
- ComfyUI validation passes and 3D generation works properly
- Texture generation no longer fails due to parameter errors

## Testing
1. Load the 3D workflow with UV texture generation
2. Generate a 3D model
3. Verify no validation errors in ComfyUI console
4. Check that texture generation completes successfully