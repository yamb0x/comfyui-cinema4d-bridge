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
    QLabel, QPushButton, QFrame
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
        self.count_label.setObjectName("connection_info")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Objects list
        self.objects_list = QListWidget()
        self.objects_list.setMaximumHeight(200)
        self.objects_list.setMinimumHeight(80)
        self.objects_list.setStyleSheet("""
            QListWidget {
                background-color: #171717;
                border: 1px solid #404040;
                border-radius: 3px;
                color: #fafafa;
                padding: 4px;
                width: 220px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #262626;
                font-size: 11px;
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
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setObjectName("secondary_btn")
        self.clear_btn.clicked.connect(self.clear_all_objects)
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
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
            logger.info(f"Added image {image_path.name} to object pool")
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
        logger.info(f"Added image to workflow: {image_path.name}")
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
        logger.info(f"Removed image from workflow: {image_path.name}")
        
    def link_model_to_image(self, model_path: Path, source_image_path: Path):
        """Link a generated 3D model to its source image"""
        object_id = self._generate_object_id(source_image_path)
        
        if object_id in self.objects:
            obj = self.objects[object_id]
            obj.model_3d = model_path
            obj.state = ObjectState.MODEL_3D
            logger.info(f"Linked model {model_path.name} to image {source_image_path.name}")
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
            logger.info(f"Created new workflow object for model: {model_path.name}")
            
        self._update_display()
        
    def mark_as_textured(self, model_path: Path, texture_files: List[Path] = None):
        """Mark a model as textured"""
        # Find object by model path
        for obj in self.objects.values():
            if obj.model_3d == model_path:
                obj.state = ObjectState.TEXTURED
                if texture_files:
                    obj.texture_files = texture_files
                logger.info(f"Marked {model_path.name} as textured")
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