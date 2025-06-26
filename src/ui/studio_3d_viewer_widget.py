"""
Studio 3D Viewer Widget - Clean minimal implementation with 3D display
"""

import sys
import os
import threading
from pathlib import Path
from typing import List, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from loguru import logger

# Import ThreeJS3DViewer for embedding in preview cards
from src.ui.viewers.threejs_3d_viewer import ThreeJS3DViewer


class LocalFileServer(SimpleHTTPRequestHandler):
    """Simple HTTP server to serve local 3D model files"""
    
    def __init__(self, *args, model_path=None, **kwargs):
        self.model_path = model_path
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        if self.path == '/model.glb' and self.model_path and Path(self.model_path).exists():
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
        pass  # Silent server


class Studio3DPreviewCard(QFrame):
    """3D model preview card with embedded ThreeJS viewer"""
    
    clicked = Signal(Path)
    selected = Signal(Path, bool)
    
    def __init__(self, model_path: Path, width: int = 512, height: int = 512, accent_color: str = "#4CAF50"):
        super().__init__()
        self.model_path = model_path
        self.is_selected = False
        self.accent_color = accent_color
        
        
        # Set minimum size but allow expansion to fill width
        self.setMinimumSize(width, height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Basic styling
        self.setFrameStyle(QFrame.Box)
        self._update_styles()
        
        # Simple layout with model name
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Removed preset sphere - no longer needed
        
        # Model info
        self.title_label = QLabel(self.model_path.stem)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setMaximumHeight(30)
        layout.addWidget(self.title_label)
        
        # Embed ThreeJS3DViewer instead of placeholder
        # Use dynamic sizing - viewer will expand to fill available space
        # Set minimum height but allow width to expand
        min_viewer_height = height - 60  # 10px top/bottom margins + 30px title + 10px spacing
        
        self.viewer = ThreeJS3DViewer(self, width=None, height=min_viewer_height, responsive=True)
        layout.addWidget(self.viewer)
        
        # Load the model if it exists
        if self.model_path.exists():
            self.viewer.load_model(str(self.model_path))
        else:
            logger.warning(f"Model file not found: {self.model_path}")
    
    def mousePressEvent(self, event):
        """Handle click for selection"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.model_path)
            # Toggle selection
            self.is_selected = not self.is_selected
            self.setProperty("selected", self.is_selected)
            self.style().unpolish(self)
            self.style().polish(self)
            self.selected.emit(self.model_path, self.is_selected)
        super().mousePressEvent(event)
    
    def _update_styles(self):
        """Update styles with current accent color"""
        self.setStyleSheet(f"""
            Studio3DPreviewCard {{
                background-color: #2a2a2a;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
            }}
            Studio3DPreviewCard:hover {{
                border-color: #4a4a4a;
            }}
            Studio3DPreviewCard[selected="true"] {{
                border-color: {self.accent_color};
                background-color: #2e2e2e;
            }}
        """)
    
    
    def update_accent_color(self, color: str):
        """Update the selection border color based on settings"""
        self.accent_color = color
        self._update_styles()
        # Force style refresh if selected
        if self.is_selected:
            self.style().unpolish(self)
            self.style().polish(self)
    


class ResponsiveStudio3DGrid(QScrollArea):
    """Simple responsive grid for 3D model cards"""
    
    model_selected = Signal(Path, bool)
    model_clicked = Signal(Path)
    models_changed = Signal(int)
    
    def __init__(self, columns: int = 1, card_size: int = 512, accent_color: str = "#4CAF50"):
        super().__init__()
        self.columns = columns
        self.card_size = card_size
        self.accent_color = accent_color
        self.models: List[Path] = []
        self.cards: List[Studio3DPreviewCard] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the grid UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Remove the fixed maximum height to allow proper sizing
        # The parent container should control the height
        
        # Set transparent background to prevent black overlay
        self.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Content widget
        self.content = QWidget()
        self.content.setStyleSheet("background-color: transparent;")
        self.setWidget(self.content)
        
        # Main layout
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Grid layout
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.grid_layout)
        
        # Add stretch to push content to top
        layout.addStretch()
    
    def add_model(self, model_path: Path):
        """Add a 3D model to the grid"""
        if model_path in self.models:
            logger.debug(f"Model {model_path.name} already in grid")
            return
        
        self.models.append(model_path)
        
        # Create preview card with accent color (full width)
        card = Studio3DPreviewCard(model_path, self.card_size, self.card_size, self.accent_color)
        card.clicked.connect(self.model_clicked.emit)
        card.selected.connect(self.model_selected.emit)
        
        # Add to grid - use full width by spanning all columns
        row = len(self.cards)
        self.grid_layout.addWidget(card, row, 0, 1, self.columns)  # Span all columns for full width
        self.cards.append(card)
        
        self.models_changed.emit(len(self.models))
        
        logger.debug(f"Added 3D model to grid: {model_path.name}")
    
    def remove_model(self, model_path: Path):
        """Remove a model from the grid"""
        if model_path not in self.models:
            return
        
        # Find and remove the card
        for i, card in enumerate(self.cards):
            if card.model_path == model_path:
                self.grid_layout.removeWidget(card)
                card.deleteLater()
                self.cards.pop(i)
                break
        
        self.models.remove(model_path)
        self._refresh_grid_layout()
        self.models_changed.emit(len(self.models))
    
    def clear_models(self):
        """Clear all models from the grid"""
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        
        self.cards.clear()
        self.models.clear()
        self.models_changed.emit(0)
    
    def get_selected_models(self) -> List[Path]:
        """Get list of selected model paths"""
        return [card.model_path for card in self.cards if card.is_selected]
    
    def _refresh_grid_layout(self):
        """Refresh the grid layout after model removal"""
        for i, card in enumerate(self.cards):
            row = i
            self.grid_layout.addWidget(card, row, 0, 1, self.columns)  # Span all columns for full width
    
    
    def set_accent_color(self, color: str):
        """Set the accent color for all cards"""
        self.accent_color = color
        for card in self.cards:
            card.update_accent_color(color)
    
    def update_accent_color(self, color: str):
        """Update the accent color for all cards (alias for set_accent_color)"""
        self.set_accent_color(color)
    
    def apply_viewer_settings(self, settings):
        """Apply new viewer settings to all 3D preview cards"""
        try:
            logger.debug(f"ResponsiveStudio3DGrid: Applying viewer settings to {len(self.cards)} cards")
            
            # Apply settings to each preview card's embedded viewer
            for card in self.cards:
                if hasattr(card, 'viewer') and card.viewer:
                    card.viewer.apply_settings(settings, save_to_file=False)
                    logger.debug(f"Applied settings to card viewer for {card.model_path.name}")
            
            logger.info(f"Successfully applied viewer settings to {len(self.cards)} 3D preview cards")
            
        except Exception as e:
            logger.error(f"Failed to apply viewer settings to grid: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")