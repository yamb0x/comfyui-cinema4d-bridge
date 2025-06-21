# Dynamic UI Implementation Guide

This guide provides a comprehensive overview of the dynamic UI system implemented in Tab 1 (Image Generation) and instructions for implementing Tab 2 (3D Model Generation) using the same patterns.

## Table of Contents
1. [Overview](#overview)
2. [Dynamic Parameter Loading](#dynamic-parameter-loading)
3. [Workflow Execution](#workflow-execution)
4. [Cross-Tab Data Flow](#cross-tab-data-flow)
5. [Implementation Guide for Tab 2](#implementation-guide-for-tab-2)
6. [Code Examples](#code-examples)

---

## Overview

The dynamic UI system automatically generates interface widgets based on ANY ComfyUI workflow, eliminating the need for hardcoded UI elements for each workflow type.

### Architecture Components

1. **Workflow Manager** (`workflow_manager.py`)
   - Loads and parses workflow JSON files
   - Converts custom nodes to standard nodes
   - Handles parameter injection
   - Manages workflow execution

2. **Dynamic Widget Updater** (`dynamic_widget_updater.py`)
   - Updates workflow parameters from UI widgets
   - Node-agnostic approach
   - Handles any node type without hardcoding

3. **UI Creation Methods** (`app_ui_methods.py`)
   - Creates widgets based on node definitions
   - Manages widget lifecycle
   - Handles cross-tab persistence

4. **Model Scanner** (`model_scanner.py`)
   - Dynamically scans ComfyUI model directories
   - Populates dropdown options
   - Supports all model types

---

## Dynamic Parameter Loading

### 1. Workflow Selection and Loading

```python
def _on_workflow_changed(self, workflow_name: str):
    """Handle workflow selection change"""
    # Save selected workflow
    config_file = self._get_config_path_for_tab(self.main_tabs.currentIndex())
    self._save_workflow_selection(config_file, workflow_name)
    
    # Trigger parameter loading
    self._load_parameters_from_config("image")
```

### 2. Node Detection and Widget Creation

```python
def _load_parameters_from_config(self, param_type: str):
    """Load workflow and create UI dynamically"""
    # 1. Load workflow JSON
    workflow = self.workflow_manager.load_workflow(workflow_file)
    
    # 2. Clear existing widgets
    self._clear_dynamic_widgets()
    
    # 3. For each selected node in workflow
    for node_id in selected_nodes:
        node_data = nodes_dict.get(node_id)
        
        # 4. Create widget group
        group_box = self._create_node_group(node_type, node_id, title)
        
        # 5. Add bypass checkbox in header
        bypass_check = QCheckBox("Bypass")
        bypass_check.stateChanged.connect(lambda: self._on_node_bypass_changed(node_id))
        
        # 6. Create widgets based on node definition
        widgets = self._create_widgets_for_node(node_type, node_id, widgets_values)
        
        # 7. Add to dynamic layout
        self.dynamic_params_layout.addWidget(group_box)
```

### 3. Widget Type Mapping

```python
def _get_node_parameter_definitions(self):
    """Define parameter structures for each node type"""
    return {
        'CheckpointLoaderSimple': {
            'widgets_mapping': [
                {'name': 'Checkpoint File', 'type': 'string', 'widget': 'combo'}
            ]
        },
        'LoraLoader': {
            'widgets_mapping': [
                {'name': 'LoRA File', 'type': 'string', 'widget': 'combo'},
                {'name': 'Model Strength', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 2.0},
                {'name': 'CLIP Strength', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 2.0}
            ]
        },
        'KSampler': {
            'widgets_mapping': [
                {'name': 'Seed', 'type': 'int', 'widget': 'int'},
                {'name': 'Steps', 'type': 'int', 'widget': 'int', 'min': 1, 'max': 150},
                {'name': 'CFG Scale', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 30.0},
                # ... more parameters
            ]
        }
    }
```

### 4. Dynamic Model Options

```python
class ComfyUIModelScanner:
    """Scans ComfyUI directories for available models"""
    
    NODE_TO_MODEL_DIR = {
        "CheckpointLoaderSimple": "checkpoints",
        "LoraLoader": "loras",
        "VAELoader": "vae",
        "UNETLoader": "diffusion_models",
        # ... more mappings
    }
    
    def scan_models(self, model_type: str) -> List[str]:
        """Scan directory for model files"""
        model_dir = self.models_base_path / self.NODE_TO_MODEL_DIR.get(model_type, "")
        if model_dir.exists():
            return [f.name for f in model_dir.glob("**/*") if f.suffix in self.MODEL_EXTENSIONS]
        return []
```

---

## Workflow Execution

### 1. Parameter Collection

```python
async def _async_generate_images(self):
    """Execute image generation workflow"""
    # 1. Collect parameters from UI
    params = await self._collect_workflow_parameters()
    
    # 2. Get workflow and inject parameters
    workflow = self.workflow_manager.load_workflow(workflow_path)
    workflow_with_params = self.workflow_manager.inject_parameters(workflow, params)
```

### 2. Dynamic Parameter Injection

```python
class DynamicWidgetUpdater:
    """Updates workflow with UI widget values"""
    
    def update_workflow_from_widgets(self, workflow, widget_refs, preserved_widgets):
        """Update workflow with current widget values"""
        for node in workflow.get("nodes", []):
            node_id = str(node.get("id"))
            node_type = node.get("type")
            
            # Get widgets_values for this node
            widgets_values = node.get("widgets_values", [])
            
            # Update each parameter
            for i, value in enumerate(widgets_values):
                widget_key = f"{node_type}_{node_id}_{i}"
                
                if widget_key in widget_refs:
                    widget = widget_refs[widget_key]
                    if self._is_widget_valid(widget):
                        new_value = self._get_widget_value(widget)
                        widgets_values[i] = new_value
```

### 3. Custom Node Conversion

```python
def convert_to_api_format(self, workflow: Dict) -> Dict:
    """Convert workflow to ComfyUI API format"""
    api_workflow = {}
    
    for node in workflow.get("nodes", []):
        node_type = node["type"]
        
        # Handle custom node conversion
        if node_type == "Image Save":  # WAS Node Suite
            # Convert to standard SaveImage
            node_data["class_type"] = "SaveImage"
            inputs.clear()
            inputs["images"] = image_connection
            inputs["filename_prefix"] = "ComfyUI"
```

### 4. Workflow Completion Monitoring

```python
def _start_workflow_completion_monitoring(self, prompt_id: str, batch_size: int):
    """Monitor workflow completion via history API"""
    # Start timer to check history
    self.workflow_monitor_timer = QTimer()
    self.workflow_monitor_timer.timeout.connect(self._check_workflow_completion)
    self.workflow_monitor_timer.start(2000)  # Check every 2 seconds

async def _check_workflow_completion(self):
    """Check if workflow completed and download images"""
    # Get workflow history
    history = await self.comfyui_client.get_history(prompt_id)
    
    if prompt_id in history and history[prompt_id]["status"]["completed"]:
        # Download images from outputs
        outputs = history[prompt_id]["outputs"]
        for node_id, output_data in outputs.items():
            if "images" in output_data:
                for image_info in output_data["images"]:
                    await self._download_and_save_image(image_info)
```

---

## Cross-Tab Data Flow

### 1. Unified Object Selection

```python
class UnifiedObjectSelectionWidget(QWidget):
    """Manages cross-tab object selection"""
    
    def add_image_selection(self, image_path: Path):
        """Add image to selection (from Tab 1)"""
        object_id = self._generate_object_id(image_path)
        self.objects[object_id] = ObjectInfo(
            id=object_id,
            name=image_path.name,
            type="image",
            path=str(image_path),
            selected=True
        )
        self._update_ui()
```

### 2. Selection Persistence

```python
def _sync_panel_tabs(self, index: int):
    """Sync left/right panels when main tab changes"""
    # Selection persists automatically through unified object selector
    # Each tab gets the same instance of the selector widget
    if index == 1:  # 3D Model Generation
        # Selected images from Tab 1 are available
        selected_images = self.unified_object_selector.get_selected_objects("image")
```

---

## Implementation Guide for Tab 2

### Step 1: Configure 3D Parameters Loading

```python
def _on_configure_3d_parameters(self):
    """Handle Configure 3D Generation Parameters menu action"""
    # 1. Show workflow selection dialog
    workflows = self._get_3d_workflows()
    selected_workflow, ok = QInputDialog.getItem(
        self, "Select 3D Workflow", "Choose workflow:", workflows
    )
    
    if ok:
        # 2. Load workflow and detect nodes
        workflow = self.workflow_manager.load_workflow(selected_workflow)
        
        # 3. Show node selection dialog
        dialog = NodeSelectionDialog(workflow, self)
        if dialog.exec():
            # 4. Save configuration
            config = {
                "workflow_file": selected_workflow,
                "selected_nodes": dialog.selected_nodes,
                "node_info": dialog.node_info
            }
            self._save_config("3d_parameters_config.json", config)
```

### Step 2: Dynamic UI for 3D Tab

```python
def _create_3d_model_controls(self) -> QWidget:
    """Create 3D model generation controls"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # 1. Prompt section (if workflow has text encoding)
    prompt_section = self._create_parameter_section("Prompt Generation")
    self.model_prompt = PositivePromptWidget()  # Only if needed
    prompt_section.layout().addWidget(self.model_prompt)
    
    # 2. Object selection (shows images from Tab 1)
    selection_section = self._create_parameter_section("Selected Images")
    self.selected_images_list = QListWidget()
    selection_section.layout().addWidget(self.selected_images_list)
    
    # 3. Dynamic parameters container
    self.dynamic_3d_params_container = QScrollArea()
    self.dynamic_3d_params_layout = QVBoxLayout()
    
    # 4. Load parameters from config
    self._load_parameters_from_config("3d")
    
    return widget
```

### Step 3: Workflow Execution with Image Injection

```python
async def _async_generate_3d_models(self):
    """Generate 3D models from selected images"""
    # 1. Get selected images
    selected_images = self.unified_object_selector.get_selected_objects("image")
    
    if not selected_images:
        QMessageBox.warning(self, "No Selection", "Please select images first")
        return
    
    # 2. For each image, run workflow
    for image_obj in selected_images:
        # 3. Load workflow
        workflow = self.workflow_manager.load_workflow(workflow_path)
        
        # 4. Find LoadImage node and inject image path
        for node in workflow.get("nodes", []):
            if node.get("type") == "LoadImage":
                node["widgets_values"] = [str(image_obj.path), "image"]
        
        # 5. Collect other parameters
        params = await self._collect_3d_workflow_parameters()
        
        # 6. Execute workflow
        workflow_api = self.workflow_manager.convert_to_api_format(workflow)
        prompt_id = await self.comfyui_client.queue_prompt(workflow_api)
        
        # 7. Monitor for completion
        self._start_3d_completion_monitoring(prompt_id)
```

### Step 4: 3D File Monitoring

```python
def _start_3d_completion_monitoring(self, prompt_id: str):
    """Monitor for 3D model generation completion"""
    # Monitor ComfyUI/output/3D directory
    output_dir = Path(self.config.comfyui_base_path) / "output" / "3D"
    
    # Start file monitor
    self.model_monitor = FileMonitor([output_dir])
    self.model_monitor.file_created.connect(self._on_3d_model_created)
    self.model_monitor.start()

def _on_3d_model_created(self, file_path: Path):
    """Handle new 3D model file"""
    if file_path.suffix in ['.glb', '.obj', '.fbx']:
        # Load into 3D viewer
        self._load_3d_model_preview(file_path)
```

### Step 5: 3D Viewer Integration

```python
def _load_3d_model_preview(self, model_path: Path):
    """Load 3D model into viewer"""
    # Use the new viewer from /viewer directory
    viewer_path = Path(__file__).parent.parent.parent / "viewer"
    
    # Option 1: Embed viewer in Qt widget
    from ui.viewers.web_3d_viewer import Web3DViewer
    viewer = Web3DViewer()
    viewer.load_model(model_path)
    
    # Add to preview card
    preview_card = self._create_3d_preview_card(model_path)
    preview_card.layout().addWidget(viewer)
    self.model_grid.addWidget(preview_card)
    
    # Option 2: Launch external viewer
    import subprocess
    subprocess.Popen([
        str(viewer_path / "run.bat"),
        str(model_path)
    ])
```

---

## Code Examples

### Example 1: Complete Dynamic Widget Creation

```python
def _create_widget_from_definition(self, widget_def: dict, value: Any, 
                                 node_type: str, node_id: str, param_key: str) -> QWidget:
    """Create widget based on parameter definition"""
    widget_type = widget_def.get('widget', 'text')
    name = widget_def.get('name', 'Parameter')
    
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Label
    label = QLabel(f"{name}:")
    label.setMinimumWidth(150)
    layout.addWidget(label)
    
    # Create appropriate widget
    if widget_type == 'combo':
        widget = QComboBox()
        options = self._get_model_options_for_parameter(node_type, name)
        widget.addItems(options)
        if value in options:
            widget.setCurrentText(value)
    
    elif widget_type == 'float':
        widget = QDoubleSpinBox()
        widget.setRange(widget_def.get('min', -999999), widget_def.get('max', 999999))
        widget.setSingleStep(widget_def.get('step', 0.01))
        widget.setValue(float(value) if value else 0.0)
    
    elif widget_type == 'int':
        widget = QSpinBox()
        widget.setRange(widget_def.get('min', -999999), widget_def.get('max', 999999))
        widget.setValue(int(value) if value else 0)
    
    elif widget_type == 'checkbox':
        widget = QCheckBox()
        widget.setChecked(bool(value))
    
    else:  # text
        widget = QLineEdit()
        widget.setText(str(value) if value else "")
    
    # Store widget reference
    self.dynamic_widget_refs[param_key] = widget
    
    # Connect change signal
    if hasattr(widget, 'currentTextChanged'):
        widget.currentTextChanged.connect(lambda: self._on_dynamic_param_changed())
    elif hasattr(widget, 'valueChanged'):
        widget.valueChanged.connect(lambda: self._on_dynamic_param_changed())
    elif hasattr(widget, 'stateChanged'):
        widget.stateChanged.connect(lambda: self._on_dynamic_param_changed())
    elif hasattr(widget, 'textChanged'):
        widget.textChanged.connect(lambda: self._on_dynamic_param_changed())
    
    layout.addWidget(widget)
    layout.addStretch()
    
    return container
```

### Example 2: Workflow Parameter Collection

```python
async def _collect_workflow_parameters(self) -> Dict[str, Any]:
    """Collect all parameters from dynamic UI"""
    params = {}
    
    # Get prompts if available
    if hasattr(self, 'positive_prompt'):
        params['positive_prompt'] = self.positive_prompt.get_prompt()
    if hasattr(self, 'negative_prompt'):
        params['negative_prompt'] = self.negative_prompt.get_prompt()
    
    # Get dimensions from left panel
    if hasattr(self, 'width_spin'):
        params['width'] = self.width_spin.value()
    if hasattr(self, 'height_spin'):
        params['height'] = self.height_spin.value()
    if hasattr(self, 'batch_size_spin'):
        params['batch_size'] = self.batch_size_spin.value()
    
    # Get dynamic parameters
    if hasattr(self, 'dynamic_widget_updater'):
        # Update workflow with current widget values
        workflow = self.current_workflow.copy()
        self.dynamic_widget_updater.update_workflow_from_widgets(
            workflow, 
            self.dynamic_widget_refs,
            self.preserved_prompt_widgets
        )
        
        # Extract parameters from updated workflow
        for node in workflow.get("nodes", []):
            node_id = str(node.get("id"))
            widgets_values = node.get("widgets_values", [])
            
            # Store in params for injection
            params[f"node_{node_id}_values"] = widgets_values
    
    return params
```

### Example 3: Error Handling Pattern

```python
async def _async_generate_3d_models(self):
    """Generate 3D models with comprehensive error handling"""
    try:
        # Check prerequisites
        if not self.comfyui_client.is_connected():
            raise ConnectionError("ComfyUI not connected")
        
        selected_images = self.unified_object_selector.get_selected_objects("image")
        if not selected_images:
            raise ValueError("No images selected")
        
        # Update UI state
        self.generate_3d_btn.setText("GENERATING...")
        self.generate_3d_btn.setEnabled(False)
        
        # Process each image
        for i, image_obj in enumerate(selected_images):
            try:
                self.logger.info(f"Processing image {i+1}/{len(selected_images)}: {image_obj.name}")
                
                # Execute workflow
                prompt_id = await self._execute_3d_workflow_for_image(image_obj)
                
                # Monitor completion
                await self._wait_for_3d_completion(prompt_id)
                
            except Exception as e:
                self.logger.error(f"Failed to process {image_obj.name}: {e}")
                # Continue with next image
        
    except ConnectionError as e:
        QMessageBox.critical(self, "Connection Error", str(e))
    except ValueError as e:
        QMessageBox.warning(self, "Invalid Input", str(e))
    except Exception as e:
        self.logger.exception("Unexpected error in 3D generation")
        QMessageBox.critical(self, "Error", f"3D generation failed: {e}")
    finally:
        # Restore UI state
        self.generate_3d_btn.setText("GENERATE 3D MODELS")
        self.generate_3d_btn.setEnabled(True)
```

---

## Key Patterns to Follow

1. **Always use the dynamic widget system** - Don't hardcode UI for specific workflows
2. **Monitor via ComfyUI history API** - More reliable than file watching
3. **Convert custom nodes automatically** - Ensure compatibility
4. **Preserve cross-tab selection** - Use unified object selector
5. **Handle errors gracefully** - Show user-friendly messages
6. **Update UI state during operations** - Disable buttons, show progress
7. **Clean up resources** - Stop timers, close viewers when done

---

## Testing Checklist for Tab 2

- [ ] Configure 3D parameters loads workflow correctly
- [ ] Dynamic UI creates widgets for all node types
- [ ] Selected images from Tab 1 appear in Tab 2
- [ ] LoadImage node receives correct image path
- [ ] Workflow executes for each selected image
- [ ] 3D models are detected when generated
- [ ] Viewer loads and displays models
- [ ] Selection system updates with new models
- [ ] Error handling works for all failure cases
- [ ] UI remains responsive during generation

---

This guide provides everything needed to implement Tab 2 using the proven patterns from Tab 1. The key is to reuse the dynamic UI system while adapting it for 3D-specific requirements like image injection and model viewing.