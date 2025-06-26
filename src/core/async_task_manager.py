"""
Async Task Management System for comfy2c4d

Prevents "RuntimeError: Task was destroyed but it is pending" issues
by properly managing async task lifecycle and preventing conflicts.
"""

import asyncio
import weakref
from typing import Dict, Optional, Any, Callable, Set
from loguru import logger
from datetime import datetime, timedelta


class AsyncTaskManager:
    """
    Centralized async task management to prevent RuntimeError crashes.
    
    Key features:
    - Exclusive task execution (cancels previous instances)
    - Proper task cleanup on application shutdown
    - Thread-safe operations
    - Task timeout handling
    """
    
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_registry: Set[asyncio.Task] = set()
        self._cleanup_interval = 30  # seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
    async def execute_exclusive(self, task_id: str, coro, timeout: Optional[float] = None) -> Any:
        """
        Execute a coroutine exclusively - cancels any previous instance with same task_id.
        
        Args:
            task_id: Unique identifier for this task type
            coro: Coroutine to execute
            timeout: Optional timeout in seconds
            
        Returns:
            Result of the coroutine execution
            
        Raises:
            asyncio.TimeoutError: If timeout is exceeded
            asyncio.CancelledError: If task was cancelled
        """
        # Cancel any existing task with same ID
        if task_id in self.active_tasks:
            old_task = self.active_tasks[task_id]
            if not old_task.done():
                logger.debug(f"Cancelling previous task: {task_id}")
                old_task.cancel()
                try:
                    await old_task
                except asyncio.CancelledError:
                    pass
        
        # Create and register new task
        if timeout:
            task = asyncio.create_task(asyncio.wait_for(coro, timeout=timeout))
        else:
            task = asyncio.create_task(coro)
            
        self.active_tasks[task_id] = task
        self.task_registry.add(task)
        
        try:
            result = await task
            logger.debug(f"Task completed successfully: {task_id}")
            return result
        except asyncio.CancelledError:
            logger.debug(f"Task was cancelled: {task_id}")
            raise
        except Exception as e:
            logger.error(f"Task failed: {task_id} - {e}")
            raise
        finally:
            # Cleanup
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            self.task_registry.discard(task)
    
    async def execute_background(self, task_id: str, coro, timeout: Optional[float] = None) -> asyncio.Task:
        """
        Execute a coroutine in the background without waiting for completion.
        
        Args:
            task_id: Unique identifier for this task type
            coro: Coroutine to execute
            timeout: Optional timeout in seconds
            
        Returns:
            The created asyncio.Task
        """
        # Cancel any existing task with same ID
        if task_id in self.active_tasks:
            old_task = self.active_tasks[task_id]
            if not old_task.done():
                logger.debug(f"Cancelling previous background task: {task_id}")
                old_task.cancel()
                # Wait briefly for cancellation to complete
                try:
                    await asyncio.sleep(0.01)  # Allow cancellation to process
                except:
                    pass
        
        # Create and register new task
        if timeout:
            task = asyncio.create_task(asyncio.wait_for(coro, timeout=timeout))
        else:
            task = asyncio.create_task(coro)
            
        self.active_tasks[task_id] = task
        self.task_registry.add(task)
        
        # Add completion callback for cleanup
        def cleanup_callback(finished_task):
            try:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                self.task_registry.discard(finished_task)
                
                if finished_task.cancelled():
                    logger.debug(f"Background task was cancelled: {task_id}")
                elif finished_task.exception():
                    logger.error(f"Background task failed: {task_id} - {finished_task.exception()}")
                else:
                    logger.debug(f"Background task completed: {task_id}")
            except Exception as e:
                logger.debug(f"Cleanup callback error for {task_id}: {e}")
        
        task.add_done_callback(cleanup_callback)
        return task
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a specific task by ID.
        
        Args:
            task_id: Task identifier to cancel
            
        Returns:
            True if task was found and cancelled, False otherwise
        """
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if not task.done():
                task.cancel()
                logger.debug(f"Cancelled task: {task_id}")
                return True
        return False
    
    def cancel_all_tasks(self):
        """Cancel all active tasks."""
        cancelled_count = 0
        for task_id, task in list(self.active_tasks.items()):
            if not task.done():
                task.cancel()
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} active tasks")
    
    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks."""
        return len([task for task in self.active_tasks.values() if not task.done()])
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get the status of a specific task.
        
        Returns:
            'running', 'completed', 'cancelled', 'failed', or None if not found
        """
        if task_id not in self.active_tasks:
            return None
            
        task = self.active_tasks[task_id]
        if task.done():
            if task.cancelled():
                return 'cancelled'
            elif task.exception():
                return 'failed'
            else:
                return 'completed'
        else:
            return 'running'
    
    async def start_cleanup_task(self):
        """Start the periodic cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodically clean up completed tasks."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up completed tasks
                completed_tasks = []
                for task_id, task in list(self.active_tasks.items()):
                    if task.done():
                        completed_tasks.append(task_id)
                
                for task_id in completed_tasks:
                    del self.active_tasks[task_id]
                
                # Clean up task registry
                self.task_registry = {task for task in self.task_registry if not task.done()}
                
                if completed_tasks:
                    logger.debug(f"Cleaned up {len(completed_tasks)} completed tasks")
                
                # Wait before next cleanup
                await asyncio.sleep(self._cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task cleanup: {e}")
                await asyncio.sleep(self._cleanup_interval)
    
    async def shutdown(self):
        """Shutdown the task manager and clean up all tasks."""
        logger.info("Shutting down AsyncTaskManager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        # Cancel all active tasks
        self.cancel_all_tasks()
        
        # Wait for tasks to complete cancellation
        if self.task_registry:
            await asyncio.gather(*self.task_registry, return_exceptions=True)
        
        logger.info("AsyncTaskManager shutdown complete")


# Global task manager instance
_task_manager = None


def get_task_manager() -> AsyncTaskManager:
    """Get the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
    return _task_manager


# Convenience functions for common patterns
async def execute_texture_workflow(workflow_data: Dict[str, Any], timeout: float = 300) -> Any:
    """
    Execute texture generation workflow exclusively.
    Prevents multiple simultaneous texture workflows that cause RuntimeError.
    """
    task_manager = get_task_manager()
    return await task_manager.execute_exclusive(
        "texture_workflow", 
        _execute_texture_workflow_impl(workflow_data),
        timeout=timeout
    )


async def execute_model_generation(workflow_data: Dict[str, Any], timeout: float = 600) -> Any:
    """
    Execute 3D model generation workflow exclusively.
    """
    task_manager = get_task_manager()
    return await task_manager.execute_exclusive(
        "model_generation",
        _execute_model_generation_impl(workflow_data),
        timeout=timeout
    )


# Implementation stubs - these will be replaced with actual workflow execution
async def _execute_texture_workflow_impl(workflow_data: Dict[str, Any]) -> Any:
    """Implementation for texture workflow execution."""
    try:
        # Import the necessary components
        from loguru import logger
        
        # For now, this is a placeholder that logs the workflow execution
        # The actual execution happens in app_redesigned._async_generate_textures
        logger.info(f"Executing texture workflow with {len(workflow_data)} nodes")
        
        # The workflow execution is handled by the main app's texture generation system
        # This function serves as a wrapper for the async task manager
        # Real implementation is in app_redesigned._async_generate_textures
        
        return {"status": "queued", "message": "Texture workflow execution delegated to main application"}
        
    except Exception as e:
        logger.error(f"Error in texture workflow execution: {e}")
        raise


async def _execute_model_generation_impl(workflow_data: Dict[str, Any]) -> Any:
    """Implementation stub for model generation workflow execution."""
    # This will be implemented by integrating with existing workflow execution
    pass