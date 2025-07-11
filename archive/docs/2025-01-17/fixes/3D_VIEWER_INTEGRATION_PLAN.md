# Three.js 3D Viewer Integration Plan for ComfyUI to Cinema4D Bridge

## Overview
This document outlines the complete implementation plan for integrating the Three.js-based 3D viewer into the main application's 3D generation page. The viewer provides high-quality rendering with texture support, custom lighting, and various visual parameters.

## Current Viewer Features
- **GLB Model Loading**: Full texture and material support
- **ASCII Emoji Loading Animation**: Smooth black overlay with fun loading animations
- **Auto Floor Positioning**: Models automatically placed at y=0
- **Drop to Floor**: Manual repositioning button
- **Camera Controls**: Orbit controls with auto-rotation
- **Studio Lighting**: Key, fill, rim lights with shadows
- **Post-processing**: Bloom effects with tone mapping
- **Grid & Floor**: Customizable grid with adaptive colors
- **Settings Persistence**: JSON-based settings save/load

## Architecture Components

### 1. Core Files
```
studio_viewer_final.py       # Standalone viewer (reference implementation)
studio_viewer_settings.json  # Shared settings file
run_final_viewer.bat        # Settings configuration tool
```

### 2. Embedded Viewer Structure
The viewer will be embedded into the main app with these components:

```python
src/ui/viewers/
├── threejs_3d_viewer.py    # QWebEngineView wrapper for Three.js
├── viewer_settings.py      # Settings management
└── viewer_html.py          # HTML/JS content generator
```

## Implementation Steps

### Phase 1: Create Embedded Viewer Module

#### 1.1 Create `threejs_3d_viewer.py`
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal
import json
import os

