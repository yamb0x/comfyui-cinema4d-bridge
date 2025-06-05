# Quick Reference

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+G` | Generate images |
| `Ctrl+3` | Generate 3D models |
| `Ctrl+I` | Import to Cinema4D |
| `Ctrl+E` | Export project |
| `Ctrl+R` | Refresh scene |
| `Ctrl+Q` | Quit application |
| `F1` | Show help |
| `F5` | Reload workflows |

## Common Tasks

### Generate Images
```
1. Enter prompt
2. Set resolution (512x512 for testing, 1024x1024 for quality)
3. Click "Generate Images" or press Ctrl+G
4. Wait for completion (check progress bar)
```

### Create 3D Models
```
1. Select images in grid (click checkboxes)
2. Click "Generate 3D Models" or press Ctrl+3
3. Models save to 3D/Hy3D/ automatically
```

### Import to Cinema4D
```
1. Go to Scene Assembly stage
2. Select models or click "Import All"
3. Objects appear at grid positions
4. Use scene list to select for modifications
```

### Apply Effects
```
Deformers:
- Select object → Choose deformer → Apply

Cloners:
- Select multiple → Choose mode → Set count → Create

Scripts:
- Available in Scene Assembly stage
- Auto-detects appropriate objects
```

## File Locations

| Type | Location |
|------|----------|
| Generated Images | `images/` |
| 3D Models | `3D/Hy3D/` |
| Workflows | `workflows/` |
| C4D Scripts | `scripts/c4d/` |
| Exports | `exports/` |
| Logs | `logs/` |
| Config | `config/app_config.json` |

## Status Indicators

- 🟢 Green: Connected and ready
- 🔴 Red: Disconnected
- 🟡 Yellow: Connecting/Processing

## Console Commands

The console shows real-time status. Key messages:

| Message | Meaning |
|---------|---------|
| `Connected to ComfyUI` | Ready for generation |
| `Queued prompt: xxx` | Job submitted |
| `Progress: x/y` | Generation progress |
| `New file detected` | Output ready |
| `Imported xxx to Cinema4D` | Model in scene |

## Workflow Parameters

### Image Generation
- **Resolution**: 512, 768, 1024, 1536, 2048
- **Steps**: 15-50 (20 default)
- **CFG**: 5-15 (7 default)
- **Sampler**: euler, dpm++, ddim
- **Seed**: -1 for random

### 3D Generation
- **Mesh Density**: low, medium, high, ultra
- **Texture**: 512, 1024, 2048, 4096
- **Normal Map**: On/Off
- **Optimization**: On/Off

## Troubleshooting

### Connection Issues
```bash
# Check ComfyUI
curl http://localhost:8188/system_stats

# Check Cinema4D port
netstat -an | findstr "5000"
```

### Generation Failures
1. Check console for errors
2. Verify workflow files exist
3. Ensure models are downloaded
4. Check disk space

### Performance
- Lower resolution for testing
- Reduce sampling steps
- Disable 3D preview
- Close unnecessary apps

## Best Practices

### Prompting
```
Good: "professional product photo of glass sphere, studio lighting, white background"
Bad: "sphere"

Include: Subject, style, lighting, background
Avoid: Blur, low quality, watermark
```

### Batch Processing
- Generate multiple variations with different seeds
- Select best results for 3D conversion
- Import all at once for efficiency

### Scene Organization
- Use scatter script for many objects
- Apply materials after import
- Group related objects
- Save incrementally

## Cinema4D Scripts

### Intelligent Scattering
```python
TARGET_OBJECTS = ["Hy3D_001", "Hy3D_002"]
# Creates Fibonacci spiral distribution
```

### Organic Growth
```python
# Applies to selected objects
# Adds animation and deformers
```

### Volumetric Lighting
```python
# No parameters needed
# Creates full lighting setup
```

### Smart Materials
```python
# Auto-assigns based on names
# Keywords: glass, metal, organic, stone
```

## Export Options

| Option | Purpose |
|--------|---------|
| Copy Textures | Includes all textures in project |
| Create Backup | Saves timestamped copy |
| Generate Report | Lists all objects and stats |

## Memory Management

- Clear image grid after 3D conversion
- Close preview windows when done
- Restart app after 100+ generations
- Monitor task manager for issues

## Network Features

### Remote ComfyUI
```env
COMFYUI_SERVER_URL="http://192.168.1.100:8188"
COMFYUI_WEBSOCKET_URL="ws://192.168.1.100:8188/ws"
```

### Shared Directories
- Map network drives for outputs
- Use UNC paths in config
- Ensure write permissions

## Updates

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Update Workflows
- Download latest from ComfyUI
- Validate before replacing
- Keep backups of custom workflows