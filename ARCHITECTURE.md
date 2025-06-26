# Architecture Overview

Technical blueprint of the comfy2c4d system.

## System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Qt6 Frontend                         │
├─────────────────────────────────────────────────────────┤
│  Tab 1: Image  │ Tab 2: 3D │ Tab 3: Texture │ Tab 4: C4D│
├─────────────────────────────────────────────────────────┤
│              Dynamic UI Generation Layer                 │
├─────────────────────────────────────────────────────────┤
│         Workflow Manager  │  Parameter Extractor        │
├─────────────────────────────────────────────────────────┤
│    ComfyUI MCP Client    │    Cinema4D MCP Client      │
├─────────────────────────────────────────────────────────┤
│    ComfyUI (Port 8188)   │   Cinema4D (Port 8888)      │
└─────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Dynamic UI Generation
- **Purpose**: Adapt UI to any ComfyUI workflow
- **Implementation**: `workflow_parameter_extractor.py`
- **Process**:
  ```python
  Workflow JSON → Node Analysis → Widget Creation → UI Layout
  ```
- **Key Classes**: `DynamicNodeWidget`, `WorkflowParameterExtractor`

### 2. Node Conversion System
- **Purpose**: Convert custom nodes to standard ComfyUI nodes
- **Location**: `workflow_manager.py:convert_was_nodes()`
- **Example**: `Image Save` → `SaveImage`

### 3. Event Loop Management
- **Framework**: qasync for Qt + asyncio integration
- **Critical**: Never mix `asyncio.run()` with qasync event loop
- **Pattern**: Use `QTimer.singleShot()` for non-blocking operations

## File Structure

```
/src/
├── core/                      # Core business logic
│   ├── app_redesigned.py     # Main application with tabs
│   ├── app_ui_methods.py     # UI creation methods
│   ├── workflow_manager.py   # Workflow processing
│   ├── workflow_parameter_extractor.py  # Dynamic UI
│   └── unified_configuration_manager.py # Config handling
│
├── ui/                       # UI components
│   ├── widgets.py           # Base UI widgets
│   ├── async_image_loader.py # Background image loading
│   ├── settings_dialog.py   # Application settings
│   └── viewers/             # 3D viewers
│
├── mcp/                     # MCP clients
│   ├── comfyui_client.py   # ComfyUI integration
│   └── cinema4d_client.py  # Cinema4D integration
│
└── utils/                   # Utilities
    ├── logger.py           # Logging system
    └── cache.py            # Image caching
```

## Communication Architecture

### ComfyUI Integration
- **Protocol**: HTTP REST API + WebSocket
- **Port**: 8188
- **Key Endpoints**:
  - `POST /prompt` - Submit workflow
  - `GET /ws` - Real-time updates
  - `GET /history` - Retrieve results

### Cinema4D Integration
- **Protocol**: TCP Socket (MCP)
- **Port**: 8888
- **Commands**: JSON-based natural language processing

## Workflow Execution Pipeline

1. **User Input** → Tab-specific UI widgets
2. **Parameter Collection** → `get_parameters_for_workflow()`
3. **Node Injection** → `inject_prompt_into_nodes()`
4. **Workflow Submission** → `queue_workflow()`
5. **WebSocket Monitoring** → Progress updates
6. **Result Processing** → Image/model retrieval
7. **UI Update** → Grid display with selections

## Performance Optimizations

### Async Image Loading
- **Implementation**: `AsyncImageLoader` with QThread workers
- **Benefit**: Non-blocking UI during image loading
- **Cache**: 50MB LRU cache with automatic eviction

### Smart Grid Refresh
- **Method**: `smart_refresh()` preserves content during navigation
- **Benefit**: 10-50x faster tab switching
- **State**: Maintains selections and scroll position

### Resource Management
- **Images**: QPixmap caching reduces memory 60-80%
- **Models**: Lazy loading only when tab is active
- **Cleanup**: Automatic resource disposal on tab switch

## Critical Technical Decisions

### 1. Import Pattern
Always use `from src.module` not `from module` - ensures virtual environment compatibility.

### 2. Cinema4D Constants
Use `c4d.ID_BASEOBJECT_POSITION` not numeric IDs - prevents version conflicts.

### 3. Widget Method Names
Custom widgets use `set_text()` not `setText()` - maintains consistency.

### 4. Selection Persistence
`unified_object_selector` tracks selections across all tabs.

### 5. Color System
5-color customizable palette mapped to node types via QSettings.

## Key Technical Patterns

### Thread Safety
```python
# UI updates must happen on main thread
QTimer.singleShot(0, lambda: self.update_ui())
```

### Error Handling
```python
try:
    result = await self.comfyui_client.queue_workflow()
except RuntimeError as e:
    if "attached to a different loop" in str(e):
        # Handle event loop conflicts
```

### Resource Cleanup
```python
def cleanup_tab_resources(self):
    if hasattr(self, 'model_grid'):
        self.model_grid.clear_cache()
```

## Logging Architecture

- **Levels**: DEBUG (verbose) → INFO (user-facing) → ERROR (critical)
- **Control**: `COMFY_C4D_DEBUG` environment variable
- **Output**: Console + `logs/app.log`
- **Performance**: ~95% reduction by converting INFO to DEBUG

## Security Considerations

- No credential storage in configs
- Local-only MCP communication
- Sanitized file paths in workflows
- No external network requests

## Future Extensibility

The architecture supports:
- Additional AI model integrations
- New workflow types via dynamic UI
- Extended MCP commands
- Plugin system for custom nodes
- Multi-user collaboration features