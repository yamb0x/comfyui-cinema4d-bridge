# Developer Guide - ComfyUI to Cinema4D Bridge

## 🚀 Getting Started

### **Prerequisites**
```bash
# Required Software
- Python 3.12+
- ComfyUI (with API enabled)
- Cinema4D R2024+ (with Python API)
- Git

# System Requirements
- Windows 10/11 (primary platform)
- 8GB+ RAM recommended
- GPU with 4GB+ VRAM for 3D viewing
```

### **Quick Setup**
```bash
# 1. Clone repository
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
cd comfy-to-c4d

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your settings

# 5. Launch application
python main.py
```

## 🏗️ Architecture Overview

### **Application Layers**
```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer (Qt6)                 │
│  - UI Components (src/ui/)                                  │
│  - Event Handlers                                           │
│  - State Management                                         │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                      │
│  - Core Application (src/core/)                             │
│  - Workflow Management                                       │
│  - File Monitoring                                          │
├─────────────────────────────────────────────────────────────┤
│                    Integration Layer                         │
│  - MCP Clients (src/mcp/)                                  │
│  - Cinema4D Integration (src/c4d/)                         │
│  - Pipeline Stages (src/pipeline/)                         │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                             │
│  - File System                                              │
│  - Configuration                                            │
│  - Logs                                                     │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

### **Source Code Organization**
```
src/
├── core/                   # Application core
│   ├── app.py             # Main application class
│   ├── config.py          # Configuration management
│   ├── workflow_manager.py # ComfyUI workflow handling
│   ├── file_monitor.py    # File system monitoring
│   └── associations.py    # File associations
│
├── ui/                    # User interface
│   ├── widgets.py         # Custom Qt widgets
│   ├── styles.py          # Styling and themes
│   ├── fonts.py           # Font management
│   ├── c4d_chat_interface.py  # Cinema4D chat UI
│   └── knowledge_dictionary.py # Command reference
│
├── c4d/                   # Cinema4D integration
│   ├── nlp_parser.py      # Natural language processing
│   ├── mcp_wrapper.py     # Cinema4D MCP wrapper
│   ├── operation_generator.py # Operation generation
│   ├── mograph_engine.py  # MoGraph intelligence
│   ├── scene_patterns.py  # Pre-built patterns
│   ├── mcp_test_validator.py # Test commands
│   └── automated_test_runner.py # Test automation
│
├── mcp/                   # MCP clients
│   ├── comfyui_client.py  # ComfyUI communication
│   └── cinema4d_client.py # Cinema4D communication
│
├── pipeline/              # Processing pipeline
│   └── stages.py          # Pipeline stages
│
└── utils/                 # Utilities
    └── logger.py          # Logging configuration

### **Output Directories**
project_files/             # Saved project files (.c2c)
images/                    # Generated images from ComfyUI
3D/                        # Generated 3D models
exports/                   # Exported scenes
logs/                      # Application logs
config/                    # Configuration files
```

## 🔧 Core Components

### **1. Main Application (src/core/app.py)**
```python
class ComfyToC4DApp(QMainWindow, LoggerMixin):
    """Main application window"""
    
    def __init__(self):
        # Initialize UI
        # Setup connections
        # Start monitoring
        
    def _setup_stage_tabs(self):
        # 4-stage pipeline UI
        # 0: Image Generation
        # 1: 3D Model Generation
        # 2: Cinema4D Intelligence
        # 3: Export
```

**Key Methods**:
- `_setup_connections()`: Initialize MCP clients
- `_setup_file_monitoring()`: Start file watchers
- `_handle_new_image()`: Process generated images
- `_handle_new_model()`: Process 3D models

### **2. Configuration System (src/core/config.py)**
```python
# Nested .env support
PROJECT_ROOT/
├── .env                   # User settings
├── .env.defaults          # Default values
└── .env.local            # Local overrides

# Access pattern
config = Config()
url = config.comfyui_url  # Nested attribute access
```

### **3. MCP Communication**

#### **ComfyUI Client (src/mcp/comfyui_client.py)**
```python
class ComfyUIClient:
    async def get_models(self) -> List[str]:
        """Get available models"""
        
    async def generate_image(self, workflow: dict) -> str:
        """Execute workflow"""
        
    async def get_history(self) -> dict:
        """Get generation history"""
