# Technical Reference - ComfyUI to Cinema4D Bridge

## 📚 API Reference

### **Core Application API**

#### **ComfyToC4DApp**
```python
class ComfyToC4DApp(QMainWindow, LoggerMixin):
    """Main application window"""
    
    # Signals
    comfyui_connection_updated = pyqtSignal(dict)
    c4d_connection_updated = pyqtSignal(dict)
    
    # Core Methods
    def __init__(self)
    def _setup_stage_tabs(self) -> QTabWidget
    def _setup_connections(self) -> None
    def _setup_file_monitoring(self) -> None
    def _handle_new_image(self, image_path: Path) -> None
    def _handle_new_model(self, model_path: Path) -> None
    def _run_async_task(self, coro: Coroutine) -> Future
    
    # UI Methods
    def _create_param_section(self, title: str) -> QGroupBox
    def _create_status_bar(self) -> QStatusBar
    def _create_menu_bar(self) -> QMenuBar
    
    # Session Management
    session_start_time: float  # Timestamp of app start
    session_models: List[Path]  # Current session models
    session_images: List[Path]  # Current session images
```

### **MCP Client APIs**

#### **ComfyUIClient**
```python
class ComfyUIClient:
    """ComfyUI API client"""
    
    async def connect(self) -> bool
    async def get_models(self) -> List[str]
    async def get_prompt(self) -> dict
    async def queue_prompt(self, prompt: dict) -> str
    async def get_history(self, prompt_id: str = None) -> dict
    async def get_queue(self) -> dict
    async def upload_image(self, image_path: str, 
                          subfolder: str = "input") -> str
    async def interrupt(self) -> bool
    async def clear_queue(self) -> bool
```

#### **Cinema4DClient**
```python
class Cinema4DClient:
    """Cinema4D MCP client"""
    
    async def connect(self) -> bool
    async def disconnect(self) -> None
    async def execute_command(self, command: str, 
                            parameters: dict = None) -> dict
    async def test_connection(self) -> dict
    
    # MCP Methods (via execute_command)
    # - execute_python: Run Python code
    # - get_objects: List scene objects
    # - create_object: Create new object
    # - modify_object: Change properties
    # - get_selection: Get selected objects
    # - set_selection: Set selection
```

### **Natural Language APIs**

#### **NLPParser**
```python
class NLPParser(LoggerMixin):
    """Natural language parser for Cinema4D commands"""
    
    def parse(self, text: str) -> ParsedIntent
    def extract_entities(self, text: str, 
                        pattern_config: dict) -> List[ParsedEntity]
    
    # Data Classes
    @dataclass
    class ParsedIntent:
        original_text: str
        operation_type: OperationType
        confidence: float
        entities: List[ParsedEntity]
        pattern_match: str
    
    @dataclass
    class ParsedEntity:
        entity_type: str
        value: Any
        confidence: float = 1.0
```

#### **OperationGenerator**
```python
class OperationGenerator(LoggerMixin):
    """Generate executable operations from parsed intents"""
    
    def generate(self, intent: ParsedIntent) -> List[ExecutableOperation]
    
    @dataclass
    class ExecutableOperation:
        operation_type: OperationType
        method: Callable
        parameters: dict
        description: str
```

### **MCPWrapper**
```python
class MCPWrapper(LoggerMixin):
    """Wrapper for Cinema4D MCP operations"""
    
    async def execute_command(self, command: str, **kwargs) -> OperationResult
    async def add_primitive(self, object_type: str, name: str = None, 
                          size: float = 100, position: List[float] = None)
    async def create_cloner(self, mode: str = "grid", count: int = 5, 
                          target_object: str = None, **kwargs)
    async def add_effector(self, effector_type: str, strength: float = 1.0, 
                         target: str = None)
    async def add_deformer(self, deformer_type: str, strength: float = 0.5, 
                         target_object: str = None)
    async def create_material(self, material_type: str = "standard", 
                            color: List[float] = None, name: str = None)
    async def create_loft(self, spline_names: List[str] = None)
    async def apply_dynamics(self, object_name: str = None, 
                           dynamics_type: str = "rigid")
    async def apply_field(self, field_type: str = "linear", 
                        strength: float = 1.0)
```

## 🔧 Configuration Reference

### **Environment Variables**
```bash
# ComfyUI Configuration
COMFYUI_URL=http://127.0.0.1:8188
COMFYUI_CLIENT_ID=comfy-to-c4d-bridge

# Cinema4D Configuration  
C4D_MCP_HOST=127.0.0.1
C4D_MCP_PORT=54321
C4D_CONNECTION_TIMEOUT=5.0

# Application Settings
APP_LOG_LEVEL=INFO
APP_DEBUG_MODE=false
APP_THEME=dark

# File Monitoring
MONITOR_POLL_INTERVAL=1.0
MONITOR_DEBOUNCE_TIME=0.5

# Resource Limits
MAX_3D_VIEWERS=50
MAX_SESSION_VIEWERS=30
MAX_IMAGE_SIZE_MB=50
```

