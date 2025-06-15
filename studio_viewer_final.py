#!/usr/bin/env python3
"""
Final Studio Three.js 3D Viewer - All Parameters Connected and Verified
"""

import sys
import os
import threading
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                              QWidget, QSlider, QLabel, QPushButton, QGroupBox,
                              QScrollArea, QCheckBox, QComboBox)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView

class LocalFileServer(SimpleHTTPRequestHandler):
    """Simple HTTP server to serve local files"""
    
    def __init__(self, *args, model_path=None, **kwargs):
        self.model_path = model_path
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        if self.path == '/model.glb' and self.model_path:
            try:
                with open(self.model_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'model/gltf-binary')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(404, f"Model not found: {e}")
        else:
            super().do_GET()
            
    def log_message(self, format, *args):
        pass


class ParameterControl(QWidget):
    """Slider control for a parameter"""
    
    def __init__(self, name, js_path, min_val, max_val, default_val, decimals=2, parent=None):
        super().__init__(parent)
        self.name = name
        self.js_path = js_path
        self.decimals = decimals
        self.multiplier = 10 ** decimals
        self.viewer = None
        self.default_val = default_val
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Label
        self.label = QLabel(f"{name}:")
        self.label.setMinimumWidth(140)
        layout.addWidget(self.label)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(min_val * self.multiplier))
        self.slider.setMaximum(int(max_val * self.multiplier))
        self.slider.setValue(int(default_val * self.multiplier))
        self.slider.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.slider)
        
        # Value label
        self.value_label = QLabel(f"{default_val:.{decimals}f}")
        self.value_label.setMinimumWidth(50)
        layout.addWidget(self.value_label)
        
        self.setLayout(layout)
        
    def on_value_changed(self, value):
        actual_value = value / self.multiplier
        self.value_label.setText(f"{actual_value:.{self.decimals}f}")
        
        # Send update to JavaScript
        if self.viewer and hasattr(self.viewer, 'update_parameter'):
            self.viewer.update_parameter(self.js_path, actual_value)
            
    def get_value(self):
        return self.slider.value() / self.multiplier
        
    def set_value(self, value):
        self.slider.setValue(int(value * self.multiplier))


