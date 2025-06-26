"""
Unified 3D Object Selection Widget
Tracks objects through their entire workflow: Image → 3D Model → Textured Model
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from loguru import logger


class ObjectState(Enum):
    """Object workflow states"""
    IMAGE = "image"          # 🖼️ Selected source image
    MODEL_3D = "model_3d"    # 📦 Generated 3D model  
    TEXTURED = "textured"    # 🎨 Textured model ready for Cinema4D


@dataclass
class WorkflowObject:
    """Represents a single object through the entire workflow"""
    id: str                          # Unique identifier (based on source image path)
    source_image: Optional[Path]     # Original image path
    model_3d: Optional[Path]         # Generated 3D model path  
    texture_files: List[Path]        # Associated texture files
    state: ObjectState              # Current workflow state
    selected: bool = True           # Whether object is selected
    
    @property
    def display_name(self) -> str:
        """Get display name for the object"""
        if self.model_3d:
            return self.model_3d.stem
        elif self.source_image:
            return self.source_image.stem
        else:
            return self.id
    
    @property  
    def state_icon(self) -> str:
        """Get emoji icon for current state"""
        icons = {
            ObjectState.IMAGE: "🖼️",
            ObjectState.MODEL_3D: "📦", 
            ObjectState.TEXTURED: "🎨"
        }
        return icons.get(self.state, "❓")
    
    @property
    def current_file_path(self) -> Optional[Path]:
        """Get the current file path based on state"""
        if self.state == ObjectState.TEXTURED and self.model_3d:
            return self.model_3d
        elif self.state == ObjectState.MODEL_3D and self.model_3d:
            return self.model_3d
        elif self.state == ObjectState.IMAGE and self.source_image:
            return self.source_image
        return None


class UnifiedObjectSelectionWidget(QWidget):
    """
    Unified 3D Object Selection widget that tracks objects through the entire workflow
    """
    
    # Signals
    object_selected = Signal(str, bool)      # object_id, selected
    workflow_hint_changed = Signal(str)      # hint text
    all_objects_cleared = Signal()           # all objects cleared
    selection_count_changed = Signal(int)    # total count of selected objects
    
    def __init__(self):
        super().__init__()
        self.objects: Dict[str, WorkflowObject] = {}  # object_id -> WorkflowObject
        self._setup_ui()
        
        # Widget visibility is handled by parent layout
        
    def _setup_ui(self):
        """Setup the unified object selection UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Set size policy for the main widget
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("3D OBJECT SELECTION")
        title.setObjectName("section_title")
        font = title.font()
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Object count
        self.count_label = QLabel("0 objects")
        self.count_label.setObjectName("object_count_label")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Objects list - remove fixed height constraints for dynamic sizing
        self.objects_list = QListWidget()
        # Height will be managed by parent container dynamically
        self.objects_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.objects_list.setStyleSheet("""
            QListWidget {
                background-color: #171717;
                border: 1px solid #404040;
                border-radius: 3px;
                color: #fafafa;
                padding: 4px;
                min-width: 120px;  /* Reduced for more compact panels */
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #262626;
                font-size: 12px;
                min-height: 20px;
            }
            QListWidget::item:selected {
                background-color: #22c55e;
                color: #000000;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)
        layout.addWidget(self.objects_list)
        
        # Workflow hint
        self.hint_label = QLabel("Select images to begin workflow →")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 10px;
                font-style: italic;
                padding: 4px;
                border-top: 1px solid #333;
            }
        """)
        layout.addWidget(self.hint_label)
        
        # Action buttons removed - CLEAR ALL button removed as requested
        
    def add_image_to_pool(self, image_path: Path) -> str:
        """Add an image to the object pool (available for selection)"""
        object_id = self._generate_object_id(image_path)
        
        if object_id not in self.objects:
            # Create new workflow object (not selected by default)
            self.objects[object_id] = WorkflowObject(
                id=object_id,
                source_image=image_path,
                model_3d=None,
                texture_files=[],
                state=ObjectState.IMAGE,
                selected=False,
                display_name=image_path.name
            )
            logger.debug(f"Added image {image_path.name} to object pool")
            self._update_display()
        
        return object_id
    
    def add_image_selection(self, image_path: Path) -> str:
        """Add a selected image to the workflow"""
        object_id = self._generate_object_id(image_path)
        
        if object_id in self.objects:
            # Mark existing object as selected
            self.objects[object_id].selected = True
        else:
            # Create new workflow object
            self.objects[object_id] = WorkflowObject(
                id=object_id,
                source_image=image_path,
                model_3d=None,
                texture_files=[],
                state=ObjectState.IMAGE,
                selected=True
            )
            
        self._update_display()
        logger.debug(f"Added image to workflow: {image_path.name}")
        return object_id
    
    def remove_image_selection(self, image_path: Path):
        """Remove an image selection from the workflow"""
        object_id = self._generate_object_id(image_path)
        
        if object_id in self.objects:
            obj = self.objects[object_id]
            if obj.state == ObjectState.IMAGE:
                # Remove completely if still just an image
                del self.objects[object_id]
            else:
                # Keep but mark as unselected if it has evolved
                obj.selected = False
                
        self._update_display()
        logger.debug(f"Removed image from workflow: {image_path.name}")
        
    def link_model_to_image(self, model_path: Path, source_image_path: Path):
        """Link a generated 3D model to its source image"""
        object_id = self._generate_object_id(source_image_path)
        
        if object_id in self.objects:
            obj = self.objects[object_id]
            obj.model_3d = model_path
            obj.state = ObjectState.MODEL_3D
            logger.debug(f"Linked model {model_path.name} to image {source_image_path.name}")
        else:
            # Create new object if image wasn't tracked
            self.objects[object_id] = WorkflowObject(
                id=object_id,
                source_image=source_image_path,
                model_3d=model_path,
                texture_files=[],
                state=ObjectState.MODEL_3D,
                selected=True
            )
            logger.debug(f"Created new workflow object for model: {model_path.name}")
        
        # Check for automatic texture detection
        self._check_for_textures(object_id)
        self._update_display()
        
    def add_standalone_model(self, model_path: Path) -> str:
        """Add a standalone 3D model without a source image"""
        # Check if this model already exists
        for obj_id, obj in self.objects.items():
            if obj.model_3d == model_path:
                obj.selected = True
                self._update_display()
                return obj_id
        
        # Create new standalone model object
        object_id = f"standalone_{model_path.stem}"
        
        self.objects[object_id] = WorkflowObject(
            id=object_id,
            source_image=None,  # No source image
            model_3d=model_path,
            texture_files=[],
            state=ObjectState.MODEL_3D,
            selected=True
        )
        self._update_display()
        logger.debug(f"Added standalone 3D model: {model_path.name}")
        
        return object_id
    
    def _check_for_textures(self, object_id: str):
        """
        Intelligent texture detection - automatically detects if textures have been generated
        for a 3D model and updates the workflow state accordingly
        """
        if object_id not in self.objects:
            return
            
        obj = self.objects[object_id]
        if not obj.model_3d or not obj.model_3d.exists():
            return
            
        # Strategy 1: Look for texture files with similar naming
        model_dir = obj.model_3d.parent
        model_stem = obj.model_3d.stem
        
        # Common texture file patterns
        texture_patterns = [
            f"{model_stem}_texture.*",
            f"{model_stem}_diffuse.*", 
            f"{model_stem}_albedo.*",
            f"{model_stem}_base.*",
            f"texture_{model_stem}.*",
            f"textured_{model_stem}.*"
        ]
        
        found_textures = []
        for pattern in texture_patterns:
            for texture_file in model_dir.glob(pattern):
                if texture_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.exr', '.hdr']:
                    found_textures.append(texture_file)
        
        # Strategy 2: Look in common texture directories
        texture_dirs = [
            model_dir / "textures",
            model_dir / "materials", 
            model_dir.parent / "textures",
            model_dir.parent / "textured_models"
        ]
        
        for tex_dir in texture_dirs:
            if tex_dir.exists():
                for texture_file in tex_dir.glob(f"*{model_stem}*"):
                    if texture_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.exr', '.hdr']:
                        found_textures.append(texture_file)
        
        # Strategy 3: Look for textured model variants
        textured_model_patterns = [
            f"textured_{model_stem}.*",
            f"{model_stem}_textured.*",
            f"{model_stem}_with_texture.*"
        ]
        
        for pattern in textured_model_patterns:
            for textured_model in model_dir.glob(pattern):
                if textured_model.suffix.lower() in ['.glb', '.gltf', '.obj', '.fbx']:
                    # Found a textured version of the model
                    obj.model_3d = textured_model  # Update to textured version
                    obj.state = ObjectState.TEXTURED
                    logger.debug(f"🎨 Auto-detected textured model: {textured_model.name}")
                    return
        
        # Update texture files if found
        if found_textures:
            obj.texture_files = found_textures
            if obj.state == ObjectState.MODEL_3D:  # Don't downgrade from TEXTURED
                obj.state = ObjectState.TEXTURED
                logger.debug(f"🎨 Auto-detected textures for {obj.display_name}: {len(found_textures)} files")
    
    def auto_detect_workflow_evolution(self):
        """
        Periodically scan for workflow evolution (new models, textures)
        Call this method when files might have been generated
        """
        for object_id in list(self.objects.keys()):
            self._check_for_textures(object_id)
        
        self._update_display()
        logger.debug("🔄 Completed automatic workflow evolution scan")
    
    def clear_all_selections(self):
        """Clear all selected objects and reset the display"""
        self.objects.clear()
        self._update_display()
        self.all_objects_cleared.emit()
        logger.debug("🧹 Cleared all object selections")
    
    def get_selection_summary(self) -> Dict[str, int]:
        """Get a summary of current selections by state"""
        summary = {state.value: 0 for state in ObjectState}
        for obj in self.objects.values():
            if obj.selected:
                summary[obj.state.value] += 1
        return summary
    
    def remove_object(self, object_id: str):
        """Remove or deselect an object by its ID"""
        if object_id in self.objects:
            obj = self.objects[object_id]
            
            # If it's a standalone model with no source image, remove completely
            if obj.source_image is None:
                del self.objects[object_id]
                logger.debug(f"Removed standalone object: {object_id}")
            else:
                # For workflow objects, just mark as unselected
                obj.selected = False
                logger.debug(f"Deselected workflow object: {object_id}")
                
            self._update_display()
        else:
            logger.warning(f"Object not found for removal: {object_id}")
    
    def mark_as_textured(self, model_path: Path, texture_files: List[Path] = None):
        """Mark a model as textured"""
        # Find object by model path
        for obj in self.objects.values():
            if obj.model_3d == model_path:
                obj.state = ObjectState.TEXTURED
                if texture_files:
                    obj.texture_files = texture_files
                logger.debug(f"Marked {model_path.name} as textured")
                break
                
        self._update_display()
        
    def get_selected_objects(self, state: ObjectState = None) -> List[WorkflowObject]:
        """Get selected objects, optionally filtered by state"""
        selected = [obj for obj in self.objects.values() if obj.selected]
        
        if state:
            selected = [obj for obj in selected if obj.state == state]
            
        return selected
    
    def get_current_file_paths(self) -> List[Path]:
        """Get current file paths for all selected objects"""
        paths = []
        for obj in self.objects.values():
            if obj.selected and obj.current_file_path:
                paths.append(obj.current_file_path)
        return paths
        
    def clear_all_objects(self):
        """Clear all objects from the workflow"""
        self.objects.clear()
        self._update_display()
        self.all_objects_cleared.emit()
        logger.info("Cleared all workflow objects")
        
    def _generate_object_id(self, image_path: Path) -> str:
        """Generate unique object ID based on source image"""
        return f"obj_{image_path.stem}"
        
    def _update_display(self):
        """Update the visual display of objects"""
        # Skip update if widget isn't properly initialized
        if not hasattr(self, 'objects_list') or self.objects_list is None:
            logger.warning(f"_update_display called on uninitialized widget {id(self)}")
            return
            
        self.objects_list.clear()
        
        selected_objects = [obj for obj in self.objects.values() if obj.selected]
        
        # Update count
        count = len(selected_objects)
        self.count_label.setText(f"{count} object{'s' if count != 1 else ''}")
        
        # Add objects to list
        for obj in selected_objects:
            item_text = f"{obj.state_icon} {obj.display_name}"
            
            # Add progress indicator if object has evolved
            if obj.source_image and obj.model_3d:
                if obj.state == ObjectState.TEXTURED:
                    item_text += " (🖼️→📦→🎨)"
                else:
                    item_text += " (🖼️→📦)"
                    
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, obj.id)  # Store object ID
            self.objects_list.addItem(item)
            
        # Update workflow hint
        self._update_workflow_hint(selected_objects)
        
        # Force Qt to refresh the display
        # Note: In PySide6, update() on widgets doesn't need parameters
        # But we'll use repaint() for immediate update instead
        self.objects_list.repaint()
        self.repaint()
        
        # Process events to ensure immediate update only if widget is properly parented
        if self.parent() is not None:
            from PySide6.QtCore import QCoreApplication
            QCoreApplication.processEvents()
        
        # Emit selection count changed signal for dynamic sizing
        self.selection_count_changed.emit(count)
        
    def _update_workflow_hint(self, selected_objects: List[WorkflowObject]):
        """Update the workflow hint based on current selection"""
        if not selected_objects:
            hint = "Select images to begin workflow →"
        else:
            # Analyze object states to determine next step
            has_images = any(obj.state == ObjectState.IMAGE for obj in selected_objects)
            has_models = any(obj.state == ObjectState.MODEL_3D for obj in selected_objects)
            has_textured = any(obj.state == ObjectState.TEXTURED for obj in selected_objects)
            
            if has_images and not has_models:
                hint = "→ Generate 3D models from selected images"
            elif has_models and not has_textured:
                hint = "→ Apply textures to selected 3D models"
            elif has_textured:
                hint = "→ Import textured models to Cinema4D"
            else:
                # Mixed states
                steps = []
                if has_images:
                    steps.append("Generate 3D models")
                if has_models:
                    steps.append("Apply textures")
                if has_textured:
                    steps.append("Import to Cinema4D")
                hint = f"→ Next: {' • '.join(steps)}"
                
        self.hint_label.setText(hint)
        self.workflow_hint_changed.emit(hint)
        
    def _setup_test_object(self):
        """Setup test object to demonstrate functionality"""
        def create_test_object():
            # Create a test image object
            test_image_path = Path("test_image.png")
            self.add_image_selection(test_image_path)
            logger.info("Test object added to unified object selector")
            
        # Use QTimer to delay test object creation
        QTimer.singleShot(2000, create_test_object)