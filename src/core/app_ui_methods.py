"""
Complete UI Methods for Redesigned Application
All missing UI creation methods and parameter panels
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, 
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QSlider, QGroupBox, QListWidget, QTextEdit,
    QFrame, QSplitter, QLineEdit, QDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from pathlib import Path
from loguru import logger
import json
from typing import Dict, Any, Optional

# Import the actual grid widgets
from src.ui.widgets import ImageGridWidget


class UICreationMethods:
    """Mixin class containing all UI creation methods"""
    
    def _create_new_canvas_view(self) -> QWidget:
        """Create New Canvas view for image generation using ImageGridWidget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("New Canvas")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Removed "Ready for image generation" label as requested
        
        layout.addLayout(header_layout)
        
        # Preview grid for batch placeholders (before generation) - with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        preview_container = QWidget()
        self.new_canvas_grid = QGridLayout(preview_container)
        self.new_canvas_grid.setSpacing(15)
        self.new_canvas_grid.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(preview_container)
        # Make scroll area take all available space
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(scroll_area, 1)  # Stretch factor 1 to fill space
        
        # Store scroll area reference for dynamic sizing
        self.preview_scroll_area = scroll_area
        
        # Use actual ImageGridWidget for session images (after generation)
        # Hidden by default - we use the scroll area above instead
        # Reduced thumbnail size from 512 to 320 for better fit and less scrolling
        self.session_image_grid = ImageGridWidget(columns=3, thumbnail_size=320)
        self.session_image_grid.image_selected.connect(self._on_image_selected)
        self.session_image_grid.hide()  # Hide this - we use the scroll area above
        layout.addWidget(self.session_image_grid)
        
        return widget
        
    def _create_view_all_images(self) -> QWidget:
        """Create View All images view using ImageGridWidget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Removed header section to save vertical space for image grid
        
        # Use actual ImageGridWidget for all images
        # Optimized for better responsive behavior across screen sizes
        self.all_images_grid = ImageGridWidget(columns=5, thumbnail_size=200)
        self.all_images_grid.image_selected.connect(self._on_image_selected)
        layout.addWidget(self.all_images_grid)
        
        # Debug: Check if grid was created
        if hasattr(self, 'logger'):
            self.logger.info("Created all_images_grid successfully")
        
        return widget
        
    def _create_scene_objects_view(self) -> QWidget:
        """Create Scene Objects view for 3D models using ResponsiveStudio3DGrid"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Match Tab 1 layout - minimal margins for full space usage
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Clean scene objects view - no header controls (moved to right panel)
        
        # Use new ResponsiveStudio3DGrid for session models
        from src.ui.studio_3d_viewer_widget import ResponsiveStudio3DGrid
        # Get accent color from config
        accent_color = getattr(self.config.ui, 'accent_color', '#4CAF50')
        # Large 1024px cards - use single column due to size
        self.session_models_grid = ResponsiveStudio3DGrid(columns=1, card_size=1024, accent_color=accent_color)
        self.session_models_grid.model_selected.connect(self._on_model_selected)
        self.session_models_grid.model_clicked.connect(self._on_model_clicked)
        self.session_models_grid.models_changed.connect(self._on_scene_models_changed)
        
        # Add the grid directly to layout for full space usage
        layout.addWidget(self.session_models_grid)
        
        return widget
        
    def _create_view_all_models(self) -> QWidget:
        """Create View All models view using ResponsiveStudio3DGrid - same as Scene Objects"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Match Scene Objects layout - minimal margins for full space usage
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Removed header section to save vertical space for 3D viewer
        
        # Use ResponsiveStudio3DGrid - same as Scene Objects
        from src.ui.studio_3d_viewer_widget import ResponsiveStudio3DGrid
        # Get accent color from config
        accent_color = getattr(self.config.ui, 'accent_color', '#4CAF50')
        # Large 1024px cards - use single column due to size
        self.all_models_grid = ResponsiveStudio3DGrid(columns=1, card_size=1024, accent_color=accent_color)
        self.all_models_grid.model_selected.connect(self._on_model_selected)
        self.all_models_grid.model_clicked.connect(self._on_model_clicked)
        self.all_models_grid.models_changed.connect(self._on_all_models_changed)
        
        # Add the grid directly to layout for full space usage
        layout.addWidget(self.all_models_grid)
        
        return widget
        
    def _create_image_parameters(self) -> QWidget:
        """Create image generation parameters - SIMPLIFIED like texture tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Workflow Parameters section - NO SCROLL AREA, direct widget addition like texture tab
        dynamic_section = self._create_parameter_section("Workflow Parameters", compact=True)
        dynamic_section_layout = dynamic_section.layout()
        
        # Store dynamic layout reference for parameter addition (direct like texture tab)
        self.dynamic_params_layout = dynamic_section_layout
        self.dynamic_params_container = dynamic_section  # Add missing container reference
        
        # Info label when no parameters loaded - directly added like texture tab
        info_label = QLabel("Configure workflow parameters from File menu")
        info_label.setObjectName("info_label")
        info_label.setWordWrap(True)
        self.dynamic_params_layout.addWidget(info_label)
        
        # Add the dynamic section directly - NO scroll area wrapper
        layout.addWidget(dynamic_section)
        
        # Critical: Add stretch to push content to top like texture tab
        layout.addStretch()
        
        return widget
        
    def _create_3d_parameters(self) -> QWidget:
        """Create 3D generation parameters - static by default, dynamic when configuration exists"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Store reference to allow lazy loading
        self._3d_params_widget = widget
        self._3d_params_layout = layout
        
        # Start with static parameters (no performance hit)
        self._create_static_3d_parameters(layout)
        
        return widget
    
    def _create_static_3d_parameters(self, layout: QVBoxLayout):
        """Create the static 3D parameters (always available)"""
        
        # DYNAMIC WORKFLOW PARAMETERS SECTION - Same as image tab
        dynamic_section = self._create_parameter_section("Workflow Parameters", compact=True) 
        dynamic_section_layout = dynamic_section.layout()
        
        # Store dynamic layout reference for unified parameter system
        self._3d_dynamic_params_layout = dynamic_section_layout
        self._3d_dynamic_params_container = dynamic_section
        
        # Info label when no parameters loaded
        info_label = QLabel("Configure 3D workflow parameters from File menu")
        info_label.setObjectName("info_label")
        info_label.setWordWrap(True)
        self._3d_dynamic_params_layout.addWidget(info_label)
        
        # Add the dynamic section
        layout.addWidget(dynamic_section)
        
        
        # Critical: Add stretch to push content to top like texture tab (prevents height expansion)
        layout.addStretch()
    
    def _load_dynamic_3d_parameters_on_demand(self):
        """Load dynamic 3D parameters when Tab 2 is accessed - LAZY LOADING"""
        if not hasattr(self, '_3d_params_widget') or not hasattr(self, '_3d_params_layout'):
            self.logger.warning("3D parameters widget not initialized for dynamic loading")
            return
            
        try:
            # Check if configuration exists
            from pathlib import Path
            config_path = Path("config/3d_parameters_config.json")
            if not config_path.exists():
                self.logger.info("No 3D configuration found, keeping static parameters")
                return
                
            # Load and apply dynamic configuration
            dynamic_section = self._create_dynamic_3d_parameters_section()
            if dynamic_section:
                # Clear existing widgets except the stretch
                layout = self._3d_params_layout
                while layout.count() > 0:
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                # Add dynamic parameters
                layout.addWidget(dynamic_section)
                # REMOVED addStretch() - was causing UI height expansion
                
                self.logger.debug("Loaded dynamic 3D parameters on demand")
            else:
                self.logger.info("Failed to create dynamic 3D parameters, keeping static")
                
        except Exception as e:
            self.logger.error(f"Error loading dynamic 3D parameters: {e}")
    
    def _create_dynamic_3d_parameters_section(self) -> QWidget:
        """Create the dynamic parameters section only (for on-demand loading)"""
        from pathlib import Path
        import json
        
        config_path = Path("config/3d_parameters_config.json")
        if not config_path.exists():
            return None
            
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        selected_nodes = config.get("selected_nodes", [])
        node_info = config.get("node_info", {})
        
        if not selected_nodes:
            return None
            
        # Create dynamic widget with smart scroll area for many parameters
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for parameters to prevent app height expansion
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set reasonable height limits to prevent app expansion
        scroll_area.setMinimumHeight(200)  # Minimum usable height
        scroll_area.setMaximumHeight(600)  # Prevent excessive height expansion
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Create container for parameters inside scroll area
        params_container = QWidget()
        layout = QVBoxLayout(params_container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Set scroll area content
        scroll_area.setWidget(params_container)
        main_layout.addWidget(scroll_area)
        
        # Store widget references for value collection
        if not hasattr(self, 'dynamic_3d_widgets'):
            self.dynamic_3d_widgets = {}
        self.dynamic_3d_widgets.clear()
        
        # Workflow selector is now in the left panel controls - no duplicate here
        
        # Create parameter sections grouped by node type
        node_types = {}
        for node_key in selected_nodes:
            if node_key in node_info:
                info = node_info[node_key]
                node_type = info.get('type', 'Unknown')
                if node_type not in node_types:
                    node_types[node_type] = []
                node_types[node_type].append((node_key, info))
        
        # Create sections for each node type, but only for nodes with meaningful parameters
        sections_created = 0
        for node_type, nodes in node_types.items():
            # Check if any nodes in this type have meaningful parameters
            has_meaningful_params = False
            nodes_with_params = []
            
            for node_key, info in nodes:
                widgets_values = info.get('widgets_values', [])
                # Include nodes that have ANY parameter values (including defaults/empty)
                meaningful_params = []
                if widgets_values:
                    for value in widgets_values:
                        # Only skip None values, include everything else (empty strings, 0, false, etc.)
                        if value is not None:
                            meaningful_params.append(value)
                
                if meaningful_params:
                    has_meaningful_params = True
                    nodes_with_params.append((node_key, info, meaningful_params))
            
            # Only create section if there are nodes with meaningful parameters
            if has_meaningful_params:
                section = self._create_parameter_section(f"{node_type} Parameters", compact=True)
                section_layout = section.layout()
                
                for node_key, info, meaningful_params in nodes_with_params:
                    node_id = info.get('id', '')
                    node_title = info.get('title', '')
                    widgets_values = info.get('widgets_values', [])
                    
                    self.logger.debug(f"Node {node_key}: widgets_values = {widgets_values}")
                    
                    # Create label for this specific node instance
                    display_name = f"Node {node_id}"
                    if node_title:
                        display_name += f" ({node_title})"
                        
                    node_label = QLabel(display_name + ":")
                    node_label.setObjectName("section_subtitle")
                    section_layout.addWidget(node_label)
                    
                    # Create widgets for ALL parameters including defaults (FIXED: Show default values)
                    param_count = 0
                    for i, value in enumerate(widgets_values):
                        # Create widgets for ALL parameters including defaults
                        # Only skip truly undefined values (None), but show empty strings, numbers, etc.
                        if value is None:
                            continue
                            
                        widget_key = f"{node_key}_widget_{i}"
                        # Get meaningful parameter name based on node type and index
                        param_name = self._get_parameter_name(info.get('type', ''), i, value)
                        param_label, param_widget = self._create_parameter_widget(param_name, value, f"{node_key}_param_{i}")
                        
                        if param_label and param_widget:
                            # Add both label and widget directly to layout like texture tab
                            section_layout.addWidget(param_label)
                            section_layout.addWidget(param_widget)
                            self.dynamic_3d_widgets[widget_key] = param_widget  # Store widget for value collection
                            param_count += 1
                    
                    # If no meaningful parameters were created, show a note
                    if param_count == 0:
                        info_label = QLabel(f"Node configured (no user parameters)")
                        info_label.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
                        section_layout.addWidget(info_label)
                
                layout.addWidget(section)
                sections_created += 1
        
        # If no sections were created, show a message
        if sections_created == 0:
            info_section = self._create_parameter_section("Workflow Information", compact=True)
            info_layout = info_section.layout()
            info_label = QLabel("This workflow has no user-configurable parameters.\nAll nodes are using their default settings.")
            info_label.setStyleSheet("color: #888888; font-style: italic; text-align: center;")
            info_label.setWordWrap(True)
            info_layout.addWidget(info_label)
            layout.addWidget(info_section)
        
        # Add stretch to push parameters to top within scroll area
        layout.addStretch()
        
        self.logger.debug(f"Created dynamic 3D parameters section for {len(selected_nodes)} configured nodes")
        return widget
    
    def _get_parameter_name(self, node_type: str, param_index: int, value) -> str:
        """Get meaningful parameter name based on node type and parameter index"""
        # Parameter name mappings for common ComfyUI node types
        parameter_mappings = {
            "Hy3DPostprocessMesh": {
                0: "Optimization Level",
                1: "Simplification Ratio", 
                2: "Texture Resolution",
                3: "Normal Smoothing",
                4: "UV Unwrap Method"
            },
            "Hy3DGenerateMesh": {
                0: "Mesh Quality",
                1: "Subdivision Level",
                2: "Detail Enhancement",
                3: "Surface Smoothing",
                4: "Topology Mode"
            },
            "Hy3DVAEDecode": {
                0: "Decode Mode",
                1: "Quality Setting",
                2: "Color Space",
                3: "Gamma Correction",
                4: "Output Format"
            },
            "ImageResize+": {
                0: "Width",
                1: "Height", 
                2: "Interpolation Method",
                3: "Maintain Aspect Ratio",
                4: "Crop Mode"
            },
            "TransparentBGSession+": {
                0: "Background Mode",
                1: "Alpha Threshold",
                2: "Edge Softness",
                3: "Color Keying",
                4: "Anti-aliasing"
            },
            "DownloadAndLoadHy3DDelightModel": {
                0: "Model Version"
            },
            "Preview3D": {
                0: "View Mode",
                1: "Lighting Setup",
                2: "Material Display",
                3: "Camera Angle",
                4: "Background"
            },
            "KSampler": {
                0: "Seed",
                1: "Steps",
                2: "CFG Scale",
                3: "Sampler Name",
                4: "Scheduler"
            },
            "EmptyLatentImage": {
                0: "Width",
                1: "Height",
                2: "Batch Size"
            },
            "Hy3DSetMeshPBRTextures": {
                0: "Base Color Map",
                1: "Normal Map",
                2: "Roughness Map",
                3: "Metallic Map",
                4: "Height Map"
            },
            "Hy3DSampleMultiView": {
                0: "View Count",
                1: "Angle Step",
                2: "Camera Distance",
                3: "Lighting Mode",
                4: "Resolution"
            },
            "Hy3DRenderMultiView": {
                0: "Render Quality",
                1: "Output Format",
                2: "Background Type",
                3: "Shading Mode",
                4: "Anti-aliasing"
            },
            "ControlNetApplyAdvanced": {
                0: "Strength",
                1: "Start Percent",
                2: "End Percent",
                3: "Control Mode",
                4: "Guidance Scale"
            },
            "UltimateSDUpscale": {
                0: "Upscale Factor",
                1: "Tile Size",
                2: "Mask Blur",
                3: "Seam Fix Mode",
                4: "Denoise Strength"
            },
            "CheckpointLoaderSimple": {
                0: "Model Name"
            },
            "CLIPTextEncode": {
                0: "Text Prompt"
            }
        }
        
        # Try to get specific parameter name for this node type and index
        if node_type in parameter_mappings:
            param_names = parameter_mappings[node_type]
            if param_index in param_names:
                return param_names[param_index]
        
        # For unknown node types, try to infer from value type
        if isinstance(value, bool):
            return f"Enable/Disable Option {param_index}"
        elif isinstance(value, (int, float)) and value >= 0 and value <= 1:
            return f"Scale Factor {param_index}"
        elif isinstance(value, (int, float)) and value > 1:
            return f"Size/Count {param_index}"
        elif isinstance(value, str):
            if value in ["fixed", "random", "auto"]:
                return f"Mode Setting {param_index}"
            elif "." in value or "/" in value:
                return f"File/Path {param_index}"
            else:
                return f"Text Setting {param_index}"
        
        # Fallback to generic name
        return f"Parameter {param_index}"
    
    def _create_parameter_widget(self, label: str, value, param_name: str = None) -> tuple:
        """Create parameter widgets (label, input) for direct addition to layout like texture tab"""
        from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QCheckBox
        
        # Create label exactly like texture parameters - NO container wrapper
        param_label = QLabel(f"{label}:")
        param_label.setObjectName("section_title")  # Match texture parameter styling
        param_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Fixed sizing
        
        # Create appropriate input widget based on value type
        if isinstance(value, bool):
            input_widget = QCheckBox()
            input_widget.setChecked(value)
        elif isinstance(value, int):
            input_widget = QSpinBox()
            input_widget.setRange(-999999, 999999)
            input_widget.setValue(value)
        elif isinstance(value, float):
            input_widget = QDoubleSpinBox()
            input_widget.setRange(-999999.0, 999999.0)
            input_widget.setDecimals(3)
            input_widget.setValue(value)
        elif isinstance(value, str):
            # Enhanced dropdown detection with ComfyUI model scanning
            dropdown_options = self._get_dropdown_options_for_parameter(label, value)
            
            if dropdown_options:
                input_widget = QComboBox()
                input_widget.addItems(dropdown_options)
                # Set current value if it exists in options
                if value in dropdown_options:
                    input_widget.setCurrentText(value)
                else:
                    # Add current value as first option if not found
                    input_widget.insertItem(0, value)
                    input_widget.setCurrentIndex(0)
            else:
                input_widget = QLineEdit()
                input_widget.setText(str(value))
        else:
            # Fallback to string input
            input_widget = QLineEdit()
            input_widget.setText(str(value))
        
        # Set fixed sizing policy to prevent expansion like texture tab
        input_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Set responsive width to use full available right panel space
        # Remove fixed max width constraints to allow responsive sizing
        # input_widget.setMaximumWidth(max_widget_width)  # REMOVED: Allow full width
        
        # Labels can have reasonable max width for readability
        param_label.setMaximumWidth(400)  # Reasonable label width for readability
        
        # Store reference for value retrieval
        input_widget.get_value = lambda: self._get_widget_value(input_widget)
        
        # Return both widgets for direct addition to layout (NO container wrapper)
        return param_label, input_widget
    
    def _get_dropdown_options_for_parameter(self, label: str, current_value: str) -> list:
        """Get dropdown options for parameter based on label and current value"""
        from pathlib import Path
        
        # Normalize label for detection
        label_lower = label.lower()
        value_lower = current_value.lower() if current_value else ""
        
        # Common static options for non-model parameters
        static_options = {
            "scheduler": ["FlowMatchEulerDiscreteScheduler", "DPMSolverMultistepScheduler", "EulerDiscreteScheduler", "LMSDiscreteScheduler"],
            "sampler": ["euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde", "dpmpp_2m", "ddim", "uni_pc"],
            "quality": ["low", "medium", "high", "ultra"],
            "format": ["glb", "obj", "ply", "stl"],
            "upscale_method": ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"],
            "mode": ["RGB", "RGBA", "L"],
        }
        
        # Check for static options first
        for option_type, options in static_options.items():
            if option_type in label_lower or any(opt.lower() == value_lower for opt in options):
                return options
        
        # ComfyUI models directory scanning
        comfyui_models_dir = None
        
        # Try to find ComfyUI models directory
        possible_paths = [
            Path("ComfyUI/models"),
            Path("../ComfyUI/models"),
            Path("../../ComfyUI/models"),
            Path.home() / "ComfyUI/models",
            Path("D:/Comfy3D_WinPortable/ComfyUI/models"),  # Common Windows path
            Path("/opt/ComfyUI/models"),  # Common Linux path
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                comfyui_models_dir = path
                break
        
        if not comfyui_models_dir:
            return []
        
        # Model type detection based on parameter name and current value
        model_keywords = {
            "checkpoints": ["checkpoint", "model", "ckpt"],
            "loras": ["lora", "lora_name"],
            "vae": ["vae", "vae_name"],
            "controlnet": ["controlnet", "control"],
            "upscale_models": ["upscale", "upscaler"],
            "embeddings": ["embedding", "textual_inversion"],
            "clip": ["clip"],
            "clip_vision": ["clip_vision"],
            "unet": ["unet"],
            "diffusers": ["diffuser"],
            "style_models": ["style"],
            "hypernetworks": ["hypernetwork"],
            "gligen": ["gligen"],
        }
        
        # Find matching model directory
        detected_model_type = None
        for model_type, keywords in model_keywords.items():
            if any(keyword in label_lower for keyword in keywords):
                detected_model_type = model_type
                break
        
        # Also check current value for model type hints
        if not detected_model_type and current_value:
            for model_type, keywords in model_keywords.items():
                if any(keyword in value_lower for keyword in keywords):
                    detected_model_type = model_type
                    break
        
        if not detected_model_type:
            return []
        
        # Scan the specific model directory
        model_dir = comfyui_models_dir / detected_model_type
        if not model_dir.exists():
            return []
        
        try:
            # Get all model files (common extensions)
            model_extensions = [".ckpt", ".safetensors", ".bin", ".pt", ".pth", ".onnx"]
            model_files = []
            
            for ext in model_extensions:
                model_files.extend(model_dir.glob(f"*{ext}"))
                # Also check subdirectories
                model_files.extend(model_dir.glob(f"*/*{ext}"))
            
            # Convert to relative paths from model directory
            options = []
            for model_file in sorted(model_files):
                # Get relative path from model directory
                relative_path = model_file.relative_to(model_dir)
                options.append(str(relative_path))
            
            # Limit to reasonable number to prevent UI slowdown
            if len(options) > 100:
                options = options[:100]
                options.append("... (more models available)")
            
            return options
            
        except Exception as e:
            self.logger.warning(f"Failed to scan model directory {model_dir}: {e}")
            return []
    
    def _get_widget_value(self, widget):
        """Get value from a widget regardless of type"""
        from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QCheckBox
        
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        elif isinstance(widget, QLineEdit):
            text = widget.text()
            # Try to convert to appropriate type
            try:
                if '.' in text:
                    return float(text)
                else:
                    return int(text)
            except ValueError:
                return text
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        else:
            return str(widget.text()) if hasattr(widget, 'text') else None
    
    def _collect_dynamic_3d_workflow_parameters(self) -> dict:
        """Collect parameters from dynamic 3D widgets"""
        params = {}
        
        # Collect from dynamic widgets if they exist
        if hasattr(self, 'dynamic_3d_widgets'):
            for widget_key, widget in self.dynamic_3d_widgets.items():
                try:
                    if hasattr(widget, 'get_value'):
                        value = widget.get_value()
                        params[widget_key] = value
                        self.logger.debug(f"Collected {widget_key}: {value}")
                except Exception as e:
                    self.logger.warning(f"Failed to collect value from {widget_key}: {e}")
        
        # Also collect from static widgets if they exist (fallback)
        static_mappings = {
            'guidance_scale_3d': 'guidance_3d_spin',
            'inference_steps_3d': 'steps_3d_spin',
            'seed_3d': 'seed_3d_spin',
            'mesh_density': 'density_spin',
            'quality_3d': 'quality_3d_combo',
            'workflow_3d': 'workflow_3d_combo'
        }
        
        for param_name, widget_name in static_mappings.items():
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                try:
                    # Check if widget is still valid before accessing
                    if hasattr(widget, 'isValid') and not widget.isValid():
                        continue
                    value = self._get_widget_value(widget)
                    params[param_name] = value
                    self.logger.debug(f"Collected static {param_name}: {value}")
                except Exception as e:
                    self.logger.debug(f"Skipping invalid widget {widget_name}: {e}")  # Changed to debug level
        
        self.logger.info(f"Collected {len(params)} parameters from 3D UI")
        return params
    
    def _regenerate_config_with_widgets_values(self, workflow_file: str, param_type: str):
        """Regenerate configuration to include widgets_values from workflow"""
        try:
            self.logger.info(f"Regenerating config for {workflow_file} to include widgets_values")
            
            # Import the workflow change method from main app
            if hasattr(self, '_on_workflow_changed'):
                # Trigger workflow change which will regenerate the config
                self._on_workflow_changed(workflow_file)
            else:
                self.logger.error("_on_workflow_changed method not found - config regeneration failed")
                
        except Exception as e:
            self.logger.error(f"Failed to regenerate config: {e}")
            # Fallback - try to load parameters anyway
            self._load_parameters_from_config(param_type)
    
    def force_regenerate_all_configs(self):
        """Force regenerate all parameter configs to include widgets_values"""
        try:
            # Force regenerate image config
            if hasattr(self, 'workflow_combo') and self.workflow_combo.count() > 0:
                current_workflow = self.workflow_combo.currentData()
                if current_workflow:
                    self.logger.info(f"Force regenerating image config for: {current_workflow}")
                    self._on_workflow_changed(current_workflow)
            
            # Force regenerate 3D config
            if hasattr(self, 'workflow_3d_combo') and self.workflow_3d_combo.count() > 0:
                current_3d_workflow = self.workflow_3d_combo.currentData() or self.workflow_3d_combo.currentText()
                if current_3d_workflow:
                    self.logger.info(f"Force regenerating 3D config for: {current_3d_workflow}")
                    self._on_workflow_changed(current_3d_workflow)
            
            # Force regenerate texture config
            if hasattr(self, 'workflow_texture_new_combo') and self.workflow_texture_new_combo.count() > 0:
                current_texture_workflow = self.workflow_texture_new_combo.currentData() or self.workflow_texture_new_combo.currentText()
                if current_texture_workflow:
                    self.logger.info(f"Force regenerating texture config for: {current_texture_workflow}")
                    self._on_workflow_texture_new_changed()
                    
        except Exception as e:
            self.logger.error(f"Failed to force regenerate configs: {e}")
    
    def _refresh_scene_objects(self):
        """Refresh scene objects - only session models"""
        try:
            # Scene Objects should only show models generated in current session
            # Just reload the session models
            if hasattr(self, '_load_session_models'):
                self.logger.info("Refreshing Scene Objects with session models...")
                self._load_session_models()
            else:
                self.logger.warning("_load_session_models method not available")
        except Exception as e:
            self.logger.error(f"Failed to refresh scene objects: {e}")
    
    def _load_test_models_on_startup(self):
        """Load existing models into View All tab on startup"""
        try:
            from pathlib import Path
            import os
            from datetime import datetime
            
            # This method should populate the View All tab, not Scene Objects
            # Scene Objects is for models generated in current session only
            
            # Just trigger the existing _load_all_models method
            if hasattr(self, '_load_all_models'):
                self.logger.info("Loading existing 3D models into View All tab...")
                self._load_all_models()
                return True
            else:
                self.logger.warning("_load_all_models method not available")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to load models on startup: {e}")
            return False
    
    def _refresh_3d_models(self):
        """Refresh only the session 3D models (models generated in current session)"""
        try:
            # This should only refresh the Scene Objects view with session models
            # Not scan the directory for all models
            
            if hasattr(self, '_load_session_models'):
                self.logger.info("Refreshing session 3D models (Scene Objects)...")
                self._load_session_models()
            else:
                self.logger.warning("_load_session_models method not available")
                
        except Exception as e:
            self.logger.error(f"Failed to refresh session 3D models: {e}")
                
    def _load_test_models_on_startup_old(self):
        """Old version kept for reference"""
        try:
            # This is the old method, keeping for reference
            pass
        except Exception as e:
            self.logger.error(f"Failed to load test models: {e}")
            return False
    
    def _clear_scene_objects(self):
        """Clear all scene objects (session models)"""
        try:
            if hasattr(self, 'session_models_grid'):
                self.session_models_grid.clear_models()
                # Also clear the session models list
                if hasattr(self, 'session_models'):
                    self.session_models.clear()
                self.logger.info("Cleared all scene objects (session models)")
        except Exception as e:
            self.logger.error(f"Failed to clear scene objects: {e}")
    
    def _on_model_clicked(self, model_path):
        """Handle model click events"""
        self.logger.info(f"Model clicked: {model_path.name}")
        # Could implement model info dialog or other actions here
    
    def _on_scene_models_changed(self, count):
        """Handle scene models count change"""
        self.logger.debug(f"Scene objects count changed: {count}")
    
    def _on_all_models_changed(self, count):
        """Handle all models count change"""
        self.logger.debug(f"All models count changed: {count}")
        
    def _create_texture_parameters(self) -> QWidget:
        """Create texture generation parameters"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Store reference to allow dynamic parameter injection
        self._texture_params_widget = widget
        self._texture_params_layout = layout
        
        
        # DYNAMIC WORKFLOW PARAMETERS SECTION - Same as image tab
        dynamic_section = self._create_parameter_section("Workflow Parameters", compact=True)
        dynamic_section_layout = dynamic_section.layout()
        
        # Store dynamic layout reference for unified parameter system
        self._texture_dynamic_params_layout = dynamic_section_layout
        self._texture_dynamic_params_container = dynamic_section
        
        # Info label when no parameters loaded
        info_label = QLabel("Configure texture workflow parameters from File menu")
        info_label.setObjectName("info_label")
        info_label.setWordWrap(True)
        self._texture_dynamic_params_layout.addWidget(info_label)
        
        # Add the dynamic section
        layout.addWidget(dynamic_section)
        
        layout.addStretch()
        
        return widget
        
    def _create_c4d_parameters(self) -> QWidget:
        """Create Cinema4D parameters"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Object Creation section
        creation_section = self._create_parameter_section("Object Creation")
        creation_layout = creation_section.layout()
        
        # Object type
        type_label = QLabel("Object Type:")
        type_label.setObjectName("section_title")
        self.object_type_combo = QComboBox()
        self.object_type_combo.addItems([
            "Primitive Objects",
            "Generator Objects",
            "Deformer Objects",
            "MoGraph Objects",
            "Light Objects",
            "Camera Objects"
        ])
        creation_layout.addWidget(type_label)
        creation_layout.addWidget(self.object_type_combo)
        
        # Quick create buttons
        quick_layout = QHBoxLayout()
        cube_btn = QPushButton("Cube")
        cube_btn.setObjectName("secondary_btn")
        sphere_btn = QPushButton("Sphere")
        sphere_btn.setObjectName("secondary_btn")
        quick_layout.addWidget(cube_btn)
        quick_layout.addWidget(sphere_btn)
        creation_layout.addLayout(quick_layout)
        
        layout.addWidget(creation_section)
        
        # Scene Management section
        scene_section = self._create_parameter_section("Scene Management")
        scene_layout = scene_section.layout()
        
        # Import/Export
        import_btn = QPushButton("Import to Cinema4D")
        import_btn.setObjectName("primary_btn")
        scene_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export Scene")
        export_btn.setObjectName("secondary_btn")
        scene_layout.addWidget(export_btn)
        
        layout.addWidget(scene_section)
        layout.addStretch()
        
        return widget
        
    def _create_parameter_section(self, title: str) -> QGroupBox:
        """Create a parameter section with consistent styling"""
        section = QGroupBox(title)
        section.setObjectName("sidebar_section")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)
        
        return section
        
    def _create_enhanced_menu_bar(self):
        """Create enhanced menu bar with all functionality"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_project_action = QAction("New Project", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self._new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction("Open Project", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)
        
        # Open Recent submenu
        from PySide6.QtWidgets import QMenu
        open_recent_menu = QMenu("Open Recent", self)
        
        # Add recent project placeholders (in real implementation, these would be loaded from settings)
        recent_projects = [
            "C:/Projects/SciFi_Environment.comfy",
            "C:/Projects/Character_Design.comfy",
            "C:/Projects/Architectural_Viz.comfy",
            "C:/Projects/Product_Showcase.comfy"
        ]
        
        for project_path in recent_projects:
            project_name = project_path.split("/")[-1]  # Get filename
            recent_action = QAction(project_name, self)
            recent_action.setData(project_path)  # Store full path in action data
            recent_action.triggered.connect(lambda checked, path=project_path: self._open_recent_project(path))
            open_recent_menu.addAction(recent_action)
        
        open_recent_menu.addSeparator()
        
        # Clear recent files action
        clear_recent_action = QAction("Clear Recent", self)
        clear_recent_action.triggered.connect(self._clear_recent_projects)
        open_recent_menu.addAction(clear_recent_action)
        
        file_menu.addMenu(open_recent_menu)
        
        save_project_action = QAction("Save Project", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self._save_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        # Configure Image Parameters action
        config_image_action = QAction("Configure Image Parameters", self)
        config_image_action.triggered.connect(self._show_configure_image_parameters_dialog)
        file_menu.addAction(config_image_action)
        
        # Configure 3D Generation Parameters action
        config_3d_action = QAction("Configure 3D Generation Parameters", self)
        config_3d_action.triggered.connect(self._show_configure_3d_parameters_dialog)
        file_menu.addAction(config_3d_action)
        
        # Configure 3D Texture Parameters action
        config_texture_action = QAction("Configure 3D Texture Parameters", self)
        config_texture_action.triggered.connect(self._show_configure_texture_parameters_dialog)
        file_menu.addAction(config_texture_action)
        
        file_menu.addSeparator()
        
        # Environment Variables action
        env_vars_action = QAction("Environment Variables", self)
        env_vars_action.triggered.connect(self._open_environment_variables)
        file_menu.addAction(env_vars_action)
        
        file_menu.addSeparator()
        
        # Magic Prompts Database action
        magic_prompts_action = QAction("Magic Prompts Database", self)
        magic_prompts_action.triggered.connect(self._show_magic_prompts_database)
        file_menu.addAction(magic_prompts_action)
        
        file_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._open_application_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self._open_preferences)
        edit_menu.addAction(preferences_action)
        
        # AI menu (moved from Tools)
        ai_menu = menubar.addMenu("AI")
        
        nlp_dict_action = QAction("NLP Dictionary", self)
        nlp_dict_action.triggered.connect(self._open_nlp_dictionary)
        ai_menu.addAction(nlp_dict_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        texture_viewer_action = QAction("Texture Viewer", self)
        texture_viewer_action.triggered.connect(self._launch_texture_viewer)
        tools_menu.addAction(texture_viewer_action)
        
        tools_menu.addSeparator()
        
        refresh_connections_action = QAction("Refresh Connections", self)
        refresh_connections_action.triggered.connect(self._refresh_all_connections)
        tools_menu.addAction(refresh_connections_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        console_action = QAction("Toggle Console", self)
        console_action.setCheckable(True)
        console_action.setChecked(True)
        console_action.triggered.connect(self._toggle_console)
        view_menu.addAction(console_action)
        
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        documentation_action = QAction("Documentation", self)
        documentation_action.triggered.connect(self._open_github_documentation)
        help_menu.addAction(documentation_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        
    # Event handler implementations
    def _randomize_seed(self):
        """Randomize seed value"""
        import random
        new_seed = random.randint(0, 2147483647)
        if hasattr(self, 'seed_spin'):
            self.seed_spin.setValue(new_seed)
        self.logger.info(f"Seed randomized to: {new_seed}")
        
    def _refresh_all_images(self):
        """Refresh all images display"""
        self.logger.info("Refreshing image gallery...")
        # Call the actual implementation from app_redesigned.py
        if hasattr(self, '_load_all_images'):
            self._load_all_images()
        else:
            self.logger.warning("_load_all_images method not found")
        
    def _refresh_all_models(self):
        """Refresh all models display"""
        self.logger.info("Refreshing 3D models...")
        # Call the actual implementation from app_redesigned.py
        if hasattr(self, '_load_all_models'):
            self._load_all_models()
        else:
            self.logger.warning("_load_all_models method not found")
        
    def _refresh_textured_models(self):
        """Refresh textured models from 3D/textured folder"""
        self.logger.info("Refreshing textured models...")
        
        # Monitor 3D/textured folder - use config computed property
        textured_path = self.config.textured_models_dir if hasattr(self.config, 'textured_models_dir') else Path(self.config.models_3d_dir) / "textured"
        if textured_path.exists():
            textured_files = list(textured_path.glob("*.obj"))
            self.logger.info(f"Found {len(textured_files)} textured models")
        else:
            self.logger.warning("Textured models folder not found")
            
    def _create_quick_object(self, object_type: str):
        """Create quick Cinema4D object"""
        self.logger.info(f"Creating {object_type} object in Cinema4D...")
        # Implement actual object creation
        
    def _open_nlp_dictionary(self):
        """Open NLP Dictionary dialog"""
        try:
            from src.ui.nlp_dictionary_dialog import NLPDictionaryDialog
            dialog = NLPDictionaryDialog(self, self.config)
            result = dialog.exec()
            if result:
                self.logger.info("NLP Dictionary dialog opened successfully")
        except Exception as e:
            self.logger.error(f"Failed to open NLP Dictionary: {e}")
            import traceback
            self.logger.error(f"NLP Dictionary error details: {traceback.format_exc()}")
    
    def _show_configure_image_parameters_dialog(self):
        """Show Configure Image Parameters dialog"""
        try:
            self.logger.info("🔄 Opening Configure Image Parameters dialog...")
            from src.ui.configure_parameters_dialog import ConfigureParametersDialog
            
            dialog = ConfigureParametersDialog("image", parent=self)
            
            # Connect the dialog's accepted signal to load parameters
            result = dialog.exec()
            self.logger.info(f"🔄 Dialog result: {result} (Accepted={dialog.Accepted})")
            
            if result == dialog.Accepted:
                self.logger.info("✅ Dialog accepted, starting parameter loading...")
                # After dialog is accepted, load the parameters
                self._load_parameters_from_config("image")
                
                self.logger.info("✅ Starting UI refresh...")
                # Refresh UI components after workflow import
                self._refresh_ui_after_workflow_import()
                
                self.logger.info("✅ Configure workflow complete!")
            else:
                self.logger.info("❌ Dialog cancelled or failed")
                
                
        except Exception as e:
            self.logger.error(f"Failed to open Configure Image Parameters dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_configure_3d_parameters_dialog(self):
        """Show Configure 3D Generation Parameters dialog"""
        try:
            self.logger.info("Opening Configure 3D Generation Parameters dialog...")
            # TODO: Import and show the actual dialog
            self._load_parameters_from_config("3d")
        except Exception as e:
            self.logger.error(f"Failed to open Configure 3D Generation Parameters dialog: {e}")
    
    def _show_configure_texture_parameters_dialog(self):
        """Show Configure 3D Texture Parameters dialog"""
        try:
            self.logger.info("Opening Configure 3D Texture Parameters dialog...")
            # TODO: Import and show the actual dialog
            self._load_parameters_from_config("texture")
        except Exception as e:
            self.logger.error(f"Failed to open Configure 3D Texture Parameters dialog: {e}")
    
    def _refresh_ui_after_workflow_import(self):
        """Refresh all UI components after workflow import"""
        try:
            self.logger.info("Refreshing UI after workflow import...")
            
            # Refresh image grids
            if hasattr(self, '_load_session_images'):
                self._load_session_images()
            if hasattr(self, '_load_all_images'):
                self._load_all_images()
            
            # Refresh model grids
            if hasattr(self, '_load_session_models'):
                self._load_session_models()
            if hasattr(self, '_load_all_models'):
                self._load_all_models()
            
            # Update selection displays
            if hasattr(self, '_update_selection_displays'):
                self._update_selection_displays()
            
            # Update object selection widget if it exists
            if hasattr(self, 'object_manager') and hasattr(self.object_manager, '_update_display'):
                self.object_manager._update_display()
            
            # Update unified object selector if it exists
            if hasattr(self, 'unified_object_selector') and hasattr(self.unified_object_selector, '_update_display'):
                self.unified_object_selector._update_display()
                
            self.logger.info("UI refresh completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error refreshing UI after workflow import: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Configuration file mapping for all parameter types
    _CONFIG_FILE_MAP = {
        "image": "config/image_parameters_config.json",
        "3d_parameters": "config/3d_parameters_config.json",
        "texture_parameters": "config/texture_parameters_config.json"
    }

    def _load_parameters_unified(self, param_type: str, force_workflow_path: Optional[Path] = None):
        """Load parameters using the unified configuration system
        
        This method handles both dropdown-triggered workflow changes and startup loading.
        When force_workflow_path is provided, it bypasses the saved configuration
        and loads parameters directly from the specified workflow file.
        
        Args:
            param_type: Type of parameters (image, 3d_parameters, texture_parameters)
            force_workflow_path: If provided, use this workflow instead of loading from config.
                                This is used when user selects a workflow from dropdown.
        
        Workflow:
            1. If force_workflow_path is provided (dropdown selection):
               - Load workflow configuration directly from specified file
               - Update UI parameters from the new workflow
               - Update prompt memory with new workflow path
            2. If no force path (normal startup):
               - Load workflow path from saved configuration file
               - Proceed with normal parameter loading
        
        Raises:
            Exception: If workflow loading or parameter update fails
        """
        try:
            self.logger.debug(f"🔧 Loading parameters for {param_type} using unified system")
            self.logger.info(f"🔧 Force workflow path: {force_workflow_path}")
            self.logger.info(f"🔧 Config integration available: {hasattr(self, 'config_integration')}")
            
            if force_workflow_path and force_workflow_path.exists():
                # CASE 1: Dropdown selection - use specified workflow directly
                self.logger.info(f"🎯 Using forced workflow path: {force_workflow_path}")
                self._load_workflow_parameters_direct(param_type, force_workflow_path)
                
            else:
                # CASE 2: Normal loading - use saved configuration
                self.logger.info(f"📂 Loading from saved configuration for {param_type}")
                self._load_workflow_parameters_from_config(param_type)
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to load parameters through unified system: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def _load_workflow_parameters_direct(self, param_type: str, workflow_file: Path):
        """Load parameters directly from a workflow file (used for dropdown changes)
        
        Args:
            param_type: Type of parameters (image, 3d_parameters, texture_parameters)
            workflow_file: Path to the workflow file to load
        """
        self.logger.info(f"🔄 Loading workflow parameters directly from {workflow_file.name}")
        
        # Load through unified manager to get organized parameters
        params = self.config_integration.config_manager.load_workflow_configuration(workflow_file)
        
        # Update UI with unified parameters
        self._update_unified_parameter_ui(param_type, params)
        
        # Update prompt memory with new workflow path
        self._update_prompt_memory_for_workflow(param_type, workflow_file)

    def _load_workflow_parameters_from_config(self, param_type: str):
        """Load parameters from saved configuration file (used for startup)
        
        Args:
            param_type: Type of parameters (image, 3d_parameters, texture_parameters)
        """
        config_path = Path(self._CONFIG_FILE_MAP.get(param_type, ""))
        if not config_path.exists():
            self.logger.warning(f"⚠️ Configuration file not found: {config_path}")
            return
        
        # Load workflow through unified configuration manager
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Try workflow_path first, then fallback to workflow_file
        workflow_path = config.get('workflow_path')
        workflow_file_name = config.get('workflow_file')
        
        if workflow_path:
            # Use full path if available
            workflow_file = Path(workflow_path)
        elif workflow_file_name and param_type:
            # Construct path from workflow_file and param_type
            workflow_type_map = {
                "image": "image_generation",
                "3d_parameters": "3d_generation", 
                "texture_parameters": "texture_generation"
            }
            workflow_type = workflow_type_map.get(param_type, "image_generation")
            workflow_file = Path("workflows") / workflow_type / workflow_file_name
            self.logger.info(f"🔨 Constructed workflow path: {workflow_file}")
        else:
            workflow_file = None
        
        if workflow_file and workflow_file.exists():
            self.logger.info(f"📁 Loading workflow from config: {workflow_file.name}")
            
            # Load through unified manager to get organized parameters
            params = self.config_integration.config_manager.load_workflow_configuration(workflow_file)
            
            # Update UI with unified parameters
            self._update_unified_parameter_ui(param_type, params)
            
            # Handle prompt memory
            self._update_prompt_memory(config)
        elif workflow_file:
            self.logger.warning(f"⚠️ Workflow file not found: {workflow_file}")
        else:
            self.logger.warning(f"⚠️ No workflow path or file found in config for {param_type}")

    def _update_prompt_memory_for_workflow(self, param_type: str, workflow_file: Path):
        """Update prompt memory with new workflow path (used for dropdown changes)
        
        Args:
            param_type: Type of parameters (image, 3d_parameters, texture_parameters)
            workflow_file: Path to the workflow file
        """
        try:
            config_path = Path(self._CONFIG_FILE_MAP.get(param_type, ""))
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Override with new workflow path
                config['workflow_path'] = str(workflow_file.absolute())
                self._update_prompt_memory(config)
                self.logger.debug(f"✅ Updated prompt memory for {param_type} with workflow {workflow_file.name}")
            else:
                self.logger.warning(f"⚠️ Could not update prompt memory - config file not found: {config_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to update prompt memory: {e}")

    def _get_target_layout_for_param_type(self, param_type: str):
        """Get the appropriate layout for the given parameter type"""
        try:
            if param_type == "image":
                # Image tab uses dynamic_params_layout
                if hasattr(self, 'dynamic_params_layout'):
                    return self.dynamic_params_layout
                else:
                    self.logger.warning("Image tab dynamic_params_layout not found")
                    return None
                    
            elif param_type == "3d_parameters":
                # 3D tab uses dynamic params layout
                if hasattr(self, '_3d_dynamic_params_layout'):
                    return self._3d_dynamic_params_layout
                else:
                    self.logger.warning("3D tab dynamic layout not found")
                    return None
                    
            elif param_type == "texture_parameters":
                # Texture tab uses dynamic params layout
                if hasattr(self, '_texture_dynamic_params_layout'):
                    return self._texture_dynamic_params_layout
                else:
                    self.logger.warning("Texture tab dynamic layout not found")
                    return None
                    
            else:
                self.logger.warning(f"Unknown param_type: {param_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting target layout for {param_type}: {e}")
            return None

    def _clear_dynamic_parameters_for_layout(self, layout):
        """Clear dynamic parameters from a specific layout"""
        try:
            if not layout:
                self.logger.debug("No layout provided for clearing")
                return
            
            initial_count = layout.count()
            self.logger.debug(f"Clearing {initial_count} widgets from layout")
                
            # Remove all widgets from the layout
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    widget = item.widget()
                    widget_name = widget.__class__.__name__
                    object_name = getattr(widget, 'objectName', lambda: 'unknown')()
                    self.logger.debug(f"Removing widget: {widget_name} (objectName: {object_name})")
                    widget.setParent(None)
                    widget.deleteLater()
                    
            final_count = layout.count()
            self.logger.debug(f"Cleared layout: {initial_count} -> {final_count} widgets")
            
        except Exception as e:
            self.logger.error(f"Error clearing parameters from layout: {e}")
    
    def _update_unified_parameter_ui(self, param_type: str, params: Dict[str, Any]):
        """Update UI with parameters from unified configuration manager"""
        try:
            # Get the appropriate layout for the parameter type
            target_layout = self._get_target_layout_for_param_type(param_type)
            if not target_layout:
                self.logger.warning(f"No target layout found for param_type: {param_type}")
                return
            
            # Clear existing parameters for this tab
            self._clear_dynamic_parameters_for_layout(target_layout)
            
            # Get the unified configuration manager
            config_manager = self.config_integration.config_manager
            
            # Create parameter widgets organized by node type with proper priority
            self.logger.info(f"🔧 Creating UI for {len(params)} parameter groups")
            self.logger.debug(f"🔧 Parameters structure: {list(params.keys())}")
            for key, value in params.items():
                self.logger.debug(f"🔧 Group {key}: {key} with {len(value.get('parameters', {}))} parameters")
            for node_type, node_params in sorted(params.items(), 
                                              key=lambda x: config_manager.PARAMETER_PRIORITY.get(
                                                  x[0], 999)):
                
                node_id = node_params.get('node_id', node_type)
                self.logger.info(f"🎯 Processing node {node_type} (node_id: {node_id})")
                
                # Skip hidden node types
                if node_type in config_manager.HIDDEN_NODE_TYPES:
                    self.logger.info(f"⏭️ Skipping {node_type} - hidden node type")
                    continue
                
                # Check if parameters are ticked for display
                if not self._are_parameters_ticked(node_type, node_params):
                    self.logger.info(f"⏭️ Skipping {node_type} - parameters not ticked")
                    continue
                
                # Create section for this node with color coding
                section_color = self._get_node_color_from_settings(node_type)
                display_name = node_params.get('display_name', node_type)
                section_widget = self._create_colored_parameter_section(
                    f"{display_name} (#{node_id})", 
                    section_color
                )
                self.logger.debug(f"✅ Created section for {display_name} (#{node_id})")
                
                section_layout = section_widget.layout()
                param_count = 0
                
                # Add parameters for this node
                for param_name, param_info in node_params.get('parameters', {}).items():
                    if param_name in ['node_type', 'node_title']:
                        continue
                    
                    self.logger.debug(f"🎯 Creating widget for {param_name}: {param_info}")
                    # Create parameter widget
                    param_widget = self._create_unified_parameter_widget(
                        param_name, 
                        param_info, 
                        node_id
                    )
                    
                    if param_widget:
                        section_layout.addWidget(param_widget)
                        param_count += 1
                        self.logger.debug(f"✅ Added parameter widget: {param_name}")
                    else:
                        self.logger.error(f"❌ Failed to create widget for: {param_name}")
                
                self.logger.debug(f"✅ Added {param_count} parameter widgets to {display_name} (#{node_id})")
                # Add section to target layout
                target_layout.addWidget(section_widget)
            
            # Add stretch at the end
            target_layout.addStretch()
            
            # Force UI refresh to make widgets visible (critical for texture parameters)
            self._force_parameter_layout_refresh(param_type, target_layout)
            
            self.logger.info(f"Updated UI with {len(params)} parameter groups")
            
        except Exception as e:
            self.logger.error(f"Failed to update unified parameter UI: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _force_parameter_layout_refresh(self, param_type: str, target_layout):
        """Force UI refresh to make parameter widgets visible"""
        try:
            # Get the container widget for this parameter type
            container_widget = None
            if param_type == "image" and hasattr(self, 'dynamic_params_container'):
                container_widget = self.dynamic_params_container
            elif param_type == "3d_parameters" and hasattr(self, '_3d_dynamic_params_container'):
                container_widget = self._3d_dynamic_params_container
            elif param_type == "texture_parameters" and hasattr(self, '_texture_dynamic_params_container'):
                container_widget = self._texture_dynamic_params_container
            
            if container_widget:
                # Force immediate layout update and repaint
                container_widget.updateGeometry()
                container_widget.repaint()
                container_widget.update()
                
                # Also ensure the container is visible
                container_widget.setVisible(True)
                container_widget.show()
                
                self.logger.debug(f"✅ Forced UI refresh for {param_type} parameter container")
            else:
                self.logger.warning(f"⚠️ No container widget found for {param_type} - cannot force refresh")
                
            # Also force layout update and activation
            if target_layout:
                target_layout.update()
                target_layout.activate()
                
        except Exception as e:
            self.logger.error(f"Failed to force parameter layout refresh: {e}")
    
    def _are_parameters_ticked(self, node_id: str, node_params: Dict[str, Any]) -> bool:
        """Check if parameters for this node should be displayed"""
        # For now, display all parameters that aren't hidden
        # TODO: Implement actual ticked parameter tracking
        return True
    
    def _get_node_color_from_settings(self, node_type: str) -> str:
        """Get the color for a node type from current settings"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            workflow_colors = settings.value("interface/workflow_colors", [
                "#4CAF50", "#2196F3", "#9C27B0", "#FF9800", "#00BCD4"
            ])
            
            # Ensure we have 5 colors
            if not workflow_colors or len(workflow_colors) < 5:
                workflow_colors = ["#4CAF50", "#2196F3", "#9C27B0", "#FF9800", "#00BCD4"]
            
            # Map node types to color indices
            node_color_mapping = {
                # Primary sampling (Color 1 - Green)
                "KSampler": 0,
                "KSamplerAdvanced": 0,
                "Hy3DGenerateMesh": 0,
                
                # Model loading (Color 2 - Blue)
                "CheckpointLoader": 1, 
                "CheckpointLoaderSimple": 1,
                "UNETLoader": 1,
                "EmptyLatentImage": 1,
                "EmptySD3LatentImage": 1,
                "Hy3DModelLoader": 1,
                "Hy3DExportMesh": 1,
                
                # LoRA and ControlNet (Color 3 - Purple)
                "LoraLoader": 2,
                "ControlNetLoader": 2,
                "Hy3DPostprocessMesh": 2,
                
                # VAE and FluxGuidance (Color 4 - Orange)
                "VAELoader": 3,
                "FluxGuidance": 3,
                "Hy3DVAEDecode": 3,
                
                # Text encoding (Color 5 - Cyan)
                "CLIPTextEncode": 4,
                "QuadrupleCLIPLoader": 4,
            }
            
            # Get color index for this node type, default to 0
            color_index = node_color_mapping.get(node_type, 0)
            selected_color = workflow_colors[color_index]
            self.logger.debug(f"🎨 Node {node_type} -> Color {color_index+1}: {selected_color}")
            return selected_color
            
        except Exception as e:
            self.logger.debug(f"Failed to get node color from settings: {e}")
            return "#4CAF50"  # Default fallback
    
    def _create_colored_parameter_section(self, title: str, color: str = None) -> QGroupBox:
        """Create a parameter section with color-coded header"""
        # If no color provided, use default
        if not color:
            color = "#4CAF50"  # Simple fallback since color should be provided
        
        section = QGroupBox(title)
        section.setObjectName("colored_parameter_section")
        
        # Apply color to the section header
        section.setStyleSheet(f"""
            QGroupBox#colored_parameter_section {{
                border: 1px solid {color};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox#colored_parameter_section::title {{
                color: {color};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(8, 15, 8, 8)
        layout.setSpacing(6)
        
        return section
    
    def _create_unified_parameter_widget(self, param_name: str, param_info: Dict[str, Any], 
                                       node_id: str) -> Optional[QWidget]:
        """Create a widget for a unified parameter"""
        try:
            param_type = param_info.get('type', 'string')
            param_value = param_info.get('current_value', param_info.get('value'))  # Try current_value first, then value
            param_ui_name = param_info.get('ui_name', param_name)
            
            self.logger.info(f"🎯 Creating {param_type} widget for {param_ui_name} with value: {param_value}")
            
            # Create container
            container = QWidget()
            container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 2, 0, 2)
            layout.setSpacing(2)
            
            # Create label
            label = QLabel(f"{param_ui_name}:")
            label.setObjectName("section_title")
            layout.addWidget(label)
            
            # Create appropriate input widget
            if param_type == 'choice':
                # Support both 'choices' and 'options' keys
                choices = param_info.get('choices', param_info.get('options', []))
                
                # If no predefined choices, try to get ComfyUI model options
                if not choices:
                    # Always try to auto-populate choices, even if param_value is None
                    search_value = str(param_value) if param_value else param_ui_name.lower()
                    choices = self._get_dropdown_options_for_parameter(param_ui_name, search_value)
                    self.logger.info(f"🎯 Auto-populated choices for {param_ui_name}: {len(choices)} options")
                
                self.logger.info(f"🎯 Choice widget for {param_ui_name}: options={len(choices)} items, value={param_value}")
                input_widget = QComboBox()
                input_widget.addItems(choices)
                if param_value and str(param_value) in choices:
                    input_widget.setCurrentText(str(param_value))
                    self.logger.info(f"✅ Set choice widget to: {param_value}")
                else:
                    self.logger.warning(f"⚠️ Value '{param_value}' not in choices (showing {len(choices)} options)")
                    if param_value:  # Add the current value even if not in choices
                        input_widget.addItem(str(param_value))
                        input_widget.setCurrentText(str(param_value))
                        self.logger.debug(f"✅ Added and set current value: {param_value}")
            elif param_type == 'int':
                input_widget = QSpinBox()
                min_val = param_info.get('min', -999999)
                max_val = param_info.get('max', 999999)
                input_widget.setRange(min_val, max_val)
                
                # Safely handle large integer values (like seeds)
                if param_value is not None:
                    safe_value = int(param_value)
                    # Clamp to widget range if necessary
                    if safe_value > max_val:
                        safe_value = max_val
                        self.logger.debug(f"Clamped large value {param_value} to {max_val} for {param_name}")
                    elif safe_value < min_val:
                        safe_value = min_val
                        self.logger.debug(f"Clamped small value {param_value} to {min_val} for {param_name}")
                    input_widget.setValue(safe_value)
                else:
                    input_widget.setValue(0)
            elif param_type == 'float':
                input_widget = QDoubleSpinBox()
                input_widget.setRange(
                    param_info.get('min', -999999.0), 
                    param_info.get('max', 999999.0)
                )
                input_widget.setDecimals(3)
                input_widget.setValue(float(param_value) if param_value is not None else 0.0)
            elif param_type == 'bool':
                input_widget = QCheckBox()
                input_widget.setChecked(bool(param_value) if param_value is not None else False)
            else:  # text or string
                input_widget = QLineEdit()
                input_widget.setText(str(param_value) if param_value is not None else "")
            
            layout.addWidget(input_widget)
            
            # Store reference for value retrieval
            container.input_widget = input_widget
            container.node_id = node_id
            container.param_name = param_name
            container.get_value = lambda: self._get_widget_value(input_widget)
            
            # Store in parameter widgets for later retrieval
            if not hasattr(self, 'parameter_widgets'):
                self.parameter_widgets = {}
            widget_key = f"{node_id}.{param_name}"
            self.parameter_widgets[widget_key] = container
            
            return container
            
        except Exception as e:
            self.logger.error(f"Failed to create parameter widget for {param_name}: {e}")
            return None
    
    def _update_prompt_memory(self, config: Dict[str, Any]):
        """Update prompt memory hierarchy"""
        try:
            # Use prompt memory manager if available
            if hasattr(self, 'prompt_memory'):
                # Load workflow path to extract prompts
                workflow_path = config.get('workflow_path')
                if workflow_path and Path(workflow_path).exists():
                    with open(workflow_path, 'r') as f:
                        workflow_data = json.load(f)
                    
                    # Load prompts through memory manager
                    self.prompt_memory.load_workflow_prompts(Path(workflow_path), workflow_data)
                    
            else:
                # Fallback to direct update
                if 'positive_prompt' in config and hasattr(self, 'positive_prompt'):
                    self.positive_prompt.setText(config['positive_prompt'])
                    
                if 'negative_prompt' in config and hasattr(self, 'negative_prompt'):
                    self.negative_prompt.setText(config['negative_prompt'])
                    
        except Exception as e:
            self.logger.error(f"Failed to update prompt memory: {e}")
    
    def _clear_dynamic_parameters(self):
        """Clear all dynamic parameter widgets"""
        if hasattr(self, 'dynamic_params_layout'):
            # Clear parameter widget references
            if hasattr(self, 'parameter_widgets'):
                self.parameter_widgets.clear()
            
            # Remove all widgets from layout
            while self.dynamic_params_layout.count():
                item = self.dynamic_params_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
    
    def _load_parameters_from_config(self, param_type: str):
        """Load parameters from configuration and update UI widgets"""
        try:
            self.logger.debug(f"🔄 _load_parameters_from_config called for {param_type}...")
            
            # Initialize parameter widget tracking if not exists
            if not hasattr(self, 'parameter_widgets'):
                self.parameter_widgets = {}
            
            # Verify UI components exist
            ui_components = {
                'dynamic_params_container': hasattr(self, 'dynamic_params_container'),
                'dynamic_params_layout': hasattr(self, 'dynamic_params_layout'),
                'positive_prompt': hasattr(self, 'positive_prompt'),
                'negative_prompt': hasattr(self, 'negative_prompt')
            }
            self.logger.debug(f"🔍 UI Components status: {ui_components}")
            
            missing_components = [name for name, exists in ui_components.items() if not exists]
            if missing_components:
                self.logger.warning(f"⚠️ Missing UI components: {missing_components}")
            self.logger.info(f"🔄 Current working directory: {Path.cwd()}")
            
            # Use unified configuration system if available
            if hasattr(self, 'config_integration'):
                self.logger.info("Using unified configuration system for parameter loading")
                self._load_parameters_unified(param_type, force_workflow_path=None)
                return
            
            if param_type == "image":
                # Load actual configuration
                config_path = Path("config/image_parameters_config.json")
                self.logger.info(f"🔄 Checking config path: {config_path.absolute()}")
                self.logger.info(f"🔄 Config exists: {config_path.exists()}")
                
                if config_path.exists():
                    import json
                    self.logger.info(f"🔄 Reading config file...")
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    self.logger.info(f"🔄 Config loaded: {len(config)} keys")
                    
                    # Check if config is missing widgets_values and regenerate if needed
                    node_info = config.get('node_info', {})
                    needs_regeneration = False
                    for node_key, node_data in node_info.items():
                        if node_data.get('supported', False) and 'widgets_values' not in node_data:
                            needs_regeneration = True
                            break
                    
                    if needs_regeneration:
                        self.logger.warning("Config missing widgets_values - regenerating from workflow")
                        workflow_file = config.get('workflow_file', '')
                        if workflow_file and hasattr(self, 'workflow_combo'):
                            # Find and trigger workflow change to regenerate config with widgets_values
                            QTimer.singleShot(100, lambda: self._regenerate_config_with_widgets_values(workflow_file, param_type))
                            return
                    
                    # Get workflow path and load it
                    workflow_path = config.get('workflow_path')
                    if workflow_path and Path(workflow_path).exists():
                        with open(workflow_path, 'r') as f:
                            workflow_data = json.load(f)
                        
                        # Convert nodes array to lookup dictionary
                        workflow = {}
                        for node in workflow_data.get('nodes', []):
                            workflow[str(node['id'])] = node
                        
                        self.logger.info(f"Loaded workflow with {len(workflow)} nodes")
                        
                        # Clear existing dynamic parameters
                        if hasattr(self, 'dynamic_params_container') and hasattr(self, 'dynamic_params_layout'):
                            old_count = self.dynamic_params_layout.count()
                            self.logger.info(f"🧹 Clearing {old_count} existing parameter widgets")
                            
                            # Clear parameter widget references FIRST
                            if hasattr(self, 'parameter_widgets'):
                                self.logger.info(f"🧹 Clearing {len(self.parameter_widgets)} parameter widget references")
                                self.parameter_widgets.clear()
                            
                            # Clear old widgets
                            while self.dynamic_params_layout.count():
                                child = self.dynamic_params_layout.takeAt(0)
                                if child.widget():
                                    child.widget().deleteLater()
                            
                            self.logger.info(f"✅ Cleared existing parameter widgets (was {old_count}, now {self.dynamic_params_layout.count()})")
                        else:
                            self.logger.warning("⚠️ dynamic_params_container or dynamic_params_layout not found during clearing")
                        
                        # Create dynamic parameter widgets based on config
                        selected_nodes_data = config.get('selected_nodes', [])
                        selected_nodes = []
                        
                        self.logger.debug(f"Creating parameter widgets for workflow: {config.get('workflow_file', 'Unknown')}")
                        # Selected nodes data: {selected_nodes_data}
                        
                        # Extract node IDs from "NodeType_ID" format
                        for node_entry in selected_nodes_data:
                            if isinstance(node_entry, str) and '_' in node_entry:
                                node_id = node_entry.split('_')[-1]
                                selected_nodes.append(node_id)
                            elif isinstance(node_entry, (str, int)):
                                selected_nodes.append(str(node_entry))
                        
                        # Extracted node IDs: {selected_nodes}
                        
                        # First, handle prompt updates
                        self.logger.debug(f"Processing {len(selected_nodes)} nodes for prompt updates")
                        self.logger.debug(f"Selected node IDs: {selected_nodes}")
                        positive_prompt_text = ""
                        negative_prompt_text = ""
                        
                        for node_id in selected_nodes:
                            # Extract numeric ID from node_id like "CLIPTextEncode_13" -> "13"
                            numeric_id = node_id.split('_')[-1] if '_' in node_id else node_id
                            node = workflow.get(str(numeric_id))
                            self.logger.debug(f"Looking for node {numeric_id} in workflow: found={node is not None}")
                            if node and node.get('type') == 'CLIPTextEncode':
                                widgets_values = node.get('widgets_values', [])
                                text = widgets_values[0] if widgets_values else ''
                                
                                # Get the node title - check main title field first, then properties
                                title = node.get('title', '') or node.get('properties', {}).get('Node name for S&R', '')
                                
                                self.logger.debug(f"Found CLIPTextEncode node {node_id} with title: '{title}'")
                                
                                # Check for explicit "positive" or "negative" in the node title
                                if 'positive' in title.lower():
                                    positive_prompt_text = text
                                    self.logger.debug(f"Found POSITIVE prompt node: {text[:50]}...")
                                elif 'negative' in title.lower():
                                    negative_prompt_text = text
                                    self.logger.debug(f"Found NEGATIVE prompt node: {text[:50]}...")
                                else:
                                    self.logger.warning(f"⚠️ CLIPTextEncode node {node_id} title '{title}' doesn't contain 'positive' or 'negative' - skipping")
                        
                        # Update prompt widgets
                        if positive_prompt_text and hasattr(self, 'positive_prompt'):
                            self.positive_prompt.setText(positive_prompt_text)
                            self.logger.debug("Updated positive prompt widget")
                            
                            # Also update through prompt memory if available
                            if hasattr(self, 'prompt_memory'):
                                self.prompt_memory.set_prompt('positive', positive_prompt_text, is_user_edit=False)
                        
                        if negative_prompt_text and hasattr(self, 'negative_prompt'):
                            self.negative_prompt.setText(negative_prompt_text)
                            self.logger.debug("Updated negative prompt widget")
                            
                            # Also update through prompt memory if available
                            if hasattr(self, 'prompt_memory'):
                                self.prompt_memory.set_prompt('negative', negative_prompt_text, is_user_edit=False)
                        
                        # Log if no prompts were found
                        if not positive_prompt_text and not negative_prompt_text:
                            self.logger.warning("⚠️ No positive or negative prompts found in workflow")
                        
                        # Sort nodes by ComfyUI workflow order
                        ordered_nodes = self._sort_nodes_by_workflow_order(selected_nodes, workflow)
                        # Ordered nodes: {ordered_nodes}
                        
                        for node_id in ordered_nodes:
                            # Extract numeric ID from node_id like "KSampler_10" -> "10"
                            numeric_id = node_id.split('_')[-1] if '_' in node_id else node_id
                            node = workflow.get(str(numeric_id))
                            if not node:
                                continue
                                
                            node_type = node.get('type', '')
                            widgets_values = node.get('widgets_values', [])
                            
                            self.logger.debug(f"Processing node {node_id}: {node_type}")
                            
                            # Skip prompt nodes - they're handled separately
                            if node_type == 'CLIPTextEncode':
                                continue
                            
                            # Handle Note/MarkdownNote nodes specially - display as text
                            if node_type in ['Note', 'MarkdownNote']:
                                if widgets_values and len(widgets_values) > 0:
                                    note_text = widgets_values[0]
                                    note_title = node.get('title', 'Note')
                                    
                                    # Create a styled note widget
                                    note_widget = self._create_note_display_widget(note_text, note_title, node_type)
                                    if note_widget and hasattr(self, 'dynamic_params_layout'):
                                        self.dynamic_params_layout.addWidget(note_widget)
                                        self.logger.debug(f"Added {node_type} display for node {node_id}")
                                continue
                            
                            # Skip nodes without configurable parameters
                            if not widgets_values or len(widgets_values) == 0:
                                self.logger.debug(f"Skipping {node_type} #{node_id} - no widget values")
                                continue
                            
                            # Skip nodes that are just display/output nodes (no user-configurable parameters)
                            display_only_nodes = ['Preview3D', 'SaveImage', 'PreviewImage', 'Note', 'MarkdownNote']
                            if node_type in display_only_nodes:
                                self.logger.debug(f"Skipping {node_type} #{node_id} - display only node")
                                continue
                            
                            # Create group for this node with better organization
                            group_title = self._get_friendly_node_title(node_type, node_id, node.get('title', ''))
                            self.logger.info(f"Creating parameter group: '{group_title}' for {node_type} #{node_id}")
                            group_box = QGroupBox(group_title)
                            group_box.setObjectName("parameter_group")
                            
                            # Add header with X button to remove/bypass node
                            header_layout = QHBoxLayout()
                            header_layout.setContentsMargins(0, 0, 0, 0)
                            
                            # Node type label
                            type_label = QLabel(f"{node_type}")
                            type_label.setObjectName("node_type_label")
                            type_label.setStyleSheet("color: #666; font-size: 10px;")
                            header_layout.addWidget(type_label)
                            
                            header_layout.addStretch()
                            
                            # Bypass checkbox
                            bypass_check = QCheckBox("Bypass")
                            bypass_check.setObjectName(f"bypass_{node_type}_{node_id}")
                            bypass_check.setToolTip("Temporarily disable this node")
                            bypass_check.stateChanged.connect(lambda state: self._on_node_bypass_changed(node_id, node_type, state))
                            header_layout.addWidget(bypass_check)
                            
                            # Remove button
                            remove_btn = QPushButton("×")
                            remove_btn.setObjectName("remove_node_btn")
                            remove_btn.setFixedSize(20, 20)
                            remove_btn.setToolTip("Remove this node from workflow")
                            remove_btn.setStyleSheet("""
                                QPushButton {
                                    background-color: transparent;
                                    color: #888;
                                    border: none;
                                    font-size: 16px;
                                    font-weight: bold;
                                }
                                QPushButton:hover {
                                    color: #ff4444;
                                    background-color: rgba(255, 68, 68, 0.1);
                                    border-radius: 3px;
                                }
                            """)
                            remove_btn.clicked.connect(lambda: self._on_remove_node_clicked(node_id, node_type))
                            header_layout.addWidget(remove_btn)
                            
                            # Main layout for the group
                            main_layout = QVBoxLayout()
                            main_layout.addLayout(header_layout)
                            
                            # Parameter widgets layout
                            group_layout = QVBoxLayout()
                            
                            # Create widgets using node parameter definitions
                            node_definitions = self._get_node_parameter_definitions()
                            node_def = node_definitions.get(node_type)
                            
                            self.logger.debug(f"Creating widgets for {node_type}")
                            
                            # Additional safety check for dynamic_params_layout
                            if not hasattr(self, 'dynamic_params_layout'):
                                self.logger.error(f"❌ CRITICAL: dynamic_params_layout not found when creating widgets for {node_type}")
                                continue
                            
                            if node_def and not node_def.get('skip_ui', False):
                                widgets_mapping = node_def.get('widgets_mapping', [])
                                self.logger.info(f"🔧 NODE: {node_type}_{node_id}")
                                self.logger.info(f"🔧 WIDGETS_VALUES: {widgets_values}")
                                self.logger.info(f"🔧 DEFINITION: {len(widgets_mapping)} widget mappings")
                                
                                # Create widgets from definition
                                for i, widget_def in enumerate(widgets_mapping):
                                    if i < len(widgets_values):
                                        # Skip if marked as skip (handled elsewhere in UI)
                                        if widget_def.get('skip', False):
                                            self.logger.info(f"⏭️ Skipping {widget_def['name']} (marked skip)")
                                            continue
                                        value = widgets_values[i]
                                        self.logger.info(f"🎯 Creating widget '{widget_def['name']}' with value: {value} (type: {type(value)})")
                                        self.logger.info(f"🎯 Widget def: {widget_def}")
                                        # Create widget key as node_type_node_id_param_index
                                        param_key = f"{node_type}_{node_id}_{str(i)}"
                                        widget = self._create_widget_from_definition(widget_def, value, node_type, node_id, param_key)
                                        if widget:
                                            group_layout.addWidget(widget)
                                            self.logger.debug(f"✅ Added widget: {widget_def['name']}")
                                        else:
                                            self.logger.error(f"❌ Failed to create widget: {widget_def['name']}")
                                    else:
                                        self.logger.warning(f"⚠️ No value for widget {i}: {widget_def['name']} (have {len(widgets_values)} values)")
                                
                                # Add extra widgets
                                extra_widgets = node_def.get('extra_widgets', [])
                                for j, extra_def in enumerate(extra_widgets):
                                    # Create widget key as node_type_node_id_param_index
                                    extra_param_key = f"{node_type}_{node_id}_{str(len(widgets_mapping) + j)}"
                                    widget = self._create_widget_from_definition(extra_def, extra_def.get('default'), node_type, node_id, extra_param_key)
                                    if widget:
                                        group_layout.addWidget(widget)
                                        # Added extra widget
                            else:
                                # Fallback for undefined node types
                                self.logger.warning(f"No definition found for node type: {node_type}")
                                for i, value in enumerate(widgets_values):
                                    widget_name = f"Parameter {i+1}"
                                    if isinstance(value, (int, float)):
                                        if isinstance(value, int):
                                            group_layout.addWidget(self._create_int_widget(widget_name, value, -1000, 1000))
                                        else:
                                            group_layout.addWidget(self._create_float_widget(widget_name, value, -100.0, 100.0))
                                    else:
                                        group_layout.addWidget(self._create_text_widget(widget_name, str(value)))
                            
                            self.logger.debug(f"Group layout widget count for {node_type}: {group_layout.count()}")
                            
                            if group_layout.count() > 0:
                                # Add parameter widgets to main layout
                                main_layout.addLayout(group_layout)
                                # Don't add stretch here - it causes unnecessary expansion
                                
                                # Set the complete layout to group box
                                group_box.setLayout(main_layout)
                                
                                # Make group box more compact
                                group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
                                
                                if hasattr(self, 'dynamic_params_layout'):
                                    # Store node info for later reference
                                    group_box.setProperty("node_id", node_id)
                                    group_box.setProperty("node_type", node_type)
                                    
                                    self.dynamic_params_layout.addWidget(group_box)
                                    self.logger.debug(f"Added parameter group for {node_type}")
                                    # Force layout update
                                    self.dynamic_params_container.updateGeometry()
                                else:
                                    self.logger.error(f"❌ dynamic_params_layout not found!")
                            else:
                                self.logger.warning(f"⚠️ No widgets created for {node_type} - group layout is empty")
                        
                        # Update batch size preview
                        if hasattr(self, 'batch_size_spin'):
                            self._update_batch_preview(self.batch_size_spin.value())
                            
                        # Final summary and UI refresh
                        final_widget_count = self.dynamic_params_layout.count()
                        self.logger.info(f"Loaded {final_widget_count} parameter groups from workflow")
                        
                        # Force UI update
                        if hasattr(self, 'dynamic_params_container'):
                            self.dynamic_params_container.repaint()
                            self.dynamic_params_container.update()
                            
                        # Parameter loading complete
                        
                        # CRITICAL: Recalculate splitter sizes after loading parameters
                        # This prevents UI height explosion when many parameters are loaded
                        if hasattr(self, '_recalculate_splitter_sizes'):
                            self._recalculate_splitter_sizes()
                        
                        # Verify the UI is actually updated
                        if hasattr(self, 'dynamic_params_layout'):
                            current_count = self.dynamic_params_layout.count()
                            self.logger.debug(f"Dynamic params layout has {current_count} widgets")
                            
                            # List all widgets in the layout for debugging
                            for i in range(current_count):
                                widget = self.dynamic_params_layout.itemAt(i).widget()
                                widget_name = widget.objectName() if widget else "Unknown"
                                self.logger.debug(f"  Widget {i}: {type(widget).__name__} - {widget_name}")
                        else:
                            self.logger.error(f"🚨 VERIFICATION FAILED: dynamic_params_layout still not found after loading!")
                    else:
                        self.logger.warning(f"Workflow file not found: {workflow_path}")
                else:
                    self.logger.info("No image parameters configuration found")
                
        except Exception as e:
            self.logger.error(f"Failed to load {param_type} parameters: {e}")
            import traceback
            self.logger.error(f"Parameter loading traceback: {traceback.format_exc()}")
            # Show error dialog for user feedback
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Parameter Loading Error", 
                              f"Failed to load {param_type} parameters. Check logs for details.\n\nError: {str(e)}")
    
    def _get_node_parameter_definitions(self):
        """Define node parameter structures with proper data types for UI widgets"""
        return {
            'CheckpointLoaderSimple': {
                'widgets_mapping': [
                    {'name': 'Checkpoint File', 'type': 'string', 'widget': 'combo', 'options': []}
                ]
            },
            'LoraLoader': {
                'widgets_mapping': [
                    {'name': 'LoRA File', 'type': 'string', 'widget': 'combo', 'options': []},
                    {'name': 'Model Strength', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 2.0, 'step': 0.01},
                    {'name': 'CLIP Strength', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 2.0, 'step': 0.01}
                ]
            },
            'KSampler': {
                'widgets_mapping': [
                    # Correct ComfyUI order: seed, control_after_generation, steps, cfg, sampler_name, scheduler, denoise
                    {'name': 'Seed', 'type': 'int', 'widget': 'int', 'min': -1, 'max': 2147483647, 'default': -1, 'index': 0},
                    {'name': 'Control After Generation', 'type': 'string', 'widget': 'combo', 'options': ['fixed', 'increment', 'decrement', 'randomize'], 'default': 'fixed', 'index': 1},
                    {'name': 'Steps', 'type': 'int', 'widget': 'int', 'min': 1, 'max': 150, 'default': 20, 'index': 2},
                    {'name': 'CFG Scale', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 30.0, 'step': 0.1, 'default': 7.5, 'index': 3},
                    {'name': 'Sampler Name', 'type': 'string', 'widget': 'combo', 'options': ['euler', 'euler_a', 'heun', 'dpm_2', 'dpm_2_a', 'lms', 'dpm_fast', 'dpm_adaptive', 'dpmpp_2s_a', 'dpmpp_2m', 'dpmpp_2m_sde', 'dpmpp_3m_sde', 'ddpm', 'lcm'], 'default': 'euler', 'index': 4},
                    {'name': 'Scheduler', 'type': 'string', 'widget': 'combo', 'options': ['normal', 'karras', 'exponential', 'sgm_uniform', 'simple', 'ddim_uniform'], 'default': 'normal', 'index': 5},
                    {'name': 'Denoise', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 1.0, 'step': 0.01, 'default': 1.0, 'index': 6}
                ]
            },
            'FluxGuidance': {
                'widgets_mapping': [
                    {'name': 'Guidance', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 20.0, 'step': 0.1, 'default': 3.5}
                ]
            },
            'EmptySD3LatentImage': {
                'widgets_mapping': [
                    {'name': 'Width', 'type': 'int', 'widget': 'int', 'min': 16, 'max': 2048, 'step': 64, 'default': 512, 'skip': True},  # Handled in left panel
                    {'name': 'Height', 'type': 'int', 'widget': 'int', 'min': 16, 'max': 2048, 'step': 64, 'default': 512, 'skip': True},  # Handled in left panel
                    {'name': 'Batch Size', 'type': 'int', 'widget': 'int', 'min': 1, 'max': 64, 'default': 1, 'skip': True}  # Handled in left panel
                ]
            },
            'CLIPTextEncode': {
                'widgets_mapping': [
                    {'name': 'Text', 'type': 'string', 'widget': 'text_multiline'}
                ],
                'skip_ui': True  # Handled separately in prompt widgets
            },
            'Note': {
                'widgets_mapping': [
                    {'name': 'Note', 'type': 'string', 'widget': 'text_display'}
                ]
            },
            # SD3 and Flux specific nodes
            'VAELoader': {
                'widgets_mapping': [
                    {'name': 'VAE Name', 'type': 'string', 'widget': 'combo', 'options': []}
                ]
            },
            'UNETLoader': {
                'widgets_mapping': [
                    {'name': 'UNET Name', 'type': 'string', 'widget': 'combo', 'options': []},
                    {'name': 'Weight dtype', 'type': 'string', 'widget': 'combo', 'options': ['default', 'fp8_e4m3fn', 'fp8_e5m2']}
                ]
            },
            'QuadrupleCLIPLoader': {
                'widgets_mapping': [
                    {'name': 'CLIP 1', 'type': 'string', 'widget': 'combo', 'options': []},
                    {'name': 'CLIP 2', 'type': 'string', 'widget': 'combo', 'options': []},
                    {'name': 'CLIP 3', 'type': 'string', 'widget': 'combo', 'options': []},
                    {'name': 'CLIP 4', 'type': 'string', 'widget': 'combo', 'options': []}
                ]
            },
            'ModelSamplingSD3': {
                'widgets_mapping': [
                    {'name': 'Shift', 'type': 'float', 'widget': 'float', 'min': 0.0, 'max': 10.0, 'step': 0.01, 'default': 3.0}
                ]
            }
        }
    
    def _sort_nodes_by_workflow_order(self, node_ids: list, workflow: dict) -> list:
        """Sort nodes in ComfyUI workflow order: Checkpoint → LoRA → KSampler → Others"""
        node_order = []
        
        # Priority order for node types
        priority_order = {
            'CheckpointLoaderSimple': 1,
            'CheckpointLoader': 1,
            'UNETLoader': 1,  # Same priority as checkpoint loaders
            'VAELoader': 1,
            'QuadrupleCLIPLoader': 1,
            'LoraLoader': 2,
            'ModelSamplingSD3': 3,
            'KSampler': 4,
            'FluxGuidance': 5,
            'EmptySD3LatentImage': 6,
            'CLIPTextEncode': 7,  # Will be handled separately
        }
        
        # Separate and sort nodes
        categorized_nodes = {}
        for node_id in node_ids:
            # Extract numeric ID from node_id like "KSampler_10" -> "10"
            numeric_id = node_id.split('_')[-1] if '_' in node_id else node_id
            node = workflow.get(str(numeric_id))
            if not node:
                continue
            
            node_type = node.get('type', '')
            priority = priority_order.get(node_type, 99)
            
            if priority not in categorized_nodes:
                categorized_nodes[priority] = []
            categorized_nodes[priority].append(node_id)
        
        # Build ordered list
        for priority in sorted(categorized_nodes.keys()):
            nodes_in_category = categorized_nodes[priority]
            
            # For LoRA nodes, sort by node ID to maintain order
            if priority == 2:  # LoraLoader
                nodes_in_category.sort(key=int)
            
            node_order.extend(nodes_in_category)
        
        return node_order
    
    def _create_widget_from_definition(self, widget_def: dict, value, node_type: str = None, node_id: str = None, param_key: str = None):
        """Create widget based on definition with proper data type validation"""
        widget_type = widget_def.get('widget', 'text')
        name = widget_def.get('name', 'Parameter')
        data_type = widget_def.get('type', 'string')
        
        # Validate and convert value to correct type
        try:
            if data_type == 'int':
                value = int(value) if value is not None else widget_def.get('default', 0)
                min_val = widget_def.get('min', -1000)
                max_val = widget_def.get('max', 1000)
                return self._create_int_widget(name, value, min_val, max_val, node_id, param_key)
                
            elif data_type == 'float':
                value = float(value) if value is not None else widget_def.get('default', 0.0)
                min_val = widget_def.get('min', -100.0)
                max_val = widget_def.get('max', 100.0)
                step = widget_def.get('step', 0.1)
                return self._create_float_widget(name, value, min_val, max_val, step, node_id, param_key)
                
            elif data_type == 'string':
                value = str(value) if value is not None else widget_def.get('default', '')
                if widget_type == 'combo':
                    options = widget_def.get('options', [])
                    self.logger.info(f"🎯 Creating combo '{name}' with {len(options)} predefined options: {options}")
                    self.logger.info(f"🎯 Combo value to set: '{value}'")
                    
                    # Auto-populate model dropdowns based on parameter name
                    if not options and name and any(keyword in name.lower() for keyword in ['checkpoint', 'lora', 'vae', 'clip', 'model']):
                        options = self._get_dropdown_options_for_parameter(name, node_type)
                        self.logger.info(f"Auto-populated {name} with {len(options)} model options")
                    # Auto-populate sampler/scheduler dropdowns from ComfyUI standard lists
                    elif not options and 'sampler' in name.lower():
                        options = ['euler', 'euler_a', 'heun', 'dpm_2', 'dpm_2_a', 'lms', 'dpm_fast', 'dpm_adaptive', 'dpmpp_2s_a', 'dpmpp_2m', 'dpmpp_2m_sde', 'dpmpp_3m_sde', 'ddpm', 'lcm']
                        self.logger.info(f"Auto-populated sampler options for {name}")
                    elif not options and 'scheduler' in name.lower():
                        options = ['normal', 'karras', 'exponential', 'sgm_uniform', 'simple', 'ddim_uniform']
                        self.logger.info(f"Auto-populated scheduler options for {name}")
                    elif not options and 'control' in name.lower():
                        options = ['fixed', 'increment', 'decrement', 'randomize']
                        self.logger.info(f"Auto-populated control options for {name}")
                    
                    self.logger.info(f"🎯 Final options for '{name}': {options}")
                    self.logger.info(f"🎯 Value '{value}' in options: {value in options}")
                    return self._create_combo_widget(name, value, options, node_type, node_id, param_key)
                elif widget_type == 'text_multiline':
                    return self._create_multiline_text_widget(name, value)
                elif widget_type == 'text_display':
                    return self._create_text_display_widget(name, value)
                else:
                    return self._create_text_widget(name, value)
                    
            elif data_type == 'bool':
                value = bool(value) if value is not None else widget_def.get('default', False)
                return self._create_checkbox_widget(name, value, node_id, param_key)
                
            elif data_type == 'action' and widget_type == 'button':
                return self._create_action_button(name)
                
        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to create widget {name}: {e}")
            # Fallback to text widget
            return self._create_text_widget(name, str(value))
        
        return None
    
    def _create_int_widget(self, name: str, value: int, min_val: int, max_val: int, node_id: str = None, param_key: str = None):
        """Create an integer input widget with type display"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(2)
        
        # Parameter name and type on top
        header_layout = QHBoxLayout()
        label = QLabel(f"{name}")
        label.setObjectName("param_name")
        header_layout.addWidget(label)
        
        header_layout.addStretch()
        
        type_label = QLabel("int")
        type_label.setObjectName("param_type")
        type_label.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
        header_layout.addWidget(type_label)
        
        layout.addLayout(header_layout)
        
        # Value input
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(value)
        spinbox.setMinimumWidth(80)  # Reduced for more compact panels
        layout.addWidget(spinbox)
        
        # Store reference to the actual input widget for value retrieval
        if node_id and param_key and hasattr(self, 'parameter_widgets'):
            # Create a safer getter that checks widget validity
            def get_int_value(widget=spinbox):
                try:
                    return widget.value()
                except RuntimeError:
                    return 0  # Default value if widget is deleted
            
            self.parameter_widgets[param_key] = {
                'widget': spinbox,
                'type': 'int',
                'get_value': get_int_value
            }
            logger.debug(f"Stored int widget tracking: {param_key}")
        
        return container
    
    def _create_float_widget(self, name: str, value: float, min_val: float, max_val: float, step: float = 0.1, node_id: str = None, param_key: str = None):
        """Create a float input widget with type display"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(2)
        
        # Parameter name and type on top
        header_layout = QHBoxLayout()
        label = QLabel(f"{name}")
        label.setObjectName("param_name")
        header_layout.addWidget(label)
        
        header_layout.addStretch()
        
        type_label = QLabel("float")
        type_label.setObjectName("param_type")
        type_label.setStyleSheet("color: #2196F3; font-size: 10px; font-weight: bold;")
        header_layout.addWidget(type_label)
        
        layout.addLayout(header_layout)
        
        # Value input
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setDecimals(3 if step < 0.1 else 2)
        spinbox.setSingleStep(step)
        spinbox.setValue(value)
        spinbox.setMinimumWidth(80)  # Reduced for more compact panels
        layout.addWidget(spinbox)
        
        # Store reference to the actual input widget for value retrieval
        if node_id and param_key and hasattr(self, 'parameter_widgets'):
            # Create a safer getter that checks widget validity
            def get_float_value(widget=spinbox):
                try:
                    return widget.value()
                except RuntimeError:
                    return 0.0  # Default value if widget is deleted
            
            self.parameter_widgets[param_key] = {
                'widget': spinbox,
                'type': 'float',
                'get_value': get_float_value
            }
            logger.debug(f"Stored float widget tracking: {param_key}")
        
        return container
    
    def _create_text_widget(self, name: str, value: str):
        """Create a text input widget"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(f"{name}:")
        label.setMinimumWidth(60)  # Reduced for more compact panels
        layout.addWidget(label)
        
        if len(value) > 50:
            # Use text edit for long values
            text_edit = QTextEdit()
            text_edit.setMaximumHeight(60)
            text_edit.setPlainText(value)
            layout.addWidget(text_edit)
        else:
            # Use line edit for short values
            line_edit = QLineEdit()
            line_edit.setText(value)
            layout.addWidget(line_edit)
        
        return container
    
    def _create_checkbox_widget(self, name: str, checked: bool, node_id: str = None, param_key: str = None):
        """Create a checkbox widget"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        checkbox = QCheckBox(name)
        checkbox.setChecked(checked)
        layout.addWidget(checkbox)
        layout.addStretch()
        
        # Store reference to the actual input widget for value retrieval
        if node_id and param_key and hasattr(self, 'parameter_widgets'):
            # Create a safer getter that checks widget validity
            def get_checkbox_value(widget=checkbox):
                try:
                    return widget.isChecked()
                except RuntimeError:
                    return False  # Default value if widget is deleted
            
            self.parameter_widgets[param_key] = {
                'widget': checkbox,
                'type': 'bool',
                'get_value': get_checkbox_value
            }
            logger.debug(f"Stored checkbox widget tracking: {param_key}")
        
        return container
    
    def _get_model_options_for_parameter(self, param_name: str, node_type: str = None) -> list:
        """Get model options dynamically based on node type using the model scanner"""
        # Use the dynamic model scanner
        if not hasattr(self, '_model_scanner'):
            from .model_scanner import ComfyUIModelScanner
            # Try to get ComfyUI path from config
            comfyui_models_dir = None
            if hasattr(self.config, 'comfyui_path') and self.config.comfyui_path:
                comfyui_models_dir = self.config.comfyui_path / "models"
            # Pass config to scanner for comprehensive directory support
            self._model_scanner = ComfyUIModelScanner(comfyui_models_dir, config=self.config)
        
        # Get models for the specific node type
        if node_type:
            options = self._model_scanner.get_models_for_node(node_type)
            if options:
                self.logger.debug(f"Found {len(options)} models for {node_type}")
                return options
        
        # Fallback: try to determine by parameter name if no node type
        options = []
        
        if 'lora' in param_name.lower():
            options = self._model_scanner.get_models_for_node("LoraLoader")
        elif 'checkpoint' in param_name.lower() or 'ckpt' in param_name.lower():
            options = self._model_scanner.get_models_for_node("CheckpointLoaderSimple")
        elif 'vae' in param_name.lower():
            options = self._model_scanner.get_models_for_node("VAELoader")
        elif 'clip' in param_name.lower():
            options = self._model_scanner.get_models_for_node("CLIPLoader")
        elif 'unet' in param_name.lower():
            options = self._model_scanner.get_models_for_node("UNETLoader")
        elif 'controlnet' in param_name.lower():
            options = self._model_scanner.get_models_for_node("ControlNetLoader")
        elif 'upscale' in param_name.lower():
            options = self._model_scanner.get_models_for_node("UpscaleModelLoader")
                    
        elif 'embedding' in param_name.lower() or 'textual_inversion' in param_name.lower():
            # Get embedding models
            if hasattr(self.config, 'comfyui_path') and self.config.comfyui_path:
                embeddings_dir = self.config.comfyui_path / "models" / "embeddings"
                if embeddings_dir.exists():
                    options = [f.name for f in embeddings_dir.glob("*.safetensors")]
                    options.extend([f.name for f in embeddings_dir.glob("*.pt")])
                    options.extend([f.name for f in embeddings_dir.glob("*.bin")])
        
        # Add "None" option at the beginning if we have options
        if options:
            options = ["None"] + sorted(options)
        else:
            options = ["None", "No models found"]
            
        return options

    def _create_combo_widget(self, name: str, value: str, options: list, node_type: str = None, node_id: str = None, param_key: str = None):
        """Create a combo box widget with type display and dynamic model options"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(2)
        
        # Parameter name and type on top
        header_layout = QHBoxLayout()
        label = QLabel(f"{name}")
        label.setObjectName("param_name")
        header_layout.addWidget(label)
        
        header_layout.addStretch()
        
        type_label = QLabel("string")
        type_label.setObjectName("param_type")
        type_label.setStyleSheet("color: #FF9800; font-size: 10px; font-weight: bold;")
        header_layout.addWidget(type_label)
        
        layout.addLayout(header_layout)
        
        # Check if this is a model parameter and get dynamic options
        model_keywords = ['lora', 'checkpoint', 'ckpt', 'vae', 'controlnet', 'control_net', 
                         'upscale', 'esrgan', 'embedding', 'textual_inversion']
        is_model_param = any(keyword in name.lower() for keyword in model_keywords)
        
        if is_model_param:
            # Get dynamic model options
            dynamic_options = self._get_model_options_for_parameter(name, node_type)
            if dynamic_options:
                options = dynamic_options
                logger.debug(f"Populated {name} with {len(options)} model options")
        
        # Value input
        combo = QComboBox()
        self.logger.info(f"🎯 Adding {len(options)} items to combo '{name}': {options}")
        combo.addItems(options)
        self.logger.info(f"🎯 Combo '{name}' now has {combo.count()} items")
        
        if value in options:
            combo.setCurrentText(value)
            self.logger.info(f"✅ Set combo '{name}' current value to: {value}")
            self.logger.info(f"✅ Combo '{name}' current text is now: {combo.currentText()}")
        else:
            self.logger.error(f"❌ Value '{value}' not found in options for '{name}', options: {options}")
            self.logger.error(f"❌ Setting combo '{name}' to first option: {options[0] if options else 'NO OPTIONS'}")
            if options:
                combo.setCurrentIndex(0)
            
        combo.setMinimumWidth(80)  # Reduced for more compact panels
        layout.addWidget(combo)
        
        # Store reference to the actual input widget for value retrieval
        if node_id and param_key and hasattr(self, 'parameter_widgets'):
            # Create a safer getter that checks widget validity
            def get_combo_value(widget=combo):
                try:
                    return widget.currentText()
                except RuntimeError:
                    return ""  # Default value if widget is deleted
            
            self.parameter_widgets[param_key] = {
                'widget': combo,
                'type': 'combo',
                'get_value': get_combo_value
            }
            logger.debug(f"Stored combo widget tracking: {param_key}")
        
        return container
    
    def _create_multiline_text_widget(self, name: str, value: str):
        """Create a multiline text widget"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(f"{name}:")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        text_edit.setMaximumHeight(80)
        text_edit.setPlainText(value)
        layout.addWidget(text_edit)
        
        return container
    
    def _create_text_display_widget(self, name: str, value: str):
        """Create a read-only text display widget for Notes"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(f"{name}:")
        label.setObjectName("section_title")
        layout.addWidget(label)
        
        # Read-only text display
        text_label = QLabel(value)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("QLabel { background-color: #2a2a2a; padding: 8px; border-radius: 4px; }")
        text_label.setMinimumHeight(40)
        layout.addWidget(text_label)
        
        return container
    
    def _create_action_button(self, name: str):
        """Create an action button widget"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if name == "Random Seed":
            button = QPushButton("🎲 Randomize")
            button.setObjectName("magic_btn")
            button.clicked.connect(self._randomize_seed)
        else:
            button = QPushButton(name)
            
        layout.addWidget(button)
        layout.addStretch()
        
        return container
    
    def _randomize_seed(self):
        """Randomize seed value - placeholder for now"""
        import random
        # This would need to find the seed widget and update it
        self.logger.info("🎲 Seed randomized")
    
    def _create_node_parameter_widget(self, node_id: str, node_type: str, param_name: str, param_value):
        """Create appropriate widget for parameter based on type"""
        widget_container = QWidget()
        layout = QHBoxLayout(widget_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(f"{param_name}:")
        label.setMinimumWidth(80)  # Reduced for more compact panels
        layout.addWidget(label)
        
        # Create appropriate widget based on value type
        if isinstance(param_value, bool):
            widget = QCheckBox()
            widget.setChecked(param_value)
            widget.stateChanged.connect(lambda state: self._on_parameter_changed(
                node_id, param_name, state == 2
            ))
        elif isinstance(param_value, (int, float)):
            widget = QSpinBox() if isinstance(param_value, int) else QDoubleSpinBox()
            widget.setMinimum(-999999)
            widget.setMaximum(999999)
            widget.setValue(param_value)
            widget.valueChanged.connect(lambda value: self._on_parameter_changed(
                node_id, param_name, value
            ))
        elif isinstance(param_value, str):
            widget = QLineEdit()
            widget.setText(param_value)
            widget.textChanged.connect(lambda text: self._on_parameter_changed(
                node_id, param_name, text
            ))
        elif isinstance(param_value, list) and len(param_value) > 0:
            # For LoRA or model lists
            widget = QComboBox()
            widget.addItems([str(item) for item in param_value])
            widget.currentTextChanged.connect(lambda text: self._on_parameter_changed(
                node_id, param_name, text
            ))
        else:
            # Default to text input
            widget = QLineEdit()
            widget.setText(str(param_value))
            widget.textChanged.connect(lambda text: self._on_parameter_changed(
                node_id, param_name, text
            ))
        
        layout.addWidget(widget)
        layout.addStretch()
        
        # Store reference for later updates
        if not hasattr(self, 'parameter_widgets'):
            self.parameter_widgets = {}
        self.parameter_widgets[f"{node_id}_{param_name}"] = widget
        
        return widget_container
    
    def _on_parameter_changed(self, node_id: str, param_name: str, value):
        """Handle parameter value change"""
        self.logger.info(f"Parameter changed - Node {node_id}, {param_name}: {value}")
        
        # Store in workflow manager for injection
        if hasattr(self, 'workflow_manager'):
            if not hasattr(self.workflow_manager, 'custom_parameters'):
                self.workflow_manager.custom_parameters = {}
            if node_id not in self.workflow_manager.custom_parameters:
                self.workflow_manager.custom_parameters[node_id] = {}
            self.workflow_manager.custom_parameters[node_id][param_name] = value
            
        # Create undo snapshot for parameter changes
        if hasattr(self, '_create_undo_snapshot'):
            self._create_undo_snapshot(f"Parameter changed: {param_name} = {value}")
    
    def _update_batch_preview(self, batch_size: int):
        """Update ImageGridWidget to expect batch_size images"""
        if not hasattr(self, 'new_canvas_grid') or not hasattr(self.new_canvas_grid, 'count'):
            return
            
        # Note: ImageGridWidget will automatically handle new images when they're detected
        # We don't need to create placeholder cards anymore
        self.logger.debug(f"Batch size set to {batch_size}")
        
        # Clear existing preview cards
        while self.new_canvas_grid.count():
            child = self.new_canvas_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Store batch size for dynamic calculations
        self.current_batch_size = batch_size
        
        # Get expected image dimensions from left panel controls
        expected_width = 1024  # Default
        expected_height = 1024
        
        # Get dimensions from the width/height spinboxes in left panel
        if hasattr(self, 'width_spin') and hasattr(self, 'height_spin'):
            expected_width = self.width_spin.value()
            expected_height = self.height_spin.value()
        
        # Store dimensions for resize events
        self.expected_image_width = expected_width
        self.expected_image_height = expected_height
        
        # Get viewport width to calculate optimal columns
        viewport_width = 1000  # Default fallback
        if hasattr(self, 'preview_scroll_area'):
            viewport = self.preview_scroll_area.viewport()
            if viewport:
                viewport_width = viewport.width()
            if viewport_width < 100:  # Not yet sized
                viewport_width = self.preview_scroll_area.width() - 40
            if viewport_width < 100:  # Still too small
                viewport_width = 1000
        
        # Calculate optimal columns based on image size and viewport
        # For 1024x1024 images, we want to fit 2 side by side if possible
        min_card_width = min(expected_width // 2, 400)  # Minimum reasonable display size
        max_card_width = min(expected_width, 600)  # Maximum reasonable display size
        
        # Calculate how many columns can fit
        spacing = 20  # Equal spacing between cards as requested
        columns = 1
        
        # Special logic for 1024x1024 images
        if expected_width == 1024 and expected_height == 1024:
            # For 1024x1024 images, check if we can fit 2 side by side
            # Calculate maximum card width for 2 columns with spacing
            max_card_width_for_2_cols = (viewport_width - spacing) / 2
            if max_card_width_for_2_cols >= 400:  # Minimum 400px per card for good visibility
                columns = 2
            else:
                columns = 1
        else:
            # For other sizes, calculate dynamically
            for test_cols in range(1, 5):  # Test 1-4 columns
                required_width = (min_card_width * test_cols) + (spacing * (test_cols - 1))
                if required_width <= viewport_width:
                    columns = test_cols
                else:
                    break
        
        # Store columns for use in preview card creation
        self.preview_columns = columns
        self.preview_spacing = spacing
        
        # Create preview cards with smart sizing
        for i in range(batch_size):
            preview_card = self._create_smart_preview_card(i + 1, expected_width, expected_height, columns, spacing, viewport_width)
            row = i // columns
            col = i % columns
            self.new_canvas_grid.addWidget(preview_card, row, col)
        
        # Update grid spacing
        self.new_canvas_grid.setSpacing(spacing)
        
        # Install resize event filter on scroll area if not already installed
        if hasattr(self, 'preview_scroll_area') and not hasattr(self, '_resize_filter_installed'):
            self.preview_scroll_area.viewport().installEventFilter(self)
            self._resize_filter_installed = True
        
        self.logger.debug(f"Created {batch_size} preview cards in {columns} columns with {spacing}px spacing")
    
    def _create_smart_preview_card(self, index: int, expected_width: int, expected_height: int, columns: int, spacing: int, viewport_width: int) -> QWidget:
        """Create a smart responsive preview card based on expected image dimensions"""
        card = QWidget()
        card.setObjectName("preview_card")
        
        # Calculate card dimensions based on columns and viewport
        # Account for spacing between cards
        available_width = viewport_width - (spacing * (columns - 1))
        card_width = available_width // columns
        
        # Calculate aspect ratio
        aspect_ratio = expected_width / expected_height if expected_height > 0 else 1.0
        
        # Smart sizing rules
        if columns == 1:  # Full width for single column
            # Maximum display size while maintaining aspect ratio
            max_display_width = min(card_width - 20, expected_width, 1200)  # Leave some margin
            display_width = max_display_width
            display_height = int(display_width / aspect_ratio)
            
            # Cap height at reasonable size
            max_height = 600
            if display_height > max_height:
                display_height = max_height
                display_width = int(display_height * aspect_ratio)
        elif columns == 2:
            # For 2 columns, optimize for side-by-side display
            # Use most of available width for better visibility
            display_width = card_width - 20  # Small margin for padding
            display_height = int(display_width / aspect_ratio)
            
            # Ensure minimum size for visibility
            if display_width < 400:
                display_width = min(400, card_width - 20)
                display_height = int(display_width / aspect_ratio)
        else:
            # For 3+ columns, scale down more
            display_width = min(card_width - 20, 400)
            display_height = int(display_width / aspect_ratio)
        
        # Set card size with padding for UI elements
        card_padding = 40  # Space for delete button and padding
        card.setFixedSize(display_width + 20, display_height + card_padding)
        
        # Studio viewer black theme for the card
        card.setStyleSheet("""
            QWidget#preview_card {
                background-color: #000000;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Image placeholder with proper sizing
        placeholder = QLabel()
        placeholder.setObjectName("preview_placeholder")
        placeholder.setFixedSize(display_width, display_height)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setScaledContents(True)
        placeholder.setWordWrap(True)
        
        # Initial placeholder display
        placeholder.setText(f"Ready for {expected_width}x{expected_height}")
        placeholder.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 1px solid #333333;
                border-radius: 8px;
                color: #666666;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 20px;
            }
        """)
        
        # Make placeholder clickable for selection
        placeholder.mousePressEvent = lambda event: self._on_image_card_clicked(index, placeholder)
        
        layout.addWidget(placeholder)
        
        # Add delete button (hidden initially, contextual)
        delete_btn = QPushButton("×")  # Using × symbol for subtle delete
        delete_btn.setObjectName("delete_btn")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 0.1);
                border: 1px solid rgba(255, 0, 0, 0.3);
                border-radius: 15px;
                color: #ff6666;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.2);
                border-color: rgba(255, 0, 0, 0.5);
            }
        """)
        delete_btn.hide()  # Hidden until image is selected
        delete_btn.clicked.connect(lambda: self._delete_image(index))
        
        # Position delete button in top-right corner
        delete_btn.setParent(placeholder)
        delete_btn.move(display_width - 35, 5)
        
        # Store reference for later
        if not hasattr(self, 'image_cards'):
            self.image_cards = {}
        self.image_cards[index] = {
            'placeholder': placeholder,
            'delete_btn': delete_btn,
            'loading_timer': None,
            'loading_frame': 0,
            'expected_size': (expected_width, expected_height),
            'display_size': (display_width, display_height),
            'selected': False
        }
        
        return card
    
    def _create_preview_card(self, index: int) -> QWidget:
        """Create a preview card for batch generation with ASCII loading animation"""
        card = QWidget()
        card.setObjectName("preview_card")
        # Responsive sizing - minimum size with maximum constraint
        card.setMinimumSize(256, 280)
        card.setMaximumSize(512, 540)
        
        # Studio viewer black theme for the card
        card.setStyleSheet("""
            QWidget#preview_card {
                background-color: #000000;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Image placeholder with ASCII loading animation
        placeholder = QLabel()
        placeholder.setObjectName("preview_placeholder")
        placeholder.setMinimumSize(240, 240)
        placeholder.setMaximumSize(496, 496)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setScaledContents(True)
        placeholder.setWordWrap(True)
        
        # Initial placeholder display (not loading yet)
        placeholder.setText(f"Ready for Image {index}")
        placeholder.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 1px solid #333333;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        
        # Make placeholder clickable for selection
        placeholder.mousePressEvent = lambda event: self._on_image_card_clicked(index, placeholder)
        
        # Removed "Ready for generation" status label as requested
        
        layout.addWidget(placeholder)
        
        # Add delete button (hidden initially, shown after image loads)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("delete_btn")
        delete_btn.setMaximumHeight(25)
        delete_btn.hide()  # Hidden until image is loaded
        delete_btn.clicked.connect(lambda: self._delete_image(index))
        layout.addWidget(delete_btn)
        
        # Store reference for later image loading and animation
        if not hasattr(self, 'image_cards'):
            self.image_cards = {}
        self.image_cards[index] = {
            'placeholder': placeholder, 
            'status': None,  # Status label removed as requested
            'delete_btn': delete_btn,
            'loading_timer': None,
            'loading_frame': 0
        }
        
        # Don't start animation yet - only when generation starts
        
        return card
    
    def _start_ascii_loading_animation(self, index: int):
        """Start ASCII loading animation for image card (same as studio viewer)"""
        # ASCII emoji collection (same as studio viewer)
        ascii_emojis = [
            '(╯°□°）╯︵ ┻━┻',
            '¯\\_(ツ)_/¯',
            '(づ｡◕‿‿◕｡)づ',
            'ᕕ( ᐛ )ᕗ',
            '♪~ ᕕ(ᐛ)ᕗ',
            '(☞ﾟヮﾟ)☞',
            '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧',
            '⊂(◉‿◉)つ',
            '(◕‿◕)♡',
            '\\(^o^)/',
            '(｡◕‿◕｡)',
            '(ᵔᴥᵔ)',
            'ʕ•ᴥ•ʔ',
            '(◔_◔)',
            '(¬‿¬)',
            '(｡♥‿♥｡)',
            '(✿◠‿◠)',
            '(◡ ω ◡)',
            '( ͡° ͜ʖ ͡°)',
            '(▰˘◡˘▰)'
        ]
        
        import random
        loading_chars = ['L', 'O', 'A', 'D', 'I', 'N', 'G', '.', '.', '.']
        
        def update_animation():
            if index in self.image_cards:
                card_data = self.image_cards[index]
                placeholder = card_data['placeholder']
                frame = card_data['loading_frame']
                
                # Don't animate if image is already loaded
                if placeholder.pixmap() and not placeholder.pixmap().isNull():
                    if card_data['loading_timer']:
                        card_data['loading_timer'].stop()
                    return
                
                # Random emoji (same for this card until reload)
                random.seed(index * 100)  # Consistent emoji per card
                emoji = random.choice(ascii_emojis)
                random.seed()  # Reset seed
                
                # Add offset per image so they look different
                offset_frame = frame + (index * 3)  # Each image starts 3 frames apart
                
                # Animate dots
                dots = '.' * (offset_frame % 4)
                spaces = ' ' * (3 - (offset_frame % 4))
                
                # Build animated text
                text = f'<div style="font-size: 20px; margin-bottom: 15px;">{emoji}</div>'
                
                # Animate the loading text with offset
                text += '<div style="font-size: 14px; letter-spacing: 2px;">'
                for i, char in enumerate(loading_chars):
                    if i < (offset_frame % (len(loading_chars) + 3)):
                        text += char + ' '
                    else:
                        text += '  '
                text += '</div>'
                
                text += f'<div style="font-size: 16px; margin-top: 10px;">{dots}{spaces}</div>'
                
                # Update placeholder
                placeholder.setText(text)
                
                # Increment frame
                card_data['loading_frame'] = frame + 1
        
        # Create and start timer
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(update_animation)
        timer.start(150)  # Same interval as studio viewer
        
        # Store timer reference
        self.image_cards[index]['loading_timer'] = timer
        
        # Update status to show loading (if status widget exists)
        if 'status' in self.image_cards[index] and self.image_cards[index]['status']:
            self.image_cards[index]['status'].setText("🎨 Generating...")
    
    def _stop_ascii_loading_animation(self, index: int):
        """Stop ASCII loading animation for image card"""
        if index in self.image_cards and self.image_cards[index]['loading_timer']:
            self.image_cards[index]['loading_timer'].stop()
            self.image_cards[index]['loading_timer'] = None
    
    def _on_image_card_clicked(self, index: int, placeholder: QLabel):
        """Handle image card click for selection and contextual delete button"""
        try:
            # Check if placeholder has an actual image
            if placeholder.pixmap() and not placeholder.pixmap().isNull():
                # Toggle selection state
                if index in self.image_cards:
                    card_info = self.image_cards[index]
                    selected = not card_info.get('selected', False)
                    card_info['selected'] = selected
                    
                    # Show/hide delete button based on selection
                    if card_info.get('delete_btn'):
                        if selected:
                            card_info['delete_btn'].show()
                            card_info['delete_btn'].raise_()  # Ensure on top
                        else:
                            card_info['delete_btn'].hide()
                    
                    # Update visual selection state
                    if selected:
                        placeholder.setStyleSheet("""
                            QLabel {
                                background-color: #000000;
                                border: 1px solid #4CAF50;
                                border-radius: 8px;
                                padding: 2px;
                            }
                        """)
                    else:
                        placeholder.setStyleSheet("""
                            QLabel {
                                background-color: #000000;
                                border: 1px solid #333333;
                                border-radius: 8px;
                                padding: 3px;
                            }
                        """)
                
                # Get the actual image path
                image_path = getattr(placeholder, 'image_path', None)
                if image_path:
                    # Toggle selection in unified object selector
                    if hasattr(self, 'unified_object_selector'):
                        # Check if already selected
                        object_id = self.unified_object_selector._generate_object_id(image_path)
                        is_selected = (object_id in self.unified_object_selector.objects and 
                                     self.unified_object_selector.objects[object_id].selected)
                        
                        if is_selected:
                            # Deselect
                            self.unified_object_selector.remove_image_selection(image_path)
                            self._update_all_unified_selectors()
                            self.logger.info(f"🚫 Removed image from selection: {image_path.name}")
                            
                            # Remove visual feedback
                            placeholder.setStyleSheet("""
                                QLabel {
                                    background-color: #000000;
                                    border: 1px solid #333333;
                                    border-radius: 8px;
                                    padding: 4px;
                                }
                            """)
                            
                            # Update status to show deselected (if status widget exists)
                            if hasattr(self, 'image_cards') and index in self.image_cards:
                                status = self.image_cards[index].get('status')
                                if status:
                                    status.setText("🖼️ Generated Image")
                                    status.setStyleSheet("""
                                        color: #e0e0e0; 
                                        font-family: 'Courier New', monospace;
                                        background-color: #000000;
                                        padding: 5px;
                                        border-radius: 4px;
                                    """)
                        else:
                            # Select
                            self.unified_object_selector.add_image_selection(image_path)
                            self._update_all_unified_selectors()
                            self.logger.debug(f"✅ Added image to selection: {image_path.name}")
                            
                            # Visual feedback for selection (get current accent color)
                            from PySide6.QtCore import QSettings
                            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
                            accent_color = settings.value("interface/accent_color", "#4CAF50")
                            
                            placeholder.setStyleSheet(f"""
                                QLabel {{
                                    background-color: #000000;
                                    border: 3px solid {accent_color};
                                    border-radius: 8px;
                                    padding: 4px;
                                }}
                            """)
                            
                            # Update status to show selected (if status widget exists)
                            if hasattr(self, 'image_cards') and index in self.image_cards:
                                status = self.image_cards[index].get('status')
                                if status:
                                    status.setText("✅ Selected for 3D Generation")
                                    status.setStyleSheet("""
                                        color: #4CAF50; 
                                        font-weight: bold;
                                        font-family: 'Courier New', monospace;
                                        background-color: #000000;
                                        padding: 5px;
                                        border-radius: 4px;
                                    """)
                    else:
                        self.logger.warning("Unified object selector not available")
                else:
                    self.logger.warning(f"No image path found for card {index}")
            else:
                self.logger.info(f"Card {index} clicked but no image generated yet")
                
        except Exception as e:
            self.logger.error(f"Error handling image card click: {e}")
    
    def _load_image_when_generated(self, index: int, image_path: Path):
        """Load actual image when generation completes"""
        try:
            if hasattr(self, 'image_cards') and index in self.image_cards:
                placeholder = self.image_cards[index]['placeholder']
                status = self.image_cards[index].get('status')
                
                # Stop ASCII loading animation first
                self._stop_ascii_loading_animation(index)
                
                # Load and display the actual image
                from PySide6.QtGui import QPixmap
                if image_path.exists():
                    pixmap = QPixmap(str(image_path))
                    if not pixmap.isNull():
                        # Use the display size we calculated during card creation
                        if 'display_size' in self.image_cards[index]:
                            display_width, display_height = self.image_cards[index]['display_size']
                            display_size = QSize(display_width, display_height)
                        else:
                            display_size = placeholder.size()
                        
                        scaled_pixmap = pixmap.scaled(display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        placeholder.setPixmap(scaled_pixmap)
                        placeholder.setText("")  # Clear loading text
                        
                        # Store image path for selection
                        placeholder.image_path = image_path
                        
                        # Update status (if status widget exists)
                        if status:
                            status.setText("💫 Generated - Click to Select")
                        
                        # Don't auto-show delete button anymore - it's contextual on selection
                        
                        # Update placeholder style for image display (with accent color)
                        from PySide6.QtCore import QSettings
                        settings = QSettings("ComfyUI-Cinema4D", "Bridge")
                        accent_color = settings.value("interface/accent_color", "#4CAF50")
                        
                        placeholder.setStyleSheet(f"""
                            QLabel {{
                                background-color: #000000;
                                border: 1px solid {accent_color};
                                border-radius: 8px;
                                padding: 4px;
                            }}
                        """)
                        
                        self.logger.info(f"✅ Loaded generated image in card {index}: {image_path.name}")
                        return True
                        
                self.logger.error(f"Failed to load image for card {index}: {image_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading image in card {index}: {e}")
            return False
    
    
            
    def _on_main_tab_changed(self, index: int):
        """Handle main tab change"""
        tab_names = ["Image Generation", "3D Model Generation", "Texture Generation", "Cinema4D Intelligence"]
        if index < len(tab_names):
            self.logger.info(f"Switched to {tab_names[index]} tab")
            
        # Sync side panels
        self._sync_panel_tabs(index)
    
    def _sync_panel_tabs(self, index: int):
        """Sync left and right panels with main tab selection"""
        try:
            # Update left panel stack to match main tab
            if hasattr(self, 'left_panel_stack'):
                self.left_panel_stack.setCurrentIndex(index)
                self.logger.info(f"Synced left panel to index {index}")
            
            # Update right panel stack to match main tab  
            if hasattr(self, 'right_panel_stack'):
                self.right_panel_stack.setCurrentIndex(index)
                self.logger.info(f"Synced right panel to index {index}")
                
            # Force update selection displays when switching tabs
            self._update_selection_displays()
            
            # Ensure object manager lists are visible
            if index == 1:  # 3D Model Generation tab
                if hasattr(self, 'selected_images_list'):
                    self.selected_images_list.show()
                    self.selected_images_list.setVisible(True)
                    self.logger.info("Made selected images list visible for 3D generation")
                    
            elif index == 2:  # Texture Generation tab  
                if hasattr(self, 'selected_models_list'):
                    self.selected_models_list.show()
                    self.selected_models_list.setVisible(True)
                    self.logger.info("Made selected models list visible for texture generation")
                    
        except Exception as e:
            self.logger.error(f"Error syncing panel tabs: {e}")
        
    # Menu action implementations
    def _new_project(self):
        """Create new project"""
        self.logger.info("Creating new project...")
        
    def _open_project(self):
        """Open existing project"""
        self.logger.info("Opening project...")
        
    def _save_project(self):
        """Save current project"""
        self.logger.info("Saving project...")
        
    def _open_settings(self):
        """Open settings dialog"""
        self.logger.info("Opening settings...")
        
    def _undo(self):
        """Undo last action"""
        if self.undo_stack:
            self.logger.info("Undo performed")
        else:
            self.logger.info("Nothing to undo", "warning")
            
    def _redo(self):
        """Redo last undone action"""
        if self.redo_stack:
            self.logger.info("Redo performed")
        else:
            self.logger.info("Nothing to redo", "warning")
            
    def _open_preferences(self):
        """Open preferences dialog"""
        self.logger.info("Opening preferences...")
        
    def _refresh_all_connections(self):
        """Refresh all MCP connections"""
        self.logger.info("Refreshing all connections...")
        self._refresh_comfyui_connection()
        self._refresh_cinema4d_connection()
        
    def _toggle_console(self, checked: bool):
        """Toggle console visibility"""
        if hasattr(self, 'console_container'):
            self.console_container.setVisible(checked)
            
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def _open_documentation(self):
        """Open documentation"""
        self.logger.info("Opening documentation...")
        
    def _show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About ComfyUI → Cinema4D Bridge",
            "Professional pipeline tool for AI-generated content creation\n\n"
            "Terminal aesthetic design with complete functionality preservation\n"
            "Version: 2.0 Redesigned"
        )
    
    def _open_recent_project(self, project_path: str):
        """Open a recent project file"""
        try:
            self.logger.info(f"Opening recent project: {project_path}")
            # TODO: Implement actual project loading logic
            # For now, just show a confirmation
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Open Recent Project",
                f"Opening project:\n{project_path}\n\n(Implementation pending)"
            )
        except Exception as e:
            self.logger.error(f"Failed to open recent project {project_path}: {e}")
    
    def _clear_recent_projects(self):
        """Clear the recent projects list"""
        try:
            self.logger.info("Clearing recent projects list...")
            # TODO: Implement actual recent projects clearing
            # For now, just show a confirmation
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Clear Recent Projects",
                "Are you sure you want to clear the recent projects list?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.logger.info("Recent projects list cleared")
                QMessageBox.information(self, "Clear Recent", "Recent projects list cleared successfully.")
        except Exception as e:
            self.logger.error(f"Failed to clear recent projects: {e}")
    
    # Settings menu implementations
    def _open_general_settings(self):
        """Open general settings dialog"""
        self.logger.info("Opening general settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "General Settings", "General Settings dialog\n(Implementation pending)")
    
    def _open_appearance_settings(self):
        """Open theme and appearance settings"""
        self.logger.info("Opening appearance settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Theme & Appearance", "Theme & Appearance settings\n(Implementation pending)")
    
    def _open_connection_settings(self):
        """Open connection settings dialog"""
        self.logger.info("Opening connection settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Connection Settings", "Connection Settings dialog\n(Implementation pending)")
    
    def _open_comfyui_settings(self):
        """Open ComfyUI configuration dialog"""
        self.logger.info("Opening ComfyUI settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "ComfyUI Configuration", "ComfyUI Configuration dialog\n(Implementation pending)")
    
    def _open_c4d_settings(self):
        """Open Cinema4D configuration dialog"""
        self.logger.info("Opening Cinema4D settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Cinema4D Configuration", "Cinema4D Configuration dialog\n(Implementation pending)")
    
    def _open_workflow_settings(self):
        """Open workflow settings dialog"""
        self.logger.info("Opening workflow settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Workflow Settings", "Workflow Settings dialog\n(Implementation pending)")
    
    def _open_performance_settings(self):
        """Open performance settings dialog"""
        self.logger.info("Opening performance settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Performance Settings", "Performance Settings dialog\n(Implementation pending)")
    
    def _open_logging_settings(self):
        """Open logging and debug settings"""
        self.logger.info("Opening logging settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Logging & Debug", "Logging & Debug settings\n(Implementation pending)")
    
    def _open_advanced_settings(self):
        """Open advanced settings dialog"""
        self.logger.info("Opening advanced settings...")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Advanced Settings", "Advanced Settings dialog\n(Implementation pending)")
    
    def _reset_settings_to_defaults(self):
        """Reset all settings to default values"""
        try:
            self.logger.info("Resetting settings to defaults...")
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Reset Settings",
                "Are you sure you want to reset all settings to default values?\n\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # TODO: Implement actual settings reset
                self.logger.info("Settings reset to defaults")
                QMessageBox.information(self, "Reset Complete", "All settings have been reset to default values.\n\nRestart the application for changes to take effect.")
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
    
    def _open_environment_variables(self):
        """Open environment variables dialog"""
        try:
            self.logger.info("Opening environment variables dialog...")
            from src.ui.env_dialog import EnvironmentVariablesDialog
            
            dialog = EnvironmentVariablesDialog(self.config, self)
            dialog.env_updated.connect(self._on_environment_updated)
            
            result = dialog.exec()
            self.logger.info(f"Environment variables dialog closed with result: {result}")
            
        except Exception as e:
            self.logger.error(f"Failed to open environment variables dialog: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open environment variables dialog:\n{e}")
    
    def _on_environment_updated(self):
        """Handle environment variables being updated"""
        self.logger.info("Environment variables have been updated")
        # TODO: Refresh any components that depend on environment variables
    
    def _open_application_settings(self):
        """Open application settings dialog"""
        try:
            self.logger.info("Opening application settings dialog...")
            from src.ui.settings_dialog import ApplicationSettingsDialog
            
            dialog = ApplicationSettingsDialog(self.config, self)
            dialog.settings_updated.connect(self._on_settings_updated)
            
            result = dialog.exec()
            self.logger.info(f"Application settings dialog closed with result: {result}")
            
        except Exception as e:
            self.logger.error(f"Failed to open application settings dialog: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open application settings dialog:\n{e}")
    
    def _on_settings_updated(self):
        """Handle application settings being updated"""
        self.logger.info("Application settings have been updated")
        # TODO: Apply new settings to the application
    
    def _open_github_documentation(self):
        """Open GitHub documentation in browser"""
        try:
            import webbrowser
            github_url = "https://github.com/anthropics/claude-code"  # Replace with actual repo URL
            webbrowser.open(github_url)
            self.logger.info(f"Opening GitHub documentation: {github_url}")
        except Exception as e:
            self.logger.error(f"Failed to open GitHub documentation: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Documentation", "GitHub Documentation\n\nPlease visit: https://github.com/anthropics/claude-code")
    
    def _show_magic_prompts_database(self):
        """Show Magic Prompts Database dialog"""
        try:
            from src.ui.magic_prompts_dialog import MagicPromptsDialog
            dialog = MagicPromptsDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Failed to open Magic Prompts Database: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open Magic Prompts Database:\n{e}")
    
    def _show_magic_prompts_dialog(self, prompt_type: str):
        """Show magic prompts selection dialog for positive or negative prompts"""
        try:
            from src.ui.magic_prompts_selector import MagicPromptsSelector
            dialog = MagicPromptsSelector(prompt_type, self)
            if dialog.exec() == QDialog.Accepted:
                selected_template = dialog.get_selected_template()
                if selected_template:
                    # Insert template into appropriate prompt widget
                    if prompt_type == 'positive' and hasattr(self, 'positive_prompt'):
                        current_text = self.positive_prompt.get_prompt()
                        if current_text:
                            self.positive_prompt.set_text(current_text + "\n" + selected_template)
                        else:
                            self.positive_prompt.set_text(selected_template)
                    elif prompt_type == 'negative' and hasattr(self, 'negative_prompt'):
                        current_text = self.negative_prompt.get_prompt()
                        if current_text:
                            self.negative_prompt.set_text(current_text + "\n" + selected_template)
                        else:
                            self.negative_prompt.set_text(selected_template)
                    
                    self.logger.info(f"Inserted {prompt_type} magic prompt template")
        except Exception as e:
            self.logger.error(f"Failed to show magic prompts dialog: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to show magic prompts:\n{e}")
    
    def eventFilter(self, watched, event):
        """Handle events for installed filters"""
        from PySide6.QtCore import QEvent
        
        # Handle viewport resize events for responsive image layout
        if (hasattr(self, 'preview_scroll_area') and 
            watched == self.preview_scroll_area.viewport() and 
            event.type() == QEvent.Resize):
            # Debounce resize events with a timer
            if not hasattr(self, '_resize_timer'):
                from PySide6.QtCore import QTimer
                self._resize_timer = QTimer()
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self._handle_viewport_resize)
            
            # Restart timer on each resize event (debounce)
            self._resize_timer.stop()
            self._resize_timer.start(100)  # 100ms debounce
        
        return super().eventFilter(watched, event) if hasattr(super(), 'eventFilter') else False
    
    def _handle_viewport_resize(self):
        """Handle viewport resize to update image layout"""
        if hasattr(self, 'current_batch_size') and self.current_batch_size > 0:
            # Re-create preview with new viewport dimensions
            self._update_batch_preview(self.current_batch_size)
            
            # If we have loaded images, reload them into the new cards
            if hasattr(self, 'image_cards'):
                # Store loaded images temporarily
                loaded_images = {}
                for idx, card_info in self.image_cards.items():
                    placeholder = card_info.get('placeholder')
                    if placeholder and hasattr(placeholder, 'image_path'):
                        loaded_images[idx] = placeholder.image_path
                
                # Reload images into new cards
                for idx, image_path in loaded_images.items():
                    if image_path.exists():
                        self._load_image_when_generated(idx, image_path)
    
    def _delete_image(self, index: int):
        """Delete an image from the card and optionally from disk"""
        try:
            if hasattr(self, 'image_cards') and index in self.image_cards:
                card_info = self.image_cards[index]
                placeholder = card_info['placeholder']
                delete_btn = card_info.get('delete_btn')
                
                # Get image path if exists
                image_path = getattr(placeholder, 'image_path', None)
                
                if image_path and image_path.exists():
                    # Ask user for confirmation
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self,
                        "Delete Image",
                        f"Delete this image?\n{image_path.name}\n\nThis will remove the file from disk.",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Delete the file
                        try:
                            image_path.unlink()
                            self.logger.info(f"Deleted image file: {image_path}")
                        except Exception as e:
                            self.logger.error(f"Failed to delete file: {e}")
                            return
                        
                        # Reset the card to ready state
                        placeholder.clear()
                        if 'expected_size' in card_info:
                            w, h = card_info['expected_size']
                            placeholder.setText(f"Ready for {w}x{h}")
                        else:
                            placeholder.setText(f"Ready for Image {index}")
                        placeholder.setStyleSheet("""
                            QLabel {
                                background-color: #000000;
                                border: 1px solid #333333;
                                border-radius: 8px;
                                color: #666666;
                                font-family: 'Courier New', monospace;
                                font-size: 12px;
                                padding: 20px;
                            }
                        """)
                        
                        # Hide delete button and reset selection
                        if delete_btn:
                            delete_btn.hide()
                        card_info['selected'] = False
                        
                        # Clear image path
                        if hasattr(placeholder, 'image_path'):
                            delattr(placeholder, 'image_path')
                        
                        # Refresh the all images grid if visible
                        if hasattr(self, 'all_images_grid'):
                            self._refresh_all_images()
                            
                        self.logger.info(f"Reset card {index} after deletion")
                        
        except Exception as e:
            self.logger.error(f"Error deleting image: {e}")
    
    def _get_friendly_node_title(self, node_type: str, node_id: str, custom_title: str = "") -> str:
        """Get a title for a node - using technical names as requested"""
        if custom_title and custom_title.strip():
            return f"{custom_title} ({node_type})"
        
        # Provide descriptive names for common nodes
        friendly_names = {
            'KSampler': 'Sampling Settings',
            'UNETLoader': 'Model Loader',
            'VAELoader': 'VAE Loader', 
            'QuadrupleCLIPLoader': 'CLIP Loader',
            'CheckpointLoaderSimple': 'Checkpoint Loader',
            'LoraLoader': 'LoRA Loader',
            'ModelSamplingSD3': 'Model Sampling',
            'FluxGuidance': 'Guidance Scale',
            'EmptySD3LatentImage': 'Latent Image Settings',
            'Hy3DModelLoader': '3D Model Loader',
            'Hy3DGenerateMesh': '3D Mesh Generation',
            'Hy3DDelightImage': '3D Delight Processing',
            'ImageResize+': 'Image Resize',
            'SolidMask': 'Mask Settings',
            'LoadImage': 'Image Input'
        }
        
        friendly_name = friendly_names.get(node_type, node_type)
        return f"{friendly_name} #{node_id}"
    
    def _on_node_bypass_changed(self, node_id: str, node_type: str, state: int):
        """Handle bypass checkbox state change"""
        is_bypassed = state == Qt.Checked
        self.logger.info(f"Node {node_id} ({node_type}) bypass: {is_bypassed}")
        
        # Store bypass state for workflow execution
        if not hasattr(self, 'node_bypass_states'):
            self.node_bypass_states = {}
        self.node_bypass_states[node_id] = is_bypassed
        
        # Update UI to show bypassed state
        if is_bypassed:
            # Find the group box and update its style
            for i in range(self.dynamic_params_layout.count()):
                widget = self.dynamic_params_layout.itemAt(i).widget()
                if widget and widget.property("node_id") == node_id:
                    widget.setStyleSheet("""
                        QGroupBox {
                            opacity: 0.5;
                            background-color: rgba(0, 0, 0, 0.1);
                        }
                    """)
                    break
    
    def _on_remove_node_clicked(self, node_id: str, node_type: str):
        """Handle remove node button click"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Remove Node",
            f"Remove {node_type} node #{node_id} from workflow?\n\nThis will permanently modify the workflow.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logger.info(f"Removing node {node_id} ({node_type}) from workflow")
            
            # Remove from UI
            for i in range(self.dynamic_params_layout.count()):
                widget = self.dynamic_params_layout.itemAt(i).widget()
                if widget and widget.property("node_id") == node_id:
                    widget.setParent(None)
                    widget.deleteLater()
                    break
            
            # Store removal for workflow execution
            if not hasattr(self, 'removed_nodes'):
                self.removed_nodes = []
            self.removed_nodes.append(node_id)
            
            # TODO: Update workflow file to actually remove the node
            self.logger.warning("Node removal from workflow file not yet implemented")
    
    def _create_note_display_widget(self, note_text: str, title: str = "Note", node_type: str = "Note") -> QWidget:
        """Create a styled display widget for Note/MarkdownNote nodes"""
        container = QWidget()
        container.setObjectName("note_display")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)
        
        # Create a frame for the note
        frame = QFrame()
        frame.setObjectName("note_frame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(15, 10, 15, 10)
        frame_layout.setSpacing(8)
        
        # Title label if provided
        if title and title != "Note":
            title_label = QLabel(f"[{title}]")
            title_label.setObjectName("note_title")
            title_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-weight: bold;
                    font-size: 14px;
                    font-family: 'Courier New', monospace;
                }
            """)
            frame_layout.addWidget(title_label)
        
        # Note content
        if node_type == "MarkdownNote":
            # For markdown, we'll do basic formatting
            content_widget = QTextEdit()
            content_widget.setReadOnly(True)
            content_widget.setPlainText(note_text)
            
            # Basic markdown styling
            content_widget.setStyleSheet("""
                QTextEdit {
                    background-color: #0a0a0a;
                    color: #a0a0a0;
                    border: none;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    padding: 10px;
                }
            """)
            
            # Calculate height based on content
            doc = content_widget.document()
            doc.setTextWidth(400)
            height = doc.size().height() + 20
            content_widget.setFixedHeight(min(int(height), 300))  # Max height 300px
            
        else:
            # Regular note - simple text
            content_widget = QLabel(note_text)
            content_widget.setWordWrap(True)
            content_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content_widget.setStyleSheet("""
                QLabel {
                    color: #a0a0a0;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    padding: 10px;
                    background-color: #0a0a0a;
                    border-radius: 4px;
                }
            """)
        
        frame_layout.addWidget(content_widget)
        
        # Style the frame
        frame.setStyleSheet("""
            QFrame#note_frame {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-left: 3px solid #4CAF50;
                border-radius: 6px;
            }
        """)
        
        layout.addWidget(frame)
        
        return container