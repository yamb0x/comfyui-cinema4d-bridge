# 3D Model Selection Fix for Texture Generation

## Date: 2025-06-14

## Issue
User reported: "When I select an object on the 3D generation tab, the selection is not kept for the 3d model generation, therefore the workflow fail as there is no input 3D model fed into the workflow"

## Root Cause
The texture generation button (`_on_generate_texture_clicked`) was only checking `model_grid.get_selected_models()` which only contains models from the "View All" tab. It wasn't checking:
1. `self.selected_models` - the main list that tracks all model selections across tabs
2. Scene Objects slots - models displayed in the "Scene Objects" tab

## Solution Implemented

### 1. Enhanced Model Selection Retrieval
Modified `_on_generate_texture_clicked()` to check all three sources:

```python
# Get selected models from all sources:
# 1. From self.selected_models (updated by _on_model_selected)
# 2. From model_grid (View All tab) if available  
# 3. From scene_objects_slots (Scene Objects tab)
selected_models = []

# First check self.selected_models which tracks all selections
if hasattr(self, 'selected_models') and self.selected_models:
    selected_models = list(self.selected_models)
    
# Also check model_grid for any additional selections (View All tab)
if hasattr(self, 'model_grid') and self.model_grid:
    grid_selected = self.model_grid.get_selected_models()
    for model in grid_selected:
        if model not in selected_models:
            selected_models.append(model)
            
# Check Scene Objects slots for selections
if hasattr(self, 'scene_objects_slots') and self.scene_objects_slots:
    for slot in self.scene_objects_slots:
        if isinstance(slot, dict) and 'widget' in slot:
            card = slot['widget']
            if hasattr(card, '_selected') and card._selected:
                model_path = slot.get('model_path')
                if model_path and model_path not in selected_models:
                    selected_models.append(model_path)
```

### 2. Enhanced Logging
Added detailed logging to `_on_model_selected()` to track selection state changes:

```python
if selected and model_path not in self.selected_models:
    self.selected_models.append(model_path)
    self.logger.info(f"Added to selected_models. Total selected: {len(self.selected_models)}")
elif not selected and model_path in self.selected_models:
    self.selected_models.remove(model_path)
    self.logger.info(f"Removed from selected_models. Total selected: {len(self.selected_models)}")

# Log current selection state
self.logger.debug(f"Current selected_models: {[p.name for p in self.selected_models]}")
```

## How Model Selection Works

1. **Scene Objects Tab**: Uses `Model3DPreviewCard` widgets stored in `scene_objects_slots`
2. **View All Tab**: Uses `Model3DPreviewWidget` with its own `model_grid.cards` collection
3. **Both tabs** connect to the same `_on_model_selected()` method which updates `self.selected_models`

## Testing
1. Select models in Scene Objects tab
2. Switch to Texture Generation tab
3. Click "Generate Textures" button
4. Selected models should now be properly detected and passed to the workflow

## Related Files
- `src/core/app.py`: Main application logic
- `src/ui/widgets.py`: Model3DPreviewCard and Model3DPreviewWidget classes