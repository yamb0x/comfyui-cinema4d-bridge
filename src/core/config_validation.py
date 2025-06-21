"""
Configuration Validation Pipeline

Advanced validation system for configuration integrity, dependencies,
and automatic issue resolution. Implements the multi-mind analysis
recommendation for configuration reliability improvements.
"""

import json
import socket
import subprocess
import psutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse
import requests
from ..utils.advanced_logging import get_logger

logger = get_logger("config_validation")


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue"""
    level: str  # "error", "warning", "info"
    category: str  # "path", "network", "dependency", "format", "security"
    setting_path: str
    message: str
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    fix_action: Optional[str] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    auto_fixes_applied: List[str] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate summary statistics"""
        self.summary = {
            "total_issues": len(self.issues),
            "errors": len([i for i in self.issues if i.level == "error"]),
            "warnings": len([i for i in self.issues if i.level == "warning"]),
            "auto_fixable": len([i for i in self.issues if i.auto_fixable]),
        }
        
        # Overall validity
        self.is_valid = self.summary["errors"] == 0


class ValidationRule(ABC):
    """Abstract base class for validation rules"""
    
    @abstractmethod
    def validate(self, config_manager, report: ValidationReport) -> None:
        """Run validation and add issues to report"""
        pass
    
    @abstractmethod
    def get_rule_name(self) -> str:
        """Get human-readable rule name"""
        pass


class PathValidationRule(ValidationRule):
    """Validates path configurations"""
    
    def get_rule_name(self) -> str:
        return "Path Validation"
    
    def validate(self, config_manager, report: ValidationReport) -> None:
        """Validate all path settings"""
        path_settings = {
            "paths.comfyui_path": {
                "required_files": ["main.py", "server.py"],
                "description": "ComfyUI installation directory",
            },
            "paths.cinema4d_path": {
                "required_files": ["Cinema 4D.exe", "c4d.exe"],
                "description": "Cinema4D installation directory",
            },
        }
        
        for setting_path, requirements in path_settings.items():
            path_str = config_manager.get_setting(setting_path)
            
            if not path_str:
                report.issues.append(ValidationIssue(
                    level="error",
                    category="path",
                    setting_path=setting_path,
                    message=f"Path not configured: {requirements['description']}",
                    suggested_fix="Configure path in settings or set environment variable",
                    auto_fixable=True,
                    fix_action="auto_detect"
                ))
                continue
            
            path = Path(path_str)
            
            # Check if path exists
            if not path.exists():
                auto_detected = self._auto_detect_path(setting_path)
                
                report.issues.append(ValidationIssue(
                    level="error" if not auto_detected else "warning",
                    category="path",
                    setting_path=setting_path,
                    message=f"Path does not exist: {path}",
                    suggested_fix=f"Auto-detected: {auto_detected}" if auto_detected else "Update path in settings",
                    auto_fixable=bool(auto_detected),
                    fix_action=f"set_path:{auto_detected}" if auto_detected else None
                ))
                
                if auto_detected:
                    config_manager.set_setting(setting_path, str(auto_detected))
                    report.auto_fixes_applied.append(f"Auto-detected {setting_path}: {auto_detected}")
                continue
            
            # Check if required files exist
            missing_files = []
            for required_file in requirements["required_files"]:
                if not (path / required_file).exists():
                    missing_files.append(required_file)
            
            if missing_files:
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="path",
                    setting_path=setting_path,
                    message=f"Missing expected files in {path}: {', '.join(missing_files)}",
                    suggested_fix="Verify installation is complete and functional"
                ))
    
    def _auto_detect_path(self, setting_path: str) -> Optional[Path]:
        """Auto-detect installation paths"""
        if "comfyui" in setting_path.lower():
            return self._detect_comfyui()
        elif "cinema4d" in setting_path.lower():
            return self._detect_cinema4d()
        return None
    
    def _detect_comfyui(self) -> Optional[Path]:
        """Auto-detect ComfyUI installation"""
        search_locations = [
            Path("D:/Comfy3D_WinPortable"),
            Path("C:/ComfyUI"),
            Path.home() / "ComfyUI",
            Path("./ComfyUI"),
            Path("../ComfyUI"),
        ]
        
        for location in search_locations:
            if location.exists() and (location / "main.py").exists():
                logger.info(f"Auto-detected ComfyUI at: {location}")
                return location
        
        return None
    
    def _detect_cinema4d(self) -> Optional[Path]:
        """Auto-detect Cinema4D installation"""
        search_locations = [
            Path("C:/Program Files/Maxon Cinema 4D 2024"),
            Path("C:/Program Files/Maxon Cinema 4D 2023"),
            Path("C:/Program Files/MAXON/Cinema 4D R25"),
            Path("C:/Program Files/MAXON/Cinema 4D R24"),
        ]
        
        for location in search_locations:
            if location.exists():
                # Look for Cinema4D executable
                for exe_name in ["Cinema 4D.exe", "c4d.exe"]:
                    if (location / exe_name).exists():
                        logger.info(f"Auto-detected Cinema4D at: {location}")
                        return location
        
        return None


