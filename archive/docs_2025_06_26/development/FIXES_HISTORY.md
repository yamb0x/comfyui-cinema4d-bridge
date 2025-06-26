# Fixes History

## 2025-01-09: File Operations Critical Fixes
**Issue**: Multiple critical file operation failures
**Fixes Applied**:

### 1. New File Operation
**Problem**: New file did not refresh sessions (images and 3D models remained in view)
**Solution**: Enhanced `_reset_ui()` method to properly clear all session data and UI elements
- Added `_clear_new_canvas_grid()` method to reset image slots in New Canvas tab
- Added `_clear_view_all_grid()` method to remove all images from View All tab  
- Added `_clear_scene_objects_grid()` method to remove all 3D models from Scene Objects
- Added `_clear_view_all_models_grid()` method to clear View All 3D models
- Reset `session_start_time` when creating new file to properly track new session

### 2. Open File Operation
**Problem**: Open file did not load the images and 3D models into the UI
**Solution**: Modified `_load_project_data()` to set session start time to past (1 second ago)
- This ensures loaded assets are treated as current session items
- Added proper asset loading with `file_generated.emit()` signals
- Assets are now properly displayed in both New Canvas and Scene Objects

### 3. Critical Exception on Load
**Problem**: Application crashed with uncaught exception when loading saved projects
**Solution**: Fixed incorrect widget cleanup in clearing methods
- Changed from checking for 'viewer' key to 'widget' key in slot data
- Added comprehensive error handling to `_reset_ui()` method
- Added try-catch blocks around all clearing operations
- Fixed indentation issue in `_load_project_data` method

### 4. Asset Tree AttributeError
**Problem**: File → New caused AttributeError: 'NoneType' object has no attribute 'setRowCount'
**Solution**: Added proper None checks for asset_tree widget in both `_reset_ui()` and `_on_file_generated()` methods

### 5. Images Not Loading to New Canvas on Project Open
**Problem**: When loading a saved project, images were not appearing in the New Canvas page
**Solution**: Added explicit refresh methods for both images and 3D models after project load
- Ensure New Canvas grid has enough slots for loaded images
- Force UI refresh with delayed loading to ensure widgets are ready

**Files Modified**: src/core/app.py

## 2025-01-09: Settings Dialog Widget Scope Crash
**Issue**: Settings dialog crashes with "Uncaught exception" when clicking ⚙️ button
**Cause**: Widgets were created on `self` (main window) instead of `dialog` object
**Solution**: Changed all `self.widget_name` to `dialog.widget_name` in:
- `_show_object_settings_dialog` method
- `_add_object_specific_controls` method
**Files Modified**: src/core/app.py
**Widgets Fixed**: 97 total (45 in main method, 52 in controls method)

## 2025-01-09: File I/O Debouncing for NL Triggers
**Issue**: NL trigger inputs saved on every keystroke, causing excessive file I/O
**Cause**: textChanged signal triggered save immediately
**Solution**: Implemented 1-second debounce timer
**Files Modified**: src/core/app.py

## 2025-01-09: Settings Dialog Display Issues
**Issue**: Values showed as "50.00 cm" instead of "50 cm"
**Solution**: Added `setDecimals(0)` to all QDoubleSpinBox widgets
**Files Modified**: src/ui/widgets.py

## 2025-01-08: Cinema4D Object Creation Constants
**Issue**: 11 primitives had incorrect object ID mappings causing wrong objects
**Cause**: Using numeric IDs instead of Cinema4D constants
**Solution**: Manually tested and corrected all primitive mappings
**Files Modified**: src/c4d/operation_generator.py
**Objects Fixed**: cylinder, plane, cone, pyramid, disc, tube, figure, platonic, oil tank, relief, capsule