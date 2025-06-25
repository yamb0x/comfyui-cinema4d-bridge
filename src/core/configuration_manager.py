"""
Unified Configuration Manager for ComfyUI to Cinema4D Bridge
Centralized configuration management with observer pattern for consistency
"""

import json
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from copy import deepcopy
from loguru import logger

from src.core.workflow_parameter_extractor import WorkflowParameterExtractor
from src.core.parameter_rules_engine import ParameterRulesEngine
from src.utils.logger import LoggerMixin


class ConfigurationObserver(ABC):
    """Abstract base class for configuration change observers"""
    
    @abstractmethod
    def on_configuration_changed(self, config_type: str, changes: Dict[str, Any]) -> None:
        """Handle configuration changes
        
        Args:
            config_type: Type of configuration that changed (e.g., 'image', '3d', 'texture')
            changes: Dictionary of changes with old and new values
        """
        pass
    
    @abstractmethod
    def on_configuration_loaded(self, config_type: str, config_data: Dict[str, Any]) -> None:
        """Handle configuration loaded event
        
        Args:
            config_type: Type of configuration loaded
            config_data: Complete configuration data
        """
        pass
    
    @abstractmethod
    def on_configuration_error(self, config_type: str, error: Exception) -> None:
        """Handle configuration error
        
        Args:
            config_type: Type of configuration that had error
            error: The exception that occurred
        """
        pass


