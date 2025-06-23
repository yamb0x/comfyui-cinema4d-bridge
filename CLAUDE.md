# comfy2c4d - Claude's Essential Reference

## 🚀 QUICK START

### Current Status (2025-06-23)
- **Tab 1: Image Generation** - ✅ Fully Working
- **Tab 2: 3D Model Generation** - ✅ Fully Working  
- **Tab 3: Texture Generation** - ✅ Fully Working (height issue fixed)
- **Tab 4: Cinema4D Intelligence** - ✅ NLP parser fixed, needs testing

### Latest Session Fixes (2025-06-23)
1. **3D Viewer Config** - Now affects texture generation tab viewers
2. **Removed Redundant Tab** - "Textured Models" tab removed (duplicated View All)
3. **Texture Tab Height** - Fixed constrained viewer area (removed addStretch)
4. **Import Consistency** - All imports now use `src.` prefix
5. **Black Overlay Fixed** - Transparent backgrounds for texture grids
6. **Message Box Styling** - Fixed black text backgrounds in popups
7. **3D Model Loading** - Fixed "click to load" placeholder issue
8. **ASCII Loader** - Restored black background (#000000)
9. **Cinema4D NLP** - Fixed parser initialization outside if block
10. **Server Error Handling** - Added try/catch for port binding errors
11. **Logging Optimization** - Converted 108 verbose INFO logs to DEBUG level (~95% reduction)

### Active Issues
- **Async Task Conflicts** - Multiple texture workflow checks causing RuntimeError
- **Port Binding Errors** - Windows socket permissions on some ports
- **File Lock Issues** - ComfyUI holding textured model files

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

- `/src/core/app_redesigned.py` - Main application
- `/src/core/workflow_manager.py` - Node conversion
- `/src/mcp/comfyui_client.py` - ComfyUI API
- `/config/*.json` - All configurations
- `/workflows/` - ComfyUI workflows

---

## 🚨 AVOID THESE MISTAKES

1. Mass find/replace without checking indentation
2. Using numeric Cinema4D IDs instead of constants
3. Mixing asyncio.run() with qasync event loop
4. Forgetting get_prompt() method on prompt widgets
5. Import paths without `src.` prefix

---

## 📝 SESSION WORKFLOW

1. Check `/issues/` folder for active tasks
2. Read implementation plan and requirements
3. Make changes incrementally
4. Test each change before proceeding
5. Update status when complete

For detailed guides on specific features, see `/docs/` folder.