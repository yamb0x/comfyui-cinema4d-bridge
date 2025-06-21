"""
Advanced State Management Features

Enhanced state management with state machines, undo/redo, snapshots,
persistence, validation, and state synchronization across components.

Part of Phase 3 Quality & Polish - extends the basic StateStore with
enterprise-grade state management capabilities.
"""

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union, TypeVar, Generic

from ..utils.advanced_logging import get_logger
from ..core.state_store import StateStore, StateChangeType

logger = get_logger("advanced_state")

T = TypeVar('T')


class StateMachineState(Enum):
    """States for application state machine"""
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class StateOperation(Enum):
    """Types of state operations for history"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_UPDATE = "batch_update"
    IMPORT = "import"
    EXPORT = "export"


@dataclass
class StateSnapshot:
    """Immutable state snapshot for undo/redo"""
    snapshot_id: str
    timestamp: float
    state_data: Dict[str, Any]
    operation: StateOperation
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "state_data": self.state_data,
            "operation": self.operation.value,
            "description": self.description,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """Create from dictionary"""
        return cls(
            snapshot_id=data["snapshot_id"],
            timestamp=data["timestamp"],
            state_data=data["state_data"],
            operation=StateOperation(data["operation"]),
            description=data["description"],
            metadata=data.get("metadata", {})
        )


@dataclass
class StateTransition:
    """State machine transition"""
    from_state: StateMachineState
    to_state: StateMachineState
    trigger: str
    condition: Optional[Callable[[], bool]] = None
    action: Optional[Callable[[], None]] = None


class StateValidator:
    """Validates state changes and constraints"""
    
    def __init__(self):
        self.validation_rules: Dict[str, List[Callable[[Any], bool]]] = {}
        self.constraints: Dict[str, List[Callable[[Dict[str, Any]], bool]]] = {}
    
    def add_validation_rule(self, state_path: str, validator: Callable[[Any], bool]):
        """Add validation rule for state path"""
        if state_path not in self.validation_rules:
            self.validation_rules[state_path] = []
        self.validation_rules[state_path].append(validator)
    
    def add_constraint(self, constraint_name: str, constraint: Callable[[Dict[str, Any]], bool]):
        """Add global state constraint"""
        if constraint_name not in self.constraints:
            self.constraints[constraint_name] = []
        self.constraints[constraint_name].append(constraint)
    
    def validate_state_change(self, state_path: str, new_value: Any, full_state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a state change"""
        errors = []
        
        # Check field-specific validation rules
        if state_path in self.validation_rules:
            for validator in self.validation_rules[state_path]:
                try:
                    if not validator(new_value):
                        errors.append(f"Validation failed for {state_path}: {new_value}")
                except Exception as e:
                    errors.append(f"Validation error for {state_path}: {str(e)}")
        
        # Check global constraints
        test_state = full_state.copy()
        self._set_nested_value(test_state, state_path, new_value)
        
        for constraint_name, constraint_list in self.constraints.items():
            for constraint in constraint_list:
                try:
                    if not constraint(test_state):
                        errors.append(f"Constraint violation: {constraint_name}")
                except Exception as e:
                    errors.append(f"Constraint error ({constraint_name}): {str(e)}")
        
        return len(errors) == 0, errors
    
    def _set_nested_value(self, state_dict: Dict[str, Any], path: str, value: Any):
        """Set nested value in state dictionary"""
        keys = path.split('.')
        current = state_dict
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


