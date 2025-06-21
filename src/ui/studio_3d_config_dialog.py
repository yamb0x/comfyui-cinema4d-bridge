"""
Studio 3D Viewer Configuration Dialog
Provides UI controls for configuring 3D viewer rendering parameters
"""

import json
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QSlider, QCheckBox, QComboBox, QPushButton,
    QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from loguru import logger


class Studio3DConfigDialog(QDialog):
    """Configuration dialog for Studio 3D viewer settings"""
    
    # Signal emitted when settings are saved
    settings_saved = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Studio3DConfigDialog: Initializing...")
        
        try:
            self.setWindowTitle("3D Viewer Configuration")
            self.setModal(True)
            self.resize(900, 600)  # Optimized width for 400x400 preview
            
            # Set window flags to ensure dialog stays on top and is visible
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            
            logger.info("Studio3DConfigDialog: Window properties set")
            
            # Load current settings
            self.settings_file = Path("viewer/studio_viewer_settings.json")
            self.settings = self._load_settings()
            logger.info("Studio3DConfigDialog: Settings loaded")
            
            self._setup_ui()
            logger.info("Studio3DConfigDialog: UI setup complete")
            
            self._load_current_values()
            logger.info("Studio3DConfigDialog: Current values loaded")
            
            # Connect live preview after UI is set up
            self._connect_live_preview_updates()
            logger.info("Studio3DConfigDialog: Live preview connected")
            
            # Trigger initial preview update with a longer delay
            QTimer.singleShot(1000, self._do_update_preview)
            logger.info("Studio3DConfigDialog: Initialization complete")
            
        except Exception as e:
            logger.error(f"Studio3DConfigDialog: Error during initialization: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        logger.info("Studio3DConfigDialog: closeEvent called")
        import traceback
        logger.info(f"Stack trace: {traceback.format_stack()}")
        super().closeEvent(event)
    
    def reject(self):
        """Handle dialog rejection"""
        logger.info("Studio3DConfigDialog: reject() called")
        import traceback
        logger.info(f"Stack trace: {traceback.format_stack()}")
        super().reject()
    
    def _load_settings(self):
        """Load settings from JSON file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            else:
                # Default settings
                return {
                    "sliders": {
                        "ambientIntensity": 0.6,
                        "keyIntensity": 2.6,
                        "keyPosX": 9.3,
                        "keyPosY": 5.1,
                        "keyPosZ": 8.2,
                        "shadowSoftness": 10.0,
                        "fillIntensity": 1.2,
                        "fillPosX": 0.3,
                        "fillPosY": 3.0,
                        "fillPosZ": -5.0,
                        "rimIntensity": 0.4,
                        "materialMetalness": 0.9,
                        "materialRoughness": 1.2,
                        "envMapIntensity": 2.8,
                        "materialEmissive": 0.0,
                        "cameraFov": 19.0,
                        "cameraDistance": 7.8,
                        "cameraHeight": 2.0,
                        "cameraNear": 0.1,
                        "cameraFar": 100.0,
                        "rotateSpeed": 0.15,
                        "dampingFactor": 0.05,
                        "bloomStrength": 1.0,
                        "bloomRadius": 0.4,
                        "bloomThreshold": 0.85,
                        "exposure": 1.4,
                        "floorMetalness": 0.1,
                        "floorRoughness": 0.8,
                        "modelOffsetY": 0.0,
                        "axesSize": 1.0
                    },
                    "checkboxes": {
                        "shadows": False,
                        "autoRotate": True,
                        "bloom": True,
                        "floor": False,
                        "grid": True,
                        "axes": True
                    },
                    "combos": {
                        "toneMapping": "None",
                        "background": "Black"
                    }
                }
        except Exception as e:
            logger.error(f"Failed to load 3D viewer settings: {e}")
            return {}
    
    def _setup_ui(self):
        """Setup the user interface with live preview"""
        layout = QHBoxLayout(self)
        
        # Left side: Configuration tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Create tabbed interface
        tabs = QTabWidget()
        
        # Lighting tab
        lighting_tab = self._create_lighting_tab()
        tabs.addTab(lighting_tab, "Lighting")
        
        # Camera tab
        camera_tab = self._create_camera_tab()
        tabs.addTab(camera_tab, "Camera")
        
        # Material tab
        material_tab = self._create_material_tab()
        tabs.addTab(material_tab, "Material")
        
        # Effects tab
        effects_tab = self._create_effects_tab()
        tabs.addTab(effects_tab, "Effects")
        
        left_layout.addWidget(tabs)
        
        # Buttons at bottom of left side
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save & Apply")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        left_layout.addLayout(button_layout)
        left_widget.setFixedWidth(450)  # Fixed width for controls
        
        # Right side: Live preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Preview title
        preview_title = QLabel("Live Preview")
        preview_title.setObjectName("section_title")
        preview_title.setStyleSheet("""
            QLabel { 
                color: #4CAF50; 
                font-size: 14px; 
                font-weight: bold; 
                padding: 8px; 
                text-align: center;
            }
        """)
        preview_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(preview_title)
        
        # Live 3D viewer preview
        try:
            from ui.viewers.threejs_3d_viewer import ThreeJS3DViewer
            self.preview_viewer = ThreeJS3DViewer(parent=self, width=400, height=400)
            
            # Start the server first
            self.preview_viewer.start_server()
            
            # Load a test model if available (delayed to ensure server is ready)
            QTimer.singleShot(500, self._load_test_model_for_preview)
        except Exception as e:
            logger.error(f"Failed to create preview viewer: {e}")
            # Create a placeholder widget if viewer fails
            self.preview_viewer = QWidget()
            self.preview_viewer.setFixedSize(400, 400)
            self.preview_viewer.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")
        
        right_layout.addWidget(self.preview_viewer)
        
        # Add manual update button
        self.update_preview_btn = QPushButton("Update Preview")
        self.update_preview_btn.clicked.connect(self._update_live_preview)
        right_layout.addWidget(self.update_preview_btn)
        
        right_layout.addStretch()
        
        # Add both sides to main layout
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
    
    def _create_lighting_tab(self):
        """Create lighting configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Ambient lighting
        ambient_group = QGroupBox("Ambient Lighting")
        ambient_layout = QGridLayout(ambient_group)
        
        self.ambient_intensity = self._create_slider("Ambient Intensity", 0.0, 3.0, 0.01)
        ambient_layout.addWidget(QLabel("Intensity:"), 0, 0)
        ambient_layout.addWidget(self.ambient_intensity, 0, 1)
        
        layout.addWidget(ambient_group)
        
        # Key lighting
        key_group = QGroupBox("Key Light")
        key_layout = QGridLayout(key_group)
        
        self.key_intensity = self._create_slider("Key Intensity", 0.0, 5.0, 0.01)
        self.key_pos_x = self._create_slider("Key X Position", -20.0, 20.0, 0.1)
        self.key_pos_y = self._create_slider("Key Y Position", -20.0, 20.0, 0.1)
        self.key_pos_z = self._create_slider("Key Z Position", -20.0, 20.0, 0.1)
        
        key_layout.addWidget(QLabel("Intensity:"), 0, 0)
        key_layout.addWidget(self.key_intensity, 0, 1)
        key_layout.addWidget(QLabel("X Position:"), 1, 0)
        key_layout.addWidget(self.key_pos_x, 1, 1)
        key_layout.addWidget(QLabel("Y Position:"), 2, 0)
        key_layout.addWidget(self.key_pos_y, 2, 1)
        key_layout.addWidget(QLabel("Z Position:"), 3, 0)
        key_layout.addWidget(self.key_pos_z, 3, 1)
        
        layout.addWidget(key_group)
        
        # Fill lighting
        fill_group = QGroupBox("Fill Light")
        fill_layout = QGridLayout(fill_group)
        
        self.fill_intensity = self._create_slider("Fill Intensity", 0.0, 3.0, 0.01)
        self.fill_pos_x = self._create_slider("Fill X Position", -20.0, 20.0, 0.1)
        self.fill_pos_y = self._create_slider("Fill Y Position", -20.0, 20.0, 0.1)
        self.fill_pos_z = self._create_slider("Fill Z Position", -20.0, 20.0, 0.1)
        
        fill_layout.addWidget(QLabel("Intensity:"), 0, 0)
        fill_layout.addWidget(self.fill_intensity, 0, 1)
        fill_layout.addWidget(QLabel("X Position:"), 1, 0)
        fill_layout.addWidget(self.fill_pos_x, 1, 1)
        fill_layout.addWidget(QLabel("Y Position:"), 2, 0)
        fill_layout.addWidget(self.fill_pos_y, 2, 1)
        fill_layout.addWidget(QLabel("Z Position:"), 3, 0)
        fill_layout.addWidget(self.fill_pos_z, 3, 1)
        
        layout.addWidget(fill_group)
        
        # Rim lighting
        rim_group = QGroupBox("Rim Light")
        rim_layout = QGridLayout(rim_group)
        
        self.rim_intensity = self._create_slider("Rim Intensity", 0.0, 2.0, 0.01)
        
        rim_layout.addWidget(QLabel("Intensity:"), 0, 0)
        rim_layout.addWidget(self.rim_intensity, 0, 1)
        
        layout.addWidget(rim_group)
        
        # Shadows
        shadow_group = QGroupBox("Shadows")
        shadow_layout = QGridLayout(shadow_group)
        
        self.shadows_enabled = QCheckBox("Enable Shadows")
        self.shadow_softness = self._create_slider("Shadow Softness", 0.0, 20.0, 0.1)
        
        shadow_layout.addWidget(self.shadows_enabled, 0, 0, 1, 2)
        shadow_layout.addWidget(QLabel("Softness:"), 1, 0)
        shadow_layout.addWidget(self.shadow_softness, 1, 1)
        
        layout.addWidget(shadow_group)
        
        layout.addStretch()
        return widget
    
    def _create_camera_tab(self):
        """Create camera configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Camera settings
        camera_group = QGroupBox("Camera Settings")
        camera_layout = QGridLayout(camera_group)
        
        self.camera_fov = self._create_slider("Field of View", 10.0, 120.0, 1.0)
        self.camera_distance = self._create_slider("Distance", 1.0, 20.0, 0.1)
        self.camera_height = self._create_slider("Height", -10.0, 10.0, 0.1)
        self.camera_near = self._create_slider("Near Plane", 0.01, 1.0, 0.01)
        self.camera_far = self._create_slider("Far Plane", 10.0, 1000.0, 1.0)
        
        camera_layout.addWidget(QLabel("Field of View:"), 0, 0)
        camera_layout.addWidget(self.camera_fov, 0, 1)
        camera_layout.addWidget(QLabel("Distance:"), 1, 0)
        camera_layout.addWidget(self.camera_distance, 1, 1)
        camera_layout.addWidget(QLabel("Height:"), 2, 0)
        camera_layout.addWidget(self.camera_height, 2, 1)
        camera_layout.addWidget(QLabel("Near Plane:"), 3, 0)
        camera_layout.addWidget(self.camera_near, 3, 1)
        camera_layout.addWidget(QLabel("Far Plane:"), 4, 0)
        camera_layout.addWidget(self.camera_far, 4, 1)
        
        layout.addWidget(camera_group)
        
        # Controls
        controls_group = QGroupBox("Camera Controls")
        controls_layout = QGridLayout(controls_group)
        
        self.auto_rotate = QCheckBox("Auto Rotate")
        self.rotate_speed = self._create_slider("Rotation Speed", 0.0, 2.0, 0.01)
        self.damping_factor = self._create_slider("Damping Factor", 0.0, 0.2, 0.01)
        
        controls_layout.addWidget(self.auto_rotate, 0, 0, 1, 2)
        controls_layout.addWidget(QLabel("Rotation Speed:"), 1, 0)
        controls_layout.addWidget(self.rotate_speed, 1, 1)
        controls_layout.addWidget(QLabel("Damping Factor:"), 2, 0)
        controls_layout.addWidget(self.damping_factor, 2, 1)
        
        layout.addWidget(controls_group)
        
        layout.addStretch()
        return widget
    
    def _create_material_tab(self):
        """Create material configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Material properties
        material_group = QGroupBox("Material Properties")
        material_layout = QGridLayout(material_group)
        
        self.material_metalness = self._create_slider("Metalness", 0.0, 1.0, 0.01)
        self.material_roughness = self._create_slider("Roughness", 0.0, 2.0, 0.01)
        self.material_emissive = self._create_slider("Emissive", 0.0, 1.0, 0.01)
        self.env_map_intensity = self._create_slider("Environment Intensity", 0.0, 5.0, 0.01)
        
        material_layout.addWidget(QLabel("Metalness:"), 0, 0)
        material_layout.addWidget(self.material_metalness, 0, 1)
        material_layout.addWidget(QLabel("Roughness:"), 1, 0)
        material_layout.addWidget(self.material_roughness, 1, 1)
        material_layout.addWidget(QLabel("Emissive:"), 2, 0)
        material_layout.addWidget(self.material_emissive, 2, 1)
        material_layout.addWidget(QLabel("Environment:"), 3, 0)
        material_layout.addWidget(self.env_map_intensity, 3, 1)
        
        layout.addWidget(material_group)
        
        # Model positioning
        model_group = QGroupBox("Model Position")
        model_layout = QGridLayout(model_group)
        
        self.model_offset_y = self._create_slider("Y Offset", -5.0, 5.0, 0.1)
        
        model_layout.addWidget(QLabel("Y Offset:"), 0, 0)
        model_layout.addWidget(self.model_offset_y, 0, 1)
        
        layout.addWidget(model_group)
        
        # Floor settings
        floor_group = QGroupBox("Floor")
        floor_layout = QGridLayout(floor_group)
        
        self.floor_enabled = QCheckBox("Show Floor")
        self.floor_metalness = self._create_slider("Floor Metalness", 0.0, 1.0, 0.01)
        self.floor_roughness = self._create_slider("Floor Roughness", 0.0, 1.0, 0.01)
        
        floor_layout.addWidget(self.floor_enabled, 0, 0, 1, 2)
        floor_layout.addWidget(QLabel("Metalness:"), 1, 0)
        floor_layout.addWidget(self.floor_metalness, 1, 1)
        floor_layout.addWidget(QLabel("Roughness:"), 2, 0)
        floor_layout.addWidget(self.floor_roughness, 2, 1)
        
        layout.addWidget(floor_group)
        
        layout.addStretch()
        return widget
    
    def _create_effects_tab(self):
        """Create effects configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Post-processing
        post_group = QGroupBox("Post-Processing")
        post_layout = QGridLayout(post_group)
        
        self.bloom_enabled = QCheckBox("Enable Bloom")
        self.bloom_strength = self._create_slider("Bloom Strength", 0.0, 3.0, 0.01)
        self.bloom_radius = self._create_slider("Bloom Radius", 0.0, 1.0, 0.01)
        self.bloom_threshold = self._create_slider("Bloom Threshold", 0.0, 2.0, 0.01)
        self.exposure = self._create_slider("Exposure", 0.0, 3.0, 0.01)
        
        post_layout.addWidget(self.bloom_enabled, 0, 0, 1, 2)
        post_layout.addWidget(QLabel("Strength:"), 1, 0)
        post_layout.addWidget(self.bloom_strength, 1, 1)
        post_layout.addWidget(QLabel("Radius:"), 2, 0)
        post_layout.addWidget(self.bloom_radius, 2, 1)
        post_layout.addWidget(QLabel("Threshold:"), 3, 0)
        post_layout.addWidget(self.bloom_threshold, 3, 1)
        post_layout.addWidget(QLabel("Exposure:"), 4, 0)
        post_layout.addWidget(self.exposure, 4, 1)
        
        layout.addWidget(post_group)
        
        # Scene settings
        scene_group = QGroupBox("Scene")
        scene_layout = QGridLayout(scene_group)
        
        self.grid_enabled = QCheckBox("Show Grid")
        self.axes_enabled = QCheckBox("Show World Axes")
        self.axes_size = self._create_slider("Axes Size", 0.05, 5.0, 0.05)
        
        # Background combo
        self.background_combo = QComboBox()
        self.background_combo.addItems(["Black", "White", "Gray", "Blue"])
        
        # Tone mapping combo
        self.tone_mapping_combo = QComboBox()
        self.tone_mapping_combo.addItems(["None", "Linear", "Reinhard", "Cineon", "ACESFilmic"])
        
        scene_layout.addWidget(self.grid_enabled, 0, 0, 1, 2)
        scene_layout.addWidget(self.axes_enabled, 1, 0, 1, 2)
        scene_layout.addWidget(QLabel("Axes Size:"), 2, 0)
        scene_layout.addWidget(self.axes_size, 2, 1)
        scene_layout.addWidget(QLabel("Background:"), 3, 0)
        scene_layout.addWidget(self.background_combo, 3, 1)
        scene_layout.addWidget(QLabel("Tone Mapping:"), 4, 0)
        scene_layout.addWidget(self.tone_mapping_combo, 4, 1)
        
        layout.addWidget(scene_group)
        
        layout.addStretch()
        return widget
    
    def _create_slider(self, name, min_val, max_val, step):
        """Create a slider with value display"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val / step))
        slider.setMaximum(int(max_val / step))
        slider.setValue(int(min_val / step))
        
        value_label = QLabel(f"{min_val:.2f}")
        value_label.setMinimumWidth(50)
        
        def update_label(value):
            actual_value = value * step
            value_label.setText(f"{actual_value:.2f}")
        
        slider.valueChanged.connect(update_label)
        
        layout.addWidget(slider)
        layout.addWidget(value_label)
        
        # Store references for easy access
        container.slider = slider
        container.label = value_label
        container.step = step
        
        return container
    
    def _load_current_values(self):
        """Load current values into UI controls"""
        sliders = self.settings.get("sliders", {})
        checkboxes = self.settings.get("checkboxes", {})
        combos = self.settings.get("combos", {})
        
        # Load slider values
        slider_mappings = {
            "ambientIntensity": self.ambient_intensity,
            "keyIntensity": self.key_intensity,
            "keyPosX": self.key_pos_x,
            "keyPosY": self.key_pos_y,
            "keyPosZ": self.key_pos_z,
            "shadowSoftness": self.shadow_softness,
            "fillIntensity": self.fill_intensity,
            "fillPosX": self.fill_pos_x,
            "fillPosY": self.fill_pos_y,
            "fillPosZ": self.fill_pos_z,
            "rimIntensity": self.rim_intensity,
            "materialMetalness": self.material_metalness,
            "materialRoughness": self.material_roughness,
            "envMapIntensity": self.env_map_intensity,
            "materialEmissive": self.material_emissive,
            "cameraFov": self.camera_fov,
            "cameraDistance": self.camera_distance,
            "cameraHeight": self.camera_height,
            "cameraNear": self.camera_near,
            "cameraFar": self.camera_far,
            "rotateSpeed": self.rotate_speed,
            "dampingFactor": self.damping_factor,
            "bloomStrength": self.bloom_strength,
            "bloomRadius": self.bloom_radius,
            "bloomThreshold": self.bloom_threshold,
            "exposure": self.exposure,
            "floorMetalness": self.floor_metalness,
            "floorRoughness": self.floor_roughness,
            "modelOffsetY": self.model_offset_y,
            "axesSize": self.axes_size
        }
        
        for key, widget in slider_mappings.items():
            if key in sliders:
                value = sliders[key]
                slider_value = int(value / widget.step)
                widget.slider.setValue(slider_value)
        
        # Load checkbox values
        checkbox_mappings = {
            "shadows": self.shadows_enabled,
            "autoRotate": self.auto_rotate,
            "bloom": self.bloom_enabled,
            "floor": self.floor_enabled,
            "grid": self.grid_enabled,
            "axes": self.axes_enabled
        }
        
        for key, widget in checkbox_mappings.items():
            if key in checkboxes:
                widget.setChecked(checkboxes[key])
        
        # Load combo values
        if "background" in combos:
            index = self.background_combo.findText(combos["background"])
            if index >= 0:
                self.background_combo.setCurrentIndex(index)
        
        if "toneMapping" in combos:
            index = self.tone_mapping_combo.findText(combos["toneMapping"])
            if index >= 0:
                self.tone_mapping_combo.setCurrentIndex(index)
    
    def _get_current_settings(self):
        """Get current settings from UI controls"""
        # Get slider values
        sliders = {
            "ambientIntensity": self.ambient_intensity.slider.value() * self.ambient_intensity.step,
            "keyIntensity": self.key_intensity.slider.value() * self.key_intensity.step,
            "keyPosX": self.key_pos_x.slider.value() * self.key_pos_x.step,
            "keyPosY": self.key_pos_y.slider.value() * self.key_pos_y.step,
            "keyPosZ": self.key_pos_z.slider.value() * self.key_pos_z.step,
            "shadowSoftness": self.shadow_softness.slider.value() * self.shadow_softness.step,
            "fillIntensity": self.fill_intensity.slider.value() * self.fill_intensity.step,
            "fillPosX": self.fill_pos_x.slider.value() * self.fill_pos_x.step,
            "fillPosY": self.fill_pos_y.slider.value() * self.fill_pos_y.step,
            "fillPosZ": self.fill_pos_z.slider.value() * self.fill_pos_z.step,
            "rimIntensity": self.rim_intensity.slider.value() * self.rim_intensity.step,
            "materialMetalness": self.material_metalness.slider.value() * self.material_metalness.step,
            "materialRoughness": self.material_roughness.slider.value() * self.material_roughness.step,
            "envMapIntensity": self.env_map_intensity.slider.value() * self.env_map_intensity.step,
            "materialEmissive": self.material_emissive.slider.value() * self.material_emissive.step,
            "cameraFov": self.camera_fov.slider.value() * self.camera_fov.step,
            "cameraDistance": self.camera_distance.slider.value() * self.camera_distance.step,
            "cameraHeight": self.camera_height.slider.value() * self.camera_height.step,
            "cameraNear": self.camera_near.slider.value() * self.camera_near.step,
            "cameraFar": self.camera_far.slider.value() * self.camera_far.step,
            "rotateSpeed": self.rotate_speed.slider.value() * self.rotate_speed.step,
            "dampingFactor": self.damping_factor.slider.value() * self.damping_factor.step,
            "bloomStrength": self.bloom_strength.slider.value() * self.bloom_strength.step,
            "bloomRadius": self.bloom_radius.slider.value() * self.bloom_radius.step,
            "bloomThreshold": self.bloom_threshold.slider.value() * self.bloom_threshold.step,
            "exposure": self.exposure.slider.value() * self.exposure.step,
            "floorMetalness": self.floor_metalness.slider.value() * self.floor_metalness.step,
            "floorRoughness": self.floor_roughness.slider.value() * self.floor_roughness.step,
            "modelOffsetY": self.model_offset_y.slider.value() * self.model_offset_y.step,
            "axesSize": self.axes_size.slider.value() * self.axes_size.step
        }
        
        # Get checkbox values
        checkboxes = {
            "shadows": self.shadows_enabled.isChecked(),
            "autoRotate": self.auto_rotate.isChecked(),
            "bloom": self.bloom_enabled.isChecked(),
            "floor": self.floor_enabled.isChecked(),
            "grid": self.grid_enabled.isChecked(),
            "axes": self.axes_enabled.isChecked()
        }
        
        # Get combo values
        combos = {
            "background": self.background_combo.currentText(),
            "toneMapping": self.tone_mapping_combo.currentText()
        }
        
        return {
            "sliders": sliders,
            "checkboxes": checkboxes,
            "combos": combos
        }
    
    def _save_settings(self):
        """Save settings and emit signal"""
        try:
            settings = self._get_current_settings()
            
            # Apply settings to preview with save_to_file=True
            if hasattr(self, 'preview_viewer'):
                self.preview_viewer.apply_settings(settings, save_to_file=True)
            
            # Save to file
            self.settings_file.parent.mkdir(exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"3D viewer settings saved to {self.settings_file}")
            
            # Emit signal
            self.settings_saved.emit(settings)
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save 3D viewer settings: {e}")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        # Reset to default values and reload UI
        self.settings = self._load_settings()  # This loads defaults if file doesn't exist
        self._load_current_values()
        
    def _load_test_model_for_preview(self):
        """Load a test model for live preview"""
        try:
            # Try to find the latest 3D model from the monitored directory
            from pathlib import Path
            models_dir = Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D")
            
            if models_dir.exists():
                # Find the most recent .glb file
                glb_files = list(models_dir.glob("*.glb"))
                if glb_files:
                    latest_model = max(glb_files, key=lambda p: p.stat().st_mtime)
                    self.preview_viewer.load_model(str(latest_model))
                    logger.info(f"Loaded preview model: {latest_model.name}")
                    return
            
            # If no models found, the viewer will show a placeholder
            logger.info("No 3D models found for preview, showing placeholder")
            
        except Exception as e:
            logger.error(f"Failed to load test model for preview: {e}")
    
    def _connect_live_preview_updates(self):
        """Connect all sliders and controls to live preview updates"""
        # Create a timer for debounced updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_update_preview)
        
        # Connect all sliders to update the preview with debouncing
        slider_widgets = [
            self.ambient_intensity, self.key_intensity, self.key_pos_x, self.key_pos_y, self.key_pos_z,
            self.shadow_softness, self.fill_intensity, self.fill_pos_x, self.fill_pos_y, self.fill_pos_z, 
            self.rim_intensity, self.material_metalness, self.material_roughness, self.env_map_intensity, 
            self.material_emissive, self.model_offset_y, self.camera_fov, self.camera_distance, 
            self.camera_height, self.camera_near, self.camera_far, self.rotate_speed, self.damping_factor, 
            self.bloom_strength, self.bloom_radius, self.bloom_threshold, self.exposure, 
            self.floor_metalness, self.floor_roughness, self.axes_size
        ]
        
        for slider_widget in slider_widgets:
            if hasattr(slider_widget, 'slider'):
                slider_widget.slider.valueChanged.connect(self._request_preview_update)
        
        # Connect checkboxes
        checkbox_widgets = [
            self.shadows_enabled, self.auto_rotate, self.bloom_enabled, 
            self.floor_enabled, self.grid_enabled, self.axes_enabled
        ]
        
        for checkbox in checkbox_widgets:
            checkbox.toggled.connect(self._request_preview_update)
        
        # Connect combo boxes
        self.background_combo.currentTextChanged.connect(self._request_preview_update)
        self.tone_mapping_combo.currentTextChanged.connect(self._request_preview_update)
    
    def _request_preview_update(self):
        """Request a preview update with debouncing"""
        # Stop any pending update and start a new timer
        # This prevents rapid updates that might trigger ASCII animations
        self.update_timer.stop()
        self.update_timer.start(250)  # 250ms delay
    
    def _do_update_preview(self):
        """Actually perform the preview update"""
        try:
            if hasattr(self, 'preview_viewer'):
                current_settings = self._get_current_settings()
                logger.debug(f"Studio3DConfigDialog: Updating live preview with {len(current_settings.get('sliders', {}))} slider settings")
                self.preview_viewer.apply_settings(current_settings)
        except Exception as e:
            logger.error(f"Failed to update live preview: {e}")
    
    def _update_live_preview(self):
        """Update the live preview with current settings (for manual button)"""
        self._do_update_preview()