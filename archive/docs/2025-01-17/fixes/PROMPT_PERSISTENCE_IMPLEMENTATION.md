# Prompt and Parameter Persistence Implementation

## Summary
This implementation adds persistence for positive/negative prompts and 3D generation parameters across application sessions.

## Implementation Details

### 1. **Prompt Persistence**
- Positive and negative prompts are saved when the application closes
- Prompts are restored when the application starts
- No more hardcoded defaults - the app remembers your last used prompts

### 2. **3D Parameter Persistence**
All 3D generation parameters are now saved and restored:
- **Mesh Generation**: guidance_scale_3d, inference_steps_3d, seed_3d, scheduler_3d
- **VAE Decode**: simplify_ratio, mesh_resolution, max_faces
- **Post-processing**: remove_duplicates, merge_vertices, optimize_mesh, target_faces
- **Delighting**: delight_steps, delight_guidance, background_level
- **UV Workflow**: render_size, texture_size, camera_distance, ortho_scale, sample_seed, sample_steps, view_size

### 3. **Technical Implementation**

#### Save Methods (src/core/app.py)
```python
def _save_prompts(self, settings: QSettings):
    """Save positive and negative prompts to settings"""
    # Saves both scene_prompt and negative_scene_prompt text

def _save_3d_parameters(self, settings: QSettings):
    """Save 3D generation parameters to settings"""
    # Saves both dynamic and static 3D parameters
```

#### Load Methods
```python
def _load_prompts(self, settings: QSettings):
    """Load saved prompts from settings"""
    # Stores prompts in _saved_positive_prompt and _saved_negative_prompt

def _load_3d_parameters(self, settings: QSettings):
    """Load saved 3D generation parameters from settings"""
    # Stores parameters in _saved_3d_params dictionary
```

#### Apply Method
```python
def _apply_saved_values(self):
    """Apply saved prompts and parameters to UI after creation"""
    # Called after UI is created to apply all saved values
```

### 4. **Storage Location**
Settings are stored using Qt's QSettings with:
- Organization: "Yambo Studio"
- Application: "ComfyUI to Cinema4D Bridge"
- Platform-specific locations:
  - Windows: Registry or %APPDATA%
  - macOS: ~/Library/Preferences/
  - Linux: ~/.config/

### 5. **User Experience**
- When you close the app, all your prompts and 3D parameters are automatically saved
- When you open the app again, everything is restored to how you left it
- The default prompt "abstract 3D sea creature..." is only used on first run
- Each parameter maintains its last used value between sessions

## Testing
1. Open the application
2. Change the positive and negative prompts to custom text
3. Modify some 3D generation parameters
4. Close the application
5. Reopen the application
6. Verify that your custom prompts and parameters are restored

## Notes
- Settings are saved automatically when the window closes
- The implementation handles missing settings gracefully with defaults
- Both static UI parameters and dynamically loaded parameters are supported