class NetworkValidationRule(ValidationRule):
    """Validates network and service configurations"""
    
    def get_rule_name(self) -> str:
        return "Network & Service Validation"
    
    def validate(self, config_manager, report: ValidationReport) -> None:
        """Validate network configurations"""
        # Validate ComfyUI server URL
        comfyui_url = config_manager.get_setting("mcp.comfyui_server_url")
        if comfyui_url:
            self._validate_http_endpoint(
                comfyui_url, "mcp.comfyui_server_url", 
                "ComfyUI API server", report
            )
        
        # Validate Cinema4D port
        c4d_port = config_manager.get_setting("mcp.cinema4d_port")
        if c4d_port:
            self._validate_port_accessibility(
                c4d_port, "mcp.cinema4d_port",
                "Cinema4D command port", report
            )
    
    def _validate_http_endpoint(self, url: str, setting_path: str, 
                              description: str, report: ValidationReport) -> None:
        """Validate HTTP endpoint accessibility"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                report.issues.append(ValidationIssue(
                    level="error",
                    category="network",
                    setting_path=setting_path,
                    message=f"Invalid URL format: {url}",
                    suggested_fix="Use format: http://host:port"
                ))
                return
            
            # Test connectivity with timeout
            response = requests.get(f"{url}/system_stats", timeout=5)
            if response.status_code == 200:
                logger.debug(f"{description} is accessible at {url}")
            else:
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="network",
                    setting_path=setting_path,
                    message=f"{description} returned status {response.status_code}",
                    suggested_fix="Check if service is running and properly configured"
                ))
                
        except requests.ConnectionError:
            report.issues.append(ValidationIssue(
                level="warning",
                category="network",
                setting_path=setting_path,
                message=f"Cannot connect to {description} at {url}",
                suggested_fix="Start the service or check network configuration"
            ))
        except requests.Timeout:
            report.issues.append(ValidationIssue(
                level="warning",
                category="network",
                setting_path=setting_path,
                message=f"Timeout connecting to {description}",
                suggested_fix="Check service responsiveness or increase timeout"
            ))
        except Exception as e:
            report.issues.append(ValidationIssue(
                level="error",
                category="network",
                setting_path=setting_path,
                message=f"Network validation error: {e}",
                suggested_fix="Check URL format and network connectivity"
            ))
    
    def _validate_port_accessibility(self, port: int, setting_path: str,
                                   description: str, report: ValidationReport) -> None:
        """Validate port accessibility"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', port))
                
                if result == 0:
                    logger.debug(f"{description} is accessible on port {port}")
                else:
                    report.issues.append(ValidationIssue(
                        level="warning",
                        category="network",
                        setting_path=setting_path,
                        message=f"{description} not accessible on port {port}",
                        suggested_fix="Start the service or check port configuration"
                    ))
        except Exception as e:
            report.issues.append(ValidationIssue(
                level="error",
                category="network",
                setting_path=setting_path,
                message=f"Port validation error: {e}",
                suggested_fix="Check port number and system configuration"
            ))


class DependencyValidationRule(ValidationRule):
    """Validates configuration dependencies and consistency"""
    
    def get_rule_name(self) -> str:
        return "Dependency & Consistency Validation"
    
    def validate(self, config_manager, report: ValidationReport) -> None:
        """Validate configuration dependencies"""
        # Check if 3D features require ComfyUI path
        if config_manager.get_setting("ui.enable_3d_preview", False):
            comfyui_path = config_manager.get_setting("paths.comfyui_path")
            if not comfyui_path or not Path(comfyui_path).exists():
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="dependency",
                    setting_path="ui.enable_3d_preview",
                    message="3D preview enabled but ComfyUI path not configured",
                    suggested_fix="Configure ComfyUI path or disable 3D preview"
                ))
        
        # Check workflow file dependencies
        workflows_dir = config_manager.get_setting("base.workflows_dir")
        if workflows_dir:
            workflows_path = Path(workflows_dir)
            
            for workflow_setting in ["workflows.image_workflow", "workflows.model_3d_workflow"]:
                workflow_file = config_manager.get_setting(workflow_setting)
                if workflow_file:
                    full_path = workflows_path / workflow_file
                    if not full_path.exists():
                        report.issues.append(ValidationIssue(
                            level="error",
                            category="dependency",
                            setting_path=workflow_setting,
                            message=f"Workflow file not found: {full_path}",
                            suggested_fix="Check workflow file path or create missing workflow"
                        ))
        
        # Validate parameter ranges are consistent
        self._validate_parameter_consistency(config_manager, report)
    
    def _validate_parameter_consistency(self, config_manager, report: ValidationReport) -> None:
        """Validate parameter value consistency"""
        # Check image resolution consistency
        resolution = config_manager.get_setting("workflows.default_image_params.resolution")
        if resolution and isinstance(resolution, list) and len(resolution) == 2:
            width, height = resolution
            if width <= 0 or height <= 0:
                report.issues.append(ValidationIssue(
                    level="error",
                    category="dependency",
                    setting_path="workflows.default_image_params.resolution",
                    message=f"Invalid resolution values: {width}x{height}",
                    suggested_fix="Use positive resolution values (e.g., [1024, 1024])"
                ))
            elif width > 4096 or height > 4096:
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="dependency",
                    setting_path="workflows.default_image_params.resolution",
                    message=f"Very high resolution may cause memory issues: {width}x{height}",
                    suggested_fix="Consider using smaller resolution for better performance"
                ))


