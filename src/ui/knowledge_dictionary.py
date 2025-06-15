"""
Knowledge Dictionary for Cinema4D Intelligence
Interactive command reference and examples
"""

from typing import Dict, List, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QFrame, QToolButton
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from utils.logger import LoggerMixin


class CollapsibleSection(QWidget):
    """Expandable section for command categories"""
    
    example_clicked = Signal(str)  # Emit example text when clicked
    
    def __init__(self, title: str, info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.title = title
        self.info = info
        self.expanded = False
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header button
        self.header_btn = QPushButton(f"{'▼' if self.expanded else '▶'} {self.title}")
        self.header_btn.setObjectName("section_header")
        self.header_btn.clicked.connect(self.toggle_expand)
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.header_btn)
        
        # Content area
        self.content_widget = QWidget()
        self.content_widget.setObjectName("section_content")
        self.content_widget.setVisible(self.expanded)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 10, 10)
        
        # Add examples
        if "examples" in self.info:
            examples_label = QLabel("Examples:")
            examples_label.setObjectName("examples_label")
            content_layout.addWidget(examples_label)
            
            for example in self.info["examples"]:
                example_btn = QPushButton(f"  • {example}")
                example_btn.setObjectName("example_item")
                example_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                example_btn.clicked.connect(lambda checked, ex=example: self.example_clicked.emit(ex))
                content_layout.addWidget(example_btn)
        
        # Add keywords if available
        if "keywords" in self.info:
            keywords_label = QLabel(f"Keywords: {', '.join(self.info['keywords'])}")
            keywords_label.setObjectName("keywords_label")
            keywords_label.setWordWrap(True)
            content_layout.addWidget(keywords_label)
        
        # Add capabilities if available
        if "capabilities" in self.info:
            cap_label = QLabel("Capabilities:")
            cap_label.setObjectName("capabilities_label")
            content_layout.addWidget(cap_label)
            
            caps_text = QLabel("\n".join(f"  • {cap}" for cap in self.info["capabilities"]))
            caps_text.setObjectName("capabilities_text")
            caps_text.setWordWrap(True)
            content_layout.addWidget(caps_text)
        
        self.content_widget.setLayout(content_layout)
        layout.addWidget(self.content_widget)
        
        self.setLayout(layout)
        
    def toggle_expand(self):
        """Toggle section expansion"""
        self.expanded = not self.expanded
        self.header_btn.setText(f"{'▼' if self.expanded else '▶'} {self.title}")
        self.content_widget.setVisible(self.expanded)


