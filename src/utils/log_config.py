"""
Logging Level Configuration
Controls verbosity for different parts of the application
"""

from enum import Enum
from typing import Dict

class LogLevel(Enum):
    """Log levels for different components"""
    SILENT = 0      # No logging
    CRITICAL = 1    # Only critical errors
    ERROR = 2       # Errors only
    WARNING = 3     # Warnings and above
    INFO = 4        # General info
    DEBUG = 5       # Detailed debug info
    VERBOSE = 6     # Everything including parameter details

# Component-specific log levels
LOG_LEVELS: Dict[str, LogLevel] = {
    # Core Application
    "app.startup": LogLevel.INFO,
    "app.ui_setup": LogLevel.WARNING,
    "app.connections": LogLevel.INFO,
    
    # Parameter/Widget System
    "params.loading": LogLevel.WARNING,  # Was showing all the 🔄 🔧 logs
    "params.widgets": LogLevel.ERROR,    # Widget creation details
    "params.updates": LogLevel.WARNING,  # Dynamic updates
    
    # Workflow Management
    "workflow.loading": LogLevel.INFO,
    "workflow.execution": LogLevel.INFO,
    "workflow.monitoring": LogLevel.INFO,
    
    # File Operations
    "file.monitoring": LogLevel.WARNING,
    "file.operations": LogLevel.INFO,
    
    # Connections
    "comfyui.connection": LogLevel.INFO,
    "c4d.connection": LogLevel.INFO,
    "mcp.operations": LogLevel.WARNING,
    
    # UI Events
    "ui.events": LogLevel.WARNING,
    "ui.selection": LogLevel.WARNING,
    "ui.tabs": LogLevel.INFO,
    
    # System Monitoring
    "system.performance": LogLevel.ERROR,  # Hide performance updates
    "system.gpu": LogLevel.ERROR,
}

def should_log(component: str, level: LogLevel) -> bool:
    """Check if a log should be shown based on component and level"""
    configured_level = LOG_LEVELS.get(component, LogLevel.INFO)
    return level.value <= configured_level.value

# Convenience functions for common checks
def is_verbose_enabled(component: str) -> bool:
    """Check if verbose logging is enabled for component"""
    return should_log(component, LogLevel.VERBOSE)

def is_debug_enabled(component: str) -> bool:
    """Check if debug logging is enabled for component"""
    return should_log(component, LogLevel.DEBUG)

def is_info_enabled(component: str) -> bool:
    """Check if info logging is enabled for component"""
    return should_log(component, LogLevel.INFO)