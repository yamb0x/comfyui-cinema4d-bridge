# ComfyUI to Cinema4D Bridge - Troubleshooting Guide

## 🚨 Common Issues & Solutions

### **🔌 Connection Problems**

#### ComfyUI Connection Failed
```
Error: Could not connect to ComfyUI at http://127.0.0.1:8188
```

**Solutions:**
1. **Check ComfyUI is running**: Launch ComfyUI and ensure API is enabled
2. **Verify API settings**: `--listen 0.0.0.0 --port 8188` in ComfyUI launch
3. **Check firewall**: Allow port 8188 through Windows Firewall
4. **Test manually**: Visit `http://127.0.0.1:8188` in browser

#### Cinema4D MCP Server Not Starting
```
Error: Cinema4D MCP server failed to start
```

**Solutions:**
1. **Run setup script**: Execute `Start ComfyUI MCP Server.bat` as administrator
2. **Check paths**: Verify `CINEMA4D_PATH` in `.env` file
3. **Permissions**: Ensure write access to Cinema4D installation directory
4. **Port conflicts**: Change `CINEMA4D_MCP_PORT` if 8765 is in use

### **⚙️ Configuration Issues**

#### .env File Not Found
```
Error: Configuration file .env not found
```

**Solutions:**
1. **Copy template**: `copy .env.example .env`
2. **Edit paths**: Update all paths to match your system
3. **Use absolute paths**: Avoid relative paths in configuration

#### Invalid Paths
```
Error: ComfyUI path does not exist: D:/InvalidPath
```

**Solutions:**
1. **Verify installation**: Check ComfyUI is actually installed
2. **Update .env**: Use correct paths with forward slashes
3. **Test manually**: Navigate to path in file explorer

### **🎬 Cinema4D Issues**

#### Object Creation Fails
```
Error: Failed to create cube in Cinema4D
```

**Solutions:**
1. **Check Cinema4D is open**: Must have active document
2. **Verify constants**: Use `c4d.Ocube` not numeric IDs
3. **Test manually**: Run script in Cinema4D Script Manager
4. **Update Cinema4D**: Ensure R2024+ with Python API

#### Parameter Errors
```
Error: 'PRIM_SPHERE_RADIUS' object has no attribute
```

**Solutions:**
1. **Use abbreviated names**: `PRIM_SPHERE_RAD` not `PRIM_SPHERE_RADIUS`
2. **Check documentation**: Verify parameter names in Cinema4D Python console
3. **Use constants**: Never use numeric parameter IDs

### **🖼️ Image Generation Problems**

#### Workflow JSON Errors
```
Error: Failed to load workflow: Invalid JSON format
```

**Solutions:**
1. **Validate JSON**: Use JSON validator to check workflow file
2. **Check ComfyUI export**: Re-export workflow from ComfyUI
3. **Backup restore**: Use backup workflow from `workflows/_backup/`

#### Missing Models/LoRAs
```
Error: Model 'flux-dev' not found in ComfyUI
```

**Solutions:**
1. **Download models**: Install required models in ComfyUI
2. **Check paths**: Verify model paths in ComfyUI settings
3. **Update workflow**: Use available models in workflow

### **🎭 3D Model Generation Issues**

#### Hy3D Workflow Fails
```
Error: Hy3D workflow execution failed
```

**Solutions:**
1. **Install Hy3D nodes**: Ensure Hy3D ComfyUI extension installed
2. **Check GPU memory**: Close other applications to free VRAM
3. **Reduce parameters**: Lower mesh density/texture resolution
4. **Update workflow**: Use latest Hy3D workflow JSON

#### Viewer Memory Issues
```
Error: Too many 3D viewers open (50 limit reached)
```

**Solutions:**
1. **Close viewers**: Click 'Clear' button to close all viewers
2. **Increase limit**: Modify `MAX_VIEWERS` in config
3. **Restart application**: Full reset clears all viewers

### **🎨 UI/UX Problems**

#### Dark Theme Not Applied
```
Issue: Parts of UI showing light theme
```

**Solutions:**
1. **Restart application**: Theme applies on startup
2. **Check styles**: Verify `styles.py` imports correctly
3. **Clear cache**: Delete `__pycache__` folders

#### Parameter Controls Missing
```
Issue: Right panel empty or not updating
```

**Solutions:**
1. **Select workflow**: Choose workflow in dropdown first
2. **Check JSON**: Ensure workflow has extractable parameters
3. **Restart application**: Reset parameter detection

### **📁 File System Issues**

#### Permission Denied
```
Error: Permission denied writing to C:/Program Files/
```

**Solutions:**
1. **Run as administrator**: Right-click → "Run as administrator"
2. **Change output directory**: Use Documents or Desktop folder
3. **Check antivirus**: Whitelist application in antivirus software

#### Files Not Detected
```
Issue: Generated images/models not appearing in UI
```

**Solutions:**
1. **Check file monitor**: Restart file monitoring in application
2. **Verify paths**: Check output directories in config
3. **File extensions**: Ensure generated files have correct extensions

### **🔧 Performance Issues**

#### Slow Application Startup
```
Issue: Application takes 30+ seconds to start
```

**Solutions:**
1. **Close other applications**: Free system memory
2. **Check disk space**: Ensure adequate free disk space
3. **Disable antivirus scanning**: Temporarily disable real-time scanning

#### High Memory Usage
```
Issue: Application using excessive RAM
```

**Solutions:**
1. **Close 3D viewers**: Use 'Clear' button frequently
2. **Reduce image cache**: Lower cache size in settings
3. **Restart periodically**: Fresh start clears memory leaks

### **🐛 Debug Strategies**

#### Enable Debug Logging
1. **Set log level**: Add `LOG_LEVEL=DEBUG` to `.env`
2. **Check console**: Watch console output while reproducing issue
3. **Check log files**: Review `logs/errors.log` for details

#### Isolate Problems
1. **Test components**: Use individual tabs to isolate issues
2. **Check dependencies**: Verify all required software installed
3. **Clean install**: Reinstall application if issues persist

#### Manual Testing
1. **Test ComfyUI**: Generate images directly in ComfyUI web interface
2. **Test Cinema4D**: Run Python scripts manually in Cinema4D
3. **Test workflows**: Validate JSON files in ComfyUI

### **📞 Getting Help**

#### Before Reporting Issues
1. **Check this guide**: Review all relevant sections
2. **Check logs**: Include relevant error messages
3. **Test isolated**: Reproduce issue with minimal setup
4. **System info**: Note OS version, Python version, etc.

#### What to Include in Bug Reports
- **Steps to reproduce**: Detailed sequence of actions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Complete error text from logs
- **System information**: OS, Python version, etc.
- **Screenshots**: Visual evidence if applicable

---

**Most issues can be resolved by checking connections, verifying paths, and ensuring all dependencies are properly installed.** 🛠️✨