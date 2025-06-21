"""
Standardized Error Handling System

Implements the multi-mind analysis recommendation for consistent error handling
to replace bare except statements and improve debugging capabilities.

This module provides structured error handling patterns, logging, and recovery
mechanisms to improve system reliability and debugging.
"""

import functools
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from ..utils.advanced_logging import get_logger

logger = get_logger("error_handling")


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    EXTERNAL_SERVICE = "external_service"
    UI = "ui"
    WORKFLOW = "workflow"
    VALIDATION = "validation"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Error context information for better debugging"""
    operation: str
    component: str
    parameters: Dict[str, Any]
    user_action: Optional[str] = None
    system_state: Optional[Dict[str, Any]] = None


@dataclass
class ErrorInfo:
    """Structured error information"""
    error_type: Type[Exception]
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: Optional[ErrorContext] = None
    recovery_suggestion: Optional[str] = None
    user_message: Optional[str] = None
    should_retry: bool = False
    max_retries: int = 0


class ErrorHandlingRegistry:
    """Registry for error handling patterns"""
    
    def __init__(self):
        self._handlers: Dict[Type[Exception], ErrorInfo] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default error handlers for common exceptions"""
        # File system errors
        self.register(FileNotFoundError, ErrorInfo(
            error_type=FileNotFoundError,
            message="File or directory not found",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.FILE_SYSTEM,
            recovery_suggestion="Check file path and permissions",
            user_message="The requested file could not be found. Please check the file path.",
            should_retry=False
        ))
        
        self.register(PermissionError, ErrorInfo(
            error_type=PermissionError,
            message="Permission denied",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.FILE_SYSTEM,
            recovery_suggestion="Check file permissions or run with appropriate privileges",
            user_message="Permission denied. Please check file permissions.",
            should_retry=False
        ))
        
        # Network errors
        self.register(ConnectionError, ErrorInfo(
            error_type=ConnectionError,
            message="Network connection failed",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            recovery_suggestion="Check network connectivity and service availability",
            user_message="Network connection failed. Please check your connection.",
            should_retry=True,
            max_retries=3
        ))
        
        # JSON/Configuration errors
        self.register(ValueError, ErrorInfo(
            error_type=ValueError,
            message="Invalid value or format",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            recovery_suggestion="Check input format and values",
            user_message="Invalid input format. Please check your settings.",
            should_retry=False
        ))
        
        # Import/Module errors
        self.register(ImportError, ErrorInfo(
            error_type=ImportError,
            message="Module import failed",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            recovery_suggestion="Check dependencies and installation",
            user_message="A required component could not be loaded. Please check installation.",
            should_retry=False
        ))
    
    def register(self, exception_type: Type[Exception], error_info: ErrorInfo):
        """Register error handler for specific exception type"""
        self._handlers[exception_type] = error_info
    
    def get_handler(self, exception_type: Type[Exception]) -> Optional[ErrorInfo]:
        """Get error handler for exception type"""
        # Try exact match first
        if exception_type in self._handlers:
            return self._handlers[exception_type]
        
        # Try parent classes
        for exc_type, handler in self._handlers.items():
            if issubclass(exception_type, exc_type):
                return handler
        
        return None


# Global error registry
error_registry = ErrorHandlingRegistry()


class ErrorHandler:
    """Centralized error handler with context and recovery"""
    
    def __init__(self, component: str):
        self.component = component
        self.error_counts: Dict[str, int] = {}
    
    def handle_error(self, 
                    exception: Exception,
                    operation: str,
                    context: Optional[ErrorContext] = None,
                    reraise: bool = False) -> Optional[Any]:
        """
        Handle error with structured logging and recovery
        
        Args:
            exception: The exception that occurred
            operation: Description of the operation that failed
            context: Additional context information
            reraise: Whether to reraise the exception after handling
        
        Returns:
            None or recovery value if applicable
        """
        error_info = error_registry.get_handler(type(exception))
        
        if not error_info:
            error_info = ErrorInfo(
                error_type=type(exception),
                message=str(exception),
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.UNKNOWN,
                recovery_suggestion="Check logs for more details"
            )
        
        # Create full context
        full_context = context or ErrorContext(
            operation=operation,
            component=self.component,
            parameters={}
        )
        
        # Track error frequency
        error_key = f"{self.component}.{operation}.{type(exception).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log error with structured information
        self._log_error(exception, error_info, full_context)
        
        # Handle based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error in {self.component}: {operation}")
        
        if reraise:
            raise exception
        
        return None
    
    def _log_error(self, exception: Exception, error_info: ErrorInfo, context: ErrorContext):
        """Log error with structured information"""
        log_data = {
            "component": self.component,
            "operation": context.operation,
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "severity": error_info.severity.value,
            "category": error_info.category.value,
            "recovery_suggestion": error_info.recovery_suggestion,
            "context_parameters": context.parameters,
        }
        
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"Error in {context.operation}", extra=log_data, exc_info=True)
        else:
            logger.warning(f"Warning in {context.operation}", extra=log_data)


# Decorators for automatic error handling

F = TypeVar('F', bound=Callable[..., Any])

