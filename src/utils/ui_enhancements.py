"""
UI Responsiveness and User Experience Enhancements

Advanced UI improvements including async operations, progress feedback,
smooth animations, keyboard shortcuts, accessibility, and user preferences.

Part of Phase 3 Quality & Polish - transforms the UI from basic functionality
to a polished, professional user experience.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..utils.advanced_logging import get_logger
from ..utils.performance_monitor import get_performance_monitor, performance_context

logger = get_logger("ui_enhancements")


class UITheme(Enum):
    """Available UI themes"""
    DARK = "dark"
    LIGHT = "light"
    HIGH_CONTRAST = "high_contrast"
    SYSTEM = "system"


class ProgressStyle(Enum):
    """Progress indicator styles"""
    BAR = "bar"
    SPINNER = "spinner"
    DOTS = "dots"
    PULSE = "pulse"


@dataclass
class UIPreferences:
    """User interface preferences"""
    theme: UITheme = UITheme.DARK
    font_size: int = 10
    animation_speed: float = 1.0
    show_tooltips: bool = True
    auto_save_interval: int = 30
    keyboard_shortcuts_enabled: bool = True
    accessibility_mode: bool = False
    progress_style: ProgressStyle = ProgressStyle.BAR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "theme": self.theme.value,
            "font_size": self.font_size,
            "animation_speed": self.animation_speed,
            "show_tooltips": self.show_tooltips,
            "auto_save_interval": self.auto_save_interval,
            "keyboard_shortcuts_enabled": self.keyboard_shortcuts_enabled,
            "accessibility_mode": self.accessibility_mode,
            "progress_style": self.progress_style.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIPreferences':
        """Create from dictionary"""
        return cls(
            theme=UITheme(data.get("theme", "dark")),
            font_size=data.get("font_size", 10),
            animation_speed=data.get("animation_speed", 1.0),
            show_tooltips=data.get("show_tooltips", True),
            auto_save_interval=data.get("auto_save_interval", 30),
            keyboard_shortcuts_enabled=data.get("keyboard_shortcuts_enabled", True),
            accessibility_mode=data.get("accessibility_mode", False),
            progress_style=ProgressStyle(data.get("progress_style", "bar"))
        )


class KeyboardShortcut:
    """Keyboard shortcut definition"""
    
    def __init__(self, key: str, action: Callable, description: str, context: str = "global"):
        self.key = key
        self.action = action
        self.description = description
        self.context = context


class ProgressTracker:
    """Tracks and manages progress indicators"""
    
    def __init__(self):
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.progress_callbacks: List[Callable[[str, int, str], None]] = []
    
    def start_operation(self, operation_id: str, title: str, total_steps: int = 100):
        """Start tracking an operation"""
        self.active_operations[operation_id] = {
            "title": title,
            "progress": 0,
            "total_steps": total_steps,
            "start_time": time.time(),
            "current_step": "",
            "is_indeterminate": total_steps == 0
        }
        
        self._notify_progress(operation_id, 0, f"Starting {title}")
        logger.debug(f"Progress tracking started: {title}", operation_id=operation_id)
    
    def update_progress(self, operation_id: str, progress: int, step_description: str = ""):
        """Update operation progress"""
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        operation["progress"] = max(0, min(progress, operation["total_steps"]))
        operation["current_step"] = step_description
        
        self._notify_progress(operation_id, progress, step_description)
    
    def complete_operation(self, operation_id: str, success: bool = True):
        """Complete operation tracking"""
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        duration = time.time() - operation["start_time"]
        
        if success:
            self._notify_progress(operation_id, operation["total_steps"], "Completed")
            logger.info(f"Operation completed: {operation['title']}", 
                       duration=f"{duration:.1f}s", operation_id=operation_id)
        else:
            self._notify_progress(operation_id, 0, "Failed")
            logger.warning(f"Operation failed: {operation['title']}", 
                          duration=f"{duration:.1f}s", operation_id=operation_id)
        
        # Remove from active operations after a delay to show completion
        asyncio.create_task(self._cleanup_operation(operation_id, 2.0))
    
    async def _cleanup_operation(self, operation_id: str, delay: float):
        """Clean up completed operation after delay"""
        await asyncio.sleep(delay)
        self.active_operations.pop(operation_id, None)
    
    def _notify_progress(self, operation_id: str, progress: int, step: str):
        """Notify progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(operation_id, progress, step)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def add_progress_callback(self, callback: Callable[[str, int, str], None]):
        """Add progress update callback"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[str, int, str], None]):
        """Remove progress update callback"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active operations"""
        return self.active_operations.copy()


