# comfy2c4d - Claude's Essential Reference

## 🚀 QUICK START

### Current Status (2025-06-26)
- **All 4 Tabs** - ✅ Fully Working
- **Performance** - ✅ Optimized (10-50x faster navigation)
- **Documentation** - ✅ Restructured for efficiency

### Active Issues & Roadmap
- **Texture Generation** - Debug workflow issues, support batch generation
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

- `/src/core/app_redesigned.py` - Main application with optimized navigation
- `/src/ui/widgets.py` - Enhanced UI widgets with smart refresh
- `/src/ui/async_image_loader.py` - Async image loading and caching system
- `/src/ui/settings_dialog.py` - Application settings with color control
- `/src/core/app_ui_methods.py` - UI creation with dynamic parameter sections
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

### UI Patterns
- **Custom widget methods** - Use `set_text()` not `setText()`
- **Color system** - 5-color palette via QSettings
- **Selection persistence** - Track with `unified_object_selector`
- **Thread safety** - UI updates on main thread only

### Debugging
- **Logging levels** - Use DEBUG for verbose, INFO for user-facing
- **Environment variable** - `COMFY_C4D_DEBUG=1` for detailed logs
- **Event loop errors** - Check for "attached to different loop"
- **Port conflicts** - ComfyUI:8188, Cinema4D:8888

---

## 📝 SESSION WORKFLOW

1. Check `/issues/` folder for active tasks
2. Read implementation plan and requirements
3. Make changes incrementally
4. Test each change before proceeding
5. Update status when complete

For detailed guides on specific features, see `/docs/` folder.