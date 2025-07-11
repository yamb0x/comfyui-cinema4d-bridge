# 3D Viewer Integration - Quick Reference

## Current Setup
- **Standalone Viewer**: `studio_viewer_final.py` - Full parameter controls for settings configuration
- **Settings File**: `studio_viewer_settings.json` - Shared between standalone and embedded
- **Run Script**: `run_final_viewer.bat` - Launch settings configurator

## Key Features to Preserve
1. **ASCII Emoji Loading**: Fun loading animation on black background
2. **Auto Floor Positioning**: Models placed at y=0 on load
3. **Drop to Floor Button**: Manual reposition to floor
4. **Settings from JSON**: Read lighting, camera, post-processing settings

## Core Components to Extract

### HTML Structure
```html
<div id="container"></div>
<div id="info" style="display: none;"></div>
<div id="loader"><!-- Loading animation --></div>
```

### Essential JavaScript Functions
```javascript
// Core functions to preserve:
- init()                    // Scene setup
- loadModel(url)           // Model loading with animation
- dropToFloor()            // Floor positioning
- startLoadingAnimation()   // ASCII emoji loader
- updateBackground()        // Background color from settings
- setupLighting()          // Studio lights from settings
- setupEnvironment()       // Grid and floor

// New functions to add:
- loadNewModel(url)        // Dynamic model loading
- disposeCurrentModel()    // Cleanup for model switching
- getScreenshot()          // Export current view
```

### Settings Application
```javascript
// Read from studio_viewer_settings.json:
- params.ambientIntensity
- params.keyIntensity
- params.cameraFov
- params.autoRotate
- params.bloomEnabled
- params.background
- params.showGrid
- params.gridSize
```

## Integration Points

### 1. Model Generation Workflow
```
ComfyUI generates GLB → Save to output/3D/ → Load in viewer → Update UI
```

### 2. UI Locations
- **Main Viewer**: 3D Generation tab (center panel)
- **Drop to Floor**: Button below viewer
- **Model List**: SCENE OBJECTS tab (right panel)
- **Thumbnails**: VIEW ALL tab (grid view)

### 3. File Serving
- Port: 8893 (different from standalone: 8892)
- Endpoint: `/model/{id}` for multiple models
- Cleanup: Remove old temp files

## Minimal Implementation Example

```python
# In main app
from ui.viewers.threejs_3d_viewer import ThreeJS3DViewer

# Add to 3D generation tab
self.viewer_3d = ThreeJS3DViewer()
layout.addWidget(self.viewer_3d)

# On model generated
def on_model_ready(self, glb_path):
    self.viewer_3d.load_model(glb_path)
    
# Drop to floor button
drop_btn = QPushButton("Drop to Floor")
drop_btn.clicked.connect(self.viewer_3d.drop_to_floor)
```

## Testing Checklist
- [ ] Model loads with textures
- [ ] Loading animation shows
- [ ] Model auto-positions on floor
- [ ] Drop to Floor works
- [ ] Settings apply from JSON
- [ ] No parameter sliders shown
- [ ] Clean error handling

## Common Issues & Solutions

1. **CORS Errors**: Use local HTTP server, not file:// URLs
2. **Settings Not Applied**: Load settings after viewer initialized
3. **Model Not Centered**: Ensure camera target updates with model
4. **Grid Not Visible**: Check background color contrast
5. **Memory Leaks**: Dispose Three.js objects properly

## File Structure
```
src/ui/viewers/
├── __init__.py
├── threejs_3d_viewer.py      # Main viewer widget
├── viewer_server.py          # HTTP server for models
└── assets/
    └── viewer_template.html  # Extracted HTML/JS
```

## Remember
- Keep `studio_viewer_final.py` as-is for settings configuration
- The embedded viewer is read-only (no parameter controls)
- Settings workflow: Configure in standalone → Apply in embedded
- Test with various GLB models for compatibility