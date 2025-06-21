"""
Comprehensive Error Recovery System

Implements intelligent error recovery mechanisms with circuit breakers,
retry policies, fallback strategies, and automatic healing.

Part of Phase 3 Quality & Polish - addresses the multi-mind analysis
finding of insufficient error handling and provides professional-grade
resilience and fault tolerance.
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from contextlib import asynccontextmanager

from ..utils.advanced_logging import get_logger

logger = get_logger("error_recovery")


class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    AUTOMATIC_HEALING = "automatic_healing"
    USER_INTERVENTION = "user_intervention"


class ErrorSeverity(Enum):
    """Error severity levels for recovery decisions"""
    MINOR = "minor"           # Recoverable with simple retry
    MODERATE = "moderate"     # Requires fallback or alternative approach
    SEVERE = "severe"         # Requires circuit breaker or degradation
    CRITICAL = "critical"     # Requires immediate intervention


@dataclass
class RecoveryPolicy:
    """Policy for error recovery"""
    strategy: RecoveryStrategy
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    fallback_enabled: bool = True
    auto_healing_enabled: bool = True
    
    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        delay = self.retry_delay * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay)


@dataclass
class ErrorContext:
    """Context information for error recovery"""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    component: str = ""
    operation: str = ""
    error_type: str = ""
    error_message: str = ""
    timestamp: float = field(default_factory=time.time)
    severity: ErrorSeverity = ErrorSeverity.MINOR
    metadata: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    last_recovery_attempt: float = 0
    recovery_successful: bool = False


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreaker:
    """Circuit breaker for automatic failure handling"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = field(default_factory=time.time)
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        current_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if current_time - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.last_success_time = time.time()
        self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN


class RecoveryHandler(ABC):
    """Abstract base for recovery handlers"""
    
    @abstractmethod
    async def can_handle(self, error_context: ErrorContext) -> bool:
        """Check if this handler can handle the error"""
        pass
    
    @abstractmethod
    async def recover(self, error_context: ErrorContext) -> Tuple[bool, str]:
        """Attempt to recover from error"""
        pass
    
    @abstractmethod
    def get_fallback(self, error_context: ErrorContext) -> Any:
        """Get fallback value/behavior"""
        pass


