# Testing Guide

## Pre-Testing Checklist

### Environment Setup
- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed via `pip install -r requirements.txt`
- [ ] `.env` file created from `.env.example` with correct paths

### External Applications
- [ ] ComfyUI running at `http://localhost:8188`
- [ ] Required ComfyUI nodes installed (Hy3DWrapper, essentials, was-node-suite)
- [ ] Cinema4D 2024 launched
- [ ] Cinema4D MCP server script running

### File System
- [ ] Write permissions on all output directories
- [ ] Workflow JSON files present in `workflows/`
- [ ] No locked files in output directories

## Test Scenarios

### 1. Application Startup
```python
# Test: Launch application
python main.py
```

**Expected Results:**
- Main window appears with dark theme
- Console shows initialization messages
- Both status indicators (ComfyUI and Cinema4D) show green
- No error messages in console

**Troubleshooting:**
- Red status indicators: Check MCP servers are running
- Import errors: Verify all dependencies installed
- Window doesn't appear: Check Qt6 installation

### 2. Image Generation Pipeline

**Test Steps:**
1. Enter positive prompt: "a beautiful crystal sphere on white background"
2. Enter negative prompt: "blurry, low quality"
3. Set parameters:
   - Resolution: 512x512 (for faster testing)
   - Steps: 20
   - CFG Scale: 7.0
4. Click "Generate Images"

**Expected Results:**
- Progress bar shows generation progress
- Console logs ComfyUI execution
- Images appear in grid view after completion
- Files saved to `images/` directory

**Validation:**
```python
# Check generated files
import os
assert len(os.listdir("images")) > 0
```

### 3. 3D Model Generation

**Test Steps:**
1. Select one or more generated images
2. Click "Generate 3D Models"
3. Wait for Hy3D processing

**Expected Results:**
- Selected images list shows chosen files
- Console shows 3D generation progress
- .obj files appear in `3D/Hy3D/` directory
- 3D preview cards show in UI

**Validation:**
```python
# Check 3D output
import os
obj_files = [f for f in os.listdir("3D/Hy3D") if f.endswith(".obj")]
assert len(obj_files) > 0
```

### 4. Cinema4D Integration

**Test Steps:**
1. Go to Scene Assembly stage
2. Click "Import Selected to C4D"
3. Test deformer application:
   - Select object in scene list
   - Choose "bend" deformer
   - Click "Apply"
4. Test cloner creation:
   - Select multiple objects
   - Choose "radial" mode
   - Set count to 8
   - Click "Create"

**Expected Results:**
- Objects appear in Cinema4D viewport
- Deformers applied successfully
- Cloner created with selected objects
- Scene objects list updates

### 5. Procedural Scripts

**Test Script Execution:**
```python
# In Scene Assembly, after importing objects
# Test each script from the scripts/c4d/ directory
```

1. **Intelligent Object Scattering**
   - Creates scatter system with Fibonacci distribution
   - Objects placed with variation

2. **Organic Growth System**
   - Adds growth animation to objects
   - Deformers and fields created

3. **Volumetric Light Setup**
   - Lighting system created
   - Volumetric effects visible

4. **Smart Material Assignment**
   - Materials created and assigned
   - Object names analyzed for material type

### 6. Project Export

**Test Steps:**
1. Go to Export stage
2. Set project name: "TestProject_001"
3. Enable all options:
   - Copy textures
   - Create backup
   - Generate report
4. Click "Export Cinema4D Project"

**Expected Results:**
- Project saved to `exports/TestProject_001.c4d`
- Textures copied to `exports/tex/`
- Backup created in `exports/backup/`
- Report generated as `exports/TestProject_001_report.txt`

## Automated Tests

### Unit Tests
```bash
# Run unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=src tests/unit/
```

### Integration Tests
```bash
# Test MCP connections
pytest tests/integration/test_mcp_clients.py

# Test file monitoring
pytest tests/integration/test_file_monitor.py

# Test workflow management
pytest tests/integration/test_workflows.py
```

## Performance Testing

### Image Generation Benchmark
```python
# Test batch generation performance
import time

start = time.time()
# Generate 10 images
await image_stage.execute(params, batch_size=10)
end = time.time()

print(f"Generated 10 images in {end-start:.2f} seconds")
# Expected: < 60 seconds for 512x512 images
```

### File System Performance
```python
# Test file monitoring with many files
import shutil

# Create 100 test files
for i in range(100):
    shutil.copy("test_image.png", f"images/test_{i}.png")

# Monitor should handle without lag
# UI should remain responsive
```

## Error Handling Tests

### 1. ComfyUI Disconnection
- Stop ComfyUI while app is running
- Expected: Error message, status indicator turns red
- Restart ComfyUI
- Expected: Auto-reconnection attempt

### 2. Invalid Workflow
- Modify workflow JSON to be invalid
- Try to load workflow
- Expected: Validation error with details

### 3. File Permission Denied
- Lock output directory
- Try to generate images
- Expected: Clear error message about permissions

### 4. Cinema4D Script Error
- Modify C4D script to have syntax error
- Try to execute
- Expected: Error captured and displayed

## Memory and Resource Testing

### Memory Leak Check
```python
# Monitor memory usage during extended operation
import psutil
import os

process = psutil.Process(os.getpid())

# Initial memory
initial_mem = process.memory_info().rss / 1024 / 1024

# Run 50 generation cycles
for i in range(50):
    await image_stage.execute(params)
    
# Final memory
final_mem = process.memory_info().rss / 1024 / 1024

# Should not increase by more than 100MB
assert (final_mem - initial_mem) < 100
```

## UI Testing

### Responsive Design
- Resize window to minimum size (800x600)
- All UI elements should remain accessible
- No overlapping or cutoff controls

### Theme Consistency
- All widgets should use dark theme
- Consistent colors and fonts
- Readable text contrast

### User Feedback
- All long operations show progress
- Clear status messages
- No UI freezing during operations

## Logging and Debugging

### Check Log Files
```bash
# View latest log
type logs\comfy_to_c4d_*.log

# Check for errors
findstr /i "error" logs\*.log
```

### Enable Debug Mode
```python
# In .env file
LOG_LEVEL=DEBUG

# Provides detailed operation logging
```

## Common Issues and Solutions

### Issue: "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "Connection refused"
```bash
# Check ports
netstat -an | findstr "8188"
netstat -an | findstr "5000"
```

### Issue: "Workflow not found"
```bash
# Verify workflow files
dir workflows\*.json
```

### Issue: "Access denied"
```bash
# Run as administrator or check permissions
icacls images /grant Everyone:F
icacls "3D\Hy3D" /grant Everyone:F
```