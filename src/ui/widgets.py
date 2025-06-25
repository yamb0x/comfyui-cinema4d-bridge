"""
Custom UI widgets for the application
"""

import sys
from pathlib import Path
from typing import List, Optional
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QPushButton, QTextEdit, QCheckBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QFont, QImage

from PIL import Image
from loguru import logger

# Import async image loading
from src.ui.async_image_loader import get_async_image_manager

# 3D visualization imports
try:
    import trimesh
except ImportError as e:
    logger.warning(f"3D mesh processing not available: {e}")

# Import ThreeJS viewer for all 3D visualization
from ui.viewers.threejs_3d_viewer import ThreeJS3DViewer


class Simple3DViewer(QWidget):
    """Simple 3D model viewer using ThreeJS - wrapper for compatibility"""
    
    # Track active viewers for resource management
    _active_viewers = []
    _viewer_pool = []  # Pool of reusable viewers
    MAX_ACTIVE_VIEWERS = 15  # Limit active 3D viewers
    
    def __init__(self, width=496, height=496, is_session_viewer=False):
        super().__init__()
        self.setFixedSize(width, height)
        self._model_path = None
        self._is_session_viewer = is_session_viewer
        self._is_active = False
        self._threejs_viewer = None
        self._thumbnail_label = None
        self._is_lazy_loaded = False
        
        # Setup UI
        self._setup_ui()
        
        # For "View All" tab, start with thumbnail mode
        if not is_session_viewer:
            self._setup_thumbnail_mode()
        else:
            # For Scene Objects, load 3D viewer immediately
            self._setup_3d_viewer()
    
    def _setup_ui(self):
        """Setup basic UI layout"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
    
    def _setup_thumbnail_mode(self):
        """Setup thumbnail placeholder for lazy loading"""
        self._thumbnail_label = QLabel("🎯 Click to load 3D view")
        self._thumbnail_label.setAlignment(Qt.AlignCenter)
        self._thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #888;
                border: 1px solid #3a3a3a;
                font-size: 14px;
            }
        """)
        self._thumbnail_label.setFixedSize(self.width(), self.height())
        self.layout.addWidget(self._thumbnail_label)
    
    def _setup_3d_viewer(self):
        """Setup actual 3D viewer"""
        if self._threejs_viewer:
            return  # Already setup
            
        # Check if we can activate a new viewer
        if len(self._active_viewers) >= self.MAX_ACTIVE_VIEWERS:
            # Try to recycle an inactive viewer
            if not self._recycle_inactive_viewer():
                logger.warning(f"Max active viewers ({self.MAX_ACTIVE_VIEWERS}) reached")
                self._show_limit_message()
                return
        
        try:
            # Try to get a viewer from the pool
            if self._viewer_pool:
                self._threejs_viewer = self._viewer_pool.pop()
                logger.debug("Reusing viewer from pool")
            else:
                # Create new ThreeJS viewer
                self._threejs_viewer = ThreeJS3DViewer(self, self.width(), self.height())
                logger.debug("Created new ThreeJS viewer")
            
            # Remove thumbnail if exists
            if self._thumbnail_label:
                self._thumbnail_label.setParent(None)
                self._thumbnail_label.deleteLater()
                self._thumbnail_label = None
            
            # Add to layout
            self.layout.addWidget(self._threejs_viewer)
            
            # Track as active
            self._active_viewers.append(self)
            self._is_active = True
            
            # Load model if we have one
            if self._model_path:
                self._threejs_viewer.load_model(str(self._model_path))
                
        except Exception as e:
            logger.error(f"Failed to setup 3D viewer: {e}")
            self._setup_fallback()
    
    def _recycle_inactive_viewer(self):
        """Try to recycle an inactive viewer"""
        # Find viewers that are not visible or out of viewport
        for viewer in self._active_viewers[:]:
            if not viewer.isVisible():
                viewer._deactivate_viewer()
                return True
        return False
    
    def _deactivate_viewer(self):
        """Deactivate this viewer and return it to pool"""
        if self._threejs_viewer and self._is_active:
            # Remove from active list
            if self in self._active_viewers:
                self._active_viewers.remove(self)
            
            # Clear the viewer
            self._threejs_viewer.setParent(None)
            
            # Add to pool for reuse
            if len(self._viewer_pool) < 5:  # Keep small pool
                self._viewer_pool.append(self._threejs_viewer)
            else:
                self._threejs_viewer.deleteLater()
                
            self._threejs_viewer = None
            self._is_active = False
            
            # Show thumbnail again
            if not self._is_session_viewer:
                self._setup_thumbnail_mode()
    
    def _show_limit_message(self):
        """Show message when viewer limit reached"""
        if not self._thumbnail_label:
            self._thumbnail_label = QLabel("⚠️ Viewer limit reached\nClick to retry")
            self._thumbnail_label.setAlignment(Qt.AlignCenter)
            self._thumbnail_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #ff9800;
                    border: 1px solid #ff9800;
                    font-size: 12px;
                }
            """)
            self._thumbnail_label.setFixedSize(self.width(), self.height())
            self.layout.addWidget(self._thumbnail_label)
    
    def _setup_fallback(self):
        """Setup fallback display"""
        if not self._thumbnail_label:
            self._thumbnail_label = QLabel("3D Viewer\nUnavailable")
            self._thumbnail_label.setAlignment(Qt.AlignCenter)
            self._thumbnail_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #666;
                    border: 1px dashed #444;
                    font-size: 14px;
                }
            """)
            self._thumbnail_label.setFixedSize(self.width(), self.height())
            self.layout.addWidget(self._thumbnail_label)
    
    def load_model(self, model_path: Path):
        """Load a 3D model"""
        self._model_path = model_path
        
        # If we have an active viewer, load immediately
        if self._threejs_viewer:
            self._threejs_viewer.load_model(str(model_path))
        else:
            # Update thumbnail to show model name
            if self._thumbnail_label:
                self._thumbnail_label.setText(f"🎯 {model_path.stem}\nClick to view 3D")
    
    def mousePressEvent(self, event):
        """Handle mouse clicks for lazy loading"""
        if event.button() == Qt.LeftButton:
            if not self._is_active and not self._is_session_viewer:
                # Lazy load the 3D viewer on click
                self._setup_3d_viewer()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter for hover effect"""
        if self._thumbnail_label and not self._is_active:
            self._thumbnail_label.setStyleSheet("""
                QLabel {
                    background-color: #333;
                    color: #aaa;
                    border: 1px solid #4a4a4a;
                    font-size: 14px;
                    cursor: pointer;
                }
            """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        if self._thumbnail_label and not self._is_active:
            self._thumbnail_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #888;
                    border: 1px solid #3a3a3a;
                    font-size: 14px;
                }
            """)
        super().leaveEvent(event)
    
    def cleanup(self):
        """Cleanup resources"""
        self._deactivate_viewer()
    
    @classmethod
    def cleanup_all(cls):
        """Cleanup all viewers"""
        for viewer in cls._active_viewers[:]:
            viewer._deactivate_viewer()
        
        for viewer in cls._viewer_pool[:]:
            viewer.deleteLater()
        cls._viewer_pool.clear()