class NotificationManager:
    """Manages user notifications and messages"""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
        self.notification_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.max_notifications = 50
    
    def show_notification(self, 
                         title: str, 
                         message: str, 
                         notification_type: str = "info",
                         duration: float = 5.0,
                         actions: List[Dict[str, Any]] = None):
        """Show notification to user"""
        notification = {
            "id": str(time.time()),
            "title": title,
            "message": message,
            "type": notification_type,  # info, warning, error, success
            "timestamp": time.time(),
            "duration": duration,
            "actions": actions or []
        }
        
        self.notifications.append(notification)
        
        # Limit notifications
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]
        
        # Notify callbacks
        for callback in self.notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")
        
        logger.info(f"Notification: {title} - {message}", 
                   type=notification_type, duration=duration)
        
        # Auto-dismiss after duration
        if duration > 0:
            asyncio.create_task(self._auto_dismiss(notification["id"], duration))
        
        return notification["id"]
    
    async def _auto_dismiss(self, notification_id: str, delay: float):
        """Auto-dismiss notification after delay"""
        await asyncio.sleep(delay)
        self.dismiss_notification(notification_id)
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss specific notification"""
        self.notifications = [n for n in self.notifications if n["id"] != notification_id]
    
    def clear_all_notifications(self):
        """Clear all notifications"""
        self.notifications.clear()
    
    def add_notification_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add notification callback"""
        self.notification_callbacks.append(callback)
    
    def get_recent_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent notifications"""
        return self.notifications[-limit:]


class AsyncOperationManager:
    """Manages async operations with UI feedback"""
    
    def __init__(self, progress_tracker: ProgressTracker, notification_manager: NotificationManager):
        self.progress_tracker = progress_tracker
        self.notification_manager = notification_manager
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def run_async_operation(self,
                                 operation_id: str,
                                 operation: Callable,
                                 title: str,
                                 show_progress: bool = True,
                                 show_notifications: bool = True,
                                 *args, **kwargs) -> Any:
        """Run async operation with UI feedback"""
        
        # Start progress tracking
        if show_progress:
            self.progress_tracker.start_operation(operation_id, title)
        
        try:
            # Create and track task
            task = asyncio.create_task(operation(*args, **kwargs))
            self.active_tasks[operation_id] = task
            
            # Wait for completion
            result = await task
            
            # Success feedback
            if show_progress:
                self.progress_tracker.complete_operation(operation_id, success=True)
            
            if show_notifications:
                self.notification_manager.show_notification(
                    "Operation Complete",
                    f"{title} completed successfully",
                    "success",
                    3.0
                )
            
            return result
            
        except asyncio.CancelledError:
            # Operation cancelled
            if show_progress:
                self.progress_tracker.complete_operation(operation_id, success=False)
            
            if show_notifications:
                self.notification_manager.show_notification(
                    "Operation Cancelled",
                    f"{title} was cancelled",
                    "warning",
                    3.0
                )
            raise
            
        except Exception as e:
            # Operation failed
            if show_progress:
                self.progress_tracker.complete_operation(operation_id, success=False)
            
            if show_notifications:
                self.notification_manager.show_notification(
                    "Operation Failed",
                    f"{title} failed: {str(e)}",
                    "error",
                    5.0
                )
            
            logger.error(f"Async operation failed: {title}", error=str(e), operation_id=operation_id)
            raise
            
        finally:
            # Cleanup
            self.active_tasks.pop(operation_id, None)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel active operation"""
        if operation_id in self.active_tasks:
            task = self.active_tasks[operation_id]
            if not task.done():
                task.cancel()
                return True
        return False
    
    def get_active_operations(self) -> List[str]:
        """Get list of active operation IDs"""
        return list(self.active_tasks.keys())


class AccessibilityManager:
    """Manages accessibility features"""
    
    def __init__(self):
        self.high_contrast_enabled = False
        self.screen_reader_enabled = False
        self.keyboard_navigation_enabled = True
        self.focus_indicators_enhanced = False
    
    def enable_high_contrast(self, enabled: bool = True):
        """Enable high contrast mode"""
        self.high_contrast_enabled = enabled
        logger.info(f"High contrast mode {'enabled' if enabled else 'disabled'}")
    
    def enable_screen_reader_support(self, enabled: bool = True):
        """Enable screen reader support"""
        self.screen_reader_enabled = enabled
        logger.info(f"Screen reader support {'enabled' if enabled else 'disabled'}")
    
    def enhance_focus_indicators(self, enabled: bool = True):
        """Enhance focus indicators for keyboard navigation"""
        self.focus_indicators_enhanced = enabled
        logger.info(f"Enhanced focus indicators {'enabled' if enabled else 'disabled'}")
    
    def get_accessibility_stylesheet(self) -> str:
        """Get CSS for accessibility enhancements"""
        styles = []
        
        if self.high_contrast_enabled:
            styles.append("""
                * {
                    background-color: black !important;
                    color: white !important;
                    border-color: white !important;
                }
                QPushButton:hover {
                    background-color: white !important;
                    color: black !important;
                }
            """)
        
        if self.focus_indicators_enhanced:
            styles.append("""
                *:focus {
                    outline: 3px solid #4CAF50 !important;
                    outline-offset: 2px !important;
                }
            """)
        
        return "\n".join(styles)


