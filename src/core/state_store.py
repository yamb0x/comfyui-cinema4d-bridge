"""
Centralized State Store

Implements centralized state management for comfy2c4d.
Replaces the scattered 60+ instance variables from the monolithic application
with a clean, event-driven state management system.

Part of Phase 2 architectural decomposition - addresses the multi-mind analysis
finding of "State Management Chaos" across architecture, UX, and reliability.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Callable, Union
from ..utils.advanced_logging import get_logger

logger = get_logger("state")

from PySide6.QtCore import QObject, Signal

from ..utils.error_handling import handle_errors, error_context
from ..core.unified_config_manager import UnifiedConfigurationManager


class StateChangeType(Enum):
    """Types of state changes for event emission"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    BATCH_UPDATE = "batch_update"


@dataclass
class SelectionState:
    """State for object selection across tabs"""
    selected_models: List[str] = field(default_factory=list)
    selected_images: List[str] = field(default_factory=list)
    selected_textures: List[str] = field(default_factory=list)
    selected_objects: List[str] = field(default_factory=list)
    current_selection_source: str = "none"  # "models", "images", "textures", "objects"
    last_updated: float = field(default_factory=time.time)
    
    def get_all_selected(self) -> List[str]:
        """Get all selected items regardless of type"""
        all_selected = []
        all_selected.extend(self.selected_models)
        all_selected.extend(self.selected_images)
        all_selected.extend(self.selected_textures)
        all_selected.extend(self.selected_objects)
        return list(set(all_selected))  # Remove duplicates
    
    def clear_all(self):
        """Clear all selections"""
        self.selected_models.clear()
        self.selected_images.clear()
        self.selected_textures.clear()
        self.selected_objects.clear()
        self.current_selection_source = "none"
        self.last_updated = time.time()
    
    def is_empty(self) -> bool:
        """Check if no items are selected"""
        return not any([
            self.selected_models,
            self.selected_images,
            self.selected_textures,
            self.selected_objects
        ])


@dataclass
class WorkflowState:
    """State for workflow execution and parameters"""
    current_workflow: str = ""
    current_tab: int = 0
    workflow_history: List[str] = field(default_factory=list)
    last_executed_workflow: str = ""
    workflow_parameters: Dict[str, Any] = field(default_factory=dict)
    execution_status: str = "idle"  # "idle", "running", "completed", "failed"
    progress_percentage: int = 0
    last_execution_time: float = 0
    active_operations: Set[str] = field(default_factory=set)
    
    def add_to_history(self, workflow: str):
        """Add workflow to history (max 10 items)"""
        if workflow in self.workflow_history:
            self.workflow_history.remove(workflow)
        self.workflow_history.insert(0, workflow)
        if len(self.workflow_history) > 10:
            self.workflow_history = self.workflow_history[:10]
    
    def is_executing(self) -> bool:
        """Check if any workflow is currently executing"""
        return self.execution_status == "running" or bool(self.active_operations)


@dataclass
class SessionState:
    """State for session data and persistence"""
    session_id: str = ""
    session_start_time: float = field(default_factory=time.time)
    generated_images: List[str] = field(default_factory=list)
    generated_models: List[str] = field(default_factory=list)
    generated_textures: List[str] = field(default_factory=list)
    recent_projects: List[str] = field(default_factory=list)
    settings_changed: bool = False
    auto_save_enabled: bool = True
    last_save_time: float = 0
    
    def add_generated_item(self, item_type: str, item_path: str):
        """Add generated item to appropriate list"""
        if item_type == "image":
            if item_path not in self.generated_images:
                self.generated_images.append(item_path)
        elif item_type == "model":
            if item_path not in self.generated_models:
                self.generated_models.append(item_path)
        elif item_type == "texture":
            if item_path not in self.generated_textures:
                self.generated_textures.append(item_path)
    
    def get_session_duration(self) -> float:
        """Get session duration in seconds"""
        return time.time() - self.session_start_time