### **Configuration Access**
```python
# Basic access
from src.core.config import config

url = config.comfyui_url
port = config.c4d_mcp_port

# Nested access (with adapter)
timeout = config.mcp.timeout
api_key = config.api.key

# Safe access with defaults
debug = config.get('debug_mode', False)
theme = config.get('app_theme', 'dark')
```

## 📊 Cinema4D Constants Reference

### **Object Creation IDs**
```python
# Primitives (Symbolic OK)
CUBE = c4d.Ocube = 5159
SPHERE = c4d.Osphere = 5160
CYLINDER = c4d.Ocylinder = 5161
CONE = c4d.Ocone = 5162
TORUS = c4d.Otorus = 5163
PLANE = c4d.Oplane = 5164
PYRAMID = c4d.Opyramid = 5165
DISC = c4d.Odisc = 5166
TUBE = c4d.Otube = 5167
PLATONIC = c4d.Oplatonic = 5168
LANDSCAPE = c4d.Olandscape = 5169

# MoGraph Objects (Numeric Required)
CLONER = 1018544        # MoGraph Cloner
INSTANCE = 1018545      # MoGraph Instance
MATRIX = 1018546        # MoGraph Matrix
FRACTURE = 1018791      # MoGraph Fracture
TEXT = 1019268          # MoGraph Text

# Effectors (Numeric Required)
RANDOM_EFFECTOR = 1018643
PLAIN_EFFECTOR = 1021337
SHADER_EFFECTOR = 1018561
DELAY_EFFECTOR = 1018883
FORMULA_EFFECTOR = 1018882
STEP_EFFECTOR = 1018881

# Deformers (Numeric Required)
BEND_DEFORMER = 5107
TWIST_DEFORMER = 5133
TAPER_DEFORMER = 5131
BULGE_DEFORMER = 5108
SHEAR_DEFORMER = 5134
SQUASH_DEFORMER = 5135

# Materials
MATERIAL = 5703             # Standard Material
REDSHIFT_MATERIAL = 1036224 # Redshift Material

# Tags
DYNAMICS_TAG = 100004020    # Dynamics Body Tag
```

### **Parameter IDs**
```python
# Primitive Parameters
PRIM_CUBE_LEN = 1110        # Cube size vector
PRIM_SPHERE_RAD = 1111      # Sphere radius
PRIM_CYLINDER_RADIUS = 1112 # Cylinder radius
PRIM_CYLINDER_HEIGHT = 1113 # Cylinder height

# MoGraph Parameters
ID_MG_MOTIONGENERATOR_MODE = 20001  # Cloner mode
MG_OBJECT_LINK = 20000              # Target object
MG_GRID_COUNT = 20002               # Grid count vector
MG_GRID_SIZE = 20003                # Grid size vector
MG_RADIAL_COUNT = 20004             # Radial count
MG_RADIAL_RADIUS = 20005            # Radial radius
MG_LINEAR_COUNT = 20006             # Linear count
MG_LINEAR_OFFSET = 20007            # Linear offset

# Deformer Parameters
DEFORMOBJECT_STRENGTH = 10001       # Deformer strength
DEFORMOBJECT_ANGLE = 10002          # Deformer angle
DEFORMOBJECT_AXIS = 10003           # Deformer axis
DEFORMOBJECT_SIZE = 10004           # Deformer size

# Cloner Modes
ID_MG_CLONE_MODE_LINEAR = 0
ID_MG_CLONE_MODE_RADIAL = 1
ID_MG_CLONE_MODE_GRID = 2
ID_MG_CLONE_MODE_HONEYCOMB = 3
```

## 🎨 UI Component Reference

### **Custom Widgets**

#### **Simple3DViewer**
```python
class Simple3DViewer(QWidget):
    """3D model viewer with resource management"""
    
    # Class constants
    MAX_TOTAL_VIEWERS = 50
    MAX_SESSION_VIEWERS = 30
    
    # Methods
    def __init__(self, model_path: Path, parent=None)
    def load_model(self) -> bool
    def reset_view(self) -> None
    def set_world_grid(self, visible: bool) -> None
    
    # Class methods
    @classmethod
    def can_create_viewer(cls, is_session: bool = False) -> bool
    @classmethod
    def get_viewer_stats(cls) -> dict
```

#### **ImageCard**
```python
class ImageCard(QWidget):
    """Image display card with selection"""
    
    # Signals
    clicked = pyqtSignal()
    selection_changed = pyqtSignal(bool)
    
    # Properties
    image_path: Path
    selected: bool
    
    # Methods
    def set_selected(self, selected: bool) -> None
    def get_thumbnail(self, size: QSize) -> QPixmap
```