```

#### **Cinema4D Client (src/mcp/cinema4d_client.py)**
```python
class Cinema4DClient:
    async def execute_command(self, command: str, **params):
        """Execute MCP command"""
        
    async def create_object(self, obj_type: str):
        """Create Cinema4D object"""
```

### **4. Natural Language System (src/c4d/)**

#### **NLP Parser**
```python
class NLPParser:
    def parse(self, text: str) -> ParsedIntent:
        """Parse natural language to intent"""
        # Pattern matching
        # Entity extraction
        # Parameter mapping
```

#### **Operation Generator**
```python
class OperationGenerator:
    def generate(self, intent: ParsedIntent) -> List[C4DOperation]:
        """Convert intent to operations"""
```

## 💻 Development Workflow

### **1. Adding New Features**

#### **Step 1: Understand the Flow**
```
User Input → Parser → Generator → Executor → Result
```

#### **Step 2: Implement Components**
```python
# 1. Add to nlp_parser.py
PATTERN_LIBRARY["your_pattern"] = {
    "keywords": ["your", "keywords"],
    "operation": OperationType.YOUR_OP
}

# 2. Add to mcp_wrapper.py
async def your_operation(self, **params):
    script = """Cinema4D Python code"""
    return await self.execute_command(...)

# 3. Add to operation_generator.py
elif intent.operation_type == OperationType.YOUR_OP:
    operations.append(...)
```

### **2. Testing New Features**

#### **Manual Testing**
1. Launch application
2. Use Cinema4D Intelligence tab buttons
3. Try chat interface
4. Check logs for errors

#### **Automated Testing**
```python
# Add to mcp_test_validator.py
TEST_COMMANDS.append(
    TestCommand(
        text="your command",
        expected_operation="your_operation",
        expected_params={"param": "value"},
        should_parse=True,
        description="Test description"
    )
)

# Run comprehensive test
Ctrl+Shift+A  # Or menu: AI → Debug → Run Tests
```

### **3. Debugging Techniques**

#### **Enable Verbose Logging**
```python
# In any component
self.logger.debug(f"Detailed info: {variable}")

# Check logs/
# - comfy_to_c4d_YYYYMMDD_HHMMSS.log
# - errors.log
```

#### **Qt Threading Issues**
```python
# Wrong - causes crashes
self.ui_element.setText("Value")  # From thread

# Correct - thread safe
QTimer.singleShot(0, lambda: self.ui_element.setText("Value"))
```

#### **Async Debugging**
```python
# Add to async methods
import asyncio
self.logger.info(f"Thread: {threading.current_thread().name}")
self.logger.info(f"Event loop: {asyncio.get_event_loop()}")
```

## 🎨 UI Development

### **1. Creating New Widgets**

#### **Widget Template**
```python
class CustomWidget(QWidget):
    # Signals
    value_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        # Add components
        
    def _create_param_section(self, title: str) -> QGroupBox:
        """Reusable parameter section"""
        group = QGroupBox(title)
        group.setObjectName("param_section")
        return group
```

### **2. Styling Guidelines**

#### **Use Existing Styles**
```python
# From styles.py or styles_new.py
button.setObjectName("primary_btn")    # Blue primary
button.setObjectName("secondary_btn")  # Gray secondary
widget.setObjectName("param_section")  # Consistent sections
```

#### **Space Optimization**
```python
# Compact layouts for controls
controls_section.setMaximumHeight(140)
controls_section.setObjectName("controls_section")

# Maximize content area
splitter.setSizes([150, 850])  # 15% controls, 85% content
```

### **3. Resource Management**

#### **3D Viewer Limits**
```python
# Check before creating viewers
if Simple3DViewer.can_create_viewer(is_session=True):
    viewer = Simple3DViewer(model_path)
else:
    # Show info card instead
    info_card = self._create_model_info_card(model_path)
```

## 🔐 Best Practices

### **1. Error Handling**
```python
try:
    # Risky operation
    result = await self.async_operation()
except SpecificError as e:
    self.logger.error(f"Known error: {e}")
    # Graceful fallback