@dataclass
class ConnectionState:
    """State for external service connections"""
    comfyui_connected: bool = False
    cinema4d_connected: bool = False
    comfyui_last_check: float = 0
    cinema4d_last_check: float = 0
    comfyui_status_message: str = "Not connected"
    cinema4d_status_message: str = "Not connected"
    retry_counts: Dict[str, int] = field(default_factory=dict)
    
    def update_connection(self, service: str, connected: bool, message: str = ""):
        """Update connection status for a service"""
        if service == "comfyui":
            self.comfyui_connected = connected
            self.comfyui_last_check = time.time()
            self.comfyui_status_message = message or ("Connected" if connected else "Disconnected")
        elif service == "cinema4d":
            self.cinema4d_connected = connected
            self.cinema4d_last_check = time.time()
            self.cinema4d_status_message = message or ("Connected" if connected else "Disconnected")
    
    def is_any_connected(self) -> bool:
        """Check if any service is connected"""
        return self.comfyui_connected or self.cinema4d_connected


@dataclass
class UIState:
    """State for UI configuration and display"""
    current_theme: str = "dark"
    window_geometry: Dict[str, int] = field(default_factory=dict)
    splitter_sizes: List[int] = field(default_factory=list)
    tab_states: Dict[str, bool] = field(default_factory=dict)
    console_visible: bool = True
    status_bar_visible: bool = True
    toolbar_visible: bool = True
    full_screen: bool = False
    
    def update_geometry(self, x: int, y: int, width: int, height: int):
        """Update window geometry"""
        self.window_geometry = {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }


class StateObserver(ABC):
    """Abstract observer for state changes"""
    
    @abstractmethod
    def on_state_changed(self, state_name: str, change_type: StateChangeType, data: Any):
        """Called when observed state changes"""
        pass