class KnowledgeDictionary(QWidget, LoggerMixin):
    """Interactive command dictionary for Cinema4D operations"""
    
    # Command dictionary structure
    COMMAND_DICTIONARY = {
        "🎯 Object Creation": {
            "keywords": ["create", "make", "generate", "build", "add"],
            "examples": [
                "create a sphere",
                "create a large cylinder",
                "make a tiny cube",
                "add a torus at the top",
                "create five pyramids",
                "make a giant cone",
                "add a plane",
                "create a disc",
                "make a tube",
                "add a landscape",
                "create text saying Hello",
                "make 10 cubes in a grid",
                "create three red spheres",
                "add a metallic cube"
            ],
            "capabilities": ["All primitives (cube, sphere, cylinder, cone, torus, plane, pyramid, disc, tube, platonic)", "Size modifiers (tiny, small, large, huge)", "Position modifiers (top, bottom, left, right, center)", "Multiple objects with counts", "Color assignment"]
        },
        
        "🎨 Scattering & Distribution": {
            "keywords": ["scatter", "distribute", "spread", "populate", "fill", "place"],
            "examples": [
                "scatter objects on the mountain peaks",
                "distribute randomly across surface",
                "populate the terrain with trees",
                "fill the volume with particles",
                "place objects along a spline"
            ],
            "capabilities": ["Surface scatter", "Volume fill", "Spline distribution", "Random placement", "Grid arrays"]
        },
        
        "🌿 Organic Effects": {
            "keywords": ["organic", "natural", "irregular", "flowing", "random", "noise"],
            "examples": [
                "make it look organic",
                "add natural variation",
                "create irregular placement",
                "flowing movement",
                "random size variations"
            ],
            "capabilities": ["Noise fields", "Random effectors", "Organic deformers", "Natural distributions"]
        },
        
        "🔗 Connections": {
            "keywords": ["connect", "link", "bridge", "spline", "wire", "bind"],
            "examples": [
                "connect these with splines",
                "link objects with cables",
                "bridge the gap between objects",
                "create wires between points",
                "bind objects together"
            ],
            "capabilities": ["Dynamic splines", "Constraints", "Smart connections", "Cable simulation"]
        },
        
        "🦱 Hair & Fibers": {
            "keywords": ["hair", "fur", "grass", "fibers", "bristles", "strands"],
            "examples": [
                "add fur to the surface",
                "create grass on terrain",
                "make it hairy",
                "add fiber details",
                "generate bristles"
            ],
            "capabilities": ["Hair objects", "Grass generation", "Fiber simulation", "Fur effects"]
        },
        
        "💥 Dynamics & Physics": {
            "keywords": ["physics", "fall", "collide", "bounce", "simulate", "gravity"],
            "examples": [
                "make them fall naturally",
                "add collision dynamics",
                "simulate physics",
                "objects bounce off each other",
                "apply gravity"
            ],
            "capabilities": ["Rigid body", "Soft body", "Collision detection", "Physics simulation"]
        },
        
        "🎭 Animation": {
            "keywords": ["animate", "move", "rotate", "scale", "transform", "sequence"],
            "examples": [
                "animate in sequence",
                "rotate randomly over time",
                "scale up gradually",
                "move along path",
                "create looping animation"
            ],
            "capabilities": ["Keyframe animation", "Procedural motion", "Effector animation", "Path animation"]
        },
        
        "🏗️ Deformers & Modifiers": {
            "keywords": ["bend", "twist", "deform", "taper", "bulge", "squash", "modify"],
            "examples": [
                "bend the cube slightly",
                "twist it strongly",
                "add gentle taper",
                "bulge in the middle",
                "squash and stretch",
                "deform the sphere subtly",
                "apply extreme bend"
            ],
            "capabilities": ["Bend deformer", "Twist", "Taper", "Bulge", "Squash", "Strength modifiers (slightly, gently, strongly, extremely)"]
        },
        
        "🎨 Materials & Shading": {
            "keywords": ["material", "texture", "color", "shader", "surface", "metallic"],
            "examples": [
                "apply metallic material",
                "add random colors",
                "create glass shader",
                "texture with noise",
                "make it reflective"
            ],
            "capabilities": ["Standard materials", "Procedural shaders", "Random colors", "Texture mapping"]
        },
        
        "📐 Cloning & Arrays": {
            "keywords": ["clone", "array", "grid", "radial", "duplicate", "repeat"],
            "examples": [
                "clone the cube in a grid",
                "create radial array",
                "duplicate 20 times",
                "make honeycomb pattern",
                "linear array with offset",
                "clone and randomize position",
                "array with random rotation"
            ],
            "capabilities": ["Grid cloner", "Radial patterns", "Linear arrays", "Honeycomb", "Random effector integration", "Count specification"]
        }
    }
    
    example_selected = Signal(str)  # Signal when example is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.sections = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the knowledge dictionary UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with search
        header_layout = QVBoxLayout()
        
        title = QLabel("🧠 Command Reference")
        title.setObjectName("dict_header")
        header_layout.addWidget(title)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search commands...")
        self.search_input.setObjectName("search_input")
        self.search_input.textChanged.connect(self.filter_commands)
        header_layout.addWidget(self.search_input)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)
        
        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("dict_scroll")
        
        # Content widget
        self.content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Create sections for each category
        for category, info in self.COMMAND_DICTIONARY.items():
            section = CollapsibleSection(category, info)
            section.example_clicked.connect(self.on_example_clicked)
            self.sections.append(section)
            content_layout.addWidget(section)
        
        # Add stretch at bottom
        content_layout.addStretch()
        
        self.content_widget.setLayout(content_layout)
        scroll.setWidget(self.content_widget)
        
        layout.addWidget(scroll)
        
        # Tips section at bottom
        tips_label = QLabel("💡 Tip: Click any example to use it in chat")
        tips_label.setObjectName("tips_label")
        tips_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tips_label)
        
        self.setLayout(layout)
        
    def filter_commands(self, search_text: str):
        """Filter visible sections based on search"""
        search_lower = search_text.lower()
        
        for section in self.sections:
            # Check if search matches title, keywords, or examples
            visible = False
            
            if search_lower in section.title.lower():
                visible = True
            elif "keywords" in section.info:
                if any(search_lower in kw.lower() for kw in section.info["keywords"]):
                    visible = True
            elif "examples" in section.info:
                if any(search_lower in ex.lower() for ex in section.info["examples"]):
                    visible = True
            
            section.setVisible(visible)
            
            # Auto-expand matching sections
            if visible and search_text:
                section.expanded = True
                section.toggle_expand()
    
    def on_example_clicked(self, example_text: str):
        """Handle example click"""
        self.logger.info(f"Example clicked: {example_text}")
        self.example_selected.emit(example_text)
        
        # If parent app has chat widget, insert the example
        if self.parent_app and hasattr(self.parent_app, 'chat_widget'):
            self.parent_app.chat_widget.input_area.text_input.setText(example_text)
            self.parent_app.chat_widget.input_area.text_input.setFocus()
    
    def expand_all(self):
        """Expand all sections"""
        for section in self.sections:
            if not section.expanded:
                section.toggle_expand()
    
    def collapse_all(self):
        """Collapse all sections"""
        for section in self.sections:
            if section.expanded:
                section.toggle_expand()