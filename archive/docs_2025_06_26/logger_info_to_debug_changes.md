# Logger.info() to Logger.debug() Changes

## Summary
Based on the codebase analysis, the following logger.info() calls should be changed to logger.debug() as they represent operational logs, parameter loading, file monitoring, and other verbose outputs that don't need to be at INFO level.

## Changes by Category

### 1. Parameter Loading & Configuration
These are internal operations that happen frequently and clutter the console:

**src/core/app_redesigned.py:**
- Line 1677: `self.logger.info(f"Validated parameters: {list(params.keys())}")`
- Line 1679: `self.logger.info(f"Injecting parameters into workflow...")`
- Line 2152: `self.logger.info(f"Collected 3D parameters: {list(params.keys())}")`
- Line 2158: `self.logger.info(f"Validated 3D parameters: {list(params.keys())}")`
- Line 2173: `self.logger.info(f"Injecting parameters for image: {image_path.name}")`

**src/core/app_ui_methods.py:**
- Line 322: `self.logger.info("Loaded dynamic 3D parameters on demand")`
- Line 324: `self.logger.info("Failed to create dynamic 3D parameters, keeping static")`
- Line 421: `self.logger.info(f"Created dynamic 3D parameters section for {len(selected_nodes)} configured nodes")`
- Line 548: `self.logger.info(f"Collected {len(params)} parameters from 3D UI")`
- Line 1083: `self.logger.info(f"🔄 _load_parameters_from_config called for {param_type}...")`
- Line 1096: `self.logger.info(f"🔍 UI Components status: {ui_components}")`

### 2. File Monitoring & Discovery
These are repetitive monitoring operations:

**src/core/app_redesigned.py:**
- Line 4543: `self.logger.info(f"Using configured models directory: {models_dir}")`
- Line 4545: `self.logger.info(f"Loading 3D models from: {models_dir}")`
- Line 4560: `self.logger.info(f"Found {len(all_models)} 3D models to load into View All grid")`
- Line 4566: `self.logger.info(f"Checking local models directory: {local_models_dir}")`
- Line 4572: `self.logger.info(f"Found {len(local_models)} {pattern} files in local directory")`
- Line 4584: `self.logger.info(f"Trying local models directory: {local_models_dir}")`
- Line 4593: `self.logger.info(f"Found {len(found_files)} {pattern} files in local directory")`
- Line 4614: `self.logger.info(f"Models grid has {len(self.all_models_grid.cards)} models loaded")`
- Line 4872: `self.logger.info(f"Auto-detected textures for {obj.model_3d.name}: {len(texture_files)} files")`

**src/core/file_monitor.py:**
- Line 36: `self.logger.info(f"File monitor detected CREATED: {file_path.name}")`

### 3. Workflow Processing & Node Conversion
Internal workflow operations that are too verbose:

**src/core/workflow_manager.py:**
- Line 79: `self.logger.info(f"Workflow contains: {', '.join(node_types)}")`
- Line 147: `self.logger.info(f"Converted UI workflow to API format with {len(api_workflow)} nodes")`
- Line 325: `self.logger.info(f"📐 MINIMAL: Converted PrimitiveNode #{node_id} to {node_type}")`
- Line 359: `self.logger.info(f"📐 MINIMAL: Camera config processed for node {node_id}")`
- Line 610: `self.logger.info(f"Converting UI workflow with {len(ui_workflow.get('nodes', []))} nodes to API format")`
- Line 614: `self.logger.info(f"All node IDs in UI workflow: {all_node_ids}")`
- Line 628: `self.logger.info(f"Skipping Reroute node {node_id} - handled through link resolution")`
- Line 633: `self.logger.info(f"Skipping {node_type} node {node_id} - will handle distributed connections")`
- Line 639: `self.logger.info(f"Skipping bypassed {node_type} node {node_id} in API conversion")`
- Lines 869-1149: All the node conversion fix logs (🔧 CONVERSION FIX, 🔧 CAMERA FIX, etc.)

### 4. UI State & Testing
Internal UI state checks:

**src/core/app_redesigned.py:**
- Line 4876: `self.logger.info(f"Testing unified selector visibility...")`
- Line 4880: `self.logger.info(f"Main unified selector visibility: {self.unified_object_selector.isVisible()}")`
- Line 4881: `self.logger.info(f"Main unified selector parent: {self.unified_object_selector.parent()}")`
- Line 4885: `self.logger.info(f"Found {len(self.unified_selectors)} tab selector instances")`
- Line 4887: `self.logger.info(f"Tab '{tab_name}' selector visibility: {selector.isVisible()}")`
- Line 4888: `self.logger.info(f"Tab '{tab_name}' selector parent: {selector.parent()}")`

