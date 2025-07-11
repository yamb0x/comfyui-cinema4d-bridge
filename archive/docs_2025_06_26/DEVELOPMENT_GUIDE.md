# comfy2c4d - Development Guide

## 🚧 Project Status

This project is **in active development** with the following status:
- ✅ Tab 1 (Image Generation): **FULLY FUNCTIONAL** with dynamic UI
- ✅ Tab 2 (3D Generation): **FULLY FUNCTIONAL** with workflow monitoring and 3D viewer
- 🚧 Tab 3 (Texture Generation): Basic UI, viewer integration pending
- 🚧 Tab 4 (Cinema4D): 80% complete, NLP dictionary working
- ✅ Dynamic UI system: Working for ANY ComfyUI workflow
- ✅ Custom node conversion: Automatic compatibility handling
- ✅ **NEW**: Unified theme management with accent color inheritance
- ✅ **NEW**: Complete project save/load with dynamic parameter persistence
- ✅ **NEW**: Undo/redo functionality for all user actions
- ✅ **NEW**: Enhanced logging configuration with all levels working
- ✅ **NEW**: Issues workflow system for structured development

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (Windows)
- ComfyUI with API enabled
- Cinema4D R2024+ with Python API
- Git

### Setup Development Environment

```bash
# 1. Clone repository
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
cd comfy-to-c4d

# 2. Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your paths

# 5. Launch application
python main.py
```

**⚠️ CRITICAL**: Always activate virtual environment before running to prevent module import errors!

## 📁 Project Structure

```
comfy-to-c4d/
├── src/
│   ├── core/               # Application core
│   │   ├── app.py         # Main application (DEPRECATED - use app_redesigned.py)
│   │   ├── app_redesigned.py  # Current main application class with enhanced features
│   │   ├── app_ui_methods.py  # UI method implementations
│   │   ├── workflow_manager.py # ComfyUI workflow handling with node conversion
│   │   ├── project_manager.py # Complete project save/load with dynamic parameters
│   │   ├── enhanced_file_monitor.py # File system monitoring
│   │   └── debug_wrapper.py # Scene assembly debugging utilities
│   │
│   ├── ui/                # User interface components
│   │   ├── widgets.py     # Core widget definitions
│   │   ├── styles.py      # QSS styling
│   │   ├── prompt_with_magic.py # Prompt widgets with magic button
│   │   ├── object_selection_widget.py # Unified image/model selector
│   │   ├── enhanced_console.py # Console output widget
│   │   ├── mcp_indicators.py # Connection status indicators
│   │   ├── settings_dialog.py # Application settings with enhanced logging config
│   │   ├── terminal_theme_complete.py # Complete terminal styling
│   │   ├── studio_3d_config_dialog.py # 3D viewer configuration
│   │   └── nlp_dictionary_dialog.py # NLP command dictionary editor
│   │
│   ├── utils/             # Utility modules
│   │   ├── theme_manager.py # Unified theme and accent color management
│   │   ├── advanced_logging.py # Enhanced logging with all levels
│   │   ├── advanced_state_management.py # Complete undo/redo system
│   │   └── logger.py      # Basic logging utilities
│   │
│   ├── c4d/               # Cinema4D integration
│   │   ├── nlp_parser.py  # Natural language processing
│   │   └── mcp_wrapper.py # Cinema4D MCP wrapper
│   │
│   └── mcp/               # MCP clients
│       ├── comfyui_client.py  # ComfyUI communication
│       └── cinema4d_client.py # Cinema4D communication
│
├── issues/                # Issue tracking for development
├── docs/                  # Documentation
│   ├── plan_*.md         # Issue requirements
│   └── [other guides]    # Development guides
├── config/                # Configuration files
├── workflows/             # ComfyUI workflow templates
├── images/               # Generated images
├── 3d_models/            # Generated 3D models
└── logs/                 # Application logs
```

## 🎯 Core Patterns

### Workflow Node Conversion

The application automatically converts custom nodes to standard ComfyUI nodes for compatibility:

```python
# In workflow_manager.py - _ensure_save_image_node()
if node_data.get("class_type") == "Image Save":
    # Convert WAS "Image Save" to standard "SaveImage" 
    node_data["class_type"] = "SaveImage"
    
    # Convert to standard SaveImage inputs
    image_connection = inputs.get("images", ["11", 0])
    inputs.clear()  # Clear all WAS-specific inputs
    inputs["images"] = image_connection
    inputs["filename_prefix"] = "ComfyUI"
```

