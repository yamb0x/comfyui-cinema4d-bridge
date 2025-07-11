"""
Simple 3D Viewer Configuration Dialog
Rebuilt to use identical viewer representation as cards
"""

import json
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QSlider, QCheckBox, QComboBox, QPushButton,
    QGroupBox, QGridLayout, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from loguru import logger

from src.ui.viewers.threejs_3d_viewer import ThreeJS3DViewer


class Simple3DConfigDialog(QDialog):
    """Simple configuration dialog with identical 3D viewer representation"""
    
    # Signal emitted when settings are saved
    settings_saved = Signal(dict)
    
    def __init__(self, parent=None, model_path=None):
        super().__init__(parent)
        self.model_path = model_path
        self.current_settings = self._load_default_settings()
        
        # Setup debouncing timer for live preview updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_live_preview_update)
        self.update_debounce_ms = 150  # Wait 150ms before applying changes
        self.viewer_ready = False  # Track if viewer is ready for updates
        
        self.setWindowTitle("3D Viewer Configuration")
        self.setModal(True)
        self.resize(1500, 800)  # Bigger dialog to fit larger viewer
        
        self.setup_ui()
        
        # Load model if provided
        if self.model_path and Path(self.model_path).exists():
            self.viewer.load_model(self.model_path)
            logger.info(f"Loaded model in config dialog: {Path(self.model_path).name}")
            
            # Set viewer as ready after a short delay to allow model loading
            QTimer.singleShot(1000, lambda: setattr(self, 'viewer_ready', True))
    
    def setup_ui(self):
        """Setup the configuration dialog UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Left side: 3D viewer (identical to cards)
        viewer_widget = self._create_viewer_widget()
        layout.addWidget(viewer_widget)
        
        # Right side: Controls (includes buttons at bottom)
        controls_widget = self._create_controls_widget()
        layout.addWidget(controls_widget)
    
    def _create_viewer_widget(self) -> QWidget:
        """Create the 3D viewer widget (identical to cards)"""
        widget = QWidget()
        widget.setFixedSize(1024, 1024)  # Much larger viewer
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title = QLabel("Live Preview")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Create ThreeJS viewer (same as used in cards but much larger)
        self.viewer = ThreeJS3DViewer(widget, width=1008, height=980)  # Account for margins and title
        layout.addWidget(self.viewer)
        
        return widget
    
    def _create_controls_widget(self) -> QWidget:
        """Create the controls panel"""
        # Create scroll area for controls since we have many parameters
        scroll_area = QScrollArea()
        scroll_area.setFixedWidth(420)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Lighting controls
        lighting_group = self._create_lighting_controls()
        layout.addWidget(lighting_group)
        
        # Material controls
        material_group = self._create_material_controls()
        layout.addWidget(material_group)
        
        # Camera controls
        camera_group = self._create_camera_controls()
        layout.addWidget(camera_group)
        
        # Environment controls
        environment_group = self._create_environment_controls()
        layout.addWidget(environment_group)
        
        # Post-processing controls
        postprocessing_group = self._create_postprocessing_controls()
        layout.addWidget(postprocessing_group)
        
        # Advanced effects controls
        advanced_group = self._create_advanced_effects_controls()
        layout.addWidget(advanced_group)
        
        # Model controls
        model_group = self._create_model_controls()
        layout.addWidget(model_group)
        
        layout.addStretch()
        
        # Action buttons at the bottom
        buttons_group = self._create_action_buttons_group()
        layout.addWidget(buttons_group)
        
        # Set the widget as the scroll area's content
        scroll_area.setWidget(widget)
        
        return scroll_area
    
    def _create_lighting_controls(self) -> QGroupBox:
        """Create lighting controls group"""
        group = QGroupBox("Lighting")
        layout = QGridLayout(group)
        
        row = 0
        
        # Ambient Intensity
        layout.addWidget(QLabel("Ambient:"), row, 0)
        self.ambient_slider = self._create_slider(0, 200, int(self.current_settings["sliders"]["ambientIntensity"] * 100))
        layout.addWidget(self.ambient_slider, row, 1)
        row += 1
        
        # Key Light Intensity  
        layout.addWidget(QLabel("Key Light:"), row, 0)
        self.key_intensity_slider = self._create_slider(0, 500, int(self.current_settings["sliders"]["keyIntensity"] * 100))
        layout.addWidget(self.key_intensity_slider, row, 1)
        row += 1
        
        # Fill Light Intensity
        layout.addWidget(QLabel("Fill Light:"), row, 0)
        self.fill_intensity_slider = self._create_slider(0, 200, int(self.current_settings["sliders"]["fillIntensity"] * 100))
        layout.addWidget(self.fill_intensity_slider, row, 1)
        row += 1
        
        # Key Light Position X
        layout.addWidget(QLabel("Key Pos X:"), row, 0)
        self.key_pos_x_slider = self._create_slider(-20, 20, int(self.current_settings["sliders"]["keyPosX"]))
        layout.addWidget(self.key_pos_x_slider, row, 1)
        row += 1
        
        # Key Light Position Y
        layout.addWidget(QLabel("Key Pos Y:"), row, 0)
        self.key_pos_y_slider = self._create_slider(0, 20, int(self.current_settings["sliders"]["keyPosY"]))
        layout.addWidget(self.key_pos_y_slider, row, 1)
        row += 1
        
        # Key Light Position Z
        layout.addWidget(QLabel("Key Pos Z:"), row, 0)
        self.key_pos_z_slider = self._create_slider(-20, 20, int(self.current_settings["sliders"]["keyPosZ"]))
        layout.addWidget(self.key_pos_z_slider, row, 1)
        row += 1
        
        # Fill Light Position X
        layout.addWidget(QLabel("Fill Pos X:"), row, 0)
        self.fill_pos_x_slider = self._create_slider(-20, 20, int(self.current_settings["sliders"]["fillPosX"]))
        layout.addWidget(self.fill_pos_x_slider, row, 1)
        row += 1
        
        # Fill Light Position Y
        layout.addWidget(QLabel("Fill Pos Y:"), row, 0)
        self.fill_pos_y_slider = self._create_slider(0, 20, int(self.current_settings["sliders"].get("fillPosY", 5)))
        layout.addWidget(self.fill_pos_y_slider, row, 1)
        row += 1
        
        # Fill Light Position Z
        layout.addWidget(QLabel("Fill Pos Z:"), row, 0)
        self.fill_pos_z_slider = self._create_slider(-20, 20, int(self.current_settings["sliders"].get("fillPosZ", -3)))
        layout.addWidget(self.fill_pos_z_slider, row, 1)
        row += 1
        
        # Rim Light Intensity
        layout.addWidget(QLabel("Rim Light:"), row, 0)
        self.rim_intensity_slider = self._create_slider(0, 200, int(self.current_settings["sliders"]["rimIntensity"] * 100))
        layout.addWidget(self.rim_intensity_slider, row, 1)
        row += 1
        
        # Shadow Softness
        layout.addWidget(QLabel("Shadow Soft:"), row, 0)
        self.shadow_softness_slider = self._create_slider(1, 50, int(self.current_settings["sliders"]["shadowSoftness"]))
        layout.addWidget(self.shadow_softness_slider, row, 1)
        row += 1
        
        # Shadows
        self.shadows_checkbox = QCheckBox("Enable Shadows")
        self.shadows_checkbox.setChecked(self.current_settings["checkboxes"]["shadows"])
        layout.addWidget(self.shadows_checkbox, row, 0, 1, 2)
        row += 1
        
        # Connect signals for live preview (use sliderReleased to avoid continuous firing)
        self.ambient_slider.sliderReleased.connect(self._update_live_preview)
        self.key_intensity_slider.sliderReleased.connect(self._update_live_preview)
        self.fill_intensity_slider.sliderReleased.connect(self._update_live_preview)
        self.key_pos_x_slider.sliderReleased.connect(self._update_live_preview)
        self.key_pos_y_slider.sliderReleased.connect(self._update_live_preview)
        self.key_pos_z_slider.sliderReleased.connect(self._update_live_preview)
        self.fill_pos_x_slider.sliderReleased.connect(self._update_live_preview)
        self.fill_pos_y_slider.sliderReleased.connect(self._update_live_preview)
        self.fill_pos_z_slider.sliderReleased.connect(self._update_live_preview)
        self.rim_intensity_slider.sliderReleased.connect(self._update_live_preview)
        self.shadow_softness_slider.sliderReleased.connect(self._update_live_preview)
        self.shadows_checkbox.toggled.connect(self._update_live_preview)
        
        return group
    
    def _create_material_controls(self) -> QGroupBox:
        """Create material controls group"""
        group = QGroupBox("Material")
        layout = QGridLayout(group)
        
        row = 0
        
        # Metalness
        layout.addWidget(QLabel("Metalness:"), row, 0)
        self.metalness_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["materialMetalness"] * 100))
        layout.addWidget(self.metalness_slider, row, 1)
        row += 1
        
        # Roughness
        layout.addWidget(QLabel("Roughness:"), row, 0)
        self.roughness_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["materialRoughness"] * 100))
        layout.addWidget(self.roughness_slider, row, 1)
        row += 1
        
        # Environment Map Intensity
        layout.addWidget(QLabel("Env Map:"), row, 0)
        self.env_map_slider = self._create_slider(0, 500, int(self.current_settings["sliders"]["envMapIntensity"] * 100))
        layout.addWidget(self.env_map_slider, row, 1)
        row += 1
        
        # Material Emissive
        layout.addWidget(QLabel("Emissive:"), row, 0)
        self.emissive_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["materialEmissive"] * 100))
        layout.addWidget(self.emissive_slider, row, 1)
        row += 1
        
        # Connect signals (use sliderReleased to avoid continuous firing)
        self.metalness_slider.sliderReleased.connect(self._update_live_preview)
        self.roughness_slider.sliderReleased.connect(self._update_live_preview)
        self.env_map_slider.sliderReleased.connect(self._update_live_preview)
        self.emissive_slider.sliderReleased.connect(self._update_live_preview)
        
        return group
    
    def _create_camera_controls(self) -> QGroupBox:
        """Create camera controls group"""
        group = QGroupBox("Camera")
        layout = QGridLayout(group)
        
        row = 0
        
        # Auto Rotate
        self.auto_rotate_checkbox = QCheckBox("Auto Rotate")
        self.auto_rotate_checkbox.setChecked(self.current_settings["checkboxes"]["autoRotate"])
        layout.addWidget(self.auto_rotate_checkbox, row, 0, 1, 2)
        row += 1
        
        # FOV
        layout.addWidget(QLabel("Field of View:"), row, 0)
        self.fov_slider = self._create_slider(10, 90, int(self.current_settings["sliders"]["cameraFov"]))
        layout.addWidget(self.fov_slider, row, 1)
        row += 1
        
        # Camera Distance
        layout.addWidget(QLabel("Distance:"), row, 0)
        self.distance_slider = self._create_slider(1, 20, int(self.current_settings["sliders"]["cameraDistance"] * 2))
        layout.addWidget(self.distance_slider, row, 1)
        row += 1
        
        # Camera Height
        layout.addWidget(QLabel("Height:"), row, 0)
        self.height_slider = self._create_slider(0, 20, int(self.current_settings["sliders"]["cameraHeight"] * 2))
        layout.addWidget(self.height_slider, row, 1)
        row += 1
        
        # Camera Near
        layout.addWidget(QLabel("Near Clip:"), row, 0)
        self.near_slider = self._create_slider(1, 100, int(self.current_settings["sliders"]["cameraNear"] * 100))
        layout.addWidget(self.near_slider, row, 1)
        row += 1
        
        # Camera Far
        layout.addWidget(QLabel("Far Clip:"), row, 0)
        self.far_slider = self._create_slider(10, 1000, int(self.current_settings["sliders"]["cameraFar"]))
        layout.addWidget(self.far_slider, row, 1)
        row += 1
        
        # Rotate Speed
        layout.addWidget(QLabel("Rotate Speed:"), row, 0)
        self.rotate_speed_slider = self._create_slider(1, 100, int(self.current_settings["sliders"]["rotateSpeed"] * 100))
        layout.addWidget(self.rotate_speed_slider, row, 1)
        row += 1
        
        # Damping Factor
        layout.addWidget(QLabel("Damping:"), row, 0)
        self.damping_slider = self._create_slider(1, 50, int(self.current_settings["sliders"]["dampingFactor"] * 1000))
        layout.addWidget(self.damping_slider, row, 1)
        row += 1
        
        # Connect signals (use sliderReleased to avoid continuous firing)
        self.auto_rotate_checkbox.toggled.connect(self._update_live_preview)
        self.fov_slider.sliderReleased.connect(self._update_live_preview)
        self.distance_slider.sliderReleased.connect(self._update_live_preview)
        self.height_slider.sliderReleased.connect(self._update_live_preview)
        self.near_slider.sliderReleased.connect(self._update_live_preview)
        self.far_slider.sliderReleased.connect(self._update_live_preview)
        self.rotate_speed_slider.sliderReleased.connect(self._update_live_preview)
        self.damping_slider.sliderReleased.connect(self._update_live_preview)
        
        return group
    
    def _create_environment_controls(self) -> QGroupBox:
        """Create environment controls group"""
        group = QGroupBox("Environment")
        layout = QGridLayout(group)
        
        row = 0
        
        # Background
        layout.addWidget(QLabel("Background:"), row, 0)
        self.background_combo = QComboBox()
        self.background_combo.addItems(["Pure Black", "Black", "Dark Gray", "Gray", "White", "Studio Blue"])
        current_bg = self.current_settings["combos"]["background"]
        if current_bg in ["Pure Black", "Black", "Dark Gray", "Gray", "White", "Studio Blue"]:
            self.background_combo.setCurrentText(current_bg)
        layout.addWidget(self.background_combo, row, 1)
        row += 1
        
        # Floor
        self.floor_checkbox = QCheckBox("Show Floor")
        self.floor_checkbox.setChecked(self.current_settings["checkboxes"]["floor"])
        layout.addWidget(self.floor_checkbox, row, 0, 1, 2)
        row += 1
        
        # Grid
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(self.current_settings["checkboxes"]["grid"])
        layout.addWidget(self.grid_checkbox, row, 0, 1, 2)
        row += 1
        
        # Floor Metalness
        layout.addWidget(QLabel("Floor Metal:"), row, 0)
        self.floor_metalness_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["floorMetalness"] * 100))
        layout.addWidget(self.floor_metalness_slider, row, 1)
        row += 1
        
        # Floor Roughness
        layout.addWidget(QLabel("Floor Rough:"), row, 0)
        self.floor_roughness_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["floorRoughness"] * 100))
        layout.addWidget(self.floor_roughness_slider, row, 1)
        row += 1
        
        # Grid Size
        layout.addWidget(QLabel("Grid Size:"), row, 0)
        self.grid_size_slider = self._create_slider(5, 50, int(self.current_settings["sliders"]["gridSize"]))
        layout.addWidget(self.grid_size_slider, row, 1)
        row += 1
        
        # Grid Divisions
        layout.addWidget(QLabel("Grid Divs:"), row, 0)
        self.grid_divisions_slider = self._create_slider(10, 100, int(self.current_settings["sliders"]["gridDivisions"]))
        layout.addWidget(self.grid_divisions_slider, row, 1)
        row += 1
        
        # Grid Opacity
        layout.addWidget(QLabel("Grid Alpha:"), row, 0)
        self.grid_opacity_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["gridOpacity"] * 100))
        layout.addWidget(self.grid_opacity_slider, row, 1)
        row += 1
        
        # Connect signals
        self.background_combo.currentTextChanged.connect(self._update_live_preview)
        self.floor_checkbox.toggled.connect(self._update_live_preview)
        self.grid_checkbox.toggled.connect(self._update_live_preview)
        self.floor_metalness_slider.sliderReleased.connect(self._update_live_preview)
        self.floor_roughness_slider.sliderReleased.connect(self._update_live_preview)
        self.grid_size_slider.sliderReleased.connect(self._update_live_preview)
        self.grid_divisions_slider.sliderReleased.connect(self._update_live_preview)
        self.grid_opacity_slider.sliderReleased.connect(self._update_live_preview)
        
        return group
    
    def _create_postprocessing_controls(self) -> QGroupBox:
        """Create post-processing controls group"""
        group = QGroupBox("Post-Processing")
        layout = QGridLayout(group)
        
        row = 0
        
        # Bloom Enable
        self.bloom_checkbox = QCheckBox("Enable Bloom")
        self.bloom_checkbox.setChecked(self.current_settings["checkboxes"]["bloom"])
        layout.addWidget(self.bloom_checkbox, row, 0, 1, 2)
        row += 1
        
        # Bloom Strength
        layout.addWidget(QLabel("Bloom Strength:"), row, 0)
        self.bloom_strength_slider = self._create_slider(0, 200, int(self.current_settings["sliders"]["bloomStrength"] * 100))
        layout.addWidget(self.bloom_strength_slider, row, 1)
        row += 1
        
        # Bloom Radius
        layout.addWidget(QLabel("Bloom Radius:"), row, 0)
        self.bloom_radius_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["bloomRadius"] * 100))
        layout.addWidget(self.bloom_radius_slider, row, 1)
        row += 1
        
        # Bloom Threshold
        layout.addWidget(QLabel("Bloom Threshold:"), row, 0)
        self.bloom_threshold_slider = self._create_slider(0, 100, int(self.current_settings["sliders"]["bloomThreshold"] * 100))
        layout.addWidget(self.bloom_threshold_slider, row, 1)
        row += 1
        
        # Exposure
        layout.addWidget(QLabel("Exposure:"), row, 0)
        self.exposure_slider = self._create_slider(0, 300, int(self.current_settings["sliders"]["exposure"] * 100))
        layout.addWidget(self.exposure_slider, row, 1)
        row += 1
        
        # Tone Mapping
        layout.addWidget(QLabel("Tone Mapping:"), row, 0)
        self.tone_mapping_combo = QComboBox()
        self.tone_mapping_combo.addItems(["None", "Linear", "Reinhard", "Cineon", "ACESFilmic"])
        current_tone = self.current_settings["combos"]["toneMapping"]
        if current_tone in ["None", "Linear", "Reinhard", "Cineon", "ACESFilmic"]:
            self.tone_mapping_combo.setCurrentText(current_tone)
        layout.addWidget(self.tone_mapping_combo, row, 1)
        row += 1
        
        # Connect signals
        self.bloom_checkbox.toggled.connect(self._update_live_preview)
        self.bloom_strength_slider.sliderReleased.connect(self._update_live_preview)
        self.bloom_radius_slider.sliderReleased.connect(self._update_live_preview)
        self.bloom_threshold_slider.sliderReleased.connect(self._update_live_preview)
        self.exposure_slider.sliderReleased.connect(self._update_live_preview)
        self.tone_mapping_combo.currentTextChanged.connect(self._update_live_preview)
        
        return group
    
    def _create_advanced_effects_controls(self) -> QGroupBox:
        """Create advanced effects controls group"""
        group = QGroupBox("Advanced Effects")
        layout = QGridLayout(group)
        
        row = 0
        
        # SSAO Enable
        self.ssao_checkbox = QCheckBox("Enable SSAO")
        self.ssao_checkbox.setChecked(self.current_settings.get("advanced_effects", {}).get("ssaoEnabled", False))
        layout.addWidget(self.ssao_checkbox, row, 0, 1, 2)
        row += 1
        
        # SSAO Intensity
        layout.addWidget(QLabel("SSAO Intensity:"), row, 0)
        self.ssao_intensity_slider = self._create_slider(0, 100, int(self.current_settings.get("advanced_effects", {}).get("ssaoIntensity", 0.5) * 100))
        layout.addWidget(self.ssao_intensity_slider, row, 1)
        row += 1
        
        # SSAO Radius
        layout.addWidget(QLabel("SSAO Radius:"), row, 0)
        self.ssao_radius_slider = self._create_slider(0, 100, int(self.current_settings.get("advanced_effects", {}).get("ssaoRadius", 0.3) * 100))
        layout.addWidget(self.ssao_radius_slider, row, 1)
        row += 1
        
        # SSAO Quality
        layout.addWidget(QLabel("SSAO Quality:"), row, 0)
        self.ssao_quality_slider = self._create_slider(8, 64, int(self.current_settings.get("advanced_effects", {}).get("ssaoQuality", 32)))
        layout.addWidget(self.ssao_quality_slider, row, 1)
        row += 1
        
        # FXAA Enable
        self.fxaa_checkbox = QCheckBox("Enable FXAA")
        self.fxaa_checkbox.setChecked(self.current_settings.get("advanced_effects", {}).get("fxaaEnabled", True))
        layout.addWidget(self.fxaa_checkbox, row, 0, 1, 2)
        row += 1
        
        # Temporal AA Enable
        self.temporal_aa_checkbox = QCheckBox("Enable Temporal AA")
        self.temporal_aa_checkbox.setChecked(self.current_settings.get("advanced_effects", {}).get("temporalAAEnabled", False))
        layout.addWidget(self.temporal_aa_checkbox, row, 0, 1, 2)
        row += 1
        
        # Connect signals
        self.ssao_checkbox.toggled.connect(self._update_live_preview)
        self.ssao_intensity_slider.sliderReleased.connect(self._update_live_preview)
        self.ssao_radius_slider.sliderReleased.connect(self._update_live_preview)
        self.ssao_quality_slider.sliderReleased.connect(self._update_live_preview)
        self.fxaa_checkbox.toggled.connect(self._update_live_preview)
        self.temporal_aa_checkbox.toggled.connect(self._update_live_preview)
        
        return group
    
    def _create_model_controls(self) -> QGroupBox:
        """Create model controls group"""
        group = QGroupBox("Model & Misc")
        layout = QGridLayout(group)
        
        row = 0
        
        # Model Offset Y
        layout.addWidget(QLabel("Y Offset:"), row, 0)
        self.model_offset_y_slider = self._create_slider(-100, 100, int(self.current_settings["sliders"].get("modelOffsetY", 0) * 100))
        layout.addWidget(self.model_offset_y_slider, row, 1)
        row += 1
        
        # Axes Size
        layout.addWidget(QLabel("Axes Size:"), row, 0)
        self.axes_size_slider = self._create_slider(0, 100, int(self.current_settings["sliders"].get("axesSize", 0.5) * 100))
        layout.addWidget(self.axes_size_slider, row, 1)
        row += 1
        
        # Connect signals
        self.model_offset_y_slider.sliderReleased.connect(self._update_live_preview)
        self.axes_size_slider.sliderReleased.connect(self._update_live_preview)
        
        return group
    
    def _create_slider(self, min_val: int, max_val: int, current_val: int) -> QSlider:
        """Create a slider with standard settings"""
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(current_val)
        slider.setFixedWidth(200)
        return slider
    
    def _create_action_buttons_group(self) -> QGroupBox:
        """Create action buttons group at bottom of controls"""
        group = QGroupBox("Actions")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Apply button (test settings without closing)
        apply_btn = QPushButton("Apply to All Viewers")
        apply_btn.setMinimumSize(200, 40)
        apply_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                font-weight: bold;
                padding: 8px 16px; 
                background-color: #2196F3; 
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        apply_btn.clicked.connect(self._apply_settings)
        layout.addWidget(apply_btn)
        
        # Save button (save and close)
        save_btn = QPushButton("Save & Close")
        save_btn.setMinimumSize(200, 40)
        save_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                font-weight: bold;
                padding: 8px 16px; 
                background-color: #4CAF50; 
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #1B5E20;
            }
        """)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_and_close)
        layout.addWidget(save_btn)
        
        # Cancel button (close without saving)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumSize(200, 35)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px; 
                padding: 6px 16px; 
                background-color: #757575; 
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        return group
    
    def _load_default_settings(self) -> dict:
        """Load default 3D viewer settings"""
        default_settings = {
            "sliders": {
                "ambientIntensity": 0.4,
                "keyIntensity": 1.2,
                "keyPosX": 5,
                "keyPosY": 8,
                "keyPosZ": 5,
                "shadowSoftness": 1,
                "fillIntensity": 0.6,
                "fillPosX": -5,
                "fillPosY": 5,
                "fillPosZ": -3,
                "rimIntensity": 0.4,
                "materialMetalness": 1.0,
                "materialRoughness": 1.0,
                "envMapIntensity": 1.0,
                "materialEmissive": 0.0,
                "cameraFov": 35,
                "cameraDistance": 3,
                "cameraHeight": 2,
                "cameraNear": 0.1,
                "cameraFar": 100,
                "rotateSpeed": 1.0,
                "dampingFactor": 0.05,
                "bloomStrength": 0.3,
                "bloomRadius": 0.4,
                "bloomThreshold": 0.85,
                "exposure": 1.0,
                "floorMetalness": 0.1,
                "floorRoughness": 0.8,
                "gridSize": 20,
                "gridDivisions": 40,
                "gridOpacity": 0.3,
                "modelOffsetY": 0.0,
                "axesSize": 0.5
            },
            "checkboxes": {
                "shadows": True,
                "autoRotate": True,
                "bloom": True,
                "floor": True,
                "grid": True
            },
            "combos": {
                "toneMapping": "ACESFilmic",
                "background": "Dark Gray"
            },
            "advanced_effects": {
                "ssaoEnabled": False,
                "ssaoIntensity": 0.5,
                "ssaoRadius": 0.3,
                "ssaoQuality": 32.0,
                "fxaaEnabled": True,
                "temporalAAEnabled": False
            }
        }
        
        # Try to load existing settings
        settings_file = Path("viewer/studio_viewer_settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    logger.info(f"Loaded settings from file: ambient={loaded_settings.get('sliders', {}).get('ambientIntensity', 'missing')}")
                    # Merge with defaults
                    for key in default_settings:
                        if key in loaded_settings:
                            default_settings[key].update(loaded_settings[key])
                    logger.info(f"Final merged settings: ambient={default_settings['sliders']['ambientIntensity']}")
            except Exception as e:
                logger.error(f"Error loading existing settings: {e}")
        else:
            logger.warning(f"Settings file not found: {settings_file}")
        
        return default_settings
    
    def _get_current_settings(self) -> dict:
        """Get current settings from UI controls"""
        return {
            "sliders": {
                # Lighting
                "ambientIntensity": self.ambient_slider.value() / 100.0,
                "keyIntensity": self.key_intensity_slider.value() / 100.0,
                "keyPosX": self.key_pos_x_slider.value(),
                "keyPosY": self.key_pos_y_slider.value(),
                "keyPosZ": self.key_pos_z_slider.value(),
                "shadowSoftness": self.shadow_softness_slider.value(),
                "fillIntensity": self.fill_intensity_slider.value() / 100.0,
                "fillPosX": self.fill_pos_x_slider.value(),
                "fillPosY": self.fill_pos_y_slider.value(),
                "fillPosZ": self.fill_pos_z_slider.value(),
                "rimIntensity": self.rim_intensity_slider.value() / 100.0,
                # Material
                "materialMetalness": self.metalness_slider.value() / 100.0,
                "materialRoughness": self.roughness_slider.value() / 100.0,
                "envMapIntensity": self.env_map_slider.value() / 100.0,
                "materialEmissive": self.emissive_slider.value() / 100.0,
                # Camera
                "cameraFov": self.fov_slider.value(),
                "cameraDistance": self.distance_slider.value() / 2.0,
                "cameraHeight": self.height_slider.value() / 2.0,
                "cameraNear": self.near_slider.value() / 100.0,
                "cameraFar": self.far_slider.value(),
                "rotateSpeed": self.rotate_speed_slider.value() / 100.0,
                "dampingFactor": self.damping_slider.value() / 1000.0,
                # Post-processing
                "bloomStrength": self.bloom_strength_slider.value() / 100.0,
                "bloomRadius": self.bloom_radius_slider.value() / 100.0,
                "bloomThreshold": self.bloom_threshold_slider.value() / 100.0,
                "exposure": self.exposure_slider.value() / 100.0,
                # Environment
                "floorMetalness": self.floor_metalness_slider.value() / 100.0,
                "floorRoughness": self.floor_roughness_slider.value() / 100.0,
                "gridSize": self.grid_size_slider.value(),
                "gridDivisions": self.grid_divisions_slider.value(),
                "gridOpacity": self.grid_opacity_slider.value() / 100.0,
                # Model
                "modelOffsetY": self.model_offset_y_slider.value() / 100.0,
                "axesSize": self.axes_size_slider.value() / 100.0
            },
            "checkboxes": {
                "shadows": self.shadows_checkbox.isChecked(),
                "autoRotate": self.auto_rotate_checkbox.isChecked(),
                "bloom": self.bloom_checkbox.isChecked(),
                "floor": self.floor_checkbox.isChecked(),
                "grid": self.grid_checkbox.isChecked()
            },
            "combos": {
                "toneMapping": self.tone_mapping_combo.currentText(),
                "background": self.background_combo.currentText()
            },
            "advanced_effects": {
                "ssaoEnabled": self.ssao_checkbox.isChecked(),
                "ssaoIntensity": self.ssao_intensity_slider.value() / 100.0,
                "ssaoRadius": self.ssao_radius_slider.value() / 100.0,
                "ssaoQuality": float(self.ssao_quality_slider.value()),
                "fxaaEnabled": self.fxaa_checkbox.isChecked(),
                "temporalAAEnabled": self.temporal_aa_checkbox.isChecked()
            }
        }
    
    def _update_live_preview(self):
        """Trigger debounced live preview update"""
        # Stop any pending update and start a new timer
        self.update_timer.stop()
        self.update_timer.start(self.update_debounce_ms)
    
    def _do_live_preview_update(self):
        """Actually perform the live preview update (called after debounce delay)"""
        try:
            # Only update if viewer is ready
            if not self.viewer_ready:
                logger.debug("Viewer not ready yet, skipping live preview update")
                return
                
            current_settings = self._get_current_settings()
            if hasattr(self, 'viewer') and self.viewer:
                self.viewer.apply_settings(current_settings, save_to_file=False)
                logger.debug("Updated live preview with new settings")
        except Exception as e:
            logger.error(f"Failed to update live preview: {e}")
            import traceback
            logger.error(f"Live preview error traceback: {traceback.format_exc()}")
    
    def _apply_settings(self):
        """Apply current settings to all viewers without closing dialog"""
        try:
            current_settings = self._get_current_settings()
            self.settings_saved.emit(current_settings)
            logger.info("Applied settings to all viewers")
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
    
    def _save_and_close(self):
        """Save settings and close dialog"""
        try:
            current_settings = self._get_current_settings()
            
            # Save to file
            settings_file = Path("viewer/studio_viewer_settings.json")
            settings_file.parent.mkdir(exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(current_settings, f, indent=2)
            
            # Emit signal for application to apply to all viewers
            self.settings_saved.emit(current_settings)
            
            logger.info("Saved 3D viewer settings and applied to all viewers")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")