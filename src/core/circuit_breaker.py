"""
Circuit Breaker Pattern Implementation for comfy2c4d

Prevents cascading failures in observer notification chains and
provides fault isolation for critical components.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Generic
from threading import Lock
from loguru import logger
from PySide6.QtCore import QObject, Signal, QTimer


T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    half_open_requests: int = 1
    excluded_exceptions: Set[type] = field(default_factory=set)
    fallback_function: Optional[Callable] = None
    monitor_function: Optional[Callable] = None


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: List[tuple] = field(default_factory=list)


class CircuitBreaker(Generic[T]):
    """
    Generic circuit breaker implementation.
    
    Protects against cascading failures by monitoring failure rates
    and temporarily blocking calls to failing services.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_requests = 0
        self._stats = CircuitBreakerStats()
        self._lock = Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting calls)"""
        return self._state == CircuitState.OPEN
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for function
            
        Returns:
            Function result or fallback value
            
        Raises:
            Exception: If circuit is open and no fallback configured
        """
        with self._lock:
            self._stats.total_calls += 1
            
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self._stats.rejected_calls += 1
                    return self._handle_open_circuit()
            
            # Check if we're in HALF_OPEN state
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_requests >= self.config.half_open_requests:
                    self._stats.rejected_calls += 1
                    return self._handle_open_circuit()
                self._half_open_requests += 1
        
        # Try to execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if type(e) not in self.config.excluded_exceptions:
                self._on_failure(e)
            raise
    
    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Async version of call"""
        with self._lock:
            self._stats.total_calls += 1
            
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self._stats.rejected_calls += 1
                    return self._handle_open_circuit()
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_requests >= self.config.half_open_requests:
                    self._stats.rejected_calls += 1
                    return self._handle_open_circuit()
                self._half_open_requests += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if type(e) not in self.config.excluded_exceptions:
                self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (self._last_failure_time and 
                time.time() - self._last_failure_time >= self.config.timeout_seconds)
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self._stats.successful_calls += 1
            self._stats.last_success_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        with self._lock:
            self._stats.failed_calls += 1
            self._stats.last_failure_time = datetime.now()
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self._state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            
            if self.config.monitor_function:
                try:
                    self.config.monitor_function(self.name, exception)
                except:
                    pass
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        logger.warning(f"Circuit breaker '{self.name}' opening")
        self._state = CircuitState.OPEN
        self._stats.state_changes.append((datetime.now(), CircuitState.OPEN))
        self._half_open_requests = 0
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        logger.info(f"Circuit breaker '{self.name}' closing")
        self._state = CircuitState.CLOSED
        self._stats.state_changes.append((datetime.now(), CircuitState.CLOSED))
        self._failure_count = 0
        self._success_count = 0
        self._half_open_requests = 0
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        logger.info(f"Circuit breaker '{self.name}' half-opening")
        self._state = CircuitState.HALF_OPEN
        self._stats.state_changes.append((datetime.now(), CircuitState.HALF_OPEN))
        self._success_count = 0
        self._failure_count = 0
        self._half_open_requests = 0
    
    def _handle_open_circuit(self):
        """Handle call when circuit is open"""
        if self.config.fallback_function:
            return self.config.fallback_function()
        raise Exception(f"Circuit breaker '{self.name}' is open")
    
    def reset(self):
        """Manually reset the circuit breaker"""
        with self._lock:
            self._transition_to_closed()
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics"""
        return self._stats