except Exception as e:
    self.logger.exception("Unexpected error")
    # User-friendly message
    QMessageBox.warning(self, "Error", "Operation failed")
```

### **2. Thread Safety**
```python
# Use signals for cross-thread communication
class Worker(QObject):
    finished = pyqtSignal(dict)
    
    def run(self):
        result = self._do_work()
        self.finished.emit(result)  # Thread-safe
```

### **3. Memory Management**
```python
# Clean up resources
def cleanup(self):
    if hasattr(self, 'viewer'):
        self.viewer.close()
        self.viewer.deleteLater()
    
    # Clear large data
    self.cached_data = None
```

### **4. Configuration**
```python
# Use type-safe config access
timeout = config.get('connection_timeout', 5.0)
url = config.get('comfyui_url', 'http://localhost:8188')

# Validate before use
if not url.startswith(('http://', 'https://')):
    raise ValueError(f"Invalid URL: {url}")
```

## 🧪 Testing Strategy

### **1. Unit Tests**
```python
# test_nlp_parser.py
def test_cube_parsing():
    parser = NLPParser()
    intent = parser.parse("create a cube")
    assert intent.operation_type == OperationType.ADD_PRIMITIVE
    assert intent.entities[0].value == "cube"
```

### **2. Integration Tests**
```python
# test_mcp_integration.py
async def test_cinema4d_connection():
    client = Cinema4DClient()
    result = await client.test_connection()
    assert result.success
```

### **3. Performance Tests**
```python
# test_performance.py
def test_viewer_limits():
    viewers = []
    for i in range(60):  # Beyond limit
        if Simple3DViewer.can_create_viewer():
            viewers.append(Simple3DViewer())
    assert len(viewers) <= 50  # Enforced limit
```

## 📚 Common Patterns

### **1. Async Task Execution**
```python
def _run_async_task(self, coro):
    """Run async task in thread pool"""
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    future = self.executor.submit(run)
    return future
```

### **2. Status Updates**
```python
# Show progress
self.status_bar.showMessage("Processing...", 0)

# Update on completion
QTimer.singleShot(0, lambda: 
    self.status_bar.showMessage("✅ Complete", 5000))
```

### **3. File Operations**
```python
# Safe file handling
def safe_delete(filepath):
    try:
        if filepath.exists():
            filepath.unlink()
            return True
    except Exception as e:
        logger.error(f"Delete failed: {e}")
    return False
```

## 🚀 Deployment

### **1. Building Executable**
```bash
# Using PyInstaller
pyinstaller --windowed --icon=icon.ico main.py
```

### **2. Configuration**
```bash
# Production .env
COMFYUI_URL=http://localhost:8188
C4D_MCP_PORT=54321
LOG_LEVEL=INFO
```

### **3. Distribution**
- Include all workflows/
- Package fonts/
- Document requirements
- Create installer

## 📈 Performance Optimization

### **1. Lazy Loading**
```python
# Load only when needed
if not self.data_loaded:
    self._load_data()
    self.data_loaded = True
```

### **2. Caching**
```python
# Cache expensive operations
@lru_cache(maxsize=100)
def expensive_calculation(param):
    return result
```

### **3. Resource Pooling**
```python
# Reuse connections
class ConnectionPool:
    def get_connection(self):
        if self.available:
            return self.available.pop()
        return self._create_new()
```

## 🔍 Troubleshooting

### **Common Issues**

1. **"Module not found"**
   - Check virtual environment active
   - Run `pip install -r requirements.txt`

2. **"Connection refused"**
   - Verify ComfyUI/Cinema4D running
   - Check port configuration

3. **"Thread safety error"**
   - Use QTimer.singleShot for UI updates
   - Check signal/slot connections

4. **"Memory error"**
   - Check 3D viewer count
   - Clear unused resources

### **Debug Commands**
- `Ctrl+D`: Debug 3D viewer status
- `Ctrl+T`: Test file monitoring
- `F12`: Show console
- `Ctrl+Shift+A`: Run test suite

---

**This developer guide provides comprehensive information for understanding, extending, and maintaining the ComfyUI to Cinema4D Bridge application. Follow these patterns and practices for consistent, high-quality development.**