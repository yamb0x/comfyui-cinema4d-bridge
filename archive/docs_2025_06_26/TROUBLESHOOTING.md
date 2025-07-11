# ComfyUI to Cinema4D Bridge - Troubleshooting Guide

## 🚨 Recent Fixes & Known Issues

### **2025-06-19: Major Recovery & Cleanup**
**Status:** ✅ FIXED - Application fully functional
**Issues Fixed:**
1. **Indentation Errors** - Fixed 200+ syntax errors in app_redesigned.py
2. **Generate Button** - Fixed misplaced return statements blocking all button actions
3. **Console Verbosity** - Reduced logging output by ~95%

**Root Causes:**
- Dynamic widget system implementation corrupted file indentation
- Faulty sed commands caused mass indentation problems
- Return statements were outside if blocks, blocking execution

### **2025-06-18: Dynamic Widget System Status**
**Current State:** ✅ FIXED - Dynamic widget system working
**Files Modified:**
- ✅ `src/core/dynamic_widget_updater.py` - NEW: Complete dynamic widget system
- ✅ `src/core/app_ui_methods.py` - Enhanced widget creation with reference storage
- ✅ `src/core/app_redesigned.py` - All indentation errors fixed

### **2025-06-17: Critical Startup Error Fixed**
**Symptom:** Application spam errors on startup
```
AttributeError: 'PositivePromptWidget' object has no attribute 'get_prompt'
```
**Solution:** Fixed in `src/ui/prompt_with_magic.py` - added missing `get_prompt()` method

### **UI Selection System Restored**
**Symptom:** Image/model selection checkboxes not working
**Solution:** Complete selection system restoration in `src/core/app_redesigned.py`
- Checkbox selection with visual feedback
- Cross-tab persistence 
- Object manager with real-time updates
- Context menus for file management

---

## 📋 Quick Diagnostics

### Check Application Status
```bash
# Virtual environment active?
python --version  # Should show Python 3.11+

# Dependencies installed?
pip list | grep PySide6  # Should show PySide6

# ComfyUI running?
curl http://127.0.0.1:8188/  # Should get response

# Cinema4D MCP running?
curl http://127.0.0.1:8765/  # Should get response
```

---

## 🚀 Startup Issues

### "ModuleNotFoundError: No module named 'PySide6'"
**Symptom:** Application fails to start with missing module errors
```
ModuleNotFoundError: No module named 'PySide6'
```
**Solutions:**
1. **Activate virtual environment first:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Windows quick fix:** Run `install_dependencies.bat`

### "did not find executable at '/usr/bin\python.exe'"
**Symptom:** Virtual environment errors on Windows
```
Error: did not find executable at '/usr/bin\python.exe'
```
**Solution:** Virtual environment created on WSL/Linux
1. Delete `venv/` folder
2. Run `install_dependencies.bat` to create Windows venv
3. Or manually: `python -m venv venv`

### Application Takes Forever to Start
**Symptom:** 30+ seconds startup time
**Solutions:**
1. Check antivirus isn't scanning Python files
2. Move project out of cloud sync folders (Dropbox/OneDrive)
3. Close resource-heavy applications
4. Check disk space (need 2GB+ free)

---

## 🔌 Connection Issues

### ComfyUI Connection Failed
**Symptom:** Red indicator, can't generate images
```
Error: Could not connect to ComfyUI at http://127.0.0.1:8188
```
**Solutions:**
1. **Start ComfyUI first:**
   ```bash
   cd /path/to/ComfyUI
   python main.py --listen 0.0.0.0 --port 8188
   ```
2. **Check in browser:** Visit http://127.0.0.1:8188
3. **Firewall:** Allow port 8188
4. **Different port?** Update `.env` file:
   ```
   COMFYUI_URL=http://127.0.0.1:YOUR_PORT
   ```

### Cinema4D MCP Server Not Starting
**Symptom:** Red Cinema4D indicator
```
Error: Cinema4D MCP server failed to start
```
**Solutions:**
1. **Run MCP server:** Execute `Start ComfyUI MCP Server.bat`
2. **Check Cinema4D path in `.env`:**
   ```
   CINEMA4D_PATH=C:/Program Files/Maxon Cinema 4D 2024/
   ```
3. **Port conflict?** Change in `.env`:
   ```
   CINEMA4D_MCP_PORT=8766  # Different port
   ```
4. **Permissions:** Run as administrator

---

## 🖼️ UI/Selection Issues

### Checkboxes Not Working
**Symptom:** Can't select images or models
**Solutions:**
1. **Update to latest version** - Fixed in 2025-06-17
2. **Clear cache:** Delete `src/__pycache__/` folders
3. **Restart application**

### Object Manager Empty
**Symptom:** Left panel not showing selected items
**Solutions:**
1. Select items using checkboxes first
2. Switch tabs to refresh
3. Check file monitoring is running (status bar)

