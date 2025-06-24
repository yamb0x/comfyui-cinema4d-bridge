"""
Unified Selection Management System for comfy2c4d

Consolidates scattered selection lists into a single, consistent system
that maintains backward compatibility while providing better performance
and state management.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from PySide6.QtCore import QObject, Signal


class SelectionType(Enum):
    """Types of objects that can be selected"""
    IMAGE = "image"
    MODEL_3D = "model_3d"
    TEXTURE = "texture"
    TEXTURED_MODEL = "textured_model"


@dataclass
class SelectionItem:
    """Represents a selected object with metadata"""
    path: Path
    type: SelectionType
    selected_at: float = field(default_factory=lambda: __import__('time').time())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(str(self.path))
    
    def __eq__(self, other):
        if isinstance(other, SelectionItem):
            return self.path == other.path
        elif isinstance(other, Path):
            return self.path == other
        return False


class UnifiedSelectionManager(QObject):
    """
    Centralized selection management that replaces scattered selection lists.
    
    Features:
    - Single source of truth for all selections
    - Type-safe selection operations
    - Automatic UI synchronization
    - Backward compatibility with existing lists
    - Performance optimization through lazy updates
    """
    
    # Signals for UI synchronization
    selection_changed = Signal(str, SelectionType, bool)  # path, type, selected
    selection_cleared = Signal(SelectionType)  # type
    selection_count_changed = Signal(SelectionType, int)  # type, count
    
    def __init__(self):
        super().__init__()
        self._selections: Dict[str, SelectionItem] = {}
        self._observers: List[Callable] = []
        self._update_pending = False
        
        # Legacy compatibility - these will be kept in sync
        self._legacy_selected_images: List[Path] = []
        self._legacy_selected_models: List[Path] = []
        
        logger.debug("UnifiedSelectionManager initialized")
    
    def add_selection(self, path: Path, selection_type: SelectionType, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an object to the selection.
        
        Args:
            path: Path to the object
            selection_type: Type of object being selected
            metadata: Optional metadata to store with the selection
            
        Returns:
            True if object was added, False if already selected
        """
        path_str = str(path)
        
        if path_str in self._selections:
            logger.debug(f"Object already selected: {path.name}")
            return False
        
        # Create selection item
        item = SelectionItem(
            path=path,
            type=selection_type,
            metadata=metadata or {}
        )
        
        # Add to selections
        self._selections[path_str] = item
        
        # Update legacy lists for backward compatibility
        self._update_legacy_lists()
        
        # Emit signals
        self.selection_changed.emit(path_str, selection_type, True)
        self.selection_count_changed.emit(selection_type, self.get_count(selection_type))
        
        logger.info(f"UnifiedSelectionManager: Added {selection_type.value}: {path.name}")
        return True
    
    def remove_selection(self, path: Path) -> bool:
        """
        Remove an object from the selection.
        
        Args:
            path: Path to the object to remove
            
        Returns:
            True if object was removed, False if not selected
        """
        path_str = str(path)
        
        if path_str not in self._selections:
            logger.debug(f"Object not selected: {path.name}")
            return False
        
        # Get type before removal
        item = self._selections[path_str]
        selection_type = item.type
        
        # Remove from selections
        del self._selections[path_str]
        
        # Update legacy lists
        self._update_legacy_lists()
        
        # Emit signals
        self.selection_changed.emit(path_str, selection_type, False)
        self.selection_count_changed.emit(selection_type, self.get_count(selection_type))
        
        logger.debug(f"Removed {selection_type.value}: {path.name}")
        return True
    
    def toggle_selection(self, path: Path, selection_type: SelectionType, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Toggle selection state of an object.
        
        Returns:
            True if object is now selected, False if now deselected
        """
        if self.is_selected(path):
            self.remove_selection(path)
            return False
        else:
            self.add_selection(path, selection_type, metadata)
            return True
    
    def is_selected(self, path: Path) -> bool:
        """Check if an object is selected."""
        return str(path) in self._selections
    
    def get_selected_paths(self, selection_type: Optional[SelectionType] = None) -> List[Path]:
        """
        Get list of selected paths, optionally filtered by type.
        
        Args:
            selection_type: Optional type filter
            
        Returns:
            List of selected paths
        """
        if selection_type is None:
            return [item.path for item in self._selections.values()]
        else:
            return [item.path for item in self._selections.values() if item.type == selection_type]
    
    def get_selected_items(self, selection_type: Optional[SelectionType] = None) -> List[SelectionItem]:
        """
        Get list of selected items, optionally filtered by type.
        
        Args:
            selection_type: Optional type filter
            
        Returns:
            List of selected items with metadata
        """
        if selection_type is None:
            return list(self._selections.values())
        else:
            return [item for item in self._selections.values() if item.type == selection_type]
    
    def get_count(self, selection_type: Optional[SelectionType] = None) -> int:
        """Get count of selected objects, optionally filtered by type."""
        if selection_type is None:
            return len(self._selections)
        else:
            return len([item for item in self._selections.values() if item.type == selection_type])
    
    def clear_selection(self, selection_type: Optional[SelectionType] = None):
        """
        Clear selection, optionally filtered by type.
        
        Args:
            selection_type: Optional type to clear, or None to clear all
        """
        if selection_type is None:
            # Clear all selections
            self._selections.clear()
            self._update_legacy_lists()
            for sel_type in SelectionType:
                self.selection_cleared.emit(sel_type)
                self.selection_count_changed.emit(sel_type, 0)
            logger.info("Cleared all selections")
        else:
            # Clear specific type
            to_remove = [path for path, item in self._selections.items() if item.type == selection_type]
            for path in to_remove:
                del self._selections[path]
            
            self._update_legacy_lists()
            self.selection_cleared.emit(selection_type)
            self.selection_count_changed.emit(selection_type, 0)
            logger.info(f"Cleared {selection_type.value} selections")
    
    def get_metadata(self, path: Path) -> Optional[Dict[str, Any]]:
        """Get metadata for a selected object."""
        item = self._selections.get(str(path))
        return item.metadata if item else None
    
    def update_metadata(self, path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a selected object.
        
        Returns:
            True if metadata was updated, False if object not selected
        """
        item = self._selections.get(str(path))
        if item:
            item.metadata.update(metadata)
            logger.debug(f"Updated metadata for {path.name}")
            return True
        return False
    
    def _update_legacy_lists(self):
        """Update legacy selection lists for backward compatibility."""
        # Update legacy image list
        self._legacy_selected_images.clear()
        self._legacy_selected_images.extend(
            self.get_selected_paths(SelectionType.IMAGE)
        )
        
        # Update legacy model list (includes both MODEL_3D and TEXTURED_MODEL)
        self._legacy_selected_models.clear()
        self._legacy_selected_models.extend(
            self.get_selected_paths(SelectionType.MODEL_3D)
        )
        self._legacy_selected_models.extend(
            self.get_selected_paths(SelectionType.TEXTURED_MODEL)
        )
    
    # Legacy compatibility properties
    @property
    def selected_images(self) -> List[Path]:
        """Legacy compatibility: selected_images list"""
        return self._legacy_selected_images
    
    @property
    def selected_models(self) -> List[Path]:
        """Legacy compatibility: selected_models list"""
        return self._legacy_selected_models
    
    # Observer pattern for custom UI updates
    def add_observer(self, callback: Callable):
        """Add observer for selection changes."""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: Callable):
        """Remove observer."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """Notify all observers of selection changes."""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in selection observer: {e}")
    
    # Migration helpers
    def migrate_from_legacy_lists(self, selected_images: List[Path], selected_models: List[Path]):
        """
        Migrate from existing legacy selection lists.
        
        Args:
            selected_images: Existing selected_images list
            selected_models: Existing selected_models list
        """
        logger.info("Migrating from legacy selection lists...")
        
        # Clear current selections
        self._selections.clear()
        
        # Migrate images
        for image_path in selected_images:
            self.add_selection(image_path, SelectionType.IMAGE)
        
        # Migrate models (need to determine if they're textured or not)
        for model_path in selected_models:
            # Simple heuristic: if path contains "textured" or is in textured directory, it's textured
            if "textured" in str(model_path).lower() or "texture" in str(model_path).lower():
                selection_type = SelectionType.TEXTURED_MODEL
            else:
                selection_type = SelectionType.MODEL_3D
            
            self.add_selection(model_path, selection_type)
        
        logger.info(f"Migrated {len(selected_images)} images and {len(selected_models)} models")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about current selection state."""
        return {
            "total_selections": len(self._selections),
            "by_type": {
                sel_type.value: self.get_count(sel_type) 
                for sel_type in SelectionType
            },
            "legacy_compatibility": {
                "selected_images_count": len(self._legacy_selected_images),
                "selected_models_count": len(self._legacy_selected_models)
            },
            "selections": [
                {
                    "path": str(item.path),
                    "type": item.type.value,
                    "selected_at": item.selected_at,
                    "metadata": item.metadata
                }
                for item in self._selections.values()
            ]
        }