**Why We Do This:**
- Many workflows use custom nodes like WAS Node Suite
- Users may not have these custom nodes installed
- Standard nodes are guaranteed to exist in ComfyUI
- Preserves workflow functionality without dependencies

**Supported Conversions:**
- WAS "Image Save" → Standard "SaveImage"
- More conversions can be added as needed

### Dynamic UI Widget System

The application creates UI widgets dynamically based on ANY workflow:

```python
# In app_ui_methods.py - _load_parameters_from_config()
def _create_widget_from_definition(self, widget_def, value, node_type, node_id, param_key):
    """Creates appropriate widget based on node parameter definition"""
    widget_type = widget_def.get('widget', 'text')
    
    if widget_type == 'combo':
        # Dynamic dropdown with model scanning
        options = self._get_model_options_for_parameter(node_type, widget_def['name'])
        return self._create_combo_widget(widget_def['name'], options, value)
    elif widget_type == 'float':
        return self._create_float_widget(...)
    # ... more widget types
```

**Key Features:**
- Detects node types from workflow JSON
- Creates appropriate widgets (combo, float, int, text, etc.)
- Stores widget references for dynamic updates
- Supports bypass functionality per node
- Handles multiple instances of same node type

### AsyncIO & Event Loop Management

**⚠️ CRITICAL**: Don't use `asyncio.run()` with qasync - it creates conflicting event loops!

```python
# ❌ WRONG - Creates multiple event loops
async def main():
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    # ...

asyncio.run(main())  # DON'T DO THIS!

# ✅ CORRECT - Single event loop managed by qasync
def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Schedule async initialization
    asyncio.ensure_future(init_app())
    
    with loop:
        loop.run_forever()

main()  # Direct call, no asyncio.run()
```

### MCP Communication Pattern

```python
# ComfyUI Client - HTTP/WebSocket based
class ComfyUIClient:
    async def _ensure_http_client(self):
        """Ensure HTTP client exists in current event loop"""
        current_loop = asyncio.get_running_loop()
        if self._last_loop != current_loop:
            if self.http_client:
                await self.http_client.aclose()
            self.http_client = httpx.AsyncClient(timeout=60.0)
            self._last_loop = current_loop

# Cinema4D Client - Simple TCP socket protocol
# ⚠️ CRITICAL: Uses SIMPLE protocol, not LENGTH-PREFIXED!
class Cinema4DClient:
    async def execute_python(self, script: str):
        # Send: {"script": "python_code"} (UTF-8, no framing)
        # Receive: {"success": bool, "output": "...", "error": "..."} 
        message = json.dumps({"script": script})
        client_socket.send(message.encode('utf-8'))  # No length prefix!
        response = client_socket.recv(4096)  # No length prefix!
```

### UI Widget Pattern

```python
class CustomWidget(QWidget):
    # Define signals
    value_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Use dark theme styling
        self.setObjectName("custom_widget")
        
    # Thread-safe UI updates
    def update_from_thread(self, value):
        QTimer.singleShot(0, lambda: self.setText(value))
```

### Cinema4D Object Creation

**⚠️ ALWAYS use Cinema4D constants, not numeric IDs!**

```python
# ✅ CORRECT - Use constants with error handling
try:
    obj = c4d.BaseObject(c4d.Ocube)  # Use constant
    if not obj:
        print("ERROR: Failed to create cube")
        return False
except AttributeError as e:
    print(f"ERROR: Unknown constant c4d.Ocube: {e}")
    return False

# ❌ WRONG - Numeric IDs can crash Cinema4D
obj = c4d.BaseObject(5159)  # DON'T DO THIS!
```

## 🚨 Common Issues & Solutions

### 1. "AttributeError: 'PositivePromptWidget' object has no attribute 'get_prompt'"
**Cause**: Missing method alias in prompt widgets  
**Solution**: Add `get_prompt()` method to `PromptWithMagicButton` base class:
```python
def get_prompt(self) -> str:
    """Alias for getText() for compatibility"""
    return self.getText()
```