class StateStore(QObject):
    """
    Centralized state management system
    
    Implements the Observer pattern with Qt signals for event-driven architecture.
    Replaces the scattered instance variables from the monolithic application.
    """
    
    # State change signals
    selection_changed = Signal(SelectionState)
    workflow_changed = Signal(WorkflowState)
    session_changed = Signal(SessionState)
    connection_changed = Signal(ConnectionState)
    ui_changed = Signal(UIState)
    
    # Generic state change signal
    state_changed = Signal(str, str, object)  # state_name, change_type, data
    
    def __init__(self, config_manager: UnifiedConfigurationManager):
        super().__init__()
        self.config = config_manager
        
        # Initialize state objects
        self.selection = SelectionState()
        self.workflow = WorkflowState()
        self.session = SessionState()
        self.connection = ConnectionState()
        self.ui = UIState()
        
        # Observer registry
        self._observers: Dict[str, List[StateObserver]] = {
            "selection": [],
            "workflow": [],
            "session": [],
            "connection": [],
            "ui": []
        }
        
        # State persistence
        self._persistence_enabled = True
        self._state_file = Path("config") / "app_state.json"
        
        # Initialize session
        self._initialize_session()
        
        # Load persisted state
        self.load_state()
    
    def _initialize_session(self):
        """Initialize new session"""
        self.session.session_id = f"session_{int(time.time())}"
        self.session.session_start_time = time.time()
        logger.info(f"Session initialized: {self.session.session_id}")
    
    def _emit_state_change(self, state_name: str, change_type: StateChangeType, state_obj: Any):
        """Emit state change signals"""
        # Emit specific signal
        if state_name == "selection":
            self.selection_changed.emit(state_obj)
        elif state_name == "workflow":
            self.workflow_changed.emit(state_obj)
        elif state_name == "session":
            self.session_changed.emit(state_obj)
        elif state_name == "connection":
            self.connection_changed.emit(state_obj)
        elif state_name == "ui":
            self.ui_changed.emit(state_obj)
        
        # Emit generic signal
        self.state_changed.emit(state_name, change_type.value, state_obj)
        
        # Notify observers
        for observer in self._observers.get(state_name, []):
            try:
                observer.on_state_changed(state_name, change_type, state_obj)
            except Exception as e:
                logger.error(f"Observer notification failed: {e}")
        
        # Auto-save if enabled
        if self.session.auto_save_enabled:
            self.save_state()
    
    # Selection State Management
    
    @handle_errors("state_store", "update_selection")
    def update_selection(self, 
                        selection_type: str,
                        items: List[str],
                        replace: bool = True):
        """Update selection for specific type"""
        with error_context("state_store", "update_selection", 
                          selection_type=selection_type, 
                          item_count=len(items)):
            
            old_selection = asdict(self.selection)
            
            if selection_type == "models":
                if replace:
                    self.selection.selected_models = items.copy()
                else:
                    self.selection.selected_models.extend(items)
                    self.selection.selected_models = list(set(self.selection.selected_models))
                self.selection.current_selection_source = "models"
            
            elif selection_type == "images":
                if replace:
                    self.selection.selected_images = items.copy()
                else:
                    self.selection.selected_images.extend(items)
                    self.selection.selected_images = list(set(self.selection.selected_images))
                self.selection.current_selection_source = "images"
            
            elif selection_type == "textures":
                if replace:
                    self.selection.selected_textures = items.copy()
                else:
                    self.selection.selected_textures.extend(items)
                    self.selection.selected_textures = list(set(self.selection.selected_textures))
                self.selection.current_selection_source = "textures"
            
            elif selection_type == "objects":
                if replace:
                    self.selection.selected_objects = items.copy()
                else:
                    self.selection.selected_objects.extend(items)
                    self.selection.selected_objects = list(set(self.selection.selected_objects))
                self.selection.current_selection_source = "objects"
            
            self.selection.last_updated = time.time()
            
            # Only emit if selection actually changed
            if asdict(self.selection) != old_selection:
                self._emit_state_change("selection", StateChangeType.UPDATED, self.selection)
                logger.debug(f"Selection updated: {selection_type} - {len(items)} items")
    
    def clear_selection(self, selection_type: Optional[str] = None):
        """Clear selection (all or specific type)"""
        if selection_type is None:
            self.selection.clear_all()
        elif selection_type == "models":
            self.selection.selected_models.clear()
        elif selection_type == "images":
            self.selection.selected_images.clear()
        elif selection_type == "textures":
            self.selection.selected_textures.clear()
        elif selection_type == "objects":
            self.selection.selected_objects.clear()
        
        self.selection.last_updated = time.time()
        self._emit_state_change("selection", StateChangeType.UPDATED, self.selection)
    
    def get_selection(self, selection_type: Optional[str] = None) -> List[str]:
        """Get current selection"""
        if selection_type is None:
            return self.selection.get_all_selected()
        elif selection_type == "models":
            return self.selection.selected_models.copy()
        elif selection_type == "images":
            return self.selection.selected_images.copy()
        elif selection_type == "textures":
            return self.selection.selected_textures.copy()
        elif selection_type == "objects":
            return self.selection.selected_objects.copy()
        else:
            return []
    
    # Workflow State Management
    
    @handle_errors("state_store", "update_workflow")
    def update_workflow(self, **kwargs):
        """Update workflow state"""
        with error_context("state_store", "update_workflow", **kwargs):
            changed = False
            
            for key, value in kwargs.items():
                if hasattr(self.workflow, key):
                    old_value = getattr(self.workflow, key)
                    if old_value != value:
                        setattr(self.workflow, key, value)
                        changed = True
            
            if changed:
                self._emit_state_change("workflow", StateChangeType.UPDATED, self.workflow)
    
    def start_workflow_execution(self, workflow_name: str, parameters: Dict[str, Any]):
        """Start workflow execution"""
        self.workflow.current_workflow = workflow_name
        self.workflow.workflow_parameters = parameters.copy()
        self.workflow.execution_status = "running"
        self.workflow.progress_percentage = 0
        self.workflow.last_execution_time = time.time()
        self.workflow.add_to_history(workflow_name)
        
        self._emit_state_change("workflow", StateChangeType.UPDATED, self.workflow)
        logger.info(f"Workflow execution started: {workflow_name}")
    
    def complete_workflow_execution(self, success: bool = True):
        """Complete workflow execution"""
        if success:
            self.workflow.execution_status = "completed"
            self.workflow.last_executed_workflow = self.workflow.current_workflow
        else:
            self.workflow.execution_status = "failed"
        
        self.workflow.progress_percentage = 100 if success else 0
        self.workflow.active_operations.clear()
        
        self._emit_state_change("workflow", StateChangeType.UPDATED, self.workflow)
        logger.info(f"Workflow execution completed: {self.workflow.current_workflow} (success: {success})")
    
    def update_workflow_progress(self, percentage: int, operation: str = ""):
        """Update workflow progress"""
        self.workflow.progress_percentage = max(0, min(100, percentage))
        if operation:
            self.workflow.active_operations.add(operation)
        
        self._emit_state_change("workflow", StateChangeType.UPDATED, self.workflow)
    
    # Session State Management
    
    def add_generated_item(self, item_type: str, item_path: str):
        """Add generated item to session"""
        self.session.add_generated_item(item_type, item_path)
        self._emit_state_change("session", StateChangeType.UPDATED, self.session)
        logger.debug(f"Generated item added: {item_type} - {item_path}")
    
    def add_recent_project(self, project_path: str):
        """Add project to recent projects"""
        if project_path in self.session.recent_projects:
            self.session.recent_projects.remove(project_path)
        self.session.recent_projects.insert(0, project_path)
        
        # Keep only last 10 projects
        if len(self.session.recent_projects) > 10:
            self.session.recent_projects = self.session.recent_projects[:10]
        
        self._emit_state_change("session", StateChangeType.UPDATED, self.session)
    
    # Connection State Management
    
    def update_connection_status(self, service: str, connected: bool, message: str = ""):
        """Update connection status"""
        self.connection.update_connection(service, connected, message)
        self._emit_state_change("connection", StateChangeType.UPDATED, self.connection)
        logger.debug(f"Connection status updated: {service} - {connected}")
    
    def increment_retry_count(self, service: str):
        """Increment retry count for service"""
        self.connection.retry_counts[service] = self.connection.retry_counts.get(service, 0) + 1
        self._emit_state_change("connection", StateChangeType.UPDATED, self.connection)
    
    def reset_retry_count(self, service: str):
        """Reset retry count for service"""
        if service in self.connection.retry_counts:
            del self.connection.retry_counts[service]
        self._emit_state_change("connection", StateChangeType.UPDATED, self.connection)
    
    # UI State Management
    
    def update_ui_state(self, **kwargs):
        """Update UI state"""
        changed = False
        
        for key, value in kwargs.items():
            if hasattr(self.ui, key):
                old_value = getattr(self.ui, key)
                if old_value != value:
                    setattr(self.ui, key, value)
                    changed = True
        
        if changed:
            self._emit_state_change("ui", StateChangeType.UPDATED, self.ui)
    
    # Observer Management
    
    def add_observer(self, state_name: str, observer: StateObserver):
        """Add state observer"""
        if state_name in self._observers:
            self._observers[state_name].append(observer)
            logger.debug(f"Observer added for {state_name}")
    
    def remove_observer(self, state_name: str, observer: StateObserver):
        """Remove state observer"""
        if state_name in self._observers and observer in self._observers[state_name]:
            self._observers[state_name].remove(observer)
            logger.debug(f"Observer removed for {state_name}")
    
    # State Persistence
    
    @handle_errors("state_store", "save_state", reraise=False)
    def save_state(self):
        """Save current state to file"""
        if not self._persistence_enabled:
            return
        
        with error_context("state_store", "save_state", file=str(self._state_file)):
            state_data = {
                "selection": asdict(self.selection),
                "workflow": asdict(self.workflow),
                "session": asdict(self.session),
                "connection": asdict(self.connection),
                "ui": asdict(self.ui),
                "saved_at": time.time()
            }
            
            # Convert sets to lists for JSON serialization
            if "active_operations" in state_data["workflow"]:
                state_data["workflow"]["active_operations"] = list(state_data["workflow"]["active_operations"])
            
            # Ensure parent directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Atomic write
            temp_file = self._state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            temp_file.replace(self._state_file)
            
            self.session.last_save_time = time.time()
            logger.debug("State saved successfully")
    
    @handle_errors("state_store", "load_state", reraise=False)
    def load_state(self):
        """Load state from file"""
        if not self._state_file.exists():
            logger.debug("No state file found, using defaults")
            return
        
        with error_context("state_store", "load_state", file=str(self._state_file)):
            try:
                with open(self._state_file, 'r') as f:
                    state_data = json.load(f)
                
                # Restore state objects
                if "selection" in state_data:
                    selection_data = state_data["selection"]
                    self.selection = SelectionState(**selection_data)
                
                if "workflow" in state_data:
                    workflow_data = state_data["workflow"]
                    # Convert lists back to sets
                    if "active_operations" in workflow_data:
                        workflow_data["active_operations"] = set(workflow_data["active_operations"])
                    self.workflow = WorkflowState(**workflow_data)
                
                if "session" in state_data:
                    session_data = state_data["session"]
                    self.session = SessionState(**session_data)
                
                if "connection" in state_data:
                    connection_data = state_data["connection"]
                    self.connection = ConnectionState(**connection_data)
                
                if "ui" in state_data:
                    ui_data = state_data["ui"]
                    self.ui = UIState(**ui_data)
                
                logger.info("State loaded successfully")
                
            except Exception as e:
                logger.warning(f"Failed to load state: {e}, using defaults")
    
    # Utility Methods
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state"""
        return {
            "selection": {
                "total_selected": len(self.selection.get_all_selected()),
                "source": self.selection.current_selection_source,
                "is_empty": self.selection.is_empty()
            },
            "workflow": {
                "current": self.workflow.current_workflow,
                "status": self.workflow.execution_status,
                "progress": self.workflow.progress_percentage,
                "is_executing": self.workflow.is_executing()
            },
            "session": {
                "duration": self.session.get_session_duration(),
                "generated_items": (
                    len(self.session.generated_images) +
                    len(self.session.generated_models) +
                    len(self.session.generated_textures)
                )
            },
            "connection": {
                "any_connected": self.connection.is_any_connected(),
                "comfyui": self.connection.comfyui_connected,
                "cinema4d": self.connection.cinema4d_connected
            }
        }
    
    def reset_state(self, confirm: bool = False):
        """Reset all state to defaults"""
        if not confirm:
            logger.warning("State reset requires confirmation")
            return
        
        self.selection = SelectionState()
        self.workflow = WorkflowState()
        self.session = SessionState()
        self.connection = ConnectionState()
        self.ui = UIState()
        
        self._initialize_session()
        
        # Emit all state changes
        self._emit_state_change("selection", StateChangeType.UPDATED, self.selection)
        self._emit_state_change("workflow", StateChangeType.UPDATED, self.workflow)
        self._emit_state_change("session", StateChangeType.UPDATED, self.session)
        self._emit_state_change("connection", StateChangeType.UPDATED, self.connection)
        self._emit_state_change("ui", StateChangeType.UPDATED, self.ui)
        
        logger.info("State reset completed")
    
    def export_state(self, export_path: Path):
        """Export current state to file"""
        state_data = {
            "selection": asdict(self.selection),
            "workflow": asdict(self.workflow),
            "session": asdict(self.session),
            "connection": asdict(self.connection),
            "ui": asdict(self.ui),
            "exported_at": time.time()
        }
        
        # Convert sets to lists for JSON serialization
        if "active_operations" in state_data["workflow"]:
            state_data["workflow"]["active_operations"] = list(state_data["workflow"]["active_operations"])
        
        with open(export_path, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        logger.info(f"State exported to: {export_path}")
    
    def set_persistence_enabled(self, enabled: bool):
        """Enable or disable state persistence"""
        self._persistence_enabled = enabled
        logger.debug(f"State persistence {'enabled' if enabled else 'disabled'}")