# comfy2c4d - Claude's Essential Reference

## 🚀 QUICK START

### Current Status (2025-06-26)
- **All 4 Tabs** - ✅ Fully Working
- **Performance** - ✅ Optimized (10-50x faster navigation)
- **Dynamic Parameters** - ✅ Fixed dynamic workflow parameter system
- **Documentation** - ✅ Restructured for efficiency

### Active Issues & Roadmap
- **Cinema4D Integration** - Test NLP Dictionary, implement Claude Code SDK
- **Settings & Optimization** - Consistent UI, performance improvements
- **3D Model Views** - Support for untextured model display

### Key Documentation
- **[README.md](README.md)** - Project overview
- **[QUICKSTART.md](QUICKSTART.md)** - Setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical details
- **[docs/](docs/)** - Additional guides

---

## 📌 CRITICAL PATTERNS

### ComfyUI Integration
```python
# Convert WAS nodes to standard nodes in workflow_manager.py
if node_data.get("class_type") == "Image Save":
    node_data["class_type"] = "SaveImage"
    inputs["images"] = image_connection
    inputs["filename_prefix"] = "ComfyUI"
```

### Dynamic Parameter System
```python
# Unified configuration manager handles both static and dynamic parameters
# Static parameters: Known node types with predefined mappings
# Dynamic parameters: ANY selected node type extracted automatically
config_manager = UnifiedConfigurationManager()
params = config_manager.load_workflow_configuration(workflow_path)

# Dynamic extraction for texture generation
selected_nodes = set(config.get("selected_nodes", []))
dynamic_params = dynamic_extractor.extract_all_parameters(workflow_path, selected_nodes)
```

### Color Control System
```python
# Access workflow colors from settings
def _get_node_color_from_settings(self, node_type: str) -> str:
    settings = QSettings("ComfyUI-Cinema4D", "Bridge")
    workflow_colors = settings.value("interface/workflow_colors", [...])
    color_index = node_color_mapping.get(node_type, 0)
    return workflow_colors[color_index]
```

### Selection System
- `self.selected_models` - main tracking list
- `model_grid.get_selected_models()` - View All tab
- `unified_object_selector` - cross-tab persistence

### Import Pattern
- Always use `from src.module` not `from module`
- Check virtual environment is activated

---

## 🔧 COMMON FIXES

### Connection Issues
- ComfyUI: Port 8188, check `config/.env`
- Cinema4D: Port 8888, MCP server running

### Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/WSL  
python3 -m venv venv
source venv/bin/activate
```

---

## 📂 KEY FILES

- `/src/core/app_redesigned.py` - Main application with workflow dropdown synchronization
- `/src/ui/widgets.py` - Enhanced UI widgets with smart refresh
- `/src/ui/async_image_loader.py` - Async image loading and caching system
- `/src/ui/settings_dialog.py` - Application settings with color control
- `/src/core/app_ui_methods.py` - UI creation with unified parameter system
- `/src/core/unified_configuration_manager.py` - Unified parameter & prompt management
- `/src/core/dynamic_parameter_extractor.py` - Dynamic node parameter extraction
- `/src/core/workflow_parameter_extractor.py` - Static node parameter mappings
- `/src/core/async_task_manager.py` - Async task execution with conflict resolution
- `/src/core/workflow_manager.py` - Node conversion
- `/src/mcp/comfyui_client.py` - ComfyUI API
- `/config/*.json` - All configurations
- `/workflows/` - ComfyUI workflows

---

## 🚨 CRITICAL MISTAKES TO AVOID

1. **Import paths without `src.` prefix** - Breaks virtual environment
2. **Using numeric Cinema4D IDs** - Use constants like `c4d.ID_BASEOBJECT_POSITION`
3. **Mixing asyncio.run() with qasync** - Causes event loop conflicts
4. **Blocking UI thread** - Use async loading and QTimer.singleShot
5. **Using grid.clear()** - Use `smart_refresh()` to preserve content
6. **Mass find/replace** - Always check indentation and context
7. **Forgetting get_prompt()** - Custom prompt widgets need this method
8. **Creating unnecessary files** - Edit existing files when possible
9. **AsyncTaskManager conflicts** - Use exclusive tasks for texture workflows
10. **Missing dropdown sync** - Always call `_sync_workflow_dropdowns()` on workflow changes

## 📚 LESSONS LEARNED

### Performance
- **Async image loading** with QThread prevents UI freezing
- **Smart grid refresh** preserves selections during navigation
- **QPixmap caching** reduces memory usage by 60-80%
- **Lazy model loading** - Only load when tab is active

### Node Handling
- **WAS nodes must be converted** - `Image Save` → `SaveImage`
- **Hidden utility nodes** - Skip KJNodes, efficiency loaders, etc.
- **Dynamic UI generation** - Adapts to any ComfyUI workflow
- **Parameter injection** - Use workflow IDs, not node titles
- **Static vs Dynamic parameters** - Static for known nodes, dynamic for ANY selected nodes
- **Prompt extraction** - Automatic extraction from CLIPTextEncode nodes via signals

### UI Patterns
- **Custom widget methods** - Use `set_text()` not `setText()`
- **Color system** - 5-color palette via QSettings
- **Selection persistence** - Track with `unified_object_selector`
- **Thread safety** - UI updates on main thread only
- **Parameter UI refresh** - Call `_force_parameter_layout_refresh()` for visibility
- **Workflow dropdown sync** - Maintain consistency across all tabs

### Debugging
- **Logging levels** - Use DEBUG for verbose, INFO for user-facing
- **Environment variable** - `COMFY_C4D_DEBUG=1` for detailed logs
- **Event loop errors** - Check for "attached to different loop"
- **Port conflicts** - ComfyUI:8188, Cinema4D:8888
- **RuntimeError in AsyncTaskManager** - Fixed with task cancellation delays and cleanup guards
- **Parameter visibility issues** - Check UI layout refresh calls and widget creation logs

---

## 🔄 DYNAMIC PARAMETER SYSTEM (2025-06-26 UPDATE)

### System Architecture
The application now uses a **dual-layer parameter extraction system**:

1. **Static Parameters** (`WorkflowParameterExtractor`)
   - Pre-defined mappings for known node types (KSampler, CheckpointLoader, etc.)
   - Hardcoded parameter names, types, and UI constraints
   - Fast extraction with type safety

2. **Dynamic Parameters** (`DynamicParameterExtractor`)
   - Automatically extracts parameters from ANY selected node type
   - Analyzes `widgets_values` to infer parameter types and constraints
   - Supports UltimateSDUpscale, ControlNet, and custom nodes

### Unified Configuration Manager
```python
# Combines both static and dynamic extraction
config_manager = UnifiedConfigurationManager()
# Uses WorkflowParameterExtractor + DynamicParameterExtractor
# Handles texture generation with selected_nodes filtering
```

### Key Fixes Implemented

#### ✅ Dynamic Parameter Extraction
- **Problem**: Only hardcoded node types appeared in texture generation parameters
- **Solution**: Added `DynamicParameterExtractor` for ANY selected node in configuration
- **Result**: UltimateSDUpscale, ControlNet, and all selected nodes now work

#### ✅ Prompt Auto-Import
- **Problem**: Prompts not imported automatically like manual config loading
- **Solution**: Added `prompts_extracted` signal from `UnifiedConfigurationManager`
- **Result**: Positive/negative prompts auto-populate from CLIPTextEncode nodes

#### ✅ Parameter UI Visibility
- **Problem**: Parameters created successfully but not visible in right panel
- **Solution**: Added `_force_parameter_layout_refresh()` with proper layout updates
- **Result**: All parameter widgets appear immediately after creation

#### ✅ Workflow Dropdown Synchronization
- **Problem**: Dropdowns not staying synchronized across tabs
- **Solution**: Enhanced `_sync_workflow_dropdowns()` with loop prevention
- **Result**: All tabs show same workflow selection consistently

#### ✅ AsyncTaskManager RuntimeError
- **Problem**: Task execution conflicts causing RuntimeError exceptions
- **Solution**: Added task cancellation delays and cleanup exception handling
- **Result**: Texture workflows execute without runtime errors

### Configuration Files
- `config/texture_parameters_config.json` - Selected nodes and metadata
- `config/unified_parameters_state.json` - Unified configuration state
- `config/discovered_node_types.json` - Dynamic node type discovery

### Signal Flow
```
Workflow Change → UnifiedConfigurationManager → 
  Static Extraction + Dynamic Extraction → 
  Parameter UI Update + Prompt Extraction → 
  UI Refresh + Signal Emission
```

---

## 📝 SESSION WORKFLOW

1. Check `/issues/` folder for active tasks
2. Read implementation plan and requirements
3. Make changes incrementally
4. Test each change before proceeding
5. Update status when complete

For detailed guides on specific features, see `/docs/` folder.