def handle_errors(component: str, 
                 operation: Optional[str] = None,
                 reraise: bool = False,
                 return_value: Any = None) -> Callable[[F], F]:
    """
    Decorator for automatic error handling
    
    Args:
        component: Component name for logging
        operation: Operation description (defaults to function name)
        reraise: Whether to reraise exceptions
        return_value: Value to return on error (if not reraising)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(component)
            op_name = operation or func.__name__
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    operation=op_name,
                    component=component,
                    parameters={"args": str(args), "kwargs": str(kwargs)}
                )
                
                handler.handle_error(e, op_name, context, reraise=reraise)
                return return_value
        
        return wrapper
    return decorator


@contextmanager
def error_context(component: str, operation: str, **context_params):
    """
    Context manager for error handling with additional context
    
    Usage:
        with error_context("workflow", "load_parameters", file_path="config.json"):
            # Code that might raise exceptions
            pass
    """
    handler = ErrorHandler(component)
    context = ErrorContext(
        operation=operation,
        component=component,
        parameters=context_params
    )
    
    try:
        yield handler
    except Exception as e:
        handler.handle_error(e, operation, context, reraise=True)


def safe_call(func: Callable, 
              component: str,
              operation: str = None,
              default_return: Any = None,
              **kwargs) -> Any:
    """
    Safely call a function with error handling
    
    Args:
        func: Function to call
        component: Component name for logging
        operation: Operation description
        default_return: Value to return on error
        **kwargs: Arguments to pass to function
    
    Returns:
        Function result or default_return on error
    """
    handler = ErrorHandler(component)
    op_name = operation or getattr(func, '__name__', 'unknown_function')
    
    try:
        return func(**kwargs)
    except Exception as e:
        context = ErrorContext(
            operation=op_name,
            component=component,
            parameters=kwargs
        )
        handler.handle_error(e, op_name, context)
        return default_return


# Specific error handling patterns for common scenarios

class ConfigurationErrorHandler(ErrorHandler):
    """Specialized error handler for configuration operations"""
    
    def __init__(self):
        super().__init__("configuration")
    
    def handle_config_load_error(self, error: Exception, config_file: Path) -> Dict[str, Any]:
        """Handle configuration loading errors with fallback"""
        context = ErrorContext(
            operation="load_configuration",
            component="configuration",
            parameters={"config_file": str(config_file)}
        )
        
        if isinstance(error, FileNotFoundError):
            logger.warning(f"Configuration file not found: {config_file}, using defaults")
            return {}
        elif isinstance(error, (ValueError, SyntaxError)):
            logger.error(f"Invalid configuration format in {config_file}", exc_info=True)
            backup_file = config_file.with_suffix('.backup')
            if backup_file.exists():
                logger.info(f"Attempting to load backup configuration: {backup_file}")
                return self.handle_config_load_error(error, backup_file)
        
        self.handle_error(error, "load_configuration", context)
        return {}


class NetworkErrorHandler(ErrorHandler):
    """Specialized error handler for network operations"""
    
    def __init__(self):
        super().__init__("network")
    
    def handle_connection_error(self, 
                              error: Exception, 
                              url: str, 
                              operation: str,
                              retry_count: int = 0,
                              max_retries: int = 3) -> Optional[Any]:
        """Handle network connection errors with retry logic"""
        context = ErrorContext(
            operation=operation,
            component="network",
            parameters={"url": url, "retry_count": retry_count}
        )
        
        if retry_count < max_retries:
            logger.warning(f"Network operation failed, retrying ({retry_count + 1}/{max_retries}): {url}")
            return None  # Signal to retry
        
        self.handle_error(error, operation, context)
        return None


class FileSystemErrorHandler(ErrorHandler):
    """Specialized error handler for file system operations"""
    
    def __init__(self):
        super().__init__("filesystem")
    
    def handle_file_operation_error(self, 
                                  error: Exception, 
                                  operation: str,
                                  file_path: Path,
                                  create_parent_dirs: bool = False) -> bool:
        """Handle file system errors with recovery attempts"""
        context = ErrorContext(
            operation=operation,
            component="filesystem",
            parameters={"file_path": str(file_path)}
        )
        
        if isinstance(error, FileNotFoundError) and create_parent_dirs:
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created parent directories for: {file_path}")
                return True  # Signal that operation can be retried
            except Exception as mkdir_error:
                self.handle_error(mkdir_error, "create_directories", context)
        
        self.handle_error(error, operation, context)
        return False


# Global instances for common use
config_error_handler = ConfigurationErrorHandler()
network_error_handler = NetworkErrorHandler()
filesystem_error_handler = FileSystemErrorHandler()


# Migration helpers for replacing bare except statements

def replace_bare_except(exception_types: List[Type[Exception]] = None) -> Callable:
    """
    Decorator to replace bare except with specific exception handling
    
    Usage:
        @replace_bare_except([ConnectionError, ValueError])
        def risky_operation():
            # code that might fail
            pass
    """
    if exception_types is None:
        exception_types = [Exception]  # Catch all but be explicit
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exception_types) as e:
                handler = ErrorHandler(getattr(func, '__module__', 'unknown'))
                context = ErrorContext(
                    operation=func.__name__,
                    component=getattr(func, '__module__', 'unknown'),
                    parameters={"args": str(args), "kwargs": str(kwargs)}
                )
                handler.handle_error(e, func.__name__, context)
                return None
        return wrapper
    return decorator


def log_and_continue(component: str, operation: str = None):
    """
    Decorator that logs errors and continues execution
    
    Replacement for bare except: pass patterns
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler(component)
                op_name = operation or func.__name__
                context = ErrorContext(
                    operation=op_name,
                    component=component,
                    parameters={"args": str(args), "kwargs": str(kwargs)}
                )
                handler.handle_error(e, op_name, context)
                # Continue execution (like the original bare except: pass)
                return None
        return wrapper
    return decorator