class FormatValidationRule(ValidationRule):
    """Validates configuration format and data types"""
    
    def get_rule_name(self) -> str:
        return "Format & Type Validation"
    
    def validate(self, config_manager, report: ValidationReport) -> None:
        """Validate configuration formats and types"""
        format_rules = {
            "mcp.comfyui_server_url": self._validate_url_format,
            "mcp.cinema4d_port": self._validate_port_format,
            "mcp.connection_timeout": self._validate_positive_number,
            "ui.window_size": self._validate_window_size,
            "workflows.default_image_params.resolution": self._validate_resolution,
            "workflows.default_image_params.cfg_scale": self._validate_cfg_scale,
        }
        
        for setting_path, validator_func in format_rules.items():
            value = config_manager.get_setting(setting_path)
            if value is not None:
                try:
                    validator_func(value, setting_path, report)
                except Exception as e:
                    report.issues.append(ValidationIssue(
                        level="error",
                        category="format",
                        setting_path=setting_path,
                        message=f"Format validation error: {e}",
                        suggested_fix="Check value format and type"
                    ))
    
    def _validate_url_format(self, value: str, setting_path: str, report: ValidationReport):
        """Validate URL format"""
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Invalid URL format: {value}",
                suggested_fix="Use format: http://host:port or https://host:port"
            ))
    
    def _validate_port_format(self, value: Any, setting_path: str, report: ValidationReport):
        """Validate port number format"""
        try:
            port = int(value)
            if not (1 <= port <= 65535):
                report.issues.append(ValidationIssue(
                    level="error",
                    category="format",
                    setting_path=setting_path,
                    message=f"Port number out of range: {port}",
                    suggested_fix="Use port number between 1 and 65535"
                ))
        except (ValueError, TypeError):
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Invalid port number format: {value}",
                suggested_fix="Use numeric port number"
            ))
    
    def _validate_positive_number(self, value: Any, setting_path: str, report: ValidationReport):
        """Validate positive number"""
        try:
            num = float(value)
            if num <= 0:
                report.issues.append(ValidationIssue(
                    level="error",
                    category="format",
                    setting_path=setting_path,
                    message=f"Value must be positive: {value}",
                    suggested_fix="Use positive number"
                ))
        except (ValueError, TypeError):
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Invalid number format: {value}",
                suggested_fix="Use numeric value"
            ))
    
    def _validate_window_size(self, value: Any, setting_path: str, report: ValidationReport):
        """Validate window size format"""
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Window size must be [width, height]: {value}",
                suggested_fix="Use format: [1400, 900]"
            ))
            return
        
        try:
            width, height = int(value[0]), int(value[1])
            if width < 800 or height < 600:
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="format",
                    setting_path=setting_path,
                    message=f"Window size may be too small: {width}x{height}",
                    suggested_fix="Consider minimum size of 800x600"
                ))
        except (ValueError, TypeError):
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Invalid window size values: {value}",
                suggested_fix="Use numeric values for width and height"
            ))
    
    def _validate_resolution(self, value: Any, setting_path: str, report: ValidationReport):
        """Validate image resolution format"""
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Resolution must be [width, height]: {value}",
                suggested_fix="Use format: [1024, 1024]"
            ))
            return
        
        try:
            width, height = int(value[0]), int(value[1])
            if width <= 0 or height <= 0:
                report.issues.append(ValidationIssue(
                    level="error",
                    category="format",
                    setting_path=setting_path,
                    message=f"Resolution values must be positive: {width}x{height}",
                    suggested_fix="Use positive values for width and height"
                ))
            elif width % 8 != 0 or height % 8 != 0:
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="format",
                    setting_path=setting_path,
                    message=f"Resolution should be divisible by 8: {width}x{height}",
                    suggested_fix="Use resolution divisible by 8 for better compatibility"
                ))
        except (ValueError, TypeError):
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Invalid resolution values: {value}",
                suggested_fix="Use numeric values for width and height"
            ))
    
    def _validate_cfg_scale(self, value: Any, setting_path: str, report: ValidationReport):
        """Validate CFG scale value"""
        try:
            cfg = float(value)
            if not (1.0 <= cfg <= 20.0):
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="format",
                    setting_path=setting_path,
                    message=f"CFG scale outside recommended range: {cfg}",
                    suggested_fix="Use CFG scale between 1.0 and 20.0"
                ))
        except (ValueError, TypeError):
            report.issues.append(ValidationIssue(
                level="error",
                category="format",
                setting_path=setting_path,
                message=f"Invalid CFG scale format: {value}",
                suggested_fix="Use numeric value for CFG scale"
            ))


