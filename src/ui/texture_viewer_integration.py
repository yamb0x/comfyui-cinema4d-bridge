"""
Texture Viewer Integration
Professional integration with run_final_viewer.bat and texture monitoring
"""

import subprocess
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QPixmap, QFont
from loguru import logger


class TextureViewerLauncher(QThread):
    """Thread for launching texture viewer"""
    
    # Signals
    launch_started = pyqtSignal()
    launch_completed = pyqtSignal(bool)  # success
    launch_error = pyqtSignal(str)  # error message
    
    def __init__(self, viewer_path: Path):
        super().__init__()
        self.viewer_path = viewer_path
        
    def run(self):
        """Launch texture viewer in separate thread"""
        self.launch_started.emit()
        
        try:
            if self.viewer_path.exists():
                # Launch the batch file
                process = subprocess.Popen(
                    [str(self.viewer_path)],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait a moment to see if it starts successfully
                self.msleep(1000)
                
                if process.poll() is None:
                    # Process is still running, assume success
                    self.launch_completed.emit(True)
                else:
                    # Process ended quickly, check for errors
                    stdout, stderr = process.communicate()
                    if stderr:
                        self.launch_error.emit(f"Viewer error: {stderr.decode()}")
                    else:
                        self.launch_completed.emit(True)
            else:
                self.launch_error.emit("Texture viewer not found")
                
        except Exception as e:
            self.launch_error.emit(f"Failed to launch viewer: {str(e)}")


class TexturedModelCard(QFrame):
    """
    Card widget for displaying textured model information
    """
    
    # Signals
    model_selected = Signal(str)  # model path
    view_in_viewer = Signal(str)  # model path
    
    def __init__(self, model_path: Path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.setObjectName("model_grid_item")
        self.setFixedSize(200, 240)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Model preview area (placeholder)
        preview_area = QLabel()
        preview_area.setObjectName("image_placeholder")
        preview_area.setText("3D Model\nPreview")
        preview_area.setAlignment(Qt.AlignCenter)
        preview_area.setMinimumHeight(140)
        preview_area.setStyleSheet("""
            background-color: #262626;
            border: 1px solid #404040;
            border-radius: 3px;
            color: #737373;
        """)
        layout.addWidget(preview_area)
        
        # Model info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Model name
        name_label = QLabel(self.model_path.stem)
        name_label.setObjectName("section_title")
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)
        
        # Model details
        size_text = f"Size: {self._get_file_size()}"
        size_label = QLabel(size_text)
        size_label.setObjectName("connection_info")
        info_layout.addWidget(size_label)
        
        # Modified time
        mod_time = self.model_path.stat().st_mtime
        import datetime
        time_str = datetime.datetime.fromtimestamp(mod_time).strftime("%H:%M")
        time_label = QLabel(f"Modified: {time_str}")
        time_label.setObjectName("connection_info")
        info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        # View button
        view_btn = QPushButton("View")
        view_btn.setObjectName("secondary_btn")
        view_btn.clicked.connect(self._on_view_clicked)
        buttons_layout.addWidget(view_btn)
        
        # Select button
        select_btn = QPushButton("Select")
        select_btn.setObjectName("primary_btn")
        select_btn.clicked.connect(self._on_select_clicked)
        buttons_layout.addWidget(select_btn)
        
        layout.addLayout(buttons_layout)
        
    def _get_file_size(self) -> str:
        """Get formatted file size"""
        try:
            size_bytes = self.model_path.stat().st_size
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            return "Unknown"
            
    def _on_view_clicked(self):
        """Handle view button click"""
        self.view_in_viewer.emit(str(self.model_path))
        
    def _on_select_clicked(self):
        """Handle select button click"""
        self.model_selected.emit(str(self.model_path))


class TextureViewerIntegration(QWidget):
    """
    Complete texture viewer integration widget
    """
    
    # Signals
    viewer_launched = Signal(bool)  # success
    model_selected = Signal(str)  # model path
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config
        # Use config path if available
        self.viewer_path = Path(config.texture_viewer_path) if config and hasattr(config, 'texture_viewer_path') else Path("viewer/run_final_viewer.bat")
        self.textured_models: List[Path] = []
        self.launcher_thread = None
        
        self.setup_ui()
        self.refresh_models()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_models)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds
        
    def setup_ui(self):
        """Setup integration UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header section
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
        # Models grid
        self.models_scroll = QScrollArea()
        self.models_scroll.setWidgetResizable(True)
        self.models_scroll.setMinimumHeight(300)
        
        self.models_content = QWidget()
        self.models_grid = QGridLayout(self.models_content)
        self.models_grid.setContentsMargins(16, 16, 16, 16)
        self.models_grid.setSpacing(12)
        
        self.models_scroll.setWidget(self.models_content)
        layout.addWidget(self.models_scroll)
        
        # Status section
        status_section = self._create_status_section()
        layout.addWidget(status_section)
        
    def _create_header(self) -> QHBoxLayout:
        """Create header section"""
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Textured Models")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Controls
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self.refresh_models)
        header_layout.addWidget(refresh_btn)
        
        self.launch_viewer_btn = QPushButton("LAUNCH TEXTURE VIEWER")
        self.launch_viewer_btn.setObjectName("launch_texture_viewer")
        self.launch_viewer_btn.clicked.connect(self.launch_viewer)
        header_layout.addWidget(self.launch_viewer_btn)
        
        return header_layout
        
    def _create_status_section(self) -> QGroupBox:
        """Create status section"""
        status_group = QGroupBox("Viewer Status")
        status_layout = QVBoxLayout(status_group)
        
        # Viewer availability
        self.viewer_status_label = QLabel()
        self.viewer_status_label.setObjectName("connection_info")
        status_layout.addWidget(self.viewer_status_label)
        
        # Models count
        self.models_count_label = QLabel()
        self.models_count_label.setObjectName("connection_info")
        status_layout.addWidget(self.models_count_label)
        
        # Launch progress
        self.launch_progress = QProgressBar()
        self.launch_progress.setVisible(False)
        status_layout.addWidget(self.launch_progress)
        
        self._update_status()
        
        return status_group
        
    def refresh_models(self):
        """Refresh textured models list"""
        # Use config computed property if available
        if self.config and hasattr(self.config, 'textured_models_dir'):
            textured_path = self.config.textured_models_dir
        elif self.config and hasattr(self.config, 'models_3d_dir'):
            textured_path = Path(self.config.models_3d_dir) / "textured"
        else:
            textured_path = Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D/textured")
        
        if not textured_path.exists():
            self.textured_models = []
            self._update_models_display()
            return
            
        # Find all textured models
        models = []
        for pattern in ["*.obj", "*.fbx", "*.dae", "*.gltf", "*.glb"]:
            models.extend(textured_path.glob(pattern))
            
        # Sort by modification time (newest first)
        models.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        self.textured_models = models
        self._update_models_display()
        self._update_status()
        
    def _update_models_display(self):
        """Update models grid display"""
        # Clear existing items
        for i in reversed(range(self.models_grid.count())):
            child = self.models_grid.itemAt(i).widget()
            if child:
                child.setParent(None)
                
        if not self.textured_models:
            # Show empty state
            empty_label = QLabel("No textured models found")
            empty_label.setObjectName("image_placeholder")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setMinimumHeight(200)
            self.models_grid.addWidget(empty_label, 0, 0)
            return
            
        # Add model cards
        cols = 4  # 4 cards per row
        for i, model in enumerate(self.textured_models[:20]):  # Limit to 20 models
            card = TexturedModelCard(model)
            card.model_selected.connect(self.model_selected.emit)
            card.view_in_viewer.connect(self._view_model_in_viewer)
            
            row = i // cols
            col = i % cols
            self.models_grid.addWidget(card, row, col)
            
    def _update_status(self):
        """Update status information"""
        # Viewer availability
        if self.viewer_path.exists():
            self.viewer_status_label.setText("✓ Texture viewer available")
            self.viewer_status_label.setStyleSheet("color: #22c55e;")
            self.launch_viewer_btn.setEnabled(True)
        else:
            self.viewer_status_label.setText("✗ Texture viewer not found")
            self.viewer_status_label.setStyleSheet("color: #ef4444;")
            self.launch_viewer_btn.setEnabled(False)
            
        # Models count
        count = len(self.textured_models)
        self.models_count_label.setText(f"Found {count} textured model{'s' if count != 1 else ''}")
        
    def launch_viewer(self):
        """Launch texture viewer"""
        if not self.viewer_path.exists():
            logger.error("Texture viewer not found")
            return
            
        # Show progress
        self.launch_progress.setVisible(True)
        self.launch_progress.setRange(0, 0)  # Indeterminate progress
        self.launch_viewer_btn.setEnabled(False)
        self.launch_viewer_btn.setText("LAUNCHING...")
        
        # Launch in thread
        self.launcher_thread = TextureViewerLauncher(self.viewer_path)
        self.launcher_thread.launch_started.connect(self._on_launch_started)
        self.launcher_thread.launch_completed.connect(self._on_launch_completed)
        self.launcher_thread.launch_error.connect(self._on_launch_error)
        self.launcher_thread.start()
        
    def _view_model_in_viewer(self, model_path: str):
        """View specific model in viewer"""
        logger.info(f"Viewing model in texture viewer: {Path(model_path).name}")
        self.launch_viewer()
        
    def _on_launch_started(self):
        """Handle launch started"""
        logger.info("Launching texture viewer...")
        
    def _on_launch_completed(self, success: bool):
        """Handle launch completed"""
        self.launch_progress.setVisible(False)
        self.launch_viewer_btn.setEnabled(True)
        self.launch_viewer_btn.setText("LAUNCH TEXTURE VIEWER")
        
        if success:
            logger.info("Texture viewer launched successfully")
            self.viewer_launched.emit(True)
        else:
            logger.error("Failed to launch texture viewer")
            self.viewer_launched.emit(False)
            
    def _on_launch_error(self, error_message: str):
        """Handle launch error"""
        self.launch_progress.setVisible(False)
        self.launch_viewer_btn.setEnabled(True)
        self.launch_viewer_btn.setText("LAUNCH TEXTURE VIEWER")
        
        logger.error(f"Texture viewer launch error: {error_message}")
        self.viewer_launched.emit(False)
        
    def get_textured_models_count(self) -> int:
        """Get count of textured models"""
        return len(self.textured_models)
        
    def get_latest_textured_model(self) -> Optional[Path]:
        """Get the latest textured model"""
        return self.textured_models[0] if self.textured_models else None