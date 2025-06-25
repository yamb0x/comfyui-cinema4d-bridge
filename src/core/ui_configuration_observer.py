"""
UI Configuration Observer for ComfyUI to Cinema4D Bridge
Bridges the Configuration Manager with UI components for automatic synchronization
"""

from typing import Dict, Any, Optional, Callable, List
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit
from loguru import logger

from src.core.configuration_manager import ConfigurationObserver, ConfigurationManager
from src.utils.logger import LoggerMixin


class UIConfigurationObserver(QObject, ConfigurationObserver, LoggerMixin):
    """Observer that synchronizes configuration changes with UI components"""
    
    # Signals for UI updates
    configuration_loaded = Signal(str, dict)  # config_type, config_data
    parameters_changed = Signal(str, dict)    # config_type, changes
    configuration_error = Signal(str, str)    # config_type, error_message
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the UI configuration observer
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # UI component mappings
        self._parameter_widgets: Dict[str, Dict[str, QWidget]] = {}
        self._workflow_dropdowns: Dict[str, QComboBox] = {}
        self._update_callbacks: Dict[str, List[Callable]] = {}
        
        # State tracking
        self._updating_ui = False
        self._batch_update_timer = QTimer()
        self._batch_update_timer.timeout.connect(self._process_batch_updates)
        self._pending_updates: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("UIConfigurationObserver initialized")
    
    def register_parameter_widget(self, config_type: str, param_key: str, widget: QWidget) -> None:
        """Register a UI widget for a specific parameter
        
        Args:
            config_type: Type of configuration
            param_key: Parameter key
            widget: UI widget to update
        """
        if config_type not in self._parameter_widgets:
            self._parameter_widgets[config_type] = {}
        
        self._parameter_widgets[config_type][param_key] = widget
        
        # Connect widget changes to parameter updates
        self._connect_widget_signals(widget, config_type, param_key)
        
        self.logger.debug(f"Registered widget for {config_type}.{param_key}")
    
    def register_workflow_dropdown(self, config_type: str, dropdown: QComboBox) -> None:
        """Register a workflow dropdown for a configuration type
        
        Args:
            config_type: Type of configuration
            dropdown: Workflow dropdown widget
        """
        self._workflow_dropdowns[config_type] = dropdown
        
        # Connect dropdown changes
        dropdown.currentTextChanged.connect(
            lambda text: self._on_workflow_dropdown_changed(config_type, text)
        )
        
        self.logger.debug(f"Registered workflow dropdown for {config_type}")
    
    def register_update_callback(self, config_type: str, callback: Callable) -> None:
        """Register a callback for configuration updates
        
        Args:
            config_type: Type of configuration
            callback: Callback function
        """
        if config_type not in self._update_callbacks:
            self._update_callbacks[config_type] = []
        
        self._update_callbacks[config_type].append(callback)
        self.logger.debug(f"Registered update callback for {config_type}")
    
    # ConfigurationObserver implementation
    
    def on_configuration_changed(self, config_type: str, changes: Dict[str, Any]) -> None:
        """Handle configuration changes
        
        Args:
            config_type: Type of configuration that changed
            changes: Dictionary of changes
        """
        self.logger.debug(f"Configuration changed for {config_type}: {len(changes)} parameters")
        
        # Batch updates to prevent UI flicker
        if config_type not in self._pending_updates:
            self._pending_updates[config_type] = {}
        
        self._pending_updates[config_type].update(changes)
        
        # Start batch timer if not running
        if not self._batch_update_timer.isActive():
            self._batch_update_timer.start(100)  # 100ms delay
        
        # Emit signal for other components
        self.parameters_changed.emit(config_type, changes)
    
    def on_configuration_loaded(self, config_type: str, config_data: Dict[str, Any]) -> None:
        """Handle configuration loaded event
        
        Args:
            config_type: Type of configuration loaded
            config_data: Complete configuration data
        """
        self.logger.info(f"Configuration loaded for {config_type}")
        
        # Update workflow dropdown if registered
        if config_type in self._workflow_dropdowns:
            self._update_workflow_dropdown(config_type, config_data)
        
        # Update all parameter widgets
        self._update_all_parameter_widgets(config_type, config_data.get("parameters", {}))
        
        # Call update callbacks
        if config_type in self._update_callbacks:
            for callback in self._update_callbacks[config_type]:
                try:
                    callback(config_data)
                except Exception as e:
                    self.logger.error(f"Error in update callback: {e}")
        
        # Emit signal
        self.configuration_loaded.emit(config_type, config_data)
    
    def on_configuration_error(self, config_type: str, error: Exception) -> None:
        """Handle configuration error
        
        Args:
            config_type: Type of configuration that had error
            error: The exception that occurred
        """
        self.logger.error(f"Configuration error for {config_type}: {error}")
        
        # Emit signal
        self.configuration_error.emit(config_type, str(error))
    
    # Private methods
    
    def _connect_widget_signals(self, widget: QWidget, config_type: str, param_key: str) -> None:
        """Connect widget signals for parameter updates"""
        if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(
                lambda value: self._on_widget_value_changed(config_type, param_key, value)
            )
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(
                lambda checked: self._on_widget_value_changed(config_type, param_key, checked)
            )
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(
                lambda text: self._on_widget_value_changed(config_type, param_key, text)
            )
        elif isinstance(widget, QLineEdit):
            # Use editingFinished to avoid too many updates
            widget.editingFinished.connect(
                lambda: self._on_widget_value_changed(config_type, param_key, widget.text())
            )
    
    def _on_widget_value_changed(self, config_type: str, param_key: str, value: Any) -> None:
        """Handle widget value change"""
        if self._updating_ui:
            return  # Prevent feedback loops
        
        # Get configuration manager instance
        from pathlib import Path
        config_manager = ConfigurationManager(Path("config"))
        
        # Update parameter
        config_manager.update_parameter(config_type, param_key, value, is_user_override=True)
        
        self.logger.debug(f"Updated {config_type}.{param_key} = {value}")
    
    def _on_workflow_dropdown_changed(self, config_type: str, workflow_name: str) -> None:
        """Handle workflow dropdown change"""
        if self._updating_ui:
            return
        
        self.logger.info(f"Workflow dropdown changed for {config_type}: {workflow_name}")
        
        # Find workflow path
        # TODO: Implement workflow path resolution
        # For now, emit signal for main app to handle
        self.configuration_loaded.emit(config_type, {"workflow_name": workflow_name})
    
    def _update_workflow_dropdown(self, config_type: str, config_data: Dict[str, Any]) -> None:
        """Update workflow dropdown to reflect current configuration"""
        dropdown = self._workflow_dropdowns.get(config_type)
        if not dropdown:
            return
        
        workflow_name = config_data.get("workflow_name", "")
        workflow_path = config_data.get("workflow_path", "")
        
        self._updating_ui = True
        try:
            # Find and select the workflow
            for i in range(dropdown.count()):
                if dropdown.itemText(i) == workflow_name or dropdown.itemData(i) == workflow_path:
                    dropdown.setCurrentIndex(i)
                    break
        finally:
            self._updating_ui = False
    
    def _update_all_parameter_widgets(self, config_type: str, parameters: Dict[str, Any]) -> None:
        """Update all parameter widgets for a configuration type"""
        if config_type not in self._parameter_widgets:
            return
        
        self._updating_ui = True
        try:
            for param_key, widget in self._parameter_widgets[config_type].items():
                if param_key in parameters:
                    param_data = parameters[param_key]
                    value = param_data.get("current_value", param_data.get("default"))
                    
                    self._update_widget_value(widget, value)
        finally:
            self._updating_ui = False
    
    def _update_widget_value(self, widget: QWidget, value: Any) -> None:
        """Update widget value based on widget type"""
        try:
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
        except Exception as e:
            self.logger.error(f"Error updating widget value: {e}")
    
    def _process_batch_updates(self) -> None:
        """Process batched parameter updates"""
        self._batch_update_timer.stop()
        
        if not self._pending_updates:
            return
        
        self._updating_ui = True
        try:
            for config_type, changes in self._pending_updates.items():
                if config_type in self._parameter_widgets:
                    for param_key, change_data in changes.items():
                        if param_key in self._parameter_widgets[config_type]:
                            widget = self._parameter_widgets[config_type][param_key]
                            value = change_data.get("new_value")
                            
                            self._update_widget_value(widget, value)
            
            self._pending_updates.clear()
            
        finally:
            self._updating_ui = False
    
    def clear_widgets(self, config_type: Optional[str] = None) -> None:
        """Clear registered widgets
        
        Args:
            config_type: Optional config type to clear, or None for all
        """
        if config_type:
            if config_type in self._parameter_widgets:
                self._parameter_widgets[config_type].clear()
        else:
            self._parameter_widgets.clear()
        
        self.logger.debug(f"Cleared widgets for {config_type or 'all'}")
    
    def get_parameter_widgets(self, config_type: str) -> Dict[str, QWidget]:
        """Get all parameter widgets for a configuration type
        
        Args:
            config_type: Type of configuration
            
        Returns:
            Dictionary of parameter widgets
        """
        return self._parameter_widgets.get(config_type, {})