class ThreeJS3DViewer(QWidget):
    """Embedded Three.js viewer for 3D model display"""
    
    model_loaded = Signal(str)  # Emits model path when loaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = "studio_viewer_settings.json"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
    def load_viewer(self, model_path=None):
        """Load the viewer with optional model"""
        html_content = self.generate_html(model_path)
        self.web_view.setHtml(html_content, QUrl("http://localhost:8892/"))
        
    def load_model(self, model_path):
        """Load a new model into existing viewer"""
        js_code = f"""
        if (window.loadNewModel) {{
            window.loadNewModel('{model_path}');
        }}
        """
        self.web_view.page().runJavaScript(js_code)
        
    def drop_to_floor(self):
        """Trigger drop to floor function"""
        js_code = """
        if (window.dropToFloor) {
            window.dropToFloor();
        }
        """
        self.web_view.page().runJavaScript(js_code)
        
    def apply_settings(self):
        """Apply settings from JSON file"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                # Apply each setting
                # ... implementation
```

#### 1.2 Extract Viewer HTML/JS
- Extract the HTML content from `studio_viewer_final.py`
- Remove parameter controls UI code
- Keep only core 3D viewing functionality
- Add `loadNewModel` function for dynamic model loading

### Phase 2: Integration with Main App

#### 2.1 Modify `src/ui/widgets.py` - Add to 3D Generation Tab
```python
# In the 3D generation section
self.viewer_3d = ThreeJS3DViewer()
self.viewer_3d.model_loaded.connect(self.on_model_loaded)
generation_layout.addWidget(self.viewer_3d)

# Add Drop to Floor button
drop_button = QPushButton("Drop to Floor")
drop_button.clicked.connect(self.viewer_3d.drop_to_floor)
```

#### 2.2 Model Loading Flow
```python
def on_3d_model_generated(self, model_path):
    """Called when ComfyUI generates a new 3D model"""
    # Copy/move model to accessible location
    served_path = self.prepare_model_for_viewing(model_path)
    
    # Load in viewer
    self.viewer_3d.load_model(served_path)
    
    # Update UI state
    self.update_3d_controls(enabled=True)
```

### Phase 3: Settings Management

#### 3.1 Shared Settings File
- `studio_viewer_settings.json` remains the single source of truth
- Standalone viewer (via .bat) updates settings
- Embedded viewer reads settings on initialization

#### 3.2 Settings Structure
```json
{
  "sliders": {
    "ambientIntensity": 0.4,
    "keyIntensity": 1.2,
    "cameraFov": 35,
    // ... other parameters
  },
  "checkboxes": {
    "shadows": true,
    "autoRotate": true,
    "bloom": true,
    "floor": true,
    "grid": true
  },
  "combos": {
    "toneMapping": "ACESFilmic",
    "background": "Dark Gray"
  }
}
```

### Phase 4: Server Integration

#### 4.1 Model Serving Options

**Option A: Embedded Server**
```python
class ModelServer:
    """Simple HTTP server for serving GLB files"""
    def __init__(self, port=8893):  # Different port to avoid conflicts
        self.port = port
        self.model_queue = {}
        
    def serve_model(self, model_path, model_id):
        """Register model for serving"""
        self.model_queue[model_id] = model_path
        return f"http://localhost:{self.port}/model/{model_id}"
```

**Option B: Direct File URLs**
- Use `file://` URLs with proper permissions
- Simpler but may have CORS issues

**Recommended: Option A** for reliability

### Phase 5: Communication Protocol

#### 5.1 App → Viewer Messages
```javascript
// Expose these functions to Python
window.loadNewModel = function(modelUrl) {
    // Clear previous model
    if (model) {
        scene.remove(model);
    }
    // Start loading animation
    startLoadingAnimation();
    // Load new model
    loadModel(modelUrl);
};

window.updateViewerSettings = function(settings) {
    // Apply settings from Python
    Object.assign(params, settings);
    applyAllSettings();
};

window.exportScreenshot = function() {
    // Return base64 image
    return renderer.domElement.toDataURL('image/png');
};
```

#### 5.2 Viewer → App Messages
```python
# Use QWebChannel for bidirectional communication
from PySide6.QtWebChannel import QWebChannel

class ViewerBridge(QObject):
    """Bridge for viewer communication"""
    
    model_loaded = Signal(str)
    model_error = Signal(str)
    loading_progress = Signal(int)
    
    @Slot(str)
    def on_model_loaded(self, path):
        self.model_loaded.emit(path)
```

### Phase 6: UI Integration Points

#### 6.1 VIEW ALL Tab
- Grid of generated models with thumbnails
- Click thumbnail → Load in main viewer
- Batch operations support

#### 6.2 SCENE OBJECTS Tab
- List of loaded models
- Select model → Highlight in viewer
- Transform controls (position, rotation, scale)

#### 6.3 Context Menus
- Right-click model → Export, Delete, Duplicate
- Right-click viewer → Screenshot, Reset View

### Phase 7: File Management

#### 7.1 Model Storage
```
output/
├── 3D/
│   ├── models/           # Generated GLB files
│   ├── thumbnails/       # Auto-generated previews
│   └── metadata/         # Model generation parameters
```

#### 7.2 Cleanup Strategy
- Auto-cleanup old models based on age/count
- Preserve models marked as "favorites"
- Link to Cinema4D project associations

### Phase 8: Performance Optimization

#### 8.1 Model Loading
- Implement progressive loading for large models
- Generate LODs for preview mode
- Cache loaded models in memory

#### 8.2 Memory Management
```javascript
// Dispose of Three.js resources properly
function disposeModel(model) {
    model.traverse((child) => {
        if (child.geometry) child.geometry.dispose();
        if (child.material) {
            if (child.material.map) child.material.map.dispose();
            child.material.dispose();
        }
    });
}
```

### Phase 9: Error Handling

#### 9.1 Loading Failures
- Graceful fallback for corrupted models
- Clear error messages with recovery options
- Automatic retry with timeout

#### 9.2 Viewer Crashes
- Detect WebEngine crashes
- Auto-restart viewer
- Preserve session state

### Phase 10: Testing Plan

#### 10.1 Unit Tests
- Model loading with various formats
- Settings persistence
- Communication bridge

#### 10.2 Integration Tests
- Full workflow: Generate → Load → View
- Multi-model scenarios
- Performance with large models

#### 10.3 User Acceptance Tests
- Smooth loading experience
- Responsive controls
- Settings consistency

## Implementation Checklist

### Immediate Tasks (Session 1)
- [ ] Create `threejs_3d_viewer.py` module
- [ ] Extract and refactor HTML/JS content
- [ ] Implement basic model loading
- [ ] Test with existing GLB files

### Core Integration (Session 2)
- [ ] Integrate with 3D generation workflow
- [ ] Connect to VIEW ALL and SCENE OBJECTS tabs
- [ ] Implement model serving solution
- [ ] Add Drop to Floor button to UI

### Polish & Features (Session 3)
- [ ] Add screenshot functionality
- [ ] Implement thumbnail generation
- [ ] Add model metadata display
- [ ] Performance optimization

### Testing & Refinement (Session 4)
- [ ] Complete test suite
- [ ] Fix identified issues
- [ ] Documentation update
- [ ] User testing

## Key Considerations

1. **Settings Workflow**: Users configure defaults via standalone viewer, app reads those settings
2. **Model Access**: Ensure proper file permissions and CORS handling
3. **Performance**: Limit concurrent loaded models, implement disposal
4. **User Experience**: Maintain smooth loading animation, clear feedback
5. **Extensibility**: Design for future features (animations, multiple models, etc.)

## Success Metrics

- Models load within 2 seconds
- Zero crashes during normal operation
- Settings persist correctly between sessions
- Smooth integration with existing workflow
- Positive user feedback on visual quality

## Next Session Starting Point

Begin with creating `threejs_3d_viewer.py` using the template above, then extract the viewer HTML/JS from `studio_viewer_final.py`, removing all parameter controls while keeping core functionality.

The standalone settings configurator (`studio_viewer_final.py` + `run_final_viewer.bat`) remains as-is for users to adjust default viewing parameters.