class ImageThumbnail(QFrame):
    """Thumbnail widget for images"""
    
    clicked = Signal(Path)
    selected = Signal(Path, bool)
    
    def __init__(self, image_path: Path, size: int = 256):
        super().__init__()
        self.image_path = image_path
        self.size = size
        self._selected = False
        self._loading = False
        
        self.setFixedSize(size + 20, size + 40)
        self.setFrameStyle(QFrame.NoFrame)  # Remove default frame, use CSS instead
        self.setObjectName("image_thumbnail")  # Set object name for specific CSS targeting
        
        # Main layout without spacing for absolute positioning
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(3)
        
        # Container for image with overlay checkbox
        image_container = QWidget()
        image_container.setFixedSize(size, size)
        main_layout.addWidget(image_container)
        
        # Image label (fills container)
        self.image_label = QLabel(image_container)
        self.image_label.setFixedSize(size, size)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2a2a2a;")
        
        # Selection checkbox (positioned in bottom-right corner)
        self.select_check = QCheckBox(image_container)
        self.select_check.setText("")  # No text, just checkbox
        checkbox_size = 16
        self.select_check.setFixedSize(checkbox_size, checkbox_size)
        self.select_check.move(size - checkbox_size - 4, size - checkbox_size - 4)  # 4px margin from edges
        self.select_check.setStyleSheet("""
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                background-color: rgba(23, 23, 23, 180);
                border: 1px solid #404040;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #22c55e;
                border-color: #22c55e;
            }
            QCheckBox::indicator:hover {
                border-color: #22c55e;
                background-color: rgba(34, 197, 94, 50);
            }
        """)
        self.select_check.stateChanged.connect(self._on_selection_changed)
        self.select_check.show()
        
        # Debug: Log initial checkbox state
        from loguru import logger
        logger.debug(f"ImageThumbnail created: {image_path.name}, checkbox checked: {self.select_check.isChecked()}, _selected: {self._selected}")
        
        # Filename label
        self.name_label = QLabel(image_path.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setMaximumWidth(size)
        self.name_label.setWordWrap(True)
        font = self.name_label.font()
        font.setPointSize(9)
        self.name_label.setFont(font)
        main_layout.addWidget(self.name_label)
        
        # Load thumbnail asynchronously
        self._load_thumbnail_async()
        
        # Apply initial style
        self._update_style()
        
    def _load_thumbnail_async(self):
        """Load thumbnail asynchronously"""
        if self._loading:
            return
            
        self._loading = True
        
        # Show loading placeholder
        self.image_label.setText("Loading...")
        self.image_label.setStyleSheet("""
            background-color: #2a2a2a;
            color: #888888;
            border: 1px dashed #444444;
        """)
        
        # Load image asynchronously
        async_manager = get_async_image_manager()
        async_manager.load_image_async(
            self.image_path, 
            self.size, 
            self._on_image_loaded
        )
    
    def _on_image_loaded(self, image_path: Path, pixmap: QPixmap, size: int):
        """Handle async image loading completion"""
        if image_path != self.image_path:
            return  # This callback is for a different image
            
        self._loading = False
        
        try:
            # Scale to fit if needed
            if pixmap.width() > self.size or pixmap.height() > self.size:
                scaled_pixmap = pixmap.scaled(
                    self.size, self.size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            else:
                scaled_pixmap = pixmap
            
            # Set the pixmap
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet("background-color: #2a2a2a;")
            
        except Exception as e:
            logger.error(f"Failed to display thumbnail for {self.image_path}: {e}")
            self._show_error_placeholder()
    
    def _show_error_placeholder(self):
        """Show error placeholder"""
        self._loading = False
        self.image_label.clear()
        self.image_label.setText("Failed to\nload image")
        self.image_label.setStyleSheet("""
            background-color: #2a2a2a;
            color: #ff6b6b;
            border: 1px solid #ff6b6b;
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)
    
    def _on_selection_changed(self, state):
        """Handle selection change"""
        # Fix: State 2 = Checked, State 0 = Unchecked  
        self._selected = state == 2
        from loguru import logger
        logger.info(f"ImageThumbnail selection changed: {self.image_path.name}, Qt state: {state}, _selected: {self._selected}")
        self.selected.emit(self.image_path, self._selected)
        self._update_style()
    
    def _update_style(self):
        """Update visual style based on selection"""
        # Set property for CSS selector and force style update
        self.setProperty("selected", self._selected)
        
        # Apply base style that includes both states
        self.setStyleSheet("""
            QFrame#image_thumbnail {
                border: 1px solid transparent;
                border-radius: 3px;
                background-color: transparent;
            }
            QFrame#image_thumbnail[selected="true"] {
                border: 1px solid #4CAF50;
            }
        """)
        
        # Force style refresh
        self.style().polish(self)
    
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
        
        # State preservation
        self._preserved_state = None
        self._preserve_state = True
        
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
        
        # Ensure thumbnail and its checkbox are visible
        thumbnail.show()
        thumbnail.select_check.show()
        thumbnail.select_check.setVisible(True)
    
    def preserve_state(self):
        """Preserve current grid state for restoration"""
        if not self._preserve_state:
            return
            
        self._preserved_state = {
            'images': [thumb.image_path for thumb in self.thumbnails],
            'selections': [thumb.image_path for thumb in self.thumbnails if thumb._selected],
            'scroll_position': self.verticalScrollBar().value(),
            'thumbnail_count': len(self.thumbnails)
        }
        logger.debug(f"Preserved state: {len(self._preserved_state['images'])} images, {len(self._preserved_state['selections'])} selected")
    
    def restore_state(self):
        """Restore preserved state"""
        if not self._preserved_state:
            return
            
        # Restore selections
        for thumbnail in self.thumbnails:
            should_be_selected = thumbnail.image_path in self._preserved_state['selections']
            if thumbnail._selected != should_be_selected:
                thumbnail.set_selected(should_be_selected)
        
        # Restore scroll position with a small delay to ensure layout is complete
        QTimer.singleShot(100, lambda: self.verticalScrollBar().setValue(self._preserved_state['scroll_position']))
        
        logger.debug(f"Restored state: {len(self._preserved_state['selections'])} selections, scroll position {self._preserved_state['scroll_position']}")
    
    def smart_refresh(self, new_images: List[Path]):
        """Smart refresh that preserves existing thumbnails and adds new ones"""
        if self._preserve_state:
            self.preserve_state()
        
        # Get current image paths
        existing_paths = {thumb.image_path for thumb in self.thumbnails}
        new_paths = set(new_images)
        
        # Remove thumbnails for images that no longer exist
        to_remove = []
        for i, thumbnail in enumerate(self.thumbnails):
            if thumbnail.image_path not in new_paths:
                to_remove.append(i)
        
        # Remove in reverse order to maintain indices
        for i in reversed(to_remove):
            thumbnail = self.thumbnails.pop(i)
            self.grid_layout.removeWidget(thumbnail)
            thumbnail.deleteLater()
        
        # Add new images
        for image_path in new_images:
            if image_path not in existing_paths and image_path.exists():
                self.add_image(image_path)
        
        # Reorganize grid to fill gaps
        self._reorganize_grid()
        
        # Restore state
        if self._preserve_state:
            self.restore_state()
        
        logger.debug(f"Smart refresh completed: {len(self.thumbnails)} total thumbnails")
    
    def clear(self):
        """Clear all images (with optional state preservation)"""
        if self._preserve_state:
            self.preserve_state()
            
        for thumbnail in self.thumbnails:
            self.grid_layout.removeWidget(thumbnail)
            thumbnail.deleteLater()
        self.thumbnails.clear()
        
        logger.debug("Grid cleared")
    
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




class ConsoleWidget(QTextEdit):
    """Console output widget with logging integration"""
    
    # Signal for thread-safe logging
    log_message = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        
        # Use JetBrains Mono font with fallbacks
        font = QFont()
        font.setFamilies(["JetBrains Mono", "Consolas", "Monaco", "Courier New", "monospace"])
        font.setPointSize(10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Console styling - focus and selection colors handled by accent color CSS
        self.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #fafafa;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 8px;
                line-height: 1.0;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        self.max_lines = 1000
        self._auto_scroll = True
        
        # Connect signal for thread-safe updates
        self.log_message.connect(self._append_log_message)
        
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
        """Log message to console - thread-safe via signal"""
        # Emit signal instead of direct update (thread-safe)
        self.log_message.emit(message)
    
    @Slot(str)
    def _append_log_message(self, message):
        """Actually append the log message (runs on main thread)"""
        message = message.strip()
        
        # Enhanced color coding with more detailed parsing
        if "| ERROR" in message or "| CRITICAL" in message:
            level_color = "#ef4444"  # Red
            icon = "❌"
        elif "| WARNING" in message:
            level_color = "#f59e0b"  # Amber
            icon = "⚠️"
        elif "| INFO" in message:
            level_color = "#10b981"  # Emerald
            icon = "ℹ️"
        elif "| DEBUG" in message:
            level_color = "#6b7280"  # Gray
            icon = "🔍"
        elif "✅" in message:
            level_color = "#22c55e"  # Green
            icon = ""
        elif "🎯" in message:
            level_color = "#3b82f6"  # Blue
            icon = ""
        elif "🧹" in message:
            level_color = "#8b5cf6"  # Purple
            icon = ""
        else:
            level_color = "#e5e7eb"  # Light gray
            icon = ""
        
        # Parse timestamp and level for better formatting
        parts = message.split(" | ", 2)
        if len(parts) >= 3:
            timestamp = parts[0]
            level = parts[1]
            content = parts[2]
            
            # Format as single line to eliminate div spacing
            html = f'<span style="color: #6b7280; font-size: 9px;">{timestamp}</span> <span style="color: {level_color}; font-weight: bold;">{level}</span> <span style="color: #fafafa;">{content}</span><br>'
        else:
            # Fallback for messages without standard format
            html = f'<span style="color: {level_color}; font-family: \'JetBrains Mono\', monospace;">{message}</span><br>'
        
        self.insertHtml(html)
        
        # Limit lines
        if self.document().blockCount() > self.max_lines:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 
                              self.document().blockCount() - self.max_lines)
            cursor.removeSelectedText()
        
        # Auto scroll
        if self._auto_scroll:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def set_auto_scroll(self, enabled: bool):
        """Enable/disable auto scroll"""
        self._auto_scroll = enabled