class ConfigurationManager(LoggerMixin):
    """Centralized configuration management with observer pattern"""
    
    # Configuration types
    CONFIG_TYPE_IMAGE = "image"
    CONFIG_TYPE_3D = "3d_generation"
    CONFIG_TYPE_TEXTURE = "texture_generation"
    CONFIG_TYPE_WORKFLOW = "workflow"
    
    # Configuration file mappings
    CONFIG_FILES = {
        CONFIG_TYPE_IMAGE: "image_parameters_config.json",
        CONFIG_TYPE_3D: "3d_parameters_config.json",
        CONFIG_TYPE_TEXTURE: "texture_parameters_config.json"
    }
    
    def __init__(self, config_dir: Path):
        """Initialize configuration manager
        
        Args:
            config_dir: Base directory for configuration files
        """
        super().__init__()
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Observers
        self._observers: List[ConfigurationObserver] = []
        
        # Configuration storage
        self._configurations: Dict[str, Dict[str, Any]] = {}
        self._parameter_cache: Dict[str, Dict[str, Any]] = {}
        self._workflow_cache: Dict[str, Dict[str, Any]] = {}
        
        # State tracking
        self._loaded_workflows: Dict[str, str] = {}  # config_type -> workflow_path
        self._user_overrides: Dict[str, Dict[str, Any]] = {}  # User parameter overrides
        
        # Components
        self.parameter_extractor = WorkflowParameterExtractor()
        self.rules_engine = ParameterRulesEngine()
        
        # Load any existing configurations
        self._load_existing_configurations()
        
        self.logger.info("ConfigurationManager initialized")
    
    def register_observer(self, observer: ConfigurationObserver) -> None:
        """Register a configuration change observer
        
        Args:
            observer: Observer instance to register
        """
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
                self.logger.debug(f"Registered observer: {observer.__class__.__name__}")
                
                # Notify observer of current configurations
                for config_type, config_data in self._configurations.items():
                    try:
                        observer.on_configuration_loaded(config_type, config_data)
                    except Exception as e:
                        self.logger.error(f"Error notifying observer of existing config: {e}")
    
    def unregister_observer(self, observer: ConfigurationObserver) -> None:
        """Unregister a configuration change observer
        
        Args:
            observer: Observer instance to unregister
        """
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
                self.logger.debug(f"Unregistered observer: {observer.__class__.__name__}")
    
    def load_configuration(self, config_type: str, workflow_path: Optional[Path] = None) -> bool:
        """Load configuration from file
        
        Args:
            config_type: Type of configuration to load
            workflow_path: Optional workflow path to load parameters from
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Load saved configuration if exists
                config_file = self.config_dir / self.CONFIG_FILES.get(config_type, f"{config_type}_config.json")
                
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        saved_config = json.load(f)
                    
                    self._configurations[config_type] = saved_config
                    self.logger.info(f"Loaded saved configuration for {config_type}")
                    
                    # If workflow path in saved config, use it
                    if not workflow_path and "workflow_path" in saved_config:
                        workflow_path = Path(saved_config["workflow_path"])
                
                # Load workflow parameters if path provided
                if workflow_path and workflow_path.exists():
                    parameters = self.parameter_extractor.extract_parameters(workflow_path)
                    
                    # Apply rules engine for organization
                    organized_params = self.rules_engine.organize_parameters(parameters)
                    
                    # Update configuration
                    if config_type not in self._configurations:
                        self._configurations[config_type] = {}
                    
                    self._configurations[config_type].update({
                        "workflow_path": str(workflow_path),
                        "workflow_name": workflow_path.name,
                        "parameters": organized_params,
                        "last_updated": datetime.now().isoformat()
                    })
                    
                    # Cache parameters
                    self._parameter_cache[config_type] = organized_params
                    self._loaded_workflows[config_type] = str(workflow_path)
                    
                    self.logger.info(f"Loaded workflow parameters for {config_type} from {workflow_path.name}")
                    
                    # Save configuration
                    self._save_configuration(config_type)
                
                # Notify observers
                self._notify_configuration_loaded(config_type, self._configurations.get(config_type, {}))
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to load configuration for {config_type}: {e}")
                self._notify_configuration_error(config_type, e)
                return False
    
    def get_configuration(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Get complete configuration for a type
        
        Args:
            config_type: Type of configuration to get
            
        Returns:
            Configuration dictionary or None if not loaded
        """
        with self._lock:
            return deepcopy(self._configurations.get(config_type))
    
    def get_parameters(self, config_type: str, filtered: bool = True) -> Dict[str, Any]:
        """Get parameters for a configuration type
        
        Args:
            config_type: Type of configuration
            filtered: Whether to apply visibility filtering
            
        Returns:
            Dictionary of parameters
        """
        with self._lock:
            # Get from cache first
            if config_type in self._parameter_cache:
                params = deepcopy(self._parameter_cache[config_type])
            else:
                # Extract from configuration
                config = self._configurations.get(config_type, {})
                params = config.get("parameters", {})
            
            # Apply user overrides
            if config_type in self._user_overrides:
                for param_key, value in self._user_overrides[config_type].items():
                    if param_key in params:
                        params[param_key]["current_value"] = value
            
            # Apply filtering if requested
            if filtered:
                params = self.rules_engine.filter_visible_parameters(params)
            
            return params
    
    def update_parameter(self, config_type: str, param_key: str, value: Any, is_user_override: bool = True) -> bool:
        """Update a single parameter value
        
        Args:
            config_type: Type of configuration
            param_key: Parameter key to update
            value: New value
            is_user_override: Whether this is a user override
            
        Returns:
            True if successful
        """
        with self._lock:
            try:
                # Get current parameters
                params = self.get_parameters(config_type, filtered=False)
                
                if param_key not in params:
                    self.logger.warning(f"Parameter {param_key} not found in {config_type}")
                    return False
                
                # Store old value for change notification
                old_value = params[param_key].get("current_value", params[param_key].get("default"))
                
                # Update parameter
                if config_type not in self._parameter_cache:
                    self._parameter_cache[config_type] = params
                
                self._parameter_cache[config_type][param_key]["current_value"] = value
                
                # Store user override if applicable
                if is_user_override:
                    if config_type not in self._user_overrides:
                        self._user_overrides[config_type] = {}
                    self._user_overrides[config_type][param_key] = value
                
                # Update configuration
                if config_type in self._configurations:
                    if "parameters" not in self._configurations[config_type]:
                        self._configurations[config_type]["parameters"] = {}
                    self._configurations[config_type]["parameters"][param_key] = self._parameter_cache[config_type][param_key]
                
                # Notify observers of change
                changes = {
                    param_key: {
                        "old_value": old_value,
                        "new_value": value,
                        "is_user_override": is_user_override
                    }
                }
                self._notify_configuration_changed(config_type, changes)
                
                # Save if not a temporary change
                if not is_user_override or self._should_persist_user_overrides():
                    self._save_configuration(config_type)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to update parameter {param_key} in {config_type}: {e}")
                return False
    
    def update_parameters_batch(self, config_type: str, updates: Dict[str, Any], is_user_override: bool = True) -> bool:
        """Update multiple parameters at once (transactional)
        
        Args:
            config_type: Type of configuration
            updates: Dictionary of parameter updates
            is_user_override: Whether these are user overrides
            
        Returns:
            True if all updates successful
        """
        with self._lock:
            try:
                # Collect all changes
                all_changes = {}
                
                # Validate all updates first
                params = self.get_parameters(config_type, filtered=False)
                for param_key in updates:
                    if param_key not in params:
                        self.logger.error(f"Parameter {param_key} not found in {config_type}")
                        return False
                
                # Apply all updates
                for param_key, value in updates.items():
                    old_value = params[param_key].get("current_value", params[param_key].get("default"))
                    
                    # Update cache
                    if config_type not in self._parameter_cache:
                        self._parameter_cache[config_type] = params
                    
                    self._parameter_cache[config_type][param_key]["current_value"] = value
                    
                    # Store user override
                    if is_user_override:
                        if config_type not in self._user_overrides:
                            self._user_overrides[config_type] = {}
                        self._user_overrides[config_type][param_key] = value
                    
                    # Track change
                    all_changes[param_key] = {
                        "old_value": old_value,
                        "new_value": value,
                        "is_user_override": is_user_override
                    }
                
                # Update configuration
                if config_type in self._configurations:
                    if "parameters" not in self._configurations[config_type]:
                        self._configurations[config_type]["parameters"] = {}
                    
                    for param_key in updates:
                        self._configurations[config_type]["parameters"][param_key] = self._parameter_cache[config_type][param_key]
                
                # Notify observers of all changes at once
                self._notify_configuration_changed(config_type, all_changes)
                
                # Save configuration
                self._save_configuration(config_type)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to batch update parameters in {config_type}: {e}")
                return False
    
    def reset_user_overrides(self, config_type: str) -> None:
        """Reset all user overrides for a configuration type
        
        Args:
            config_type: Type of configuration to reset
        """
        with self._lock:
            if config_type in self._user_overrides:
                del self._user_overrides[config_type]
                self.logger.info(f"Reset user overrides for {config_type}")
                
                # Reload parameters from saved configuration
                self.load_configuration(config_type)
    
    def get_workflow_path(self, config_type: str) -> Optional[Path]:
        """Get the workflow path for a configuration type
        
        Args:
            config_type: Type of configuration
            
        Returns:
            Path to workflow file or None
        """
        with self._lock:
            workflow_path = self._loaded_workflows.get(config_type)
            return Path(workflow_path) if workflow_path else None
    
    def export_configuration(self, config_type: str, export_path: Path) -> bool:
        """Export configuration to file
        
        Args:
            config_type: Type of configuration to export
            export_path: Path to export to
            
        Returns:
            True if successful
        """
        with self._lock:
            try:
                config = self.get_configuration(config_type)
                if not config:
                    self.logger.error(f"No configuration found for {config_type}")
                    return False
                
                # Add export metadata
                config["exported_at"] = datetime.now().isoformat()
                config["exported_by"] = "ConfigurationManager"
                
                # Write to file
                with open(export_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                self.logger.info(f"Exported {config_type} configuration to {export_path}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to export configuration: {e}")
                return False
    
    def import_configuration(self, config_type: str, import_path: Path) -> bool:
        """Import configuration from file
        
        Args:
            config_type: Type of configuration to import
            import_path: Path to import from
            
        Returns:
            True if successful
        """
        with self._lock:
            try:
                with open(import_path, 'r') as f:
                    config_data = json.load(f)
                
                # Validate configuration structure
                if "parameters" not in config_data:
                    self.logger.error("Invalid configuration file: missing parameters")
                    return False
                
                # Update configuration
                self._configurations[config_type] = config_data
                self._parameter_cache[config_type] = config_data["parameters"]
                
                if "workflow_path" in config_data:
                    self._loaded_workflows[config_type] = config_data["workflow_path"]
                
                # Save to standard location
                self._save_configuration(config_type)
                
                # Notify observers
                self._notify_configuration_loaded(config_type, config_data)
                
                self.logger.info(f"Imported {config_type} configuration from {import_path}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to import configuration: {e}")
                self._notify_configuration_error(config_type, e)
                return False
    
    # Private methods
    
    def _load_existing_configurations(self) -> None:
        """Load any existing configuration files on startup"""
        for config_type, filename in self.CONFIG_FILES.items():
            config_file = self.config_dir / filename
            if config_file.exists():
                try:
                    self.load_configuration(config_type)
                    self.logger.info(f"Loaded existing configuration for {config_type}")
                except Exception as e:
                    self.logger.error(f"Failed to load existing config for {config_type}: {e}")
    
    def _save_configuration(self, config_type: str) -> bool:
        """Save configuration to file
        
        Args:
            config_type: Type of configuration to save
            
        Returns:
            True if successful
        """
        try:
            config_file = self.config_dir / self.CONFIG_FILES.get(config_type, f"{config_type}_config.json")
            config_data = self._configurations.get(config_type, {})
            
            # Add metadata
            config_data["last_saved"] = datetime.now().isoformat()
            
            # Write to file
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.debug(f"Saved configuration for {config_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration for {config_type}: {e}")
            return False
    
    def _should_persist_user_overrides(self) -> bool:
        """Check if user overrides should be persisted
        
        Returns:
            True if overrides should be saved
        """
        # TODO: Make this configurable via settings
        return True
    
    def _notify_configuration_changed(self, config_type: str, changes: Dict[str, Any]) -> None:
        """Notify all observers of configuration changes"""
        for observer in self._observers:
            try:
                observer.on_configuration_changed(config_type, changes)
            except Exception as e:
                self.logger.error(f"Error notifying observer {observer.__class__.__name__}: {e}")
    
    def _notify_configuration_loaded(self, config_type: str, config_data: Dict[str, Any]) -> None:
        """Notify all observers of configuration loaded"""
        for observer in self._observers:
            try:
                observer.on_configuration_loaded(config_type, config_data)
            except Exception as e:
                self.logger.error(f"Error notifying observer {observer.__class__.__name__}: {e}")
    
    def _notify_configuration_error(self, config_type: str, error: Exception) -> None:
        """Notify all observers of configuration error"""
        for observer in self._observers:
            try:
                observer.on_configuration_error(config_type, error)
            except Exception as e:
                self.logger.error(f"Error notifying observer {observer.__class__.__name__}: {e}")


# Singleton instance getter
_instance = None
_lock = threading.Lock()

def get_configuration_manager(config_dir: Path) -> ConfigurationManager:
    """Get or create the singleton ConfigurationManager instance
    
    Args:
        config_dir: Configuration directory path
        
    Returns:
        ConfigurationManager instance
    """
    global _instance
    with _lock:
        if _instance is None:
            _instance = ConfigurationManager(config_dir)
        return _instance