# Selection System Guide

## Overview
The comfy2c4d application uses a unified object selection system that tracks objects through their entire workflow: **Image → 3D Model → Textured Model**. The system uses both a visual unified selector widget and internal tracking lists to handle workflow-connected objects and standalone selections.

## Two Selection Systems

### 1. Unified Object Selector (Workflow-Based)
- **Purpose**: Tracks objects that are part of the generation workflow
- **Location**: Left panel "Object Selection" 
- **Shows**: Connected workflow chains (Image → 3D Model → Textured Model)
- **Used for**: Objects generated in the current session with clear lineage

### 2. Internal Selection Lists (Standalone)
- **Purpose**: Tracks all selected items regardless of workflow connection
- **Variables**: `self.selected_images` and `self.selected_models`
- **Used for**: Batch operations, including models from "View All" tabs

## How Selection Works

### Image Selection (Tab 1)
1. User selects image
2. Added to `self.selected_images`
3. Added to unified selector via `add_image_selection()`
4. Shows in Object Selection panel

### 3D Model Generation (Tab 2)
1. When generated from selected images:
   - Model linked to source image via `link_model_to_image()`
   - Shows connected in Object Selection panel
   
2. When selected from "View All":
   - Added to `self.selected_models` only
   - System attempts to find source image by matching numbers
   - If found: linked via `link_model_to_image()`
   - If not found: tracked internally only

### Texture Generation (Tab 3)
- Checks BOTH selection sources:
  1. `self.selected_models` (includes View All selections)
  2. Unified selector objects (workflow-connected models)
- Removes duplicates
- Can texture ANY selected model

## Key Methods

### `_on_model_selected(model_path, selected)`
- Handles model selection/deselection
- Updates internal `selected_models` list
- Attempts to link to source image if possible
- Only removes from unified selector if object exists there

### `_on_generate_textures()`
- Gathers models from both selection systems
- Ensures all selected models are included
- Works with or without workflow connections

## Common Scenarios

### Scenario 1: Complete Workflow
1. Generate image → Shows in Object Selection
2. Generate 3D from image → Shows connected
3. Generate texture → Updates existing chain

### Scenario 2: Existing Model Selection
1. Select model from "View All" → Internal tracking only
2. Generate texture → Works normally
3. No error if model has no source image

### Scenario 3: Mixed Selection
1. Select some workflow-connected models
2. Select some standalone models from View All
3. Generate textures for all → Both types processed

## Error Prevention
- Always check if object exists before removing from unified selector
- Use `hasattr()` checks for optional UI elements
- Track selections internally even if UI updates fail
- Handle missing source images gracefully

## Common Issues and Solutions (2025-06-22)

### Issue 1: Import Path Errors
**Problem**: `ModuleNotFoundError: No module named 'ui.object_selection_widget'`
**Solution**: Use `from src.ui.` instead of `from ui.` for all imports

### Issue 2: Qt API TypeError
**Problem**: `TypeError: QListWidget.update() takes exactly one argument (0 given)`
**Solution**: Use `repaint()` instead of `update()` for PySide6 compatibility
```python
# Wrong
self.objects_list.update()

# Correct
self.objects_list.repaint()
```

### Issue 3: Uncaught Exceptions on Selection
**Problem**: Exceptions when selecting models/images, no clear error message
**Solution**: 
1. Fix import paths (see Issue 1)
2. Fix Qt API calls (see Issue 2)
3. Add safety checks for uninitialized widgets:
```python
if not hasattr(self, 'objects_list') or self.objects_list is None:
    logger.warning(f"_update_display called on uninitialized widget")
    return
```

## Architecture Details

### Widget Instance Management
- **Main instance**: `self.unified_object_selector` (created at startup)
- **Tab instances**: Created via `_get_unified_selector(tab_name)`
- **Shared data**: All instances share the same `objects` dictionary
```python
selector.objects = self.unified_object_selector.objects  # Shared reference
```

### Update Flow
1. Selection change occurs
2. Main selector updates its data
3. `_update_all_unified_selectors()` is called
4. Each selector instance refreshes its display
5. Workflow hints are updated

### Signal Connections
- Main instance connects all signals (object_selected, workflow_hint_changed, all_objects_cleared)
- Tab instances only connect necessary signals to avoid loops
- Workflow hint is emitted only from main instance