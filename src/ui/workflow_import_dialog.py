"""
Workflow Import Dialog with Improved Layout
Fixes the wide parameter list issue with proper line wrapping
"""

from typing import Dict, Any, Set
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QCheckBox, QPushButton, QFileDialog,
    QGroupBox, QGridLayout, QWidget, QSizePolicy,
    QDialogButtonBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from loguru import logger

from src.core.unified_configuration_manager import UnifiedConfigurationManager


class WorkflowImportDialog(QDialog):
    """
    Import dialog for ComfyUI workflow configuration
    Implements proper layout with line wrapping for parameters
    """
    
    parameters_selected = Signal(dict)  # Selected parameters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = UnifiedConfigurationManager()
        self.parameter_checkboxes: Dict[str, QCheckBox] = {}
        self.selected_parameters: Set[str] = set()
        
        self.setWindowTitle("Import Workflow Configuration")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI with proper layout"""
        # Set reasonable dialog size
        self.setMinimumSize(600, 400)
        self.setMaximumSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # File selection section
        file_section = self._create_file_section()
        layout.addWidget(file_section)
        
        # Parameters section with scroll area
        params_label = QLabel("Select Parameters to Import:")
        params_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(params_label)
        
        # Scroll area for parameters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Container for parameters
        self.params_container = QWidget()
        self.params_layout = QVBoxLayout(self.params_container)
        self.params_layout.setSpacing(8)
        
        # Info label when no workflow loaded
        self.info_label = QLabel("Select a workflow file to see available parameters")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #888; padding: 40px;")
        self.params_layout.addWidget(self.info_label)
        
        scroll_area.setWidget(self.params_container)
        layout.addWidget(scroll_area, 1)  # Give scroll area most space
        
        # Quick selection buttons
        quick_buttons = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        self.select_none_btn = QPushButton("Select None")
        self.select_none_btn.clicked.connect(self._select_none)
        self.select_important_btn = QPushButton("Select Important")
        self.select_important_btn.clicked.connect(self._select_important)
        
        quick_buttons.addWidget(self.select_all_btn)
        quick_buttons.addWidget(self.select_none_btn)
        quick_buttons.addWidget(self.select_important_btn)
        quick_buttons.addStretch()
        
        layout.addLayout(quick_buttons)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        
        layout.addWidget(self.button_box)
    
    def _create_file_section(self) -> QWidget:
        """Create file selection section"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Workflow File:")
        label.setMinimumWidth(80)  # Reduced for more compact panels
        layout.addWidget(label)
        
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: #888;")
        layout.addWidget(self.file_path_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_workflow)
        layout.addWidget(browse_btn)
        
        return widget
    
    def _browse_workflow(self):
        """Browse for workflow file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ComfyUI Workflow",
            str(Path("workflows")),
            "JSON Files (*.json)"
        )
        
        if file_path:
            self._load_workflow(Path(file_path))
    
    def _load_workflow(self, workflow_path: Path):
        """Load workflow and display parameters"""
        try:
            # Update file label
            self.file_path_label.setText(workflow_path.name)
            self.file_path_label.setStyleSheet("color: #4CAF50;")
            
            # Load parameters
            parameters = self.config_manager.load_workflow_configuration(workflow_path)
            
            # Clear existing parameter display
            self._clear_parameters()
            
            if parameters:
                self.info_label.hide()
                self._display_parameters(parameters)
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            else:
                self.info_label.setText("No parameters found in workflow")
                self.info_label.show()
                
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            self.info_label.setText(f"Error loading workflow: {str(e)}")
            self.info_label.show()
    
    def _display_parameters(self, parameters: Dict[str, Any]):
        """Display parameters with proper grouping and wrapping"""
        # Create sections for each node type
        for node_type, section_data in parameters.items():
            section_widget = self._create_parameter_section(node_type, section_data)
            self.params_layout.insertWidget(self.params_layout.count() - 1, section_widget)
    
    def _create_parameter_section(self, node_type: str, section_data: Dict[str, Any]) -> QGroupBox:
        """Create a parameter section with grid layout for wrapping"""
        display_name = section_data.get("display_name", node_type)
        color = section_data.get("color", "#666666")
        
        # Create group box
        group_box = QGroupBox(display_name)
        group_box.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {color};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {color};
                font-weight: bold;
            }}
        """)
        
        # Use grid layout for better wrapping
        grid_layout = QGridLayout(group_box)
        grid_layout.setSpacing(8)
        
        # Add parameters in a grid (2 columns)
        parameters = section_data.get("parameters", {})
        row = 0
        col = 0
        
        for param_name, param_data in parameters.items():
            # Skip prompts (handled separately)
            if param_name == "text" and node_type == "CLIPTextEncode":
                continue
            
            # Create checkbox
            param_key = f"{node_type}_{section_data.get('node_id', '')}_{param_name}"
            checkbox = QCheckBox(param_data.get("ui_name", param_name))
            checkbox.setChecked(True)  # Default to checked
            checkbox.stateChanged.connect(lambda state, key=param_key: self._on_param_toggled(key, state))
            
            # Store reference
            self.parameter_checkboxes[param_key] = checkbox
            self.selected_parameters.add(param_key)
            
            # Add to grid
            grid_layout.addWidget(checkbox, row, col)
            
            # Move to next position
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
        
        return group_box
    
    def _clear_parameters(self):
        """Clear parameter display"""
        while self.params_layout.count() > 1:  # Keep info label
            item = self.params_layout.takeAt(0)
            if item.widget() and item.widget() != self.info_label:
                item.widget().deleteLater()
        
        self.parameter_checkboxes.clear()
        self.selected_parameters.clear()
    
    def _on_param_toggled(self, param_key: str, state: int):
        """Handle parameter checkbox toggle"""
        if state == Qt.Checked:
            self.selected_parameters.add(param_key)
        else:
            self.selected_parameters.discard(param_key)
    
    def _select_all(self):
        """Select all parameters"""
        for checkbox in self.parameter_checkboxes.values():
            checkbox.setChecked(True)
    
    def _select_none(self):
        """Deselect all parameters"""
        for checkbox in self.parameter_checkboxes.values():
            checkbox.setChecked(False)
    
    def _select_important(self):
        """Select only important parameters"""
        important_types = ["KSampler", "CheckpointLoader", "CheckpointLoaderSimple", "LoraLoader"]
        
        for param_key, checkbox in self.parameter_checkboxes.items():
            # Check if this parameter belongs to an important node type
            node_type = param_key.split('_')[0]
            checkbox.setChecked(node_type in important_types)
    
    def _on_accept(self):
        """Handle dialog acceptance"""
        # Update configuration manager with selected parameters
        for param_key in self.parameter_checkboxes:
            is_visible = param_key in self.selected_parameters
            self.config_manager.set_parameter_visibility(param_key, is_visible)
        
        # Emit signal with configuration
        config = self.config_manager.get_all_parameters()
        self.parameters_selected.emit(config)
        
        self.accept()
    
    def get_selected_parameters(self) -> Dict[str, Any]:
        """Get the selected parameters configuration"""
        return self.config_manager.get_all_parameters()