### 5. Object Management Operations
Routine object operations:

**src/ui/object_selection_widget.py:**
- Line 181: `logger.info(f"Added image {image_path.name} to object pool")`
- Line 205: `logger.info(f"Added image to workflow: {image_path.name}")`
- Line 222: `logger.info(f"Removed image from workflow: {image_path.name}")`
- Line 232: `logger.info(f"Linked model {model_path.name} to image {source_image_path.name}")`
- Line 243: `logger.info(f"Created new workflow object for model: {model_path.name}")`
- Line 253: `logger.info(f"Model already exists, marked as selected: {model_path.name}")`
- Line 268: `logger.info(f"Added standalone 3D model: {model_path.name}")`
- Line 281: `logger.info(f"Removed standalone object: {object_id}")`
- Line 285: `logger.info(f"Deselected workflow object: {object_id}")`
- Line 299: `logger.info(f"Marked {model_path.name} as textured")`

### 6. ComfyUI Debug Information
Detailed ComfyUI operations:

**src/mcp/comfyui_client.py:**
- Line 253: `self.logger.info(f"Loaded workflow: {workflow_path}")`
- Line 305-309: All the workflow save instructions
- Line 375-376: SAVED FINAL WORKFLOW comparison logs
- Line 387: `self.logger.info(f"🚀 SENDING TO COMFYUI: Hy3DLoadMesh node {node_id} glb_path='{mesh_path}'")`
- Line 390: `self.logger.info(f"🚀 SENDING TO COMFYUI: Hy3DUploadMesh node {node_id} mesh='{mesh_input}'")`
- Line 585-588: Model count logs

### 7. Settings & Configuration Changes
Routine settings updates:

**src/ui/settings_dialog.py:**
- Line 845: `logger.info(f"Auto-save timer started with {self.auto_save_interval_spin.value()} minute interval")`
- Line 847: `logger.info("Auto-save timer setup complete (not started - disabled or controls not ready)")`
- Line 910: `logger.info(f"Font size changed to {value}px")`
- Line 925: `logger.info(f"Accent color changed to {self.accent_color}")`
- Line 993: `logger.info(f"Console auto-scroll {'enabled' if checked else 'disabled'}")`
- Line 1020: `logger.info(f"Console buffer size changed to {value} lines")`
- Line 1047: `logger.info(f"Timestamp format changed to {format_str}")`
- Line 1063: `logger.info(f"Max concurrent operations changed to {value}")`
- Line 1082: `logger.info(f"Memory limit changed to {value}MB")`
- Line 1101: `logger.info(f"GPU acceleration {'enabled' if checked else 'disabled'}")`
- Line 1120: `logger.info(f"Cache size changed to {value}MB")`
- Line 1127: `logger.info(f"Auto-clear cache {'enabled' if checked else 'disabled'}")`
- Line 1146: `logger.info(f"File logging {'enabled' if checked else 'disabled'}")`
- Line 1153: `logger.info(f"Log rotation {'enabled' if checked else 'disabled'}")`
- Line 1160: `logger.info(f"Max log file size changed to {value}MB")`
- Line 1173: `logger.info(f"Debug mode {'enabled' if checked else 'disabled'}")`
- Line 1181: `logger.info(f"Telemetry {'enabled' if checked else 'disabled'}")`
- Line 1223: `logger.info(f"Auto-save interval changed to {value} minutes")`
- Line 1225: `logger.info(f"Auto-save interval set to {value} minutes (currently disabled)")`

## Logs to Keep at INFO Level
These should remain as logger.info() as they represent important user-facing operations:

1. Application startup/initialization logs
2. Successful connection establishment (ComfyUI, Cinema4D)
3. Workflow execution start/completion
4. Image/3D/Texture generation start messages
5. File save/load operations
6. Project operations (new, save, load)
7. Error recovery or important state changes
8. User-initiated actions (button clicks, menu selections)

## Implementation Script
To make these changes efficiently, here's a sed script that can be used:

```bash
# Create backup first
cp -r src src_backup

# Apply changes with sed
# Parameter loading
sed -i 's/self\.logger\.info(f"Validated parameters:/self.logger.debug(f"Validated parameters:/g' src/core/app_redesigned.py
sed -i 's/self\.logger\.info(f"Injecting parameters/self.logger.debug(f"Injecting parameters/g' src/core/app_redesigned.py
# ... continue for each pattern
```

## Expected Impact
Changing these ~150+ logger.info() calls to logger.debug() will:
- Reduce console output by approximately 95%
- Keep only important user-facing messages visible
- Make debugging easier by enabling debug mode when needed
- Improve application perceived performance (less I/O)