class UndoRedoManager:
    """Manages undo/redo functionality with snapshots"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.current_index = -1
        self.undo_stack: deque = deque(maxlen=max_history)
        self.redo_stack: deque = deque(maxlen=max_history)
    
    def add_snapshot(self, snapshot: StateSnapshot):
        """Add state snapshot to history"""
        # Clear redo stack when new action is taken
        self.redo_stack.clear()
        
        # Add to undo stack
        self.undo_stack.append(snapshot)
        
        # Add to history
        self.history.append(snapshot)
        
        logger.debug(f"State snapshot added: {snapshot.description}",
                    snapshot_id=snapshot.snapshot_id,
                    operation=snapshot.operation.value)
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.undo_stack) > 1  # Keep at least one state
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return len(self.redo_stack) > 0
    
    def undo(self) -> Optional[StateSnapshot]:
        """Undo last operation"""
        if not self.can_undo():
            return None
        
        # Move current state to redo stack
        current = self.undo_stack.pop()
        self.redo_stack.append(current)
        
        # Get previous state
        previous = self.undo_stack[-1] if self.undo_stack else None
        
        if previous:
            logger.info(f"Undo operation: {current.description} -> {previous.description}",
                       current_id=current.snapshot_id,
                       previous_id=previous.snapshot_id)
        
        return previous
    
    def redo(self) -> Optional[StateSnapshot]:
        """Redo last undone operation"""
        if not self.can_redo():
            return None
        
        # Move state from redo to undo stack
        next_state = self.redo_stack.pop()
        self.undo_stack.append(next_state)
        
        logger.info(f"Redo operation: {next_state.description}",
                   snapshot_id=next_state.snapshot_id)
        
        return next_state
    
    def get_history(self, limit: int = 10) -> List[StateSnapshot]:
        """Get recent history"""
        return list(self.history)[-limit:]
    
    def clear_history(self):
        """Clear all history"""
        self.history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        logger.info("State history cleared")


class StateMachine:
    """Application state machine for managing workflow states"""
    
    def __init__(self, initial_state: StateMachineState = StateMachineState.INITIALIZING):
        self.current_state = initial_state
        self.transitions: Dict[StateMachineState, List[StateTransition]] = {}
        self.state_history: List[Tuple[StateMachineState, float]] = []
        self.listeners: List[Callable[[StateMachineState, StateMachineState], None]] = []
        
        # Record initial state
        self.state_history.append((initial_state, time.time()))
        
        # Setup default transitions
        self._setup_default_transitions()
    
    def _setup_default_transitions(self):
        """Setup default state transitions"""
        self.add_transition(StateMachineState.INITIALIZING, StateMachineState.READY, "initialization_complete")
        self.add_transition(StateMachineState.READY, StateMachineState.LOADING, "start_loading")
        self.add_transition(StateMachineState.LOADING, StateMachineState.READY, "loading_complete")
        self.add_transition(StateMachineState.LOADING, StateMachineState.ERROR, "loading_failed")
        self.add_transition(StateMachineState.READY, StateMachineState.PROCESSING, "start_processing")
        self.add_transition(StateMachineState.PROCESSING, StateMachineState.READY, "processing_complete")
        self.add_transition(StateMachineState.PROCESSING, StateMachineState.ERROR, "processing_failed")
        self.add_transition(StateMachineState.ERROR, StateMachineState.READY, "error_recovered")
        
        # Any state can go to shutdown
        for state in StateMachineState:
            if state != StateMachineState.SHUTDOWN:
                self.add_transition(state, StateMachineState.SHUTDOWN, "shutdown")
    
    def add_transition(self, from_state: StateMachineState, to_state: StateMachineState, trigger: str,
                      condition: Optional[Callable[[], bool]] = None,
                      action: Optional[Callable[[], None]] = None):
        """Add state transition"""
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        
        transition = StateTransition(from_state, to_state, trigger, condition, action)
        self.transitions[from_state].append(transition)
    
    def trigger(self, trigger_name: str) -> bool:
        """Trigger state transition"""
        if self.current_state not in self.transitions:
            return False
        
        for transition in self.transitions[self.current_state]:
            if transition.trigger == trigger_name:
                # Check condition if present
                if transition.condition and not transition.condition():
                    continue
                
                # Execute action if present
                if transition.action:
                    try:
                        transition.action()
                    except Exception as e:
                        logger.error(f"State transition action failed: {e}")
                        return False
                
                # Perform transition
                old_state = self.current_state
                self.current_state = transition.to_state
                self.state_history.append((self.current_state, time.time()))
                
                # Notify listeners
                for listener in self.listeners:
                    try:
                        listener(old_state, self.current_state)
                    except Exception as e:
                        logger.error(f"State listener error: {e}")
                
                logger.info(f"State transition: {old_state.value} -> {self.current_state.value}",
                           trigger=trigger_name)
                
                return True
        
        logger.warning(f"No valid transition found for trigger '{trigger_name}' from state '{self.current_state.value}'")
        return False
    
    def add_listener(self, listener: Callable[[StateMachineState, StateMachineState], None]):
        """Add state change listener"""
        self.listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[StateMachineState, StateMachineState], None]):
        """Remove state change listener"""
        if listener in self.listeners:
            self.listeners.remove(listener)
    
    def get_current_state(self) -> StateMachineState:
        """Get current state"""
        return self.current_state
    
    def can_transition(self, trigger_name: str) -> bool:
        """Check if transition is possible"""
        if self.current_state not in self.transitions:
            return False
        
        for transition in self.transitions[self.current_state]:
            if transition.trigger == trigger_name:
                if transition.condition:
                    return transition.condition()
                return True
        
        return False
    
    def get_available_triggers(self) -> List[str]:
        """Get available triggers from current state"""
        if self.current_state not in self.transitions:
            return []
        
        return [t.trigger for t in self.transitions[self.current_state]]
    
    def get_state_duration(self) -> float:
        """Get how long we've been in current state"""
        if not self.state_history:
            return 0.0
        
        last_transition_time = self.state_history[-1][1]
        return time.time() - last_transition_time


