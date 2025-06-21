"""
Centralized Resource Management System

Implements the multi-mind analysis recommendation for resource cleanup patterns
to prevent memory leaks and improve system stability.

This module provides centralized management for HTTP clients, file handles,
timers, and other system resources with proper cleanup and monitoring.
"""

import asyncio
import threading
import time
import weakref
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Set, TypeVar
from ..utils.advanced_logging import get_logger

logger = get_logger("resource")
import httpx
from watchdog.observers import Observer


@dataclass
class ResourceInfo:
    """Information about a managed resource"""
    resource_id: str
    resource_type: str
    created_at: float
    last_accessed: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    cleanup_callback: Optional[callable] = None


class ManagedResource(ABC):
    """Abstract base class for managed resources"""
    
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.created_at = time.time()
        self.last_accessed = time.time()
        self._is_cleaned_up = False
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup the resource"""
        pass
    
    def touch(self) -> None:
        """Update last accessed time"""
        self.last_accessed = time.time()
    
    @property
    def is_cleaned_up(self) -> bool:
        return self._is_cleaned_up
    
    def mark_cleaned_up(self) -> None:
        self._is_cleaned_up = True


class HTTPClientResource(ManagedResource):
    """Managed HTTP client resource"""
    
    def __init__(self, resource_id: str, client: httpx.AsyncClient):
        super().__init__(resource_id)
        self.client = client
    
    async def cleanup(self) -> None:
        """Close HTTP client"""
        if not self._is_cleaned_up and self.client:
            try:
                await self.client.aclose()
                logger.debug(f"Closed HTTP client: {self.resource_id}")
            except Exception as e:
                logger.warning(f"Error closing HTTP client {self.resource_id}: {e}")
            finally:
                self.mark_cleaned_up()


class FileMonitorResource(ManagedResource):
    """Managed file monitor resource"""
    
    def __init__(self, resource_id: str, observer: Observer):
        super().__init__(resource_id)
        self.observer = observer
    
    async def cleanup(self) -> None:
        """Stop file monitor"""
        if not self._is_cleaned_up and self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                logger.debug(f"Stopped file monitor: {self.resource_id}")
            except Exception as e:
                logger.warning(f"Error stopping file monitor {self.resource_id}: {e}")
            finally:
                self.mark_cleaned_up()


class TimerResource(ManagedResource):
    """Managed timer resource"""
    
    def __init__(self, resource_id: str, timer: Any):
        super().__init__(resource_id)
        self.timer = timer
    
    async def cleanup(self) -> None:
        """Stop timer"""
        if not self._is_cleaned_up and self.timer:
            try:
                if hasattr(self.timer, 'stop'):
                    self.timer.stop()
                elif hasattr(self.timer, 'cancel'):
                    self.timer.cancel()
                logger.debug(f"Stopped timer: {self.resource_id}")
            except Exception as e:
                logger.warning(f"Error stopping timer {self.resource_id}: {e}")
            finally:
                self.mark_cleaned_up()


class TaskResource(ManagedResource):
    """Managed asyncio task resource"""
    
    def __init__(self, resource_id: str, task: asyncio.Task):
        super().__init__(resource_id)
        self.task = task
    
    async def cleanup(self) -> None:
        """Cancel task"""
        if not self._is_cleaned_up and self.task and not self.task.done():
            try:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                logger.debug(f"Cancelled task: {self.resource_id}")
            except Exception as e:
                logger.warning(f"Error cancelling task {self.resource_id}: {e}")
            finally:
                self.mark_cleaned_up()


class ResourcePool:
    """Pool for managing resources of a specific type"""
    
    def __init__(self, 
                 pool_name: str,
                 max_size: Optional[int] = None,
                 idle_timeout: float = 300.0):  # 5 minutes
        self.pool_name = pool_name
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self.resources: Dict[str, ManagedResource] = {}
        self._lock = threading.RLock()
    
    def add_resource(self, resource: ManagedResource) -> None:
        """Add resource to pool"""
        with self._lock:
            if self.max_size and len(self.resources) >= self.max_size:
                # Remove oldest resource
                oldest_id = min(self.resources.keys(), 
                              key=lambda k: self.resources[k].last_accessed)
                old_resource = self.resources.pop(oldest_id)
                asyncio.create_task(old_resource.cleanup())
                logger.debug(f"Evicted resource from pool {self.pool_name}: {oldest_id}")
            
            self.resources[resource.resource_id] = resource
            logger.debug(f"Added resource to pool {self.pool_name}: {resource.resource_id}")
    
    def get_resource(self, resource_id: str) -> Optional[ManagedResource]:
        """Get resource by ID"""
        with self._lock:
            resource = self.resources.get(resource_id)
            if resource:
                resource.touch()
            return resource
    
    def remove_resource(self, resource_id: str) -> Optional[ManagedResource]:
        """Remove resource from pool"""
        with self._lock:
            return self.resources.pop(resource_id, None)
    
    async def cleanup_idle_resources(self) -> int:
        """Cleanup idle resources beyond timeout"""
        current_time = time.time()
        idle_resources = []
        
        with self._lock:
            for resource_id, resource in list(self.resources.items()):
                if current_time - resource.last_accessed > self.idle_timeout:
                    idle_resources.append(resource_id)
        
        # Cleanup idle resources
        cleaned_count = 0
        for resource_id in idle_resources:
            resource = self.remove_resource(resource_id)
            if resource:
                await resource.cleanup()
                cleaned_count += 1
                logger.debug(f"Cleaned up idle resource: {resource_id}")
        
        return cleaned_count
    
    async def cleanup_all(self) -> None:
        """Cleanup all resources in pool"""
        with self._lock:
            resources_to_cleanup = list(self.resources.values())
            self.resources.clear()
        
        for resource in resources_to_cleanup:
            await resource.cleanup()
        
        logger.info(f"Cleaned up all resources in pool: {self.pool_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            current_time = time.time()
            idle_count = sum(1 for r in self.resources.values() 
                           if current_time - r.last_accessed > self.idle_timeout)
            
            return {
                "pool_name": self.pool_name,
                "total_resources": len(self.resources),
                "idle_resources": idle_count,
                "max_size": self.max_size,
                "idle_timeout": self.idle_timeout
            }


class CentralizedResourceManager:
    """
    Centralized resource manager for the entire application
    
    Implements the multi-mind analysis recommendation for centralized
    resource cleanup to prevent memory leaks and improve stability.
    """
    
    def __init__(self):
        self.pools: Dict[str, ResourcePool] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 60.0  # 1 minute
        self._shutdown_event = asyncio.Event()
        self._lock = threading.RLock()
        
        # Setup default pools
        self._setup_default_pools()
    
    def _setup_default_pools(self):
        """Setup default resource pools"""
        self.pools["http_clients"] = ResourcePool(
            "http_clients", 
            max_size=10, 
            idle_timeout=300.0
        )
        self.pools["file_monitors"] = ResourcePool(
            "file_monitors", 
            max_size=20, 
            idle_timeout=600.0
        )
        self.pools["timers"] = ResourcePool(
            "timers", 
            max_size=50, 
            idle_timeout=120.0
        )
        self.pools["tasks"] = ResourcePool(
            "tasks", 
            max_size=100, 
            idle_timeout=60.0
        )
    
    def start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started resource cleanup task")
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._periodic_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _periodic_cleanup(self):
        """Perform periodic cleanup of idle resources"""
        total_cleaned = 0
        
        for pool_name, pool in self.pools.items():
            try:
                cleaned = await pool.cleanup_idle_resources()
                total_cleaned += cleaned
            except Exception as e:
                logger.error(f"Error cleaning up pool {pool_name}: {e}")
        
        if total_cleaned > 0:
            logger.debug(f"Periodic cleanup: removed {total_cleaned} idle resources")
    
    # HTTP Client Management
    
    def create_http_client(self, 
                          client_id: str, 
                          timeout: float = 30.0,
                          **kwargs) -> httpx.AsyncClient:
        """Create and register HTTP client"""
        client = httpx.AsyncClient(timeout=timeout, **kwargs)
        resource = HTTPClientResource(client_id, client)
        self.pools["http_clients"].add_resource(resource)
        logger.debug(f"Created HTTP client: {client_id}")
        return client
    
    def get_http_client(self, client_id: str) -> Optional[httpx.AsyncClient]:
        """Get existing HTTP client"""
        resource = self.pools["http_clients"].get_resource(client_id)
        return resource.client if resource else None
    
    async def close_http_client(self, client_id: str) -> None:
        """Close specific HTTP client"""
        resource = self.pools["http_clients"].remove_resource(client_id)
        if resource:
            await resource.cleanup()
    
    # File Monitor Management
    
    def register_file_monitor(self, monitor_id: str, observer: Observer) -> None:
        """Register file monitor for management"""
        resource = FileMonitorResource(monitor_id, observer)
        self.pools["file_monitors"].add_resource(resource)
        logger.debug(f"Registered file monitor: {monitor_id}")
    
    async def stop_file_monitor(self, monitor_id: str) -> None:
        """Stop specific file monitor"""
        resource = self.pools["file_monitors"].remove_resource(monitor_id)
        if resource:
            await resource.cleanup()
    
    # Timer Management
    
    def register_timer(self, timer_id: str, timer: Any) -> None:
        """Register timer for management"""
        resource = TimerResource(timer_id, timer)
        self.pools["timers"].add_resource(resource)
        logger.debug(f"Registered timer: {timer_id}")
    
    async def stop_timer(self, timer_id: str) -> None:
        """Stop specific timer"""
        resource = self.pools["timers"].remove_resource(timer_id)
        if resource:
            await resource.cleanup()
    
    # Task Management
    
    def register_task(self, task_id: str, task: asyncio.Task) -> None:
        """Register asyncio task for management"""
        resource = TaskResource(task_id, task)
        self.pools["tasks"].add_resource(resource)
        logger.debug(f"Registered task: {task_id}")
    
    async def cancel_task(self, task_id: str) -> None:
        """Cancel specific task"""
        resource = self.pools["tasks"].remove_resource(task_id)
        if resource:
            await resource.cleanup()
    
    # Context Managers
    
    @asynccontextmanager
    async def managed_http_client(self, 
                                  client_id: str,
                                  timeout: float = 30.0,
                                  **kwargs) -> AsyncIterator[httpx.AsyncClient]:
        """Context manager for HTTP client with automatic cleanup"""
        client = self.create_http_client(client_id, timeout, **kwargs)
        try:
            yield client
        finally:
            await self.close_http_client(client_id)
    
    @contextmanager
    def managed_timer(self, timer_id: str, timer: Any) -> Iterator[Any]:
        """Context manager for timer with automatic cleanup"""
        self.register_timer(timer_id, timer)
        try:
            yield timer
        finally:
            asyncio.create_task(self.stop_timer(timer_id))
    
    # Utility Methods
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics"""
        stats = {
            "total_pools": len(self.pools),
            "cleanup_task_running": self._cleanup_task and not self._cleanup_task.done(),
            "pools": {}
        }
        
        for pool_name, pool in self.pools.items():
            stats["pools"][pool_name] = pool.get_stats()
        
        return stats
    
    async def force_cleanup_all(self) -> None:
        """Force cleanup of all resources immediately"""
        logger.info("Starting forced cleanup of all resources")
        
        for pool_name, pool in self.pools.items():
            try:
                await pool.cleanup_all()
            except Exception as e:
                logger.error(f"Error during forced cleanup of pool {pool_name}: {e}")
        
        logger.info("Forced cleanup completed")
    
    async def shutdown(self) -> None:
        """Shutdown resource manager"""
        logger.info("Shutting down resource manager")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup all resources
        await self.force_cleanup_all()
        
        logger.info("Resource manager shutdown complete")


