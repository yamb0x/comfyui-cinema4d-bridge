"""
Advanced Logging System

Implements structured, contextual logging with performance monitoring,
error correlation, and multiple output formats. Addresses the multi-mind
analysis finding of inconsistent logging patterns across the application.

Part of Phase 3 Quality & Polish - provides professional-grade logging
with filtering, correlation IDs, and structured output for better debugging
and monitoring.
"""

import json
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone

from PySide6.QtCore import QObject, Signal


class LogLevel(Enum):
    """Enhanced log levels with priority"""
    TRACE = (5, "TRACE")
    DEBUG = (10, "DEBUG")
    INFO = (20, "INFO")
    WARNING = (30, "WARNING")
    ERROR = (40, "ERROR")
    CRITICAL = (50, "CRITICAL")
    
    def __init__(self, level_value: int, level_name: str):
        self.value = level_value
        self.name = level_name
    
    def __lt__(self, other):
        return self.value < other.value
    
    def __le__(self, other):
        return self.value <= other.value


class LogFormat(Enum):
    """Log output formats"""
    CONSOLE = "console"
    JSON = "json"
    STRUCTURED = "structured"
    MINIMAL = "minimal"


@dataclass
class LogContext:
    """Log context for correlation and filtering"""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    component: str = ""
    operation: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    message: str
    context: LogContext
    location: str = ""
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class LogFormatter:
    """Formats log entries for different outputs"""
    
    @staticmethod
    def format_console(entry: LogEntry) -> str:
        """Format for console output with colors"""
        # Color codes for different log levels
        colors = {
            "TRACE": "\033[37m",      # White
            "DEBUG": "\033[36m",      # Cyan
            "INFO": "\033[32m",       # Green
            "WARNING": "\033[33m",    # Yellow
            "ERROR": "\033[31m",      # Red
            "CRITICAL": "\033[35m",   # Magenta
        }
        reset = "\033[0m"
        
        color = colors.get(entry.level, "")
        
        # Format: [TIMESTAMP] LEVEL [COMPONENT:OPERATION] MESSAGE [DURATION]
        parts = [
            f"[{entry.timestamp}]",
            f"{color}{entry.level:8s}{reset}",
            f"[{entry.context.component}:{entry.context.operation}]" if entry.context.component else "",
            entry.message
        ]
        
        if entry.duration_ms is not None:
            parts.append(f"({entry.duration_ms:.1f}ms)")
        
        if entry.context.correlation_id:
            parts.append(f"#{entry.context.correlation_id}")
        
        return " ".join(filter(None, parts))
    
    @staticmethod
    def format_json(entry: LogEntry) -> str:
        """Format as JSON for structured logging"""
        return entry.to_json()
    
    @staticmethod
    def format_structured(entry: LogEntry) -> str:
        """Format as structured text for file output"""
        parts = [
            f"timestamp={entry.timestamp}",
            f"level={entry.level}",
            f"component={entry.context.component}",
            f"operation={entry.context.operation}",
            f"correlation_id={entry.context.correlation_id}",
            f"message=\"{entry.message}\""
        ]
        
        if entry.duration_ms is not None:
            parts.append(f"duration_ms={entry.duration_ms}")
        
        if entry.error_type:
            parts.append(f"error_type={entry.error_type}")
        
        return " ".join(parts)
    
    @staticmethod
    def format_minimal(entry: LogEntry) -> str:
        """Minimal format for performance-critical logging"""
        return f"{entry.level[0]} {entry.context.component[:8]:8s} {entry.message}"


class LogFilter:
    """Filters log entries based on criteria"""
    
    def __init__(self):
        self.min_level = LogLevel.INFO
        self.component_filters: List[str] = []
        self.operation_filters: List[str] = []
        self.correlation_filters: List[str] = []
        self.custom_filters: List[Callable[[LogEntry], bool]] = []
    
    def should_log(self, entry: LogEntry) -> bool:
        """Determine if entry should be logged"""
        # Check level
        entry_level = LogLevel[entry.level]
        if entry_level < self.min_level:
            return False
        
        # Check component filters
        if self.component_filters and entry.context.component not in self.component_filters:
            return False
        
        # Check operation filters
        if self.operation_filters and entry.context.operation not in self.operation_filters:
            return False
        
        # Check correlation filters
        if self.correlation_filters and entry.context.correlation_id not in self.correlation_filters:
            return False
        
        # Check custom filters
        for custom_filter in self.custom_filters:
            if not custom_filter(entry):
                return False
        
        return True
    
    def add_component_filter(self, component: str):
        """Add component to allow list"""
        if component not in self.component_filters:
            self.component_filters.append(component)
    
    def add_custom_filter(self, filter_func: Callable[[LogEntry], bool]):
        """Add custom filter function"""
        self.custom_filters.append(filter_func)