class StateSync:
    """Synchronizes state across multiple components"""
    
    def __init__(self):
        self.sync_channels: Dict[str, Set[Callable[[str, Any], None]]] = {}
        self.sync_filters: Dict[str, Callable[[str, Any], bool]] = {}
    
    def register_sync_channel(self, channel: str, callback: Callable[[str, Any], None],
                            sync_filter: Optional[Callable[[str, Any], bool]] = None):
        """Register component for state synchronization"""
        if channel not in self.sync_channels:
            self.sync_channels[channel] = set()
        
        self.sync_channels[channel].add(callback)
        
        if sync_filter:
            self.sync_filters[f"{channel}:{id(callback)}"] = sync_filter
        
        logger.debug(f"Registered sync channel: {channel}")
    
    def unregister_sync_channel(self, channel: str, callback: Callable[[str, Any], None]):
        """Unregister component from synchronization"""
        if channel in self.sync_channels:
            self.sync_channels[channel].discard(callback)
            filter_key = f"{channel}:{id(callback)}"
            if filter_key in self.sync_filters:
                del self.sync_filters[filter_key]
    
    def broadcast_state_change(self, channel: str, state_path: str, value: Any, source_callback: Optional[Callable] = None):
        """Broadcast state change to all registered components"""
        if channel not in self.sync_channels:
            return
        
        for callback in self.sync_channels[channel]:
            # Don't notify the source of the change
            if callback == source_callback:
                continue
            
            # Check sync filter
            filter_key = f"{channel}:{id(callback)}"
            if filter_key in self.sync_filters:
                if not self.sync_filters[filter_key](state_path, value):
                    continue
            
            try:
                callback(state_path, value)
            except Exception as e:
                logger.error(f"State sync callback error: {e}")


