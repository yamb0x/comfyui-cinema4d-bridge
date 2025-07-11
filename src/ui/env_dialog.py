"""
Environment Variables Configuration Dialog
"""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QLineEdit, QGroupBox, 
    QDialogButtonBox, QFileDialog, QTabWidget, 
    QWidget, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from loguru import logger


class EnvironmentVariablesDialog(QDialog):
    """Dialog for configuring environment variables"""
    
    env_updated = Signal()  # Emitted when environment is saved
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Environment Variables Configuration")
        self.setModal(True)
        self.resize(800, 600)
        
        # Apply terminal theme styling
        self._apply_terminal_theme()
        
        self._setup_ui()
        self._load_current_values()
    
    def _apply_terminal_theme(self):
        """Apply terminal theme styling to the dialog"""
        from ui.terminal_theme_complete import get_complete_terminal_theme
        self.setStyleSheet(get_complete_terminal_theme())
        
    def _setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Configure application paths and settings")
        header.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Create tabs for different sections
        tabs = QTabWidget()
        
        # Application Paths tab
        app_paths_tab = self._create_app_paths_tab()
        tabs.addTab(app_paths_tab, "Application Paths")
        
        # ComfyUI Integration tab
        comfyui_tab = self._create_comfyui_tab()
        tabs.addTab(comfyui_tab, "ComfyUI Integration")
        
        # Cinema4D Integration tab
        c4d_tab = self._create_c4d_tab()
        tabs.addTab(c4d_tab, "Cinema4D Integration")
        
        # API Configuration tab
        api_tab = self._create_api_tab()
        tabs.addTab(api_tab, "API Configuration")
        
        # 3D Viewer Settings tab
        viewer_tab = self._create_viewer_tab()
        tabs.addTab(viewer_tab, "3D Viewer Settings")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._save_env)
        
        # Reload from .env button
        reload_btn = QPushButton("Reload from .env")
        reload_btn.clicked.connect(self._load_current_values)
        button_box.addButton(reload_btn, QDialogButtonBox.ActionRole)
        
        layout.addWidget(button_box)
        
    def _create_app_paths_tab(self) -> QWidget:
        """Create application paths configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Project Root
        self.project_root_edit = self._create_path_field()
        layout.addRow("Project Root:", self.project_root_edit)
        
        # Cinema4D Python Scripts
        self.cinema4d_scripts_edit = self._create_path_field()
        layout.addRow("Cinema4D Python Scripts:", self.cinema4d_scripts_edit)
        
        # ComfyUI Workflows
        self.workflows_edit = self._create_path_field()
        layout.addRow("ComfyUI Workflows:", self.workflows_edit)
        
        # Generated Images
        self.images_dir_edit = self._create_path_field()
        layout.addRow("Generated Images Dir:", self.images_dir_edit)
        
        # Logs Directory
        self.logs_dir_edit = self._create_path_field()
        layout.addRow("Logs Directory:", self.logs_dir_edit)
        
        return widget
        
    def _create_comfyui_tab(self) -> QWidget:
        """Create ComfyUI integration configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # ComfyUI Root
        self.comfyui_root_edit = self._create_path_field()
        layout.addRow("ComfyUI Root:", self.comfyui_root_edit)
        
        # Image Output Directory
        self.image_output_edit = self._create_path_field()
        layout.addRow("Image Output Dir:", self.image_output_edit)
        
        # 3D Output Directory
        self.output_3d_edit = self._create_path_field()
        layout.addRow("3D Output Dir:", self.output_3d_edit)
        
        # Checkpoints Directory
        self.checkpoints_edit = self._create_path_field()
        layout.addRow("Checkpoints Dir:", self.checkpoints_edit)
        
        # LoRAs Directory
        self.loras_edit = self._create_path_field()
        layout.addRow("LoRAs Dir:", self.loras_edit)
        
        return widget
        
    def _create_c4d_tab(self) -> QWidget:
        """Create Cinema4D integration configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # C4D Scripts Directory
        self.c4d_scripts_dir_edit = self._create_path_field()
        layout.addRow("C4D Scripts Dir:", self.c4d_scripts_dir_edit)
        
        # C4D Project Files Directory
        self.c4d_project_dir_edit = self._create_path_field()
        layout.addRow("C4D Project Files Dir:", self.c4d_project_dir_edit)
        
        return widget
        
    def _create_api_tab(self) -> QWidget:
        """Create API configuration tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # ComfyUI API URL
        self.comfyui_api_edit = QLineEdit()
        layout.addRow("ComfyUI API URL:", self.comfyui_api_edit)
        
        # C4D MCP Port
        self.c4d_port_edit = QLineEdit()
        layout.addRow("C4D MCP Port:", self.c4d_port_edit)
        
        return widget
        
    def _create_viewer_tab(self) -> QWidget:
        """Create 3D viewer settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Background Color
        self.bg_color_edit = QLineEdit()
        layout.addRow("Background Color:", self.bg_color_edit)
        
        # Grid Color
        self.grid_color_edit = QLineEdit()
        layout.addRow("Grid Color:", self.grid_color_edit)
        
        # Grid Opacity
        self.grid_opacity_edit = QLineEdit()
        layout.addRow("Grid Opacity:", self.grid_opacity_edit)
        
        # Max Models in Grid
        self.max_models_edit = QLineEdit()
        layout.addRow("Max Models in Grid:", self.max_models_edit)
        
        # Enable Textures
        self.enable_textures_edit = QLineEdit()
        layout.addRow("Enable Textures:", self.enable_textures_edit)
        
        # Enable Shadows
        self.enable_shadows_edit = QLineEdit()
        layout.addRow("Enable Shadows:", self.enable_shadows_edit)
        
        return widget
        
    def _create_path_field(self) -> QWidget:
        """Create a path field with browse button"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        edit = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.setMaximumWidth(80)
        browse_btn.clicked.connect(lambda: self._browse_for_path(edit))
        
        layout.addWidget(edit, 1)
        layout.addWidget(browse_btn)
        
        # Store reference to the line edit
        widget.line_edit = edit
        
        return widget
        
    def _browse_for_path(self, edit_widget):
        """Browse for a directory path"""
        current_path = edit_widget.text()
        path = QFileDialog.getExistingDirectory(
            self, "Select Directory", current_path
        )
        if path:
            edit_widget.setText(path)
            
    def _load_current_values(self):
        """Load current environment variable values"""
        # Application Paths
        self.project_root_edit.line_edit.setText(
            os.getenv("PROJECT_ROOT", str(self.config.base_dir))
        )
        self.cinema4d_scripts_edit.line_edit.setText(
            os.getenv("CINEMA4D_PYTHON_SCRIPTS", "")
        )
        self.workflows_edit.line_edit.setText(
            os.getenv("COMFYUI_WORKFLOWS", "")
        )
        self.images_dir_edit.line_edit.setText(
            os.getenv("GENERATED_IMAGES_DIR", "")
        )
        self.logs_dir_edit.line_edit.setText(
            os.getenv("LOGS_DIR", "")
        )
        
        # ComfyUI Integration
        self.comfyui_root_edit.line_edit.setText(
            os.getenv("COMFYUI_ROOT", "")
        )
        self.image_output_edit.line_edit.setText(
            os.getenv("COMFYUI_IMAGE_OUTPUT_DIR", "")
        )
        self.output_3d_edit.line_edit.setText(
            os.getenv("COMFYUI_3D_OUTPUT_DIR", "")
        )
        self.checkpoints_edit.line_edit.setText(
            os.getenv("COMFYUI_CHECKPOINTS", "")
        )
        self.loras_edit.line_edit.setText(
            os.getenv("COMFYUI_LORAS", "")
        )
        
        # Cinema4D Integration
        self.c4d_scripts_dir_edit.line_edit.setText(
            os.getenv("C4D_SCRIPTS_DIR", "")
        )
        self.c4d_project_dir_edit.line_edit.setText(
            os.getenv("C4D_FILES_PROJECT_DIR", "")
        )
        
        # API Configuration
        self.comfyui_api_edit.setText(
            os.getenv("COMFYUI_API_URL", "http://127.0.0.1:8188")
        )
        self.c4d_port_edit.setText(
            os.getenv("C4D_MCP_PORT", "54321")
        )
        
        # 3D Viewer Settings
        self.bg_color_edit.setText(
            os.getenv("VIEWER_BACKGROUND_COLOR", "#1a1a1a")
        )
        self.grid_color_edit.setText(
            os.getenv("VIEWER_GRID_COLOR", "#333333")
        )
        self.grid_opacity_edit.setText(
            os.getenv("VIEWER_GRID_OPACITY", "0.3")
        )
        self.max_models_edit.setText(
            os.getenv("VIEWER_MAX_MODELS_GRID", "100")
        )
        self.enable_textures_edit.setText(
            os.getenv("VIEWER_ENABLE_TEXTURES", "true")
        )
        self.enable_shadows_edit.setText(
            os.getenv("VIEWER_ENABLE_SHADOWS", "true")
        )
        
    def _save_env(self):
        """Save environment variables to .env file"""
        try:
            env_file = self.config.base_dir / ".env"
            
            # Read existing .env content
            existing_vars = {}
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_vars[key] = value
            
            # Update with new values
            new_vars = {
                "PROJECT_ROOT": self.project_root_edit.line_edit.text(),
                "CINEMA4D_PYTHON_SCRIPTS": self.cinema4d_scripts_edit.line_edit.text(),
                "COMFYUI_WORKFLOWS": self.workflows_edit.line_edit.text(),
                "GENERATED_IMAGES_DIR": self.images_dir_edit.line_edit.text(),
                "LOGS_DIR": self.logs_dir_edit.line_edit.text(),
                "COMFYUI_ROOT": self.comfyui_root_edit.line_edit.text(),
                "COMFYUI_IMAGE_OUTPUT_DIR": self.image_output_edit.line_edit.text(),
                "COMFYUI_3D_OUTPUT_DIR": self.output_3d_edit.line_edit.text(),
                "COMFYUI_CHECKPOINTS": self.checkpoints_edit.line_edit.text(),
                "COMFYUI_LORAS": self.loras_edit.line_edit.text(),
                "C4D_SCRIPTS_DIR": self.c4d_scripts_dir_edit.line_edit.text(),
                "C4D_FILES_PROJECT_DIR": self.c4d_project_dir_edit.line_edit.text(),
                "COMFYUI_API_URL": self.comfyui_api_edit.text(),
                "C4D_MCP_PORT": self.c4d_port_edit.text(),
                "VIEWER_BACKGROUND_COLOR": self.bg_color_edit.text(),
                "VIEWER_GRID_COLOR": self.grid_color_edit.text(),
                "VIEWER_GRID_OPACITY": self.grid_opacity_edit.text(),
                "VIEWER_MAX_MODELS_GRID": self.max_models_edit.text(),
                "VIEWER_ENABLE_TEXTURES": self.enable_textures_edit.text(),
                "VIEWER_ENABLE_SHADOWS": self.enable_shadows_edit.text(),
            }
            
            # Merge with existing
            existing_vars.update(new_vars)
            
            # Write back to .env file
            with open(env_file, 'w') as f:
                f.write("# comfy2c4d - Environment Configuration\n")
                f.write("# Generated by Environment Variables dialog\n\n")
                
                # Group by sections
                sections = {
                    "Application Paths": [
                        "PROJECT_ROOT", "CINEMA4D_PYTHON_SCRIPTS", 
                        "COMFYUI_WORKFLOWS", "GENERATED_IMAGES_DIR", "LOGS_DIR"
                    ],
                    "ComfyUI Integration": [
                        "COMFYUI_ROOT", "COMFYUI_IMAGE_OUTPUT_DIR", 
                        "COMFYUI_3D_OUTPUT_DIR", "COMFYUI_CHECKPOINTS", "COMFYUI_LORAS"
                    ],
                    "Cinema4D Integration": [
                        "C4D_SCRIPTS_DIR", "C4D_FILES_PROJECT_DIR"
                    ],
                    "API Configuration": [
                        "COMFYUI_API_URL", "C4D_MCP_PORT"
                    ],
                    "3D Viewer Settings": [
                        "VIEWER_BACKGROUND_COLOR", "VIEWER_GRID_COLOR", 
                        "VIEWER_GRID_OPACITY", "VIEWER_MAX_MODELS_GRID", 
                        "VIEWER_ENABLE_TEXTURES", "VIEWER_ENABLE_SHADOWS"
                    ]
                }
                
                for section, keys in sections.items():
                    f.write(f"# {'=' * 20}\n")
                    f.write(f"# {section}\n")
                    f.write(f"# {'=' * 20}\n")
                    for key in keys:
                        if key in existing_vars:
                            f.write(f"{key}={existing_vars[key]}\n")
                    f.write("\n")
            
            self.env_updated.emit()
            QMessageBox.information(self, "Success", "Environment variables saved successfully!")
            logger.info(f"Environment variables saved to {env_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save environment variables:\n{str(e)}")
            logger.error(f"Failed to save environment variables: {e}")
            
    def _save_and_close(self):
        """Save and close the dialog"""
        self._save_env()
        self.accept()