class LogHandler:
    """Base class for log output handlers"""
    
    def __init__(self, format_type: LogFormat = LogFormat.CONSOLE):
        self.format_type = format_type
        self.filter = LogFilter()
        self.formatter = LogFormatter()
    
    def handle(self, entry: LogEntry):
        """Handle log entry"""
        if not self.filter.should_log(entry):
            return
        
        formatted = self._format_entry(entry)
        self._write_output(formatted)
    
    def _format_entry(self, entry: LogEntry) -> str:
        """Format entry based on format type"""
        if self.format_type == LogFormat.CONSOLE:
            return self.formatter.format_console(entry)
        elif self.format_type == LogFormat.JSON:
            return self.formatter.format_json(entry)
        elif self.format_type == LogFormat.STRUCTURED:
            return self.formatter.format_structured(entry)
        elif self.format_type == LogFormat.MINIMAL:
            return self.formatter.format_minimal(entry)
        else:
            return self.formatter.format_console(entry)
    
    def _write_output(self, formatted: str):
        """Write formatted output (to be overridden)"""
        pass


class ConsoleHandler(LogHandler):
    """Console output handler"""
    
    def __init__(self, format_type: LogFormat = LogFormat.CONSOLE):
        super().__init__(format_type)
    
    def _write_output(self, formatted: str):
        """Write to console"""
        print(formatted, file=sys.stdout)
        sys.stdout.flush()


class FileHandler(LogHandler):
    """File output handler with rotation"""
    
    def __init__(self, 
                 log_file: Path,
                 format_type: LogFormat = LogFormat.STRUCTURED,
                 max_size_mb: int = 10,
                 backup_count: int = 5):
        super().__init__(format_type)
        self.log_file = log_file
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _write_output(self, formatted: str):
        """Write to file with rotation"""
        # Check if rotation is needed
        if self.log_file.exists() and self.log_file.stat().st_size > self.max_size_bytes:
            self._rotate_logs()
        
        # Write to file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(formatted + '\n')
                f.flush()
        except Exception as e:
            # Fallback to console if file write fails
            print(f"Failed to write to log file: {e}", file=sys.stderr)
            print(formatted, file=sys.stdout)
    
    def _rotate_logs(self):
        """Rotate log files"""
        try:
            # Move existing backups
            for i in range(self.backup_count - 1, 0, -1):
                old_file = self.log_file.with_suffix(f'.{i}')
                new_file = self.log_file.with_suffix(f'.{i + 1}')
                if old_file.exists():
                    if new_file.exists():
                        new_file.unlink()
                    old_file.rename(new_file)
            
            # Move current log to .1
            if self.log_file.exists():
                backup_file = self.log_file.with_suffix('.1')
                if backup_file.exists():
                    backup_file.unlink()
                self.log_file.rename(backup_file)
        
        except Exception as e:
            print(f"Log rotation failed: {e}", file=sys.stderr)