class SecurityValidationRule(ValidationRule):
    """Validates security-related configuration aspects"""
    
    def get_rule_name(self) -> str:
        return "Security Validation"
    
    def validate(self, config_manager, report: ValidationReport) -> None:
        """Validate security configurations"""
        # Check for insecure URLs
        urls_to_check = [
            "mcp.comfyui_server_url",
            "mcp.comfyui_websocket_url",
        ]
        
        for url_setting in urls_to_check:
            url = config_manager.get_setting(url_setting)
            if url and url.startswith("http://") and not self._is_local_url(url):
                report.issues.append(ValidationIssue(
                    level="warning",
                    category="security",
                    setting_path=url_setting,
                    message=f"Insecure HTTP connection to external host: {url}",
                    suggested_fix="Use HTTPS for external connections"
                ))
        
        # Check for overly permissive settings
        if config_manager.get_setting("logging.level") == "DEBUG":
            report.issues.append(ValidationIssue(
                level="info",
                category="security",
                setting_path="logging.level",
                message="Debug logging enabled - may expose sensitive information",
                suggested_fix="Use INFO or WARNING level in production"
            ))
    
    def _is_local_url(self, url: str) -> bool:
        """Check if URL points to local/localhost"""
        parsed = urlparse(url)
        local_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
        return parsed.hostname in local_hosts


class ConfigurationValidationPipeline:
    """
    Comprehensive configuration validation pipeline
    
    Implements the multi-mind analysis recommendation for configuration
    validation to prevent startup failures and improve system reliability.
    """
    
    def __init__(self):
        self.rules = [
            PathValidationRule(),
            NetworkValidationRule(),
            DependencyValidationRule(),
            FormatValidationRule(),
            SecurityValidationRule(),
        ]
    
    def validate(self, config_manager, auto_fix: bool = False) -> ValidationReport:
        """Run comprehensive validation pipeline"""
        report = ValidationReport(is_valid=True)
        
        logger.info("Starting configuration validation pipeline")
        
        for rule in self.rules:
            try:
                logger.debug(f"Running validation rule: {rule.get_rule_name()}")
                rule.validate(config_manager, report)
            except Exception as e:
                logger.error(f"Validation rule failed: {rule.get_rule_name()}: {e}")
                report.issues.append(ValidationIssue(
                    level="error",
                    category="system",
                    setting_path="validation.pipeline",
                    message=f"Validation rule error: {e}",
                    suggested_fix="Check validation rule implementation"
                ))
        
        # Apply auto-fixes if requested
        if auto_fix:
            self._apply_auto_fixes(config_manager, report)
        
        # Log summary
        logger.info(f"Validation complete: {report.summary}")
        
        if report.issues:
            for issue in report.issues:
                log_func = getattr(logger, issue.level, logger.info)
                log_func(f"Config {issue.level}: {issue.message}")
        
        return report
    
    def _apply_auto_fixes(self, config_manager, report: ValidationReport) -> None:
        """Apply automatic fixes for auto-fixable issues"""
        for issue in report.issues:
            if issue.auto_fixable and issue.fix_action:
                try:
                    self._execute_fix_action(config_manager, issue)
                    report.auto_fixes_applied.append(
                        f"Fixed {issue.setting_path}: {issue.message}"
                    )
                except Exception as e:
                    logger.error(f"Auto-fix failed for {issue.setting_path}: {e}")
    
    def _execute_fix_action(self, config_manager, issue: ValidationIssue) -> None:
        """Execute a specific fix action"""
        if issue.fix_action == "auto_detect":
            # Auto-detection already handled in validation rules
            pass
        elif issue.fix_action.startswith("set_path:"):
            path_value = issue.fix_action.split(":", 1)[1]
            config_manager.set_setting(issue.setting_path, path_value)
        else:
            logger.warning(f"Unknown fix action: {issue.fix_action}")