class ThemeManager:
    """Manages UI themes and styling"""
    
    def __init__(self):
        self.current_theme = UITheme.DARK
        self.custom_themes: Dict[str, Dict[str, str]] = {}
        self.theme_callbacks: List[Callable[[UITheme], None]] = []
    
    def get_theme_stylesheet(self, theme: UITheme) -> str:
        """Get stylesheet for theme"""
        if theme == UITheme.DARK:
            return self._get_dark_theme()
        elif theme == UITheme.LIGHT:
            return self._get_light_theme()
        elif theme == UITheme.HIGH_CONTRAST:
            return self._get_high_contrast_theme()
        else:
            return self._get_dark_theme()  # Default
    
    def _get_dark_theme(self) -> str:
        """Dark theme stylesheet"""
        return """
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4CAF50;
            }
            
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
            
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1e1e1e;
            }
            
            QTabBar::tab {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: #000000;
            }
            
            QLineEdit, QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
            }
            
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
            }
            
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """
    
    def _get_light_theme(self) -> str:
        """Light theme stylesheet"""
        return """
            QMainWindow, QWidget {
                background-color: #ffffff;
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #e5e5e5;
                border-color: #4CAF50;
            }
            
            QPushButton:pressed {
                background-color: #d5d5d5;
            }
            
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
        """
    
    def _get_high_contrast_theme(self) -> str:
        """High contrast theme stylesheet"""
        return """
            QMainWindow, QWidget {
                background-color: #000000;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
            }
            
            QPushButton {
                background-color: #000000;
                border: 2px solid #ffffff;
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 20px;
                color: #ffffff;
            }
            
            QPushButton:hover {
                background-color: #ffffff;
                color: #000000;
            }
            
            QPushButton:focus {
                outline: 3px solid #ffff00;
            }
        """
    
    def set_theme(self, theme: UITheme):
        """Set current theme"""
        self.current_theme = theme
        
        # Notify callbacks
        for callback in self.theme_callbacks:
            try:
                callback(theme)
            except Exception as e:
                logger.error(f"Theme callback error: {e}")
        
        logger.info(f"Theme changed to: {theme.value}")
    
    def add_theme_callback(self, callback: Callable[[UITheme], None]):
        """Add theme change callback"""
        self.theme_callbacks.append(callback)


class KeyboardShortcutManager:
    """Manages keyboard shortcuts"""
    
    def __init__(self):
        self.shortcuts: Dict[str, KeyboardShortcut] = {}
        self.enabled = True
    
    def register_shortcut(self, shortcut: KeyboardShortcut):
        """Register keyboard shortcut"""
        self.shortcuts[shortcut.key] = shortcut
        logger.debug(f"Registered shortcut: {shortcut.key} - {shortcut.description}")
    
    def unregister_shortcut(self, key: str):
        """Unregister keyboard shortcut"""
        if key in self.shortcuts:
            del self.shortcuts[key]
            logger.debug(f"Unregistered shortcut: {key}")
    
    def handle_key_press(self, key: str, context: str = "global") -> bool:
        """Handle key press event"""
        if not self.enabled:
            return False
        
        if key in self.shortcuts:
            shortcut = self.shortcuts[key]
            if shortcut.context == "global" or shortcut.context == context:
                try:
                    shortcut.action()
                    logger.debug(f"Executed shortcut: {key}")
                    return True
                except Exception as e:
                    logger.error(f"Shortcut execution error: {e}")
        
        return False
    
    def get_shortcuts_for_context(self, context: str = "global") -> List[KeyboardShortcut]:
        """Get shortcuts for specific context"""
        return [s for s in self.shortcuts.values() 
                if s.context == context or s.context == "global"]
    
    def enable_shortcuts(self, enabled: bool = True):
        """Enable or disable shortcuts"""
        self.enabled = enabled
        logger.info(f"Keyboard shortcuts {'enabled' if enabled else 'disabled'}")


