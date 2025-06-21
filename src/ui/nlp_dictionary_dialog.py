"""
NLP Dictionary Dialog for Cinema4D command management
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget,
    QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QLabel, QGroupBox, QGridLayout, QMessageBox, QSplitter,
    QTextEdit, QComboBox, QSpinBox, QCheckBox, QScrollArea,
    QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon
from loguru import logger

from .terminal_theme_complete import get_complete_terminal_theme


class NLPDictionaryDialog(QDialog):
    """Dialog for managing NLP command dictionary"""
    
    command_created = Signal(str, dict)  # command_type, parameters
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.parent_app = parent
        
        # Dictionary data storage
        self.dictionary_file = self.config.config_dir / "nlp_dictionary.json"
        self.dictionary_data = self._load_dictionary()
        
        # Track current category
        self.current_category = "primitives"
        
        self.setup_ui()
        self.apply_styles()
        self._apply_accent_colors()
        
        # Load initial category data after UI is fully set up
        self.load_category_data()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("NLP Dictionary - Cinema4D Commands")
        self.setModal(False)
        self.resize(1200, 800)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("NLP Dictionary Configuration")
        header.setObjectName("dialog_header")
        layout.addWidget(header)
        
        # Tab widget for categories
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("nlp_tabs")
        
        # Categories based on Cinema4D structure - UPDATED
        self.categories = {
            "primitives": "Primitives",
            "generators": "Generators", 
            "splines": "Splines",
            "deformers": "Deformers",
            "cameras_lights": "Cameras & Lights",
            "effectors": "MoGraph Effectors",
            "tags": "Tags",
            "mograph": "MoGraph",
            "fields": "Fields",
            "dynamics": "Dynamic Tags",
            "volumes": "Volumes",
            "models": "3D Models",
            "materials": "Materials",
            "render": "Render Settings"
        }
        
        # Create tabs for each category
        self.category_widgets = {}
        for key, name in self.categories.items():
            widget = self._create_category_widget(key)
            self.category_widgets[key] = widget
            self.tab_widget.addTab(widget, name)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_dictionary)
        button_layout.addWidget(self.save_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def _create_category_widget(self, category: str) -> QWidget:
        """Create widget for a category tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)
        
        # Left side - Command list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter commands...")
        self.search_box.textChanged.connect(lambda text: self._filter_commands(category, text))
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        left_layout.addLayout(search_layout)
        
        # Command list
        list_widget = QListWidget()
        list_widget.setObjectName("command_list")
        list_widget.itemSelectionChanged.connect(lambda: self._on_selection_changed(category))
        left_layout.addWidget(list_widget)
        
        # Store reference to list widget
        if not hasattr(self, 'list_widgets'):
            self.list_widgets = {}
        self.list_widgets[category] = list_widget
        
        # Add new command button
        add_button = QPushButton("+ Add New Command")
        add_button.clicked.connect(lambda: self._add_new_command(category))
        left_layout.addWidget(add_button)
        
        left_panel.setMaximumWidth(300)
        
        # Right side - Command details
        right_panel = self._create_details_panel(category)
        
        # Add to main layout with splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
        return widget
        
    def _create_details_panel(self, category: str) -> QWidget:
        """Create the details panel for command editing"""
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        
        # Command info group
        info_group = QGroupBox("Command Information")
        info_layout = QGridLayout(info_group)
        
        # Name field
        info_layout.addWidget(QLabel("Name:"), 0, 0)
        name_edit = QLineEdit()
        name_edit.setObjectName(f"{category}_name")
        info_layout.addWidget(name_edit, 0, 1)
        
        # C4D Constant field
        info_layout.addWidget(QLabel("C4D Constant:"), 1, 0)
        constant_edit = QLineEdit()
        constant_edit.setPlaceholderText("e.g., c4d.Ocube")
        constant_edit.setObjectName(f"{category}_constant")
        info_layout.addWidget(constant_edit, 1, 1)
        
        # Keywords field
        info_layout.addWidget(QLabel("Keywords:"), 2, 0)
        keywords_edit = QTextEdit()
        keywords_edit.setPlaceholderText("Enter keywords separated by commas\ne.g., cube, box, square")
        keywords_edit.setMaximumHeight(80)
        keywords_edit.setObjectName(f"{category}_keywords")
        info_layout.addWidget(keywords_edit, 2, 1)
        
        # Description field
        info_layout.addWidget(QLabel("Description:"), 3, 0)
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText("Brief description of the command")
        desc_edit.setMaximumHeight(60)
        desc_edit.setObjectName(f"{category}_description")
        info_layout.addWidget(desc_edit, 3, 1)
        
        layout.addWidget(info_group)
        
        # Parameters group (dynamic based on selection)
        params_group = QGroupBox("Default Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # Create a container for dynamic parameters
        params_container = QWidget()
        params_container.setObjectName(f"{category}_params_container")
        params_container_layout = QGridLayout(params_container)
        params_container_layout.setSpacing(5)
        
        # Store reference to container
        if not hasattr(self, 'param_containers'):
            self.param_containers = {}
        self.param_containers[category] = params_container
        
        params_layout.addWidget(params_container)
        layout.addWidget(params_group)
        
        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout(action_group)
        
        # Create button
        create_btn = QPushButton("Create in C4D")
        create_btn.setObjectName("create_button")
        create_btn.clicked.connect(lambda: self._create_command(category))
        action_layout.addWidget(create_btn)
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(lambda: self._show_settings(category))
        action_layout.addWidget(settings_btn)
        
        # Remove button
        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.setObjectName("remove_button")
        remove_btn.clicked.connect(lambda: self._remove_command(category))
        action_layout.addWidget(remove_btn)
        
        # Test button
        test_btn = QPushButton("🧪 Test")
        test_btn.clicked.connect(lambda: self._test_command(category))
        action_layout.addWidget(test_btn)
        
        layout.addWidget(action_group)
        
        # Store references
        if not hasattr(self, 'detail_panels'):
            self.detail_panels = {}
        self.detail_panels[category] = content
        
        panel.setWidget(content)
        return panel
        
    def _load_dictionary(self) -> Dict[str, Any]:
        """Load dictionary data from file"""
        if self.dictionary_file.exists():
            try:
                with open(self.dictionary_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading dictionary: {e}")
        
        # Return default structure
        return {
            "primitives": self._get_default_primitives(),
            "generators": self._get_default_generators(),
            "splines": self._get_default_splines(),
            "deformers": self._get_default_deformers(),
            "cameras_lights": self._get_default_cameras_lights(),
            "effectors": self._get_default_effectors(),
            "tags": self._get_default_tags(),
            "mograph": {},
            "fields": self._get_default_fields(),
            "dynamics": {},
            "volumes": {},
            "models": self._get_default_models(),
            "materials": {},
            "render": {}
        }
        
    def _get_default_primitives(self) -> Dict[str, Any]:
        """Get default primitive definitions"""
        return {
            "cube": {
                "name": "Cube",
                "constant": "c4d.Ocube",
                "keywords": ["cube", "box", "square", "block"],
                "description": "Creates a cube primitive",
                "parameters": {
                    "size_x": 200,
                    "size_y": 200,
                    "size_z": 200,
                    "segments": 1,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "sphere": {
                "name": "Sphere",
                "constant": "c4d.Osphere",
                "keywords": ["sphere", "ball", "orb", "globe"],
                "description": "Creates a sphere primitive",
                "parameters": {
                    "radius": 100,
                    "segments": 24,
                    "type": 0,
                    "render_perfect": True,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "cylinder": {
                "name": "Cylinder",
                "constant": "c4d.Ocylinder",
                "keywords": ["cylinder", "tube", "pipe", "rod"],
                "description": "Creates a cylinder primitive",
                "parameters": {
                    "radius": 50,
                    "height": 200,
                    "segments": 36,
                    "caps": True,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "cone": {
                "name": "Cone",
                "constant": "c4d.Ocone",
                "keywords": ["cone", "pyramid", "funnel"],
                "description": "Creates a cone primitive",
                "parameters": {
                    "bottom_radius": 100,
                    "top_radius": 0,
                    "height": 200,
                    "segments": 36,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "torus": {
                "name": "Torus",
                "constant": "c4d.Otorus",
                "keywords": ["torus", "donut", "ring"],
                "description": "Creates a torus primitive",
                "parameters": {
                    "ring_radius": 100,
                    "pipe_radius": 20,
                    "ring_segments": 36,
                    "pipe_segments": 18,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "plane": {
                "name": "Plane",
                "constant": "c4d.Oplane",
                "keywords": ["plane", "ground", "floor", "surface"],
                "description": "Creates a plane primitive",
                "parameters": {
                    "width": 400,
                    "height": 400,
                    "width_segments": 1,
                    "height_segments": 1,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "disc": {
                "name": "Disc",
                "constant": "c4d.Odisc",
                "keywords": ["disc", "disk", "circle", "round"],
                "description": "Creates a disc primitive",
                "parameters": {
                    "outer_radius": 100,
                    "inner_radius": 0,
                    "segments": 36,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "pyramid": {
                "name": "Pyramid",
                "constant": "c4d.Opyramid",
                "keywords": ["pyramid", "tetrahedron"],
                "description": "Creates a pyramid primitive",
                "parameters": {
                    "size_x": 200,
                    "size_y": 200,
                    "size_z": 200,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "tube": {
                "name": "Tube",
                "constant": "c4d.Otube",
                "keywords": ["tube", "hollow cylinder", "pipe"],
                "description": "Creates a tube primitive",
                "parameters": {
                    "inner_radius": 50,
                    "outer_radius": 100,
                    "height": 200,
                    "segments": 36,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "figure": {
                "name": "Figure",
                "constant": "c4d.Ofigure",
                "keywords": ["figure", "person", "human"],
                "description": "Creates a figure primitive",
                "parameters": {
                    "size": 200,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "platonic": {
                "name": "Platonic",
                "constant": "c4d.Oplatonic",
                "keywords": ["platonic", "polyhedron", "geometric"],
                "description": "Creates a platonic solid",
                "parameters": {
                    "type": 0,  # 0=Tetrahedron, 1=Hexahedron, 2=Octahedron, etc.
                    "size": 100,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "landscape": {
                "name": "Landscape",
                "constant": "c4d.Olandscape",
                "keywords": ["landscape", "terrain", "mountain"],
                "description": "Creates a landscape primitive",
                "parameters": {
                    "size": 1000,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "oil_tank": {
                "name": "Oil Tank",
                "constant": "c4d.Ooiltank",
                "keywords": ["oil tank", "tank", "container"],
                "description": "Creates an oil tank primitive",
                "parameters": {
                    "radius": 100,
                    "height": 200,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "capsule": {
                "name": "Capsule",
                "constant": "c4d.Ocapsule",
                "keywords": ["capsule", "pill", "rounded cylinder"],
                "description": "Creates a capsule primitive",
                "parameters": {
                    "radius": 50,
                    "height": 200,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "relief": {
                "name": "Relief",
                "constant": "c4d.Orelief",
                "keywords": ["relief", "heightmap", "displacement"],
                "description": "Creates a relief primitive",
                "parameters": {
                    "size": 400,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "single_polygon": {
                "name": "Single Polygon",
                "constant": "c4d.Opolygon",
                "keywords": ["polygon", "single polygon", "face"],
                "description": "Creates a single polygon",
                "parameters": {
                    "size": 200,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "fractal": {
                "name": "Fractal",
                "constant": "c4d.Ofractal",
                "keywords": ["fractal", "recursive", "mandelbrot"],
                "description": "Creates a fractal primitive",
                "parameters": {
                    "size": 200,
                    "iterations": 3,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "formula": {
                "name": "Formula",
                "constant": "c4d.Oformula",
                "keywords": ["formula", "math", "equation", "expression"],
                "description": "Creates a formula-based object",
                "parameters": {
                    "size": 200,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            }
        }
        
    def _get_default_generators(self) -> Dict[str, Any]:
        """Get default generator definitions"""
        return {
            "array": {
                "name": "Array",
                "constant": "c4d.Oarray",
                "keywords": ["array", "duplicate", "clone", "repeat"],
                "description": "Creates an array generator",
                "parameters": {
                    "copies": 7,
                    "radius": 250.0,
                    "amplitude": 0.0,
                    "frequency": 0.0
                }
            },
            "boolean": {
                "name": "Boolean",
                "constant": "c4d.Oboole",  # Might need to be Oboolean or another variant
                "keywords": ["boolean", "bool", "combine", "subtract", "intersect"],
                "description": "Creates a boolean generator",
                "parameters": {
                    "mode": 0,  # 0=A-B, 1=A+B, 2=A AND B, 3=A without B
                    "create_single_object": True
                }
            },
            "cloner": {
                "name": "Cloner",
                "constant": "c4d.Omgcloner",  # MoGraph Cloner correct constant
                "keywords": ["cloner", "mograph", "duplicate", "instance", "clone"],
                "description": "Creates a MoGraph cloner",
                "parameters": {
                    "mode": 0,  # 0=Linear, 1=Radial, 2=Grid
                    "count": 5,
                    "radius": 200,
                    "spacing": 100
                }
            },
            "extrude": {
                "name": "Extrude",
                "constant": "c4d.Oextrude",
                "keywords": ["extrude", "depth", "push", "pull"],
                "description": "Creates an extrude generator",
                "parameters": {
                    "offset": 100,
                    "subdivision": 1,
                    "movement_x": 0,
                    "movement_y": 0,
                    "movement_z": 100
                }
            },
            "lathe": {
                "name": "Lathe",
                "constant": "c4d.Olathe",
                "keywords": ["lathe", "revolve", "spin", "rotate"],
                "description": "Creates a lathe generator",
                "parameters": {
                    "angle": 360,
                    "subdivision": 24,
                    "axis": 1  # 0=X, 1=Y, 2=Z
                }
            },
            "loft": {
                "name": "Loft",
                "constant": "c4d.Oloft",
                "keywords": ["loft", "skin", "surface", "connect"],
                "description": "Creates a loft generator",
                "parameters": {
                    "subdivision_u": 20,
                    "subdivision_v": 20,
                    "organic_form": False
                }
            },
            "sweep": {
                "name": "Sweep",
                "constant": "c4d.Osweep",
                "keywords": ["sweep", "profile", "path", "rail"],
                "description": "Creates a sweep generator",
                "parameters": {
                    "end_growth": 100,
                    "start_growth": 0,
                    "parallel_movement": True
                }
            },
            "subdivision_surface": {
                "name": "Subdivision Surface",
                "constant": "c4d.Osds",  # May also be Ohypernurbs in older versions
                "keywords": ["subdivision", "smooth", "sds", "hypernurbs"],
                "description": "Creates a subdivision surface generator",
                "parameters": {
                    "subdivision_editor": 1,
                    "subdivision_render": 2,
                    "type": 0  # 0=Catmull-Clark, 1=Loop, 2=Catmull-Clark (N-Gons)
                }
            },
            "symmetry": {
                "name": "Symmetry",
                "constant": "c4d.Osymmetry",
                "keywords": ["symmetry", "mirror", "reflect", "flip"],
                "description": "Creates a symmetry generator",
                "parameters": {
                    "mirror_plane": 0,  # 0=YZ, 1=ZX, 2=XY
                    "weld_points": True,
                    "tolerance": 0.01
                }
            },
            "instance": {
                "name": "Instance",
                "constant": "c4d.Oinstance",
                "keywords": ["instance", "reference", "link", "copy"],
                "description": "Creates an instance generator",
                "parameters": {
                    "render_instances": True,
                    "multi_instances": False
                }
            },
            "metaball": {
                "name": "Metaball",
                "constant": "c4d.Ometaball",
                "keywords": ["metaball", "blob", "organic", "merge"],
                "description": "Creates a metaball generator",
                "parameters": {
                    "hull_value": 1,
                    "subdivision_editor": 3
                }
            },
            "bezier": {
                "name": "Bezier",
                "constant": "c4d.Obezier",
                "keywords": ["bezier", "nurbs", "curve", "smooth"],
                "description": "Creates a bezier generator",
                "parameters": {
                    "subdivision": 20
                }
            },
            "connect": {
                "name": "Connect", 
                "constant": "c4d.Oconnector",  # Note: it's Oconnector not Oconnect
                "keywords": ["connect", "merge", "combine", "join"],
                "description": "Creates a connect generator",
                "parameters": {
                    "weld": True,
                    "tolerance": 0.01,
                    "phong_tag": True
                }
            },
            "spline_wrap": {
                "name": "Spline Wrap",
                "constant": "c4d.Osplinewrap",
                "keywords": ["spline wrap", "deform", "bend", "curve"],
                "description": "Creates a spline wrap generator",
                "parameters": {
                    "axis": 2,  # 0=X, 1=Y, 2=Z
                    "offset": 0,
                    "size": 100
                }
            },
            "polygon_reduction": {
                "name": "Polygon Reduction",
                "constant": "c4d.Opolyreduxgen",
                "keywords": ["polygon reduction", "reduce", "optimize", "decimate"],
                "description": "Creates a polygon reduction generator",
                "parameters": {
                    "reduction_strength": 50,
                    "boundary_curve_preservation": 100
                }
            }
        }
        
    def _get_default_splines(self) -> Dict[str, Any]:
        """Get default spline definitions"""
        return {
            "circle": {
                "name": "Circle",
                "constant": "c4d.Osplinecircle",
                "keywords": ["circle", "round", "ring", "spline"],
                "description": "Creates a circle spline",
                "parameters": {
                    "circle_ellipse": 0,
                    "circle_radius": 200.0,
                    "circle_inner": 100.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "rectangle": {
                "name": "Rectangle",
                "constant": "c4d.Osplinerectangle",
                "keywords": ["rectangle", "square", "box", "spline"],
                "description": "Creates a rectangle spline",
                "parameters": {
                    "rectangle_width": 400.0,
                    "rectangle_height": 400.0,
                    "rectangle_radius": 50.0,
                    "rectangle_rounding": 0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "text": {
                "name": "Text",
                "constant": "c4d.Osplinetext",
                "keywords": ["text", "font", "letters", "spline"],
                "description": "Creates a text spline",
                "parameters": {
                    "text_text": "Text",
                    "text_height": 200.0,
                    "text_hspacing": 0.0,
                    "text_vspacing": 0.0,
                    "text_align": 0,
                    "text_separate": 0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "helix": {
                "name": "Helix",
                "constant": "c4d.Osplinehelix",
                "keywords": ["helix", "spiral", "coil", "spline"],
                "description": "Creates a helix spline",
                "parameters": {
                    "helix_start": 0.0,
                    "helix_end": 12.566370614359172,
                    "helix_height": 200.0,
                    "helix_radius1": 200.0,
                    "helix_radius2": 200.0,
                    "helix_sub": 100,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "star": {
                "name": "Star",
                "constant": "c4d.Osplinestar",
                "keywords": ["star", "points", "shape", "spline"],
                "description": "Creates a star spline",
                "parameters": {
                    "star_points": 8,
                    "star_orad": 200.0,
                    "star_irad": 100.0,
                    "star_twist": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            }
        }
        
    def _get_default_cameras_lights(self) -> Dict[str, Any]:
        """Get default camera and light definitions - USING VERIFIED DATA FROM DISCOVERY"""
        return {
            # CAMERAS - Only camera exists, target_camera doesn't exist in Cinema4D
            "camera": {
                "name": "Camera",
                "constant": "c4d.Ocamera",
                "keywords": ["camera", "view", "perspective", "lens"],
                "description": "Creates a camera object",
                "parameters": {
                    "fov": 0.9500215125301936,  # VERIFIED: Actual default from Cinema4D
                    "targetdistance": 2000.0,   # VERIFIED: Actual default from Cinema4D
                    "film_offset_x": 0.0,       # VERIFIED: Actual default from Cinema4D
                    "film_offset_y": 0.0,       # VERIFIED: Actual default from Cinema4D
                    "projection": 0,            # VERIFIED: Actual default from Cinema4D
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            # LIGHTS
            "light": {
                "name": "Light",
                "constant": "c4d.Olight",
                "keywords": ["light", "illumination", "lighting", "lamp"],
                "description": "Creates a light object",
                "parameters": {
                    "brightness": 1.0,                    # VERIFIED: Actual default from Cinema4D
                    "type": 0,                           # VERIFIED: Actual default from Cinema4D
                    "shadowtype": 0,                     # VERIFIED: Actual default from Cinema4D
                    "outerangle": 0.5235987755982988,    # VERIFIED: Actual default from Cinema4D (~30°)
                    "innerangle": 0.0,                   # VERIFIED: Actual default from Cinema4D
                    "falloff": 0,                        # VERIFIED: Actual default from Cinema4D
                    "pos_x": 0,
                    "pos_y": 200,
                    "pos_z": 0
                }
            }
        }
        
    def _get_default_effectors(self) -> Dict[str, Any]:
        """Get default MoGraph effector definitions"""
        return {
            "plain_effector": {
                "name": "Plain Effector",
                "constant": "c4d.Omgplain",
                "keywords": ["plain", "effector", "mograph", "basic"],
                "description": "Creates a plain MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "random_effector": {
                "name": "Random Effector",
                "constant": "c4d.Omgrandom",
                "keywords": ["random", "effector", "mograph", "chaos"],
                "description": "Creates a random MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "seed": 12345,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "shader_effector": {
                "name": "Shader Effector",
                "constant": "c4d.Omgshader",
                "keywords": ["shader", "effector", "mograph", "texture"],
                "description": "Creates a shader MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "delay_effector": {
                "name": "Delay Effector",
                "constant": "c4d.Omgdelay",
                "keywords": ["delay", "effector", "mograph", "timing"],
                "description": "Creates a delay MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "delay": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "formula_effector": {
                "name": "Formula Effector",
                "constant": "c4d.Omgformula",
                "keywords": ["formula", "effector", "mograph", "math"],
                "description": "Creates a formula MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "step_effector": {
                "name": "Step Effector",
                "constant": "c4d.Omgstep",
                "keywords": ["step", "effector", "mograph", "sequence"],
                "description": "Creates a step MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "steps": 5,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "target_effector": {
                "name": "Target Effector", 
                "constant": "c4d.Omgeffectortarget",
                "keywords": ["target", "effector", "mograph", "aim"],
                "description": "Creates a target MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "time_effector": {
                "name": "Time Effector",
                "constant": "c4d.Omgtime",
                "keywords": ["time", "effector", "mograph", "animation"],
                "description": "Creates a time MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "frequency": 1.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "sound_effector": {
                "name": "Sound Effector",
                "constant": "c4d.Omgsound",
                "keywords": ["sound", "effector", "mograph", "audio"],
                "description": "Creates a sound MoGraph effector",
                "parameters": {
                    "strength": 1.0,
                    "uniformity": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            }
        }
        
    def _get_default_deformers(self) -> Dict[str, Any]:
        """Get default Cinema4D deformer definitions (10 working deformers discovered)"""
        return {
            "bend_deformer": {
                "name": "Bend Deformer",
                "constant": "c4d.Obend",
                "keywords": ["bend", "deformer", "curve", "arc"],
                "description": "Creates a bend deformer",
                "parameters": {
                    "strength": 0.0,
                    "angle": 0.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "bulge_deformer": {
                "name": "Bulge Deformer", 
                "constant": "c4d.Obulge",
                "keywords": ["bulge", "deformer", "inflate", "expand"],
                "description": "Creates a bulge deformer",
                "parameters": {
                    "strength": 0.0,
                    "curvature": 1.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "explosion_deformer": {
                "name": "Explosion Deformer",
                "constant": "c4d.Oexplosion",
                "keywords": ["explosion", "deformer", "blast", "scatter"],
                "description": "Creates an explosion deformer",
                "parameters": {
                    "strength": 0.0,
                    "size": 100.0,
                    "angle": 1.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "explosionfx_deformer": {
                "name": "ExplosionFX Deformer",
                "constant": "c4d.Oexplosionfx",
                "keywords": ["explosionfx", "deformer", "blast", "fx"],
                "description": "Creates an explosion FX deformer",
                "parameters": {
                    "strength": 1000.0,
                    "size": 10.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "formula_deformer": {
                "name": "Formula Deformer",
                "constant": "c4d.Oformula",
                "keywords": ["formula", "deformer", "math", "expression"],
                "description": "Creates a formula deformer",
                "parameters": {
                    "size": 400.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "melt_deformer": {
                "name": "Melt Deformer",
                "constant": "c4d.Omelt",
                "keywords": ["melt", "deformer", "drip", "liquid"],
                "description": "Creates a melt deformer",
                "parameters": {
                    "strength": 1.0,
                    "size": 100.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "shatter_deformer": {
                "name": "Shatter Deformer",
                "constant": "c4d.Oshatter",
                "keywords": ["shatter", "deformer", "break", "fracture"],
                "description": "Creates a shatter deformer",
                "parameters": {
                    "strength": 1.0,
                    "size": 100.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "shear_deformer": {
                "name": "Shear Deformer",
                "constant": "c4d.Oshear",
                "keywords": ["shear", "deformer", "skew", "slant"],
                "description": "Creates a shear deformer",
                "parameters": {
                    "strength": 0.0,
                    "angle": 0.0,
                    "curvature": 1.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "spherify_deformer": {
                "name": "Spherify Deformer",
                "constant": "c4d.Ospherify",
                "keywords": ["spherify", "deformer", "sphere", "round"],
                "description": "Creates a spherify deformer",
                "parameters": {
                    "strength": 0.5,
                    "size": 200.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            },
            "taper_deformer": {
                "name": "Taper Deformer",
                "constant": "c4d.Otaper", 
                "keywords": ["taper", "deformer", "scale", "narrow"],
                "description": "Creates a taper deformer",
                "parameters": {
                    "strength": 0.0,
                    "curvature": 1.0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0
                }
            }
        }
    
    def _get_default_fields(self) -> Dict[str, Any]:
        """Get default field definitions"""
        return {
            "linear_field": {
                "name": "Linear Field",
                "constant": "c4d.Flinear",
                "keywords": ["linear", "field", "gradient", "direction"],
                "description": "Creates a linear field with directional gradient",
                "parameters": {
                    "name": "Linear Field",
                    "length": 200.0,
                    "clip_to_shape": False,
                    "direction": 2
                }
            },
            "spherical_field": {
                "name": "Spherical Field",
                "constant": "c4d.Fspherical",
                "keywords": ["spherical", "field", "radial", "sphere"],
                "description": "Creates a spherical field with radial falloff",
                "parameters": {
                    "name": "Spherical Field",
                    "size": 200.0,
                    "clip_to_shape": False
                }
            },
            "box_field": {
                "name": "Box Field",
                "constant": "c4d.Fbox",
                "keywords": ["box", "field", "rectangular", "cube"],
                "description": "Creates a box-shaped field",
                "parameters": {
                    "name": "Box Field",
                    "size": 200.0,
                    "clip_to_shape": False
                }
            },
            "cylinder_field": {
                "name": "Cylinder Field",
                "constant": "c4d.Fcylinder",
                "keywords": ["cylinder", "field", "cylindrical", "tube"],
                "description": "Creates a cylindrical field",
                "parameters": {
                    "name": "Cylinder Field",
                    "radius": 100.0,
                    "height": 200.0,
                    "offset": 0.0,
                    "remap": "None"
                }
            },
            "cone_field": {
                "name": "Cone Field",
                "constant": "c4d.Fcone",
                "keywords": ["cone", "field", "conical"],
                "description": "Creates a cone-shaped field",
                "parameters": {
                    "name": "Cone Field",
                    "radius": 100.0,
                    "height": 200.0,
                    "offset": 0.0,
                    "remap": "None"
                }
            },
            "torus_field": {
                "name": "Torus Field",
                "constant": "c4d.Ftorus",
                "keywords": ["torus", "field", "donut", "ring"],
                "description": "Creates a torus-shaped field",
                "parameters": {
                    "name": "Torus Field",
                    "radius": 100.0,
                    "inner_radius": 50.0,
                    "offset": 0.0,
                    "remap": "None"
                }
            },
            "formula_field": {
                "name": "Formula Field",
                "constant": "c4d.Fformula",
                "keywords": ["formula", "field", "math", "expression"],
                "description": "Creates a field based on mathematical formulas",
                "parameters": {
                    "name": "Formula Field",
                    "formula": "sin(x)",
                    "size": 200.0,
                    "offset": 0.0,
                    "remap": "None"
                }
            },
            "random_field": {
                "name": "Random Field",
                "constant": "c4d.Frandom",
                "keywords": ["random", "field", "noise", "variation"],
                "description": "Creates a random noise-based field",
                "parameters": {
                    "name": "Random Field",
                    "seed": 1234,
                    "noise": "Perlin",
                    "scale": 100.0,
                    "offset": 0.0
                }
            },
            "radial_field": {
                "name": "Radial Field",
                "constant": "c4d.Fradial",
                "keywords": ["radial", "field", "circular", "round"],
                "description": "Creates a radial field pattern",
                "parameters": {
                    "name": "Radial Field",
                    "radius": 200.0,
                    "falloff": "Linear",
                    "offset": 0.0,
                    "remap": "None"
                }
            },
            "sound_field": {
                "name": "Sound Field",
                "constant": "c4d.Fsound",
                "keywords": ["sound", "field", "audio", "frequency"],
                "description": "Creates a sound-reactive field",
                "parameters": {
                    "name": "Sound Field",
                    "frequency": 440.0,
                    "amplitude": 100.0,
                    "offset": 0.0,
                    "remap": "None"
                }
            },
            "shader_field": {
                "name": "Shader Field",
                "constant": "c4d.Fshader",
                "keywords": ["shader", "field", "texture", "material"],
                "description": "Creates a field based on shader values",
                "parameters": {
                    "name": "Shader Field",
                    "channel": "Alpha",
                    "offset": 0.0,
                    "remap": "None"
                }
            },
            "python_field": {
                "name": "Python Field",
                "constant": "c4d.Fpython",
                "keywords": ["python", "field", "script", "code"],
                "description": "Creates a field using Python scripts",
                "parameters": {
                    "name": "Python Field",
                    "script": "# Python field script",
                    "offset": 0.0,
                    "remap": "None"
                }
            }
        }
    
    def _get_default_models(self) -> Dict[str, Any]:
        """Get default 3D models import commands"""
        return {
            "import_selected": {
                "name": "Import Selected Models",
                "constant": "import_selected",
                "keywords": ["import", "selected", "models", "all", "batch"],
                "description": "Import all selected 3D models from Tab 2 with transform settings",
                "parameters": {
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0,
                    "scale": 1.0,
                    "rotation_x": 0.0,
                    "rotation_y": 0.0,
                    "rotation_z": 0.0
                }
            },
            "import_single": {
                "name": "Import Single Model",
                "constant": "import_single",
                "keywords": ["import", "single", "model", "one", "index"],
                "description": "Import a specific 3D model by index from selected models",
                "parameters": {
                    "model_index": 0,
                    "pos_x": 0,
                    "pos_y": 0,
                    "pos_z": 0,
                    "scale": 1.0
                }
            },
            "import_to_cloner": {
                "name": "Import to Cloner",
                "constant": "import_to_cloner",
                "keywords": ["import", "cloner", "clone", "mograph", "duplicate"],
                "description": "Import selected 3D models into a cloner object for duplication",
                "parameters": {
                    "cloner_mode": "grid",
                    "count": 10,
                    "spacing": 100.0
                }
            },
            "import_with_softbody": {
                "name": "Import with Soft Body",
                "constant": "import_with_softbody",
                "keywords": ["import", "softbody", "physics", "deform", "dynamics"],
                "description": "Import selected 3D models and apply soft body physics simulation",
                "parameters": {
                    "pos_x": 0,
                    "pos_y": 500,
                    "pos_z": 0,
                    "scale": 1.0,
                    "mass": 1.0,
                    "bounce": 0.3
                }
            },
            "import_with_rigidbody": {
                "name": "Import with Rigid Body",
                "constant": "import_with_rigidbody",
                "keywords": ["import", "rigidbody", "physics", "collision", "dynamics"],
                "description": "Import selected 3D models and apply rigid body physics simulation",
                "parameters": {
                    "pos_x": 0,
                    "pos_y": 500,
                    "pos_z": 0,
                    "scale": 1.0,
                    "mass": 1.0,
                    "friction": 0.3
                }
            },
            "import_with_cloth": {
                "name": "Import with Cloth Physics",
                "constant": "import_with_cloth",
                "keywords": ["import", "cloth", "soft", "fabric", "physics", "deform"],
                "description": "Import selected 3D models and apply cloth/soft body physics simulation",
                "parameters": {
                    "pos_x": 0,
                    "pos_y": 500,
                    "pos_z": 0,
                    "scale": 1.0,
                    "cloth_type": "cloth",
                    "mass": 1.0
                }
            },
            "quick_import": {
                "name": "Quick Import Grid",
                "constant": "quick_import",
                "keywords": ["quick", "import", "grid", "layout", "automatic"],
                "description": "Quick import selected 3D models in automatic grid layout",
                "parameters": {
                    "spacing_x": 200.0,
                    "spacing_y": 0.0,
                    "spacing_z": 200.0
                }
            }
        }
    
    def _get_default_tags(self) -> Dict[str, Any]:
        """Get default tag definitions - will be updated with accurate Cinema4D discovery results"""
        return {
            "phong_tag": {
                "name": "Phong Tag",
                "constant": "c4d.Tphong",
                "keywords": ["phong", "tag", "shading", "smooth"],
                "description": "Creates a phong shading tag",
                "parameters": {
                    "name": "Phong Tag",
                    "angle": 80.0
                }
            },
            "material_tag": {
                "name": "Material Tag",
                "constant": "c4d.Tmaterial",
                "keywords": ["material", "tag", "texture", "shader"],
                "description": "Creates a material tag",
                "parameters": {
                    "name": "Material Tag"
                }
            },
            "texture_tag": {
                "name": "Texture Tag", 
                "constant": "c4d.Ttexture",
                "keywords": ["texture", "tag", "uv", "mapping"],
                "description": "Creates a texture tag",
                "parameters": {
                    "name": "Texture Tag",
                    "projection": "UVW Mapping"
                }
            },
            "uvw_tag": {
                "name": "UVW Tag",
                "constant": "c4d.Tuvw",
                "keywords": ["uvw", "tag", "mapping", "coordinates"],
                "description": "Creates a UVW mapping tag",
                "parameters": {
                    "name": "UVW Tag"
                }
            },
            "selection_tag": {
                "name": "Selection Tag",
                "constant": "c4d.Tselection",
                "keywords": ["selection", "tag", "group", "set"],
                "description": "Creates a selection tag",
                "parameters": {
                    "name": "Selection Tag"
                }
            },
            "python_tag": {
                "name": "Python Tag",
                "constant": "c4d.Tpython",
                "keywords": ["python", "tag", "script", "code"],
                "description": "Creates a python tag",
                "parameters": {
                    "name": "Python Tag"
                }
            },
            "expression_tag": {
                "name": "Expression Tag",
                "constant": "c4d.Texpression",
                "keywords": ["expression", "tag", "formula", "math"],
                "description": "Creates an expression tag",
                "parameters": {
                    "name": "Expression Tag"
                }
            },
            "protection_tag": {
                "name": "Protection Tag",
                "constant": "c4d.Tprotection",
                "keywords": ["protection", "tag", "lock", "prevent"],
                "description": "Creates a protection tag",
                "parameters": {
                    "name": "Protection Tag"
                }
            },
            "display_tag": {
                "name": "Display Tag",
                "constant": "c4d.Tdisplay",
                "keywords": ["display", "tag", "visibility", "show"],
                "description": "Creates a display tag",
                "parameters": {
                    "name": "Display Tag"
                }
            },
            "compositing_tag": {
                "name": "Compositing Tag",
                "constant": "c4d.Tcompositing",
                "keywords": ["compositing", "tag", "render", "pass"],
                "description": "Creates a compositing tag",
                "parameters": {
                    "name": "Compositing Tag"
                }
            }
        }
        
    def load_category_data(self):
        """Load data for the current category"""
        category = self.current_category
        list_widget = self.list_widgets.get(category)
        
        # DEBUG: Print what we're trying to load
        logger.info(f"[NLP DEBUG] Loading category: {category}")
        logger.info(f"[NLP DEBUG] Available categories: {list(self.categories.keys())}")
        logger.info(f"[NLP DEBUG] Dictionary data keys: {list(self.dictionary_data.keys())}")
        
        if not list_widget:
            logger.warning(f"[NLP DEBUG] No list widget found for category: {category}")
            return
            
        list_widget.clear()
        
        # Get commands for this category
        commands = self.dictionary_data.get(category, {})
        logger.info(f"[NLP DEBUG] Commands for {category}: {list(commands.keys())}")
        
        # Add items to list
        for cmd_id, cmd_data in commands.items():
            item = QListWidgetItem(cmd_data.get("name", cmd_id))
            item.setData(Qt.UserRole, cmd_id)
            list_widget.addItem(item)
            logger.info(f"[NLP DEBUG] Added item: {cmd_data.get('name', cmd_id)}")
        
        logger.info(f"[NLP DEBUG] Total items added to {category}: {list_widget.count()}")
            
    def _on_tab_changed(self, index: int):
        """Handle tab change"""
        category_list = list(self.categories.keys())
        if 0 <= index < len(category_list):
            self.current_category = category_list[index]
            self.load_category_data()
            
    def _on_selection_changed(self, category: str):
        """Handle selection change in command list"""
        list_widget = self.list_widgets.get(category)
        if not list_widget:
            return
            
        current_item = list_widget.currentItem()
        if not current_item:
            return
            
        cmd_id = current_item.data(Qt.UserRole)
        cmd_data = self.dictionary_data.get(category, {}).get(cmd_id, {})
        
        # Update detail fields
        self._update_detail_fields(category, cmd_data)
        
    def _update_detail_fields(self, category: str, cmd_data: Dict[str, Any]):
        """Update the detail panel fields"""
        panel = self.detail_panels.get(category)
        if not panel:
            return
            
        # Update name
        name_edit = panel.findChild(QLineEdit, f"{category}_name")
        if name_edit:
            name_edit.setText(cmd_data.get("name", ""))
            
        # Update constant
        constant_edit = panel.findChild(QLineEdit, f"{category}_constant")
        if constant_edit:
            constant_edit.setText(cmd_data.get("constant", ""))
            
        # Update keywords
        keywords_edit = panel.findChild(QTextEdit, f"{category}_keywords")
        if keywords_edit:
            keywords = cmd_data.get("keywords", [])
            keywords_edit.setPlainText(", ".join(keywords) if isinstance(keywords, list) else keywords)
            
        # Update description
        desc_edit = panel.findChild(QTextEdit, f"{category}_description")
        if desc_edit:
            desc_edit.setPlainText(cmd_data.get("description", ""))
            
        # Update parameters dynamically
        self._update_parameter_fields(category, cmd_data)
                    
    def _update_parameter_fields(self, category: str, cmd_data: Dict[str, Any]):
        """Update parameter fields dynamically based on command type"""
        container = self.param_containers.get(category)
        if not container:
            return
            
        # Clear existing parameter fields
        layout = container.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get command name to determine parameter structure
        cmd_name = cmd_data.get("name", "").lower()
        cmd_id = ""
        
        # Find command ID from list widget selection
        list_widget = self.list_widgets.get(category)
        if list_widget and list_widget.currentItem():
            cmd_id = list_widget.currentItem().data(Qt.UserRole)
        
        # Get parameter definitions for this primitive
        param_defs = self._get_parameter_definitions(category, cmd_id)
        if not param_defs:
            return
            
        # Create parameter fields
        params = cmd_data.get("parameters", {})
        row = 0
        
        # Always add position fields first
        for pos_param in ["pos_x", "pos_y", "pos_z"]:
            label = QLabel(f"{pos_param.replace('_', ' ').title()}:")
            widget = QSpinBox()
            widget.setMinimum(-10000)
            widget.setMaximum(10000)
            widget.setValue(params.get(pos_param, 0))
            widget.setObjectName(f"{category}_{cmd_id}_{pos_param}")
            layout.addWidget(label, row, 0)
            layout.addWidget(widget, row, 1)
            row += 1
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Add specific parameters for this primitive
        for param_name, param_info in param_defs.items():
            if param_name.startswith("pos_"):  # Skip position, already added
                continue
                
            label = QLabel(f"{param_info['label']}:")
            
            # Create appropriate widget based on type
            if param_info['type'] == 'int':
                widget = QSpinBox()
                widget.setMinimum(param_info.get('min', 0))
                widget.setMaximum(param_info.get('max', 10000))
                widget.setValue(params.get(param_name, param_info.get('default', 0)))
            elif param_info['type'] == 'float':
                from PySide6.QtWidgets import QDoubleSpinBox
                widget = QDoubleSpinBox()
                widget.setMinimum(param_info.get('min', 0.0))
                widget.setMaximum(param_info.get('max', 10000.0))
                widget.setSingleStep(0.01)
                widget.setDecimals(2)
                widget.setValue(params.get(param_name, param_info.get('default', 0.0)))
            elif param_info['type'] == 'bool':
                widget = QCheckBox()
                widget.setChecked(params.get(param_name, param_info.get('default', False)))
            elif param_info['type'] == 'choice':
                widget = QComboBox()
                for choice_value, choice_label in param_info['choices'].items():
                    widget.addItem(choice_label, choice_value)
                current_value = params.get(param_name, param_info.get('default', 0))
                index = widget.findData(current_value)
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif param_info['type'] == 'str':
                widget = QLineEdit()
                widget.setText(params.get(param_name, param_info.get('default', "")))
            else:
                continue
                
            widget.setObjectName(f"{category}_{cmd_id}_{param_name}")
            layout.addWidget(label, row, 0)
            layout.addWidget(widget, row, 1)
            row += 1
    
    def _get_parameter_definitions(self, category: str, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for a specific command"""
        if category == "primitives":
            return self._get_primitive_parameters(cmd_id)
        elif category == "generators":
            return self._get_generator_parameters(cmd_id)
        elif category == "splines":
            return self._get_splines_parameters(cmd_id)
        elif category == "cameras_lights":
            return self._get_cameras_lights_parameters(cmd_id)
        elif category == "effectors":
            # Transform effector IDs: "plain_effector" -> "plain"
            transformed_id = cmd_id.replace("_effector", "")
            return self._get_effectors_parameters(transformed_id)
        elif category == "deformers":
            # Transform deformer IDs: "bend_deformer" -> "bend"  
            transformed_id = cmd_id.replace("_deformer", "")
            return self._get_deformers_parameters(transformed_id)
        elif category == "fields":
            # Transform field IDs: "linear_field" -> "linear"
            transformed_id = cmd_id.replace("_field", "")
            return self._get_fields_parameters(transformed_id)
        elif category == "tags":
            # Transform tag IDs: "phong_tag" -> "phong"
            transformed_id = cmd_id.replace("_tag", "")
            return self._get_tags_parameters(transformed_id)
        elif category == "models":
            # 3D Models import commands - no transformation needed
            return self._get_models_parameters(cmd_id)
        else:
            return {}  # TODO: Add support for other categories
    
    def _get_primitive_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for primitives"""
            
        # Parameter definitions for each primitive type
        primitive_params = {
            "sphere": {
                "radius": {"label": "Radius", "type": "int", "min": 1, "max": 5000, "default": 100},
                "segments": {"label": "Segments", "type": "int", "min": 3, "max": 200, "default": 24},
                "type": {
                    "label": "Type", 
                    "type": "choice", 
                    "choices": {0: "Standard", 1: "Tetrahedron", 2: "Octahedron", 3: "Icosahedron", 4: "Hemisphere"},
                    "default": 0
                },
                "render_perfect": {"label": "Render Perfect", "type": "bool", "default": True}
            },
            "cube": {
                "size_x": {"label": "Size X", "type": "int", "min": 1, "max": 10000, "default": 200},
                "size_y": {"label": "Size Y", "type": "int", "min": 1, "max": 10000, "default": 200},
                "size_z": {"label": "Size Z", "type": "int", "min": 1, "max": 10000, "default": 200},
                "segments": {"label": "Segments", "type": "int", "min": 1, "max": 100, "default": 1}
            },
            "cylinder": {
                "radius": {"label": "Radius", "type": "int", "min": 1, "max": 5000, "default": 50},
                "height": {"label": "Height", "type": "int", "min": 1, "max": 10000, "default": 200},
                "segments": {"label": "Segments", "type": "int", "min": 3, "max": 200, "default": 36},
                "caps": {"label": "Caps", "type": "bool", "default": True}
            },
            "cone": {
                "bottom_radius": {"label": "Bottom Radius", "type": "int", "min": 0, "max": 5000, "default": 100},
                "top_radius": {"label": "Top Radius", "type": "int", "min": 0, "max": 5000, "default": 0},
                "height": {"label": "Height", "type": "int", "min": 1, "max": 10000, "default": 200},
                "segments": {"label": "Segments", "type": "int", "min": 3, "max": 200, "default": 36}
            },
            "torus": {
                "ring_radius": {"label": "Ring Radius", "type": "int", "min": 1, "max": 5000, "default": 100},
                "pipe_radius": {"label": "Pipe Radius", "type": "int", "min": 1, "max": 5000, "default": 20},
                "ring_segments": {"label": "Ring Segments", "type": "int", "min": 3, "max": 200, "default": 36},
                "pipe_segments": {"label": "Pipe Segments", "type": "int", "min": 3, "max": 200, "default": 18}
            },
            "plane": {
                "width": {"label": "Width", "type": "int", "min": 1, "max": 10000, "default": 400},
                "height": {"label": "Height", "type": "int", "min": 1, "max": 10000, "default": 400},
                "width_segments": {"label": "Width Segments", "type": "int", "min": 1, "max": 100, "default": 1},
                "height_segments": {"label": "Height Segments", "type": "int", "min": 1, "max": 100, "default": 1}
            },
            "disc": {
                "outer_radius": {"label": "Outer Radius", "type": "int", "min": 1, "max": 5000, "default": 100},
                "inner_radius": {"label": "Inner Radius", "type": "int", "min": 0, "max": 5000, "default": 0},
                "segments": {"label": "Segments", "type": "int", "min": 3, "max": 200, "default": 36}
            },
            "pyramid": {
                "size_x": {"label": "Size X", "type": "int", "min": 1, "max": 10000, "default": 200},
                "size_y": {"label": "Size Y", "type": "int", "min": 1, "max": 10000, "default": 200},
                "size_z": {"label": "Size Z", "type": "int", "min": 1, "max": 10000, "default": 200}
            },
            "tube": {
                "inner_radius": {"label": "Inner Radius", "type": "int", "min": 1, "max": 5000, "default": 50},
                "outer_radius": {"label": "Outer Radius", "type": "int", "min": 1, "max": 5000, "default": 100},
                "height": {"label": "Height", "type": "int", "min": 1, "max": 10000, "default": 200},
                "segments": {"label": "Segments", "type": "int", "min": 3, "max": 200, "default": 36}
            },
            "figure": {
                "size": {"label": "Size", "type": "int", "min": 1, "max": 10000, "default": 200}
            },
            "platonic": {
                "size": {"label": "Size", "type": "int", "min": 1, "max": 5000, "default": 100},
                "type": {
                    "label": "Type",
                    "type": "choice",
                    "choices": {0: "Tetrahedron", 1: "Hexahedron", 2: "Octahedron", 3: "Dodecahedron", 4: "Icosahedron"},
                    "default": 0
                }
            },
            "landscape": {
                "size": {"label": "Size", "type": "int", "min": 1, "max": 50000, "default": 1000}
            },
            "oil_tank": {
                "radius": {"label": "Radius", "type": "int", "min": 1, "max": 5000, "default": 100},
                "height": {"label": "Height", "type": "int", "min": 1, "max": 10000, "default": 200}
            },
            "capsule": {
                "radius": {"label": "Radius", "type": "int", "min": 1, "max": 5000, "default": 50},
                "height": {"label": "Height", "type": "int", "min": 1, "max": 10000, "default": 200}
            },
            "relief": {
                "size": {"label": "Size", "type": "int", "min": 1, "max": 10000, "default": 400}
            },
            "single_polygon": {
                "size": {"label": "Size", "type": "int", "min": 1, "max": 10000, "default": 200}
            },
            "fractal": {
                "size": {"label": "Size", "type": "int", "min": 1, "max": 10000, "default": 200},
                "iterations": {"label": "Iterations", "type": "int", "min": 1, "max": 10, "default": 3}
            },
            "formula": {
                "size": {"label": "Size", "type": "int", "min": 1, "max": 10000, "default": 200}
            }
        }
        
        return primitive_params.get(cmd_id, {})
    
    def _get_generator_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for generators"""
        generator_params = {
            "array": {
                "copies": {"label": "Copies", "type": "int", "min": 1, "max": 1000, "default": 7},
                "radius": {"label": "Radius", "type": "float", "min": 0.0, "max": 10000.0, "default": 250.0},
                "amplitude": {"label": "Amplitude", "type": "float", "min": -1000.0, "max": 1000.0, "default": 0.0},
                "frequency": {"label": "Frequency", "type": "float", "min": 0.0, "max": 100.0, "default": 0.0}
            },
            "boolean": {
                "type": {
                    "label": "Boolean Type",
                    "type": "choice", 
                    "choices": {0: "Union (A + B)", 1: "Subtract (A - B)", 2: "Intersect (A ∩ B)", 3: "Without (A without B)"},
                    "default": 1
                },
                "single_object": {"label": "Create Single Object", "type": "bool", "default": True},
                "hide_new_edges": {"label": "Hide New Edges", "type": "bool", "default": True}
            },
            "cloner": {
                "mode": {
                    "label": "Cloner Mode",
                    "type": "choice", 
                    "choices": {0: "Object", 1: "Linear", 2: "Radial", 3: "Grid", 4: "Honeycomb"},
                    "default": 2
                },
                "clones": {"label": "Clones", "type": "int", "min": 1, "max": 10000, "default": 1},
                "count": {"label": "Grid Count", "type": "int", "min": 1, "max": 100, "default": 3},
                "count_x": {"label": "Count X", "type": "int", "min": 1, "max": 100, "default": 3},
                "count_y": {"label": "Count Y", "type": "int", "min": 1, "max": 100, "default": 1}, 
                "count_z": {"label": "Count Z", "type": "int", "min": 1, "max": 100, "default": 3},
                "size": {"label": "Grid Size", "type": "float", "min": 1.0, "max": 10000.0, "default": 200.0},
                "size_x": {"label": "Size X", "type": "float", "min": 1.0, "max": 10000.0, "default": 200.0},
                "size_y": {"label": "Size Y", "type": "float", "min": 1.0, "max": 10000.0, "default": 200.0},
                "size_z": {"label": "Size Z", "type": "float", "min": 1.0, "max": 10000.0, "default": 200.0},
                "fill": {"label": "Fill", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
                "reset_coordinates": {"label": "Reset Coordinates", "type": "bool", "default": True}
            },
            "extrude": {
                "isoparm": {"label": "Isoparm", "type": "int", "min": 1, "max": 100, "default": 10},
                "sub": {"label": "Subdivision", "type": "int", "min": 0, "max": 100, "default": 1},
                "move": {"label": "Movement", "type": "float", "min": -10000.0, "max": 10000.0, "default": 100.0},
                "flipnormals": {"label": "Flip Normals", "type": "bool", "default": False},
                "hierarchic": {"label": "Hierarchic", "type": "bool", "default": False}
            },
            "lathe": {
                "isoparm": {"label": "Isoparm", "type": "int", "min": 1, "max": 100, "default": 10},
                "sub": {"label": "Subdivision", "type": "int", "min": 3, "max": 200, "default": 32},
                "move": {"label": "Movement", "type": "float", "min": -1000.0, "max": 1000.0, "default": 0.0},
                "scale": {"label": "Scale", "type": "float", "min": 0.1, "max": 10.0, "default": 1.0},
                "rotate": {"label": "Rotation", "type": "float", "min": 0.0, "max": 6.28, "default": 6.28},
                "flipnormals": {"label": "Flip Normals", "type": "bool", "default": False}
            },
            "loft": {
                "isoparm": {"label": "Isoparm", "type": "int", "min": 1, "max": 100, "default": 10},
                "subx": {"label": "Subdivision X", "type": "int", "min": 1, "max": 200, "default": 16},
                "suby": {"label": "Subdivision Y", "type": "int", "min": 1, "max": 200, "default": 4},
                "closey": {"label": "Close Y", "type": "bool", "default": False},
                "flipnormals": {"label": "Flip Normals", "type": "bool", "default": False},
                "linear": {"label": "Linear", "type": "bool", "default": False},
                "organic": {"label": "Organic", "type": "bool", "default": False},
                "adaptivey": {"label": "Adaptive Y", "type": "bool", "default": True},
                "fituv": {"label": "Fit UV", "type": "bool", "default": True}
            },
            "sweep": {
                "isoparm": {"label": "Isoparm", "type": "int", "min": 1, "max": 100, "default": 10},
                "growth": {"label": "Growth", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "scale": {"label": "Scale", "type": "float", "min": 0.1, "max": 10.0, "default": 1.0},
                "rotate": {"label": "Rotation", "type": "float", "min": -6.28, "max": 6.28, "default": 0.0},
                "parallel": {"label": "Parallel", "type": "bool", "default": False},
                "constant": {"label": "Constant Cross Section", "type": "bool", "default": True},
                "banking": {"label": "Banking", "type": "bool", "default": True},
                "flipnormals": {"label": "Flip Normals", "type": "bool", "default": False},
                "startgrowth": {"label": "Start Growth", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0}
            },
            "subdivision_surface": {
                "subdivision_editor": {"label": "Editor Subdivision", "type": "int", "min": 0, "max": 6, "default": 1},
                "subdivision_render": {"label": "Render Subdivision", "type": "int", "min": 0, "max": 6, "default": 2},
                "type": {
                    "label": "Type",
                    "type": "choice",
                    "choices": {0: "Catmull-Clark", 1: "Loop", 2: "Catmull-Clark (N-Gons)"},
                    "default": 0
                },
                "boundary_mode": {
                    "label": "Boundary",
                    "type": "choice",
                    "choices": {0: "None", 1: "Corner", 2: "Edge"},
                    "default": 0
                }
            },
            "symmetry": {
                "mirror_plane": {
                    "label": "Mirror Plane",
                    "type": "choice",
                    "choices": {0: "YZ", 1: "ZX", 2: "XY"},
                    "default": 0
                },
                "weld_points": {"label": "Weld Points", "type": "bool", "default": True},
                "tolerance": {"label": "Tolerance", "type": "float", "min": 0.0, "max": 100.0, "default": 0.01},
                "flip": {"label": "Flip", "type": "bool", "default": False}
            },
            "instance": {
                "render_instances": {"label": "Render Instances", "type": "bool", "default": True},
                "multi_instances": {"label": "Multi-Instances", "type": "bool", "default": False}
            },
            "metaball": {
                "threshold": {"label": "Threshold", "type": "float", "min": 0.1, "max": 10.0, "default": 1.0},
                "subeditor": {"label": "Editor Subdivision", "type": "int", "min": 1, "max": 100, "default": 40},
                "subray": {"label": "Render Subdivision", "type": "int", "min": 1, "max": 100, "default": 5},
                "exponential": {"label": "Exponential", "type": "bool", "default": False},
                "accuratenormals": {"label": "Accurate Normals", "type": "bool", "default": False}
            },
            "bezier": {
                "subdivision": {"label": "Subdivision", "type": "int", "min": 1, "max": 200, "default": 20}
            },
            "connect": {
                "weld": {"label": "Weld", "type": "bool", "default": True},
                "tolerance": {"label": "Tolerance", "type": "float", "min": 0.0, "max": 100.0, "default": 0.01},
                "phong_tag": {"label": "Phong Tag", "type": "bool", "default": True},
                "center_axis": {"label": "Center Axis", "type": "bool", "default": False}
            },
            "spline_wrap": {
                "axis": {
                    "label": "Axis",
                    "type": "choice",
                    "choices": {0: "X", 1: "Y", 2: "Z"},
                    "default": 2
                },
                "offset": {"label": "Offset", "type": "int", "min": -10000, "max": 10000, "default": 0},
                "size": {"label": "Size", "type": "int", "min": 0, "max": 10000, "default": 100},
                "rotation": {"label": "Rotation", "type": "int", "min": -360, "max": 360, "default": 0}
            },
            "polygon_reduction": {
                "reduction_strength": {"label": "Reduction Strength", "type": "int", "min": 0, "max": 100, "default": 50},
                "boundary_curve_preservation": {"label": "Boundary Preservation", "type": "int", "min": 0, "max": 100, "default": 100},
                "preserve_3d_boundary": {"label": "Preserve 3D Boundary", "type": "bool", "default": True}
            }
        }
        
        return generator_params.get(cmd_id, {})
    
    def _get_splines_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for splines"""
        
        spline_params = {
            "circle": {
                "circle_ellipse": {"label": "Ellipse", "type": "bool", "default": False},
                "circle_radius": {"label": "Radius", "type": "float", "min": 1.0, "max": 1000.0, "default": 200.0},
                "circle_inner": {"label": "Inner Radius", "type": "float", "min": 0.0, "max": 1000.0, "default": 100.0}
            },
            "rectangle": {
                "rectangle_width": {"label": "Width", "type": "float", "min": 1.0, "max": 1000.0, "default": 400.0},
                "rectangle_height": {"label": "Height", "type": "float", "min": 1.0, "max": 1000.0, "default": 400.0},
                "rectangle_radius": {"label": "Corner Radius", "type": "float", "min": 0.0, "max": 200.0, "default": 50.0},
                "rectangle_rounding": {"label": "Rounding", "type": "bool", "default": False}
            },
            "text": {
                "text_text": {"label": "Text", "type": "str", "default": "Text"},
                "text_height": {"label": "Height", "type": "float", "min": 1.0, "max": 1000.0, "default": 200.0},
                "text_hspacing": {"label": "H Spacing", "type": "float", "min": -100.0, "max": 100.0, "default": 0.0},
                "text_vspacing": {"label": "V Spacing", "type": "float", "min": -100.0, "max": 100.0, "default": 0.0},
                "text_align": {
                    "label": "Alignment",
                    "type": "choice", 
                    "choices": {0: "Left", 1: "Center", 2: "Right"},
                    "default": 0
                },
                "text_separate": {"label": "Separate", "type": "bool", "default": False}
            },
            "helix": {
                "helix_start": {"label": "Start Angle", "type": "float", "min": 0.0, "max": 360.0, "default": 0.0},
                "helix_end": {"label": "End Angle", "type": "float", "min": 0.0, "max": 720.0, "default": 360.0},
                "helix_height": {"label": "Height", "type": "float", "min": 1.0, "max": 1000.0, "default": 200.0},
                "helix_radius1": {"label": "Start Radius", "type": "float", "min": 1.0, "max": 1000.0, "default": 200.0},
                "helix_radius2": {"label": "End Radius", "type": "float", "min": 1.0, "max": 1000.0, "default": 200.0},
                "helix_sub": {"label": "Subdivisions", "type": "int", "min": 3, "max": 1000, "default": 100}
            },
            "star": {
                "star_points": {"label": "Points", "type": "int", "min": 3, "max": 100, "default": 8},
                "star_orad": {"label": "Outer Radius", "type": "float", "min": 1.0, "max": 1000.0, "default": 200.0},
                "star_irad": {"label": "Inner Radius", "type": "float", "min": 0.0, "max": 1000.0, "default": 100.0},
                "star_twist": {"label": "Twist", "type": "float", "min": -360.0, "max": 360.0, "default": 0.0}
            }
        }
        
        return spline_params.get(cmd_id, {})
    
    def _get_cameras_lights_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for cameras and lights - USING VERIFIED DATA FROM DISCOVERY"""
        
        cameras_lights_params = {
            # CAMERAS - Only parameters that ACTUALLY WORK in Cinema4D
            "camera": {
                "fov": {"label": "FOV", "type": "float", "min": 0.1, "max": 3.14, "default": 0.9500215125301936},  # VERIFIED radians
                "targetdistance": {"label": "Target Distance", "type": "float", "min": 1.0, "max": 10000.0, "default": 2000.0},  # VERIFIED
                "film_offset_x": {"label": "Film Offset X", "type": "float", "min": -1000.0, "max": 1000.0, "default": 0.0},  # VERIFIED
                "film_offset_y": {"label": "Film Offset Y", "type": "float", "min": -1000.0, "max": 1000.0, "default": 0.0},  # VERIFIED
                "projection": {
                    "label": "Projection Type",
                    "type": "choice",
                    "choices": {0: "Perspective", 1: "Parallel"},
                    "default": 0  # VERIFIED
                }
            },
            # LIGHTS - Only parameters that ACTUALLY WORK in Cinema4D
            "light": {
                "brightness": {"label": "Intensity", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},  # VERIFIED
                "type": {
                    "label": "Light Type", 
                    "type": "choice",
                    "choices": {0: "Omni", 1: "Spot", 2: "Infinite", 3: "Area"},
                    "default": 0  # VERIFIED
                },
                "shadowtype": {
                    "label": "Shadow Type",
                    "type": "choice", 
                    "choices": {0: "None", 1: "Shadow Maps", 2: "Raytraced"},
                    "default": 0  # VERIFIED
                },
                "outerangle": {"label": "Spot Outer Angle", "type": "float", "min": 0.0, "max": 3.14, "default": 0.5235987755982988},  # VERIFIED radians
                "innerangle": {"label": "Spot Inner Angle", "type": "float", "min": 0.0, "max": 3.14, "default": 0.0},  # VERIFIED radians
                "falloff": {
                    "label": "Falloff Type",
                    "type": "choice",
                    "choices": {0: "None", 1: "Linear", 2: "Inverse Square"},
                    "default": 0  # VERIFIED
                }
            }
        }
        
        return cameras_lights_params.get(cmd_id, {})
    
    def _get_effectors_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for MoGraph effectors (23 objects discovered)"""
        
        effectors_params = {
            # Core MoGraph Effectors  
            "random": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "plain": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "shader": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "delay": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 0.5},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "formula": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "step": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "time": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "sound": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "inheritance": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "volume": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "python": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "weight": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "matrix": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "polyfx": {
                "strength": {"label": "Strength", "type": "int", "min": 0, "max": 100, "default": 0}
            },
            "pushapart": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "reeffector": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                "falloff": {"label": "Falloff", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "spline_wrap": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "tracer": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            # MoGraph Objects
            "fracture": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "moextrude": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "moinstance": {
                "falloff": {"label": "Falloff", "type": "int", "min": 0, "max": 100, "default": 10}
            },
            "spline_mask": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            },
            "voronoi_fracture": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0}
            }
        }
        
        return effectors_params.get(cmd_id, {})
    
    def _get_deformers_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for Cinema4D deformers (10 working objects discovered)"""
        
        deformers_params = {
            # Core Deformers (USING ACTUAL CINEMA4D VALUES FROM DISCOVERY)
            "bend": {
                "strength": {"label": "Strength", "type": "int", "min": -45, "max": 45, "default": 0},
                "angle": {"label": "Angle", "type": "int", "min": -180, "max": 180, "default": 0}
            },
            "bulge": {
                "strength": {"label": "Strength", "type": "int", "min": -10, "max": 10, "default": 0},
                "curvature": {"label": "Curvature", "type": "int", "min": 0, "max": 10, "default": 1}
            },
            "explosion": {
                "strength": {"label": "Strength", "type": "int", "min": 0, "max": 10, "default": 0},
                "size": {"label": "Size", "type": "int", "min": 10, "max": 1000, "default": 100},
                "angle": {"label": "Angle", "type": "int", "min": 0, "max": 10, "default": 1}
            },
            "explosionfx": {
                "strength": {"label": "Strength", "type": "int", "min": 0, "max": 2000, "default": 1000},
                "size": {"label": "Size", "type": "int", "min": 1, "max": 100, "default": 10}
            },
            "formula": {
                "size": {"label": "Size", "type": "int", "min": 100, "max": 1000, "default": 400}
            },
            "melt": {
                "strength": {"label": "Strength", "type": "int", "min": 0, "max": 5, "default": 1},
                "size": {"label": "Size", "type": "int", "min": 10, "max": 1000, "default": 100}
            },
            "shatter": {
                "strength": {"label": "Strength", "type": "int", "min": 0, "max": 5, "default": 1},
                "size": {"label": "Size", "type": "int", "min": 0, "max": 180, "default": 100}
            },
            "shear": {
                "strength": {"label": "Strength", "type": "int", "min": -45, "max": 45, "default": 0},
                "angle": {"label": "Angle", "type": "int", "min": -180, "max": 180, "default": 0},
                "curvature": {"label": "Curvature", "type": "int", "min": 0, "max": 10, "default": 1}
            },
            "spherify": {
                "strength": {"label": "Strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
                "size": {"label": "Size", "type": "int", "min": 10, "max": 1000, "default": 200}
            },
            "taper": {
                "strength": {"label": "Strength", "type": "int", "min": -10, "max": 10, "default": 0},
                "curvature": {"label": "Curvature", "type": "int", "min": 0, "max": 10, "default": 1}
            }
        }
        
        return deformers_params.get(cmd_id, {})
    
    def _get_fields_parameters(self, cmd_id: str) -> dict:
        """Get parameters for Fields category objects"""
        
        fields_params = {
            "linear": {
                "name": {"type": "text", "default": "Linear Field", "label": "Name"},
                "length": {"type": "float", "default": 200.0, "min": 0.1, "max": 1000.0, "label": "Length"},
                "clip_to_shape": {"type": "bool", "default": False, "label": "Clip to Shape"},
                "direction": {"type": "choice", "default": 2, "choices": {0: "X", 1: "Y", 2: "Z"}, "label": "Direction"}
            },
            "box": {
                "name": {"type": "text", "default": "Box Field", "label": "Name"},
                "size": {"type": "float", "default": 200.0, "min": 0.1, "max": 1000.0, "label": "Size"},
                "clip_to_shape": {"type": "bool", "default": False, "label": "Clip to Shape"}
            },
            "spherical": {
                "name": {"type": "text", "default": "Spherical Field", "label": "Name"},
                "size": {"type": "float", "default": 200.0, "min": 0.1, "max": 1000.0, "label": "Size"},
                "clip_to_shape": {"type": "bool", "default": False, "label": "Clip to Shape"}
            },
            "cylinder": {
                "name": {"type": "text", "default": "Cylinder Field", "label": "Name"},
                "direction": {"type": "choice", "default": 1, "choices": {0: "X", 1: "Y", 2: "Z"}, "label": "Direction"},
                "height": {"type": "float", "default": 200.0, "min": 0.1, "max": 1000.0, "label": "Height"},
                "radius": {"type": "float", "default": 100.0, "min": 0.1, "max": 1000.0, "label": "Radius"},
                "clip_to_shape": {"type": "bool", "default": False, "label": "Clip to Shape"}
            },
            "torus": {
                "name": {"type": "text", "default": "Torus Field", "label": "Name"},
                "radius": {"type": "float", "default": 100.0, "min": 0.1, "max": 1000.0, "label": "Radius"},
                "clip_to_shape": {"type": "bool", "default": False, "label": "Clip to Shape"},
                "direction": {"type": "choice", "default": 2, "choices": {0: "X", 2: "Z"}, "label": "Direction"}
            },
            "cone": {
                "name": {"type": "text", "default": "Cone Field", "label": "Name"},
                "clip_to_shape": {"type": "bool", "default": False, "label": "Clip to Shape"},
                "direction": {"type": "choice", "default": 1, "choices": {0: "X", 1: "Y", 2: "Z"}, "label": "Direction"},
                "radius": {"type": "float", "default": 100.0, "min": 0.1, "max": 1000.0, "label": "Radius"},
                "height": {"type": "float", "default": 200.0, "min": 0.1, "max": 1000.0, "label": "Height"}
            },
            "random": {
                "name": {"type": "text", "default": "Random Field", "label": "Name"},
                "seed": {"type": "int", "default": 1234, "min": 0, "max": 999999, "label": "Seed"},
                "scale": {"type": "float", "default": 100.0, "min": 0.1, "max": 1000.0, "label": "Scale"},
                "viewplane_preview": {"type": "bool", "default": False, "label": "Viewplane Preview"},
                "viewplane_resolution": {"type": "int", "default": 100, "min": 10, "max": 500, "label": "Viewplane Resolution"},
                "relative_scale": {"type": "float", "default": 1.0, "min": 0.1, "max": 10.0, "label": "Relative Scale"},
                "noise_type": {"type": "choice", "default": 1, "choices": {1: "Perlin", 2: "Ridge", 3: "Turbulence", 4: "FBM"}, "label": "Noise Type"},
                "sample_position_seed": {"type": "int", "default": 0, "min": 0, "max": 999999, "label": "Sample Position Seed"}
            },
            "sound": {
                "name": {"type": "text", "default": "Sound Field", "label": "Name"},
                "sound": {"type": "text", "default": "", "label": "Sound File"}
            },
            "formula": {
                "name": {"type": "text", "default": "Formula Field", "label": "Name"},
                "formula": {"type": "text", "default": "sin(x)", "label": "Formula"},
                "variables": {"type": "text", "default": "", "label": "Variables"},
                "scale_xyz": {"type": "float", "default": 1.0, "min": 0.1, "max": 10.0, "label": "Scale XYZ"},
                "uvw": {"type": "float", "default": 1.0, "min": 0.1, "max": 10.0, "label": "UVW"},
                "component_count": {"type": "int", "default": 1, "min": 1, "max": 10, "label": "Component Count"},
                "falloff_weight": {"type": "float", "default": 1.0, "min": 0.0, "max": 1.0, "label": "Falloff Weight"},
                "frequency": {"type": "float", "default": 1.0, "min": 0.1, "max": 10.0, "label": "Frequency"}
            },
            "radial": {
                "name": {"type": "text", "default": "Radial Field", "label": "Name"},
                "start_angle": {"type": "float", "default": 0.0, "min": 0.0, "max": 360.0, "label": "Start Angle"},
                "end_angle": {"type": "float", "default": 360.0, "min": 0.0, "max": 360.0, "label": "End Angle"},
                "axis": {"type": "choice", "default": 1, "choices": {0: "X", 1: "Y", 2: "Z"}, "label": "Axis"},
                "offset": {"type": "float", "default": 0.0, "min": -1000.0, "max": 1000.0, "label": "Offset"},
                "clip_to_shape": {"type": "bool", "default": False, "label": "Clip to Shape"}
            },
            "python": {
                "name": {"type": "text", "default": "Python Field", "label": "Name"},
                "code": {"type": "text", "default": "# Python field code", "label": "Code"}
            }
        }
        
        return fields_params.get(cmd_id, {})
    
    def _get_tags_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for tags"""
        
        tags_params = {
            "phong": {
                "name": {"type": "text", "default": "Phong Tag", "label": "Name"},
                "angle": {"type": "float", "default": 80.0, "min": 0.0, "max": 180.0, "label": "Phong Angle"}
            },
            "material": {
                "name": {"type": "text", "default": "Material Tag", "label": "Name"}
            },
            "texture": {
                "name": {"type": "text", "default": "Texture Tag", "label": "Name"},
                "projection": {"type": "choice", "default": "UVW Mapping", "choices": ["UVW Mapping", "Planar", "Cylindrical", "Spherical", "Cubic"], "label": "Projection"}
            },
            "uvw": {
                "name": {"type": "text", "default": "UVW Tag", "label": "Name"}
            },
            "selection": {
                "name": {"type": "text", "default": "Selection Tag", "label": "Name"}
            },
            "python": {
                "name": {"type": "text", "default": "Python Tag", "label": "Name"}
            },
            "expression": {
                "name": {"type": "text", "default": "Expression Tag", "label": "Name"}
            },
            "protection": {
                "name": {"type": "text", "default": "Protection Tag", "label": "Name"}
            },
            "display": {
                "name": {"type": "text", "default": "Display Tag", "label": "Name"}
            },
            "compositing": {
                "name": {"type": "text", "default": "Compositing Tag", "label": "Name"}
            }
        }
        
        return tags_params.get(cmd_id, {})
    
    def _get_models_parameters(self, cmd_id: str) -> Dict[str, Any]:
        """Get parameter definitions for 3D Models import commands"""
        
        models_params = {
            # Import Commands for Selected 3D Models from Tab 2
            "import_selected": {
                "scale": {"label": "Scale", "type": "float", "min": 0.01, "max": 100.0, "default": 1.0},
                "rotation_x": {"label": "Rotation X", "type": "float", "min": -360.0, "max": 360.0, "default": 0.0},
                "rotation_y": {"label": "Rotation Y", "type": "float", "min": -360.0, "max": 360.0, "default": 0.0},
                "rotation_z": {"label": "Rotation Z", "type": "float", "min": -360.0, "max": 360.0, "default": 0.0}
            },
            "import_single": {
                "model_index": {"label": "Model Index", "type": "int", "min": 0, "max": 50, "default": 0},
                "scale": {"label": "Scale", "type": "float", "min": 0.01, "max": 100.0, "default": 1.0}
            },
            "import_to_cloner": {
                "cloner_mode": {
                    "label": "Cloner Mode",
                    "type": "choice",
                    "choices": {"linear": "Linear", "radial": "Radial", "grid": "Grid", "honeycomb": "Honeycomb"},
                    "default": "grid"
                },
                "count": {"label": "Clone Count", "type": "int", "min": 1, "max": 1000, "default": 10},
                "spacing": {"label": "Spacing", "type": "float", "min": 1.0, "max": 1000.0, "default": 100.0}
            },
            "import_with_softbody": {
                "scale": {"label": "Scale", "type": "float", "min": 0.01, "max": 100.0, "default": 1.0},
                "pos_y": {"label": "Start Height", "type": "float", "min": -10000.0, "max": 10000.0, "default": 500.0},
                "mass": {"label": "Mass", "type": "float", "min": 0.1, "max": 100.0, "default": 1.0},
                "bounce": {"label": "Bounce", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3}
            },
            "import_with_rigidbody": {
                "pos_x": {"label": "Position X", "type": "int", "min": -10000, "max": 10000, "default": 0},
                "pos_y": {"label": "Position Y", "type": "int", "min": -10000, "max": 10000, "default": 500},
                "pos_z": {"label": "Position Z", "type": "int", "min": -10000, "max": 10000, "default": 0},
                "scale": {"label": "Scale", "type": "float", "min": 0.01, "max": 100.0, "default": 1.0},
                "mass": {"label": "Mass", "type": "float", "min": 0.1, "max": 100.0, "default": 1.0},
                "friction": {"label": "Friction", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3}
            },
            "import_with_cloth": {
                "pos_x": {"label": "Position X", "type": "int", "min": -10000, "max": 10000, "default": 0},
                "pos_y": {"label": "Position Y", "type": "int", "min": -10000, "max": 10000, "default": 500},
                "pos_z": {"label": "Position Z", "type": "int", "min": -10000, "max": 10000, "default": 0},
                "scale": {"label": "Scale", "type": "float", "min": 0.01, "max": 100.0, "default": 1.0},
                "cloth_type": {
                    "label": "Cloth Type",
                    "type": "choice",
                    "choices": {"cloth": "Standard Cloth", "cloth_belt": "Cloth Belt"},
                    "default": "cloth"
                },
                "mass": {"label": "Mass", "type": "float", "min": 0.1, "max": 100.0, "default": 1.0}
            },
            "quick_import": {
                "spacing_x": {"label": "X Spacing", "type": "float", "min": 0.0, "max": 1000.0, "default": 200.0},
                "spacing_y": {"label": "Y Spacing", "type": "float", "min": 0.0, "max": 1000.0, "default": 0.0},
                "spacing_z": {"label": "Z Spacing", "type": "float", "min": 0.0, "max": 1000.0, "default": 200.0}
            }
        }
        
        return models_params.get(cmd_id, {})
    
    def _filter_commands(self, category: str, text: str):
        """Filter commands based on search text"""
        list_widget = self.list_widgets.get(category)
        if not list_widget:
            return
            
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def _add_new_command(self, category: str):
        """Add a new command to the category"""
        # TODO: Implement add new command dialog
        logger.info(f"Add new command to {category}")
        
    def _create_command(self, category: str):
        """Create the selected command in Cinema4D"""
        logger.info(f"[NLP] _create_command called for category: {category}")
        
        list_widget = self.list_widgets.get(category)
        if not list_widget:
            logger.warning(f"[NLP] No list widget for category: {category}")
            return
            
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a command to create.")
            return
            
        cmd_id = current_item.data(Qt.UserRole)
        cmd_data = self.dictionary_data.get(category, {}).get(cmd_id, {}).copy()
        
        logger.info(f"[NLP] Creating command: {cmd_id} - {cmd_data.get('name', 'Unknown')}")
        
        # Collect current parameter values from UI
        container = self.param_containers.get(category)
        logger.info(f"[PARAM DEBUG] Container found: {container is not None}")
        if container:
            params = {}
            layout = container.layout()
            logger.info(f"[PARAM DEBUG] Layout widget count: {layout.count()}")
            
            # Iterate through all widgets in the parameter container
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    obj_name = widget.objectName()
                    logger.info(f"[PARAM DEBUG] Widget {i}: {type(widget).__name__}, objectName: '{obj_name}'")
                    
                    # Extract parameter name from object name (format: category_cmdid_paramname)
                    if obj_name and '_' in obj_name:
                        # Expected format: fields_box_field_size → category=fields, cmd_id=box_field, param=size
                        expected_prefix = f"{category}_{cmd_id}_"
                        logger.info(f"[PARAM DEBUG] Object name: '{obj_name}', expected prefix: '{expected_prefix}'")
                        if obj_name.startswith(expected_prefix):
                            param_name = obj_name[len(expected_prefix):]  # Extract everything after the prefix
                            logger.info(f"[PARAM DEBUG] Matched parameter: {param_name}")
                            
                            # Get value based on widget type
                            if isinstance(widget, QSpinBox):
                                value = widget.value()
                                params[param_name] = value
                                logger.info(f"[PARAM DEBUG] QSpinBox {param_name}: {value}")
                            elif isinstance(widget, QCheckBox):
                                value = widget.isChecked()
                                params[param_name] = value
                                logger.info(f"[PARAM DEBUG] QCheckBox {param_name}: {value}")
                            elif isinstance(widget, QComboBox):
                                value = widget.currentData()
                                params[param_name] = value
                                logger.info(f"[PARAM DEBUG] QComboBox {param_name}: {value}")
                            elif hasattr(widget, 'value'):  # Handles QDoubleSpinBox and other value-based widgets
                                value = widget.value()
                                params[param_name] = value
                                logger.info(f"[PARAM DEBUG] {type(widget).__name__} {param_name}: {value}")
                        else:
                            logger.info(f"[PARAM DEBUG] No match: parts length {len(parts)}, parts[1]='{parts[1] if len(parts) > 1 else 'N/A'}'")
                    else:
                        logger.info(f"[PARAM DEBUG] Invalid object name: '{obj_name}'")
            
            logger.info(f"[PARAM DEBUG] Collected params: {params}")
            
            # Update command data with current UI values
            if params:
                cmd_data['parameters'] = params
            else:
                logger.warning(f"[PARAM DEBUG] No parameters collected - using defaults")
        
        # Log final command data
        logger.info(f"[NLP] Final command data: {cmd_data}")
        
        # Emit signal for parent to handle creation
        logger.info(f"[NLP] Emitting command_created signal")
        self.command_created.emit(category, cmd_data)
        logger.info(f"[NLP] Signal emitted")
        
    def _show_settings(self, category: str):
        """Show settings for the selected command"""
        list_widget = self.list_widgets.get(category)
        if not list_widget:
            return
            
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a command to configure.")
            return
            
        # TODO: Show settings dialog similar to primitive settings
        logger.info(f"Show settings for {current_item.text()}")
        
    def _remove_command(self, category: str):
        """Remove the selected command"""
        list_widget = self.list_widgets.get(category)
        if not list_widget:
            return
            
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a command to remove.")
            return
            
        cmd_id = current_item.data(Qt.UserRole)
        cmd_name = current_item.text()
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Removal",
            f"Are you sure you want to remove '{cmd_name}'?\n\n"
            "This action is permanent and can only be undone by manually editing the settings file.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from dictionary
            if cmd_id in self.dictionary_data.get(category, {}):
                del self.dictionary_data[category][cmd_id]
                self.save_dictionary()
                self.load_category_data()
                QMessageBox.information(self, "Removed", f"'{cmd_name}' has been removed.")
                
    def _test_command(self, category: str):
        """Test the selected command"""
        list_widget = self.list_widgets.get(category)
        if not list_widget:
            return
            
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a command to test.")
            return
            
        # TODO: Implement command testing
        logger.info(f"Test command {current_item.text()}")
        
    def save_dictionary(self):
        """Save dictionary data to file"""
        try:
            # Ensure directory exists
            self.dictionary_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self.dictionary_file, 'w') as f:
                json.dump(self.dictionary_data, f, indent=2)
                
            logger.info(f"Dictionary saved to {self.dictionary_file}")
            
        except Exception as e:
            logger.error(f"Error saving dictionary: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save dictionary: {str(e)}")
            
    def apply_styles(self):
        """Apply terminal theme styles"""
        self.setStyleSheet(get_complete_terminal_theme() + """
            QDialog {
                background-color: #000000;
                color: #fafafa;
                font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
            }
            
            #dialog_header {
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
            
            #nlp_tabs {
                background-color: #000000;
                border: 1px solid #3a3a3a;
            }
            
            #nlp_tabs::pane {
                background-color: #000000;
                border: 1px solid #3a3a3a;
            }
            
            #nlp_tabs::tab-bar {
                alignment: left;
            }
            
            #nlp_tabs QTabBar::tab {
                background-color: #171717;
                color: #fafafa;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                border: 1px solid #3a3a3a;
            }
            
            #nlp_tabs QTabBar::tab:hover {
                background-color: #2a2a2a;
            }
            
            #command_list {
                background-color: #171717;
                border: 1px solid #3a3a3a;
                padding: 5px;
                color: #fafafa;
            }
            
            #command_list::item {
                padding: 5px;
                border-bottom: 1px solid #333;
            }
            
            #command_list::item:selected {
                background-color: #0d7377;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #333;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            #create_button {
                background-color: #0d7377;
                font-weight: bold;
                padding: 8px 16px;
            }
            
            #create_button:hover {
                background-color: #14ffec;
                color: #1a1a1a;
            }
            
            #remove_button {
                background-color: #d32f2f;
            }
            
            #remove_button:hover {
                background-color: #f44336;
            }
        """)
    
    def _apply_accent_colors(self):
        """Apply accent colors to override hardcoded green colors"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            accent_color = settings.value("interface/accent_color", "#4CAF50")
            
            accent_css = f"""
            #dialog_header {{
                color: {accent_color} !important;
            }}
            
            #nlp_tabs QTabBar::tab:selected {{
                background-color: {accent_color} !important;
                color: #000000 !important;
                font-weight: bold;
            }}
            
            #nlp_tabs QTabBar::tab:hover {{
                border-color: {accent_color} !important;
            }}
            """
            
            # Apply the accent color CSS
            current_style = self.styleSheet()
            self.setStyleSheet(current_style + accent_css)
            
        except Exception as e:
            logger.error(f"Failed to apply accent colors to NLP dictionary: {e}")