# Global resource manager instance
resource_manager = CentralizedResourceManager()


# Convenience functions for common patterns

@asynccontextmanager
async def managed_http_session(session_id: str, 
                             timeout: float = 30.0,
                             **kwargs) -> AsyncIterator[httpx.AsyncClient]:
    """Convenience context manager for HTTP sessions"""
    async with resource_manager.managed_http_client(session_id, timeout, **kwargs) as client:
        yield client


def auto_register_timer(timer_id: str):
    """Decorator to automatically register QTimer instances"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            timer = func(*args, **kwargs)
            if hasattr(timer, 'timeout'):  # QTimer-like object
                resource_manager.register_timer(timer_id, timer)
            return timer
        return wrapper
    return decorator


def auto_register_task(task_id: str):
    """Decorator to automatically register asyncio tasks"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            task = func(*args, **kwargs)
            if isinstance(task, asyncio.Task):
                resource_manager.register_task(task_id, task)
            return task
        return wrapper
    return decorator


# Integration with application lifecycle

async def initialize_resource_management():
    """Initialize resource management system"""
    resource_manager.start_cleanup_task()
    logger.info("Resource management system initialized")


async def cleanup_resources_on_exit():
    """Cleanup resources on application exit"""
    await resource_manager.shutdown()
    logger.info("Resources cleaned up on exit")