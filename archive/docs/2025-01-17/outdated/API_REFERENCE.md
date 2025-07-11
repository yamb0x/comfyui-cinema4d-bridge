# ComfyUI to Cinema4D Bridge - API Reference

## 🔌 Core API Classes

### **WorkflowManager**
```python
class WorkflowManager:
    def load_workflow(self, file_path: Path) -> Dict[str, Any]
    def update_workflow_parameters(self, workflow: Dict, params: Dict) -> Dict
    def execute_workflow(self, workflow: Dict) -> WorkflowResult
    def get_workflow_parameters(self, workflow: Dict) -> List[Parameter]
```

### **Cinema4DClient**
```python
class Cinema4DClient:
    async def connect(self) -> bool
    async def execute_python(self, script: str) -> CommandResult
    async def create_object(self, object_type: str, **params) -> CommandResult
    async def test_connection(self) -> bool
```

### **ComfyUIClient**
```python
class ComfyUIClient:
    async def queue_prompt(self, workflow: Dict) -> str
    async def get_queue_status() -> QueueStatus
    async def interrupt_execution() -> bool
    async def get_images(self, prompt_id: str) -> List[Image]
```

## 🎬 Cinema4D Integration

### **Universal Object Creation Pattern**
```python
# All Cinema4D objects use same pattern
obj = c4d.BaseObject(c4d.Ocube)      # Primitive
obj = c4d.BaseObject(c4d.Oextrude)   # Generator  
obj = c4d.BaseObject(c4d.Omgrandom)  # Effector
obj = c4d.BaseObject(c4d.Obend)      # Deformer
```

### **Essential Constants**
```python
# Primitives
c4d.Ocube, c4d.Osphere, c4d.Ocylinder, c4d.Oplane, c4d.Otorus

# Generators
c4d.Oextrude, c4d.Olathe, c4d.Osweep, c4d.Mocloner

# Deformers
c4d.Obend, c4d.Obulge, c4d.Oshear, c4d.Otaper

# Parameters (abbreviated names!)
c4d.PRIM_SPHERE_RAD      # NOT RADIUS
c4d.PRIM_CYLINDER_SEG    # NOT SUB
c4d.PRIM_TORUS_CSUB      # NOT VSUB
```

## ⚙️ Configuration System

### **Environment Variables**
```bash
COMFYUI_PATH="D:/Comfy3D_WinPortable"
CINEMA4D_PATH="C:/Program Files/Maxon Cinema 4D 2024"
COMFYUI_API_URL="http://127.0.0.1:8188"
CINEMA4D_MCP_PORT=8765
LOG_LEVEL=INFO
```

### **AppConfig Access**
```python
config = AppConfig()
comfyui_path = config.paths.comfyui_path
cinema4d_path = config.paths.cinema4d_path
```

## 🎯 Operation Types

### **Cinema4D Operations**
```python
class OperationType(Enum):
    # Object Creation
    CREATE_PRIMITIVE = "create_primitive"
    CREATE_GENERATOR = "create_generator"
    CREATE_DEFORMER = "create_deformer"
    CREATE_EFFECTOR = "create_effector"
    
    # Scene Operations
    SELECT_OBJECT = "select_object"
    DELETE_OBJECT = "delete_object"
    DUPLICATE_OBJECT = "duplicate_object"
    
    # Testing
    TEST_CONNECTION = "test_connection"
```

## 📊 Data Structures

### **OperationResult**
```python
@dataclass
class OperationResult:
    success: bool
    message: str = ""
    error: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
```

### **WorkflowResult**
```python
@dataclass
class WorkflowResult:
    success: bool
    prompt_id: str = ""
    images: List[str] = field(default_factory=list)
    error: str = ""
```

## 🔄 Event System

### **Qt Signals**
```python
# Main application signals
workflow_completed = pyqtSignal(WorkflowResult)
object_created = pyqtSignal(str)  # object_name
error_occurred = pyqtSignal(str)  # error_message
```

## 🛠️ MCP Protocol

### **Command Structure**
```python
{
    "jsonrpc": "2.0",
    "id": "unique_id",
    "method": "execute_python",
    "params": {
        "code": "python_script_here"
    }
}
```

### **Response Format**
```python
{
    "jsonrpc": "2.0",
    "id": "unique_id",
    "result": {
        "success": true,
        "output": "execution_result"
    }
}
```

## 🎨 UI Components

### **Custom Widgets**
```python
class ParameterWidget(QWidget):
    def set_value(self, value: Any) -> None
    def get_value(self) -> Any
    
class ImageViewer(QLabel):
    def load_image(self, path: Path) -> None
    
class Model3DViewer(QOpenGLWidget):
    def load_model(self, path: Path) -> None
```

## 📁 File Management

### **FileMonitor**
```python
class FileMonitor:
    def add_directory(self, name: str, path: Path, callback: Callable) -> None
    def remove_directory(self, name: str) -> None
    def start() -> None
    def stop() -> None
```

### **Utility Functions**
```python
def ensure_directory(path: Path) -> None
def get_latest_image(directory: Path) -> Optional[Path]
def cleanup_old_files(directory: Path, max_files: int) -> None
```

## 🔍 Logging System

### **Logger Usage**
```python
logger = setup_logger("comfy_to_c4d")
logger.info("Information message")
logger.error("Error message")
logger.debug("Debug message")
```

---

**Complete API reference for the ComfyUI to Cinema4D Bridge application.** 🎬✨