### 2. Event Loop Binding Errors
**Cause**: HTTP client created in different event loop  
**Solution**: Use lazy initialization and track event loops:
```python
async def _ensure_http_client(self):
    current_loop = asyncio.get_running_loop()
    if self._last_loop != current_loop:
        # Recreate client in new loop
```

### 3. Cinema4D MCP Disconnection
**Cause**: Invalid object IDs or protocol mismatch  
**Solution**: 
- Use Cinema4D constants (`c4d.Ocube`) not numeric IDs
- Never modify socket protocol in `cinema4d_client.py`
- Test with "Create Test Cube" after any MCP changes

### 4. Module Import Errors
**Cause**: Virtual environment not activated  
**Solution**: Always run `venv\Scripts\activate` before launching

### 5. UI Not Updating from Background Thread
**Cause**: Direct UI manipulation from non-main thread  
**Solution**: Use signals or QTimer.singleShot:
```python
# From background thread
QTimer.singleShot(0, lambda: self.label.setText("Updated"))
```

## 🧪 Testing Approach

### Manual Testing Checklist
1. **Connection Test**: Both MCP indicators should be green
2. **Image Generation**: Generate test image, verify it appears in UI
3. **3D Generation**: Convert image to 3D, check viewer loads
4. **Cinema4D Test**: Use "Create Test Cube" button
5. **Selection System**: Test checkboxes persist across tabs
6. **File Deletion**: Right-click → Delete, verify confirmation

### Adding New Cinema4D Commands

1. **Add Pattern** (`src/c4d/nlp_parser.py`):
```python
PATTERN_LIBRARY["your_pattern"] = {
    "keywords": ["your", "keywords"],
    "operation": OperationType.YOUR_OP
}
```

2. **Add MCP Method** (`src/c4d/mcp_wrapper.py`):
```python
async def your_operation(self, **params):
    script = """
    import c4d
    # Your Cinema4D Python code
    """
    return await self.execute_command(
        command="execute_python",
        parameters={"code": script}
    )
```

3. **Test in Cinema4D Console First**:
```python
# Always test your script in Cinema4D before implementing
import c4d
obj = c4d.BaseObject(c4d.Ocube)
doc.InsertObject(obj)
c4d.EventAdd()
```

## 💻 Code Standards

### Dark Theme Colors
- Background: #1e1e1e
- Text: #e0e0e0  
- Borders: #3a3a3a
- Accent: #4CAF50 (green)
- Primary Button: #0d7377
- Secondary Button: #3a3a3a

### Logging Best Practices

**As of 2025-06-21**: Enhanced logging system with full configuration support:

```python
from src.utils.logger import LoggerMixin

class MyClass(LoggerMixin):
    def method(self):
        # Use debug for implementation details
        self.logger.debug("Widget created with params: {...}")
        
        # Use info ONLY for important user-facing events
        self.logger.info("Workflow queued successfully")
        
        # Always show warnings and errors
        self.logger.warning("Connection timeout, retrying...")
        self.logger.error("Failed to load workflow")
        self.logger.critical("System failure - cannot continue")
```

**Enhanced Logging Features:**
- **Full Level Support**: Debug, Info, Warning, Error, Critical all configurable
- **Settings Integration**: Change log levels from UI Settings → Logging tab
- **Runtime Configuration**: Logging levels update immediately without restart
- **Professional Output**: NO emojis, clean console formatting
- **Correlation IDs**: For tracking related operations across components

**Logging Rules:**
- Use `debug` for: parameter details, file monitoring, internal state
- Use `info` for: user actions, completion status, important state changes
- Use `warning` for: recoverable issues, fallback scenarios
- Use `error` for: operation failures, invalid states
- Use `critical` for: system failures that prevent operation
- Keep messages concise and professional

### Error Handling Pattern
```python
try:
    result = await self.risky_operation()
except SpecificError as e:
    self.logger.error(f"Expected error: {e}")
    # Graceful fallback
except Exception as e:
    self.logger.exception("Unexpected error")
    # Show user-friendly message
    QMessageBox.warning(self, "Error", "Operation failed")
```

### Resource Management
```python
def cleanup(self):
    """Clean up resources on shutdown"""
    if hasattr(self, 'viewer'):
        self.viewer.close()
        self.viewer.deleteLater()
    
    # Clear large data
    self.cached_data = None
    
    # Close async clients
    if self.http_client:
        asyncio.create_task(self.http_client.aclose())
```

