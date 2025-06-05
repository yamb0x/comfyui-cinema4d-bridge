# API Reference

## MCP Clients

### ComfyUIClient

```python
class ComfyUIClient(LoggerMixin):
    """Client for interacting with ComfyUI through MCP"""
    
    def __init__(self, server_url: str = "http://localhost:8188", 
                 websocket_url: str = "ws://localhost:8188/ws")
```

#### Methods

##### connect() -> bool
Establish connection to ComfyUI server.
- Returns: `True` if connection successful

##### disconnect()
Close all connections to ComfyUI.

##### queue_prompt(workflow: Dict[str, Any], number: int = 1) -> Optional[str]
Queue a workflow for execution.
- `workflow`: ComfyUI workflow dictionary
- `number`: Number of times to execute
- Returns: Prompt ID if successful

##### inject_prompt_into_workflow(workflow: Dict, positive: str, negative: str = "") -> Dict
Inject text prompts into workflow.
- `workflow`: Original workflow
- `positive`: Positive prompt text
- `negative`: Negative prompt text
- Returns: Modified workflow

##### update_workflow_parameters(workflow: Dict, params: Dict) -> Dict
Update various workflow parameters.
- `workflow`: Original workflow
- `params`: Parameters to update
- Returns: Modified workflow

##### get_models() -> Dict[str, List[str]]
Get available models from ComfyUI.
- Returns: Dictionary of model types and names

##### on(event: str, callback: Callable)
Register callback for WebSocket events.
- `event`: Event name ('progress', 'execution_complete', etc.)
- `callback`: Function to call on event

### Cinema4DClient

```python
class Cinema4DClient(LoggerMixin):
    """Client for interacting with Cinema4D through MCP"""
    
    def __init__(self, c4d_path: Path, port: int = 5000)
```

#### Methods

##### connect() -> bool
Connect to Cinema4D MCP server.
- Returns: `True` if connection successful

##### execute_python(script: str) -> Dict[str, Any]
Execute Python script in Cinema4D.
- `script`: Python code to execute
- Returns: Result dictionary with success status and output

##### import_obj(obj_path: Path, position: tuple = (0,0,0), scale: float = 1.0) -> bool
Import OBJ file into Cinema4D.
- `obj_path`: Path to OBJ file
- `position`: 3D position tuple
- `scale`: Uniform scale factor
- Returns: Success status

##### create_deformer(obj_name: str, deformer_type: C4DDeformerType, params: Dict = None) -> bool
Create and apply deformer to object.
- `obj_name`: Name of target object
- `deformer_type`: Type of deformer (enum)
- `params`: Additional parameters
- Returns: Success status

##### create_mograph_cloner(objects: List[str], mode: C4DClonerMode, count: int = 10, params: Dict = None) -> bool
Create MoGraph cloner with objects.
- `objects`: List of object names
- `mode`: Cloner mode (enum)
- `count`: Number of clones
- `params`: Additional parameters
- Returns: Success status

##### save_project(project_path: Path) -> bool
Save Cinema4D project.
- `project_path`: Path to save project
- Returns: Success status

## Pipeline Stages

### PipelineStage (Base Class)

```python
class PipelineStage(ABC, LoggerMixin):
    """Base class for pipeline stages"""
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> bool
    
    async def cancel()
    
    @property
    def is_running(self) -> bool
```

### ImageGenerationStage

```python
async def execute(self, params: Dict[str, Any], batch_size: int = 1) -> bool
```

Parameters dictionary should include:
- `positive_prompt`: Main prompt text
- `negative_prompt`: Negative prompt text
- `width`, `height`: Image dimensions
- `steps`: Sampling steps
- `cfg`: CFG scale
- `sampler_name`: Sampler algorithm
- `scheduler`: Scheduler type
- `seed`: Random seed (-1 for random)

### Model3DGenerationStage

```python
async def execute(self, image_path: Path, params: Dict[str, Any]) -> bool
```

Parameters dictionary should include:
- `mesh_density`: "low", "medium", "high", "ultra"
- `texture_resolution`: 512, 1024, 2048, 4096
- `normal_map`: Boolean
- `optimize_mesh`: Boolean

### SceneAssemblyStage

```python
async def execute(self, models: List[Path]) -> bool
async def import_model(self, model_path: Path, position: tuple = (0,0,0), scale: float = 1.0) -> bool
async def apply_procedural_setup(self, script_name: str, target_objects: List[str] = None) -> bool
```

### ExportStage

```python
async def execute(self, project_path: Path, copy_textures: bool = True, 
                  create_backup: bool = True, generate_report: bool = True) -> bool
```

## File Monitoring

### FileMonitor

```python
class FileMonitor(LoggerMixin):
    """Monitor multiple directories for file changes"""
    
    def add_directory(self, name: str, path: Path, 
                     callback: Callable[[Path, str], None],
                     patterns: Optional[List[str]] = None)
    
    def remove_directory(self, name: str)
    
    def start()
    
    def stop()
    
    def get_existing_files(self, directory: Path, 
                          extensions: List[str] = None) -> List[Path]
```

### AssetTracker

```python
class AssetTracker(LoggerMixin):
    """Track relationships between generated assets"""
    
    def add_asset(self, asset_path: Path, asset_type: str,
                 metadata: Dict[str, Any] = None)
    
    def link_assets(self, source_path: Path, target_path: Path,
                   relationship: str = "generated_from")
    
    def get_related_assets(self, asset_path: Path, 
                          relationship: str = None) -> List[Path]
    
    def get_asset_metadata(self, asset_path: Path) -> Optional[Dict[str, Any]]
```

## Configuration

### AppConfig

```python
class AppConfig(BaseSettings):
    """Main application configuration"""
    
    paths: PathConfig
    workflows: WorkflowConfig
    mcp: MCPConfig
    ui: UIConfig
    
    @classmethod
    def load(cls) -> "AppConfig"
    
    def save(self)
    
    def ensure_directories(self)
    
    def validate_external_apps(self) -> Dict[str, bool]
```

## UI Components

### Custom Widgets

#### ImageGridWidget
```python
class ImageGridWidget(QScrollArea):
    image_selected = Signal(Path, bool)
    image_clicked = Signal(Path)
    
    def add_image(self, image_path: Path)
    def get_selected_images(self) -> List[Path]
    def clear(self)
```

#### Model3DPreviewWidget
```python
class Model3DPreviewWidget(QWidget):
    model_selected = Signal(Path, bool)
    model_clicked = Signal(Path)
    
    def add_model(self, model_path: Path)
```

#### ConsoleWidget
```python
class ConsoleWidget(QTextEdit):
    def setup_logging(self)
    def set_auto_scroll(self, enabled: bool)
```

## Workflow Management

### WorkflowManager

```python
class WorkflowManager(LoggerMixin):
    """Manage ComfyUI workflow JSON files"""
    
    def load_workflow(self, workflow_name: str) -> Optional[Dict[str, Any]]
    
    def save_workflow(self, workflow_name: str, workflow: Dict[str, Any],
                     create_backup: bool = True) -> bool
    
    def inject_parameters(self, workflow: Dict[str, Any],
                         params: Dict[str, Any]) -> Dict[str, Any]
    
    def validate_workflow(self, workflow: Dict[str, Any]) -> tuple[bool, List[str]]
    
    def extract_parameters(self, workflow: Dict[str, Any]) -> Dict[str, Any]
```