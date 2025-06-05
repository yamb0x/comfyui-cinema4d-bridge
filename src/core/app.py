"""
Main application window and UI
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QTextEdit, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QListWidget,
    QListWidgetItem, QGridLayout, QGroupBox, QFileDialog,
    QMessageBox, QProgressBar, QSlider, QFrame, QScrollArea,
    QSizePolicy, QHeaderView, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QImage
from qasync import asyncSlot

from loguru import logger

from core.config_adapter import AppConfig
from core.workflow_manager import WorkflowManager
from core.file_monitor import FileMonitor, AssetTracker
from mcp.comfyui_client import ComfyUIClient
from mcp.cinema4d_client import Cinema4DClient, C4DDeformerType, C4DClonerMode
from ui.widgets import ImageGridWidget, Model3DPreviewWidget, ConsoleWidget
from ui.styles import get_dark_stylesheet, get_available_themes
from ui.fonts import get_font_manager, load_project_fonts
from pipeline.stages import PipelineStage, ImageGenerationStage, Model3DGenerationStage, SceneAssemblyStage, ExportStage
from utils.logger import LoggerMixin


class ComfyToC4DApp(QMainWindow, LoggerMixin):
    """Main application window"""
    
    # Signals
    file_generated = Signal(Path, str)  # path, type
    pipeline_progress = Signal(str, float)  # stage, progress
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        
        # Core components
        self.workflow_manager = WorkflowManager(config.workflows_dir)
        self.file_monitor = FileMonitor()
        self.asset_tracker = AssetTracker()
        self.comfyui_client = ComfyUIClient(
            config.mcp.comfyui_server_url,
            config.mcp.comfyui_websocket_url
        )
        self.c4d_client = Cinema4DClient(
            config.paths.cinema4d_path,
            config.mcp.cinema4d_port
        )
        
        # Pipeline stages
        self.stages: Dict[str, PipelineStage] = {}
        
        # UI state
        self.current_stage = 0
        self.selected_images: List[Path] = []
        self.selected_models: List[Path] = []
        self.stage_buttons = []  # Initialize empty list since we use tabs now
        
        # Image grid state
        self.image_slots = []
        self.image_labels = []
        self.image_paths = []
        
        # Initialize UI components that are referenced later
        self.asset_tree = None
        self.queue_list = None
        
        # Setup UI
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("ComfyUI to Cinema4D Bridge")
        self.setGeometry(100, 100, 2544, 1368)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header - exactly like reference design
        header_widget = QWidget()
        header_widget.setObjectName("main_header")
        header_widget.setFixedHeight(60)  # Reduced height
        header_main_layout = QHBoxLayout(header_widget)
        header_main_layout.setContentsMargins(20, 15, 20, 15)
        header_main_layout.setSpacing(0)
        
        # Connection status indicators on the left
        status_indicators = QWidget()
        status_layout = QHBoxLayout(status_indicators)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(30)
        status_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # ComfyUI status
        comfyui_container = QWidget()
        comfyui_layout = QVBoxLayout(comfyui_container)
        comfyui_layout.setContentsMargins(0, 0, 0, 0)
        comfyui_layout.setSpacing(2)
        comfyui_layout.setAlignment(Qt.AlignLeft)
        
        # ComfyUI main status line
        comfyui_main = QWidget()
        comfyui_main_layout = QHBoxLayout(comfyui_main)
        comfyui_main_layout.setContentsMargins(0, 0, 0, 0)
        comfyui_main_layout.setSpacing(6)
        
        self.comfyui_circle = QLabel("●")
        self.comfyui_circle.setObjectName("status_circle_disconnected")
        self.comfyui_status = QLabel("ComfyUI")
        self.comfyui_status.setObjectName("status_text")
        
        comfyui_main_layout.addWidget(self.comfyui_circle)
        comfyui_main_layout.addWidget(self.comfyui_status)
        
        # ComfyUI address info
        self.comfyui_info = QLabel("localhost:8188")
        self.comfyui_info.setObjectName("connection_info")
        
        comfyui_layout.addWidget(comfyui_main)
        comfyui_layout.addWidget(self.comfyui_info)
        
        # Cinema4D status
        c4d_container = QWidget()
        c4d_layout = QVBoxLayout(c4d_container)
        c4d_layout.setContentsMargins(0, 0, 0, 0)
        c4d_layout.setSpacing(2)
        c4d_layout.setAlignment(Qt.AlignLeft)
        
        # Cinema4D main status line
        c4d_main = QWidget()
        c4d_main_layout = QHBoxLayout(c4d_main)
        c4d_main_layout.setContentsMargins(0, 0, 0, 0)
        c4d_main_layout.setSpacing(6)
        
        self.c4d_circle = QLabel("●")
        self.c4d_circle.setObjectName("status_circle_disconnected")
        self.c4d_status = QLabel("Cinema4D")
        self.c4d_status.setObjectName("status_text")
        
        c4d_main_layout.addWidget(self.c4d_circle)
        c4d_main_layout.addWidget(self.c4d_status)
        
        # Cinema4D address info
        self.c4d_info = QLabel("localhost:54321")
        self.c4d_info.setObjectName("connection_info")
        
        c4d_layout.addWidget(c4d_main)
        c4d_layout.addWidget(self.c4d_info)
        
        status_layout.addWidget(comfyui_container)
        status_layout.addWidget(c4d_container)
        status_layout.addStretch()  # Push everything to the left
        
        # Center content (title and subtitle)
        center_content = QWidget()
        center_layout = QVBoxLayout(center_content)
        center_layout.setContentsMargins(40, 0, 40, 0)  # More horizontal padding
        center_layout.setSpacing(5)
        center_layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel("ComfyUI → Cinema4D Pipeline Tool")
        title_label.setObjectName("main_title")
        title_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("BY YAMBO × CLAUDE")
        subtitle_label.setObjectName("main_subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(subtitle_label)
        
        # Add to main header layout
        header_main_layout.addWidget(status_indicators, 0)  # Don't stretch
        header_main_layout.addWidget(center_content, 1)     # Stretch to fill
        header_main_layout.addStretch(0)                    # Empty right side
        
        main_layout.addWidget(header_widget)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Remove the pipeline navigation since we have tabs
        
        # Main content area (horizontal layout)
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Scene Generator/Controls
        left_panel = self._create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Center panel - Main workspace
        center_panel = self._create_center_panel()
        content_splitter.addWidget(center_panel)
        
        # Right panel - Parameters
        right_panel = self._create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter sizes for larger window (2544px width)
        content_splitter.setSizes([400, 1600, 400])
        
        main_layout.addWidget(content_splitter)
        
        # Bottom panel (console only - remove actions)
        bottom_panel = self._create_bottom_panel()
        main_layout.addWidget(bottom_panel)
        
        # Status bar
        status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.progress_bar)
        status_bar.showMessage("Ready")
    
# Removed unused pipeline navigation method
        
    def _create_left_panel(self) -> QWidget:
        """Create left panel - Scene Generator"""
        panel = QWidget()
        panel.setFixedWidth(400)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # No header - remove the bounding box
        
        # Panel content with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 0, 30, 30)
        content_layout.setSpacing(25)
        
        # Scene Description Section
        scene_section = QWidget()
        scene_section.setObjectName("parameter_section")
        scene_layout = QVBoxLayout(scene_section)
        
        scene_title = QLabel("Positive Prompt")
        scene_title.setObjectName("section_title")
        scene_layout.addWidget(scene_title)
        
        # Main prompt input
        self.scene_prompt = QTextEdit()
        self.scene_prompt.setObjectName("prompt_input")
        self.scene_prompt.setPlaceholderText("Describe your 3D scene...")
        self.scene_prompt.setText("abstract 3D sea creature \n\nBright, Graphic, minimal, clean white background")
        self.scene_prompt.setMaximumHeight(80)
        scene_layout.addWidget(self.scene_prompt)
        
        # Magic button is now integrated into the prompt input
        
        content_layout.addWidget(scene_section)
        
        # Negative Prompt Section
        negative_section = QWidget()
        negative_section.setObjectName("parameter_section")
        negative_layout = QVBoxLayout(negative_section)
        
        negative_title = QLabel("Negative Prompt")
        negative_title.setObjectName("section_title")
        negative_layout.addWidget(negative_title)
        
        self.negative_scene_prompt = QTextEdit()
        self.negative_scene_prompt.setPlaceholderText("What to avoid...")
        self.negative_scene_prompt.setText("low quality, blurry, artifacts, distorted")
        self.negative_scene_prompt.setMaximumHeight(40)
        negative_layout.addWidget(self.negative_scene_prompt)
        
        content_layout.addWidget(negative_section)
        
        # Style Preset Section
        style_section = QWidget()
        style_section.setObjectName("parameter_section")
        style_layout = QVBoxLayout(style_section)
        
        style_title = QLabel("Style Preset")
        style_title.setObjectName("section_title")
        style_layout.addWidget(style_title)
        
        self.style_preset = QComboBox()
        self.style_preset.addItems([
            "yamb0x_underwater_v2.1",
            "Clean Studio - White Background",
            "Clean Studio - Transparent", 
            "Minimal Clay Render",
            "Wireframe Preview",
            "Flat Illustration",
            "Technical Blueprint"
        ])
        self.style_preset.setCurrentText("yamb0x_underwater_v2.1")
        style_layout.addWidget(self.style_preset)
        
        content_layout.addWidget(style_section)
        
        # Image Generation Controls Section
        generation_section = QWidget()
        generation_section.setObjectName("parameter_section")
        generation_layout = QVBoxLayout(generation_section)
        
        generation_title = QLabel("Image Generation")
        generation_title.setObjectName("section_title")
        generation_layout.addWidget(generation_title)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Images")
        self.generate_btn.setObjectName("generate_btn")
        self.generate_btn.setMinimumHeight(40)
        generation_layout.addWidget(self.generate_btn)
        
        # Refresh images button
        self.refresh_images_btn = QPushButton("Refresh Images")
        self.refresh_images_btn.setObjectName("secondary_btn")
        self.refresh_images_btn.setMinimumHeight(40)
        self.refresh_images_btn.setToolTip("Manually check for new images")
        generation_layout.addWidget(self.refresh_images_btn)
        
        # Batch size control
        batch_layout = QHBoxLayout()
        batch_label = QLabel("Batch Size:")
        batch_label.setObjectName("section_title")
        self.batch_size = QSpinBox()
        self.batch_size.setMinimum(1)
        self.batch_size.setMaximum(12)
        self.batch_size.setValue(4)
        self.batch_size.valueChanged.connect(self.update_image_grid)
        batch_layout.addWidget(batch_label)
        batch_layout.addWidget(self.batch_size)
        batch_layout.addStretch()
        generation_layout.addLayout(batch_layout)
        
        content_layout.addWidget(generation_section)
        
        # Object Generation Preview
        object_section = QWidget()
        object_section.setObjectName("parameter_section")
        object_layout = QVBoxLayout(object_section)
        
        object_title = QLabel("Object Generation Preview")
        object_title.setObjectName("section_title")
        object_layout.addWidget(object_title)
        
        # Object counts container
        object_counts = QWidget()
        object_counts.setObjectName("object_preview_container")
        counts_layout = QVBoxLayout(object_counts)
        
        # Selected images display - dynamically populated based on picked images
        self.selected_images_display = QWidget()
        selected_layout = QVBoxLayout(self.selected_images_display)
        selected_layout.setContentsMargins(0, 0, 0, 0)
        selected_layout.setSpacing(4)
        
        # Initial message
        self.no_selection_label = QLabel("No images selected.\nPick images to see object counts.")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #666666; font-size: 11px; padding: 20px;")
        selected_layout.addWidget(self.no_selection_label)
        
        counts_layout.addWidget(self.selected_images_display)
        
        object_layout.addWidget(object_counts)
        content_layout.addWidget(object_section)
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        return panel
        
    def _generate_random_prompt(self):
        """Generate a random scene prompt"""
        prompts = [
            "A futuristic cityscape with floating buildings, neon lights, and flying vehicles",
            "An enchanted forest with bioluminescent plants, fairy creatures, and crystal formations",
            "A steampunk workshop filled with gears, pipes, steam engines, and mechanical inventions",
            "An alien planet surface with strange rock formations, exotic vegetation, and mysterious structures",
            "A post-apocalyptic wasteland with ruined buildings, overgrown vegetation, and makeshift shelters",
            "A magical library with floating books, glowing orbs, and spiraling staircases",
            "An underwater temple with ancient statues, coral gardens, and schools of tropical fish",
            "A cyberpunk alley with holographic signs, rain effects, and tech-modified characters"
        ]
        import random
        self.scene_prompt.setText(random.choice(prompts))
        
# Removed old unused code that was causing issues
    
    def _create_center_panel(self) -> QWidget:
        """Create center panel with stage-specific content"""
        panel = QWidget()
        panel.setObjectName("content_area")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for different stages
        self.stage_stack = QTabWidget()
        self.stage_stack.setTabBarAutoHide(False)  # Show tabs since we removed pipeline nav
        self.stage_stack.currentChanged.connect(self._select_stage)
        
        # Stage 1: Image Generation
        self.image_gen_widget = self._create_image_generation_ui()
        self.stage_stack.addTab(self.image_gen_widget, "Image Generation")
        
        # Stage 2: 3D Model Generation
        self.model_gen_widget = self._create_model_generation_ui()
        self.stage_stack.addTab(self.model_gen_widget, "3D Model Generation")
        
        # Stage 3: Scene Assembly
        self.scene_assembly_widget = self._create_scene_assembly_ui()
        self.stage_stack.addTab(self.scene_assembly_widget, "Scene Assembly")
        
        # Stage 4: Export
        self.export_widget = self._create_export_ui()
        self.stage_stack.addTab(self.export_widget, "Export")
        
        layout.addWidget(self.stage_stack)
        
        return panel
    
    def _create_image_generation_ui(self) -> QWidget:
        """Create UI for image generation stage - full screen for images"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Generated Images")
        title_label.setObjectName("section_title")
        layout.addWidget(title_label)
        
        # Image grid - takes full available space
        images_scroll = QScrollArea()
        images_scroll.setWidgetResizable(True)
        images_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        images_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        images_widget = QWidget()
        self.images_grid_layout = QGridLayout(images_widget)
        self.images_grid_layout.setSpacing(20)  # Dynamic padding
        self.images_grid_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create image slots dynamically based on batch size
        self.image_slots = []
        self.update_image_grid(4)  # Default 4 images
        
        images_scroll.setWidget(images_widget)
        layout.addWidget(images_scroll)  # Takes all remaining space
        
        return widget
    
    def update_image_grid(self, count):
        """Update image grid based on batch size"""
        # Clear existing image slots
        for slot in getattr(self, 'image_slots', []):
            slot.setParent(None)
        
        self.image_slots = []
        self.image_labels = []  # Keep track of image labels for loading
        self.image_paths = [None] * count  # Track which images are loaded
        
        # Fixed 3-column layout with line breaks after 3 images
        cols = 3
        rows = (count + cols - 1) // cols
        
        for i in range(count):
            image_slot = QWidget()
            image_slot.setObjectName("image_slot")
            image_slot.setFixedSize(512, 512)  # Full 512x512 size
            
            slot_layout = QVBoxLayout(image_slot)
            slot_layout.setContentsMargins(8, 8, 8, 8)
            slot_layout.setSpacing(8)
            
            # Main image area
            image_label = QLabel(f"Waiting for Image {i+1}...")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setObjectName("image_placeholder")
            image_label.setFixedHeight(460)  # Leave room for buttons
            image_label.setStyleSheet("""
                QLabel#image_placeholder {
                    border: 2px dashed #cccccc;
                    border-radius: 8px;
                    background-color: #f8f8f8;
                    color: #666666;
                    font-size: 14px;
                }
            """)
            slot_layout.addWidget(image_label)
            self.image_labels.append(image_label)
            
            # Action buttons row
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(8)
            
            # Download button
            download_btn = QPushButton("⬇")
            download_btn.setObjectName("action_btn")
            download_btn.setToolTip("Download image")
            download_btn.setFixedSize(32, 32)
            download_btn.setEnabled(False)  # Disabled until image loads
            download_btn.clicked.connect(lambda checked, idx=i: self._download_image(idx))
            
            # Pick button  
            pick_btn = QPushButton("✓")
            pick_btn.setObjectName("action_btn_primary")
            pick_btn.setToolTip("Pick for 3D generation")
            pick_btn.setFixedSize(32, 32)
            pick_btn.setEnabled(False)  # Disabled until image loads
            pick_btn.clicked.connect(lambda checked, idx=i: self._pick_image(idx))
            
            actions_layout.addWidget(download_btn)
            actions_layout.addStretch()
            actions_layout.addWidget(pick_btn)
            
            slot_layout.addLayout(actions_layout)
            
            # Store button references for enabling later
            image_slot.download_btn = download_btn
            image_slot.pick_btn = pick_btn
            
            # Add to grid with 3-column layout
            row = i // cols
            col = i % cols
            self.images_grid_layout.addWidget(image_slot, row, col)
            self.image_slots.append(image_slot)
        
        # Add dynamic spacing - adjust grid spacing based on available space
        total_width = 3 * 512  # 3 columns * 512px each
        available_width = 1600 - 80  # Center panel width minus margins
        if available_width > total_width:
            extra_space = available_width - total_width
            spacing = min(extra_space // 4, 40)  # Max 40px spacing
            self.images_grid_layout.setHorizontalSpacing(spacing)
            self.images_grid_layout.setVerticalSpacing(30)  # Vertical spacing between rows
    
    def _pick_image(self, image_index):
        """Handle image picking for 3D generation"""
        if image_index < len(self.image_paths) and self.image_paths[image_index]:
            image_path = self.image_paths[image_index]
            if image_path not in self.selected_images:
                self.selected_images.append(image_path)
                # Update button appearance
                self.image_slots[image_index].pick_btn.setStyleSheet(
                    "QPushButton { background-color: #4CAF50; color: white; }"
                )
                self.image_slots[image_index].pick_btn.setText("✓")
                self.logger.info(f"Selected image {image_path.name} for 3D generation")
            else:
                # Deselect
                self.selected_images.remove(image_path)
                self.image_slots[image_index].pick_btn.setStyleSheet("")
                self.image_slots[image_index].pick_btn.setText("✓")
                self.logger.info(f"Deselected image {image_path.name}")
            
            # Update object generation preview
            self._update_object_generation_preview()
    
    def _update_object_generation_preview(self):
        """Update the object generation preview based on selected images"""
        # Clear existing display
        for i in reversed(range(self.selected_images_display.layout().count())):
            child = self.selected_images_display.layout().itemAt(i).widget()
            if child:
                child.setParent(None)
        
        layout = self.selected_images_display.layout()
        
        if not self.selected_images:
            # Show "no selection" message
            self.no_selection_label = QLabel("No images selected.\nPick images to see object counts.")
            self.no_selection_label.setAlignment(Qt.AlignCenter)
            self.no_selection_label.setStyleSheet("color: #666666; font-size: 11px; padding: 20px;")
            layout.addWidget(self.no_selection_label)
        else:
            # Show selected images with estimated object counts
            title_label = QLabel(f"Selected Images ({len(self.selected_images)}):")
            title_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-bottom: 8px;")
            layout.addWidget(title_label)
            
            # Object type estimates based on number of selected images
            object_types = [
                ("Corals", 3),
                ("Fish", 5), 
                ("Ruins", 1),
                ("Seaweed", 8),
                ("AI Creatures", 2)
            ]
            
            total_objects = 0
            for obj_type, base_count in object_types:
                # Scale count by number of selected images
                estimated_count = base_count * len(self.selected_images)
                total_objects += estimated_count
                
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 2, 0, 2)
                
                name_label = QLabel(obj_type)
                name_label.setStyleSheet("font-size: 10px;")
                count_label = QLabel(str(estimated_count))
                count_label.setStyleSheet("font-size: 10px; color: #888888; font-weight: bold;")
                count_label.setFixedWidth(30)
                count_label.setAlignment(Qt.AlignRight)
                
                row_layout.addWidget(name_label)
                row_layout.addStretch()
                row_layout.addWidget(count_label)
                
                layout.addWidget(row_widget)
            
            # Total display
            total_widget = QWidget()
            total_layout = QHBoxLayout(total_widget)
            total_layout.setContentsMargins(0, 8, 0, 0)
            total_label = QLabel(f"Total: {total_objects} objects")
            total_label.setStyleSheet("font-size: 11px; color: #333333; font-weight: bold;")
            total_label.setAlignment(Qt.AlignCenter)
            total_layout.addWidget(total_label)
            layout.addWidget(total_widget)
    
    def _download_image(self, image_index):
        """Handle image download"""
        if image_index < len(self.image_paths) and self.image_paths[image_index]:
            image_path = self.image_paths[image_index]
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Image", 
                f"{image_path.stem}.png",
                "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
            )
            if save_path:
                try:
                    import shutil
                    shutil.copy2(image_path, save_path)
                    self.logger.info(f"Downloaded image to {save_path}")
                    QMessageBox.information(self, "Download Complete", 
                                           f"Image saved to:\n{save_path}")
                except Exception as e:
                    self.logger.error(f"Failed to download image: {e}")
                    QMessageBox.warning(self, "Download Failed", 
                                       f"Failed to save image: {str(e)}")
    
    def _create_model_generation_ui(self) -> QWidget:
        """Create UI for 3D model generation stage"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Selected images
        selected_group = QGroupBox("Selected Images")
        selected_layout = QVBoxLayout(selected_group)
        
        self.selected_images_list = QListWidget()
        self.selected_images_list.setMaximumHeight(100)
        selected_layout.addWidget(self.selected_images_list)
        
        layout.addWidget(selected_group)
        
        # 3D generation controls
        controls_layout = QHBoxLayout()
        
        self.generate_3d_btn = QPushButton("Generate 3D Models")
        self.generate_3d_btn.setObjectName("generate_3d_btn")
        self.generate_3d_btn.setMinimumHeight(40)
        controls_layout.addWidget(self.generate_3d_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # 3D preview grid
        self.model_grid = Model3DPreviewWidget()
        self.model_grid.setMinimumHeight(400)
        layout.addWidget(self.model_grid)
        
        return widget
    
    def _create_scene_assembly_ui(self) -> QWidget:
        """Create UI for scene assembly stage"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scene controls
        controls_group = QGroupBox("Scene Assembly Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Import controls
        import_layout = QHBoxLayout()
        self.import_selected_btn = QPushButton("Import Selected to C4D")
        self.import_selected_btn.setObjectName("import_selected_btn")
        self.import_all_btn = QPushButton("Import All")
        import_layout.addWidget(self.import_selected_btn)
        import_layout.addWidget(self.import_all_btn)
        import_layout.addStretch()
        controls_layout.addLayout(import_layout)
        
        # Deformer controls
        deformer_layout = QHBoxLayout()
        deformer_layout.addWidget(QLabel("Add Deformer:"))
        self.deformer_combo = QComboBox()
        self.deformer_combo.addItems([d.value for d in C4DDeformerType])
        self.apply_deformer_btn = QPushButton("Apply")
        deformer_layout.addWidget(self.deformer_combo)
        deformer_layout.addWidget(self.apply_deformer_btn)
        deformer_layout.addStretch()
        controls_layout.addLayout(deformer_layout)
        
        # Cloner controls
        cloner_layout = QHBoxLayout()
        cloner_layout.addWidget(QLabel("Create Cloner:"))
        self.cloner_mode_combo = QComboBox()
        self.cloner_mode_combo.addItems([m.value for m in C4DClonerMode])
        self.cloner_count = QSpinBox()
        self.cloner_count.setMinimum(1)
        self.cloner_count.setMaximum(1000)
        self.cloner_count.setValue(10)
        self.create_cloner_btn = QPushButton("Create")
        cloner_layout.addWidget(self.cloner_mode_combo)
        cloner_layout.addWidget(QLabel("Count:"))
        cloner_layout.addWidget(self.cloner_count)
        cloner_layout.addWidget(self.create_cloner_btn)
        cloner_layout.addStretch()
        controls_layout.addLayout(cloner_layout)
        
        layout.addWidget(controls_group)
        
        # Scene object list
        objects_group = QGroupBox("Scene Objects")
        objects_layout = QVBoxLayout(objects_group)
        
        self.scene_objects_table = QTableWidget()
        self.scene_objects_table.setColumnCount(4)
        self.scene_objects_table.setHorizontalHeaderLabels(["Name", "Type", "Position", "Children"])
        objects_layout.addWidget(self.scene_objects_table)
        
        # Refresh button
        self.refresh_scene_btn = QPushButton("Refresh Scene")
        objects_layout.addWidget(self.refresh_scene_btn)
        
        layout.addWidget(objects_group)
        
        return widget
    
    def _create_export_ui(self) -> QWidget:
        """Create UI for export stage"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Export settings
        settings_group = QGroupBox("Export Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Project name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Project Name:"))
        self.project_name = QLineEdit()
        self.project_name.setText(f"ComfyC4D_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        name_layout.addWidget(self.project_name)
        settings_layout.addLayout(name_layout)
        
        # Export path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Export Path:"))
        self.export_path = QLineEdit()
        self.export_path.setText(str(self.config.base_dir / "exports"))
        self.browse_export_btn = QPushButton("Browse...")
        path_layout.addWidget(self.export_path)
        path_layout.addWidget(self.browse_export_btn)
        settings_layout.addLayout(path_layout)
        
        # Export options
        self.copy_textures_check = QCheckBox("Copy textures to project")
        self.copy_textures_check.setChecked(True)
        self.create_backup_check = QCheckBox("Create backup")
        self.create_backup_check.setChecked(True)
        self.generate_report_check = QCheckBox("Generate scene report")
        self.generate_report_check.setChecked(True)
        
        settings_layout.addWidget(self.copy_textures_check)
        settings_layout.addWidget(self.create_backup_check)
        settings_layout.addWidget(self.generate_report_check)
        
        layout.addWidget(settings_group)
        
        # Export button
        self.export_btn = QPushButton("Export Cinema4D Project")
        self.export_btn.setObjectName("export_btn")
        self.export_btn.setMinimumHeight(50)
        layout.addWidget(self.export_btn)
        
        # Export log
        log_group = QGroupBox("Export Log")
        log_layout = QVBoxLayout(log_group)
        
        self.export_log = QTextEdit()
        self.export_log.setReadOnly(True)
        log_layout.addWidget(self.export_log)
        
        layout.addWidget(log_group)
        
        return widget
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel - Parameters"""
        panel = QWidget()
        panel.setFixedWidth(400)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # No header - remove the bounding box
        
        # Scrollable parameters area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create stacked widget for different parameter sets
        from PySide6.QtWidgets import QStackedWidget
        self.params_stack = QStackedWidget()
        
        # Create parameter widgets for each stage
        self.image_params_widget = self._create_image_parameters()
        self.model_3d_params_widget = self._create_3d_parameters()
        self.scene_params_widget = self._create_scene_parameters()
        self.export_params_widget = self._create_export_parameters()
        
        # Add to stack
        self.params_stack.addWidget(self.image_params_widget)
        self.params_stack.addWidget(self.model_3d_params_widget)
        self.params_stack.addWidget(self.scene_params_widget)
        self.params_stack.addWidget(self.export_params_widget)
        
        scroll_area.setWidget(self.params_stack)
        layout.addWidget(scroll_area)
        
        return panel
    
    def _create_image_parameters(self) -> QWidget:
        """Create image generation parameters widget - matching scene generator layout quality"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 0, 30, 30)
        layout.setSpacing(15)  # Reduced from 25 to 15
        
        # Model Section - following scene generator pattern
        model_section = self._create_param_section("Generation Parameters")
        model_content_layout = model_section.layout()
        
        # Model selection
        self._add_clean_param_row(model_content_layout, "Model")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["flux1-dev-fp8.safetensors", "flux1-schnell-fp8.safetensors"])
        self.model_combo.setCurrentText("flux1-dev-fp8.safetensors")
        model_content_layout.addWidget(self.model_combo)
        
        # Resolution  
        self._add_clean_param_row(model_content_layout, "Resolution")
        res_container = QWidget()
        res_layout = QHBoxLayout(res_container)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setSpacing(8)
        
        self.width_spin = QSpinBox()
        self.width_spin.setMinimum(256)
        self.width_spin.setMaximum(1024)
        self.width_spin.setSingleStep(64)
        self.width_spin.setValue(512)
        self.width_spin.setFixedWidth(70)
        
        self.height_spin = QSpinBox()
        self.height_spin.setMinimum(256)
        self.height_spin.setMaximum(1024)
        self.height_spin.setSingleStep(64)
        self.height_spin.setValue(512)
        self.height_spin.setFixedWidth(70)
        
        res_layout.addWidget(self.width_spin)
        res_layout.addWidget(QLabel("×"))
        res_layout.addWidget(self.height_spin)
        res_layout.addStretch()
        model_content_layout.addWidget(res_container)
        
        # Steps
        self._add_clean_param_row(model_content_layout, "Steps")
        self.steps_spin = QSpinBox()
        self.steps_spin.setMinimum(1)
        self.steps_spin.setMaximum(150)
        self.steps_spin.setValue(20)
        model_content_layout.addWidget(self.steps_spin)
        
        # CFG Scale
        self._add_clean_param_row(model_content_layout, "CFG Scale")
        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setMinimum(0.5)
        self.cfg_spin.setMaximum(10.0)
        self.cfg_spin.setSingleStep(0.1)
        self.cfg_spin.setValue(1.0)
        self.cfg_spin.setToolTip("CFG Scale for FLUX models. Range: 0.5-4.0 typical, 1.0-2.0 recommended.")
        model_content_layout.addWidget(self.cfg_spin)
        
        # Sampler
        self._add_clean_param_row(model_content_layout, "Sampler")
        self.sampler_combo = QComboBox()
        self.sampler_combo.addItems([
            "euler", "euler_ancestral", "dpmpp_2m", "dpmpp_sde", "dpmpp_2m_sde",
            "heun", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", 
            "dpmpp_2s_ancestral", "dpmpp_3m_sde", "ddim", "uni_pc"
        ])
        self.sampler_combo.setCurrentText("euler")
        model_content_layout.addWidget(self.sampler_combo)
        
        # Scheduler
        self._add_clean_param_row(model_content_layout, "Scheduler")
        self.scheduler_combo = QComboBox()
        self.scheduler_combo.addItems(["simple", "normal", "karras", "exponential", "sgm_uniform", "ddim_uniform"])
        self.scheduler_combo.setCurrentText("simple")
        model_content_layout.addWidget(self.scheduler_combo)
        
        layout.addWidget(model_section)
        
        # Seed Control Section
        seed_section = self._create_param_section("Seed Control")
        seed_content_layout = seed_section.layout()
        
        # Seed value
        self._add_clean_param_row(seed_content_layout, "Seed")
        seed_container = QWidget()
        seed_layout = QHBoxLayout(seed_container)
        seed_layout.setContentsMargins(0, 0, 0, 0)
        seed_layout.setSpacing(6)
        
        self.seed_spin = QSpinBox()
        self.seed_spin.setMinimum(-1)
        self.seed_spin.setMaximum(2147483647)
        self.seed_spin.setValue(-1)
        self.seed_spin.setSpecialValueText("Random")
        
        self.random_seed_btn = QPushButton("🎲")
        self.random_seed_btn.setFixedWidth(30)
        self.random_seed_btn.clicked.connect(self._randomize_seed)
        
        seed_layout.addWidget(self.seed_spin)
        seed_layout.addWidget(self.random_seed_btn)
        seed_content_layout.addWidget(seed_container)
        
        # After Generate
        self._add_clean_param_row(seed_content_layout, "After Generate")
        self.seed_control_combo = QComboBox()
        self.seed_control_combo.addItems(["increment", "decrement", "randomize", "fixed"])
        self.seed_control_combo.setCurrentText("increment")
        self.seed_control_combo.setToolTip("Control how seed changes after each generation")
        seed_content_layout.addWidget(self.seed_control_combo)
        
        layout.addWidget(seed_section)
        
        # LoRA Models Section
        lora_section = self._create_param_section("LoRA Models")
        lora_content_layout = lora_section.layout()
        
        # LoRA 1
        self._add_clean_param_row(lora_content_layout, "LoRA 1")
        self.lora1_combo = QComboBox()
        self.lora1_combo.addItems([
            "deep_sea_creatures_cts.safetensors",
            "aidmaFLUXpro1.1-FLUX-V0.1.safetensors",
            "Luminous_Shadowscape-000016.safetensors",
            "None"
        ])
        self.lora1_combo.setCurrentText("deep_sea_creatures_cts.safetensors")
        lora_content_layout.addWidget(self.lora1_combo)
        
        # LoRA 1 Controls  
        lora1_controls = QWidget()
        lora1_controls_layout = QHBoxLayout(lora1_controls)
        lora1_controls_layout.setContentsMargins(0, 0, 0, 0)
        lora1_controls_layout.setSpacing(8)
        
        strength1_label = QLabel("Strength:")
        strength1_label.setObjectName("section_title")
        self.lora1_strength = QDoubleSpinBox()
        self.lora1_strength.setRange(0.0, 2.0)
        self.lora1_strength.setSingleStep(0.1)
        self.lora1_strength.setValue(0.8)
        self.lora1_strength.setFixedWidth(70)
        
        self.lora1_active = QCheckBox("Active")
        self.lora1_active.setChecked(True)
        
        lora1_controls_layout.addWidget(strength1_label)
        lora1_controls_layout.addWidget(self.lora1_strength)
        lora1_controls_layout.addWidget(self.lora1_active)
        lora1_controls_layout.addStretch()
        lora_content_layout.addWidget(lora1_controls)
        
        # LoRA 2
        self._add_clean_param_row(lora_content_layout, "LoRA 2")
        self.lora2_combo = QComboBox()
        self.lora2_combo.addItems([
            "aidmaFLUXpro1.1-FLUX-V0.1.safetensors",
            "deep_sea_creatures_cts.safetensors", 
            "Luminous_Shadowscape-000016.safetensors",
            "None"
        ])
        self.lora2_combo.setCurrentText("aidmaFLUXpro1.1-FLUX-V0.1.safetensors")
        lora_content_layout.addWidget(self.lora2_combo)
        
        # LoRA 2 Controls
        lora2_controls = QWidget()
        lora2_controls_layout = QHBoxLayout(lora2_controls)
        lora2_controls_layout.setContentsMargins(0, 0, 0, 0)
        lora2_controls_layout.setSpacing(8)
        
        strength2_label = QLabel("Strength:")
        strength2_label.setObjectName("section_title")
        self.lora2_strength = QDoubleSpinBox()
        self.lora2_strength.setRange(0.0, 2.0)
        self.lora2_strength.setSingleStep(0.1)
        self.lora2_strength.setValue(0.6)
        self.lora2_strength.setFixedWidth(70)
        
        self.lora2_active = QCheckBox("Active")
        self.lora2_active.setChecked(True)
        
        lora2_controls_layout.addWidget(strength2_label)
        lora2_controls_layout.addWidget(self.lora2_strength)
        lora2_controls_layout.addWidget(self.lora2_active)
        lora2_controls_layout.addStretch()
        lora_content_layout.addWidget(lora2_controls)
        
        layout.addWidget(lora_section)
        
        # Workflow Section
        workflow_section = self._create_param_section("Workflows")
        workflow_content_layout = workflow_section.layout()
        
        self.workflow_combo = QComboBox()
        workflow_content_layout.addWidget(self.workflow_combo)
        
        workflow_btns = QWidget()
        workflow_btns_layout = QHBoxLayout(workflow_btns)
        workflow_btns_layout.setContentsMargins(0, 0, 0, 0)
        workflow_btns_layout.setSpacing(6)
        
        self.reload_workflows_btn = QPushButton("Reload")
        self.reload_workflows_btn.setObjectName("secondary_btn")
        self.save_workflow_btn = QPushButton("Save")
        self.save_workflow_btn.setObjectName("secondary_btn")
        
        workflow_btns_layout.addWidget(self.reload_workflows_btn)
        workflow_btns_layout.addWidget(self.save_workflow_btn)
        workflow_content_layout.addWidget(workflow_btns)
        
        layout.addWidget(workflow_section)
        layout.addStretch()
        
        return widget
    
    def _create_param_section(self, title: str) -> QWidget:
        """Create a parameter section matching scene generator layout"""
        section = QWidget()
        section.setObjectName("parameter_section")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(8)  # Reduced spacing
        
        section_title = QLabel(title)
        section_title.setObjectName("section_title")
        section_layout.addWidget(section_title)
        
        return section
    
    def _add_clean_param_row(self, layout: QVBoxLayout, label: str):
        """Add a clean parameter label with proper spacing"""
        # Add small spacing before label
        layout.addSpacing(2)  # Further reduced spacing
        
        label_widget = QLabel(label)
        label_widget.setObjectName("section_title")
        layout.addWidget(label_widget)
    
    def _create_3d_parameters(self) -> QWidget:
        """Create 3D model generation parameters widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 0, 30, 30)
        layout.setSpacing(20)
        
        # 3D Generation Parameters
        params_3d_group = QGroupBox("3D Generation Parameters")
        params_3d_layout = QVBoxLayout(params_3d_group)
        
        # Mesh density
        mesh_layout = QHBoxLayout()
        mesh_layout.addWidget(QLabel("Mesh Density:"))
        self.mesh_density_combo = QComboBox()
        self.mesh_density_combo.addItems(["low", "medium", "high", "ultra"])
        self.mesh_density_combo.setCurrentText("high")
        mesh_layout.addWidget(self.mesh_density_combo)
        params_3d_layout.addLayout(mesh_layout)
        
        # Texture resolution
        tex_layout = QHBoxLayout()
        tex_layout.addWidget(QLabel("Texture Res:"))
        self.texture_res_combo = QComboBox()
        self.texture_res_combo.addItems(["512", "1024", "2048", "4096"])
        self.texture_res_combo.setCurrentText("2048")
        tex_layout.addWidget(self.texture_res_combo)
        params_3d_layout.addLayout(tex_layout)
        
        # Options
        self.normal_map_check = QCheckBox("Generate Normal Map")
        self.normal_map_check.setChecked(True)
        self.optimize_mesh_check = QCheckBox("Optimize Mesh")
        self.optimize_mesh_check.setChecked(True)
        
        params_3d_layout.addWidget(self.normal_map_check)
        params_3d_layout.addWidget(self.optimize_mesh_check)
        
        layout.addWidget(params_3d_group)
        layout.addStretch()
        
        return widget
    
    def _create_scene_parameters(self) -> QWidget:
        """Create scene assembly parameters widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 0, 30, 30)
        layout.setSpacing(20)
        
        # Scene Assembly Parameters
        scene_group = QGroupBox("Scene Assembly Parameters")
        scene_layout = QVBoxLayout(scene_group)
        
        # Placeholder for future scene parameters
        placeholder = QLabel("Scene assembly parameters will be added here")
        placeholder.setAlignment(Qt.AlignCenter)
        scene_layout.addWidget(placeholder)
        
        layout.addWidget(scene_group)
        layout.addStretch()
        
        return widget
    
    def _create_export_parameters(self) -> QWidget:
        """Create export parameters widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 0, 30, 30)
        layout.setSpacing(20)
        
        # Export Parameters
        export_group = QGroupBox("Export Parameters")
        export_layout = QVBoxLayout(export_group)
        
        # Placeholder for future export parameters
        placeholder = QLabel("Export parameters will be added here")
        placeholder.setAlignment(Qt.AlignCenter)
        export_layout.addWidget(placeholder)
        
        layout.addWidget(export_group)
        layout.addStretch()
        
        return widget
    
    def _add_param_row(self, layout: QVBoxLayout, label: str, widget: QWidget):
        """Add a parameter row to layout (legacy method)"""
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(widget)
        row.addStretch()
        layout.addLayout(row)
    
    def _add_param_grid_row(self, layout: QVBoxLayout, label: str, widget: QWidget):
        """Add a parameter row using grid layout for consistency"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)
        grid_layout.setContentsMargins(0, 0, 0, 6)
        
        label_widget = QLabel(label)
        label_widget.setObjectName("section_title")
        
        grid_layout.addWidget(label_widget, 0, 0)
        grid_layout.addWidget(widget, 0, 1)
        grid_layout.setColumnStretch(2, 1)  # Push content to left
        
        row_widget = QWidget()
        row_widget.setLayout(grid_layout)
        layout.addWidget(row_widget)
    
    def _create_console(self) -> QWidget:
        """Create console widget"""
        console_group = QGroupBox("Console Output")
        console_group.setObjectName("console_group")
        console_layout = QVBoxLayout(console_group)
        
        self.console = ConsoleWidget()
        self.console.setObjectName("console")
        self.console.setMaximumHeight(150)
        console_layout.addWidget(self.console)
        
        # Console controls
        controls = QHBoxLayout()
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.clear_console_btn = QPushButton("Clear")
        controls.addWidget(self.auto_scroll_check)
        controls.addStretch()
        controls.addWidget(self.clear_console_btn)
        console_layout.addLayout(controls)
        
        return console_group
    
    def _create_bottom_panel(self) -> QWidget:
        """Create bottom panel with console only"""
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(200)
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        
        console_group = QGroupBox("Console Output")
        console_group.setObjectName("console_group")
        console_group_layout = QVBoxLayout(console_group)
        console_group_layout.setContentsMargins(20, 15, 20, 15)
        
        self.console = ConsoleWidget()
        self.console.setObjectName("console")
        console_group_layout.addWidget(self.console)
        
        # Console controls
        console_controls = QHBoxLayout()
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.clear_console_btn = QPushButton("Clear")
        console_controls.addWidget(self.auto_scroll_check)
        console_controls.addStretch()
        console_controls.addWidget(self.clear_console_btn)
        console_group_layout.addLayout(console_controls)
        
        bottom_layout.addWidget(console_group)
        
        return bottom_widget
    
    def _apply_styles(self):
        """Apply application styles"""
        themes = get_available_themes()
        
        # Use the new black theme
        theme_name = 'black'
        
        try:
            if theme_name in themes:
                stylesheet = themes[theme_name]()
                self.setStyleSheet(stylesheet)
                self.logger.info(f"Applied {theme_name} theme successfully")
            else:
                self.logger.warning(f"Theme {theme_name} not found, using dark theme")
                self.setStyleSheet(themes['dark']())
        except Exception as e:
            self.logger.error(f"Failed to apply theme: {e}")
            # Fallback to basic white theme
            self.setStyleSheet("QMainWindow { background-color: white; color: black; }")
    
    def _connect_signals(self):
        """Connect UI signals"""
        # Console
        self.clear_console_btn.clicked.connect(self.console.clear)
        
        # Workflow
        self.reload_workflows_btn.clicked.connect(self._reload_workflows)
        
        # Image generation
        self.generate_btn.clicked.connect(self._on_generate_images)
        self.refresh_images_btn.clicked.connect(self._check_for_new_images)
        self.random_seed_btn.clicked.connect(self._randomize_seed)
        
        # 3D generation
        self.generate_3d_btn.clicked.connect(self._on_generate_3d)
        
        # Scene assembly
        self.import_selected_btn.clicked.connect(self._on_import_selected)
        self.import_all_btn.clicked.connect(self._on_import_all)
        self.apply_deformer_btn.clicked.connect(self._on_apply_deformer)
        self.create_cloner_btn.clicked.connect(self._on_create_cloner)
        self.refresh_scene_btn.clicked.connect(self._on_refresh_scene)
        
        # Export
        self.browse_export_btn.clicked.connect(self._browse_export_path)
        self.export_btn.clicked.connect(self._on_export_project)
        
        # File monitor signals
        self.file_generated.connect(self._on_file_generated)
        
        # Quick action buttons removed - using tab navigation instead
        
        # Debug: Add keyboard shortcut to refresh theme (Ctrl+R)
        from PySide6.QtGui import QShortcut, QKeySequence
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self._refresh_theme)
        
        # Debug: Add keyboard shortcut to test file monitoring (Ctrl+T)
        test_monitoring_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        test_monitoring_shortcut.activated.connect(self._test_file_monitoring)
    
    async def initialize(self):
        """Initialize the application"""
        self.logger.info("Initializing application...")
        
        # Load custom fonts
        font_manager = get_font_manager()
        load_project_fonts(font_manager, self.config.base_dir)
        
        # Setup console logging
        self.console.setup_logging()
        
        # Load workflows
        self._reload_workflows()
        
        # Setup file monitoring
        self._setup_file_monitoring()
        
        # Connect to services
        await self._connect_services()
        
        # Initialize pipeline stages
        self._init_pipeline_stages()
        
        # Load any existing images
        if hasattr(self, 'image_labels') and self.image_labels:
            self._load_existing_images()
        
        self.logger.info("Application initialized")
    
    def _setup_file_monitoring(self):
        """Setup file system monitoring"""
        self.logger.info("Setting up file monitoring...")
        
        # Set the event loop for the file monitor
        loop = asyncio.get_event_loop()
        self.file_monitor.set_event_loop(loop)
        
        # Ensure directories exist
        self.config.images_dir.mkdir(parents=True, exist_ok=True)
        self.config.models_3d_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitor images directory
        self.logger.info(f"Monitoring images directory: {self.config.images_dir}")
        self.file_monitor.add_directory(
            "images",
            self.config.images_dir,
            lambda path, event: self.file_generated.emit(path, "image"),
            patterns=["*.png", "*.jpg", "*.jpeg"]
        )
        
        # Monitor 3D models directory
        self.logger.info(f"Monitoring 3D models directory: {self.config.models_3d_dir}")
        self.file_monitor.add_directory(
            "models",
            self.config.models_3d_dir,
            lambda path, event: self.file_generated.emit(path, "model"),
            patterns=["*.obj", "*.fbx", "*.gltf"]
        )
        
        self.file_monitor.start()
        self.logger.info("File monitoring started successfully")
        
        # Test if file monitor is working by checking directory
        self.logger.info(f"Monitoring directory exists: {self.config.images_dir.exists()}")
        if self.config.images_dir.exists():
            existing_images = list(self.config.images_dir.glob("*.png"))
            self.logger.info(f"Found {len(existing_images)} existing images at startup")
    
    async def _connect_services(self):
        """Connect to ComfyUI and Cinema4D"""
        # Connect to ComfyUI
        comfyui_connected = await self.comfyui_client.connect()
        if comfyui_connected:
            self.comfyui_circle.setObjectName("status_circle_connected")
            self.comfyui_status.setText("ComfyUI")
            
            # Setup callbacks
            self.comfyui_client.on("progress", self._on_comfyui_progress)
            self.comfyui_client.on("execution_complete", self._on_comfyui_complete)
            self.comfyui_client.on("execution_error", self._on_comfyui_error)
            
            # Load available models
            models = await self.comfyui_client.get_models()
            if models.get("checkpoints"):
                self.model_combo.addItems(models["checkpoints"])
        else:
            self.comfyui_circle.setObjectName("status_circle_disconnected")
            self.comfyui_status.setText("ComfyUI")
            QMessageBox.warning(self, "Connection Failed", 
                              "Failed to connect to ComfyUI. Please ensure it's running.")
        
        # Connect to Cinema4D
        c4d_connected = await self.c4d_client.connect()
        if c4d_connected:
            self.c4d_circle.setObjectName("status_circle_connected")
            self.c4d_status.setText("Cinema4D")
        else:
            self.c4d_circle.setObjectName("status_circle_disconnected")
            self.c4d_status.setText("Cinema4D")
            QMessageBox.warning(self, "Connection Failed",
                              "Failed to connect to Cinema4D. Please ensure it's running with MCP server.")
        
        # Force style update to apply connection status colors
        self._apply_styles()
    
    def _init_pipeline_stages(self):
        """Initialize pipeline stages"""
        self.stages = {
            "image_generation": ImageGenerationStage(
                self.comfyui_client,
                self.workflow_manager,
                self.config
            ),
            "model_generation": Model3DGenerationStage(
                self.comfyui_client,
                self.workflow_manager,
                self.config
            ),
            "scene_assembly": SceneAssemblyStage(
                self.c4d_client,
                self.config
            ),
            "export": ExportStage(
                self.c4d_client,
                self.config
            )
        }
    
    def _select_stage(self, stage_index: int):
        """Select pipeline stage"""
        # Switch to stage tab
        self.stage_stack.setCurrentIndex(stage_index)
        self.current_stage = stage_index
        
        # Switch parameter panel to match current stage
        if hasattr(self, 'params_stack'):
            self.params_stack.setCurrentIndex(stage_index)
        
        # Update status
        stage_names = ["Image Generation", "3D Model Generation", "Scene Assembly", "Export"]
        self.statusBar().showMessage(f"Current Stage: {stage_names[stage_index]}")
        
        # Update right panel subtitle based on stage
        if hasattr(self, 'params_subtitle'):
            subtitles = ["Image Generation Settings", "3D Model Settings", "Scene Assembly Settings", "Export Settings"]
            self.params_subtitle.setText(subtitles[stage_index])
    
    def _reload_workflows(self):
        """Reload available workflows"""
        self.workflow_combo.clear()
        workflows = self.workflow_manager.list_workflows()
        self.workflow_combo.addItems(workflows)
        
        # Select appropriate workflow based on current stage
        if self.current_stage == 0:  # Image generation
            idx = self.workflow_combo.findText(self.config.workflows.image_workflow)
            if idx >= 0:
                self.workflow_combo.setCurrentIndex(idx)
        elif self.current_stage == 1:  # 3D generation
            idx = self.workflow_combo.findText(self.config.workflows.model_3d_workflow)
            if idx >= 0:
                self.workflow_combo.setCurrentIndex(idx)
    
    def _randomize_seed(self):
        """Generate random seed"""
        import random
        self.seed_spin.setValue(random.randint(0, 2147483647))
    
    @asyncSlot()
    async def _on_generate_images(self):
        """Handle image generation"""
        try:
            # Get parameters from UI
            cfg_value = self.cfg_spin.value()
            sampler_value = self.sampler_combo.currentText()
            scheduler_value = self.scheduler_combo.currentText()
            steps_value = self.steps_spin.value()
            seed_control_value = self.seed_control_combo.currentText()
            
            self.logger.info(f"UI Parameters - CFG: {cfg_value}, Sampler: {sampler_value}, Scheduler: {scheduler_value}, Steps: {steps_value}, Seed Control: {seed_control_value}")
            
            params = {
                "positive_prompt": self.scene_prompt.toPlainText(),
                "negative_prompt": self.negative_scene_prompt.toPlainText(),
                "width": self.width_spin.value(),
                "height": self.height_spin.value(),
                "steps": steps_value,
                "cfg": cfg_value,
                "sampler_name": sampler_value,
                "scheduler": scheduler_value,
                "checkpoint": self.model_combo.currentText(),
                "seed": self.seed_spin.value() if self.seed_spin.value() >= 0 else -1,
                "seed_control": seed_control_value,
                "batch_size": self.batch_size.value(),
                # LoRA parameters
                "lora1_model": self.lora1_combo.currentText(),
                "lora1_strength": self.lora1_strength.value(),
                "lora1_active": self.lora1_active.isChecked(),
                "lora2_model": self.lora2_combo.currentText(),
                "lora2_strength": self.lora2_strength.value(),
                "lora2_active": self.lora2_active.isChecked()
            }
            
            # Load workflow - try API format first, then fallback to UI format
            workflow = self.workflow_manager.load_workflow("generate_images_api.json")
            if not workflow:
                self.logger.info("API format workflow not found, trying UI format...")
                workflow = self.workflow_manager.load_workflow("generate_images.json")
                if not workflow:
                    QMessageBox.warning(self, "Workflow Error", 
                                      "Could not load image generation workflow.")
                    return
            
            # Inject parameters
            workflow_with_params = self.workflow_manager.inject_parameters_comfyui(workflow, params)
            
            # Clear previous images and reset UI
            self._clear_image_grid()
            
            # Update UI state
            self.generate_btn.setEnabled(False)
            self.generate_btn.setText("Generating...")
            self.progress_bar.setValue(0)
            self.statusBar().showMessage("Starting image generation...")
            
            # Queue prompt with ComfyUI
            success = await self.comfyui_client.queue_prompt(workflow_with_params)
            
            if success:
                self.logger.info(f"Queued image generation with batch size {params['batch_size']}")
                # Schedule checks for new images after delays (in case file monitor misses them)
                QTimer.singleShot(5000, self._check_for_new_images)   # Check after 5 seconds
                QTimer.singleShot(15000, self._check_for_new_images)  # Check after 15 seconds
                QTimer.singleShot(35000, self._check_for_new_images)  # Check after 35 seconds (after typical FLUX generation)
            else:
                QMessageBox.warning(self, "Generation Failed", 
                                  "Failed to queue image generation. Check console for details.")
                
        except Exception as e:
            self.logger.error(f"Error in image generation: {e}")
            QMessageBox.critical(self, "Generation Error", 
                               f"An error occurred during image generation: {str(e)}")
        finally:
            # Reset UI state
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Generate Images")
    
    @asyncSlot()
    async def _on_generate_3d(self):
        """Handle 3D model generation"""
        if not self.selected_images:
            QMessageBox.warning(self, "No Images Selected",
                              "Please select images to convert to 3D.")
            return
        
        # Get parameters from 3D parameters UI
        params = {
            "mesh_density": self.mesh_density_combo.currentText(),
            "texture_resolution": int(self.texture_res_combo.currentText()),
            "normal_map": self.normal_map_check.isChecked(),
            "optimize_mesh": self.optimize_mesh_check.isChecked()
        }
        
        # Generate 3D models
        stage = self.stages["model_generation"]
        for image_path in self.selected_images:
            success = await stage.execute(image_path, params)
            if not success:
                self.logger.error(f"Failed to generate 3D model for {image_path.name}")
    
    @asyncSlot()
    async def _on_import_selected(self):
        """Import selected 3D models to Cinema4D"""
        if not self.selected_models:
            QMessageBox.warning(self, "No Models Selected",
                              "Please select 3D models to import.")
            return
        
        stage = self.stages["scene_assembly"]
        for model_path in self.selected_models:
            success = await stage.import_model(model_path)
            if success:
                self.logger.info(f"Imported {model_path.name} to Cinema4D")
    
    @asyncSlot()
    async def _on_import_all(self):
        """Import all 3D models to Cinema4D"""
        models = self.file_monitor.get_existing_files(
            self.config.models_3d_dir,
            extensions=[".obj", ".fbx", ".gltf"]
        )
        
        if not models:
            QMessageBox.information(self, "No Models",
                                  "No 3D models found to import.")
            return
        
        stage = self.stages["scene_assembly"]
        for model_path in models:
            success = await stage.import_model(model_path)
            if success:
                self.logger.info(f"Imported {model_path.name} to Cinema4D")
    
    @asyncSlot()
    async def _on_apply_deformer(self):
        """Apply deformer to selected objects"""
        # Get selected objects from scene table
        selected_items = self.scene_objects_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection",
                              "Please select objects in the scene.")
            return
        
        deformer_type = C4DDeformerType(self.deformer_combo.currentText())
        
        # Apply deformer to each selected object
        for item in selected_items:
            if item.column() == 0:  # Name column
                obj_name = item.text()
                success = await self.c4d_client.create_deformer(obj_name, deformer_type)
                if success:
                    self.logger.info(f"Applied {deformer_type.value} to {obj_name}")
    
    @asyncSlot()
    async def _on_create_cloner(self):
        """Create MoGraph cloner"""
        # Get selected objects
        selected_items = self.scene_objects_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection",
                              "Please select objects for cloning.")
            return
        
        # Get object names
        object_names = []
        for item in selected_items:
            if item.column() == 0:  # Name column
                object_names.append(item.text())
        
        if not object_names:
            return
        
        mode = C4DClonerMode(self.cloner_mode_combo.currentText())
        count = self.cloner_count.value()
        
        success = await self.c4d_client.create_mograph_cloner(
            object_names, mode, count
        )
        
        if success:
            self.logger.info(f"Created {mode.value} cloner with {len(object_names)} objects")
            await self._on_refresh_scene()
    
    @asyncSlot()
    async def _on_refresh_scene(self):
        """Refresh scene objects list"""
        objects = await self.c4d_client.get_scene_objects()
        
        # Clear table
        self.scene_objects_table.setRowCount(0)
        
        # Add objects to table
        def add_object_to_table(obj, level=0):
            row = self.scene_objects_table.rowCount()
            self.scene_objects_table.insertRow(row)
            
            # Name with indentation
            name_item = QTableWidgetItem("  " * level + obj["name"])
            self.scene_objects_table.setItem(row, 0, name_item)
            
            # Type
            self.scene_objects_table.setItem(row, 1, QTableWidgetItem(obj["type"]))
            
            # Position
            pos = obj["position"]
            pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"
            self.scene_objects_table.setItem(row, 2, QTableWidgetItem(pos_str))
            
            # Children count
            children_count = len(obj["children"])
            self.scene_objects_table.setItem(row, 3, QTableWidgetItem(str(children_count)))
            
            # Add children
            for child in obj["children"]:
                add_object_to_table(child, level + 1)
        
        for obj in objects:
            add_object_to_table(obj)
        
        self.logger.info(f"Refreshed scene: {len(objects)} root objects")
    
    def _browse_export_path(self):
        """Browse for export path"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Export Directory",
            self.export_path.text()
        )
        if path:
            self.export_path.setText(path)
    
    @asyncSlot()
    async def _on_export_project(self):
        """Export Cinema4D project"""
        project_name = self.project_name.text()
        if not project_name:
            QMessageBox.warning(self, "Invalid Name",
                              "Please enter a project name.")
            return
        
        export_path = Path(self.export_path.text())
        if not export_path.exists():
            export_path.mkdir(parents=True, exist_ok=True)
        
        # Create project file path
        project_file = export_path / f"{project_name}.c4d"
        
        # Clear export log
        self.export_log.clear()
        self.export_log.append(f"Exporting project: {project_name}")
        self.export_log.append(f"Path: {project_file}")
        self.export_log.append("-" * 50)
        
        # Export
        stage = self.stages["export"]
        success = await stage.execute(
            project_file,
            copy_textures=self.copy_textures_check.isChecked(),
            create_backup=self.create_backup_check.isChecked(),
            generate_report=self.generate_report_check.isChecked()
        )
        
        if success:
            self.export_log.append("\n✅ Export completed successfully!")
            QMessageBox.information(self, "Export Complete",
                                  f"Project exported to:\n{project_file}")
        else:
            self.export_log.append("\n❌ Export failed!")
            QMessageBox.warning(self, "Export Failed",
                              "Failed to export project. Check console for details.")
    
    def _on_file_generated(self, path: Path, file_type: str):
        """Handle generated file"""
        self.logger.info(f"File monitoring detected new {file_type}: {path.name}")
        
        # Add to asset tracker
        self.asset_tracker.add_asset(path, file_type)
        
        # Update asset table (simplified)
        if self.asset_tree:
            row = self.asset_tree.rowCount()
            self.asset_tree.insertRow(row)
            self.asset_tree.setItem(row, 0, QTableWidgetItem(path.name))
            self.asset_tree.setItem(row, 1, QTableWidgetItem(file_type))
        
        # Update UI based on file type
        if file_type == "image":
            self.logger.info(f"Loading image into grid: {path.name}")
            self._load_image_to_grid(path)
            
            # Update status message
            self.statusBar().showMessage(f"New image loaded: {path.name}")
        elif file_type == "model":
            if hasattr(self, 'model_grid'):
                self.model_grid.add_model(path)
                self.statusBar().showMessage(f"New 3D model detected: {path.name}")
    
    def _load_image_to_grid(self, image_path: Path):
        """Load image into the next available grid slot"""
        try:
            # Ensure we have image grid components initialized
            if not hasattr(self, 'image_paths') or not self.image_paths:
                self.logger.warning("Image grid not initialized yet")
                return
            
            # Check if image is already loaded
            if image_path in self.image_paths:
                self.logger.debug(f"Image {image_path.name} already loaded")
                return
            
            # Find next available slot
            available_slot = None
            slot_index = None
            
            for i, path in enumerate(self.image_paths):
                if path is None:  # Empty slot
                    available_slot = i
                    slot_index = i
                    break
            
            if available_slot is None:
                self.logger.warning(f"No available image slots for {image_path.name} - all {len(self.image_paths)} slots full")
                return
            
            # Load image with PIL for better format support
            from PIL import Image
            img = Image.open(image_path)
            
            # Scale image to fit 460x460 (leaving room for buttons)
            img.thumbnail((460, 460), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            if img.mode == "RGBA":
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            else:
                img = img.convert("RGB")
                data = img.tobytes("raw", "RGB")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                460, 460,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Update the image label
            self.image_labels[slot_index].setPixmap(scaled_pixmap)
            self.image_labels[slot_index].setText("")  # Remove text
            self.image_labels[slot_index].setStyleSheet("""
                QLabel {
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                    background-color: white;
                }
            """)
            
            # Store the image path
            self.image_paths[slot_index] = image_path
            
            # Enable action buttons
            self.image_slots[slot_index].download_btn.setEnabled(True)
            self.image_slots[slot_index].pick_btn.setEnabled(True)
            
            self.logger.info(f"Loaded image {image_path.name} into slot {slot_index + 1}")
            
        except Exception as e:
            self.logger.error(f"Failed to load image {image_path}: {e}")
    
    def _clear_image_grid(self):
        """Clear all images from the grid"""
        for i, label in enumerate(self.image_labels):
            label.clear()
            label.setText(f"Waiting for Image {i+1}...")
            label.setStyleSheet("""
                QLabel#image_placeholder {
                    border: 2px dashed #cccccc;
                    border-radius: 8px;
                    background-color: #f8f8f8;
                    color: #666666;
                    font-size: 14px;
                }
            """)
            
            # Disable buttons
            if i < len(self.image_slots):
                self.image_slots[i].download_btn.setEnabled(False)
                self.image_slots[i].pick_btn.setEnabled(False)
                self.image_slots[i].pick_btn.setStyleSheet("")  # Reset selection style
        
        # Clear tracking arrays
        self.image_paths = [None] * len(self.image_labels)
        self.selected_images.clear()
    
    def _load_existing_images(self):
        """Load any existing images from the images directory"""
        try:
            images_dir = self.config.images_dir
            if not images_dir.exists():
                return
            
            # Get recent image files (sorted by modification time)
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                image_files.extend(images_dir.glob(ext))
            
            # Sort by modification time (newest first)
            image_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Load up to the number of available slots
            max_slots = len(self.image_labels)
            for i, image_file in enumerate(image_files[:max_slots]):
                self._load_image_to_grid(image_file)
                
            if image_files:
                self.logger.info(f"Loaded {min(len(image_files), max_slots)} existing images")
                
        except Exception as e:
            self.logger.error(f"Failed to load existing images: {e}")
    
    def _on_comfyui_progress(self, data: Dict[str, Any]):
        """Handle ComfyUI progress update"""
        value = data.get("value", 0)
        max_value = data.get("max", 1)
        progress = (value / max_value) * 100 if max_value > 0 else 0
        
        self.progress_bar.setValue(int(progress))
        self.statusBar().showMessage(f"Generating... {progress:.0f}%")
    
    def _on_comfyui_complete(self, data: Dict[str, Any]):
        """Handle ComfyUI execution complete"""
        self.progress_bar.setValue(100)
        self.statusBar().showMessage("Generation complete - Images should appear shortly")
        self.logger.info("ComfyUI execution completed - monitoring for new image files")
        
        # Optional: Trigger a manual check for new images after a short delay
        QTimer.singleShot(2000, self._check_for_new_images)  # Check after 2 seconds
    
    def _check_for_new_images(self):
        """Manually check for new images in case file monitoring missed them"""
        try:
            images_dir = self.config.images_dir
            if not images_dir.exists():
                self.logger.warning(f"Images directory does not exist: {images_dir}")
                return
            
            # Get recent image files (last 60 seconds to catch FLUX generation)
            import time
            current_time = time.time()
            recent_files = []
            all_files = []
            
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                for image_file in images_dir.glob(ext):
                    all_files.append(image_file)
                    if current_time - image_file.stat().st_mtime < 60:  # Modified in last 60 seconds
                        recent_files.append(image_file)
            
            self.logger.info(f"Manual check: Found {len(all_files)} total images, {len(recent_files)} recent")
            
            if recent_files:
                self.logger.info(f"Recent images: {[f.name for f in recent_files]}")
                loaded_count = 0
                for image_file in recent_files:
                    # Check if image is already loaded
                    if hasattr(self, 'image_paths') and image_file not in self.image_paths:
                        self.logger.info(f"Loading new image: {image_file.name}")
                        self._load_image_to_grid(image_file)
                        loaded_count += 1
                    else:
                        self.logger.debug(f"Image already loaded: {image_file.name}")
                self.logger.info(f"Loaded {loaded_count} new images into grid")
            else:
                self.logger.debug("Manual check: No recent images found")
                
        except Exception as e:
            self.logger.error(f"Error checking for new images: {e}")
    
    def _on_comfyui_error(self, data: Dict[str, Any]):
        """Handle ComfyUI execution error"""
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Generation failed")
        self.logger.error(f"ComfyUI error: {data}")
        
        QMessageBox.critical(self, "Execution Error",
                           f"ComfyUI execution failed:\n{data.get('error', 'Unknown error')}")
    
    def _refresh_theme(self):
        """Refresh the application theme (Debug function)"""
        self.logger.info("Refreshing theme...")
        self._apply_styles()
        self.update()  # Force UI update
        self.logger.info("Theme refreshed!")
    
    def _test_file_monitoring(self):
        """Test file monitoring system (Debug function - Ctrl+T)"""
        self.logger.info("Testing file monitoring system...")
        
        # Check if monitoring is active
        if hasattr(self.file_monitor, '_observers') and self.file_monitor._observers:
            self.logger.info("File monitoring is active")
        else:
            self.logger.warning("File monitoring may not be active")
        
        # Manually check for images
        self._check_for_new_images()
        
        self.statusBar().showMessage("File monitoring test completed - check console for details")
    
    def closeEvent(self, event):
        """Handle application close"""
        # Stop file monitoring
        self.file_monitor.stop()
        
        # Disconnect services
        asyncio.create_task(self.comfyui_client.disconnect())
        asyncio.create_task(self.c4d_client.disconnect())
        
        # Save configuration
        self.config.save()
        
        event.accept()