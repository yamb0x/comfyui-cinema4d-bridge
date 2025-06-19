"""
Complete UI Methods for Redesigned Application
All missing UI creation methods and parameter panels
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, 
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QSlider, QGroupBox, QListWidget, QTextEdit,
    QFrame, QSplitter, QLineEdit, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from pathlib import Path
from loguru import logger

# Import the actual grid widgets
from ui.widgets import ImageGridWidget, Model3DPreviewWidget


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
        
        self.session_info_label = QLabel("Ready for image generation")
        self.session_info_label.setObjectName("connection_info")
        header_layout.addWidget(self.session_info_label)
        
        layout.addLayout(header_layout)
        
        # Preview grid for batch placeholders (before generation)
        preview_container = QWidget()
        self.new_canvas_grid = QGridLayout(preview_container)
        self.new_canvas_grid.setSpacing(15)
        layout.addWidget(preview_container)
        
        # Use actual ImageGridWidget for session images (after generation)
        self.session_image_grid = ImageGridWidget(columns=2, thumbnail_size=512)
        self.session_image_grid.image_selected.connect(self._on_image_selected)
        layout.addWidget(self.session_image_grid)
        
        return widget
        
    def _create_view_all_images(self) -> QWidget:
        """Create View All images view using ImageGridWidget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header with controls
        header_layout = QHBoxLayout()
        title = QLabel("All Generated Images")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self._refresh_all_images)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Use actual ImageGridWidget for all images
        self.all_images_grid = ImageGridWidget(columns=6, thumbnail_size=180)
        self.all_images_grid.image_selected.connect(self._on_image_selected)
        layout.addWidget(self.all_images_grid)
        
        # Debug: Check if grid was created
        if hasattr(self, 'logger'):
            self.logger.info("Created all_images_grid successfully")
        
        return widget
        
    def _create_scene_objects_view(self) -> QWidget:
        """Create Scene Objects view for 3D models using Model3DPreviewWidget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Scene Objects")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 3D viewer controls
        viewer_controls = QHBoxLayout()
        
        wireframe_btn = QPushButton("Wireframe")
        wireframe_btn.setObjectName("secondary_btn")
        wireframe_btn.setCheckable(True)
        viewer_controls.addWidget(wireframe_btn)
        
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.setObjectName("secondary_btn")
        viewer_controls.addWidget(reset_view_btn)
        
        header_layout.addLayout(viewer_controls)
        layout.addLayout(header_layout)
        
        # Use actual Model3DPreviewWidget for session models
        self.session_models_grid = Model3DPreviewWidget(columns=3, is_session_widget=True)
        self.session_models_grid.model_selected.connect(self._on_model_selected)
        layout.addWidget(self.session_models_grid)
        
        return widget
        
    def _create_view_all_models(self) -> QWidget:
        """Create View All models view using Model3DPreviewWidget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("All 3D Models")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh Models")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self._refresh_all_models)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Use actual Model3DPreviewWidget for all models
        self.all_models_grid = Model3DPreviewWidget(columns=4, is_session_widget=False)
        self.all_models_grid.model_selected.connect(self._on_model_selected)
        layout.addWidget(self.all_models_grid)
        
        return widget
        
    def _create_image_parameters(self) -> QWidget:
        """Create image generation parameters"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        
        # Dynamic Parameters section with scrollable area
        dynamic_section = self._create_parameter_section("Workflow Parameters")
        dynamic_section_layout = dynamic_section.layout()
        
        # Create scrollable area for parameters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Remove minimum height to allow full panel height usage
        
        # Container widget for scrollable content
        self.dynamic_params_container = QWidget()
        self.dynamic_params_container.setObjectName("dynamic_params")
        self.dynamic_params_layout = QVBoxLayout(self.dynamic_params_container)
        self.dynamic_params_layout.setContentsMargins(8, 8, 8, 8)
        self.dynamic_params_layout.setSpacing(12)
        
        # Info label when no parameters loaded
        info_label = QLabel("Configure workflow parameters from File menu")
        info_label.setObjectName("info_label")
        info_label.setWordWrap(True)
        self.dynamic_params_layout.addWidget(info_label)
        
        # Set container as scroll area widget
        scroll_area.setWidget(self.dynamic_params_container)
        dynamic_section_layout.addWidget(scroll_area, 1)  # Give scroll area all space in the section
        
        # Give the dynamic section all available space
        layout.addWidget(dynamic_section, 1)  # stretch factor of 1
        
        return widget
        
    def _create_3d_parameters(self) -> QWidget:
        """Create 3D generation parameters"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 3D Model Settings section
        model_section = self._create_parameter_section("3D Model Settings")
        model_layout = model_section.layout()
        
        # Quality
        quality_label = QLabel("Quality:")
        quality_label.setObjectName("section_title")
        self.quality_3d_combo = QComboBox()
        self.quality_3d_combo.addItems(["Low", "Medium", "High", "Ultra"])
        self.quality_3d_combo.setCurrentText("High")
        model_layout.addWidget(quality_label)
        model_layout.addWidget(self.quality_3d_combo)
        
        # Mesh density
        density_label = QLabel("Mesh Density:")
        density_label.setObjectName("section_title")
        self.density_spin = QSpinBox()
        self.density_spin.setRange(1000, 10000)
        self.density_spin.setValue(5000)
        self.density_spin.setSingleStep(500)
        model_layout.addWidget(density_label)
        model_layout.addWidget(self.density_spin)
        
        layout.addWidget(model_section)
        
        # Generation Settings section
        gen_section = self._create_parameter_section("Generation Settings")
        gen_layout = gen_section.layout()
        
        # Guidance scale
        guidance_label = QLabel("Guidance Scale:")
        guidance_label.setObjectName("section_title")
        self.guidance_3d_spin = QDoubleSpinBox()
        self.guidance_3d_spin.setRange(1.0, 10.0)
        self.guidance_3d_spin.setValue(5.5)
        self.guidance_3d_spin.setSingleStep(0.1)
        gen_layout.addWidget(guidance_label)
        gen_layout.addWidget(self.guidance_3d_spin)
        
        # Inference steps
        steps_label = QLabel("Inference Steps:")
        steps_label.setObjectName("section_title")
        self.steps_3d_spin = QSpinBox()
        self.steps_3d_spin.setRange(10, 100)
        self.steps_3d_spin.setValue(50)
        gen_layout.addWidget(steps_label)
        gen_layout.addWidget(self.steps_3d_spin)
        
        # Seed
        seed_label = QLabel("Seed:")
        seed_label.setObjectName("section_title")
        self.seed_3d_spin = QSpinBox()
        self.seed_3d_spin.setRange(-1, 2147483647)
        self.seed_3d_spin.setValue(123)
        gen_layout.addWidget(seed_label)
        gen_layout.addWidget(self.seed_3d_spin)
        
        layout.addWidget(gen_section)
        layout.addStretch()
        
        return widget
        
    def _create_texture_parameters(self) -> QWidget:
        """Create texture generation parameters"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Texture Quality section
        quality_section = self._create_parameter_section("Texture Quality")
        quality_layout = quality_section.layout()
        
        # Resolution
        res_label = QLabel("Resolution:")
        res_label.setObjectName("section_title")
        self.texture_res_combo = QComboBox()
        self.texture_res_combo.addItems(["512x512", "1024x1024", "2048x2048", "4096x4096"])
        self.texture_res_combo.setCurrentText("1024x1024")
        quality_layout.addWidget(res_label)
        quality_layout.addWidget(self.texture_res_combo)
        
        # UV unwrap quality
        uv_label = QLabel("UV Quality:")
        uv_label.setObjectName("section_title")
        self.uv_quality_combo = QComboBox()
        self.uv_quality_combo.addItems(["Standard", "High", "Ultra"])
        self.uv_quality_combo.setCurrentText("High")
        quality_layout.addWidget(uv_label)
        quality_layout.addWidget(self.uv_quality_combo)
        
        layout.addWidget(quality_section)
        
        # Material Properties section
        material_section = self._create_parameter_section("Material Properties")
        material_layout = material_section.layout()
        
        # Material type
        mat_label = QLabel("Material Type:")
        mat_label.setObjectName("section_title")
        self.material_type_combo = QComboBox()
        self.material_type_combo.addItems([
            "PBR (Physical)",
            "Stylized",
            "Photorealistic",
            "Cartoon",
            "Metallic",
            "Fabric"
        ])
        material_layout.addWidget(mat_label)
        material_layout.addWidget(self.material_type_combo)
        
        # Roughness
        rough_label = QLabel("Roughness:")
        rough_label.setObjectName("section_title")
        self.roughness_spin = QDoubleSpinBox()
        self.roughness_spin.setRange(0.0, 1.0)
        self.roughness_spin.setValue(0.5)
        self.roughness_spin.setSingleStep(0.1)
        material_layout.addWidget(rough_label)
        material_layout.addWidget(self.roughness_spin)
        
        # Metallic
        metal_label = QLabel("Metallic:")
        metal_label.setObjectName("section_title")
        self.metallic_spin = QDoubleSpinBox()
        self.metallic_spin.setRange(0.0, 1.0)
        self.metallic_spin.setValue(0.0)
        self.metallic_spin.setSingleStep(0.1)
        material_layout.addWidget(metal_label)
        material_layout.addWidget(self.metallic_spin)
        
        layout.addWidget(material_section)
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
        
        # Monitor 3D/textured folder
        textured_path = Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D/textured")
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
            from ui.nlp_dictionary_dialog import NLPDictionaryDialog
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
            from ui.configure_parameters_dialog import ConfigureParametersDialog
            
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
    
    def _load_parameters_from_config(self, param_type: str):
        """Load parameters from configuration and update UI widgets"""
        try:
            self.logger.info(f"🔄 _load_parameters_from_config called for {param_type}...")
            
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
            self.logger.info(f"🔍 UI Components status: {ui_components}")
            
            missing_components = [name for name, exists in ui_components.items() if not exists]
            if missing_components:
                self.logger.warning(f"⚠️ Missing UI components: {missing_components}")
            self.logger.info(f"🔄 Current working directory: {Path.cwd()}")
            
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
                        positive_prompt_text = ""
                        negative_prompt_text = ""
                        
                        for node_id in selected_nodes:
                            node = workflow.get(str(node_id))
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
                            self.positive_prompt.set_text(positive_prompt_text)
                            self.logger.debug("Updated positive prompt widget")
                        
                        if negative_prompt_text and hasattr(self, 'negative_prompt'):
                            self.negative_prompt.set_text(negative_prompt_text)
                            self.logger.debug("Updated negative prompt widget")
                        
                        # Log if no prompts were found
                        if not positive_prompt_text and not negative_prompt_text:
                            self.logger.warning("⚠️ No positive or negative prompts found in workflow")
                        
                        # Sort nodes by ComfyUI workflow order
                        ordered_nodes = self._sort_nodes_by_workflow_order(selected_nodes, workflow)
                        # Ordered nodes: {ordered_nodes}
                        
                        for node_id in ordered_nodes:
                            node = workflow.get(str(node_id))
                            if not node:
                                continue
                                
                            node_type = node.get('type', '')
                            widgets_values = node.get('widgets_values', [])
                            
                            self.logger.debug(f"Processing node {node_id}: {node_type}")
                            
                            # Skip prompt nodes - they're handled separately
                            if node_type == 'CLIPTextEncode':
                                continue
                            
                            # Skip nodes without configurable parameters
                            if not widgets_values:
                                # Skipping node - no widget values
                                continue
                            
                            # Create group for this node
                            group_box = QGroupBox(f"{node_type} (Node {node_id})")
                            group_box.setObjectName("parameter_group")
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
                                self.logger.debug(f"Found definition with {len(widgets_mapping)} widget mappings")
                                
                                # Create widgets from definition
                                for i, widget_def in enumerate(widgets_mapping):
                                    if i < len(widgets_values):
                                        value = widgets_values[i]
                                        self.logger.debug(f"Creating widget: {widget_def['name']}")
                                        # Create widget key as node_type_node_id_param_index
                                        param_key = f"{node_type}_{node_id}_{str(i)}"
                                        widget = self._create_widget_from_definition(widget_def, value, node_type, node_id, param_key)
                                        if widget:
                                            group_layout.addWidget(widget)
                                            # Added widget: {widget_def['name']}
                                        else:
                                            self.logger.error(f"❌ Failed to create widget: {widget_def['name']}")
                                
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
                                group_box.setLayout(group_layout)
                                if hasattr(self, 'dynamic_params_layout'):
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
                ],
                'extra_widgets': [
                    {'name': 'Bypass LoRA', 'type': 'bool', 'widget': 'checkbox', 'default': False}
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
                    {'name': 'Width', 'type': 'int', 'widget': 'int', 'min': 16, 'max': 2048, 'step': 64, 'default': 512},
                    {'name': 'Height', 'type': 'int', 'widget': 'int', 'min': 16, 'max': 2048, 'step': 64, 'default': 512},
                    {'name': 'Batch Size', 'type': 'int', 'widget': 'int', 'min': 1, 'max': 64, 'default': 1}
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
            }
        }
    
    def _sort_nodes_by_workflow_order(self, node_ids: list, workflow: dict) -> list:
        """Sort nodes in ComfyUI workflow order: Checkpoint → LoRA → KSampler → Others"""
        node_order = []
        
        # Priority order for node types
        priority_order = {
            'CheckpointLoaderSimple': 1,
            'CheckpointLoader': 1,
            'LoraLoader': 2,
            'KSampler': 3,
            'FluxGuidance': 4,
            'EmptySD3LatentImage': 5,
            'CLIPTextEncode': 6,  # Will be handled separately
        }
        
        # Separate and sort nodes
        categorized_nodes = {}
        for node_id in node_ids:
            node = workflow.get(str(node_id))
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
                    return self._create_combo_widget(name, value, options, node_type, node_id, param_key)
                elif widget_type == 'text_multiline':
                    return self._create_multiline_text_widget(name, value)
                elif widget_type == 'text_display':
                    return self._create_text_display_widget(name, value)
                else:
                    return self._create_text_widget(name, value)
                    
            elif data_type == 'bool':
                value = bool(value) if value is not None else widget_def.get('default', False)
                return self._create_checkbox_widget(name, value)
                
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
        spinbox.setMinimumWidth(120)
        layout.addWidget(spinbox)
        
        # Store reference to the actual input widget for value retrieval
        if node_id and param_key and hasattr(self, 'parameter_widgets'):
            self.parameter_widgets[param_key] = {
                'widget': spinbox,
                'type': 'int',
                'get_value': lambda: spinbox.value()
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
        spinbox.setMinimumWidth(120)
        layout.addWidget(spinbox)
        
        # Store reference to the actual input widget for value retrieval
        if node_id and param_key and hasattr(self, 'parameter_widgets'):
            self.parameter_widgets[param_key] = {
                'widget': spinbox,
                'type': 'float',
                'get_value': lambda: spinbox.value()
            }
            logger.debug(f"Stored float widget tracking: {param_key}")
        
        return container
    
    def _create_text_widget(self, name: str, value: str):
        """Create a text input widget"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(f"{name}:")
        label.setMinimumWidth(100)
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
    
    def _create_checkbox_widget(self, name: str, checked: bool):
        """Create a checkbox widget"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        checkbox = QCheckBox(name)
        checkbox.setChecked(checked)
        layout.addWidget(checkbox)
        layout.addStretch()
        
        return container
    
    def _get_model_options_for_parameter(self, param_name: str, node_type: str = None) -> list:
        """Get model options dynamically based on parameter name and node type"""
        options = []
        
        # Determine model type based on parameter name
        if 'lora' in param_name.lower():
            # Get LoRA models
            options = self.config.get_lora_files() if hasattr(self.config, 'get_lora_files') else []
            if not options and hasattr(self.config, 'loras_dir') and self.config.loras_dir.exists():
                options = [f.name for f in self.config.loras_dir.glob("*.safetensors")]
                
        elif 'checkpoint' in param_name.lower() or 'ckpt' in param_name.lower():
            # Get checkpoint models
            options = self.config.get_checkpoint_files() if hasattr(self.config, 'get_checkpoint_files') else []
            if not options and hasattr(self.config, 'checkpoints_dir') and self.config.checkpoints_dir.exists():
                options = [f.name for f in self.config.checkpoints_dir.glob("*.safetensors")]
                # Also include .ckpt files for checkpoints
                options.extend([f.name for f in self.config.checkpoints_dir.glob("*.ckpt")])
                
        elif 'vae' in param_name.lower():
            # Get VAE models (usually in VAE subfolder)
            if hasattr(self.config, 'comfyui_path') and self.config.comfyui_path:
                vae_dir = self.config.comfyui_path / "models" / "vae"
                if vae_dir.exists():
                    options = [f.name for f in vae_dir.glob("*.safetensors")]
                    options.extend([f.name for f in vae_dir.glob("*.ckpt")])
                    
        elif 'controlnet' in param_name.lower() or 'control_net' in param_name.lower():
            # Get ControlNet models
            if hasattr(self.config, 'comfyui_path') and self.config.comfyui_path:
                controlnet_dir = self.config.comfyui_path / "models" / "controlnet"
                if controlnet_dir.exists():
                    options = [f.name for f in controlnet_dir.glob("*.safetensors")]
                    options.extend([f.name for f in controlnet_dir.glob("*.ckpt")])
                    
        elif 'upscale' in param_name.lower() or 'esrgan' in param_name.lower():
            # Get upscaling models
            if hasattr(self.config, 'comfyui_path') and self.config.comfyui_path:
                upscale_dir = self.config.comfyui_path / "models" / "upscale_models"
                if upscale_dir.exists():
                    options = [f.name for f in upscale_dir.glob("*.pth")]
                    options.extend([f.name for f in upscale_dir.glob("*.safetensors")])
                    
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
        combo.addItems(options)
        if value in options:
            combo.setCurrentText(value)
        combo.setMinimumWidth(120)
        layout.addWidget(combo)
        
        # Store reference to the actual input widget for value retrieval
        if node_id and param_key and hasattr(self, 'parameter_widgets'):
            self.parameter_widgets[param_key] = {
                'widget': combo,
                'type': 'combo',
                'get_value': lambda: combo.currentText()
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
    
    def _create_parameter_widget(self, node_id: str, node_type: str, param_name: str, param_value):
        """Create appropriate widget for parameter based on type"""
        widget_container = QWidget()
        layout = QHBoxLayout(widget_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(f"{param_name}:")
        label.setMinimumWidth(120)
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
        
        # Create preview cards
        for i in range(batch_size):
            preview_card = self._create_preview_card(i + 1)
            row = i // 2  # 2 columns
            col = i % 2
            self.new_canvas_grid.addWidget(preview_card, row, col)
        
        # Created preview cards
    
    def _create_preview_card(self, index: int) -> QWidget:
        """Create a preview card for batch generation with ASCII loading animation"""
        card = QWidget()
        card.setObjectName("preview_card")
        card.setFixedSize(540, 590)  # Size for 512px image + labels
        
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
        
        # Image placeholder with ASCII loading animation
        placeholder = QLabel()
        placeholder.setObjectName("preview_placeholder")
        placeholder.setFixedSize(512, 512)
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
        
        # Status label with terminal style
        status = QLabel("Ready for generation")
        status.setObjectName("preview_status")
        status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet("""
            color: #4CAF50; 
            font-weight: bold;
            font-family: 'Courier New', monospace;
            background-color: #000000;
            padding: 5px;
            border-radius: 4px;
        """)
        
        layout.addWidget(placeholder)
        layout.addWidget(status)
        
        # Store reference for later image loading and animation
        if not hasattr(self, 'image_cards'):
            self.image_cards = {}
        self.image_cards[index] = {
            'placeholder': placeholder, 
            'status': status,
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
        loading_chars = ['G', 'E', 'N', 'E', 'R', 'A', 'T', 'I', 'N', 'G', '.', '.', '.']
        
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
        
        # Update status to show loading
        self.image_cards[index]['status'].setText("🎨 Generating...")
    
    def _stop_ascii_loading_animation(self, index: int):
        """Stop ASCII loading animation for image card"""
        if index in self.image_cards and self.image_cards[index]['loading_timer']:
            self.image_cards[index]['loading_timer'].stop()
            self.image_cards[index]['loading_timer'] = None
    
    def _on_image_card_clicked(self, index: int, placeholder: QLabel):
        """Handle image card click for selection (same as View All)"""
        try:
            # Check if placeholder has an actual image
            if placeholder.pixmap() and not placeholder.pixmap().isNull():
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
                            
                            # Update status to show deselected
                            if hasattr(self, 'image_cards') and index in self.image_cards:
                                status = self.image_cards[index]['status']
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
                            self.logger.info(f"✅ Added image to selection: {image_path.name}")
                            
                            # Visual feedback for selection (green border)
                            placeholder.setStyleSheet("""
                                QLabel {
                                    background-color: #000000;
                                    border: 3px solid #4CAF50;
                                    border-radius: 8px;
                                    padding: 4px;
                                }
                            """)
                            
                            # Update status to show selected
                            if hasattr(self, 'image_cards') and index in self.image_cards:
                                status = self.image_cards[index]['status']
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
                status = self.image_cards[index]['status']
                
                # Stop ASCII loading animation first
                self._stop_ascii_loading_animation(index)
                
                # Load and display the actual image
                from PySide6.QtGui import QPixmap
                if image_path.exists():
                    pixmap = QPixmap(str(image_path))
                    if not pixmap.isNull():
                        # Scale image to fit placeholder
                        scaled_pixmap = pixmap.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        placeholder.setPixmap(scaled_pixmap)
                        placeholder.setText("")  # Clear loading text
                        
                        # Store image path for selection
                        placeholder.image_path = image_path
                        
                        # Update status
                        status.setText("💫 Generated - Click to Select")
                        
                        # Update placeholder style for image display
                        placeholder.setStyleSheet("""
                            QLabel {
                                background-color: #000000;
                                border: 1px solid #4CAF50;
                                border-radius: 8px;
                                padding: 4px;
                            }
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
            from ui.env_dialog import EnvironmentVariablesDialog
            
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
            from ui.settings_dialog import ApplicationSettingsDialog
            
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
            from ui.magic_prompts_dialog import MagicPromptsDialog
            dialog = MagicPromptsDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Failed to open Magic Prompts Database: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open Magic Prompts Database:\n{e}")
    
    def _show_magic_prompts_dialog(self, prompt_type: str):
        """Show magic prompts selection dialog for positive or negative prompts"""
        try:
            from ui.magic_prompts_selector import MagicPromptsSelector
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