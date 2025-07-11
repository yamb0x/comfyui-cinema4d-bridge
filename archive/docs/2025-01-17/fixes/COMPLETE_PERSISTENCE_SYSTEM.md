# Complete Persistence System Documentation

## Overview
The ComfyUI to Cinema4D Bridge now features a comprehensive persistence system that saves and restores user settings, prompts, and parameters across application sessions. This ensures a seamless user experience where all customizations are preserved.

## Key Features Implemented

### 1. **Window State Persistence**
- Window position and size are saved when closing the app
- Restored to the exact same position when reopening
- Uses Qt's QSettings for platform-specific storage

### 2. **Prompt Persistence**
- **Positive prompts**: Your creative descriptions are saved and restored
- **Negative prompts**: Your exclusion terms are preserved
- No more hardcoded defaults after the first run
- The default "abstract 3D sea creature..." only appears on initial launch

### 3. **Dynamic Image Generation Parameters**
- All workflow-specific parameters are saved
- Supports any ComfyUI workflow configuration
- Parameters include:
  - Dimensions (width, height)
  - Sampling settings (steps, CFG, sampler, scheduler)
  - Model selections (checkpoint, LoRA models)
  - Batch size and seed values

### 4. **Dynamic 3D Generation Parameters**
- Complete persistence for all 3D workflow parameters:
  - **Mesh Generation**: guidance_scale, inference_steps, seed, scheduler
  - **VAE Processing**: simplify_ratio, mesh_resolution, max_faces
  - **Post-processing**: remove_duplicates, merge_vertices, optimize_mesh, target_faces
  - **Delighting**: delight_steps, delight_guidance, background_level
  - **UV Workflow**: render_size, texture_size, camera settings, sampling parameters

### 5. **Workflow Configuration Persistence**
- Selected workflows are remembered
- Dynamic parameter configurations are preserved
- Both image and 3D workflow selections persist

## Technical Implementation

### Storage System
Using Qt's QSettings with hierarchical key structure:
```
Organization: "Yambo Studio"
Application: "ComfyUI to Cinema4D Bridge"

Key Structure:
- window/geometry, window/x, window/y, window/width, window/height
- workflow/has_configuration, workflow/last_selected
- prompts/positive, prompts/negative
- 3d_params/{parameter_name}
- image_params/{parameter_name}
```

### Key Components

#### 1. **Save System** (`_save_window_settings()`)
Called on application close, saves:
- Window geometry
- Workflow state
- Prompts
- All parameter values

#### 2. **Load System** (`_load_window_settings()`)
Called on application start, loads:
- Window position
- Saved values into temporary storage
- Defers UI updates until widgets exist

#### 3. **Apply System** (`_apply_saved_values()`)
Called after UI creation:
- Applies prompts to text fields
- Sets all parameter values
- Handles both static and dynamic widgets

#### 4. **Dynamic Widget Tracking**
- `dynamic_3d_widgets`: Dictionary mapping parameter names to widget references
- Automatic discovery using Qt property system
- Supports all widget types: QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QSlider

### Load Order
1. Application starts
2. UI is created with default/placeholder values
3. Window settings are loaded
4. If configurations exist, dynamic UIs are created
5. Saved values are applied to all widgets
6. User sees their last session restored

## User Experience

### First Run
- Default prompts and parameters are shown
- User can customize everything
- All changes are automatically saved on close

### Subsequent Runs
- Window appears in the same position
- All prompts are restored
- Image generation parameters match last session
- 3D generation parameters (if configured) are restored
- Ready to continue where you left off

### Benefits
- No need to reconfigure parameters each session
- Consistent workflow experience
- Time-saving for production work
- Supports complex workflow configurations

## File Dependencies

### Configuration Files
- `config/image_parameters_config.json` - Image workflow configuration
- `config/3d_parameters_config.json` - 3D workflow configuration

### Implementation Files
- `src/core/app.py` - Main persistence implementation
- Methods: `_save_window_settings()`, `_load_window_settings()`, `_save_prompts()`, `_load_prompts()`, `_save_3d_parameters()`, `_load_3d_parameters()`, `_apply_saved_values()`, `_apply_saved_3d_values()`

## Testing the System

1. **Test Prompt Persistence**
   - Change positive and negative prompts
   - Close and reopen app
   - Verify prompts are restored

2. **Test Image Parameters**
   - Modify image generation settings
   - Close and reopen app
   - Check all values are preserved

3. **Test 3D Parameters**
   - Configure 3D workflow (File > Configure 3D Generation Parameters)
   - Adjust 3D generation settings
   - Close and reopen app
   - Verify 3D parameters are restored

4. **Test Window Position**
   - Move and resize window
   - Close and reopen app
   - Window should appear in same position

## Future Enhancements
- Project-based settings (save/load different configurations)
- Export/import settings profiles
- Sync settings across machines
- Preset management system

## Troubleshooting

### Settings Not Saving
- Check write permissions for settings location
- Windows: Registry or %APPDATA%
- macOS: ~/Library/Preferences/
- Linux: ~/.config/

### Parameters Not Loading
- Ensure configuration files exist in config/ directory
- Check logs for loading errors
- Verify workflow files are present

### Reset to Defaults
- Delete settings file to start fresh
- Or manually clear specific keys in QSettings

---

This persistence system ensures a professional, production-ready experience where users can focus on their creative work without repeatedly configuring the application.