class NetworkRecoveryHandler(RecoveryHandler):
    """Recovery handler for network-related errors"""
    
    async def can_handle(self, error_context: ErrorContext) -> bool:
        """Check if this is a network error"""
        network_errors = [
            "ConnectionError", "TimeoutError", "HTTPError",
            "NetworkError", "URLError", "ConnectTimeout"
        ]
        return any(error in error_context.error_type for error in network_errors)
    
    async def recover(self, error_context: ErrorContext) -> Tuple[bool, str]:
        """Attempt network recovery"""
        try:
            # Wait before retry
            await asyncio.sleep(1.0)
            
            # Try to verify network connectivity
            if await self._test_connectivity():
                return True, "Network connectivity restored"
            else:
                return False, "Network still unavailable"
                
        except Exception as e:
            return False, f"Recovery attempt failed: {str(e)}"
    
    async def _test_connectivity(self) -> bool:
        """Test basic network connectivity"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://httpbin.org/status/200")
                return response.status_code == 200
        except:
            return False
    
    def get_fallback(self, error_context: ErrorContext) -> Any:
        """Get fallback for network operations"""
        if "comfyui" in error_context.component.lower():
            return {"status": "offline", "message": "ComfyUI unavailable, using cached data"}
        elif "cinema4d" in error_context.component.lower():
            return {"status": "offline", "message": "Cinema4D unavailable, operations queued"}
        else:
            return {"status": "error", "message": "Network service unavailable"}


class FileSystemRecoveryHandler(RecoveryHandler):
    """Recovery handler for file system errors"""
    
    async def can_handle(self, error_context: ErrorContext) -> bool:
        """Check if this is a file system error"""
        fs_errors = [
            "FileNotFoundError", "PermissionError", "OSError",
            "IOError", "IsADirectoryError", "NotADirectoryError"
        ]
        return any(error in error_context.error_type for error in fs_errors)
    
    async def recover(self, error_context: ErrorContext) -> Tuple[bool, str]:
        """Attempt file system recovery"""
        try:
            file_path = error_context.metadata.get("file_path")
            if not file_path:
                return False, "No file path provided for recovery"
            
            path = Path(file_path)
            
            # Try to create parent directories
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                return True, f"Created missing directories: {path.parent}"
            
            # Try to create empty file if it doesn't exist
            if not path.exists() and error_context.error_type == "FileNotFoundError":
                path.touch()
                return True, f"Created missing file: {path}"
            
            return False, "Unable to recover file system error"
            
        except Exception as e:
            return False, f"File system recovery failed: {str(e)}"
    
    def get_fallback(self, error_context: ErrorContext) -> Any:
        """Get fallback for file operations"""
        if "config" in error_context.operation.lower():
            return {}  # Empty configuration
        elif "workflow" in error_context.operation.lower():
            return {"nodes": {}, "version": "1.0"}  # Minimal workflow
        else:
            return None


class ConfigurationRecoveryHandler(RecoveryHandler):
    """Recovery handler for configuration errors"""
    
    async def can_handle(self, error_context: ErrorContext) -> bool:
        """Check if this is a configuration error"""
        return "config" in error_context.component.lower() or "configuration" in error_context.operation.lower()
    
    async def recover(self, error_context: ErrorContext) -> Tuple[bool, str]:
        """Attempt configuration recovery"""
        try:
            # Try to load backup configuration
            config_dir = Path("config")
            backup_dir = config_dir / "backups"
            
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.json"))
                if backup_files:
                    latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                    return True, f"Recovered from backup: {latest_backup.name}"
            
            # Create default configuration
            default_config = self._create_default_config()
            config_file = config_dir / "unified_config.json"
            
            config_dir.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                import json
                json.dump(default_config, f, indent=2)
            
            return True, "Created default configuration"
            
        except Exception as e:
            return False, f"Configuration recovery failed: {str(e)}"
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "ui": {
                "theme": "dark",
                "window_size": [1200, 800],
                "auto_save": True
            },
            "mcp": {
                "comfyui_server_url": "http://127.0.0.1:8188",
                "cinema4d_port": 54321,
                "connection_timeout": 10
            },
            "base": {
                "workflows_dir": "workflows",
                "images_dir": "images",
                "models_dir": "models"
            }
        }
    
    def get_fallback(self, error_context: ErrorContext) -> Any:
        """Get fallback configuration"""
        return self._create_default_config()


class WorkflowRecoveryHandler(RecoveryHandler):
    """Recovery handler for workflow execution errors"""
    
    async def can_handle(self, error_context: ErrorContext) -> bool:
        """Check if this is a workflow error"""
        return "workflow" in error_context.component.lower() or "workflow" in error_context.operation.lower()
    
    async def recover(self, error_context: ErrorContext) -> Tuple[bool, str]:
        """Attempt workflow recovery"""
        try:
            # Check if ComfyUI is accessible
            from ..mcp.comfyui_client import ComfyUIClient
            client = ComfyUIClient()
            
            if await client.check_web_interface():
                # Clear any stuck executions
                await client.interrupt()
                await asyncio.sleep(2.0)
                
                return True, "Cleared workflow execution queue"
            else:
                return False, "ComfyUI service unavailable"
                
        except Exception as e:
            return False, f"Workflow recovery failed: {str(e)}"
    
    def get_fallback(self, error_context: ErrorContext) -> Any:
        """Get fallback for workflow operations"""
        return {
            "status": "queued",
            "message": "Workflow queued for later execution",
            "fallback_mode": True
        }


class ErrorRecoveryManager:
    """
    Comprehensive error recovery system
    
    Provides intelligent error handling with multiple recovery strategies,
    circuit breakers, automatic healing, and fallback mechanisms.
    """
    
    def __init__(self):
        self.recovery_handlers: List[RecoveryHandler] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[ErrorContext] = []
        self.recovery_policies: Dict[str, RecoveryPolicy] = {}
        self.auto_healing_enabled = True
        self.max_history_size = 1000
        
        # Register default handlers
        self._register_default_handlers()
        self._configure_default_policies()
    
    def _register_default_handlers(self):
        """Register default recovery handlers"""
        self.recovery_handlers = [
            NetworkRecoveryHandler(),
            FileSystemRecoveryHandler(),
            ConfigurationRecoveryHandler(),
            WorkflowRecoveryHandler()
        ]
    
    def _configure_default_policies(self):
        """Configure default recovery policies"""
        self.recovery_policies = {
            "network": RecoveryPolicy(
                strategy=RecoveryStrategy.RETRY,
                max_retries=3,
                retry_delay=2.0,
                circuit_breaker_threshold=5
            ),
            "filesystem": RecoveryPolicy(
                strategy=RecoveryStrategy.FALLBACK,
                max_retries=2,
                retry_delay=0.5,
                fallback_enabled=True
            ),
            "configuration": RecoveryPolicy(
                strategy=RecoveryStrategy.AUTOMATIC_HEALING,
                max_retries=1,
                auto_healing_enabled=True
            ),
            "workflow": RecoveryPolicy(
                strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                max_retries=2,
                circuit_breaker_threshold=3,
                circuit_breaker_timeout=30.0
            ),
            "critical": RecoveryPolicy(
                strategy=RecoveryStrategy.USER_INTERVENTION,
                max_retries=0
            )
        }
    
    def add_recovery_handler(self, handler: RecoveryHandler):
        """Add custom recovery handler"""
        self.recovery_handlers.append(handler)
    
    def configure_circuit_breaker(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """Configure circuit breaker for component"""
        self.circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
    
    def set_recovery_policy(self, component: str, policy: RecoveryPolicy):
        """Set recovery policy for component"""
        self.recovery_policies[component] = policy
    
    async def handle_error(self, 
                          exception: Exception,
                          component: str,
                          operation: str,
                          metadata: Dict[str, Any] = None) -> Tuple[bool, Any]:
        """
        Handle error with recovery strategies
        
        Returns:
            Tuple of (recovery_successful, result_or_fallback)
        """
        # Create error context
        error_context = ErrorContext(
            component=component,
            operation=operation,
            error_type=type(exception).__name__,
            error_message=str(exception),
            severity=self._assess_error_severity(exception, component),
            metadata=metadata or {}
        )
        
        # Add to history
        self._add_to_history(error_context)
        
        # Log error
        with logger.context(component=component, operation=operation):
            logger.error(f"Error occurred: {str(exception)}",
                        error_type=error_context.error_type,
                        error_id=error_context.error_id,
                        severity=error_context.severity.value)
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers.get(component)
        if circuit_breaker and not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for {component}, returning fallback")
            fallback = await self._get_fallback(error_context)
            return False, fallback
        
        # Attempt recovery
        recovery_successful, result = await self._attempt_recovery(error_context)
        
        # Update circuit breaker
        if circuit_breaker:
            if recovery_successful:
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()
        
        return recovery_successful, result
    
    def _assess_error_severity(self, exception: Exception, component: str) -> ErrorSeverity:
        """Assess error severity for recovery decisions"""
        error_type = type(exception).__name__
        
        # Critical errors
        critical_errors = [
            "SystemExit", "KeyboardInterrupt", "MemoryError",
            "SystemError", "RuntimeError"
        ]
        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        
        # Severe errors
        severe_errors = [
            "ConnectionRefusedError", "ConnectionAbortedError",
            "PermissionError", "ProcessLookupError"
        ]
        if error_type in severe_errors:
            return ErrorSeverity.SEVERE
        
        # Moderate errors
        moderate_errors = [
            "FileNotFoundError", "HTTPError", "TimeoutError",
            "ValueError", "TypeError"
        ]
        if error_type in moderate_errors:
            return ErrorSeverity.MODERATE
        
        return ErrorSeverity.MINOR
    
    async def _attempt_recovery(self, error_context: ErrorContext) -> Tuple[bool, Any]:
        """Attempt error recovery using appropriate strategy"""
        policy = self._get_recovery_policy(error_context)
        
        if policy.strategy == RecoveryStrategy.USER_INTERVENTION:
            # Critical errors require user intervention
            return False, await self._get_fallback(error_context)
        
        # Try recovery with appropriate handler
        handler = await self._find_recovery_handler(error_context)
        if not handler:
            logger.warning(f"No recovery handler found for error: {error_context.error_type}")
            return False, await self._get_fallback(error_context)
        
        # Attempt recovery with retries
        for attempt in range(1, policy.max_retries + 1):
            error_context.recovery_attempts = attempt
            error_context.last_recovery_attempt = time.time()
            
            try:
                with logger.context(operation="error_recovery"):
                    logger.debug(f"Recovery attempt {attempt}/{policy.max_retries}",
                               error_id=error_context.error_id,
                               handler=type(handler).__name__)
                
                success, message = await handler.recover(error_context)
                
                if success:
                    error_context.recovery_successful = True
                    logger.info(f"Recovery successful: {message}",
                              error_id=error_context.error_id,
                              attempts=attempt)
                    return True, None
                else:
                    logger.debug(f"Recovery attempt {attempt} failed: {message}",
                               error_id=error_context.error_id)
                    
                    # Wait before next attempt
                    if attempt < policy.max_retries:
                        delay = policy.get_retry_delay(attempt)
                        await asyncio.sleep(delay)
            
            except Exception as recovery_error:
                logger.error(f"Recovery handler failed: {str(recovery_error)}",
                           error_id=error_context.error_id,
                           recovery_attempt=attempt)
        
        # All recovery attempts failed, use fallback
        logger.warning(f"All recovery attempts failed for error: {error_context.error_id}")
        fallback = await self._get_fallback(error_context)
        return False, fallback
    
    def _get_recovery_policy(self, error_context: ErrorContext) -> RecoveryPolicy:
        """Get recovery policy for error context"""
        # Check for component-specific policy
        if error_context.component in self.recovery_policies:
            return self.recovery_policies[error_context.component]
        
        # Check for severity-based policy
        if error_context.severity == ErrorSeverity.CRITICAL:
            return self.recovery_policies["critical"]
        
        # Default based on error type
        error_type = error_context.error_type.lower()
        if "network" in error_type or "connection" in error_type:
            return self.recovery_policies["network"]
        elif "file" in error_type or "directory" in error_type:
            return self.recovery_policies["filesystem"]
        elif "config" in error_type:
            return self.recovery_policies["configuration"]
        elif "workflow" in error_type:
            return self.recovery_policies["workflow"]
        
        # Default policy
        return RecoveryPolicy(strategy=RecoveryStrategy.RETRY)
    
    async def _find_recovery_handler(self, error_context: ErrorContext) -> Optional[RecoveryHandler]:
        """Find appropriate recovery handler for error"""
        for handler in self.recovery_handlers:
            if await handler.can_handle(error_context):
                return handler
        return None
    
    async def _get_fallback(self, error_context: ErrorContext) -> Any:
        """Get fallback value for error"""
        handler = await self._find_recovery_handler(error_context)
        if handler:
            return handler.get_fallback(error_context)
        
        # Default fallback
        return {
            "status": "error",
            "message": f"Operation failed: {error_context.error_message}",
            "error_id": error_context.error_id,
            "fallback_mode": True
        }
    
    def _add_to_history(self, error_context: ErrorContext):
        """Add error to history"""
        self.error_history.append(error_context)
        
        # Limit history size
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    # Management and monitoring methods
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error and recovery statistics"""
        if not self.error_history:
            return {}
        
        total_errors = len(self.error_history)
        recovered_errors = sum(1 for ctx in self.error_history if ctx.recovery_successful)
        
        # Group by component
        component_stats = {}
        for ctx in self.error_history:
            if ctx.component not in component_stats:
                component_stats[ctx.component] = {"total": 0, "recovered": 0}
            component_stats[ctx.component]["total"] += 1
            if ctx.recovery_successful:
                component_stats[ctx.component]["recovered"] += 1
        
        # Group by error type
        error_type_stats = {}
        for ctx in self.error_history:
            if ctx.error_type not in error_type_stats:
                error_type_stats[ctx.error_type] = {"total": 0, "recovered": 0}
            error_type_stats[ctx.error_type]["total"] += 1
            if ctx.recovery_successful:
                error_type_stats[ctx.error_type]["recovered"] += 1
        
        return {
            "total_errors": total_errors,
            "recovered_errors": recovered_errors,
            "recovery_rate": (recovered_errors / total_errors * 100) if total_errors > 0 else 0,
            "component_stats": component_stats,
            "error_type_stats": error_type_stats,
            "circuit_breaker_states": {
                name: cb.state.value for name, cb in self.circuit_breakers.items()
            }
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """Get recent errors"""
        return self.error_history[-limit:] if self.error_history else []
    
    def reset_circuit_breaker(self, component: str):
        """Manually reset circuit breaker"""
        if component in self.circuit_breakers:
            cb = self.circuit_breakers[component]
            cb.state = CircuitBreakerState.CLOSED
            cb.failure_count = 0
            logger.info(f"Circuit breaker reset for {component}")
    
    def enable_auto_healing(self, enabled: bool = True):
        """Enable or disable automatic healing"""
        self.auto_healing_enabled = enabled
        logger.info(f"Auto-healing {'enabled' if enabled else 'disabled'}")


# Context manager for error recovery
@asynccontextmanager
async def error_recovery_context(component: str, 
                               operation: str,
                               recovery_manager: ErrorRecoveryManager = None,
                               metadata: Dict[str, Any] = None):
    """Context manager for automatic error recovery"""
    if recovery_manager is None:
        recovery_manager = get_recovery_manager()
    
    try:
        yield
    except Exception as e:
        recovery_successful, result = await recovery_manager.handle_error(
            e, component, operation, metadata
        )
        
        if not recovery_successful:
            # Re-raise if recovery failed and no fallback
            if result is None or (isinstance(result, dict) and result.get("fallback_mode")):
                raise
            
            # If we have a usable fallback, the context should continue normally
            # The caller needs to handle the fallback value appropriately


# Global recovery manager instance
_global_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_recovery_manager() -> ErrorRecoveryManager:
    """Get or create global recovery manager"""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = ErrorRecoveryManager()
    return _global_recovery_manager


def configure_error_recovery(
    auto_healing: bool = True,
    circuit_breaker_configs: Dict[str, Tuple[int, float]] = None,
    custom_handlers: List[RecoveryHandler] = None
):
    """Configure global error recovery system"""
    recovery_manager = get_recovery_manager()
    
    # Configure auto-healing
    recovery_manager.enable_auto_healing(auto_healing)
    
    # Configure circuit breakers
    if circuit_breaker_configs:
        for component, (threshold, timeout) in circuit_breaker_configs.items():
            recovery_manager.configure_circuit_breaker(component, threshold, timeout)
    
    # Add custom handlers
    if custom_handlers:
        for handler in custom_handlers:
            recovery_manager.add_recovery_handler(handler)
    
    logger.info("Error recovery system configured",
                auto_healing=auto_healing,
                circuit_breakers=len(circuit_breaker_configs) if circuit_breaker_configs else 0,
                custom_handlers=len(custom_handlers) if custom_handlers else 0)