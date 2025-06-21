"""
Unified Configuration Manager for ComfyUI-Cinema4D Bridge

This module implements the multi-mind analysis recommendation for centralizing
all configuration management with layered precedence and validation.

Based on multi-specialist analysis identifying configuration fragmentation
as a critical issue affecting UX, reliability, and maintainability.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from ..utils.advanced_logging import get_logger

logger = get_logger("config_manager")
import shutil
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    auto_fixes: List[str] = field(default_factory=list)


class ConfigLayer(ABC):
    """Abstract base class for configuration layers"""
    
    @abstractmethod
    def has_setting(self, path: str) -> bool:
        """Check if setting exists in this layer"""
        pass
    
    @abstractmethod
    def get_setting(self, path: str, default=None) -> Any:
        """Get setting from this layer"""
        pass
    
    @abstractmethod
    def set_setting(self, path: str, value: Any) -> None:
        """Set setting in this layer"""
        pass
    
    @abstractmethod
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings from this layer"""
        pass


class DefaultConfigLayer(ConfigLayer):
    """Default configuration values - lowest precedence"""
    
    def __init__(self):
        self.defaults = {
            "paths.comfyui_path": "D:/Comfy3D_WinPortable",
            "paths.cinema4d_path": "C:/Program Files/Maxon Cinema 4D 2024",
            "workflows.image_workflow": "generate_images.json",
            "workflows.model_3d_workflow": "generate_3D.json",
            "workflows.default_image_params.resolution": [1024, 1024],
            "workflows.default_image_params.sampling_steps": 20,
            "workflows.default_image_params.cfg_scale": 7.0,
            "mcp.comfyui_server_url": "http://127.0.0.1:8188",
            "mcp.cinema4d_port": 54321,
            "mcp.connection_timeout": 30,
            "ui.theme": "dark",
            "ui.window_size": [1400, 900],
            "ui.console_max_lines": 1000,
            "logging.level": "INFO",
            "logging.file_enabled": True,
            "logging.console_enabled": True,
        }
    
    def has_setting(self, path: str) -> bool:
        return path in self.defaults
    
    def get_setting(self, path: str, default=None) -> Any:
        return self.defaults.get(path, default)
    
    def set_setting(self, path: str, value: Any) -> None:
        # Defaults are read-only
        logger.warning(f"Cannot set default configuration: {path}")
    
    def get_all_settings(self) -> Dict[str, Any]:
        return self.defaults.copy()


class EnvironmentConfigLayer(ConfigLayer):
    """Environment variable configuration layer"""
    
    ENV_MAPPING = {
        "paths.comfyui_path": "COMFYUI_PATH",
        "paths.cinema4d_path": "CINEMA4D_PATH",
        "mcp.comfyui_server_url": "COMFYUI_URL",
        "mcp.cinema4d_port": "CINEMA4D_PORT",
        "logging.level": "LOG_LEVEL",
        "ui.theme": "UI_THEME",
        "debug.enabled": "DEBUG",
    }
    
    def has_setting(self, path: str) -> bool:
        env_var = self.ENV_MAPPING.get(path)
        return env_var and env_var in os.environ
    
    def get_setting(self, path: str, default=None) -> Any:
        env_var = self.ENV_MAPPING.get(path)
        if not env_var or env_var not in os.environ:
            return default
        
        value = os.environ[env_var]
        
        # Type conversion based on setting type
        if path.endswith("_port"):
            try:
                return int(value)
            except ValueError:
                logger.warning(f"Invalid port number in {env_var}: {value}")
                return default
        elif path.endswith("_path"):
            return Path(value)
        elif path == "debug.enabled":
            return value.lower() in ("1", "true", "yes", "on")
        
        return value
    
    def set_setting(self, path: str, value: Any) -> None:
        # Environment variables are read-only from app perspective
        logger.warning(f"Cannot set environment variable from app: {path}")
    
    def get_all_settings(self) -> Dict[str, Any]:
        settings = {}
        for path, env_var in self.ENV_MAPPING.items():
            if env_var in os.environ:
                settings[path] = self.get_setting(path)
        return settings


