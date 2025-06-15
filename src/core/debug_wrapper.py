"""Debug wrapper for Scene Assembly functions"""

import functools
import traceback
import asyncio
import sys
from typing import Any, Callable
from loguru import logger
import threading
import gc

class DebugTracker:
    """Track function calls and memory usage"""
    
    def __init__(self):
        self.call_count = {}
        self.error_count = {}
        self.active_calls = set()
        self.memory_snapshots = []
        
    def track_call(self, func_name: str):
        """Track function call"""
        self.call_count[func_name] = self.call_count.get(func_name, 0) + 1
        self.active_calls.add(func_name)
        logger.debug(f"[CALL TRACK] {func_name} - Call #{self.call_count[func_name]} - Active: {len(self.active_calls)}")
        
    def track_error(self, func_name: str, error: Exception):
        """Track function error"""
        self.error_count[func_name] = self.error_count.get(func_name, 0) + 1
        logger.error(f"[ERROR TRACK] {func_name} - Error #{self.error_count[func_name]}: {error}")
        
    def track_complete(self, func_name: str):
        """Track function completion"""
        self.active_calls.discard(func_name)
        logger.debug(f"[COMPLETE] {func_name} - Active calls remaining: {len(self.active_calls)}")
        
    def check_memory(self):
        """Check memory usage"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.debug(f"[MEMORY] Current usage: {memory_mb:.2f} MB")
        return memory_mb

# Global debug tracker
debug_tracker = DebugTracker()

def debug_scene_assembly(func: Callable) -> Callable:
    """Decorator to debug Scene Assembly functions"""
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"[DEBUG] Calling {func_name} with args={args[1:]} kwargs={kwargs}")
        
        # Track the call
        debug_tracker.track_call(func_name)
        
        # Check thread info
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        logger.debug(f"[THREAD] {func_name} running on thread {thread_name} (ID: {thread_id})")
        
        # Check memory before (only occasionally to reduce noise)
        mem_before = debug_tracker.check_memory() if debug_tracker.call_count.get(func_name, 0) % 10 == 1 else None
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Check memory after (only occasionally)
            if mem_before is not None:
                mem_after = debug_tracker.check_memory()
                mem_diff = mem_after - mem_before
                if mem_diff > 10:  # Alert if memory increased by more than 10MB
                    logger.warning(f"[MEMORY LEAK?] {func_name} increased memory by {mem_diff:.2f} MB")
            
            logger.debug(f"[SUCCESS] {func_name} completed successfully")
            return result
            
        except Exception as e:
            # Track the error
            debug_tracker.track_error(func_name, e)
            
            # Log full traceback
            logger.error(f"[CRASH] {func_name} crashed with error: {e}")
            logger.error(f"[TRACEBACK]\n{traceback.format_exc()}")
            
            # Check if it's a Qt/GUI error
            if "Qt" in str(e) or "QTimer" in str(e):
                logger.error("[CRASH TYPE] Qt/GUI related crash detected")
                
            # Check if it's a threading error
            if "thread" in str(e).lower():
                logger.error("[CRASH TYPE] Threading related crash detected")
                
            # Re-raise the exception
            raise
            
        finally:
            # Track completion
            debug_tracker.track_complete(func_name)
            
            # Force garbage collection to detect memory leaks
            gc.collect()
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.info(f"[DEBUG ASYNC] Calling {func_name} with args={args[1:]} kwargs={kwargs}")
        
        # Track the call
        debug_tracker.track_call(func_name)
        
        # Check event loop info
        try:
            loop = asyncio.get_running_loop()
            logger.debug(f"[EVENT LOOP] {func_name} running on loop: {loop}")
        except RuntimeError:
            logger.warning(f"[EVENT LOOP] No running event loop for {func_name}")
        
        # Check memory before
        mem_before = debug_tracker.check_memory()
        
        try:
            # Call the async function
            result = await func(*args, **kwargs)
            
            # Check memory after
            mem_after = debug_tracker.check_memory()
            mem_diff = mem_after - mem_before
            if mem_diff > 10:  # Alert if memory increased by more than 10MB
                logger.warning(f"[MEMORY LEAK?] {func_name} increased memory by {mem_diff:.2f} MB")
            
            logger.info(f"[SUCCESS ASYNC] {func_name} completed successfully")
            return result
            
        except Exception as e:
            # Track the error
            debug_tracker.track_error(func_name, e)
            
            # Log full traceback
            logger.error(f"[CRASH ASYNC] {func_name} crashed with error: {e}")
            logger.error(f"[TRACEBACK]\n{traceback.format_exc()}")
            
            # Check specific error types
            if isinstance(e, asyncio.CancelledError):
                logger.error("[CRASH TYPE] Async task was cancelled")
            elif isinstance(e, asyncio.TimeoutError):
                logger.error("[CRASH TYPE] Async operation timed out")
                
            # Re-raise the exception
            raise
            
        finally:
            # Track completion
            debug_tracker.track_complete(func_name)
            
            # Force garbage collection
            gc.collect()
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def wrap_scene_assembly_methods(app_instance):
    """Wrap all Scene Assembly methods with debugging"""
    methods_to_wrap = [
        # Sync methods
        '_create_primitive_object',
        '_create_deformer_object',
        '_create_mograph_object',
        '_create_effector_object',
        '_create_tag_object',
        '_create_generator_object',
        '_run_async_task',
        
        # Async methods
        '_execute_create_primitive_object',
        '_execute_create_deformer_object',
        '_execute_create_mograph_object',
        '_execute_create_effector_object',
        '_execute_create_tag_object',
        '_execute_create_generator_object',
    ]
    
    for method_name in methods_to_wrap:
        if hasattr(app_instance, method_name):
            original_method = getattr(app_instance, method_name)
            wrapped_method = debug_scene_assembly(original_method)
            setattr(app_instance, method_name, wrapped_method)
            logger.info(f"[DEBUG WRAPPER] Wrapped method: {method_name}")
    
    return app_instance

def get_debug_report():
    """Get a debug report of all tracked calls"""
    report = []
    report.append("=== DEBUG REPORT ===")
    report.append(f"Total calls: {sum(debug_tracker.call_count.values())}")
    report.append(f"Total errors: {sum(debug_tracker.error_count.values())}")
    report.append(f"Active calls: {len(debug_tracker.active_calls)}")
    
    report.append("\nCall counts:")
    for func, count in debug_tracker.call_count.items():
        report.append(f"  {func}: {count}")
    
    report.append("\nError counts:")
    for func, count in debug_tracker.error_count.items():
        report.append(f"  {func}: {count}")
    
    if debug_tracker.active_calls:
        report.append(f"\nStill active: {debug_tracker.active_calls}")
    
    return "\n".join(report)