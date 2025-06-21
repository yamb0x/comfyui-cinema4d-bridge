# ComfyUI to Cinema4D Bridge - Development Guide

## 🚧 Project Status

This project is **in active development** with the following status:
- ✅ Tab 1 (Image Generation): **FULLY FUNCTIONAL** with dynamic UI
- 🚧 Tab 2 (3D Generation): Needs workflow monitoring implementation
- 🚧 Tab 3 (Texture Generation): Basic UI, viewer integration pending
- 🚧 Tab 4 (Cinema4D): 80% complete, NLP dictionary working
- ✅ Dynamic UI system: Working for ANY ComfyUI workflow
- ✅ Custom node conversion: Automatic compatibility handling

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
│   │   ├── app_redesigned.py  # Current main application class
│   │   ├── app_ui_methods.py  # UI method implementations
│   │   ├── workflow_manager.py # ComfyUI workflow handling
│   │   └── enhanced_file_monitor.py # File system monitoring
│   │
│   ├── ui/                # User interface components
│   │   ├── widgets.py     # Core widget definitions
│   │   ├── styles.py      # QSS styling
│   │   ├── prompt_with_magic.py # Prompt widgets with magic button
│   │   ├── object_selection_widget.py # Unified image/model selector
│   │   ├── enhanced_console.py # Console output widget
│   │   └── mcp_indicators.py # Connection status indicators
│   │
│   ├── c4d/               # Cinema4D integration
│   │   ├── nlp_parser.py  # Natural language processing
│   │   └── mcp_wrapper.py # Cinema4D MCP wrapper
│   │
│   └── mcp/               # MCP clients
│       ├── comfyui_client.py  # ComfyUI communication
│       └── cinema4d_client.py # Cinema4D communication
│
├── config/                # Configuration files
├── workflows/             # ComfyUI workflow templates
├── images/               # Generated images
├── 3D/                   # Generated 3D models
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

**As of June 19, 2025**: Console output has been significantly cleaned up. Follow these guidelines:

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
```

**Logging Rules:**
- NO emojis in log messages (removed all 🔄, ✅, 📸, etc.)
- Use `debug` for: parameter details, file monitoring, internal state
- Use `info` for: user actions, completion status, important state changes
- Keep messages concise and professional
- Enable debug mode with `setup_logging(debug=True)` when needed

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

## 🚀 Next Steps

1. **Start Simple**: Test existing functionality before adding features
2. **Use Working Examples**: Copy patterns from existing code
3. **Test Incrementally**: Verify each change works before moving on
4. **Check Logs**: Always review console output and log files
5. **Ask for Help**: Include error messages and steps to reproduce

---

**Remember**: Most issues come from virtual environment problems, event loop conflicts, or using wrong Cinema4D constants. Always check these first! 🛠️✨