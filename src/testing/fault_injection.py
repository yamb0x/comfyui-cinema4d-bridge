"""
Fault Injection Framework for comfy2c4d

Provides systematic fault injection capabilities for testing reliability
patterns and improving system resilience.
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from contextlib import contextmanager
from loguru import logger


class FaultType(Enum):
    """Types of faults that can be injected"""
    NETWORK_DELAY = "network_delay"
    NETWORK_FAILURE = "network_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    DATA_CORRUPTION = "data_corruption"
    CONCURRENCY_ISSUE = "concurrency_issue"
    STATE_INCONSISTENCY = "state_inconsistency"
    OBSERVER_FAILURE = "observer_failure"
    CONFIG_DRIFT = "config_drift"


@dataclass
class FaultConfig:
    """Configuration for a fault injection"""
    fault_type: FaultType
    probability: float = 0.1  # 10% chance by default
    delay_ms: Optional[int] = None
    exception_type: Optional[type] = None
    custom_behavior: Optional[Callable] = None
    metadata: Dict[str, Any] = None


@dataclass
class FaultEvent:
    """Record of a fault injection event"""
    timestamp: datetime
    fault_type: FaultType
    component: str
    method: str
    triggered: bool
    impact: Optional[str] = None
    recovery_time_ms: Optional[float] = None


class FaultInjector(ABC):
    """Abstract base class for fault injectors"""
    
    @abstractmethod
    def inject(self, *args, **kwargs) -> Any:
        """Inject the fault"""
        pass


class NetworkDelayInjector(FaultInjector):
    """Inject network delays"""
    
    def __init__(self, min_delay_ms: int = 100, max_delay_ms: int = 5000):
        self.min_delay = min_delay_ms / 1000.0
        self.max_delay = max_delay_ms / 1000.0
    
    async def inject(self, func: Callable, *args, **kwargs) -> Any:
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Injecting network delay: {delay*1000:.0f}ms")
        await asyncio.sleep(delay)
        return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)


class NetworkFailureInjector(FaultInjector):
    """Inject network failures"""
    
    def inject(self, *args, **kwargs) -> None:
        logger.debug("Injecting network failure")
        raise ConnectionError("Simulated network failure")


class ResourceExhaustionInjector(FaultInjector):
    """Simulate resource exhaustion"""
    
    def __init__(self, resource_type: str = "memory"):
        self.resource_type = resource_type
    
    def inject(self, *args, **kwargs) -> None:
        if self.resource_type == "memory":
            raise MemoryError("Simulated memory exhaustion")
        elif self.resource_type == "cpu":
            # Simulate CPU exhaustion with busy loop
            start = time.time()
            while time.time() - start < 0.1:
                _ = sum(i**2 for i in range(1000))
        elif self.resource_type == "disk":
            raise OSError("No space left on device")


class DataCorruptionInjector(FaultInjector):
    """Inject data corruption"""
    
    def inject(self, data: Any) -> Any:
        if isinstance(data, dict):
            # Randomly modify dictionary values
            corrupted = data.copy()
            if corrupted:
                key = random.choice(list(corrupted.keys()))
                corrupted[key] = None
            return corrupted
        elif isinstance(data, list):
            # Randomly remove items
            corrupted = data.copy()
            if corrupted:
                corrupted.pop(random.randint(0, len(corrupted) - 1))
            return corrupted
        elif isinstance(data, str):
            # Randomly corrupt string
            if data:
                pos = random.randint(0, len(data) - 1)
                return data[:pos] + "�" + data[pos+1:]
        return data


class ConcurrencyIssueInjector(FaultInjector):
    """Simulate concurrency issues"""
    
    async def inject(self, func: Callable, *args, **kwargs) -> Any:
        # Add random delay to increase chance of race conditions
        await asyncio.sleep(random.uniform(0, 0.1))
        
        # Potentially execute multiple times to simulate double execution
        if random.random() < 0.3:
            logger.debug("Simulating double execution")
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        
        return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)


class FaultInjectionManager:
    """
    Manages fault injection across the application.
    
    Features:
    - Configurable fault injection by component/method
    - Probability-based injection
    - Fault event tracking
    - Recovery time measurement
    - Integration with health monitoring
    """
    
    def __init__(self):
        self._enabled = False
        self._fault_configs: Dict[str, FaultConfig] = {}
        self._fault_events: List[FaultEvent] = []
        self._injectors: Dict[FaultType, FaultInjector] = {
            FaultType.NETWORK_DELAY: NetworkDelayInjector(),
            FaultType.NETWORK_FAILURE: NetworkFailureInjector(),
            FaultType.RESOURCE_EXHAUSTION: ResourceExhaustionInjector(),
            FaultType.DATA_CORRUPTION: DataCorruptionInjector(),
            FaultType.CONCURRENCY_ISSUE: ConcurrencyIssueInjector(),
        }
        
        logger.info("Fault injection framework initialized")
    
    def enable(self, enabled: bool = True):
        """Enable or disable fault injection"""
        self._enabled = enabled
        logger.info(f"Fault injection {'enabled' if enabled else 'disabled'}")
    
    def configure_fault(self, component: str, method: str, config: FaultConfig):
        """Configure fault injection for a specific component/method"""
        key = f"{component}.{method}"
        self._fault_configs[key] = config
        logger.debug(f"Configured fault injection for {key}: {config.fault_type.value}")
    
    def should_inject(self, component: str, method: str) -> Optional[FaultConfig]:
        """Determine if fault should be injected"""
        if not self._enabled:
            return None
        
        key = f"{component}.{method}"
        config = self._fault_configs.get(key)
        
        if config and random.random() < config.probability:
            return config
        
        return None
    
    @contextmanager
    def inject_fault(self, component: str, method: str):
        """Context manager for fault injection"""
        config = self.should_inject(component, method)
        
        if not config:
            yield None
            return
        
        start_time = time.time()
        event = FaultEvent(
            timestamp=datetime.now(),
            fault_type=config.fault_type,
            component=component,
            method=method,
            triggered=True
        )
        
        try:
            # Get appropriate injector
            injector = self._injectors.get(config.fault_type)
            
            if config.custom_behavior:
                # Use custom behavior if provided
                yield config.custom_behavior
            elif injector:
                yield injector
            else:
                yield None
            
        except Exception as e:
            event.impact = str(e)
            raise
        finally:
            event.recovery_time_ms = (time.time() - start_time) * 1000
            self._fault_events.append(event)
            logger.info(f"Fault injected: {component}.{method} - {config.fault_type.value}")
    
    def wrap_method(self, component: str, method_name: str):
        """Decorator to wrap methods with fault injection"""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                with self.inject_fault(component, method_name) as injector:
                    if injector:
                        return await injector.inject(func, *args, **kwargs)
                    return await func(*args, **kwargs)
            
            def sync_wrapper(*args, **kwargs):
                with self.inject_fault(component, method_name) as injector:
                    if injector:
                        return injector.inject(func, *args, **kwargs)
                    return func(*args, **kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    def get_fault_events(self, component: Optional[str] = None, 
                        fault_type: Optional[FaultType] = None) -> List[FaultEvent]:
        """Get fault injection events"""
        events = self._fault_events
        
        if component:
            events = [e for e in events if e.component == component]
        
        if fault_type:
            events = [e for e in events if e.fault_type == fault_type]
        
        return events
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fault injection statistics"""
        if not self._fault_events:
            return {"total_faults": 0}
        
        total = len(self._fault_events)
        by_type = {}
        by_component = {}
        avg_recovery_times = {}
        
        for event in self._fault_events:
            # Count by type
            fault_name = event.fault_type.value
            by_type[fault_name] = by_type.get(fault_name, 0) + 1
            
            # Count by component
            by_component[event.component] = by_component.get(event.component, 0) + 1
            
            # Track recovery times
            if event.recovery_time_ms:
                if fault_name not in avg_recovery_times:
                    avg_recovery_times[fault_name] = []
                avg_recovery_times[fault_name].append(event.recovery_time_ms)
        
        # Calculate averages
        for fault_type, times in avg_recovery_times.items():
            avg_recovery_times[fault_type] = sum(times) / len(times)
        
        return {
            "total_faults": total,
            "by_type": by_type,
            "by_component": by_component,
            "avg_recovery_times_ms": avg_recovery_times
        }
    
    def clear_events(self):
        """Clear recorded fault events"""
        self._fault_events.clear()