#### **C4DChatInterface**
```python
class C4DChatInterface(QWidget):
    """Natural language chat interface"""
    
    # Signals
    command_sent = pyqtSignal(str)
    
    # Methods
    def __init__(self, mcp_wrapper: MCPWrapper)
    def send_message(self, text: str) -> None
    def add_message(self, text: str, is_user: bool) -> None
    def show_thinking(self, thinking: bool) -> None
```

### **Style Classes**
```python
# Available QSS object names
"primary_btn"       # Blue primary button
"secondary_btn"     # Gray secondary button
"param_section"     # Parameter group box
"controls_section"  # Compact control section
"image_grid"        # Image grid container
"model_info_card"   # Model information card
"chat_message"      # Chat message bubble
"status_indicator"  # Connection status
```

## 📁 File Structure Reference

### **Generated Content Paths**
```python
# Image outputs
images/
├── NNNN_ComfyUI.png    # Generated images
├── NNNN_ComfyUI.jpg    # Alternative format
└── thumbnails/         # Cached thumbnails

# 3D Model outputs  
D:\Comfy3D_WinPortable\ComfyUI\output\3D\
├── model_NNNN.glb      # Generated 3D models
├── model_NNNN.obj      # Alternative formats
└── textures/           # Model textures

# Workflow templates
workflows/
├── generate_images.json      # Image generation
├── generate_3D.json         # 3D conversion
└── generate_3D_noUV.json    # No UV mapping
```

### **Log Files**
```python
logs/
├── comfy_to_c4d_YYYYMMDD_HHMMSS.log  # Session logs
├── errors.log                          # Error aggregation
└── performance.log                     # Performance metrics
```

## 🔐 Thread Safety Patterns

### **UI Updates from Threads**
```python
# Pattern 1: QTimer.singleShot
QTimer.singleShot(0, lambda: self.label.setText("Done"))

# Pattern 2: Custom signals
class Worker(QThread):
    update_ui = pyqtSignal(str)
    
    def run(self):
        # Do work
        self.update_ui.emit("Status update")

# Pattern 3: Qt.QueuedConnection
QMetaObject.invokeMethod(self.widget, "update", 
                        Qt.QueuedConnection, 
                        Q_ARG(str, "value"))
```

### **Async Operations**
```python
# Pattern 1: Thread pool executor
def _run_async_task(self, coro):
    future = self.executor.submit(self._run_in_loop, coro)
    return future

def _run_in_loop(self, coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Pattern 2: QThread with event loop
class AsyncWorker(QThread):
    def __init__(self, coro):
        self.coro = coro
        
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.coro)
        loop.close()
```

## 📈 Performance Guidelines

### **Memory Limits**
```python
# Per-component memory budgets
BASE_APPLICATION = 200  # MB
PER_3D_VIEWER = 50     # MB
PER_IMAGE_CACHE = 10   # MB
MAX_TOTAL_MEMORY = 2048 # MB

# Calculation
available = MAX_TOTAL_MEMORY - BASE_APPLICATION
max_viewers = available // PER_3D_VIEWER
```

### **Response Time Targets**
```python
# User interaction limits
UI_RESPONSE = 100       # ms - Immediate feedback
PROGRESS_UPDATE = 250   # ms - Progress indicators
OPERATION_START = 1000  # ms - Begin operation
OPERATION_COMPLETE = 10000 # ms - Finish operation
```

### **Optimization Techniques**
```python
# 1. Lazy loading
if not self.loaded:
    self._load_data()
    self.loaded = True

# 2. Resource pooling
class ViewerPool:
    def acquire(self):
        return self.available.pop() if self.available else None
    
    def release(self, viewer):
        self.available.append(viewer)

# 3. Batch operations
def process_batch(items):
    with self.batch_mode():
        for item in items:
            self.process(item)
```

## 🛠️ Debugging Tools

### **Logging Configuration**
```python
# Logger setup
import logging
from src.utils.logger import LoggerMixin

class MyClass(LoggerMixin):
    def method(self):
        self.logger.debug("Detailed info")
        self.logger.info("General info")
        self.logger.warning("Warning")
        self.logger.error("Error occurred")
        self.logger.exception("With traceback")
```

### **Debug Shortcuts**
| Key | Action | Method |
|-----|--------|--------|
| F12 | Toggle console | `_menu_toggle_console()` |
| Ctrl+D | Debug 3D viewers | `_debug_3d_viewer_state()` |
| Ctrl+T | Test monitoring | `_test_file_monitoring()` |
| Ctrl+I | Force image refresh | `_force_refresh_images()` |
| Ctrl+Shift+A | Run AI tests | `_run_comprehensive_ai_test()` |

### **Performance Profiling**
```python
# Method timing decorator
def timed_method(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

# Memory tracking
import tracemalloc
tracemalloc.start()
# ... code to profile ...
current, peak = tracemalloc.get_traced_memory()
logger.info(f"Memory: {current / 1024 / 1024:.1f}MB")
```

---

**This technical reference provides comprehensive documentation of all APIs, constants, patterns, and guidelines for developing and maintaining the ComfyUI to Cinema4D Bridge application.**