class UIEnhancementManager:
    """
    Comprehensive UI enhancement system
    
    Provides professional UI/UX improvements including:
    - Async operation management with progress feedback
    - User notifications and messaging
    - Keyboard shortcuts and accessibility
    - Theme management and user preferences
    - Performance-optimized UI operations
    """
    
    def __init__(self):
        # Core managers
        self.progress_tracker = ProgressTracker()
        self.notification_manager = NotificationManager()
        self.async_manager = AsyncOperationManager(self.progress_tracker, self.notification_manager)
        self.accessibility_manager = AccessibilityManager()
        self.theme_manager = ThemeManager()
        self.shortcut_manager = KeyboardShortcutManager()
        
        # User preferences
        self.preferences = UIPreferences()
        
        # Performance monitoring
        self.performance_monitor = get_performance_monitor()
        
        # Setup default shortcuts
        self._setup_default_shortcuts()
        
        logger.info("UI enhancement system initialized")
    
    def _setup_default_shortcuts(self):
        """Setup default keyboard shortcuts"""
        shortcuts = [
            KeyboardShortcut("Ctrl+N", lambda: self.notification_manager.show_notification(
                "New", "New project started", "info"), "New Project"),
            KeyboardShortcut("Ctrl+S", lambda: self.notification_manager.show_notification(
                "Save", "Project saved", "success"), "Save Project"),
            KeyboardShortcut("Ctrl+Z", lambda: self.notification_manager.show_notification(
                "Undo", "Action undone", "info"), "Undo"),
            KeyboardShortcut("Ctrl+Y", lambda: self.notification_manager.show_notification(
                "Redo", "Action redone", "info"), "Redo"),
            KeyboardShortcut("F11", lambda: self.notification_manager.show_notification(
                "Fullscreen", "Toggled fullscreen mode", "info"), "Toggle Fullscreen"),
        ]
        
        for shortcut in shortcuts:
            self.shortcut_manager.register_shortcut(shortcut)
    
    # Async operations with UI feedback
    
    async def run_workflow_async(self, workflow_name: str, workflow_function: Callable, *args, **kwargs) -> Any:
        """Run workflow with progress tracking"""
        operation_id = f"workflow_{int(time.time())}"
        
        with performance_context("ui_enhancement", "async_workflow"):
            return await self.async_manager.run_async_operation(
                operation_id=operation_id,
                operation=workflow_function,
                title=f"Running {workflow_name}",
                show_progress=True,
                show_notifications=True,
                *args, **kwargs
            )
    
    async def load_data_async(self, data_type: str, load_function: Callable, *args, **kwargs) -> Any:
        """Load data with progress tracking"""
        operation_id = f"load_{data_type}_{int(time.time())}"
        
        with performance_context("ui_enhancement", "async_data_load"):
            return await self.async_manager.run_async_operation(
                operation_id=operation_id,
                operation=load_function,
                title=f"Loading {data_type}",
                show_progress=True,
                show_notifications=False,  # Don't notify for data loading
                *args, **kwargs
            )
    
    # User feedback methods
    
    def show_success_message(self, title: str, message: str):
        """Show success notification"""
        self.notification_manager.show_notification(title, message, "success", 3.0)
    
    def show_error_message(self, title: str, message: str):
        """Show error notification"""
        self.notification_manager.show_notification(title, message, "error", 5.0)
    
    def show_warning_message(self, title: str, message: str):
        """Show warning notification"""
        self.notification_manager.show_notification(title, message, "warning", 4.0)
    
    def show_info_message(self, title: str, message: str):
        """Show info notification"""
        self.notification_manager.show_notification(title, message, "info", 3.0)
    
    # Progress tracking
    
    def start_progress(self, operation_id: str, title: str, total_steps: int = 100):
        """Start progress tracking"""
        self.progress_tracker.start_operation(operation_id, title, total_steps)
    
    def update_progress(self, operation_id: str, progress: int, step: str = ""):
        """Update progress"""
        self.progress_tracker.update_progress(operation_id, progress, step)
    
    def complete_progress(self, operation_id: str, success: bool = True):
        """Complete progress tracking"""
        self.progress_tracker.complete_operation(operation_id, success)
    
    # Theme and preferences
    
    def set_theme(self, theme: UITheme):
        """Set UI theme"""
        self.theme_manager.set_theme(theme)
        self.preferences.theme = theme
    
    def get_current_stylesheet(self) -> str:
        """Get current theme stylesheet"""
        base_style = self.theme_manager.get_theme_stylesheet(self.preferences.theme)
        
        if self.preferences.accessibility_mode:
            accessibility_style = self.accessibility_manager.get_accessibility_stylesheet()
            return base_style + "\n" + accessibility_style
        
        return base_style
    
    def update_preferences(self, **preferences):
        """Update user preferences"""
        for key, value in preferences.items():
            if hasattr(self.preferences, key):
                setattr(self.preferences, key, value)
                logger.debug(f"Preference updated: {key} = {value}")
    
    def save_preferences(self, file_path: Path = None):
        """Save user preferences"""
        if file_path is None:
            file_path = Path("config") / "ui_preferences.json"
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(file_path, 'w') as f:
                json.dump(self.preferences.to_dict(), f, indent=2)
            
            logger.info(f"UI preferences saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def load_preferences(self, file_path: Path = None):
        """Load user preferences"""
        if file_path is None:
            file_path = Path("config") / "ui_preferences.json"
        
        try:
            if file_path.exists():
                import json
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.preferences = UIPreferences.from_dict(data)
                logger.info(f"UI preferences loaded from {file_path}")
            else:
                logger.debug("No preferences file found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
    
    # Accessibility
    
    def enable_accessibility_mode(self, enabled: bool = True):
        """Enable accessibility mode"""
        self.preferences.accessibility_mode = enabled
        self.accessibility_manager.enable_high_contrast(enabled)
        self.accessibility_manager.enhance_focus_indicators(enabled)
        
        if enabled:
            self.show_info_message("Accessibility", "Accessibility mode enabled")
    
    # Keyboard shortcuts
    
    def handle_key_event(self, key: str, context: str = "global") -> bool:
        """Handle keyboard event"""
        if self.preferences.keyboard_shortcuts_enabled:
            return self.shortcut_manager.handle_key_press(key, context)
        return False
    
    def register_custom_shortcut(self, key: str, action: Callable, description: str, context: str = "global"):
        """Register custom keyboard shortcut"""
        shortcut = KeyboardShortcut(key, action, description, context)
        self.shortcut_manager.register_shortcut(shortcut)
    
    # Performance optimization
    
    def optimize_ui_performance(self):
        """Apply UI performance optimizations"""
        # This would implement various UI optimizations
        # based on current performance metrics
        
        metrics = self.performance_monitor.get_performance_summary()
        
        if metrics.get("performance_level") in ["poor", "critical"]:
            # Reduce animation speed
            self.preferences.animation_speed = 0.5
            
            # Show notification
            self.show_warning_message(
                "Performance", 
                "UI performance optimizations applied"
            )
            
            logger.info("UI performance optimizations applied")
    
    # Status and monitoring
    
    def get_ui_status(self) -> Dict[str, Any]:
        """Get UI enhancement status"""
        return {
            "theme": self.preferences.theme.value,
            "accessibility_mode": self.preferences.accessibility_mode,
            "shortcuts_enabled": self.preferences.keyboard_shortcuts_enabled,
            "active_operations": len(self.progress_tracker.active_operations),
            "recent_notifications": len(self.notification_manager.get_recent_notifications()),
            "performance_level": self.performance_monitor.get_performance_summary().get("performance_level", "unknown")
        }
    
    def cleanup(self):
        """Cleanup resources"""
        # Cancel any active operations
        for operation_id in self.async_manager.get_active_operations():
            self.async_manager.cancel_operation(operation_id)
        
        # Clear notifications
        self.notification_manager.clear_all_notifications()
        
        logger.info("UI enhancement system cleanup completed")


# Global UI enhancement manager
_global_ui_enhancement: Optional[UIEnhancementManager] = None


def get_ui_enhancement_manager() -> UIEnhancementManager:
    """Get or create global UI enhancement manager"""
    global _global_ui_enhancement
    if _global_ui_enhancement is None:
        _global_ui_enhancement = UIEnhancementManager()
    return _global_ui_enhancement


def configure_ui_enhancements(
    theme: UITheme = UITheme.DARK,
    accessibility_mode: bool = False,
    animation_speed: float = 1.0,
    auto_save_preferences: bool = True
):
    """Configure UI enhancements"""
    manager = get_ui_enhancement_manager()
    
    manager.set_theme(theme)
    manager.enable_accessibility_mode(accessibility_mode)
    manager.update_preferences(animation_speed=animation_speed)
    
    if auto_save_preferences:
        manager.save_preferences()
    
    logger.info("UI enhancements configured",
                theme=theme.value,
                accessibility=accessibility_mode,
                animation_speed=animation_speed)