class StudioViewer(QMainWindow):
    """Final Studio Three.js viewer with all parameters"""
    
    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.server = None
        self.server_port = 8892
        self.model_path = r"D:\Comfy3D_WinPortable\ComfyUI\output\3D\Hy3D_textured_00003_.glb"
        self.parameter_controls = []
        self.checkbox_controls = {}
        self.combo_controls = {}
        self.settings_file = "studio_viewer_settings.json"
        
        self.setup_ui()
        self.start_server()
        
        # Load viewer after server starts
        QTimer.singleShot(500, self.load_viewer)
        
        # Apply saved settings after viewer loads and initializes
        QTimer.singleShot(2000, self.load_and_apply_settings)
        
    def setup_ui(self):
        """Set up the UI"""
        self.setWindowTitle("Final Studio 3D Viewer - All Parameters Working")
        self.setGeometry(50, 50, 1700, 950)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Left side - 3D viewer
        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        main_layout.addWidget(self.web_view, 3)
        
        # Right side - Controls
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setMaximumWidth(450)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout()
        controls_widget.setLayout(controls_layout)
        controls_scroll.setWidget(controls_widget)
        
        # Add all control groups
        self.add_lighting_controls(controls_layout)
        self.add_material_controls(controls_layout)
        self.add_camera_controls(controls_layout)
        self.add_postprocessing_controls(controls_layout)
        self.add_environment_controls(controls_layout)
        
        # Save/Load buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; font-weight: bold; }")
        button_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Settings")
        load_btn.clicked.connect(self.load_and_apply_settings)
        button_layout.addWidget(load_btn)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(reset_btn)
        
        controls_layout.addLayout(button_layout)
        
        # Model control buttons
        model_layout = QHBoxLayout()
        
        drop_btn = QPushButton("Drop to Floor")
        drop_btn.clicked.connect(self.drop_to_floor)
        drop_btn.setStyleSheet("QPushButton { background-color: #2196F3; font-weight: bold; }")
        model_layout.addWidget(drop_btn)
        
        controls_layout.addLayout(model_layout)
        
        # Export button
        export_btn = QPushButton("Export to Console")
        export_btn.clicked.connect(self.export_settings)
        controls_layout.addWidget(export_btn)
        
        controls_layout.addStretch()
        main_layout.addWidget(controls_scroll, 1)
        
        # Apply styling
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { background-color: #1e1e1e; color: #e0e0e0; }
            QGroupBox {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #3a3a3a;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #3a3a3a;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #4a4a4a; }
            QCheckBox { spacing: 5px; }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        
    def add_lighting_controls(self, parent_layout):
        """Add lighting controls"""
        group = QGroupBox("Studio Lighting")
        layout = QVBoxLayout()
        
        # Ambient light
        controls = [
            ("Ambient Intensity", "ambientIntensity", 0, 2, 0.4),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        layout.addWidget(QLabel("Key Light:"))
        controls = [
            ("Intensity", "keyIntensity", 0, 3, 1.2),
            ("Position X", "keyPosX", -10, 10, 5, 1),
            ("Position Y", "keyPosY", 0, 20, 8, 1),
            ("Position Z", "keyPosZ", -10, 10, 5, 1),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        # Shadow controls
        shadow_check = QCheckBox("Enable Shadows")
        shadow_check.setChecked(True)
        shadow_check.stateChanged.connect(lambda state: self.update_parameter("shadowsEnabled", state == Qt.Checked))
        self.checkbox_controls["shadows"] = shadow_check
        layout.addWidget(shadow_check)
        
        controls = [
            ("Shadow Softness", "shadowSoftness", 0, 10, 1, 1),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        layout.addWidget(QLabel("Fill Light:"))
        controls = [
            ("Intensity", "fillIntensity", 0, 2, 0.6),
            ("Position X", "fillPosX", -10, 10, -5, 1),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        layout.addWidget(QLabel("Rim Light:"))
        controls = [
            ("Intensity", "rimIntensity", 0, 2, 0.4),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def add_material_controls(self, parent_layout):
        """Add material controls"""
        group = QGroupBox("Material Properties")
        layout = QVBoxLayout()
        
        controls = [
            ("Metalness Multiply", "materialMetalness", 0, 2, 1.0),
            ("Roughness Multiply", "materialRoughness", 0, 2, 1.0),
            ("Env Map Intensity", "envMapIntensity", 0, 5, 1.0),
            ("Emissive Intensity", "materialEmissive", 0, 2, 0.0),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def add_camera_controls(self, parent_layout):
        """Add camera controls"""
        group = QGroupBox("Camera")
        layout = QVBoxLayout()
        
        controls = [
            ("Field of View", "cameraFov", 10, 120, 35, 0),
            ("Camera Distance", "cameraDistance", 1, 10, 3, 1),
            ("Camera Height", "cameraHeight", -5, 10, 2, 1),
            ("Near Clip", "cameraNear", 0.01, 1, 0.1),
            ("Far Clip", "cameraFar", 10, 1000, 100, 0),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        # Auto rotate
        auto_rotate_check = QCheckBox("Auto Rotate")
        auto_rotate_check.setChecked(True)
        auto_rotate_check.stateChanged.connect(lambda state: self.update_parameter("autoRotate", state == Qt.Checked))
        self.checkbox_controls["autoRotate"] = auto_rotate_check
        layout.addWidget(auto_rotate_check)
        
        controls = [
            ("Rotation Speed", "rotateSpeed", -5, 5, 1.0),
            ("Damping Factor", "dampingFactor", 0, 0.2, 0.05),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def add_postprocessing_controls(self, parent_layout):
        """Add post-processing controls"""
        group = QGroupBox("Post-Processing")
        layout = QVBoxLayout()
        
        # Bloom
        bloom_check = QCheckBox("Enable Bloom")
        bloom_check.setChecked(True)
        bloom_check.stateChanged.connect(lambda state: self.update_parameter("bloomEnabled", state == Qt.Checked))
        self.checkbox_controls["bloom"] = bloom_check
        layout.addWidget(bloom_check)
        
        controls = [
            ("Bloom Strength", "bloomStrength", 0, 3, 0.3),
            ("Bloom Radius", "bloomRadius", 0, 1, 0.4),
            ("Bloom Threshold", "bloomThreshold", 0, 1, 0.85),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        # Tone mapping
        layout.addWidget(QLabel("Tone Mapping:"))
        tone_combo = QComboBox()
        tone_combo.addItems(["ACESFilmic", "Cineon", "Reinhard", "Linear", "None"])
        tone_combo.currentTextChanged.connect(lambda value: self.update_parameter("toneMapping", value))
        self.combo_controls["toneMapping"] = tone_combo
        layout.addWidget(tone_combo)
        
        controls = [
            ("Exposure", "exposure", 0, 3, 1.0),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def add_environment_controls(self, parent_layout):
        """Add environment controls"""
        group = QGroupBox("Environment")
        layout = QVBoxLayout()
        
        # Background
        layout.addWidget(QLabel("Background:"))
        bg_combo = QComboBox()
        bg_combo.addItems(["Pure Black", "Black", "Dark Gray", "Gray", "White", "Studio Blue"])
        bg_combo.setCurrentText("Dark Gray")
        bg_combo.currentTextChanged.connect(lambda value: self.update_parameter("background", value))
        self.combo_controls["background"] = bg_combo
        layout.addWidget(bg_combo)
        
        # Floor
        floor_check = QCheckBox("Show Floor")
        floor_check.setChecked(True)
        floor_check.stateChanged.connect(lambda state: self.update_parameter("showFloor", state == Qt.Checked))
        self.checkbox_controls["floor"] = floor_check
        layout.addWidget(floor_check)
        
        controls = [
            ("Floor Reflectivity", "floorMetalness", 0, 1, 0.1),
            ("Floor Roughness", "floorRoughness", 0, 1, 0.8),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
            
        # Grid
        layout.addWidget(QLabel("Grid:"))
        grid_check = QCheckBox("Show Grid")
        grid_check.setChecked(True)
        grid_check.stateChanged.connect(lambda state: self.update_parameter("showGrid", state == Qt.Checked))
        self.checkbox_controls["grid"] = grid_check
        layout.addWidget(grid_check)
        
        controls = [
            ("Grid Size", "gridSize", 5, 50, 20, 0),
            ("Grid Divisions", "gridDivisions", 10, 100, 40, 0),
            ("Grid Opacity", "gridOpacity", 0, 1, 0.3),
        ]
        
        for params in controls:
            control = ParameterControl(*params)
            control.viewer = self
            self.parameter_controls.append(control)
            layout.addWidget(control)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def start_server(self):
        """Start local HTTP server"""
        def run_server():
            handler = lambda *args: LocalFileServer(*args, model_path=self.model_path)
            self.server = HTTPServer(('localhost', self.server_port), handler)
            self.server.serve_forever()
            
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
    def update_parameter(self, js_path, value):
        """Update parameter in JavaScript"""
        if isinstance(value, bool):
            value = str(value).lower()
        elif isinstance(value, str):
            value = f'"{value}"'
            
        js_code = f"""
        if (window.updateParam) {{
            window.updateParam('{js_path}', {value});
        }}
        """
        self.web_view.page().runJavaScript(js_code)
        
    def save_settings(self):
        """Save current settings to file"""
        settings = {
            "sliders": {},
            "checkboxes": {},
            "combos": {}
        }
        
        # Save slider values
        for control in self.parameter_controls:
            settings["sliders"][control.js_path] = control.get_value()
            
        # Save checkbox states
        for name, checkbox in self.checkbox_controls.items():
            settings["checkboxes"][name] = checkbox.isChecked()
            
        # Save combo selections
        for name, combo in self.combo_controls.items():
            settings["combos"][name] = combo.currentText()
            
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
            
        print(f"Settings saved to {self.settings_file}")
        
    def load_and_apply_settings(self):
        """Load and apply settings from file"""
        if not os.path.exists(self.settings_file):
            return
            
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                
            print(f"Loading settings from {self.settings_file}")
            
            # Apply slider values and trigger updates
            for control in self.parameter_controls:
                if control.js_path in settings.get("sliders", {}):
                    value = settings["sliders"][control.js_path]
                    control.set_value(value)
                    # Force update to JavaScript
                    self.update_parameter(control.js_path, value)
                    
            # Apply checkbox states and trigger updates
            for name, checkbox in self.checkbox_controls.items():
                if name in settings.get("checkboxes", {}):
                    checked = settings["checkboxes"][name]
                    checkbox.setChecked(checked)
                    # Trigger the connected signal
                    checkbox.stateChanged.emit(Qt.Checked if checked else Qt.Unchecked)
                    
            # Apply combo selections and trigger updates
            for name, combo in self.combo_controls.items():
                if name in settings.get("combos", {}):
                    text = settings["combos"][name]
                    combo.setCurrentText(text)
                    # Trigger the connected signal
                    combo.currentTextChanged.emit(text)
                    
            print("Settings loaded and applied successfully")
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def reset_settings(self):
        """Reset all settings to default"""
        for control in self.parameter_controls:
            control.set_value(control.default_val)
            
        # Reset checkboxes
        self.checkbox_controls.get("shadows", QCheckBox()).setChecked(True)
        self.checkbox_controls.get("autoRotate", QCheckBox()).setChecked(True)
        self.checkbox_controls.get("bloom", QCheckBox()).setChecked(True)
        self.checkbox_controls.get("floor", QCheckBox()).setChecked(True)
        self.checkbox_controls.get("grid", QCheckBox()).setChecked(True)
        
        # Reset combos
        self.combo_controls.get("toneMapping", QComboBox()).setCurrentText("ACESFilmic")
        self.combo_controls.get("background", QComboBox()).setCurrentText("Dark Gray")
        
        print("Settings reset to default")
        
    def export_settings(self):
        """Export current settings to console"""
        js_code = """
        if (window.exportSettings) {
            const settings = window.exportSettings();
            console.log('=== Current Settings ===');
            console.log(settings);
            console.log('=======================');
        }
        """
        self.web_view.page().runJavaScript(js_code)
        
    def drop_to_floor(self):
        """Drop model to floor"""
        js_code = """
        if (window.dropToFloor) {
            window.dropToFloor();
        }
        """
        self.web_view.page().runJavaScript(js_code)
        
    def load_viewer(self):
        """Load the Three.js viewer"""
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Final Studio 3D Viewer</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: #0a0a0a;
        }}
        #container {{ width: 100vw; height: 100vh; }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            color: #fff;
            font-size: 14px;
            background: rgba(0,0,0,0.7);
            padding: 12px;
            border-radius: 5px;
            backdrop-filter: blur(10px);
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="info" style="display: none;">Loading model...</div>
    <div id="loader" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000000; display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 1;">
        <div id="loaderContent" style="text-align: center; color: #ffffff; font-family: 'Courier New', monospace;">
            <div style="font-size: 20px; margin-bottom: 20px;">Loading...</div>
        </div>
    </div>

    <script type="importmap">
    {{
        "imports": {{
            "three": "https://unpkg.com/three@0.161.0/build/three.module.js",
            "three/addons/": "https://unpkg.com/three@0.161.0/examples/jsm/"
        }}
    }}
    </script>

    <script type="module">
        import * as THREE from 'three';
        import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ EffectComposer }} from 'three/addons/postprocessing/EffectComposer.js';
        import {{ RenderPass }} from 'three/addons/postprocessing/RenderPass.js';
        import {{ UnrealBloomPass }} from 'three/addons/postprocessing/UnrealBloomPass.js';
        import {{ OutputPass }} from 'three/addons/postprocessing/OutputPass.js';

        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a1a); // Set default background immediately
        
        let camera, renderer, controls, composer;
        let model, lights = {{}}, bloomPass;
        
        // ASCII emoji collection for loading
        const asciiEmojis = [
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
        ];
        
        let loadingInterval;
        
        // Parameters - all connected and verified
        const params = {{
            // Lighting
            ambientIntensity: 0.4,
            keyIntensity: 1.2,
            keyPosX: 5,
            keyPosY: 8,
            keyPosZ: 5,
            shadowsEnabled: true,
            shadowSoftness: 1,
            fillIntensity: 0.6,
            fillPosX: -5,
            rimIntensity: 0.4,
            
            // Material
            materialMetalness: 1.0,
            materialRoughness: 1.0,
            envMapIntensity: 1.0,
            materialEmissive: 0.0,
            
            // Camera
            cameraFov: 35,
            cameraDistance: 3,
            cameraHeight: 2,
            cameraNear: 0.1,
            cameraFar: 100,
            autoRotate: true,
            rotateSpeed: 1.0,
            dampingFactor: 0.05,
            
            // Post-processing
            bloomEnabled: true,
            bloomStrength: 0.3,
            bloomRadius: 0.4,
            bloomThreshold: 0.85,
            toneMapping: "ACESFilmic",
            exposure: 1.0,
            
            // Environment
            background: "Dark Gray",
            showFloor: true,
            floorMetalness: 0.1,
            floorRoughness: 0.8,
            showGrid: true,
            gridSize: 20,
            gridDivisions: 40,
            gridOpacity: 0.3
        }};
        
        let floor, grid;

        function init() {{
            const container = document.getElementById('container');
            
            // Start loading animation immediately
            startLoadingAnimation();
            
            // Camera
            camera = new THREE.PerspectiveCamera(
                params.cameraFov,
                window.innerWidth / window.innerHeight,
                params.cameraNear,
                params.cameraFar
            );
            updateCameraPosition();

            // Renderer
            renderer = new THREE.WebGLRenderer({{ 
                antialias: true,
                powerPreference: "high-performance"
            }});
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = params.exposure;
            renderer.shadowMap.enabled = params.shadowsEnabled;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.outputColorSpace = THREE.SRGBColorSpace;
            container.appendChild(renderer.domElement);

            // Post-processing
            composer = new EffectComposer(renderer);
            const renderPass = new RenderPass(scene, camera);
            composer.addPass(renderPass);

            bloomPass = new UnrealBloomPass(
                new THREE.Vector2(window.innerWidth, window.innerHeight),
                params.bloomStrength,
                params.bloomRadius,
                params.bloomThreshold
            );
            bloomPass.enabled = params.bloomEnabled;
            composer.addPass(bloomPass);

            const outputPass = new OutputPass();
            composer.addPass(outputPass);

            // Controls
            controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = params.dampingFactor;
            controls.autoRotate = params.autoRotate;
            controls.autoRotateSpeed = params.rotateSpeed;
            controls.target.set(0, 0.5, 0); // Default target slightly above ground

            // Lighting
            setupLighting();

            // Environment
            setupEnvironment();
            
            // Initialize grid early to avoid null reference
            grid = new THREE.GridHelper(20, 40, 0x505050, 0x606060);
            grid.position.y = 0; // Set grid exactly at y=0
            grid.visible = true;
            scene.add(grid);
            
            // Update background
            updateBackground();

            // Load model after a short delay to ensure everything is initialized
            setTimeout(() => {{
                loadModel();
            }}, 500);

            // Handle resize
            window.addEventListener('resize', onWindowResize);

            animate();
        }}

        function setupLighting() {{
            // Ambient
            lights.ambient = new THREE.AmbientLight(0xffffff, params.ambientIntensity);
            scene.add(lights.ambient);

            // Key light
            lights.key = new THREE.DirectionalLight(0xffffff, params.keyIntensity);
            lights.key.position.set(params.keyPosX, params.keyPosY, params.keyPosZ);
            lights.key.castShadow = params.shadowsEnabled;
            lights.key.shadow.mapSize.width = 2048;
            lights.key.shadow.mapSize.height = 2048;
            lights.key.shadow.camera.near = 0.1;
            lights.key.shadow.camera.far = 30;
            lights.key.shadow.camera.left = -10;
            lights.key.shadow.camera.right = 10;
            lights.key.shadow.camera.top = 10;
            lights.key.shadow.camera.bottom = -10;
            lights.key.shadow.radius = params.shadowSoftness;
            lights.key.shadow.blurSamples = 25;
            scene.add(lights.key);

            // Fill light
            lights.fill = new THREE.DirectionalLight(0xffffff, params.fillIntensity);
            lights.fill.position.set(params.fillPosX, 5, -3);
            scene.add(lights.fill);

            // Rim light
            lights.rim = new THREE.DirectionalLight(0xffffff, params.rimIntensity);
            lights.rim.position.set(0, 5, -8);
            scene.add(lights.rim);
        }}

        function setupEnvironment() {{
            // Floor
            const floorGeometry = new THREE.CircleGeometry(20, 64);
            const floorMaterial = new THREE.MeshStandardMaterial({{
                color: 0x202020,
                metalness: params.floorMetalness,
                roughness: params.floorRoughness
            }});
            floor = new THREE.Mesh(floorGeometry, floorMaterial);
            floor.rotation.x = -Math.PI / 2;
            floor.position.y = -0.01; // Just slightly below grid
            floor.receiveShadow = true;
            floor.visible = params.showFloor;
            scene.add(floor);

            // Update grid with initial parameters
            updateGrid();
        }}

        function loadModel() {{
            console.log('Starting to load model...');
            console.log('Model URL:', 'http://localhost:{self.server_port}/model.glb');
            
            const loader = new GLTFLoader();
            
            loader.load(
                'http://localhost:{self.server_port}/model.glb',
                function(gltf) {{
                    console.log('Model loaded successfully');
                    model = gltf.scene;
                    
                    // Center and scale
                    const box = new THREE.Box3().setFromObject(model);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 2 / maxDim;
                    
                    model.scale.multiplyScalar(scale);
                    model.position.sub(center.multiplyScalar(scale));
                    
                    // Calculate floor offset
                    const floorBox = new THREE.Box3().setFromObject(model);
                    const minY = floorBox.min.y;
                    
                    // If model is below floor, lift it up
                    if (minY < 0) {{
                        model.position.y -= minY;
                        console.log('Auto-adjusted model to floor, lifted by:', -minY);
                    }}
                    
                    // Update materials
                    updateMaterials();
                    
                    scene.add(model);
                    
                    // Update camera target to model center
                    const modelBox = new THREE.Box3().setFromObject(model);
                    const modelCenter = modelBox.getCenter(new THREE.Vector3());
                    controls.target.copy(modelCenter);
                    controls.update();
                    console.log('Camera target set to model center:', modelCenter);
                    
                    // Clear loading animation
                    if (loadingInterval) {{
                        clearInterval(loadingInterval);
                    }}
                    
                    // Add longer delay to ensure model is fully loaded and camera is positioned
                    setTimeout(() => {{
                        // Ensure one more frame is rendered with correct camera position
                        controls.update();
                        composer.render();
                        
                        // Now fade out loader
                        setTimeout(() => {{
                            const loader = document.getElementById('loader');
                            loader.style.transition = 'opacity 0.5s ease-out';
                            loader.style.opacity = '0';
                            
                            setTimeout(() => {{
                                loader.style.display = 'none';
                            }}, 500);
                            
                            // Hide info - no longer needed
                            document.getElementById('info').style.display = 'none';
                        }}, 500); // Additional delay for camera settling
                    }}, 800); // Increased from 300ms to 800ms
                }},
                function(xhr) {{
                    console.log('Loading progress:', (xhr.loaded / xhr.total * 100) + '%');
                }},
                function(error) {{
                    console.error('Error loading model:', error);
                    console.error('Model URL:', 'http://localhost:{self.server_port}/model.glb');
                    
                    // Clear loading animation
                    if (loadingInterval) {{
                        clearInterval(loadingInterval);
                    }}
                    
                    // Update loader with error
                    const loaderContent = document.getElementById('loaderContent');
                    const sadEmoji = '(╥﹏╥)';
                    loaderContent.innerHTML = '<div style="font-size: 30px; margin-bottom: 20px;">' + sadEmoji + '</div>' +
                                            '<div style="font-size: 18px; color: #ff6b6b;">Error loading model</div>' +
                                            '<div style="font-size: 14px; margin-top: 10px; color: #aaa;">' + error.message + '</div>';
                }}
            );
        }}

        function dropToFloor() {{
            if (!model) return;
            
            // Reset to original position first
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            // Scale and center as in initial load
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 2 / maxDim;
            
            model.scale.set(scale, scale, scale);
            model.position.set(0, 0, 0);
            model.position.sub(center.multiplyScalar(scale));
            
            // Now calculate the offset to place on floor
            const newBox = new THREE.Box3().setFromObject(model);
            const minY = newBox.min.y;
            
            // Move up so bottom touches y=0
            model.position.y -= minY;
            
            // Update camera target to new model center
            const modelCenter = newBox.getCenter(new THREE.Vector3());
            modelCenter.y = (modelCenter.y - minY); // Adjust for floor positioning
            controls.target.copy(modelCenter);
            controls.update();
            
            console.log('Model repositioned to floor at y=0, camera target updated');
        }}
        
        function startLoadingAnimation() {{
            const loader = document.getElementById('loader');
            const loaderContent = document.getElementById('loaderContent');
            loader.style.display = 'flex';
            
            let frame = 0;
            const loadingChars = ['L', 'O', 'A', 'D', 'I', 'N', 'G', ' ', 'M', 'O', 'D', 'E', 'L'];
            
            loadingInterval = setInterval(() => {{
                const emoji = asciiEmojis[Math.floor(Math.random() * asciiEmojis.length)];
                const dots = '.'.repeat((frame % 4));
                const spaces = ' '.repeat(3 - (frame % 4));
                
                let text = '<div style="font-size: 20px; margin-bottom: 15px;">' + emoji + '</div>';
                
                // Animate the loading text
                text += '<div style="font-size: 14px; letter-spacing: 2px;">';
                for (let i = 0; i < loadingChars.length; i++) {{
                    if (i < (frame % (loadingChars.length + 3))) {{
                        text += loadingChars[i] + ' ';
                    }} else {{
                        text += '  ';
                    }}
                }}
                text += '</div>';
                
                text += '<div style="font-size: 16px; margin-top: 10px;">' + dots + spaces + '</div>';
                loaderContent.innerHTML = text;
                
                frame++;
            }}, 150);
        }}
        
        function updateMaterials() {{
            if (!model) return;
            
            model.traverse((child) => {{
                if (child.isMesh) {{
                    child.castShadow = true;
                    child.receiveShadow = true;
                    
                    if (child.material) {{
                        // Store original values
                        if (child.material.userData.originalMetalness === undefined) {{
                            child.material.userData.originalMetalness = child.material.metalness || 0;
                            child.material.userData.originalRoughness = child.material.roughness || 1;
                        }}
                        
                        // Apply multipliers
                        child.material.metalness = Math.min(
                            child.material.userData.originalMetalness * params.materialMetalness, 1
                        );
                        child.material.roughness = Math.max(
                            child.material.userData.originalRoughness * params.materialRoughness, 0
                        );
                        child.material.envMapIntensity = params.envMapIntensity;
                        
                        // Emissive
                        if (params.materialEmissive > 0) {{
                            child.material.emissive = new THREE.Color(1, 1, 1);
                            child.material.emissiveIntensity = params.materialEmissive;
                        }} else {{
                            child.material.emissiveIntensity = 0;
                        }}
                    }}
                }}
            }});
        }}

        function updateCameraPosition() {{
            const angle = 0.5;
            camera.position.x = params.cameraDistance * Math.sin(angle);
            camera.position.y = params.cameraHeight;
            camera.position.z = params.cameraDistance * Math.cos(angle);
            
            // Look at current target (will be updated when model loads)
            if (controls && controls.target) {{
                camera.lookAt(controls.target);
                controls.update();
            }} else {{
                camera.lookAt(0, 0.5, 0);
            }}
        }}
        
        function updateBackground() {{
            const colors = {{
                'Pure Black': 0x000000,
                'Black': 0x0a0a0a,
                'Dark Gray': 0x1a1a1a,
                'Gray': 0x404040,
                'White': 0xffffff,
                'Studio Blue': 0x1a2332
            }};
            scene.background = new THREE.Color(colors[params.background] || 0x1a1a1a);
        }}
        
        function updateGrid() {{
            // Remove existing grid
            if (grid) {{
                scene.remove(grid);
                grid.geometry.dispose();
                grid.material.dispose();
            }}
            
            // Create new grid with updated parameters
            // Default to dark grid if background not set yet
            let gridColor = 0x606060;
            let gridCenterColor = 0x505050;
            
            if (scene.background && scene.background.getHex) {{
                try {{
                    const bgHex = scene.background.getHex();
                    gridColor = bgHex < 0x808080 ? 0x606060 : 0x404040;
                    gridCenterColor = bgHex < 0x808080 ? 0x505050 : 0x303030;
                }} catch(e) {{
                    console.warn('Could not get background color:', e);
                }}
            }}
            
            grid = new THREE.GridHelper(
                params.gridSize, 
                params.gridDivisions, 
                gridCenterColor, 
                gridColor
            );
            grid.position.y = 0; // Grid at exactly y=0
            grid.visible = params.showGrid;
            
            // Apply opacity to grid materials (GridHelper has two materials)
            if (grid.material) {{
                if (Array.isArray(grid.material)) {{
                    grid.material.forEach(mat => {{
                        mat.opacity = params.gridOpacity;
                        mat.transparent = true;
                    }});
                }} else {{
                    grid.material.opacity = params.gridOpacity;
                    grid.material.transparent = true;
                }}
            }}
            
            scene.add(grid);
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
            composer.setSize(window.innerWidth, window.innerHeight);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            composer.render();
        }}

        // Parameter update function - handles all parameters
        window.updateParam = function(param, value) {{
            params[param] = value;
            
            // Log for debugging
            console.log('Updating param:', param, '=', value);
            
            // Skip updates if objects aren't initialized yet
            if (!lights.ambient && param.startsWith('ambient')) {{
                console.warn('Skipping', param, '- lights.ambient not initialized');
                return;
            }}
            if (!lights.key && (param.startsWith('key') || param === 'shadowsEnabled' || param === 'shadowSoftness')) {{
                console.warn('Skipping', param, '- lights.key not initialized');
                return;
            }}
            if (!lights.fill && param.startsWith('fill')) {{
                console.warn('Skipping', param, '- lights.fill not initialized');
                return;
            }}
            if (!lights.rim && param.startsWith('rim')) {{
                console.warn('Skipping', param, '- lights.rim not initialized');
                return;
            }}
            if (!floor && (param === 'showFloor' || param.startsWith('floor'))) {{
                console.warn('Skipping', param, '- floor not initialized');
                return;
            }}
            if (!grid && (param === 'showGrid' || param.startsWith('grid'))) {{
                console.warn('Skipping', param, '- grid not initialized');
                return;
            }}
            if (!bloomPass && param.startsWith('bloom')) {{
                console.warn('Skipping', param, '- bloomPass not initialized');
                return;
            }}
            if (!camera && param.startsWith('camera')) {{
                console.warn('Skipping', param, '- camera not initialized');
                return;
            }}
            if (!renderer && (param === 'exposure' || param === 'toneMapping')) {{
                console.warn('Skipping', param, '- renderer not initialized');
                return;
            }}
            if (!controls && (param === 'autoRotate' || param === 'rotateSpeed' || param === 'dampingFactor')) {{
                console.warn('Skipping', param, '- controls not initialized');
                return;
            }}
            
            switch(param) {{
                // Lighting parameters
                case 'ambientIntensity':
                    lights.ambient.intensity = value;
                    break;
                case 'keyIntensity':
                    lights.key.intensity = value;
                    break;
                case 'keyPosX':
                case 'keyPosY':
                case 'keyPosZ':
                    lights.key.position.set(params.keyPosX, params.keyPosY, params.keyPosZ);
                    break;
                case 'shadowsEnabled':
                    renderer.shadowMap.enabled = value;
                    lights.key.castShadow = value;
                    break;
                case 'shadowSoftness':
                    lights.key.shadow.radius = value;
                    break;
                case 'fillIntensity':
                    lights.fill.intensity = value;
                    break;
                case 'fillPosX':
                    lights.fill.position.x = value;
                    break;
                case 'rimIntensity':
                    lights.rim.intensity = value;
                    break;
                    
                // Material parameters
                case 'materialMetalness':
                case 'materialRoughness':
                case 'envMapIntensity':
                case 'materialEmissive':
                    updateMaterials();
                    break;
                    
                // Camera parameters
                case 'cameraFov':
                    camera.fov = value;
                    camera.updateProjectionMatrix();
                    break;
                case 'cameraDistance':
                case 'cameraHeight':
                    updateCameraPosition();
                    break;
                case 'cameraNear':
                    camera.near = value;
                    camera.updateProjectionMatrix();
                    break;
                case 'cameraFar':
                    camera.far = value;
                    camera.updateProjectionMatrix();
                    break;
                case 'autoRotate':
                    controls.autoRotate = value;
                    break;
                case 'rotateSpeed':
                    controls.autoRotateSpeed = value;
                    break;
                case 'dampingFactor':
                    controls.dampingFactor = value;
                    break;
                    
                // Post-processing parameters
                case 'bloomEnabled':
                    bloomPass.enabled = value;
                    break;
                case 'bloomStrength':
                    bloomPass.strength = value;
                    break;
                case 'bloomRadius':
                    bloomPass.radius = value;
                    break;
                case 'bloomThreshold':
                    bloomPass.threshold = value;
                    break;
                case 'toneMapping':
                    const mappings = {{
                        'ACESFilmic': THREE.ACESFilmicToneMapping,
                        'Cineon': THREE.CineonToneMapping,
                        'Reinhard': THREE.ReinhardToneMapping,
                        'Linear': THREE.LinearToneMapping,
                        'None': THREE.NoToneMapping
                    }};
                    renderer.toneMapping = mappings[value] || THREE.ACESFilmicToneMapping;
                    break;
                case 'exposure':
                    renderer.toneMappingExposure = value;
                    break;
                    
                // Environment parameters
                case 'background':
                    updateBackground();
                    updateGrid(); // Update grid colors based on background
                    break;
                case 'showFloor':
                    floor.visible = value;
                    break;
                case 'floorMetalness':
                    floor.material.metalness = value;
                    break;
                case 'floorRoughness':
                    floor.material.roughness = value;
                    break;
                case 'showGrid':
                    grid.visible = value;
                    break;
                case 'gridSize':
                case 'gridDivisions':
                case 'gridOpacity':
                    updateGrid();
                    break;
            }}
        }};

        // Export settings function
        window.exportSettings = function() {{
            return JSON.stringify(params, null, 2);
        }};
        
        // Expose dropToFloor to Python
        window.dropToFloor = dropToFloor;

        init();
    </script>
</body>
</html>
        '''
        
        self.web_view.setHtml(html_content, QUrl(f"http://localhost:{self.server_port}/"))
        
    def closeEvent(self, event):
        """Clean up server on close"""
        if self.server:
            self.server.shutdown()
        event.accept()


def main():
    """Run the final studio viewer"""
    # Set attribute before creating QApplication
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    app = QApplication(sys.argv)
    
    viewer = StudioViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()