# Test scenarios aligned with QA patterns
class FaultScenarios:
    """Pre-defined fault scenarios for testing"""
    
    @staticmethod
    def parameter_extraction_faults() -> List[FaultConfig]:
        """Faults for testing parameter extraction reliability"""
        return [
            FaultConfig(
                fault_type=FaultType.DATA_CORRUPTION,
                probability=0.2,
                metadata={"target": "workflow_json"}
            ),
            FaultConfig(
                fault_type=FaultType.EXCEPTION,
                probability=0.1,
                exception_type=KeyError,
                metadata={"target": "node_parsing"}
            ),
            FaultConfig(
                fault_type=FaultType.STATE_INCONSISTENCY,
                probability=0.15,
                metadata={"target": "parameter_cache"}
            )
        ]
    
    @staticmethod
    def ui_sync_faults() -> List[FaultConfig]:
        """Faults for testing UI synchronization"""
        return [
            FaultConfig(
                fault_type=FaultType.CONCURRENCY_ISSUE,
                probability=0.25,
                metadata={"target": "ui_update"}
            ),
            FaultConfig(
                fault_type=FaultType.OBSERVER_FAILURE,
                probability=0.15,
                metadata={"target": "signal_emission"}
            ),
            FaultConfig(
                fault_type=FaultType.TIMEOUT,
                probability=0.1,
                delay_ms=5000,
                metadata={"target": "ui_refresh"}
            )
        ]
    
    @staticmethod
    def observer_pattern_faults() -> List[FaultConfig]:
        """Faults for testing observer pattern resilience"""
        return [
            FaultConfig(
                fault_type=FaultType.OBSERVER_FAILURE,
                probability=0.3,
                metadata={"target": "observer_notification"}
            ),
            FaultConfig(
                fault_type=FaultType.EXCEPTION,
                probability=0.2,
                exception_type=RuntimeError,
                metadata={"target": "observer_callback"}
            ),
            FaultConfig(
                fault_type=FaultType.CONCURRENCY_ISSUE,
                probability=0.15,
                metadata={"target": "observer_list_modification"}
            )
        ]
    
    @staticmethod
    def config_management_faults() -> List[FaultConfig]:
        """Faults for testing configuration management"""
        return [
            FaultConfig(
                fault_type=FaultType.CONFIG_DRIFT,
                probability=0.2,
                metadata={"target": "config_sync"}
            ),
            FaultConfig(
                fault_type=FaultType.DATA_CORRUPTION,
                probability=0.1,
                metadata={"target": "config_values"}
            ),
            FaultConfig(
                fault_type=FaultType.STATE_INCONSISTENCY,
                probability=0.15,
                metadata={"target": "config_layers"}
            )
        ]


# Global instance
_fault_manager = None


def get_fault_injection_manager() -> FaultInjectionManager:
    """Get the global fault injection manager"""
    global _fault_manager
    if _fault_manager is None:
        _fault_manager = FaultInjectionManager()
    return _fault_manager