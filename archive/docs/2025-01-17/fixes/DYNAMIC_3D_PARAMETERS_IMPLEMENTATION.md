# Dynamic 3D Parameters Implementation

## Overview
Successfully implemented dynamic parameter loading for the 3D Generation tab, mirroring the functionality of the Image Generation tab.

## Implementation Details

### 1. Menu Entry Added
- **Location**: File menu
- **Entry**: "Configure 3D Generation Parameters"
- **Shortcut**: Alt+3
- **Function**: `_show_configure_3d_parameters_dialog()`

### 2. Configuration Dialog
- **File**: `src/ui/configure_3d_parameters_dialog.py`
- **Purpose**: Allows users to select which 3D workflow nodes should expose parameters
- **Features**:
  - Loads 3D workflow JSON files
  - Shows node tree with checkboxes for selection
  - Filters for supported 3D node types
  - Saves configuration to `config/3d_parameters_config.json`
  - Defaults to loading `generate_3D_withUVs_09-06-2025.json`

### 3. Supported 3D Node Types
- `LoadImage`: Input image from generation
- `Hy3DGenerateMesh`: 3D mesh generation parameters
- `Hy3DVAEDecode`: VAE decoding for 3D mesh
- `Hy3DPostprocessMesh`: Mesh post-processing options
- `Hy3DDelightImage`: Image delighting parameters
- `SolidMask`: Background mask settings
- `TransparentBGSession+`: Background removal
- `ImageCompositeMasked`: Image compositing
- `Hy3DExportMesh`: Mesh export options
- `Note`: Workflow notes

### 4. Dynamic UI Generation
- **Method**: `_create_dynamic_3d_parameters()`
- **Features**:
  - Creates parameter sections based on selected nodes
  - Auto-selects common 3D nodes if no configuration exists
  - Properly sets fixed widths on all controls
  - Includes parameter property names for collection

### 5. Parameter Collection
- **Method**: `_collect_3d_parameters()` (updated)
- **Features**:
  - First attempts to collect from dynamic UI widgets
  - Falls back to static parameters if no dynamic UI
  - Collects from all control types: spin boxes, combos, checkboxes, sliders

### 6. 3D Generation Updates
- **Method**: `_on_generate_3d()` (updated)
- **Features**:
  - Loads workflow file from configuration
  - Falls back to default workflow if no config
  - Passes selected image from tab 1 to LoadImage node

### 7. UI Refresh
- **Method**: `_refresh_3d_parameters_ui()`
- **Features**:
  - Loads configuration and workflow
  - Creates dynamic parameter widget
  - Replaces existing widget at index 1
  - Switches params_stack to 3D tab

## Configuration Format
```json
{
  "selected_nodes": [
    "LoadImage_93",
    "Hy3DGenerateMesh_53",
    "Hy3DVAEDecode_54",
    "Hy3DPostprocessMesh_55",
    "Hy3DDelightImage_72",
    "SolidMask_56"
  ],
  "node_info": {
    "LoadImage_93": {
      "type": "LoadImage",
      "id": "93",
      "title": "",
      "supported": true
    },
    ...
  },
  "workflow_file": "generate_3D_withUVs_09-06-2025.json"
}
```

## Usage Workflow
1. User selects images in Image Generation tab
2. User switches to 3D Generation tab
3. If no dynamic parameters configured:
   - User goes to File > Configure 3D Generation Parameters
   - Selects nodes to expose in UI
   - Saves configuration
4. Dynamic parameters appear in right panel
5. User adjusts parameters and clicks "Generate 3D Models"
6. Selected images are automatically passed to workflow

## Key Benefits
- Consistent UI behavior between Image and 3D tabs
- Flexible parameter exposure based on workflow
- No hardcoded parameters - adapts to any 3D workflow
- Maintains fixed width constraints to prevent scrolling
- Automatic image passing between pipeline stages