## 🛠️ Debug Tools

### Keyboard Shortcuts
- **F12**: Toggle debug console
- **Ctrl+D**: Debug 3D viewer state
- **Ctrl+T**: Test file monitoring
- **Ctrl+Shift+A**: Run comprehensive AI test

### Performance Monitoring
```python
# Time operations
import time
start = time.time()
# ... operation ...
elapsed = time.time() - start
self.logger.info(f"Operation took {elapsed:.3f}s")

# Check 3D viewer count
from src.ui.viewers.simple_3d_viewer import Simple3DViewer
stats = Simple3DViewer.get_viewer_stats()
self.logger.info(f"Active viewers: {stats['total_count']}/{stats['max_total']}")
```

## 📋 Development Checklist

Before committing changes:
- [ ] Virtual environment activated
- [ ] All imports resolve without errors
- [ ] UI updates use thread-safe methods
- [ ] Cinema4D scripts tested in console first
- [ ] Error handling for all async operations
- [ ] Logging added for debugging
- [ ] Resource cleanup implemented
- [ ] Dark theme colors used consistently

## 🚀 New Features (2025-06-21)

### Theme Management System
- **Unified Theming**: Complete theme consistency across all UI components
- **Accent Color Inheritance**: All elements properly inherit accent color from settings
- **Real-time Updates**: Theme changes apply immediately without restart
- **Enhanced CSS**: Proper CSS variables and override support

### Project Persistence System
- **Complete Save/Load**: All dynamic parameters, content, and UI state preserved
- **Asset Management**: Images, models, and textures tracked and saved with projects
- **Version Control**: Project format versioning for future compatibility
- **Recent Projects**: Quick access to recently opened projects

### Advanced Undo/Redo System
- **Full State Tracking**: All user actions (parameters, prompts, selections) are undoable
- **State Machines**: Proper state management for complex UI interactions
- **Memory Efficient**: Smart state compression to prevent memory bloat
- **UI Integration**: Undo/Redo accessible via keyboard shortcuts and menus

### Enhanced Logging Configuration
- **All Levels Supported**: Debug, Info, Warning, Error, Critical all configurable
- **Settings UI Integration**: Change log levels from Settings → Logging tab
- **Runtime Updates**: Logging configuration changes apply immediately
- **Professional Output**: Clean, emoji-free console output

### Issues Workflow System
- **Structured Development**: `/issues/<no>.md` for issue tracking
- **Requirements Planning**: `/docs/plan_<no>.md` for detailed requirements
- **Session Integration**: Tackle issues systematically in development sessions
- **Progress Tracking**: Clear documentation of what's implemented vs pending

## 🚀 Next Steps

1. **Start Simple**: Test existing functionality before adding features
2. **Use Working Examples**: Copy patterns from existing code
3. **Test Incrementally**: Verify each change works before moving on
4. **Check Logs**: Always review console output and log files
5. **Use Issues System**: Document new features/bugs in `/issues/` directory
6. **Ask for Help**: Include error messages and steps to reproduce

---

**Remember**: Most issues come from virtual environment problems, event loop conflicts, or using wrong Cinema4D constants. Always check these first! The new theme management, project persistence, undo/redo, and logging systems provide a solid foundation for enterprise-grade development.

## 📋 Current Issue Tracker

The project now uses a structured issues workflow system with 7 planned issues:

1. **[Issue #1: UI Layout & Responsiveness Fixes](../issues/1.md)** - Critical UI improvements
2. **[Issue #2: Complete Texture Generation Tab](../issues/2.md)** - Feature completion  
3. **[Issue #3: Cinema4D Commands & NLP Scene Generation](../issues/3.md)** - Advanced features
4. **[Issue #4: Performance Optimization & Code Quality](../issues/4.md)** - Production readiness
5. **[Issue #5: Enhanced User Experience & Polish](../issues/5.md)** - UX improvements
6. **[Issue #6: Testing Framework & Documentation](../issues/6.md)** - Quality assurance
7. **[Issue #7: Professional Splash Screen & Application Loader](../issues/7.md)** - Professional branding

Each issue includes detailed requirements in `/docs/plan_<no>.md` for systematic development.