### Dark Theme Not Applied
**Symptom:** Mixed light/dark UI elements
**Solutions:**
1. Restart application (theme applies on startup)
2. Check `src/ui/styles.py` exists
3. Clear Python cache:
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} +
   ```

### Settings Not Saving
**Symptom:** Settings dialog changes don't persist
**Solution:** Fixed in latest version - all settings now functional

---

## 🔧 Virtual Environment Issues

### Wrong Python Version
**Symptom:** Syntax errors or module issues
```
SyntaxError: invalid syntax
```
**Solution:** Need Python 3.11+
```bash
python --version  # Check version
# If wrong, specify full path:
C:\Python311\python.exe -m venv venv
```

### Cloud Sync Corruption
**Symptom:** Random module errors after sync
**Prevention:**
1. **Move project to local drive:**
   ```
   C:\dev\comfy-to-c4d\
   ```
2. **Exclude from sync:** Add `venv/` to sync exclusions
3. **Add to .gitignore:**
   ```
   venv/
   __pycache__/
   *.pyc
   ```

---

## ⚡ AsyncIO/Event Loop Issues

### "RuntimeError: There is no current event loop"
**Symptom:** Async errors when using features
```
RuntimeError: There is no current event loop in thread
```
**Solutions:**
1. **Don't mix event loops** - Let qasync handle it
2. **Restart application** - Clears stale loops
3. **Check for `asyncio.run()` calls** - Should not exist with qasync

### "This event loop is already running"
**Symptom:** Can't execute async operations
**Solution:** Application uses qasync - don't create new loops
```python
# Wrong:
asyncio.run(some_function())

# Right - let the app handle it:
QTimer.singleShot(0, lambda: some_function())
```

---

## 🎬 Cinema4D Issues

### Object Creation Fails
**Symptom:** "Create Cube" does nothing or creates wrong object
```
Error: Failed to create cube in Cinema4D
```
**Solutions:**
1. **Cinema4D must be open** with active document
2. **Use constants not IDs:**
   ```python
   # Wrong:
   obj = c4d.BaseObject(5159)  # Numeric ID
   
   # Right:
   obj = c4d.BaseObject(c4d.Ocube)  # Constant
   ```
3. **Check MCP server running** (green indicator)

### Parameter Changes Don't Apply
**Symptom:** Sliders move but object doesn't update
**Solutions:**
1. **Check parameter names** - Use abbreviated forms:
   ```
   PRIM_SPHERE_RAD not PRIM_SPHERE_RADIUS
   ```
2. **Verify in Cinema4D console:**
   ```python
   import c4d
   print(c4d.PRIM_SPHERE_RAD)  # Should print number
   ```

---

## 🎨 Workflow Issues

### "Invalid JSON format"
**Symptom:** Can't load workflow files
```
Error: Failed to load workflow: Invalid JSON format
```
**Solutions:**
1. **Validate JSON:** Use online JSON validator
2. **Re-export from ComfyUI:** Save workflow again
3. **Check encoding:** Save as UTF-8 without BOM

### Missing Models/LoRAs
**Symptom:** Workflow fails with model not found
```
Error: Model 'flux-dev' not found in ComfyUI
```
**Solutions:**
1. **Install in ComfyUI:** Download required models
2. **Check paths:** Verify `ComfyUI/models/` structure
3. **Update workflow:** Use available models

---

## 📁 File System Issues

### Generated Files Not Appearing
**Symptom:** Images/models generated but not shown in UI
**Solutions:**
1. **Check output paths in `.env`:**
   ```
   COMFYUI_OUTPUT_PATH=D:/ComfyUI/output
   BRIDGE_OUTPUT_PATH=D:/comfy-to-c4d/bridge_outputs
   ```
2. **Verify file extensions:** `.png`, `.jpg`, `.glb` only
3. **Check file monitoring** (status bar indicator)
4. **Refresh manually:** Switch tabs to trigger refresh

### Permission Denied Errors
**Symptom:** Can't save files or settings
```
Error: Permission denied writing to C:/Program Files/
```
**Solutions:**
1. **Don't install in Program Files**
2. **Run as administrator** if necessary
3. **Check antivirus** - whitelist the app
4. **Use user directories** for outputs

---

## 🐛 Debug Mode & Logging Control

### Console Verbosity (Since June 19, 2025)
**Default:** Clean, minimal output showing only essential information
**What you'll see:**
```
Starting ComfyUI to Cinema4D Bridge...
11:19:11 | INFO     | Starting ComfyUI to Cinema4D Bridge Application
11:19:12 | INFO     | Loaded 9 parameter groups from workflow
11:19:13 | INFO     | Application fully initialized and ready
```

### Enable Detailed Logging
**For debugging issues:**
1. **In main.py:** Change `setup_logging(debug=True)`
2. **Or via environment:** Set `DEBUG=1`
3. **Or add to `.env` file:**
   ```
   LOG_LEVEL=DEBUG
   ```

### What Was Cleaned Up
- Parameter loading details (was ~50+ lines per workflow)
- Widget creation logs
- File monitoring updates
- Queue status checks
- ASCII animation lifecycle
- All emoji decorations (🔄, ✅, 📸, etc.)

### Review Log Files
- `logs/application.log` - General logs
- `logs/errors.log` - Error details
- `logs/comfy_to_c4d_[date].log` - Session logs

### Clean Installation
If all else fails:
```bash
# Backup settings
copy .env .env.backup
copy config/*.json config_backup/

# Clean install
rmdir /s /q venv
rmdir /s /q src/__pycache__
del /s *.pyc

# Reinstall
install_dependencies.bat
```

---

## 📞 Getting Help

### Before Reporting Issues
1. **Try solutions above** for your specific symptom
2. **Check recent fixes** at top of this guide
3. **Enable debug logging** and collect error messages
4. **Test in isolation:**
   - Can you use ComfyUI web interface?
   - Can you run Cinema4D Python scripts?
   - Do example workflows work?

### Bug Report Template
```
**System Info:**
- OS: Windows 11
- Python: 3.11.x
- Cinema4D: 2024.x
- ComfyUI: Latest

**Issue:**
- What happened:
- Expected behavior:
- Steps to reproduce:

**Error Messages:**
[Paste from logs/errors.log]

**Screenshots:**
[If applicable]
```

---

**Remember:** Most issues are connection/path related. Verify all services are running and paths are correct! 🛠️✨