class ObserverChainBreaker(QObject):
    """
    Specialized circuit breaker for observer notification chains.
    
    Prevents cascading failures when observers throw exceptions
    during notification.
    """
    
    # Signals
    observer_failed = Signal(str, str)  # observer_id, error
    chain_broken = Signal(str)  # chain_id
    chain_recovered = Signal(str)  # chain_id
    
    def __init__(self):
        super().__init__()
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._observer_failures: Dict[str, int] = {}
        self._chain_configs: Dict[str, CircuitBreakerConfig] = {}
        
        # Default configuration for observer chains
        self._default_config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=30.0,
            half_open_requests=1,
            excluded_exceptions={KeyboardInterrupt, SystemExit},
            fallback_function=self._log_fallback
        )
    
    def configure_chain(self, chain_id: str, config: Optional[CircuitBreakerConfig] = None):
        """Configure circuit breaker for an observer chain"""
        self._chain_configs[chain_id] = config or self._default_config
        self._breakers[chain_id] = CircuitBreaker(
            name=f"observer_chain_{chain_id}",
            config=self._chain_configs[chain_id]
        )
    
    def notify_observers(self, chain_id: str, observers: List[Callable], *args, **kwargs):
        """
        Safely notify all observers in a chain.
        
        Args:
            chain_id: Identifier for the observer chain
            observers: List of observer callbacks
            *args, **kwargs: Arguments to pass to observers
        """
        if chain_id not in self._breakers:
            self.configure_chain(chain_id)
        
        breaker = self._breakers[chain_id]
        successful_notifications = 0
        failed_observers = []
        
        for i, observer in enumerate(observers):
            observer_id = f"{chain_id}_{i}"
            
            try:
                # Check if this specific observer has failed too many times
                if self._observer_failures.get(observer_id, 0) >= 5:
                    logger.debug(f"Skipping permanently failed observer: {observer_id}")
                    continue
                
                # Use circuit breaker for the entire chain
                if breaker.is_open:
                    logger.debug(f"Circuit open for chain {chain_id}, using fallback")
                    self._notify_fallback(observer_id, *args, **kwargs)
                    continue
                
                # Execute observer notification
                breaker.call(self._execute_observer, observer, observer_id, *args, **kwargs)
                successful_notifications += 1
                
                # Reset failure count on success
                if observer_id in self._observer_failures:
                    self._observer_failures[observer_id] = 0
                    
            except Exception as e:
                failed_observers.append((observer_id, str(e)))
                self._observer_failures[observer_id] = self._observer_failures.get(observer_id, 0) + 1
                self.observer_failed.emit(observer_id, str(e))
                logger.error(f"Observer {observer_id} failed: {e}")
        
        # Check if chain is broken
        if failed_observers and breaker.is_open:
            self.chain_broken.emit(chain_id)
        elif successful_notifications > 0 and breaker.is_closed:
            self.chain_recovered.emit(chain_id)
        
        logger.debug(f"Chain {chain_id}: {successful_notifications}/{len(observers)} observers notified")
    
    async def notify_observers_async(self, chain_id: str, observers: List[Callable], *args, **kwargs):
        """Async version of notify_observers"""
        if chain_id not in self._breakers:
            self.configure_chain(chain_id)
        
        breaker = self._breakers[chain_id]
        tasks = []
        
        for i, observer in enumerate(observers):
            observer_id = f"{chain_id}_{i}"
            
            if self._observer_failures.get(observer_id, 0) >= 5:
                continue
            
            if breaker.is_open:
                await self._notify_fallback_async(observer_id, *args, **kwargs)
                continue
            
            task = asyncio.create_task(
                self._execute_observer_async(breaker, observer, observer_id, *args, **kwargs)
            )
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if not isinstance(r, Exception))
            if successful > 0 and breaker.is_closed:
                self.chain_recovered.emit(chain_id)
    
    def _execute_observer(self, observer: Callable, observer_id: str, *args, **kwargs):
        """Execute a single observer callback"""
        return observer(*args, **kwargs)
    
    async def _execute_observer_async(self, breaker: CircuitBreaker, observer: Callable, 
                                     observer_id: str, *args, **kwargs):
        """Execute a single observer callback asynchronously"""
        try:
            if asyncio.iscoroutinefunction(observer):
                result = await breaker.call_async(observer, *args, **kwargs)
            else:
                result = await breaker.call_async(
                    lambda: observer(*args, **kwargs)
                )
            
            if observer_id in self._observer_failures:
                self._observer_failures[observer_id] = 0
                
            return result
            
        except Exception as e:
            self._observer_failures[observer_id] = self._observer_failures.get(observer_id, 0) + 1
            self.observer_failed.emit(observer_id, str(e))
            raise
    
    def _notify_fallback(self, observer_id: str, *args, **kwargs):
        """Fallback notification when circuit is open"""
        logger.debug(f"Fallback notification for {observer_id}")
    
    async def _notify_fallback_async(self, observer_id: str, *args, **kwargs):
        """Async fallback notification"""
        logger.debug(f"Async fallback notification for {observer_id}")
    
    def _log_fallback(self):
        """Default fallback function"""
        logger.debug("Circuit breaker fallback executed")
    
    def get_chain_stats(self, chain_id: str) -> Optional[CircuitBreakerStats]:
        """Get statistics for a specific chain"""
        if chain_id in self._breakers:
            return self._breakers[chain_id].get_stats()
        return None
    
    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all chains"""
        return {
            chain_id: breaker.get_stats() 
            for chain_id, breaker in self._breakers.items()
        }
    
    def reset_chain(self, chain_id: str):
        """Reset circuit breaker for a chain"""
        if chain_id in self._breakers:
            self._breakers[chain_id].reset()
            # Clear observer failures for this chain
            to_clear = [k for k in self._observer_failures.keys() if k.startswith(chain_id)]
            for k in to_clear:
                del self._observer_failures[k]


# Global instance
_observer_chain_breaker = None


def get_observer_chain_breaker() -> ObserverChainBreaker:
    """Get the global observer chain breaker"""
    global _observer_chain_breaker
    if _observer_chain_breaker is None:
        _observer_chain_breaker = ObserverChainBreaker()
    return _observer_chain_breaker