class UserConfigLayer(ConfigLayer):
    """User configuration stored in JSON files"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "unified_config.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self._settings = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration with backup recovery"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self._settings = json.load(f)
                with logger.context(operation="load_config"):
                    logger.debug(f"Loaded user config: {len(self._settings)} settings")
            else:
                logger.info("No user config file found, using defaults")
                self._settings = {}
        except Exception as e:
            logger.error(f"Failed to load user config: {e}")
            self._attempt_backup_recovery()
    
    def _attempt_backup_recovery(self):
        """Attempt to recover from backup"""
        backup_files = list(self.backup_dir.glob("unified_config_*.json"))
        if backup_files:
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest_backup, 'r') as f:
                    self._settings = json.load(f)
                logger.info(f"Recovered configuration from backup: {latest_backup}")
            except Exception as e:
                logger.error(f"Backup recovery failed: {e}")
                self._settings = {}
        else:
            logger.warning("No backup files found, using empty configuration")
            self._settings = {}
    
    def _save_config(self):
        """Save configuration with atomic write and backup"""
        if not self._settings:
            return
        
        try:
            # Create backup
            if self.config_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"unified_config_{timestamp}.json"
                shutil.copy2(self.config_file, backup_file)
            
            # Atomic write
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self._settings, f, indent=2, default=str)
            temp_file.replace(self.config_file)
            
            logger.debug("User configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save user configuration: {e}")
            raise
    
    def has_setting(self, path: str) -> bool:
        return self._get_nested_value(self._settings, path) is not None
    
    def get_setting(self, path: str, default=None) -> Any:
        value = self._get_nested_value(self._settings, path)
        return value if value is not None else default
    
    def set_setting(self, path: str, value: Any) -> None:
        self._set_nested_value(self._settings, path, value)
        self._save_config()
    
    def get_all_settings(self) -> Dict[str, Any]:
        return self._flatten_dict(self._settings)
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _set_nested_value(self, data: Dict, path: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _flatten_dict(self, data: Dict, prefix: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary to dot notation"""
        result = {}
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten_dict(value, new_key))
            else:
                result[new_key] = value
        return result


class ConfigurationValidator:
    """Validates configuration integrity and provides auto-fixes"""
    
    def __init__(self):
        self.validation_rules = [
            self._validate_paths,
            self._validate_ports,
            self._validate_numeric_ranges,
            self._validate_dependencies,
        ]
    
    def validate(self, config_manager: 'UnifiedConfigurationManager') -> ValidationResult:
        """Run comprehensive validation"""
        result = ValidationResult(is_valid=True)
        
        for rule in self.validation_rules:
            try:
                rule(config_manager, result)
            except Exception as e:
                result.errors.append(f"Validation rule failed: {e}")
                result.is_valid = False
        
        # Overall validation result
        if result.errors:
            result.is_valid = False
        
        return result
    
    def _validate_paths(self, config_manager, result: ValidationResult):
        """Validate path configurations"""
        path_settings = [
            "paths.comfyui_path",
            "paths.cinema4d_path",
        ]
        
        for path_setting in path_settings:
            path_str = config_manager.get_setting(path_setting)
            if path_str:
                path = Path(path_str)
                if not path.exists():
                    result.warnings.append(f"Path does not exist: {path_setting} = {path}")
                    
                    # Auto-fix: Try to detect installation
                    if "comfyui" in path_setting.lower():
                        detected = self._detect_comfyui_path()
                        if detected:
                            result.auto_fixes.append(f"Auto-detected ComfyUI: {detected}")
                            config_manager.set_setting(path_setting, str(detected), layer="user")
    
    def _validate_ports(self, config_manager, result: ValidationResult):
        """Validate port configurations"""
        port_settings = [
            "mcp.comfyui_server_port",
            "mcp.cinema4d_port",
        ]
        
        for port_setting in port_settings:
            port = config_manager.get_setting(port_setting)
            if port:
                try:
                    port_num = int(port)
                    if not (1 <= port_num <= 65535):
                        result.errors.append(f"Invalid port number: {port_setting} = {port}")
                except (ValueError, TypeError):
                    result.errors.append(f"Port must be a number: {port_setting} = {port}")
    
    def _validate_numeric_ranges(self, config_manager, result: ValidationResult):
        """Validate numeric range settings"""
        range_checks = {
            "workflows.default_image_params.sampling_steps": (1, 100),
            "workflows.default_image_params.cfg_scale": (1.0, 20.0),
            "ui.console_max_lines": (100, 10000),
        }
        
        for setting, (min_val, max_val) in range_checks.items():
            value = config_manager.get_setting(setting)
            if value is not None:
                try:
                    num_val = float(value)
                    if not (min_val <= num_val <= max_val):
                        result.warnings.append(
                            f"Value out of recommended range: {setting} = {value} "
                            f"(recommended: {min_val}-{max_val})"
                        )
                except (ValueError, TypeError):
                    result.errors.append(f"Numeric value expected: {setting} = {value}")
    
    def _validate_dependencies(self, config_manager, result: ValidationResult):
        """Validate configuration dependencies"""
        # Example: If 3D preview is enabled, ensure ComfyUI path is valid
        if config_manager.get_setting("ui.enable_3d_preview", False):
            comfyui_path = config_manager.get_setting("paths.comfyui_path")
            if not comfyui_path or not Path(comfyui_path).exists():
                result.warnings.append(
                    "3D preview enabled but ComfyUI path not configured properly"
                )
    
    def _detect_comfyui_path(self) -> Optional[Path]:
        """Auto-detect ComfyUI installation"""
        common_locations = [
            Path("D:/Comfy3D_WinPortable"),
            Path("C:/ComfyUI"),
            Path.home() / "ComfyUI",
            Path("./ComfyUI"),
        ]
        
        for location in common_locations:
            if location.exists() and (location / "main.py").exists():
                return location
        
        return None