class PerformanceTracker:
    """Tracks performance metrics in logging"""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
        self.call_counts: Dict[str, int] = {}
    
    def record_operation(self, operation: str, duration_ms: float):
        """Record operation timing"""
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(duration_ms)
        
        self.call_counts[operation] = self.call_counts.get(operation, 0) + 1
    
    def record_error(self, operation: str):
        """Record error occurrence"""
        self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
    
    def get_metrics(self, operation: str) -> Dict[str, Any]:
        """Get metrics for operation"""
        times = self.operation_times.get(operation, [])
        if not times:
            return {}
        
        return {
            "call_count": self.call_counts.get(operation, 0),
            "error_count": self.error_counts.get(operation, 0),
            "avg_duration_ms": sum(times) / len(times),
            "min_duration_ms": min(times),
            "max_duration_ms": max(times),
            "error_rate": self.error_counts.get(operation, 0) / self.call_counts.get(operation, 1)
        }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all operation metrics"""
        return {op: self.get_metrics(op) for op in self.operation_times.keys()}


class AdvancedLogger(QObject):
    """
    Advanced logging system with structured output, correlation, and performance tracking
    
    Provides professional-grade logging capabilities including:
    - Structured logging with correlation IDs
    - Multiple output formats (console, JSON, structured text)
    - Performance monitoring integration
    - Contextual logging with component/operation tracking
    - Error correlation and metrics
    """
    
    # Qt signals for log events
    log_entry_created = Signal(LogEntry)
    error_logged = Signal(str, str)  # component, error_message
    performance_threshold_exceeded = Signal(str, float)  # operation, duration_ms
    
    def __init__(self, name: str = "app"):
        super().__init__()
        self.name = name
        self.handlers: List[LogHandler] = []
        self.context_stack: List[LogContext] = []
        self.performance_tracker = PerformanceTracker()
        self.error_correlation: Dict[str, List[str]] = {}
        
        # Default context
        self.base_context = LogContext(component=name)
        
        # Performance thresholds (ms)
        self.performance_thresholds = {
            "workflow_execution": 30000,  # 30 seconds
            "image_generation": 60000,    # 1 minute
            "model_generation": 120000,   # 2 minutes
            "ui_operation": 1000,         # 1 second
            "file_operation": 5000,       # 5 seconds
            "network_request": 10000,     # 10 seconds
        }
    
    def add_handler(self, handler: LogHandler):
        """Add log handler"""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: LogHandler):
        """Remove log handler"""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def _get_current_context(self) -> LogContext:
        """Get current logging context"""
        if self.context_stack:
            return self.context_stack[-1]
        return self.base_context
    
    def _create_entry(self,
                     level: LogLevel,
                     message: str,
                     error_type: Optional[str] = None,
                     stack_trace: Optional[str] = None,
                     duration_ms: Optional[float] = None,
                     **kwargs) -> LogEntry:
        """Create log entry"""
        context = self._get_current_context()
        
        # Create entry
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.name,
            message=message,
            context=context,
            location=self._get_caller_location(),
            duration_ms=duration_ms,
            error_type=error_type,
            stack_trace=stack_trace,
            metrics=kwargs
        )
        
        return entry
    
    def _get_caller_location(self) -> str:
        """Get caller file and line number"""
        import inspect
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual caller
            caller_frame = frame.f_back.f_back.f_back
            if caller_frame:
                filename = Path(caller_frame.f_code.co_filename).name
                line_no = caller_frame.f_lineno
                func_name = caller_frame.f_code.co_name
                return f"{filename}:{line_no}:{func_name}"
        except:
            pass
        finally:
            del frame
        return "unknown"
    
    def _emit_entry(self, entry: LogEntry):
        """Emit log entry to all handlers"""
        # Send to handlers
        for handler in self.handlers:
            try:
                handler.handle(entry)
            except Exception as e:
                # Prevent logging loops
                print(f"Log handler error: {e}", file=sys.stderr)
        
        # Emit Qt signal
        self.log_entry_created.emit(entry)
        
        # Track performance
        if entry.duration_ms is not None:
            self.performance_tracker.record_operation(
                entry.context.operation, entry.duration_ms
            )
            
            # Check thresholds
            threshold = self.performance_thresholds.get(entry.context.operation)
            if threshold and entry.duration_ms > threshold:
                self.performance_threshold_exceeded.emit(
                    entry.context.operation, entry.duration_ms
                )
        
        # Track errors
        if entry.level in ["ERROR", "CRITICAL"]:
            self.performance_tracker.record_error(entry.context.operation)
            self.error_logged.emit(entry.context.component, entry.message)
            
            # Error correlation
            correlation_key = f"{entry.context.component}:{entry.context.operation}"
            if correlation_key not in self.error_correlation:
                self.error_correlation[correlation_key] = []
            self.error_correlation[correlation_key].append(entry.message)
    
    # Logging methods
    
    def trace(self, message: str, **kwargs):
        """Log trace message"""
        entry = self._create_entry(LogLevel.TRACE, message, **kwargs)
        self._emit_entry(entry)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        entry = self._create_entry(LogLevel.DEBUG, message, **kwargs)
        self._emit_entry(entry)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        entry = self._create_entry(LogLevel.INFO, message, **kwargs)
        self._emit_entry(entry)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        entry = self._create_entry(LogLevel.WARNING, message, **kwargs)
        self._emit_entry(entry)
    
    def error(self, message: str, error_type: str = None, stack_trace: str = None, **kwargs):
        """Log error message"""
        entry = self._create_entry(LogLevel.ERROR, message, error_type, stack_trace, **kwargs)
        self._emit_entry(entry)
    
    def critical(self, message: str, error_type: str = None, stack_trace: str = None, **kwargs):
        """Log critical message"""
        entry = self._create_entry(LogLevel.CRITICAL, message, error_type, stack_trace, **kwargs)
        self._emit_entry(entry)
    
    def log_exception(self, exception: Exception, message: str = "", **kwargs):
        """Log exception with stack trace"""
        import traceback
        
        error_message = message or f"Exception occurred: {str(exception)}"
        stack_trace = traceback.format_exc()
        error_type = type(exception).__name__
        
        entry = self._create_entry(
            LogLevel.ERROR, error_message, error_type, stack_trace, **kwargs
        )
        self._emit_entry(entry)
    
    # Context management
    
    @contextmanager
    def context(self, component: str = None, operation: str = None, **metadata):
        """Contextual logging scope"""
        # Create new context based on current context
        current_context = self._get_current_context()
        new_context = LogContext(
            correlation_id=current_context.correlation_id,
            component=component or current_context.component,
            operation=operation or current_context.operation,
            user_id=current_context.user_id,
            session_id=current_context.session_id,
            request_id=current_context.request_id,
            metadata={**current_context.metadata, **metadata}
        )
        
        # Push context
        self.context_stack.append(new_context)
        
        try:
            yield new_context
        finally:
            # Pop context
            if self.context_stack:
                self.context_stack.pop()
    
    @contextmanager
    def timed_operation(self, operation: str, component: str = None):
        """Timed operation with automatic duration logging"""
        start_time = time.perf_counter()
        
        with self.context(component=component, operation=operation):
            try:
                yield
                # Success
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.info(f"Operation completed", duration_ms=duration_ms)
            except Exception as e:
                # Failure
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.error(f"Operation failed: {str(e)}", duration_ms=duration_ms)
                raise
    
    def set_session_context(self, session_id: str, user_id: str = None):
        """Set session context for correlation"""
        self.base_context.session_id = session_id
        self.base_context.user_id = user_id
    
    def new_correlation_id(self) -> str:
        """Generate new correlation ID"""
        correlation_id = str(uuid.uuid4())[:8]
        self.base_context.correlation_id = correlation_id
        return correlation_id
    
    # Configuration and metrics
    
    def configure_performance_thresholds(self, thresholds: Dict[str, float]):
        """Configure performance thresholds"""
        self.performance_thresholds.update(thresholds)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_tracker.get_all_metrics()
    
    def get_error_correlation(self) -> Dict[str, List[str]]:
        """Get error correlation data"""
        return self.error_correlation.copy()
    
    def set_log_level(self, level: LogLevel):
        """Set minimum log level for all handlers"""
        for handler in self.handlers:
            handler.filter.min_level = level
    
    def add_component_filter(self, component: str):
        """Add component filter to all handlers"""
        for handler in self.handlers:
            handler.filter.add_component_filter(component)


# Global logger instance
_global_logger: Optional[AdvancedLogger] = None


def get_logger(name: str = "app") -> AdvancedLogger:
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AdvancedLogger(name)
        
        # Add default console handler
        console_handler = ConsoleHandler(LogFormat.CONSOLE)
        _global_logger.add_handler(console_handler)
        
        # Add default file handler
        log_dir = Path("logs")
        file_handler = FileHandler(log_dir / "app.log", LogFormat.JSON)
        _global_logger.add_handler(file_handler)
    
    return _global_logger


def configure_logging(
    log_level: LogLevel = LogLevel.INFO,
    log_dir: Path = None,
    console_format: LogFormat = LogFormat.CONSOLE,
    file_format: LogFormat = LogFormat.JSON,
    enable_performance_tracking: bool = True
):
    """Configure global logging system"""
    logger = get_logger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Add console handler
    console_handler = ConsoleHandler(console_format)
    console_handler.filter.min_level = log_level
    logger.add_handler(console_handler)
    
    # Add file handler if log directory specified
    if log_dir:
        file_handler = FileHandler(log_dir / "app.log", file_format)
        file_handler.filter.min_level = log_level
        logger.add_handler(file_handler)
        
        # Add error-only file handler
        error_handler = FileHandler(log_dir / "errors.log", LogFormat.JSON)
        error_handler.filter.min_level = LogLevel.ERROR
        logger.add_handler(error_handler)
    
    logger.info("Advanced logging system configured", 
                log_level=log_level.name,
                console_format=console_format.value,
                file_format=file_format.value if log_dir else None,
                performance_tracking=enable_performance_tracking)


# Convenience functions for backward compatibility
def trace(message: str, **kwargs):
    get_logger().trace(message, **kwargs)

def debug(message: str, **kwargs):
    get_logger().debug(message, **kwargs)

def info(message: str, **kwargs):
    get_logger().info(message, **kwargs)

def warning(message: str, **kwargs):
    get_logger().warning(message, **kwargs)

def error(message: str, **kwargs):
    get_logger().error(message, **kwargs)

def critical(message: str, **kwargs):
    get_logger().critical(message, **kwargs)

def log_exception(exception: Exception, message: str = "", **kwargs):
    get_logger().log_exception(exception, message, **kwargs)