"""
Configuration Integration Module
Integrates unified configuration management into the existing application
"""

from typing import Dict, Any, Optional
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from loguru import logger

from src.core.unified_configuration_manager import UnifiedConfigurationManager
from src.ui.unified_parameter_panel import UnifiedParameterPanel, CompactParameterPanel
from src.ui.workflow_import_dialog import WorkflowImportDialog
from src.core.workflow_manager import WorkflowManager


class ConfigurationIntegration(QObject):
    """
    Integration layer for unified configuration management
    Handles coordination between UI, configuration manager, and workflow system
    """
    
    # Signals
    configuration_updated = Signal(dict)
    workflow_changed = Signal(str)
    
    def __init__(self, workflow_manager: WorkflowManager):
        super().__init__()
        self.workflow_manager = workflow_manager
        self.config_manager = UnifiedConfigurationManager()
        self._parameter_panels: Dict[str, UnifiedParameterPanel] = {}
        
        # Connect signals
        self.config_manager.parameters_updated.connect(self._on_parameters_updated)
        self.config_manager.workflow_loaded.connect(self._on_workflow_loaded)
    
    def create_parameter_panel(self, tab_name: str, compact: bool = False) -> UnifiedParameterPanel:
        """
        Create a unified parameter panel for a specific tab
        Ensures all tabs use the same configuration source
        """
        if compact:
            panel = CompactParameterPanel(self.config_manager)
        else:
            panel = UnifiedParameterPanel(self.config_manager)
        
        # Store reference
        self._parameter_panels[tab_name] = panel
        
        # Connect parameter changes
        panel.parameter_changed.connect(self._on_ui_parameter_changed)
        
        logger.info(f"Created unified parameter panel for {tab_name} (compact={compact})")
        return panel
    
    def show_import_dialog(self, parent=None) -> Optional[Dict[str, Any]]:
        """
        Show the workflow import dialog
        Returns selected configuration or None if cancelled
        """
        dialog = WorkflowImportDialog(parent)
        
        if dialog.exec():
            config = dialog.get_selected_parameters()
            self.configuration_updated.emit(config)
            return config
        
        return None
    
    def load_workflow_from_dropdown(self, workflow_name: str) -> bool:
        """
        Load workflow configuration when dropdown selection changes
        Ensures dropdown changes trigger full parameter reload
        """
        try:
            workflow_path = Path("workflows") / workflow_name
            if not workflow_path.exists():
                logger.error(f"Workflow file not found: {workflow_path}")
                return False
            
            # Load configuration through unified manager
            config = self.config_manager.load_workflow_configuration(workflow_path)
            
            if config:
                logger.info(f"Loaded workflow configuration from dropdown: {workflow_name}")
                # Emit signals to trigger UI updates
                self.configuration_updated.emit(config)
                self.workflow_changed.emit(workflow_name)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to load workflow from dropdown: {e}")
            return False
    
    def inject_parameters_for_execution(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject current parameter values into workflow for execution
        Maintains minimal conversion to avoid breaking workflows
        """
        try:
            # Get all current parameter values
            all_params = self.config_manager.get_all_parameters()
            
            # Convert to flat parameter dict for injection
            flat_params = {}
            
            for node_type, section in all_params.items():
                params = section.get("parameters", {})
                for param_name, param_data in params.items():
                    # Use current value or default
                    value = param_data.get("current_value", param_data.get("default"))
                    if value is not None:
                        # Map to expected parameter names
                        if node_type == "CLIPTextEncode" and param_name == "text":
                            # Handle positive/negative prompts specially
                            node_id = section.get("node_id", "")
                            if node_id == "12":  # Positive prompt
                                flat_params["positive_prompt"] = value
                            elif node_id == "13":  # Negative prompt
                                flat_params["negative_prompt"] = value
                        else:
                            # Use simple parameter name for injection
                            flat_params[param_name] = value
            
            # Use existing workflow manager injection (minimal conversion)
            return self.workflow_manager.inject_parameters_comfyui(workflow, flat_params)
            
        except Exception as e:
            logger.error(f"Failed to inject parameters: {e}")
            return workflow
    
    def get_current_workflow_name(self) -> Optional[str]:
        """Get the name of the currently loaded workflow"""
        return self.config_manager._current_workflow
    
    def handle_prompt_memory(self, prompt_type: str, new_value: str) -> str:
        """
        Handle prompt memory management
        Returns the value that should be used (user override or file value)
        """
        param_key = f"positive_prompt" if prompt_type == "positive" else "negative_prompt"
        
        # Check if user has modified this prompt
        if param_key in self.config_manager._user_overrides:
            # User modification takes precedence
            return self.config_manager._user_overrides[param_key]
        
        # Otherwise use the new value and save as override
        self.config_manager._user_overrides[param_key] = new_value
        return new_value
    
    def clear_prompt_overrides(self):
        """Clear prompt overrides when explicitly reloading workflow"""
        self.config_manager._user_overrides.pop("positive_prompt", None)
        self.config_manager._user_overrides.pop("negative_prompt", None)
    
    def _on_parameters_updated(self, parameters: Dict[str, Any]):
        """Handle parameter updates from configuration manager"""
        self.configuration_updated.emit(parameters)
    
    def _on_workflow_loaded(self, workflow_name: str):
        """Handle workflow load events"""
        self.workflow_changed.emit(workflow_name)
    
    def _on_ui_parameter_changed(self, param_key: str, value: Any):
        """Handle parameter changes from UI"""
        # Configuration manager already updated by the panel
        # This is for any additional handling needed
        logger.debug(f"UI parameter changed: {param_key} = {value}")
    
    def export_current_configuration(self, filepath: Path) -> bool:
        """Export current configuration to file"""
        return self.config_manager.export_configuration(filepath)
    
    def import_configuration_file(self, filepath: Path) -> bool:
        """Import configuration from file"""
        return self.config_manager.import_configuration(filepath)