class UnifiedConfigurationManager:
    """
    Centralized configuration manager with layered precedence:
    1. Defaults (lowest precedence)
    2. Environment variables
    3. User configuration (highest precedence)
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path("config")
        
        # Initialize layers (order matters - later layers have higher precedence)
        self.layers = [
            DefaultConfigLayer(),
            EnvironmentConfigLayer(),
            UserConfigLayer(config_dir),
        ]
        
        self.validator = ConfigurationValidator()
        
        # Run initial validation
        self._validate_on_startup()
    
    def _validate_on_startup(self):
        """Run validation on startup and apply auto-fixes"""
        result = self.validator.validate(self)
        
        if result.errors:
            for error in result.errors:
                logger.error(f"Configuration error: {error}")
        
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"Configuration warning: {warning}")
        
        if result.auto_fixes:
            for fix in result.auto_fixes:
                logger.info(f"Auto-fix applied: {fix}")
    
    def get_setting(self, path: str, default=None) -> Any:
        """Get setting with layer precedence resolution"""
        for layer in reversed(self.layers):  # Higher precedence layers first
            if layer.has_setting(path):
                value = layer.get_setting(path)
                if value is not None:
                    return value
        return default
    
    def set_setting(self, path: str, value: Any, layer: str = "user") -> None:
        """Set setting in specified layer"""
        target_layer = self._get_layer(layer)
        if target_layer:
            target_layer.set_setting(path, value)
            logger.debug(f"Setting updated: {path} = {value} (layer: {layer})")
        else:
            logger.error(f"Unknown configuration layer: {layer}")
    
    def has_setting(self, path: str) -> bool:
        """Check if setting exists in any layer"""
        for layer in self.layers:
            if layer.has_setting(path):
                return True
        return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings with proper precedence resolution"""
        all_settings = {}
        
        # Apply layers in order (defaults first, user last)
        for layer in self.layers:
            layer_settings = layer.get_all_settings()
            all_settings.update(layer_settings)
        
        return all_settings
    
    def _get_layer(self, layer_name: str) -> Optional[ConfigLayer]:
        """Get layer by name"""
        layer_map = {
            "default": DefaultConfigLayer,
            "environment": EnvironmentConfigLayer,
            "user": UserConfigLayer,
        }
        
        layer_type = layer_map.get(layer_name)
        if not layer_type:
            return None
        
        for layer in self.layers:
            if isinstance(layer, layer_type):
                return layer
        
        return None
    
    def validate_configuration(self) -> ValidationResult:
        """Run configuration validation"""
        return self.validator.validate(self)
    
    def reset_to_defaults(self, confirm: bool = False) -> None:
        """Reset user configuration to defaults"""
        if not confirm:
            logger.warning("Reset requires confirmation")
            return
        
        user_layer = self._get_layer("user")
        if user_layer and hasattr(user_layer, '_settings'):
            user_layer._settings.clear()
            user_layer._save_config()
            logger.info("User configuration reset to defaults")
    
    def export_configuration(self, export_path: Path) -> None:
        """Export current configuration to file"""
        try:
            all_settings = self.get_all_settings()
            with open(export_path, 'w') as f:
                json.dump(all_settings, f, indent=2, default=str)
            logger.info(f"Configuration exported to: {export_path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise
    
    def import_configuration(self, import_path: Path) -> None:
        """Import configuration from file"""
        try:
            with open(import_path, 'r') as f:
                imported_settings = json.load(f)
            
            user_layer = self._get_layer("user")
            if user_layer:
                for path, value in imported_settings.items():
                    user_layer.set_setting(path, value)
                logger.info(f"Configuration imported from: {import_path}")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise


# Backward compatibility interface
class ConfigAdapter:
    """Adapter to maintain backward compatibility with existing config usage"""
    
    def __init__(self, unified_manager: UnifiedConfigurationManager):
        self.unified = unified_manager
    
    @property
    def paths(self):
        return type('paths', (), {
            'comfyui_path': Path(self.unified.get_setting("paths.comfyui_path", "")),
            'cinema4d_path': Path(self.unified.get_setting("paths.cinema4d_path", "")),
        })
    
    @property
    def workflows(self):
        return type('workflows', (), {
            'image_workflow': self.unified.get_setting("workflows.image_workflow"),
            'model_3d_workflow': self.unified.get_setting("workflows.model_3d_workflow"),
            'default_image_params': self.unified.get_setting("workflows.default_image_params", {}),
            'default_3d_params': self.unified.get_setting("workflows.default_3d_params", {}),
        })
    
    @property
    def mcp(self):
        return type('mcp', (), {
            'comfyui_server_url': self.unified.get_setting("mcp.comfyui_server_url"),
            'cinema4d_port': self.unified.get_setting("mcp.cinema4d_port"),
            'connection_timeout': self.unified.get_setting("mcp.connection_timeout"),
        })
    
    @property
    def ui(self):
        return type('ui', (), {
            'theme': self.unified.get_setting("ui.theme"),
            'window_size': self.unified.get_setting("ui.window_size"),
            'console_max_lines': self.unified.get_setting("ui.console_max_lines"),
        })