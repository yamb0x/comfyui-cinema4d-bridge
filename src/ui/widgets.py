"""
Custom UI widgets for the application
"""

import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QPushButton, QTextEdit, QCheckBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QFont, QImage

from PIL import Image
from loguru import logger


class ImageThumbnail(QFrame):
    """Thumbnail widget for images"""
    
    clicked = Signal(Path)
    selected = Signal(Path, bool)
    
    def __init__(self, image_path: Path, size: int = 256):
        super().__init__()
        self.image_path = image_path
        self.size = size
        self._selected = False
        
        self.setFixedSize(size + 20, size + 40)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setFixedSize(size, size)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2a2a2a;")
        layout.addWidget(self.image_label)
        
        # Filename label
        self.name_label = QLabel(image_path.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setMaximumWidth(size)
        self.name_label.setWordWrap(True)
        font = self.name_label.font()
        font.setPointSize(9)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        
        # Selection checkbox
        self.select_check = QCheckBox()
        self.select_check.stateChanged.connect(self._on_selection_changed)
        layout.addWidget(self.select_check, alignment=Qt.AlignCenter)
        
        # Load thumbnail
        self._load_thumbnail()
        
    def _load_thumbnail(self):
        """Load and display thumbnail"""
        try:
            # Load with PIL for better format support
            img = Image.open(self.image_path)
            img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            if img.mode == "RGBA":
                # Handle transparency
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            else:
                # Convert to RGB
                img = img.convert("RGB")
                data = img.tobytes("raw", "RGB")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale to fit
            scaled_pixmap = pixmap.scaled(
                self.size, self.size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            logger.error(f"Failed to load thumbnail for {self.image_path}: {e}")
            self.image_label.setText("Failed to\nload image")
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)
    
    def _on_selection_changed(self, state):
        """Handle selection change"""
        self._selected = state == Qt.Checked
        self.selected.emit(self.image_path, self._selected)
        self._update_style()
    
    def _update_style(self):
        """Update visual style based on selection"""
        if self._selected:
            self.setStyleSheet("QFrame { border: 3px solid #4CAF50; }")
        else:
            self.setStyleSheet("")
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.select_check.setChecked(selected)


class ImageGridWidget(QScrollArea):
    """Grid widget for displaying images"""
    
    image_selected = Signal(Path, bool)
    image_clicked = Signal(Path)
    
    def __init__(self, columns: int = 4, thumbnail_size: int = 256):
        super().__init__()
        self.columns = columns
        self.thumbnail_size = thumbnail_size
        self.thumbnails: List[ImageThumbnail] = []
        
        # Setup scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        self.content = QWidget()
        self.setWidget(self.content)
        
        # Grid layout
        self.grid_layout = QGridLayout(self.content)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
    
    def add_image(self, image_path: Path):
        """Add image to grid"""
        # Create thumbnail
        thumbnail = ImageThumbnail(image_path, self.thumbnail_size)
        thumbnail.clicked.connect(self.image_clicked.emit)
        thumbnail.selected.connect(self.image_selected.emit)
        
        # Add to grid
        row = len(self.thumbnails) // self.columns
        col = len(self.thumbnails) % self.columns
        
        self.grid_layout.addWidget(thumbnail, row, col)
        self.thumbnails.append(thumbnail)
    
    def clear(self):
        """Clear all images"""
        for thumbnail in self.thumbnails:
            self.grid_layout.removeWidget(thumbnail)
            thumbnail.deleteLater()
        self.thumbnails.clear()
    
    def get_selected_images(self) -> List[Path]:
        """Get list of selected images"""
        selected = []
        for thumbnail in self.thumbnails:
            if thumbnail._selected:
                selected.append(thumbnail.image_path)
        return selected
    
    def set_columns(self, columns: int):
        """Set number of columns"""
        self.columns = columns
        self._reorganize_grid()
    
    def _reorganize_grid(self):
        """Reorganize grid layout"""
        # Remove all widgets
        for thumbnail in self.thumbnails:
            self.grid_layout.removeWidget(thumbnail)
        
        # Re-add in new configuration
        for i, thumbnail in enumerate(self.thumbnails):
            row = i // self.columns
            col = i % self.columns
            self.grid_layout.addWidget(thumbnail, row, col)


class Model3DPreviewWidget(QWidget):
    """Widget for previewing 3D models"""
    
    model_selected = Signal(Path, bool)
    model_clicked = Signal(Path)
    
    def __init__(self):
        super().__init__()
        self.models: List[Path] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Info label
        self.info_label = QLabel("3D model preview will be displayed here")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.info_label)
        
        # Placeholder for 3D viewer
        self.viewer_frame = QFrame()
        self.viewer_frame.setFrameStyle(QFrame.Box)
        self.viewer_frame.setMinimumHeight(300)
        layout.addWidget(self.viewer_frame)
        
        # Model list
        self.model_list = QWidget()
        self.model_layout = QHBoxLayout(self.model_list)
        self.model_layout.setSpacing(10)
        
        scroll = QScrollArea()
        scroll.setWidget(self.model_list)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(150)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        layout.addWidget(scroll)
    
    def add_model(self, model_path: Path):
        """Add 3D model"""
        self.models.append(model_path)
        
        # Create preview card
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setFixedSize(120, 120)
        card_layout = QVBoxLayout(card)
        
        # Model icon
        icon_label = QLabel("🎲")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        card_layout.addWidget(icon_label)
        
        # Model name
        name_label = QLabel(model_path.stem)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        font = name_label.font()
        font.setPointSize(9)
        name_label.setFont(font)
        card_layout.addWidget(name_label)
        
        self.model_layout.addWidget(card)
        
        # Update info
        self.info_label.setText(f"{len(self.models)} 3D models loaded")


class ConsoleWidget(QTextEdit):
    """Console output widget with logging integration"""
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #333;
            }
        """)
        
        self.max_lines = 1000
        self._auto_scroll = True
        
    def setup_logging(self):
        """Setup logging handler to capture logs"""
        from loguru import logger
        
        # Add custom sink
        logger.add(
            self._log_to_console,
            format="{time:HH:mm:ss} | <level>{level: <8}</level> | {message}",
            level="DEBUG",
            colorize=False
        )
    
    def _log_to_console(self, message):
        """Log message to console"""
        # Parse level from message
        if "| ERROR" in message:
            color = "#FF5252"
        elif "| WARNING" in message:
            color = "#FFC107"
        elif "| INFO" in message:
            color = "#4CAF50"
        elif "| DEBUG" in message:
            color = "#9E9E9E"
        else:
            color = "#e0e0e0"
        
        # Format and append
        html = f'<span style="color: {color};">{message.strip()}</span>'
        self.append(html)
        
        # Limit lines
        if self.document().blockCount() > self.max_lines:
            cursor = self.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 
                              self.document().blockCount() - self.max_lines)
            cursor.removeSelectedText()
        
        # Auto scroll
        if self._auto_scroll:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def set_auto_scroll(self, enabled: bool):
        """Enable/disable auto scroll"""
        self._auto_scroll = enabled