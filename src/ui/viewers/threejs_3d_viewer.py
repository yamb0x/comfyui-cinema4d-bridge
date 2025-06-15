"""
ThreeJS 3D Viewer Module for Textured Models
Embedded version of studio_viewer_final.py without parameter controls
"""

import json
import os
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QUrl, Signal, QTimer, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from loguru import logger


class LocalFileServer(SimpleHTTPRequestHandler):
    """Simple HTTP server to serve local GLB files"""
    
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
        pass  # Suppress logging


class ThreeJS3DViewer(QWidget):
    """Embedded Three.js viewer for 3D model display"""
    
    model_loaded = Signal(str)  # Emits model path when loaded
    model_error = Signal(str)   # Emits error message
    
    # Class variable to track server port usage
    _next_port = 8893
    _port_lock = threading.Lock()
    
    def __init__(self, parent=None, width=496, height=460):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.settings_file = "studio_viewer_settings.json"
        self.server_thread = None
        self.server = None
        self.model_path = None
        
        # Get unique port for this instance
        with ThreeJS3DViewer._port_lock:
            self.server_port = ThreeJS3DViewer._next_port
            ThreeJS3DViewer._next_port += 1
        
        self.setup_ui()
        self.start_server()
        
    def setup_ui(self):
        """Setup the viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        layout.addWidget(self.web_view)
        
    def start_server(self):
        """Start local HTTP server for this viewer instance"""
        def run_server():
            handler = lambda *args: LocalFileServer(*args, model_path=self.model_path)
            self.server = HTTPServer(('localhost', self.server_port), handler)
            self.server.serve_forever()
            
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"Started server for ThreeJS viewer on port {self.server_port}")
        
    def load_model(self, model_path):
        """Load a new model into the viewer"""
        self.model_path = model_path
        
        # Update server with new model path
        if self.server_thread:
            # Restart server with new model
            self.stop_server()
            self.start_server()
        
        # Load viewer HTML
        QTimer.singleShot(100, lambda: self._load_viewer_html())
        
    def _load_viewer_html(self):
        """Load the Three.js viewer HTML"""
        # Load settings
        settings = self._load_settings()
        
        html_content = self._generate_viewer_html(settings)
        self.web_view.setHtml(html_content, QUrl(f"http://localhost:{self.server_port}/"))
        
    def _load_settings(self):
        """Load viewer settings from JSON file"""
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
                "gridOpacity": 0.3
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
            }
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults
                    for key in default_settings:
                        if key in loaded_settings:
                            default_settings[key].update(loaded_settings[key])
                    return default_settings
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        
        return default_settings
        
    def _generate_viewer_html(self, settings):
        """Generate the viewer HTML with embedded settings"""
        # Extract individual settings
        sliders = settings.get("sliders", {})
        checkboxes = settings.get("checkboxes", {})
        combos = settings.get("combos", {})
        
        # Build parameters object from settings
        params_js = json.dumps({
            # Lighting
            "ambientIntensity": sliders.get("ambientIntensity", 0.4),
            "keyIntensity": sliders.get("keyIntensity", 1.2),
            "keyPosX": sliders.get("keyPosX", 5),
            "keyPosY": sliders.get("keyPosY", 8),
            "keyPosZ": sliders.get("keyPosZ", 5),
            "shadowsEnabled": checkboxes.get("shadows", True),
            "shadowSoftness": sliders.get("shadowSoftness", 1),
            "fillIntensity": sliders.get("fillIntensity", 0.6),
            "fillPosX": sliders.get("fillPosX", -5),
            "rimIntensity": sliders.get("rimIntensity", 0.4),
            # Material
            "materialMetalness": sliders.get("materialMetalness", 1.0),
            "materialRoughness": sliders.get("materialRoughness", 1.0),
            "envMapIntensity": sliders.get("envMapIntensity", 1.0),
            "materialEmissive": sliders.get("materialEmissive", 0.0),
            # Camera
            "cameraFov": sliders.get("cameraFov", 35),
            "cameraDistance": sliders.get("cameraDistance", 3),
            "cameraHeight": sliders.get("cameraHeight", 2),
            "cameraNear": sliders.get("cameraNear", 0.1),
            "cameraFar": sliders.get("cameraFar", 100),
            "autoRotate": checkboxes.get("autoRotate", True),
            "rotateSpeed": sliders.get("rotateSpeed", 1.0),
            "dampingFactor": sliders.get("dampingFactor", 0.05),
            # Post-processing
            "bloomEnabled": checkboxes.get("bloom", True),
            "bloomStrength": sliders.get("bloomStrength", 0.3),
            "bloomRadius": sliders.get("bloomRadius", 0.4),
            "bloomThreshold": sliders.get("bloomThreshold", 0.85),
            "toneMapping": combos.get("toneMapping", "ACESFilmic"),
            "exposure": sliders.get("exposure", 1.0),
            # Environment
            "background": combos.get("background", "Dark Gray"),
            "showFloor": checkboxes.get("floor", True),
            "floorMetalness": sliders.get("floorMetalness", 0.1),
            "floorRoughness": sliders.get("floorRoughness", 0.8),
            "showGrid": checkboxes.get("grid", True),
            "gridSize": sliders.get("gridSize", 20),
            "gridDivisions": sliders.get("gridDivisions", 40),
            "gridOpacity": sliders.get("gridOpacity", 0.3)
        })
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>3D Model Viewer</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: #0a0a0a;
        }}
        #container {{ width: 100vw; height: 100vh; }}
        #loader {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #000000;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 1;
        }}
        #loaderContent {{
            text-align: center;
            color: #ffffff;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="loader">
        <div id="loaderContent">
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

        // Parameters from settings
        const params = {params_js};
        
        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a1a);
        
        let camera, renderer, controls, composer;
        let model, lights = {{}}, bloomPass;
        let floor, grid;
        
        // ASCII emoji collection for loading
        const asciiEmojis = [
            '(╯°□°）╯︵ ┻━┻', '¯\\\\_(ツ)_/¯', '(づ｡◕‿‿◕｡)づ', 'ᕕ( ᐛ )ᕗ',
            '♪~ ᕕ(ᐛ)ᕗ', '(☞ﾟヮﾟ)☞', '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧', '⊂(◉‿◉)つ',
            '(◕‿◕)♡', '\\\\(^o^)/', '(｡◕‿◕｡)', '(ᵔᴥᵔ)', 'ʕ•ᴥ•ʔ'
        ];
        
        let loadingInterval;

        function init() {{
            const container = document.getElementById('container');
            
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
            controls.target.set(0, 0.5, 0);

            // Setup scene
            setupLighting();
            setupEnvironment();
            updateBackground();
            
            // Load model
            setTimeout(() => {{ loadModel(); }}, 500);

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
            floor.position.y = -0.01;
            floor.receiveShadow = true;
            floor.visible = params.showFloor;
            scene.add(floor);

            // Grid
            updateGrid();
        }}

        function loadModel() {{
            console.log('Loading model from:', 'http://localhost:{self.server_port}/model.glb');
            
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
                    
                    // Auto drop to floor
                    const floorBox = new THREE.Box3().setFromObject(model);
                    const minY = floorBox.min.y;
                    if (minY < 0) {{
                        model.position.y -= minY;
                    }}
                    
                    // Update materials
                    updateMaterials();
                    
                    scene.add(model);
                    
                    // Update camera target
                    const modelBox = new THREE.Box3().setFromObject(model);
                    const modelCenter = modelBox.getCenter(new THREE.Vector3());
                    controls.target.copy(modelCenter);
                    controls.update();
                    
                    // Clear loading animation
                    if (loadingInterval) {{
                        clearInterval(loadingInterval);
                    }}
                    
                    // Wait for everything to settle, then hide loader
                    setTimeout(() => {{
                        controls.update();
                        composer.render();
                        
                        setTimeout(() => {{
                            const loader = document.getElementById('loader');
                            loader.style.transition = 'opacity 0.5s ease-out';
                            loader.style.opacity = '0';
                            
                            setTimeout(() => {{
                                loader.style.display = 'none';
                            }}, 500);
                        }}, 500);
                    }}, 800);
                }},
                function(xhr) {{
                    console.log('Loading progress:', (xhr.loaded / xhr.total * 100) + '%');
                }},
                function(error) {{
                    console.error('Error loading model:', error);
                    if (loadingInterval) {{
                        clearInterval(loadingInterval);
                    }}
                    
                    const loaderContent = document.getElementById('loaderContent');
                    loaderContent.innerHTML = '<div style="font-size: 30px;">(╥﹏╥)</div>' +
                                            '<div style="font-size: 18px; color: #ff6b6b;">Error loading model</div>';
                }}
            );
        }}

        function startLoadingAnimation() {{
            const loaderContent = document.getElementById('loaderContent');
            let frame = 0;
            
            loadingInterval = setInterval(() => {{
                const emoji = asciiEmojis[Math.floor(Math.random() * asciiEmojis.length)];
                const dots = '.'.repeat((frame % 4));
                
                loaderContent.innerHTML = 
                    '<div style="font-size: 20px; margin-bottom: 15px;">' + emoji + '</div>' +
                    '<div style="font-size: 16px;">Loading' + dots + '</div>';
                
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
            if (grid) {{
                scene.remove(grid);
                grid.geometry.dispose();
                grid.material.dispose();
            }}
            
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
            grid.position.y = 0;
            grid.visible = params.showGrid;
            
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

        // Initialize
        init();
    </script>
</body>
</html>'''
        
        return html
        
    def stop_server(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server_thread.join(timeout=1)
            
    def closeEvent(self, event):
        """Clean up on close"""
        self.stop_server()
        event.accept()