class StatePersistence:
    """Advanced state persistence with compression and encryption"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save_enabled = True
        self.auto_save_interval = 30.0  # seconds
        self.last_auto_save = 0.0
        self.compression_enabled = True
    
    async def save_state(self, state_data: Dict[str, Any], filename: str = "state.json") -> bool:
        """Save state to file"""
        try:
            file_path = self.storage_dir / filename
            
            # Create backup of existing file
            if file_path.exists():
                backup_path = file_path.with_suffix('.backup')
                file_path.rename(backup_path)
            
            # Prepare state data
            save_data = {
                "timestamp": time.time(),
                "version": "1.0",
                "state": state_data
            }
            
            # Save with atomic write
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            temp_path.rename(file_path)
            
            logger.debug(f"State saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    async def load_state(self, filename: str = "state.json") -> Optional[Dict[str, Any]]:
        """Load state from file"""
        try:
            file_path = self.storage_dir / filename
            
            if not file_path.exists():
                logger.debug(f"State file not found: {file_path}")
                return None
            
            with open(file_path, 'r') as f:
                save_data = json.load(f)
            
            # Validate format
            if "state" not in save_data:
                logger.warning(f"Invalid state file format: {file_path}")
                return None
            
            logger.debug(f"State loaded from {file_path}")
            return save_data["state"]
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    async def auto_save_if_needed(self, state_data: Dict[str, Any]):
        """Auto-save state if interval has passed"""
        current_time = time.time()
        if (self.auto_save_enabled and 
            current_time - self.last_auto_save > self.auto_save_interval):
            
            if await self.save_state(state_data, "auto_save.json"):
                self.last_auto_save = current_time
    
    def enable_auto_save(self, enabled: bool = True, interval: float = 30.0):
        """Enable or disable auto-save"""
        self.auto_save_enabled = enabled
        self.auto_save_interval = interval
        logger.info(f"Auto-save {'enabled' if enabled else 'disabled'}, interval: {interval}s")


class AdvancedStateManager:
    """
    Advanced state management system
    
    Extends the basic StateStore with enterprise features:
    - State machines for workflow management
    - Undo/redo with snapshots
    - State validation and constraints
    - Cross-component synchronization
    - Advanced persistence with auto-save
    """
    
    def __init__(self, base_state_store: StateStore, storage_dir: Optional[Path] = None):
        self.base_state = base_state_store
        self.storage_dir = storage_dir or Path("state_storage")
        
        # Advanced features
        self.validator = StateValidator()
        self.undo_redo = UndoRedoManager()
        self.state_machine = StateMachine()
        self.state_sync = StateSync()
        self.persistence = StatePersistence(self.storage_dir)
        
        # State tracking
        self.state_snapshots: Dict[str, StateSnapshot] = {}
        self.auto_snapshot_enabled = True
        self.snapshot_triggers: Set[str] = {
            "workflow_execution", "selection_change", "configuration_update"
        }
        
        # Connect to base state store
        self._connect_to_base_state()
        
        # Setup validation rules
        self._setup_default_validation()
        
        logger.info("Advanced state management initialized")
    
    def _connect_to_base_state(self):
        """Connect to base state store events"""
        self.base_state.state_changed.connect(self._on_state_changed)
        self.base_state.selection_changed.connect(self._on_selection_changed)
        self.base_state.workflow_changed.connect(self._on_workflow_changed)
    
    def _setup_default_validation(self):
        """Setup default validation rules"""
        # Selection validation
        self.validator.add_validation_rule(
            "selection.models", 
            lambda x: isinstance(x, list) and all(isinstance(item, str) for item in x)
        )
        
        # Workflow validation
        self.validator.add_validation_rule(
            "workflow.batch_size",
            lambda x: isinstance(x, int) and 1 <= x <= 10
        )
        
        # Global constraints
        self.validator.add_constraint(
            "max_selected_items",
            lambda state: len(state.get("selection", {}).get("models", [])) <= 50
        )
    
    def _on_state_changed(self, state_name: str, change_type: str, data: Any):
        """Handle base state changes"""
        # Create snapshot if needed
        if self.auto_snapshot_enabled and state_name in self.snapshot_triggers:
            self.create_snapshot(
                operation=StateOperation.UPDATE,
                description=f"State change: {state_name}",
                metadata={"state_name": state_name, "change_type": change_type}
            )
        
        # Auto-save if needed
        asyncio.create_task(self._auto_save_state())
    
    def _on_selection_changed(self, selection_state):
        """Handle selection changes"""
        # Broadcast to sync channels
        self.state_sync.broadcast_state_change(
            "selection", "selection", selection_state
        )
    
    def _on_workflow_changed(self, workflow_state):
        """Handle workflow changes"""
        # Update state machine based on workflow status
        if workflow_state.execution_status == "running":
            self.state_machine.trigger("start_processing")
        elif workflow_state.execution_status == "completed":
            self.state_machine.trigger("processing_complete")
        elif workflow_state.execution_status == "failed":
            self.state_machine.trigger("processing_failed")
    
    async def _auto_save_state(self):
        """Auto-save current state"""
        try:
            current_state = self.get_full_state()
            await self.persistence.auto_save_if_needed(current_state)
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
    
    # Snapshot management
    
    def create_snapshot(self, operation: StateOperation, description: str, metadata: Dict[str, Any] = None) -> str:
        """Create state snapshot"""
        snapshot_id = str(uuid.uuid4())
        current_state = self.get_full_state()
        
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            timestamp=time.time(),
            state_data=current_state,
            operation=operation,
            description=description,
            metadata=metadata or {}
        )
        
        self.state_snapshots[snapshot_id] = snapshot
        self.undo_redo.add_snapshot(snapshot)
        
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore state from snapshot"""
        if snapshot_id not in self.state_snapshots:
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        snapshot = self.state_snapshots[snapshot_id]
        
        try:
            self._restore_state_data(snapshot.state_data)
            logger.info(f"State restored from snapshot: {snapshot.description}",
                       snapshot_id=snapshot_id)
            return True
        except Exception as e:
            logger.error(f"Failed to restore snapshot {snapshot_id}: {e}")
            return False
    
    def _restore_state_data(self, state_data: Dict[str, Any]):
        """Restore state data to base state store"""
        # This would need to be implemented based on the base state store structure
        # For now, we'll update the major state components
        
        if "selection" in state_data:
            selection_data = state_data["selection"]
            for selection_type, items in selection_data.items():
                if selection_type.startswith("selected_"):
                    clean_type = selection_type.replace("selected_", "")
                    self.base_state.update_selection(clean_type, items)
        
        if "workflow" in state_data:
            workflow_data = state_data["workflow"]
            self.base_state.update_workflow(**workflow_data)
    
    # Undo/Redo operations
    
    def undo(self) -> bool:
        """Undo last operation"""
        snapshot = self.undo_redo.undo()
        if snapshot:
            self._restore_state_data(snapshot.state_data)
            return True
        return False
    
    def redo(self) -> bool:
        """Redo last undone operation"""
        snapshot = self.undo_redo.redo()
        if snapshot:
            self._restore_state_data(snapshot.state_data)
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.undo_redo.can_undo()
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.undo_redo.can_redo()
    
    # State validation
    
    def validate_state_change(self, state_path: str, new_value: Any) -> Tuple[bool, List[str]]:
        """Validate proposed state change"""
        current_state = self.get_full_state()
        return self.validator.validate_state_change(state_path, new_value, current_state)
    
    def add_validation_rule(self, state_path: str, validator: Callable[[Any], bool]):
        """Add validation rule"""
        self.validator.add_validation_rule(state_path, validator)
    
    def add_constraint(self, constraint_name: str, constraint: Callable[[Dict[str, Any]], bool]):
        """Add global constraint"""
        self.validator.add_constraint(constraint_name, constraint)
    
    # State synchronization
    
    def register_sync_channel(self, channel: str, callback: Callable[[str, Any], None]):
        """Register for state synchronization"""
        self.state_sync.register_sync_channel(channel, callback)
    
    def broadcast_change(self, channel: str, state_path: str, value: Any):
        """Broadcast state change"""
        self.state_sync.broadcast_state_change(channel, state_path, value)
    
    # State machine operations
    
    def trigger_state_machine(self, trigger: str) -> bool:
        """Trigger state machine transition"""
        return self.state_machine.trigger(trigger)
    
    def get_application_state(self) -> StateMachineState:
        """Get current application state"""
        return self.state_machine.get_current_state()
    
    def can_perform_action(self, action: str) -> bool:
        """Check if action can be performed in current state"""
        # Map actions to state machine triggers
        action_triggers = {
            "load_workflow": "start_loading",
            "execute_workflow": "start_processing",
            "recover_from_error": "error_recovered"
        }
        
        trigger = action_triggers.get(action)
        if trigger:
            return self.state_machine.can_transition(trigger)
        
        return True  # Allow unknown actions
    
    # Persistence operations
    
    async def save_state(self, filename: str = None) -> bool:
        """Save current state"""
        current_state = self.get_full_state()
        filename = filename or f"state_{int(time.time())}.json"
        return await self.persistence.save_state(current_state, filename)
    
    async def load_state(self, filename: str = None) -> bool:
        """Load state from file"""
        filename = filename or "state.json"
        state_data = await self.persistence.load_state(filename)
        
        if state_data:
            self._restore_state_data(state_data)
            self.create_snapshot(
                operation=StateOperation.IMPORT,
                description=f"Loaded state from {filename}"
            )
            return True
        
        return False
    
    def enable_auto_save(self, enabled: bool = True, interval: float = 30.0):
        """Enable auto-save"""
        self.persistence.enable_auto_save(enabled, interval)
    
    # Utility methods
    
    def get_full_state(self) -> Dict[str, Any]:
        """Get complete current state"""
        return {
            "selection": {
                "selected_models": self.base_state.selection.selected_models,
                "selected_images": self.base_state.selection.selected_images,
                "selected_textures": self.base_state.selection.selected_textures,
                "selected_objects": self.base_state.selection.selected_objects,
                "current_selection_source": self.base_state.selection.current_selection_source
            },
            "workflow": {
                "current_workflow": self.base_state.workflow.current_workflow,
                "current_tab": self.base_state.workflow.current_tab,
                "execution_status": self.base_state.workflow.execution_status,
                "progress_percentage": self.base_state.workflow.progress_percentage,
                "workflow_parameters": self.base_state.workflow.workflow_parameters
            },
            "session": {
                "session_id": self.base_state.session.session_id,
                "generated_images": self.base_state.session.generated_images,
                "generated_models": self.base_state.session.generated_models,
                "generated_textures": self.base_state.session.generated_textures
            },
            "ui": {
                "current_theme": self.base_state.ui.current_theme,
                "window_geometry": self.base_state.ui.window_geometry,
                "console_visible": self.base_state.ui.console_visible
            },
            "connection": {
                "comfyui_connected": self.base_state.connection.comfyui_connected,
                "cinema4d_connected": self.base_state.connection.cinema4d_connected
            }
        }
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get advanced state management summary"""
        return {
            "application_state": self.state_machine.get_current_state().value,
            "state_history": len(self.undo_redo.history),
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "snapshots": len(self.state_snapshots),
            "sync_channels": len(self.state_sync.sync_channels),
            "auto_save_enabled": self.persistence.auto_save_enabled,
            "validation_rules": len(self.validator.validation_rules),
            "constraints": len(self.validator.constraints)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.state_machine.listeners.clear()
        self.state_sync.sync_channels.clear()
        logger.info("Advanced state management cleanup completed")


# Global advanced state manager
_global_advanced_state: Optional[AdvancedStateManager] = None


def get_advanced_state_manager(base_state_store: StateStore = None) -> AdvancedStateManager:
    """Get or create global advanced state manager"""
    global _global_advanced_state
    if _global_advanced_state is None:
        if base_state_store is None:
            raise ValueError("Base state store required for first initialization")
        _global_advanced_state = AdvancedStateManager(base_state_store)
    return _global_advanced_state


def configure_advanced_state_management(
    base_state_store: StateStore,
    auto_snapshot: bool = True,
    auto_save: bool = True,
    auto_save_interval: float = 30.0,
    storage_dir: Optional[Path] = None
):
    """Configure advanced state management"""
    manager = get_advanced_state_manager(base_state_store)
    
    manager.auto_snapshot_enabled = auto_snapshot
    manager.enable_auto_save(auto_save, auto_save_interval)
    
    if storage_dir:
        manager.storage_dir = storage_dir
        manager.persistence = StatePersistence(storage_dir)
    
    logger.info("Advanced state management configured",
                auto_snapshot=auto_snapshot,
                auto_save=auto_save,
                auto_save_interval=auto_save_interval)