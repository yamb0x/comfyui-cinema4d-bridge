"""
Unified Parameter Panel Widget
Consistent parameter display across all tabs with proper layout management
"""

from typing import Dict, Any, Optional, Set
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit,
    QCheckBox, QGroupBox, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor
from loguru import logger

from src.core.unified_configuration_manager import UnifiedConfigurationManager
from src.core.workflow_parameter_extractor import WorkflowParameterExtractor


class ParameterWidget(QWidget):
    """Individual parameter widget with consistent styling"""
    
    value_changed = Signal(str, object)  # param_key, value
    
    def __init__(self, param_key: str, param_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.param_key = param_key
        self.param_data = param_data
        self.setup_ui()
    
    def setup_ui(self):
        """Create the parameter widget based on type"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)
        
        # Parameter label
        label = QLabel(self.param_data.get("ui_name", self.param_key))
        label.setMinimumWidth(80)  # Reduced for more compact panels
        label.setMaximumWidth(150)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Create appropriate input widget
        param_type = self.param_data.get("type", "text")
        current_value = self.param_data.get("current_value", self.param_data.get("default"))
        
        if param_type == "int":
            self.input_widget = QSpinBox()
            self.input_widget.setMinimum(self.param_data.get("min", 0))
            self.input_widget.setMaximum(self.param_data.get("max", 2147483647))
            self.input_widget.setValue(int(current_value) if current_value is not None else 0)
            self.input_widget.valueChanged.connect(lambda v: self.value_changed.emit(self.param_key, v))
            
        elif param_type == "float":
            self.input_widget = QDoubleSpinBox()
            self.input_widget.setMinimum(self.param_data.get("min", 0.0))
            self.input_widget.setMaximum(self.param_data.get("max", 999999.0))
            self.input_widget.setDecimals(2)
            self.input_widget.setSingleStep(0.1)
            self.input_widget.setValue(float(current_value) if current_value is not None else 0.0)
            self.input_widget.valueChanged.connect(lambda v: self.value_changed.emit(self.param_key, v))
            
        elif param_type == "choice":
            self.input_widget = QComboBox()
            choices = self._get_choices()
            self.input_widget.addItems(choices)
            if current_value and str(current_value) in choices:
                self.input_widget.setCurrentText(str(current_value))
            self.input_widget.currentTextChanged.connect(lambda v: self.value_changed.emit(self.param_key, v))
            
        else:  # text
            self.input_widget = QLineEdit()
            self.input_widget.setText(str(current_value) if current_value is not None else "")
            self.input_widget.textChanged.connect(lambda v: self.value_changed.emit(self.param_key, v))
        
        # Set size policy for input widget
        self.input_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.input_widget)
    
    def _get_choices(self) -> list:
        """Get choices for dropdown parameters"""
        param_name = self.param_data.get("param_name", "")
        
        if param_name == "sampler_name":
            return WorkflowParameterExtractor.SAMPLER_CHOICES
        elif param_name == "scheduler":
            return WorkflowParameterExtractor.SCHEDULER_CHOICES
        else:
            # For model selections, we'd need to query available models
            # For now, return a placeholder
            return ["default", "none"]
    
    def update_value(self, value: Any):
        """Update the widget value programmatically"""
        if isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            self.input_widget.setValue(value)
        elif isinstance(self.input_widget, QComboBox):
            self.input_widget.setCurrentText(str(value))
        elif isinstance(self.input_widget, QLineEdit):
            self.input_widget.setText(str(value))


class UnifiedParameterPanel(QWidget):
    """
    Unified parameter panel that displays workflow parameters consistently
    Solves the configuration consistency issues across tabs
    """
    
    parameter_changed = Signal(str, object)  # param_key, value
    
    def __init__(self, config_manager: UnifiedConfigurationManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.parameter_widgets: Dict[str, ParameterWidget] = {}
        self.setup_ui()
        
        # Connect to configuration manager signals
        self.config_manager.parameters_updated.connect(self.update_parameters)
    
    def setup_ui(self):
        """Setup the UI with proper layout management"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for parameters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container for scrollable content
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll_layout.setSpacing(12)
        
        # Add initial info label
        self.info_label = QLabel("No workflow loaded. Use File menu to configure parameters.")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #888; padding: 20px;")
        self.scroll_layout.addWidget(self.info_label)
        
        # Add stretch to push content to top
        self.scroll_layout.addStretch()
        
        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Set size constraints to prevent excessive expansion
        self.setMaximumHeight(600)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
    
    def update_parameters(self, parameters: Dict[str, Any]):
        """Update the parameter display with new configuration"""
        # Clear existing widgets
        self._clear_parameters()
        
        if not parameters:
            self.info_label.show()
            return
        
        self.info_label.hide()
        
        # Group parameters by section
        for node_type, section_data in parameters.items():
            # Create section group
            section_widget = self._create_section(node_type, section_data)
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, section_widget)
        
        # Update the layout
        self.scroll_content.adjustSize()
    
    def _create_section(self, node_type: str, section_data: Dict[str, Any]) -> QGroupBox:
        """Create a parameter section with proper styling"""
        # Create group box with colored title
        group_box = QGroupBox(section_data.get("display_name", node_type))
        group_box.setObjectName("parameter_section")
        
        # Apply color coding
        color = section_data.get("color", "#666666")
        group_box.setStyleSheet(f"""
            QGroupBox#parameter_section {{
                border: 1px solid {color};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }}
            QGroupBox#parameter_section::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {color};
            }}
        """)
        
        # Create layout for parameters
        layout = QVBoxLayout(group_box)
        layout.setSpacing(4)
        
        # Add parameters
        parameters = section_data.get("parameters", {})
        for param_name, param_data in parameters.items():
            # Skip certain parameters that are handled separately
            if param_name == "text" and node_type == "CLIPTextEncode":
                continue  # Prompts are handled by dedicated widgets
            
            # Create parameter widget
            param_key = f"{node_type}_{section_data.get('node_id', '')}_{param_name}"
            param_widget = ParameterWidget(param_key, param_data)
            param_widget.value_changed.connect(self._on_parameter_changed)
            
            # Store reference
            self.parameter_widgets[param_key] = param_widget
            
            # Add to layout with proper wrapping
            layout.addWidget(param_widget)
        
        return group_box
    
    def _clear_parameters(self):
        """Clear all parameter widgets"""
        # Remove all widgets except info label and stretch
        while self.scroll_layout.count() > 2:
            item = self.scroll_layout.takeAt(0)
            if item.widget() and item.widget() != self.info_label:
                item.widget().deleteLater()
        
        self.parameter_widgets.clear()
    
    def _on_parameter_changed(self, param_key: str, value: Any):
        """Handle parameter value changes"""
        # Update configuration manager
        self.config_manager.update_parameter(param_key, value, is_user_override=True)
        
        # Emit signal for other components
        self.parameter_changed.emit(param_key, value)
        
        logger.debug(f"Parameter changed: {param_key} = {value}")
    
    def get_parameter_values(self) -> Dict[str, Any]:
        """Get all current parameter values"""
        values = {}
        for param_key, widget in self.parameter_widgets.items():
            if hasattr(widget, 'input_widget'):
                if isinstance(widget.input_widget, (QSpinBox, QDoubleSpinBox)):
                    values[param_key] = widget.input_widget.value()
                elif isinstance(widget.input_widget, QComboBox):
                    values[param_key] = widget.input_widget.currentText()
                elif isinstance(widget.input_widget, QLineEdit):
                    values[param_key] = widget.input_widget.text()
        return values
    
    def set_parameter_value(self, param_key: str, value: Any):
        """Set a specific parameter value"""
        if param_key in self.parameter_widgets:
            self.parameter_widgets[param_key].update_value(value)


class CompactParameterPanel(UnifiedParameterPanel):
    """Compact version of parameter panel for right sidebar"""
    
    def __init__(self, config_manager: UnifiedConfigurationManager, parent=None):
        super().__init__(config_manager, parent)
        
        # Override size constraints for compact mode
        self.setMaximumHeight(400)
        self.setMinimumHeight(150)