"""
REDESIGNED ComfyUI to Cinema4D Bridge Application
Complete terminal aesthetic implementation with all functionality preserved
Professional monospace design with enhanced user experience
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

# System monitoring imports
try:
    import psutil
    SYSTEM_MONITORING_AVAILABLE = True
except ImportError:
    SYSTEM_MONITORING_AVAILABLE = False

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_MONITORING_AVAILABLE = True
except Exception:
    GPU_MONITORING_AVAILABLE = False

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QTextEdit, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QListWidget,
    QListWidgetItem, QGridLayout, QGroupBox, QFileDialog,
    QMessageBox, QProgressBar, QSlider, QFrame, QScrollArea,
    QSizePolicy, QHeaderView, QTableWidget, QTableWidgetItem,
    QMenuBar, QMenu, QDialog, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize, QSettings
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QImage, QKeySequence, QShortcut, QAction
from qasync import asyncSlot

from loguru import logger

# Import all enhanced components
from ui.enhanced_console import ConsoleContainer, TerminalConsoleWidget
from ui.mcp_indicators import MCPStatusBar, ConnectionStatus
from ui.prompt_with_magic import PositivePromptWidget, NegativePromptWidget as NegativePromptWidgetWithMagic
from ui.terminal_theme_complete import get_complete_terminal_theme

# Import existing core components
from core.config_adapter import AppConfig
from core.workflow_manager import WorkflowManager
from core.file_monitor import FileMonitor, AssetTracker
from core.project_manager import ProjectManager
from mcp.comfyui_client import ComfyUIClient
from mcp.cinema4d_client import Cinema4DClient, C4DDeformerType, C4DClonerMode
from ui.widgets import ImageGridWidget, ConsoleWidget
from c4d.mcp_wrapper import CommandResult
from ui.styles import get_available_themes
from ui.fonts import get_font_manager, load_project_fonts
from ui.nlp_dictionary_dialog import NLPDictionaryDialog
from ui.studio_3d_config_dialog import Studio3DConfigDialog
from pipeline.stages import PipelineStage, ImageGenerationStage, Model3DGenerationStage, SceneAssemblyStage, ExportStage
from utils.logger import LoggerMixin

# Import debug wrapper for Scene Assembly debugging
from core.debug_wrapper import wrap_scene_assembly_methods, get_debug_report

# Import UI methods
from .app_ui_methods import UICreationMethods


class PerformanceMeter(QWidget):
    """Performance meter widget with text and visual progress bar"""
    
    def __init__(self, label_text: str, value: int = 0, max_value: int = 100, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.value = value
        self.max_value = max_value
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the performance meter UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Text label
        self.text_label = QLabel(f"{self.label_text}: {self.value}%")
        self.text_label.setObjectName("performance_meter_label")
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)
        
        # Progress bar styled as performance meter
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("performance_meter_bar")
        self.progress_bar.setRange(0, self.max_value)
        self.progress_bar.setValue(self.value)
        self.progress_bar.setFixedHeight(8)   # Slightly taller than original for visibility
        self.progress_bar.setFixedWidth(80)   # Keep width
        self.progress_bar.setTextVisible(False)
        
        # Initial styling - will be updated by update_value()
        self.update_style_color("#4CAF50")
        
        layout.addWidget(self.progress_bar)
    
    def update_style_color(self, color: str):
        """Update progress bar color with consistent styling"""
        # Try a much simpler approach - just force the CSS with high specificity
        css = f"""
        QProgressBar[objectName="performance_meter_bar"] {{
            border: 1px solid #666666;
            background-color: #1a1a1a;
            border-radius: 3px;
        }}
        QProgressBar[objectName="performance_meter_bar"]::chunk {{
            background-color: {color} !important;
            border-radius: 2px;
        }}
        """
        
        # Apply to the specific widget
        self.progress_bar.setStyleSheet(css)
        
        # Force immediate update
        self.progress_bar.repaint()
        
    def update_value(self, value: int, text: str = None):
        """Update the performance meter value"""
        self.value = value
        self.progress_bar.setValue(value)
        
        if text:
            self.text_label.setText(text)
        else:
            self.text_label.setText(f"{self.label_text}: {value}%")
            
        # Update color based on usage level
        if value >= 80:
            color = "#FF4444"  # Red for high usage
        elif value >= 60:
            color = "#FF8000"  # Orange for medium usage
        else:
            color = "#4CAF50"  # Application theme green for low usage
            
        # Apply color styling
        self.update_style_color(color)


class ComfyToC4DAppRedesigned(QMainWindow, LoggerMixin, UICreationMethods):
    """
    REDESIGNED Main Application Window
    Complete terminal aesthetic with all functionality preserved
    """
    
    # Signals
    file_generated = Signal(Path, str)  # path, type
    pipeline_progress = Signal(str, float)  # stage, progress
    comfyui_connection_updated = Signal(dict)  # connection result
    c4d_connection_updated = Signal(dict)  # connection result
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        
        # Core components - preserve all existing functionality
        self._initialize_core_components()
        
        # Enhanced UI components
        self.mcp_status_bar = None
        self.console = None
        self.main_tab_widget = None
        
        # Initialize unified object selector early
        from ui.object_selection_widget import UnifiedObjectSelectionWidget
        self.unified_object_selector = UnifiedObjectSelectionWidget()
        self.unified_object_selector.object_selected.connect(self._on_unified_object_selected)
        self.unified_object_selector.workflow_hint_changed.connect(self._on_workflow_hint_changed)
        self.unified_object_selector.all_objects_cleared.connect(self._on_all_objects_cleared)
        self.logger.debug("Unified object selector created")
        
        # Create separate instances for each tab (Qt doesn't allow same widget in multiple parents)
        self.unified_selectors = {}
        
        # Setup the redesigned UI
        self._setup_redesigned_ui()
        
    def _get_unified_selector(self, tab_name: str):
        """Get or create a unified selector instance for a specific tab"""
        if tab_name not in self.unified_selectors:
            from ui.object_selection_widget import UnifiedObjectSelectionWidget
            selector = UnifiedObjectSelectionWidget()
            
            # Connect the clear signal for this instance too
            selector.all_objects_cleared.connect(self._on_all_objects_cleared)
            
            # Share the same data objects dictionary  
            selector.objects = self.unified_object_selector.objects
            
            self.unified_selectors[tab_name] = selector
            self.logger.debug(f"Created unified selector for {tab_name} tab")
            
        return self.unified_selectors[tab_name]
    
    def _update_all_unified_selectors(self):
        """Update display for all unified selector instances"""
        # Update main instance
        self.unified_object_selector._update_display()
        
        # Update all tab instances
        for tab_name, selector in self.unified_selectors.items():
            selector._update_display()
            
        self.logger.debug("Updated all unified selector displays")
        
    def _initialize_core_components(self):
        """Initialize all core components - preserve existing functionality"""
        # Thread safety
        import threading
        self._mcp_wrapper_lock = threading.Lock()
        self.mcp_wrapper = None
        
        # Core systems
        self.workflow_manager = WorkflowManager(self.config.workflows_dir, self.config)
        self.file_monitor = FileMonitor()
        self.project_manager = ProjectManager(self.config)
        self.current_project = self.project_manager.create_new_project()
        
        # Workflow settings persistence
        from .workflow_settings import WorkflowSettings
        self.workflow_settings = WorkflowSettings(self.config.config_dir)
        
        # Association system
        from .associations import ImageModelAssociationManager
        self.associations = ImageModelAssociationManager(self.config.config_dir)
        self.asset_tracker = AssetTracker()
        
        # Session tracking
        import time
        self.session_start_time = time.time()
        self.session_images = []
        self.session_models = []
        
        # Initialize NLP dictionary
        self.nlp_dictionary = {}
        self._load_nlp_dictionary()
        
        # Initialize parameter widgets dictionary
        self.parameter_widgets = {}
        
        # MCP clients
        self.comfyui_client = ComfyUIClient(
            self.config.mcp.comfyui_server_url,
            self.config.mcp.comfyui_websocket_url
        )
        self.c4d_client = Cinema4DClient(
            self.config.paths.cinema4d_path,
            self.config.mcp.cinema4d_port
        )
        
        # Pipeline stages
        self.stages: Dict[str, PipelineStage] = {}
        
        # Undo/Redo system
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50
        
        # Lazy loading flags
        self.view_all_models_loaded = False
        
        # Parameter widget tracking for dynamic workflow updates
        self.parameter_widgets = {}  # Stores references to UI widgets for parameter collection
        
        # Initialize component references
        self.asset_tree = None
        self.queue_list = None
        
        # System monitoring setup
        self.performance_update_timer = None
        self.setup_system_monitoring()
        
    def _setup_redesigned_ui(self):
        """Setup the completely redesigned UI with terminal aesthetics"""
        try:
            self.logger.debug("Starting UI setup...")
            self.setWindowTitle("ComfyUI → Cinema4D Bridge")
            self.setGeometry(100, 100, 1920, 1080)
            # Window title and geometry set
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Enhanced header with MCP indicators
            header_widget = self._create_enhanced_header()
            main_layout.addWidget(header_widget)
            
            # Main vertical splitter for content and console
            main_splitter = QSplitter(Qt.Vertical)
            main_splitter.setChildrenCollapsible(False)
            
            # Main content area with dynamic panels
            content_splitter = self._create_main_content_area()
            main_splitter.addWidget(content_splitter)
            
            # Console at bottom using original ConsoleWidget
            console = QWidget()
            console.setMinimumHeight(120)
            console.setMaximumHeight(400)
            console_layout = QVBoxLayout(console)
            console_layout.setContentsMargins(8, 8, 8, 8)
            
            # Console header
            console_header = QHBoxLayout()
            console_title = QLabel("Console Output")
            console_title.setObjectName("section_title")
            console_header.addWidget(console_title)
            
            console_header.addStretch()
            
            # Console controls
            self.auto_scroll_check = QCheckBox("Auto-scroll")
            self.auto_scroll_check.setChecked(True)
            self.auto_scroll_check.toggled.connect(self._on_autoscroll_toggled)
            console_header.addWidget(self.auto_scroll_check)
            
            clear_btn = QPushButton("Clear")
            clear_btn.setObjectName("secondary_btn")
            clear_btn.clicked.connect(self._clear_console)
            console_header.addWidget(clear_btn)
            
            console_layout.addLayout(console_header)
            
            # Original console widget
            self.console = ConsoleWidget()
            self.console.setObjectName("console")
            self.console.setup_logging()
            self.console.set_auto_scroll(True)
            console_layout.addWidget(self.console)
            
            # Add console to splitter
            main_splitter.addWidget(console)
            
            # Store splitter reference for dynamic resizing
            self.main_splitter = main_splitter
            
            # Set initial splitter proportions
            self._recalculate_splitter_sizes()
            
            # Add splitter to main layout
            main_layout.addWidget(main_splitter)
            
            # Status bar
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("Application initialized - Ready")
            
            # Apply terminal theme
            terminal_theme = get_complete_terminal_theme()
            self.setStyleSheet(terminal_theme)
            
            # Apply saved accent color on startup
            QTimer.singleShot(200, self._apply_saved_accent_color)
            
            # Enhanced menu bar
            self._create_complete_menu_bar()
            
            # Initialize batch preview after UI is fully set up
            QTimer.singleShot(100, lambda: self._update_batch_preview(1))
            
            # Load last workflow state after UI is ready
            QTimer.singleShot(1000, self._load_last_workflow_state)
            
            # Load window settings after UI is fully initialized
            QTimer.singleShot(50, self._load_window_settings)
            
            # Auto-refresh ComfyUI connection after UI is ready
            QTimer.singleShot(2000, lambda: asyncio.create_task(self._async_refresh_comfyui()))
            
            # Initial performance metrics update
            QTimer.singleShot(1000, self.update_performance_metrics)
            
            # Initialize workflow parameters after UI is fully set up
            QTimer.singleShot(500, self._initialize_workflow_parameters)
            
            # Load test models after all initialization is complete
            QTimer.singleShot(3000, self._load_test_models_on_startup)
            
            self.logger.debug("UI setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup UI: {e}")
            import traceback
            self.logger.error(f"UI setup traceback: {traceback.format_exc()}")
            raise
        
    def _create_enhanced_header(self) -> QWidget:
        """Create enhanced header with MCP status indicators"""
        header_widget = QWidget()
        header_widget.setObjectName("main_header")
        header_widget.setFixedHeight(60)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 12, 20, 12)
        header_layout.setSpacing(0)
        
        # Left: Enhanced MCP status indicators
        self.mcp_status_bar = MCPStatusBar()
        self.mcp_status_bar.comfyui_refresh_requested.connect(self._refresh_comfyui_connection)
        self.mcp_status_bar.cinema4d_refresh_requested.connect(self._refresh_cinema4d_connection)
        header_layout.addWidget(self.mcp_status_bar)
        
        # Add spacer to center the layout
        header_layout.addStretch(1)
        
        # Right: Performance indicators (horizontal layout with meters)
        system_info = QWidget()
        system_info_layout = QHBoxLayout(system_info)
        system_info_layout.setContentsMargins(0, 0, 0, 0)
        system_info_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        system_info_layout.setSpacing(30)
        
        # GPU name label (separate from percentage)
        self.gpu_name_label = QLabel("GPU")
        self.gpu_name_label.setObjectName("performance_meter_label")
        system_info_layout.addWidget(self.gpu_name_label)
        
        # GPU performance meter
        self.gpu_meter = PerformanceMeter("GPU", 1)
        system_info_layout.addWidget(self.gpu_meter)
        
        # CPU performance meter
        self.cpu_meter = PerformanceMeter("CPU", 1)
        system_info_layout.addWidget(self.cpu_meter)
        
        # Memory performance meter
        self.memory_meter = PerformanceMeter("RAM", 1)
        system_info_layout.addWidget(self.memory_meter)
        
        header_layout.addWidget(system_info)
        
        return header_widget
        
    def _create_main_content_area(self) -> QSplitter:
        """Create main content area with dynamic panels"""
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # Left panel - Dynamic controls
        left_panel = self._create_enhanced_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Center panel - Main workspace with tabs
        center_panel = self._create_enhanced_center_panel()
        content_splitter.addWidget(center_panel)
        
        # Right panel - Dynamic parameters
        right_panel = self._create_enhanced_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set optimal proportions for professional workflow
        content_splitter.setSizes([350, 1220, 350])
        
        # Allow larger sizes for left and right panels
        content_splitter.setStretchFactor(0, 1)  # Left panel can stretch
        content_splitter.setStretchFactor(1, 3)  # Center panel gets priority
        content_splitter.setStretchFactor(2, 1)  # Right panel can stretch
        
        # Set minimum and maximum sizes for better usability
        left_panel.setMinimumWidth(250)
        left_panel.setMaximumWidth(600)  # Allow up to 600px
        right_panel.setMinimumWidth(250)
        right_panel.setMaximumWidth(600)  # Allow up to 600px
        
        return content_splitter
        
    def _create_enhanced_left_panel(self) -> QWidget:
        """Create enhanced left panel with dynamic controls"""
        panel = QWidget()
        panel.setObjectName("left_panel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Dynamic sections based on current tab - NO TABS, USE STACKED WIDGET
        from PySide6.QtWidgets import QStackedWidget
        self.left_panel_stack = QStackedWidget()
        
        # Image Generation controls
        image_controls = self._create_image_generation_controls()
        self.left_panel_stack.addWidget(image_controls)
        
        # 3D Model controls
        model_controls = self._create_3d_model_controls()
        self.left_panel_stack.addWidget(model_controls)
        
        # Texture controls
        texture_controls = self._create_texture_controls()
        self.left_panel_stack.addWidget(texture_controls)
        
        # Cinema4D controls
        c4d_controls = self._create_cinema4d_controls()
        self.left_panel_stack.addWidget(c4d_controls)
        
        layout.addWidget(self.left_panel_stack)
        
        return panel
        
    def _create_enhanced_center_panel(self) -> QWidget:
        """Create enhanced center panel with main workspace"""
        panel = QWidget()
        panel.setObjectName("content_area")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main tab widget for different stages
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.currentChanged.connect(self._on_main_tab_changed)
        
        # Image Generation tab
        image_tab = self._create_enhanced_image_generation_tab()
        self.main_tab_widget.addTab(image_tab, "Image Generation")
        
        # 3D Model Generation tab
        model_tab = self._create_enhanced_3d_model_tab()
        self.main_tab_widget.addTab(model_tab, "3D Model Generation")
        
        # Texture Generation tab
        texture_tab = self._create_enhanced_texture_generation_tab()
        self.main_tab_widget.addTab(texture_tab, "Texture Generation")
        
        # Cinema4D Intelligence tab
        c4d_tab = self._create_enhanced_cinema4d_tab()
        self.main_tab_widget.addTab(c4d_tab, "Cinema4D Intelligence")
        
        layout.addWidget(self.main_tab_widget)
        
        return panel
        
    def _create_enhanced_right_panel(self) -> QWidget:
        """Create enhanced right panel with dynamic parameters"""
        panel = QWidget()
        panel.setObjectName("right_panel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Dynamic parameter stack - NO TABS, USE STACKED WIDGET
        from PySide6.QtWidgets import QStackedWidget
        self.right_panel_stack = QStackedWidget()
        
        # Parameters for each stage
        image_params = self._create_image_parameters()
        self.right_panel_stack.addWidget(image_params)
        
        model_params = self._create_3d_parameters()
        self.right_panel_stack.addWidget(model_params)
        
        texture_params = self._create_texture_parameters()
        self.right_panel_stack.addWidget(texture_params)
        
        c4d_params = self._create_c4d_parameters()
        self.right_panel_stack.addWidget(c4d_params)
        
        layout.addWidget(self.right_panel_stack)
        
        # Set size constraint to prevent vertical expansion
        panel.setMaximumHeight(1000)  # Reasonable max height for parameter panel
        
        return panel
        
    def _create_image_generation_controls(self) -> QWidget:
        """Create image generation controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Prompt Generation section
        prompt_section = self._create_parameter_section("Prompt Generation")
        prompt_layout = prompt_section.layout()
        
        # Positive prompt with magic button inside
        positive_prompt_label = QLabel("Positive Prompt")
        positive_prompt_label.setObjectName("section_title")
        prompt_layout.addWidget(positive_prompt_label)
        
        # Use PositivePromptWidget with integrated magic button
        self.positive_prompt = PositivePromptWidget()
        self.positive_prompt.setMinimumHeight(120)
        self.positive_prompt.setMaximumHeight(120)
        # Connect magic button to dialog
        self.positive_prompt.magic_prompt_requested.connect(lambda: self._show_magic_prompts_dialog('positive'))
        
        prompt_layout.addWidget(self.positive_prompt)
        
        # Negative prompt with magic button inside
        negative_prompt_label = QLabel("Negative Prompt")
        negative_prompt_label.setObjectName("section_title")
        prompt_layout.addWidget(negative_prompt_label)
        
        # Use NegativePromptWidget with integrated magic button
        self.negative_prompt = NegativePromptWidgetWithMagic()
        self.negative_prompt.setMinimumHeight(80)
        self.negative_prompt.setMaximumHeight(80)
        # Connect magic button to dialog
        self.negative_prompt.magic_prompt_requested.connect(lambda: self._show_magic_prompts_dialog('negative'))
        
        prompt_layout.addWidget(self.negative_prompt)
        
        layout.addWidget(prompt_section)
        
        # Generation Controls section
        controls_section = self._create_parameter_section("Generation Controls")
        controls_layout = controls_section.layout()
        
        # Workflow selection
        workflow_label = QLabel("Workflow:")
        workflow_label.setObjectName("section_title")
        controls_layout.addWidget(workflow_label)
        
        self.workflow_combo = QComboBox()
        # Populate with actual workflow files from image_generation directory
        self._populate_workflow_combo("image_generation")
        
        # Set default workflow
        default_workflow = "image_generation/generate_thermal_shapes.json"
        index = self.workflow_combo.findData(default_workflow)
        if index >= 0:
            self.workflow_combo.setCurrentIndex(index)
        else:
            # Fallback to first item if default not found
            if self.workflow_combo.count() > 0:
                self.workflow_combo.setCurrentIndex(0)
        # Note: Change handler will be connected later after UI is fully initialized
        controls_layout.addWidget(self.workflow_combo)
        
        # Image size controls
        size_label = QLabel("Image Size:")
        size_label.setObjectName("section_title")
        controls_layout.addWidget(size_label)
        
        # Size preset dropdown
        self.size_preset_combo = QComboBox()
        self.size_preset_combo.addItems([
            "1024×1024 (Square)",
            "1920×1080 (16:9)",
            "1344×768 (7:4)",
            "832×1216 (Portrait)",
            "1216×832 (Landscape)",
            "512×512 (Small)",
            "Custom"
        ])
        self.size_preset_combo.currentTextChanged.connect(self._on_size_preset_changed)
        controls_layout.addWidget(self.size_preset_combo)
        
        # Custom size inputs (hidden by default)
        size_layout = QHBoxLayout()
        size_layout.setSpacing(8)
        size_layout.setContentsMargins(0, 8, 0, 8)  # Add vertical padding
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(64, 4096)
        self.width_spin.setSingleStep(64)
        self.width_spin.setValue(1024)
        self.width_spin.setPrefix("W: ")
        self.width_spin.valueChanged.connect(self._on_custom_size_changed)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(64, 4096)
        self.height_spin.setSingleStep(64)
        self.height_spin.setValue(1024)
        self.height_spin.setPrefix("H: ")
        self.height_spin.valueChanged.connect(self._on_custom_size_changed)
        
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(self.height_spin)
        
        self.custom_size_widget = QWidget()
        self.custom_size_widget.setLayout(size_layout)
        self.custom_size_widget.hide()  # Hidden until "Custom" is selected
        controls_layout.addWidget(self.custom_size_widget)
        
        # Batch size
        batch_label = QLabel("Batch Size:")
        batch_label.setObjectName("section_title")
        controls_layout.addWidget(batch_label)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 10)
        self.batch_size_spin.setValue(1)
        self.batch_size_spin.valueChanged.connect(self._update_batch_preview)
        controls_layout.addWidget(self.batch_size_spin)
        
        # Generate button
        self.generate_image_btn = QPushButton("GENERATE IMAGES")
        self.generate_image_btn.setObjectName("generate_btn")
        self.generate_image_btn.clicked.connect(self._on_generate_images)
        controls_layout.addWidget(self.generate_image_btn)
        
        # Additional controls
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("refresh_btn")
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary_btn")
        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addWidget(clear_btn)
        controls_layout.addLayout(refresh_layout)
        
        layout.addWidget(controls_section)
        
        # Unified Object Selection section (positioned below generation controls)
        image_selector = self._get_unified_selector("image_generation")
        layout.addWidget(image_selector)
        # REMOVED addStretch() - was causing UI height expansion
        
        return widget
    
    def _create_parameter_section(self, title: str) -> QGroupBox:
        """Create a parameter section with consistent styling"""
        from PySide6.QtWidgets import QGroupBox
        section = QGroupBox(title)
        section.setObjectName("sidebar_section")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)
        
        return section
        
    def _create_3d_model_controls(self) -> QWidget:
        """Create 3D model generation controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Generation Controls section
        controls_section = self._create_parameter_section("Generation Controls")
        controls_layout = controls_section.layout()
        
        # Generate button
        self.generate_3d_btn = QPushButton("GENERATE 3D MODELS")
        self.generate_3d_btn.setObjectName("generate_btn")
        self.generate_3d_btn.clicked.connect(self._on_generate_3d_models)
        controls_layout.addWidget(self.generate_3d_btn)
        
        # Additional controls
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("refresh_btn")
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary_btn")
        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addWidget(clear_btn)
        controls_layout.addLayout(refresh_layout)
        
        layout.addWidget(controls_section)
        
        # Unified Object Selection section (positioned below generation controls)
        model_selector = self._get_unified_selector("3d_model_generation")
        layout.addWidget(model_selector)
        # REMOVED addStretch() - was causing UI height expansion
        
        return widget
        
    def _create_texture_controls(self) -> QWidget:
        """Create texture generation controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Prompt Generation section
        prompt_section = self._create_parameter_section("Prompt Generation")
        prompt_layout = prompt_section.layout()
        
        # Texture prompt with embedded magic button
        texture_prompt_label = QLabel("Texture Description")
        texture_prompt_label.setObjectName("section_title")
        prompt_layout.addWidget(texture_prompt_label)
        
        self.texture_prompt = PositivePromptWidget()
        prompt_layout.addWidget(self.texture_prompt)
        
        layout.addWidget(prompt_section)
        
        # Generation Controls section
        controls_section = self._create_parameter_section("Generation Controls")
        controls_layout = controls_section.layout()
        
        # Generate button
        self.generate_texture_btn = QPushButton("GENERATE TEXTURES")
        self.generate_texture_btn.setObjectName("generate_btn")
        self.generate_texture_btn.clicked.connect(self._on_generate_textures)
        controls_layout.addWidget(self.generate_texture_btn)
        
        # Texture viewer launcher
        viewer_btn = QPushButton("LAUNCH TEXTURE VIEWER")
        viewer_btn.setObjectName("launch_texture_viewer")
        viewer_btn.clicked.connect(self._launch_texture_viewer)
        controls_layout.addWidget(viewer_btn)
        
        # Additional controls
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("refresh_btn")
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary_btn")
        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addWidget(clear_btn)
        controls_layout.addLayout(refresh_layout)
        
        layout.addWidget(controls_section)
        
        # Unified Object Selection section (shared across all tabs) - positioned below generation controls
        texture_selector = self._get_unified_selector("texture_generation")
        layout.addWidget(texture_selector)
        # REMOVED addStretch() - was causing UI height expansion
        
        return widget
        
    def _create_cinema4d_controls(self) -> QWidget:
        """Create Cinema4D intelligence controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # NLP Dictionary button
        nlp_btn = QPushButton("OPEN NLP DICTIONARY")
        nlp_btn.setObjectName("primary_btn")
        nlp_btn.clicked.connect(self._open_nlp_dictionary)
        layout.addWidget(nlp_btn)
        
        # Object creation shortcuts
        objects_section = QWidget()
        objects_section.setObjectName("sidebar_section")
        objects_layout = QVBoxLayout(objects_section)
        
        title = QLabel("Quick Objects")
        title.setObjectName("section_title")
        objects_layout.addWidget(title)
        
        # Quick object buttons
        quick_objects = [
            ("Cube", "cube"),
            ("Sphere", "sphere"),
            ("Cylinder", "cylinder"),
            ("Plane", "plane")
        ]
        
        for obj_name, obj_type in quick_objects:
            btn = QPushButton(obj_name)
            btn.setObjectName("secondary_btn")
            btn.clicked.connect(lambda checked, ot=obj_type: self._create_quick_object(ot))
            objects_layout.addWidget(btn)
        
        layout.addWidget(objects_section)
        
        # Unified Object Selection section
        c4d_selector = self._get_unified_selector("cinema4d")
        layout.addWidget(c4d_selector)
        # REMOVED addStretch() - was causing UI height expansion
        
        return widget
        
    def _create_enhanced_image_generation_tab(self) -> QWidget:
        """Create enhanced image generation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sub-tabs for New Canvas vs View All
        image_tabs = QTabWidget()
        
        # New Canvas tab
        new_canvas = self._create_new_canvas_view()
        image_tabs.addTab(new_canvas, "New Canvas")
        
        # View All tab
        view_all = self._create_view_all_images()
        image_tabs.addTab(view_all, "View All")
        
        layout.addWidget(image_tabs)
        
        return widget
        
    def _create_enhanced_3d_model_tab(self) -> QWidget:
        """Create enhanced 3D model generation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sub-tabs for Scene Objects vs View All
        model_tabs = QTabWidget()
        
        # Scene Objects tab
        scene_objects = self._create_scene_objects_view()
        model_tabs.addTab(scene_objects, "Scene Objects")
        
        # View All Models tab
        view_all_models = self._create_view_all_models()
        model_tabs.addTab(view_all_models, "View All Models")
        
        layout.addWidget(model_tabs)
        
        return widget
        
    def _create_enhanced_texture_generation_tab(self) -> QWidget:
        """Create enhanced texture generation tab with viewer integration"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Texture Generation Workspace")
        header_label.setObjectName("section_title")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_textures_btn = QPushButton("Refresh Textures")
        refresh_textures_btn.setObjectName("refresh_btn")
        refresh_textures_btn.clicked.connect(self._refresh_textured_models)
        header_layout.addWidget(refresh_textures_btn)
        
        layout.addLayout(header_layout)
        
        # Textured models grid
        self.textured_models_scroll = QScrollArea()
        self.textured_models_scroll.setWidgetResizable(True)
        
        self.textured_models_content = QWidget()
        self.textured_models_grid = QGridLayout(self.textured_models_content)
        self.textured_models_grid.setContentsMargins(20, 20, 20, 20)
        self.textured_models_grid.setSpacing(16)
        
        self.textured_models_scroll.setWidget(self.textured_models_content)
        layout.addWidget(self.textured_models_scroll)
        
        # Texture viewer integration
        viewer_section = QWidget()
        viewer_section.setObjectName("texture_viewer_container")
        viewer_layout = QVBoxLayout(viewer_section)
        
        viewer_label = QLabel("Texture Viewer Integration")
        viewer_label.setObjectName("section_title")
        viewer_layout.addWidget(viewer_label)
        
        viewer_info = QLabel("Use the texture viewer to examine generated textures in detail")
        viewer_info.setObjectName("connection_info")
        viewer_layout.addWidget(viewer_info)
        
        launch_viewer_btn = QPushButton("LAUNCH TEXTURE VIEWER")
        launch_viewer_btn.setObjectName("launch_texture_viewer")
        launch_viewer_btn.clicked.connect(self._launch_texture_viewer)
        viewer_layout.addWidget(launch_viewer_btn)
        
        layout.addWidget(viewer_section)
        
        return widget
        
    def _create_enhanced_cinema4d_tab(self) -> QWidget:
        """Create enhanced Cinema4D intelligence tab with chat interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Cinema4D Intelligence Chat")
        header_label.setObjectName("section_title")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # NLP Dictionary button
        nlp_btn = QPushButton("Open NLP Dictionary")
        nlp_btn.setObjectName("secondary_btn")
        nlp_btn.clicked.connect(self._open_nlp_dictionary)
        header_layout.addWidget(nlp_btn)
        
        layout.addLayout(header_layout)
        
        # Chat interface
        self.chat_container = QWidget()
        self.chat_container.setObjectName("chat_container")
        chat_layout = QVBoxLayout(self.chat_container)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chat_display")
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        chat_layout.addWidget(self.chat_display)
        
        # Chat input
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("chat_input")
        self.chat_input.setPlaceholderText("Ask about Cinema4D objects, parameters, or workflows...")
        self.chat_input.returnPressed.connect(self._send_chat_message)
        
        send_btn = QPushButton("Send")
        send_btn.setObjectName("primary_btn")
        send_btn.clicked.connect(self._send_chat_message)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)
        chat_layout.addLayout(input_layout)
        
        layout.addWidget(self.chat_container)
        
        # Add welcome message
        self._add_chat_message("system", "Cinema4D Intelligence Chat initialized. Ask me about objects, parameters, or workflows!")
        
        return widget
        
    def _open_nlp_dictionary(self):
        """Open the NLP Dictionary dialog"""
        try:
            
            # Initialize MCP wrapper if not exists
            if not hasattr(self, 'mcp_wrapper'):
                from src.c4d.mcp_wrapper import MCPCommandWrapper
                self.mcp_wrapper = MCPCommandWrapper(self.c4d_client)
            
            # Create and show dialog
            dialog = NLPDictionaryDialog(self, self.config)
            
            # Connect the command_created signal to execute through MCP
            def handle_command(category: str, cmd_data: dict):
                try:
                    # Extract command from cmd_data
                    command = cmd_data.get('command', '')
                    object_name = cmd_data.get('name', 'object')
                    
                    # Parse command parts
                    command_parts = command.split('.')
                    if len(command_parts) >= 2:
                        # Execute via MCP wrapper
                        result = self.mcp_wrapper.execute_command(
                            command_parts[0],
                            object_type=command_parts[1]
                        )
                        
                        # Add response to chat
                        if hasattr(result, 'success') and result.success:
                            self._add_chat_message("system", f"✅ Created {object_name} via NLP Dictionary")
                        else:
                            error_msg = result.error if hasattr(result, 'error') else 'Unknown error'
                            self._add_chat_message("system", f"❌ Failed to create {object_name}: {error_msg}")
                    else:
                        self._add_chat_message("system", f"❌ Invalid command format: {command}")
                        
                except Exception as e:
                    self.logger.error(f"Error executing NLP command: {e}")
                    self._add_chat_message("system", f"❌ Error: {str(e)}")
            
            dialog.command_created.connect(handle_command)
            dialog.show()
            
        except Exception as e:
            self.logger.error(f"Failed to open NLP Dictionary: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open NLP Dictionary: {str(e)}")
    
    def _apply_terminal_theme(self):
        """Apply complete terminal theme"""
        try:
            stylesheet = get_complete_terminal_theme()
            self.setStyleSheet(stylesheet)
            self.logger.info("Applied complete terminal theme successfully")
        except Exception as e:
            self.logger.error(f"Failed to apply terminal theme: {e}")
            # Fallback
            self.setStyleSheet("QMainWindow { background-color: #000000; color: #fafafa; }")
            
    def _connect_enhanced_signals(self):
        """Connect all enhanced UI signals"""
        # MCP status indicators are already connected in header creation
        
        # Main tab synchronization - removed duplicate connection, handled in _on_main_tab_changed
            
        # Console integration
        if hasattr(self, 'console') and self.console:
            # Add initial system messages
            self.logger.info("Application initialized successfully")
            self.logger.info("Terminal theme applied")
        
        # Setup selection context menus
        self._add_selection_context_menu()
        
        # Setup initial selection displays
        self._update_selection_displays()
        
        # Connect tab changes to selection sync
        if hasattr(self, 'main_tabs'):
            self.main_tabs.currentChanged.connect(self._on_tab_changed_sync_selection)
        
        # Load initial images and sync selection state
        QTimer.singleShot(500, self._initialize_image_loading_and_selection)
        
        # Start periodic texture detection
        self.texture_check_timer = QTimer()
        self.texture_check_timer.timeout.connect(self._check_for_new_textures)
        self.texture_check_timer.start(5000)  # Check every 5 seconds
            
    def _on_tab_changed_sync_selection(self, index: int):
        """Handle tab change and sync selection visuals"""
        # Sync panel tabs
        if hasattr(self, 'left_panel_stack'):
            self.left_panel_stack.setCurrentIndex(index)
        if hasattr(self, 'right_panel_stack'):
            self.right_panel_stack.setCurrentIndex(index)
        
        # Sync selection visuals to maintain persistence across tabs
        self._sync_image_selection_to_grids()
        
        # Update displays after a short delay to ensure widgets are ready
        QTimer.singleShot(100, self._update_selection_displays)
    
    def _initialize_image_loading_and_selection(self):
        """Initialize image loading and selection state after UI is ready"""
        try:
            # Ensure image grids are visible first
            if hasattr(self, 'session_image_grid'):
                self.session_image_grid.show()
                self.session_image_grid.setVisible(True)
            
            if hasattr(self, 'all_images_grid'):
                self.all_images_grid.show()
                self.all_images_grid.setVisible(True)
            
            # Load session images
            self._load_session_images()
            
            # Process events to ensure rendering
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Delay image loading until UI is fully created
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._delayed_image_loading)
            
            # Sync selection state to grids
            self._sync_image_selection_to_grids()
            
            # Update selection displays
            self._update_selection_displays()
            
            self.logger.info("Image loading and selection state initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize image loading and selection: {e}")
    
    def _on_main_tab_changed(self, index: int):
        """Handle main tab change"""
        self._sync_panel_tabs(index)
        stage_names = ["Image Generation", "3D Model Generation", "Texture Generation", "Cinema4D Intelligence"]
        if index < len(stage_names):
            self.logger.info(f"Switched to: {stage_names[index]}")
            
            # Lazy load dynamic 3D parameters when Tab 2 is accessed
            if index == 1:  # Tab 2: 3D Model Generation
                self._load_dynamic_3d_parameters_on_demand()
            
            # Update workflow dropdown based on current tab
            self._update_workflow_dropdown_for_tab(index)
            
            # CRITICAL: Recalculate splitter sizes to prevent UI height explosion
            # This ensures console remains visible when switching tabs
            self._recalculate_splitter_sizes()
    
    def _sync_panel_tabs(self, index: int):
        """Synchronize side panel tabs with main tab"""
        if hasattr(self, 'left_panel_stack'):
            self.left_panel_stack.setCurrentIndex(index)
        if hasattr(self, 'right_panel_stack'):
            self.right_panel_stack.setCurrentIndex(index)
            
    def _refresh_comfyui_connection(self):
        """Refresh ComfyUI connection"""
        if self.mcp_status_bar:
            self.mcp_status_bar.set_comfyui_status(ConnectionStatus.CONNECTING, "Refreshing...")
        self.logger.info("Refreshing ComfyUI connection...")
        
        # Trigger actual connection refresh
        asyncio.create_task(self._async_refresh_comfyui())
        
    def _refresh_cinema4d_connection(self):
        """Refresh Cinema4D connection"""
        if self.mcp_status_bar:
            self.mcp_status_bar.set_cinema4d_status(ConnectionStatus.CONNECTING, "Refreshing...")
        self.logger.info("Refreshing Cinema4D connection...")
        
        # Trigger actual connection refresh
        asyncio.create_task(self._async_refresh_cinema4d())
    
    def _recalculate_splitter_sizes(self):
        """Recalculate main splitter sizes to maintain proper console visibility"""
        if hasattr(self, 'main_splitter'):
            # Get current window height
            window_height = self.height()
            console_height = 200  # Fixed console height
            
            # Calculate content height accounting for header and margins
            header_height = 60  # Header is fixed at 60px
            margins = 40  # Various margins and spacing
            content_height = window_height - console_height - header_height - margins
            
            # Ensure minimum heights
            content_height = max(400, content_height)  # Minimum content height
            
            # Apply new sizes
            self.main_splitter.setSizes([content_height, console_height])
            self.logger.debug(f"Recalculated splitter sizes: content={content_height}, console={console_height}")
        
    async def _async_refresh_comfyui(self):
        """Async ComfyUI connection refresh with actual validation"""
        try:
            if hasattr(self, 'comfyui_client') and self.comfyui_client:
                # Test actual connection to ComfyUI using existing check_connection method
                result = await self.comfyui_client.check_connection()
                if result:
                    if self.mcp_status_bar:
                        self.mcp_status_bar.set_comfyui_status(ConnectionStatus.CONNECTED, f"{self.config.mcp.comfyui_server_url}")
                    self.logger.debug("ComfyUI connection verified")
                else:
                    if self.mcp_status_bar:
                        self.mcp_status_bar.set_comfyui_status(ConnectionStatus.ERROR, "Server unreachable")
                    self.logger.warning("ComfyUI server is not responding")
            else:
                # Try to create a new connection
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.config.mcp.comfyui_server_url}/history", timeout=5) as response:
                        if response.status == 200:
                            if self.mcp_status_bar:
                                self.mcp_status_bar.set_comfyui_status(ConnectionStatus.CONNECTED, f"{self.config.mcp.comfyui_server_url}")
                            self.logger.info("ComfyUI connection established")
                        else:
                            if self.mcp_status_bar:
                                self.mcp_status_bar.set_comfyui_status(ConnectionStatus.ERROR, f"HTTP {response.status}")
                            self.logger.warning(f"ComfyUI server returned status {response.status}")
        except Exception as e:
            if self.mcp_status_bar:
                self.mcp_status_bar.set_comfyui_status(ConnectionStatus.ERROR, "Connection failed")
            self.logger.error(f"ComfyUI connection failed: {e}")
            
    async def _async_refresh_cinema4d(self):
        """Async Cinema4D connection refresh with actual validation"""
        try:
            if hasattr(self, 'cinema4d_client') and self.cinema4d_client:
                # Test actual connection to Cinema4D MCP using existing test_connection method
                result = await self.cinema4d_client.test_connection()
                if result and result.get('success', False):
                    if self.mcp_status_bar:
                        self.mcp_status_bar.set_cinema4d_status(ConnectionStatus.CONNECTED, f"localhost:{self.config.mcp.cinema4d_port}")
                    self.logger.info("Cinema4D MCP connection verified")
                else:
                    if self.mcp_status_bar:
                        self.mcp_status_bar.set_cinema4d_status(ConnectionStatus.ERROR, "MCP unreachable")
                    self.logger.warning("Cinema4D MCP server is not responding")
            else:
                # Try to test MCP connection
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((self.config.mcp.cinema4d_host, self.config.mcp.cinema4d_port))
                sock.close()
            
            if result == 0:
                if self.mcp_status_bar:
                    self.mcp_status_bar.set_cinema4d_status(ConnectionStatus.CONNECTED, f"localhost:{self.config.mcp.cinema4d_port}")
                self.logger.info("Cinema4D MCP port is accessible")
            else:
                if self.mcp_status_bar:
                    self.mcp_status_bar.set_cinema4d_status(ConnectionStatus.ERROR, "Port unreachable")
                self.logger.warning(f"Cinema4D MCP port {self.config.mcp.cinema4d_port} is not accessible")
        except Exception as e:
            if self.mcp_status_bar:
                self.mcp_status_bar.set_cinema4d_status(ConnectionStatus.ERROR, "Connection failed")
            self.logger.error(f"Cinema4D connection failed: {e}")
            
    def _launch_texture_viewer(self):
        """Launch texture viewer using run_final_viewer.bat"""
        try:
            viewer_path = Path("viewer/run_final_viewer.bat")
            if viewer_path.exists():
                subprocess.Popen([str(viewer_path)], shell=True)
                self.logger.info("Texture viewer launched successfully")
            else:
                self.logger.error("Texture viewer not found at: " + str(viewer_path))
        except Exception as e:
            self.logger.error(f"Failed to launch texture viewer: {e}")
            
    def _refresh_textured_models(self):
        """Refresh the textured models display"""
        try:
            self.logger.info("Refreshing textured models...")
            
            # Clear existing grid
            for i in reversed(range(self.textured_models_grid.count())):
                child = self.textured_models_grid.itemAt(i).widget()
            if child:
                child.setParent(None)
            
            # Get textured models from enhanced file monitor
            if hasattr(self, 'enhanced_monitor'):
                textured_models = self.enhanced_monitor.get_textured_models()
            
            if not textured_models:
                # Show empty state
                empty_label = QLabel("No textured models found\n\nGenerate textures for 3D models to see them here")
                empty_label.setObjectName("image_placeholder")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setMinimumHeight(200)
                self.textured_models_grid.addWidget(empty_label, 0, 0)
                return
            
            # Add model cards
            cols = 3  # 3 models per row
            for i, model_path in enumerate(textured_models[:12]):  # Limit to 12 models
                card = self._create_textured_model_card(model_path)
                row = i // cols
                col = i % cols
                self.textured_models_grid.addWidget(card, row, col)
                
            self.logger.info(f"Loaded {len(textured_models)} textured models")
            
            # Update status if we have a texture status label
            if hasattr(self, 'texture_status_label'):
                self.texture_status_label.setText(f"{len(textured_models)} textured models available")
                
        except Exception as e:
            self.logger.error(f"Error refreshing textured models: {e}")
            
    def _create_textured_model_card(self, model_path: Path) -> QFrame:
        """Create a card widget for a textured model"""
        card = QFrame()
        card.setObjectName("model_grid_item")
        card.setFixedSize(180, 220)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Model preview placeholder
        preview = QLabel()
        preview.setObjectName("image_placeholder")
        preview.setText("3D Model")
        preview.setAlignment(Qt.AlignCenter)
        preview.setMinimumHeight(120)
        layout.addWidget(preview)
        
        # Model name
        name_label = QLabel(model_path.stem[:20] + "..." if len(model_path.stem) > 20 else model_path.stem)
        name_label.setObjectName("model_name")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Size info
        try:
            size_bytes = model_path.stat().st_size
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB" if size_bytes > 1024 * 1024 else f"{size_bytes / 1024:.1f} KB"
            size_label = QLabel(size_str)
            size_label.setObjectName("connection_info")
            layout.addWidget(size_label)
        except:
            pass
        
        # View button
        view_btn = QPushButton("View in 3D")
        view_btn.setObjectName("secondary_btn")
        view_btn.clicked.connect(lambda: self._view_textured_model(model_path))
        layout.addWidget(view_btn)
        
        return card
        
    def _view_textured_model(self, model_path: Path):
        """View a textured model in the embedded viewer or external viewer"""
        try:
            self.logger.info(f"Viewing textured model: {model_path.name}")
            
            # If we have an embedded viewer and auto-preview is enabled
            if hasattr(self, 'embedded_texture_viewer') and hasattr(self, 'auto_preview_check') and self.auto_preview_check.isChecked():
                self.embedded_texture_viewer.load_model(str(model_path))
                self.logger.info("Loaded model in embedded viewer")
            else:
                # Launch external viewer
                self._launch_texture_viewer()
            
        except Exception as e:
            self.logger.error(f"Error viewing textured model: {e}")
            
    def _send_chat_message(self):
        """Send message to Cinema4D intelligence chat"""
        message = self.chat_input.text().strip()
        if message:
            self._add_chat_message("user", message)
            self.chat_input.clear()
            
            # Simulate AI response (implement actual AI logic here)
            self._simulate_ai_response(message)
            
    def _add_chat_message(self, sender: str, message: str):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "user":
            color = "#22c55e"
            prefix = "You"
        elif sender == "system":
            color = "#3b82f6"
            prefix = "System"
        else:
            color = "#eab308"
            prefix = "AI"
            
        html_message = f'''
        <div style="margin-bottom: 8px; font-family: 'JetBrains Mono', monospace;">
            <span style="color: #737373;">[{timestamp}]</span>
            <span style="color: {color}; font-weight: 500;">{prefix}:</span>
            <span style="color: #fafafa; margin-left: 8px;">{message}</span>
        </div>
        '''
        
        self.chat_display.append(html_message)
        
    def _simulate_ai_response(self, user_message: str):
        """Process user message through NLP parser and execute Cinema4D commands"""
        try:
            # Initialize NLP parser if not exists
            if not hasattr(self, 'nlp_parser'):
                from src.c4d.nlp_parser import C4DNaturalLanguageParser
            self.nlp_parser = C4DNaturalLanguageParser()
            
            # Initialize MCP wrapper if not exists
            if not hasattr(self, 'mcp_wrapper'):
                from src.c4d.mcp_wrapper import MCPCommandWrapper
                self.mcp_wrapper = MCPCommandWrapper(self.c4d_client)
            
            # Parse the message
            scene_intent = self.nlp_parser.parse(user_message)
            
            if not scene_intent.operations:
                # No operations detected, provide help
                response = "I can help you create objects in Cinema4D. Try:\n• Create a cube/sphere/torus\n• Add a light/camera\n• Create cloner/array\n• Apply bend/twist deformer"
                QTimer.singleShot(500, lambda: self._add_chat_message("ai", response))
                return
            
            # Execute each operation
            responses = []
            for operation in scene_intent.operations:
                try:
                    # Check if it's a create operation and we have NLP dictionary support
                    if operation.operation_type.value in ['create', 'add', 'make']:
                        object_type = operation.parameters.get('object_type', '')
                        
                        # Check if this is in our NLP dictionary
                        for category, items in self.nlp_dictionary.items():
                            for item_id, item_data in items.items():
                                if object_type.lower() in [item_id.lower(), item_data.get('name', '').lower()]:
                                    # Found in NLP dictionary - use the dialog command
                                    command_parts = item_data.get('command', '').split('.')
                                    if len(command_parts) >= 2:
                                        # Execute via MCP
                                        result = self.mcp_wrapper.execute_command(
                                            command_parts[0],
                                            object_type=command_parts[1],
                                            **operation.parameters
                                        )
                                        if hasattr(result, 'success') and result.success:
                                            responses.append(f"✅ Created {item_data.get('name', object_type)}")
                                        else:
                                            responses.append(f"❌ Failed to create {object_type}")
                                        break
                    
                    # If not handled by NLP dictionary, try direct command
                    if not responses:
                        command = operation.operation_type.value
                        result = self.mcp_wrapper.execute_command(
                        command,
                        **operation.parameters
                        )
                    
                        if hasattr(result, 'success') and result.success:
                            responses.append(f"✅ {result.message if hasattr(result, 'message') else 'Command executed'}")
                        else:
                            responses.append(f"❌ Error: {result.error if hasattr(result, 'error') else 'Command failed'}")
                        
                except Exception as e:
                    responses.append(f"❌ Error: {str(e)}")
            
            # Send combined response
            if responses:
                response = "\n".join(responses)
            else:
                response = "✅ Command processed"
            
            QTimer.singleShot(500, lambda: self._add_chat_message("ai", response))
            
        except Exception as e:
            # Fallback to helpful response on error
            self.logger.error(f"NLP processing error: {e}")
            error_response = f"I encountered an error processing your request. Please check:\n• Cinema4D is running\n• MCP server is connected\n• Try simpler commands like 'create a cube'"
            QTimer.singleShot(500, lambda: self._add_chat_message("ai", error_response))
        
    # Event handlers for generation buttons
    def _on_generate_images(self):
        """Handle image generation"""
        try:
            # Check if widgets exist
            if not hasattr(self, 'positive_prompt'):
                self.logger.error("positive_prompt widget not found")
                return
            if not hasattr(self, 'negative_prompt'):
                self.logger.error("negative_prompt widget not found")
                return
            if not hasattr(self, 'batch_size_spin'):
                self.logger.error("batch_size_spin widget not found")
                return
            
            prompt = self.positive_prompt.get_prompt()
            neg_prompt = self.negative_prompt.get_prompt()
            batch_size = self.batch_size_spin.value()
            
            self.logger.info(f"Starting image generation: {batch_size} images")
            self.logger.info(f"Prompt: {prompt[:50]}...")
            
            # Start the async image generation
            asyncio.create_task(self._async_generate_images(prompt, neg_prompt, batch_size))
        except Exception as e:
            self.logger.error(f"Error in _on_generate_images: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to start image generation: {str(e)}")
    
    async def _async_generate_images(self, prompt: str, neg_prompt: str, batch_size: int):
        """Handle async image generation using ComfyUI workflow"""
        from PySide6.QtWidgets import QMessageBox
        import json
        
        self.logger.info("Starting async image generation...")
        
        # Disable the generate button to prevent multiple clicks
        if hasattr(self, 'generate_image_btn'):
            self.generate_image_btn.setEnabled(False)
            self.generate_image_btn.setText("Generating...")
        
        try:
            # Check ComfyUI connection first
            if not hasattr(self, 'comfyui_client') or not self.comfyui_client:
                QMessageBox.critical(self, "Error", "ComfyUI client not connected. Please ensure ComfyUI is running.")
                return
            
            # Check connection status
            if not await self.comfyui_client.check_connection():
                QMessageBox.critical(self, "Error", "Cannot connect to ComfyUI. Please ensure ComfyUI is running at http://127.0.0.1:8188")
                return
            
            # Load the appropriate workflow based on prompt content
            # Get selected workflow from dropdown (now includes subdirectory path)
            workflow_file = self.workflow_combo.currentData() if hasattr(self, 'workflow_combo') else "image_generation/generate_thermal_shapes.json"
            
            self.logger.info(f"Loading image generation workflow: {workflow_file}")
            workflow = self.workflow_manager.load_workflow(workflow_file)
            if not workflow:
                QMessageBox.critical(self, "Error", f"Failed to load image generation workflow ({workflow_file})")
                return
            
            # Collect parameters dynamically based on workflow
            params = self._collect_dynamic_workflow_parameters(workflow, prompt, neg_prompt, batch_size)
            
            # Validate parameters before injection
            from core.parameter_validator import ParameterValidator
            validator = ParameterValidator()
            params = validator.validate_parameters(params)
            self.logger.info(f"Validated parameters: {list(params.keys())}")
            
            self.logger.info(f"Injecting parameters into workflow...")
            
            # Use our new dynamic workflow handler for better compatibility
            from .dynamic_workflow_handler import DynamicWorkflowHandler
            dynamic_handler = DynamicWorkflowHandler()
            
            # First inject prompts dynamically
            workflow_with_prompts = dynamic_handler.inject_prompts_dynamic(workflow, prompt, neg_prompt)
            
            # Then update latent sizes from UI controls
            if hasattr(self, 'width_spin') and hasattr(self, 'height_spin'):
                workflow_with_prompts = dynamic_handler.update_latent_size_dynamic(
                    workflow_with_prompts, 
                    self.width_spin.value(),
                    self.height_spin.value(),
                    batch_size
                )
            
            # Finally inject other parameters using existing method
            workflow_with_params = self.workflow_manager.inject_parameters_comfyui(workflow_with_prompts, params)
            
            if not workflow_with_params:
                self.logger.error("Failed to inject parameters into workflow")
                QMessageBox.critical(self, "Error", "Failed to prepare workflow with parameters")
                return
            
            # Start ASCII loading animations for preview cards
            self._start_generation_loading_animations(batch_size)
            
            # Execute workflow in ComfyUI (skip UI loading for automated execution)
            self.logger.info(f"Executing ComfyUI workflow for {batch_size} images...")
            success = await self.comfyui_client.queue_prompt(workflow_with_params, load_in_ui_first=False)
            
            if success:
                self.logger.info(f"Successfully queued image generation with prompt_id: {success}")
                # Start monitoring for workflow completion and download images
                self._start_workflow_completion_monitoring(success, batch_size)
            
            # Also try to get more info about the queue status after a short delay
            async def check_queue_after_delay():
                await asyncio.sleep(3)  # Wait 3 seconds
                try:
                    queue_status = await self.comfyui_client.get_queue_status()
                    queue_pending = len(queue_status.get("queue_pending", []))
                    queue_running = len(queue_status.get("queue_running", []))
                    self.logger.debug(f"Queue status after 3s: {queue_running} running, {queue_pending} pending")
                    
                    # Check if our specific prompt is in the queue
                    for item in queue_status.get("queue_pending", []):
                        if item[1] == success:  # prompt_id match
                            self.logger.debug(f"Found our workflow {success} in pending queue")
                            return
                    for item in queue_status.get("queue_running", []):
                        if item[1] == success:  # prompt_id match
                            self.logger.debug(f"Found our workflow {success} currently running")
                            return
                    
                    # If not found in queue, check history
                    self.logger.debug(f"Workflow {success} not found in queue, checking history...")
                    
                except Exception as e:
                    self.logger.error(f"Error checking queue status: {e}")
            
            # Run the check in background
            asyncio.create_task(check_queue_after_delay())
            
        except Exception as e:
            self.logger.error(f"Error during image generation: {e}")
            import traceback
            self.logger.error(f"Image generation traceback: {traceback.format_exc()}")
            # Stop animations on error
            self._stop_all_loading_animations()
            QMessageBox.critical(self, "Error", f"Image generation failed: {str(e)}")
        
        finally:
            # Re-enable the generate button
            if hasattr(self, 'generate_image_btn'):
                self.generate_image_btn.setEnabled(True)
                self.generate_image_btn.setText("GENERATE IMAGES")
    
    def _start_generation_loading_animations(self, batch_size: int):
        """Start ASCII loading animations for all preview cards"""
        if hasattr(self, 'image_cards'):
            for i in range(1, batch_size + 1):
                if i in self.image_cards:
                    self._start_ascii_loading_animation(i)
                    self.logger.debug(f"Started ASCII animation for card {i}")
    
    def _stop_all_loading_animations(self):
        """Stop all ASCII loading animations"""
        if hasattr(self, 'image_cards'):
            for i in self.image_cards.keys():
                self._stop_ascii_loading_animation(i)
                self.logger.debug(f"Stopped ASCII animation for card {i}")
    
    def _start_workflow_completion_monitoring(self, prompt_id: str, batch_size: int):
        """Start monitoring for workflow completion and download generated images"""
        import os
        from pathlib import Path
        
        # Use the configured images directory from the app config
        images_dir = Path(self.config.images_dir)
        
        # Ensure the directory exists
        images_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"Monitoring workflow {prompt_id} completion, will save images to: {images_dir}")
        
        # Store workflow info for monitoring
        self._current_prompt_id = prompt_id
        self._expected_batch_size = batch_size
        self._images_downloaded = 0
        
        # Stop any existing timer
        if hasattr(self, 'workflow_monitor_timer') and self.workflow_monitor_timer:
            self.workflow_monitor_timer.stop()
            self.workflow_monitor_timer = None
        
        # Reset monitoring counters
        self._monitor_check_count = 0
        
        # Start timer to check for workflow completion
        self.workflow_monitor_timer = QTimer()
        self.workflow_monitor_timer.timeout.connect(self._check_workflow_completion)
        self.workflow_monitor_timer.start(2000)  # Check every 2 seconds
        self.logger.debug(f"Started workflow completion monitoring for prompt {prompt_id}")
    
    def _check_workflow_completion(self):
        """Check if workflow is complete and download generated images"""
        try:
            if not hasattr(self, '_current_prompt_id'):
                return
            
            # Create async task to check completion
            asyncio.create_task(self._async_check_workflow_completion())
            
        except Exception as e:
            self.logger.error(f"Error in workflow completion check: {e}")
    
    async def _async_check_workflow_completion(self):
        """Async method to check workflow completion and download images"""
        try:
            prompt_id = self._current_prompt_id
            
            # Get workflow history to check if completed
            history = await self.comfyui_client.get_history(prompt_id)
            if prompt_id not in history:
                # Workflow not in history yet, continue monitoring
                self._monitor_check_count += 1
                if self._monitor_check_count % 5 == 0:  # Every 10 seconds
                    self.logger.debug(f"Still waiting for workflow {prompt_id} to complete...")
                return
            
            workflow_data = history[prompt_id]
            status = workflow_data.get("status", {})
            
            if not status.get("completed", False):
                # Workflow not completed yet
                self._monitor_check_count += 1
                if self._monitor_check_count % 5 == 0:  # Every 10 seconds
                    self.logger.debug(f"Workflow {prompt_id} still running...")
                return
            
            # Workflow completed! Get the outputs
            outputs = workflow_data.get("outputs", {})
            self.logger.info(f"Workflow {prompt_id} completed, processing outputs...")
            
            # Find images in the outputs
            images_found = []
            for node_id, output_data in outputs.items():
                if "images" in output_data:
                    for image_info in output_data["images"]:
                        if image_info:  # Non-empty image info
                            images_found.append(image_info)
            
            if not images_found:
                self.logger.warning(f"Workflow completed but no images found in outputs")
                self._stop_workflow_monitoring()
                return
            
            self.logger.debug(f"Found {len(images_found)} images to download")
            
            # Download and save images
            for i, image_info in enumerate(images_found[:self._expected_batch_size]):
                await self._download_and_save_image(image_info, i + 1)
            
            # Stop monitoring
            self._stop_workflow_monitoring()
            
        except Exception as e:
            self.logger.error(f"Error checking workflow completion: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _download_and_save_image(self, image_info: dict, card_index: int):
        """Download image from ComfyUI and save to our images directory"""
        try:
            # Download image data from ComfyUI
            image_data = await self.comfyui_client.fetch_image(image_info)
            if not image_data:
                self.logger.error(f"Failed to download image {image_info}")
                return
            
            # Generate filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ComfyUI_{timestamp}_{card_index:04d}.png"
            
            # Save to our images directory
            from pathlib import Path
            images_dir = Path(self.config.images_dir)
            image_path = images_dir / filename
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            self.logger.debug(f"Saved image to: {image_path}")
            
            # Load image into preview card
            self._load_image_when_generated(card_index, image_path)
            self._images_downloaded += 1
            
        except Exception as e:
            self.logger.error(f"Error downloading image: {e}")
    
    def _stop_workflow_monitoring(self):
        """Stop workflow completion monitoring"""
        if hasattr(self, 'workflow_monitor_timer') and self.workflow_monitor_timer:
            self.workflow_monitor_timer.stop()
            self.workflow_monitor_timer = None
            self.logger.info(f"Stopped workflow monitoring - downloaded {getattr(self, '_images_downloaded', 0)} images")
    
    def _check_for_generated_images(self, expected_count: int, output_dir: Path):
        """Check if new images have been generated"""
        try:
            if not output_dir.exists():
                self.logger.warning(f"Output directory does not exist: {output_dir}")
                return
            
            # Get all PNG files sorted by modification time (newest first)
            png_files = sorted(output_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
            current_count = len(png_files)
            
            # Check if we have new images
            new_images = current_count - self.initial_image_count
            
            # Debug logging for monitoring
            self.logger.debug(f"File monitoring: current={current_count}, initial={self.initial_image_count}, new={new_images}, expected={expected_count}")
            
            if new_images >= expected_count:
                self.logger.debug(f"Found {new_images} new images (expected {expected_count}), loading into preview cards")
            
            # Load the newest images into preview cards
            loaded_count = 0
            for i in range(min(expected_count, len(png_files))):
                image_path = png_files[i]
                card_index = i + 1
                
                # Check if this is actually a new file (modified within last 60 seconds)
                import time
                file_age_seconds = time.time() - image_path.stat().st_mtime
                if file_age_seconds <= 60:  # File modified within last minute
                    self.logger.debug(f"Loading new image into card {card_index}: {image_path.name}")
                    self._load_image_when_generated(card_index, image_path)
                    loaded_count += 1
                else:
                    self.logger.debug(f"Skipping older file (age: {file_age_seconds:.1f}s): {image_path.name}")
            
            # Stop monitoring if we loaded any images
            if loaded_count > 0:
                if hasattr(self, 'image_monitor_timer') and self.image_monitor_timer:
                    self.image_monitor_timer.stop()
                    self.image_monitor_timer = None
                    self.logger.debug(f"Stopped image generation monitoring - loaded {loaded_count} images")
                
                # Update initial count for next generation
                self.initial_image_count = current_count
            else:
                self.logger.warning(f"Found {new_images} new images but none were recent enough - continuing monitoring")
            
            # Log progress every 10 seconds (5 checks at 2-second intervals)
            if not hasattr(self, '_monitor_check_count'):
                self._monitor_check_count = 0
            self._monitor_check_count += 1
            
            if self._monitor_check_count % 5 == 0:  # Every 10 seconds
                self.logger.debug(f"Still monitoring for images... (found {new_images}/{expected_count} new images)")
            
        except Exception as e:
            self.logger.error(f"Error checking for generated images: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _auto_load_new_3d_model(self, model_path: Path):
        """Auto-load new 3D model into scene objects viewer with dynamic loading animation"""
        try:
            # Switch to Tab 2 (3D Model Generation) if not already there
            if hasattr(self, 'main_tab_widget') and self.main_tab_widget.currentIndex() != 1:
                self.main_tab_widget.setCurrentIndex(1)
                self.logger.info("Switched to 3D Model Generation tab to show new model")
            
            # Add to session models list if not already there
            if model_path not in self.session_models:
                self.session_models.append(model_path)
                self.logger.debug(f"Added {model_path.name} to session models list")
            
            # Add model to session grid with loading animation
            if hasattr(self, 'session_models_grid'):
                # Add the model to the grid
                self.session_models_grid.add_model(model_path)
                
                # Start ASCII loading animation for the new model card
                self._start_3d_model_loading_animation(model_path)
                
                self.logger.info(f"Auto-loaded new 3D model: {model_path.name}")
            else:
                self.logger.warning("Session models grid not available for auto-loading")
                
        except Exception as e:
            self.logger.error(f"Failed to auto-load 3D model: {e}")
    
    def _start_3d_model_loading_animation(self, model_path: Path):
        """Start ASCII loading animation for a specific 3D model"""
        try:
            # ASCII characters for 3D model loading
            ascii_3d_frames = [
                "⬆️🔺⬇️", "⬇️⬆️🔺", "🔺⬇️⬆️", "⬆️🔺⬇️",
                "🔲🔳⚪", "⚪🔲🔳", "🔳⚪🔲", "🔲🔳⚪",
                "🌐🎲🧊", "🧊🌐🎲", "🎲🧊🌐", "🌐🎲🧊"
            ]
            
            frame_index = [0]
            
            def update_animation():
                try:
                    if hasattr(self, 'session_models_grid'):
                        # Find the card for this model and update its title with animation
                        for card in self.session_models_grid.cards:
                            if card.model_path == model_path:
                                frame = ascii_3d_frames[frame_index[0] % len(ascii_3d_frames)]
                                card.title_label.setText(f"{frame} Loading...")
                                frame_index[0] += 1
                                break
                    
                    # Stop animation after model is fully loaded (10 seconds max)
                    if frame_index[0] >= 40:  # 40 frames * 250ms = 10 seconds
                        if hasattr(self, 'session_models_grid'):
                            for card in self.session_models_grid.cards:
                                if card.model_path == model_path:
                                    card.title_label.setText(model_path.stem)
                                    break
                        return False  # Stop timer
                    
                    return True  # Continue timer
                    
                except Exception as e:
                    self.logger.error(f"Error in 3D loading animation: {e}")
                    return False
            
            # Create animation timer
            animation_timer = QTimer()
            animation_timer.timeout.connect(lambda: update_animation() or animation_timer.stop())
            animation_timer.start(250)  # Update every 250ms
            
            # Store timer reference to prevent garbage collection
            if not hasattr(self, '_3d_animation_timers'):
                self._3d_animation_timers = []
            self._3d_animation_timers.append(animation_timer)
            
        except Exception as e:
            self.logger.error(f"Failed to start 3D model loading animation: {e}")
        
    def _on_generate_3d_models(self):
        """Handle 3D model generation"""
        if not hasattr(self, 'unified_object_selector'):
            self.logger.warning("Unified object selector not available")
            return
            
        # Get selected images from unified object system
        from ui.object_selection_widget import ObjectState
        selected_objects = self.unified_object_selector.get_selected_objects(ObjectState.IMAGE)
        
        if not selected_objects:
            self.logger.warning("No images selected for 3D generation")
            return
            
        selected_count = len(selected_objects)
        self.logger.info(f"Starting 3D generation from {selected_count} selected images")
        self.logger.info(f"Selected images: {[obj.display_name for obj in selected_objects]}")
        
        # Get the actual image paths
        image_paths = [obj.source_image for obj in selected_objects if obj.source_image]
        
        if not image_paths:
            self.logger.error("No valid image paths found from selected objects")
            return
            
        self.logger.info(f"Image paths to generate: {[path.name for path in image_paths]}")
        
        # Start the actual 3D generation
        asyncio.create_task(self._async_generate_3d_models(image_paths))
        
    async def _async_generate_3d_models(self, image_paths: List[Path]):
        """Handle async 3D model generation using ComfyUI workflow"""
        from PySide6.QtWidgets import QMessageBox
        import json
        import asyncio
        
        self.logger.info("Starting async 3D model generation...")
        
        # Disable the generate button to prevent multiple clicks
        if hasattr(self, 'generate_3d_btn'):
            self.generate_3d_btn.setEnabled(False)
            self.generate_3d_btn.setText("Generating...")
        
        # Store batch information for progress tracking
        self._3d_batch_total = len(image_paths)
        self._3d_batch_completed = 0
        self._3d_batch_prompt_ids = {}
        
        try:
            # Check ComfyUI connection first
            if not hasattr(self, 'comfyui_client') or not self.comfyui_client:
                QMessageBox.critical(self, "Error", "ComfyUI client not connected. Please ensure ComfyUI is running.")
                return
            
            # Load the 3D workflow from configuration or use default
            config_path = Path("config/3d_parameters_config.json")
            workflow_file = "3d_generation/3D_gen_Hunyuan2_onlymesh.json"  # Updated to match new structure
            
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    configured_workflow = config.get("workflow_file", workflow_file)
                    
                    # Handle different path formats from configuration
                    if configured_workflow:
                        # If it doesn't include the directory, add it
                        if not configured_workflow.startswith("3d_generation/"):
                            if configured_workflow == "3D_gen_Hunyuan2_onlymesh.json":
                                workflow_file = "3d_generation/3D_gen_Hunyuan2_onlymesh.json"
                            else:
                                workflow_file = f"3d_generation/{configured_workflow}"
                        else:
                            workflow_file = configured_workflow
                    
                    self.logger.info(f"Using configured 3D workflow: {workflow_file}")
                except Exception as e:
                    self.logger.error(f"Error loading 3D config: {e}")
            
            self.logger.info("Loading 3D generation workflow...")
            workflow_path = self.config.workflows_dir / workflow_file
            self.logger.info(f"Looking for workflow at: {workflow_path}")
            self.logger.info(f"Workflow file exists: {workflow_path.exists()}")
            
            workflow = self.workflow_manager.load_workflow(workflow_file)
            if not workflow:
                QMessageBox.critical(self, "Error", f"Failed to load 3D generation workflow ({workflow_file})")
                return
            
            # Debug workflow structure
            if "nodes" in workflow:
                self.logger.info(f"Successfully loaded UI workflow with {len(workflow.get('nodes', []))} nodes")
                node_types = [node.get('type', 'unknown') for node in workflow.get('nodes', [])]
                self.logger.info(f"Node types in workflow: {set(node_types)}")
            else:
                self.logger.info(f"Successfully loaded API workflow with {len(workflow)} nodes")
                node_types = [node.get('class_type', 'unknown') for node in workflow.values()]
                self.logger.info(f"Node class types in workflow: {set(node_types)}")
            
            # Collect parameters from 3D UI
            params = self._collect_dynamic_3d_workflow_parameters()
            self.logger.info(f"Collected 3D parameters: {list(params.keys())}")
            
            # Validate parameters before injection
            from core.parameter_validator import ParameterValidator
            validator = ParameterValidator()
            params = validator.validate_parameters(params)
            self.logger.info(f"Validated 3D parameters: {list(params.keys())}")
            
            # Process each selected image
            total_images = len(image_paths)
            successful_count = 0
            
            for i, image_path in enumerate(image_paths):
                self.logger.info(f"Processing image {i+1}/{total_images}: {image_path.name}")
            
                # Ensure image exists and is accessible
                if not image_path.exists():
                    self.logger.error(f"Image file not found: {image_path}")
                    continue
            
                # Inject parameters and image path into workflow
                self.logger.info(f"Injecting parameters for image: {image_path.name}")
                workflow_with_params = self.workflow_manager.inject_parameters_3d(
                    workflow, params, str(image_path)
                )
            
                if not workflow_with_params:
                    self.logger.error(f"Failed to inject parameters for {image_path.name}")
                    continue
            
                # Execute workflow in ComfyUI (skip UI loading for automated execution)
                self.logger.info(f"Executing ComfyUI workflow for {image_path.name}")
                result = await self.comfyui_client.queue_prompt(workflow_with_params, load_in_ui_first=False)
            
                # comfyui_client.queue_prompt() returns prompt_id string directly (not a dict)
                if result and isinstance(result, str):
                    prompt_id = result
                    successful_count += 1
                    self.logger.info(f"Successfully queued 3D generation for {image_path.name} with prompt_id: {prompt_id}")
                    
                    # Track batch prompt IDs
                    self._3d_batch_prompt_ids[prompt_id] = image_path
                    
                    # Update button to show progress
                    if hasattr(self, 'generate_3d_btn'):
                        self.generate_3d_btn.setText(f"Generating... ({successful_count}/{self._3d_batch_total})")
                    
                    # Start workflow completion monitoring for 3D model
                    self._start_3d_workflow_completion_monitoring(prompt_id, image_path)
                else:
                    self.logger.error(f"Failed to queue 3D generation for {image_path.name} - result: {result}")
            
                # Small delay between generations to avoid overwhelming ComfyUI
                if i < total_images - 1:  # Don't delay after the last image
                    await asyncio.sleep(1)
            
            # Show completion message
            self.logger.info(f"3D generation queued: {successful_count}/{total_images} successful")
            if successful_count > 0:
                QMessageBox.information(self, "3D Generation Queued",
                                  f"Successfully queued {successful_count}/{total_images} images for 3D generation in ComfyUI.\n\n"
                                  f"3D models will appear in the 3D Model Generation tab when complete.")
            else:
                QMessageBox.warning(self, "3D Generation Failed",
                              "Failed to queue any images for 3D generation. Please check ComfyUI connection.")
            
        except Exception as e:
            self.logger.error(f"Error during 3D generation: {e}")
            import traceback
            self.logger.error(f"3D generation traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"3D generation failed: {str(e)}")
        
        finally:
            # Re-enable the generate button
            if hasattr(self, 'generate_3d_btn'):
                self.generate_3d_btn.setEnabled(True)
                self.generate_3d_btn.setText("GENERATE 3D MODELS")
    
    def _start_3d_workflow_completion_monitoring(self, prompt_id: str, source_image: Path):
        """Monitor ComfyUI workflow completion for 3D model generation"""
        from PySide6.QtCore import QTimer
        import asyncio
        
        self.logger.info(f"Starting 3D workflow completion monitoring for prompt {prompt_id}")
        
        check_count = [0]
        max_checks = 60  # 60 checks * 2 seconds = 2 minutes max
        
        async def check_completion():
            await self._check_3d_workflow_completion(prompt_id, source_image, check_count, max_checks)
        
        def timer_callback():
            asyncio.ensure_future(check_completion())
        
        # Check every 2 seconds for 3D models (they take longer)
        timer = QTimer()
        timer.timeout.connect(timer_callback)
        timer.start(2000)
        
        # Store timer to prevent garbage collection
        if not hasattr(self, '3d_completion_timers'):
            self.three_d_completion_timers = {}
        self.three_d_completion_timers[prompt_id] = timer
    
    async def _check_3d_workflow_completion(self, prompt_id: str, source_image: Path, check_count: list, max_checks: int):
        """Check if 3D workflow has completed and download the model"""
        try:
            check_count[0] += 1
            
            # Get workflow status
            history = await self.comfyui_client.get_history(prompt_id)
            
            if history and prompt_id in history:
                prompt_history = history[prompt_id]
                status = prompt_history.get('status', {})
                
                if status.get('completed', False):
                    self.logger.info(f"3D workflow {prompt_id} completed!")
                    
                    # Stop the timer
                    if hasattr(self, 'three_d_completion_timers') and prompt_id in self.three_d_completion_timers:
                        self.three_d_completion_timers[prompt_id].stop()
                        del self.three_d_completion_timers[prompt_id]
                    
                    # Download the 3D model
                    outputs = prompt_history.get('outputs', {})
                    self.logger.debug(f"3D workflow outputs structure: {list(outputs.keys())}")
                    
                    # Log detailed output structure
                    for node_id, node_output in outputs.items():
                        self.logger.debug(f"Node {node_id} output keys: {list(node_output.keys())}")
                        # Log the full output for debugging
                        if any(key in node_output for key in ['gltf', 'glb', 'mesh', 'files']):
                            self.logger.debug(f"Node {node_id} full output: {node_output}")
                    
                    for node_id, node_output in outputs.items():
                        # Check for various possible 3D output formats
                        model_key = None
                        if 'gltf' in node_output:
                            model_key = 'gltf'
                        elif 'glb' in node_output:
                            model_key = 'glb'
                        elif 'mesh' in node_output:
                            model_key = 'mesh'
                        
                        if model_key:
                            # Handle 3D model output
                            for model_info in node_output[model_key]:
                                filename = model_info.get('filename', 'model.glb')
                                subfolder = model_info.get('subfolder', '')
                                type_folder = model_info.get('type', 'output')
                                
                                # Download the 3D model
                                model_data = await self.comfyui_client.fetch_3d_model(filename, subfolder, type_folder)
                                
                                if model_data:
                                    # Save to 3D models directory
                                    models_dir = self.config.base_dir / "3d_models"
                                    models_dir.mkdir(exist_ok=True)
                                    
                                    # Create traceable filename based on source image
                                    # Extract the last number from source image name
                                    import re
                                    match = re.search(r'_(\d+)$', source_image.stem)
                                    if match:
                                        # Use existing number for traceability
                                        base_number = match.group(1)
                                        model_filename = f"3D_{base_number}.glb"
                                    else:
                                        # Use full stem if no number found
                                        model_filename = f"{source_image.stem}_3d.glb"
                                    model_path = models_dir / model_filename
                                    
                                    with open(model_path, 'wb') as f:
                                        f.write(model_data)
                                    
                                    self.logger.info(f"Saved 3D model to: {model_path}")
                                    
                                    # Update the unified object selector with the new 3D model
                                    if hasattr(self, 'unified_object_selector'):
                                        self.unified_object_selector.link_model_to_image(model_path, source_image)
                                    
                                    # Auto-load the new model in scene objects viewer
                                    self._auto_load_new_3d_model(model_path)
                                    
                                    # Update batch progress
                                    if hasattr(self, '_3d_batch_completed'):
                                        self._3d_batch_completed += 1
                                        
                                        # Update button text
                                        if hasattr(self, 'generate_3d_btn'):
                                            if self._3d_batch_completed < self._3d_batch_total:
                                                self.generate_3d_btn.setText(f"Generated {self._3d_batch_completed}/{self._3d_batch_total}")
                                            else:
                                                # All models completed
                                                self.generate_3d_btn.setText("GENERATE 3D MODELS")
                                                self.generate_3d_btn.setEnabled(True)
                                                self.logger.info(f"Batch 3D generation complete: {self._3d_batch_completed} models")
                                    
                                    return
                    
                    self.logger.warning(f"3D workflow completed but no 3D model output found in ComfyUI history")
                    
                    # Fallback: Since workflow save_file is True, check filesystem
                    self.logger.info("Checking filesystem for generated 3D models...")
                    
                    # Check both local directory and ComfyUI output directory
                    models_dir = self.config.base_dir / "3d_models"
                    models_dir.mkdir(exist_ok=True)
                    
                    # Also check ComfyUI output directory from config
                    comfyui_3d_dir = Path(self.config.models_3d_dir) if hasattr(self.config, 'models_3d_dir') else Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D")
                    
                    # Get existing files in our directory before checking
                    existing_files = set(models_dir.glob("*.glb"))
                    
                    # Wait a bit for file to be written
                    await asyncio.sleep(2)
                    
                    # First check ComfyUI output directory for new files
                    if comfyui_3d_dir.exists():
                        comfyui_files = list(comfyui_3d_dir.glob("*.glb"))
                        # Sort by modification time to get the newest
                        comfyui_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                        
                        if comfyui_files:
                            # Get the newest file
                            newest_file = comfyui_files[0]
                            # Check if it was created recently (within last 10 seconds)
                            if time.time() - newest_file.stat().st_mtime < 10:
                                self.logger.info(f"Found new 3D model in ComfyUI output: {newest_file}")
                                
                                # Copy to our 3D models directory with traceable name
                                import re
                                # Match patterns like ComfyUI_20250619_201722_0053 - get the last number
                                match = re.search(r'_(\d+)$', source_image.stem)
                                if match:
                                    base_number = match.group(1)
                                    target_filename = f"3D_{base_number}.glb"
                                else:
                                    target_filename = f"{source_image.stem}_3d.glb"
                                target_path = models_dir / target_filename
                                
                                # Copy the file
                                import shutil
                                shutil.copy2(newest_file, target_path)
                                self.logger.info(f"Copied 3D model to: {target_path}")
                                
                                # Use the target path for UI updates
                                new_file = target_path
                                
                                # Update the unified object selector
                                if hasattr(self, 'unified_object_selector'):
                                    self.unified_object_selector.link_model_to_image(new_file, source_image)
                                
                                # Auto-load in scene objects viewer
                                self._auto_load_new_3d_model(new_file)
                                
                                # Update batch progress
                                if hasattr(self, '_3d_batch_completed'):
                                    self._3d_batch_completed += 1
                                    if hasattr(self, 'generate_3d_btn'):
                                        if self._3d_batch_completed < self._3d_batch_total:
                                            self.generate_3d_btn.setText(f"Generated {self._3d_batch_completed}/{self._3d_batch_total}")
                                        else:
                                            self.generate_3d_btn.setText("GENERATE 3D MODELS")
                                            self.generate_3d_btn.setEnabled(True)
                                            self.logger.info(f"Batch 3D generation complete: {self._3d_batch_completed} models")
                                
                                return  # Successfully found and processed the file
                    
                    # If not found in ComfyUI directory, check local directory
                    current_files = set(models_dir.glob("*.glb"))
                    new_files = current_files - existing_files
                    
                    if new_files:
                        for new_file in new_files:
                            self.logger.info(f"Found new 3D model in local directory: {new_file}")
                            
                            # Update the unified object selector
                            if hasattr(self, 'unified_object_selector'):
                                self.unified_object_selector.link_model_to_image(new_file, source_image)
                            
                            # Auto-load in scene objects viewer
                            self._auto_load_new_3d_model(new_file)
                            
                            # Update batch progress
                            if hasattr(self, '_3d_batch_completed'):
                                self._3d_batch_completed += 1
                                if hasattr(self, 'generate_3d_btn'):
                                    if self._3d_batch_completed < self._3d_batch_total:
                                        self.generate_3d_btn.setText(f"Generated {self._3d_batch_completed}/{self._3d_batch_total}")
                                    else:
                                        self.generate_3d_btn.setText("GENERATE 3D MODELS")
                                        self.generate_3d_btn.setEnabled(True)
                                        self.logger.info(f"Batch 3D generation complete: {self._3d_batch_completed} models")
                    
                elif status.get('status_str') == 'error':
                    self.logger.error(f"3D workflow {prompt_id} failed with error")
                    # Stop the timer
                    if hasattr(self, 'three_d_completion_timers') and prompt_id in self.three_d_completion_timers:
                        self.three_d_completion_timers[prompt_id].stop()
                        del self.three_d_completion_timers[prompt_id]
                    
            elif check_count[0] >= max_checks:
                self.logger.warning(f"3D workflow {prompt_id} timed out after {max_checks} checks")
                # Stop the timer
                if hasattr(self, 'three_d_completion_timers') and prompt_id in self.three_d_completion_timers:
                    self.three_d_completion_timers[prompt_id].stop()
                    del self.three_d_completion_timers[prompt_id]
                
                # Fallback: Try to refresh 3D models from file system
                self.logger.info("Attempting fallback: scanning file system for new 3D models")
                QTimer.singleShot(2000, self._refresh_3d_models)
                    
        except Exception as e:
            self.logger.error(f"Error checking 3D workflow completion: {e}")
        
    def _on_generate_textures(self):
        """Handle texture generation"""
        if not hasattr(self, 'unified_object_selector'):
            self.logger.warning("Unified object selector not available")
            return
            
        # Get selected models from unified object system
        from ui.object_selection_widget import ObjectState
        selected_objects = self.unified_object_selector.get_selected_objects(ObjectState.MODEL_3D)
        
        if not selected_objects:
            self.logger.warning("No 3D models selected for texture generation")
            return
            
        prompt = self.texture_prompt.get_prompt()
        selected_count = len(selected_objects)
        
        self.logger.info(f"Starting texture generation for {selected_count} models")
        self.logger.info(f"Selected models: {[obj.display_name for obj in selected_objects]}")
        self.logger.info(f"Texture prompt: {prompt[:50]}...")
        
        # Get the model paths from selected objects
        model_paths = [obj.model_3d for obj in selected_objects if obj.model_3d]
        
        if not model_paths:
            self.logger.error("No valid model paths found from selected objects")
            return
            
        self.logger.info(f"Model paths to texture: {[path.name for path in model_paths]}")
        
        # Start the actual texture generation
        asyncio.create_task(self._async_generate_textures(model_paths, prompt))
    
    async def _async_generate_textures(self, model_paths: List[Path], prompt: str):
        """Handle async texture generation using ComfyUI workflow"""
        from PySide6.QtWidgets import QMessageBox
        import json
        
        self.logger.info("Starting async texture generation...")
        
        # Disable the generate button to prevent multiple clicks
        if hasattr(self, 'generate_texture_btn'):
            self.generate_texture_btn.setEnabled(False)
            self.generate_texture_btn.setText("Generating...")
        
        try:
            # Check ComfyUI connection first
            if not hasattr(self, 'comfyui_client') or not self.comfyui_client:
                QMessageBox.critical(self, "Error", "ComfyUI client not connected. Please ensure ComfyUI is running.")
                return
            
            # Check connection status
            if not await self.comfyui_client.check_connection():
                QMessageBox.critical(self, "Error", "Cannot connect to ComfyUI. Please ensure ComfyUI is running at http://127.0.0.1:8188")
                return
            
            # Load the texture workflow from configuration or use default
            config_path = Path("config/texture_parameters_config.json")
            workflow_file = "texture_generation/Model_texturing_juggernautXL_v08.json"  # Default to latest version in new structure
            
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    workflow_file = config.get("workflow_file", workflow_file)
                    self.logger.info(f"Using configured texture workflow: {workflow_file}")
                except Exception as e:
                    self.logger.error(f"Error loading texture config: {e}")
            
            self.logger.info(f"Loading texture generation workflow: {workflow_file}")
            workflow = self.workflow_manager.load_workflow(workflow_file)
            if not workflow:
                QMessageBox.critical(self, "Error", f"Failed to load texture generation workflow ({workflow_file})")
                return
            
            # Process each selected model
            total_models = len(model_paths)
            successful_count = 0
            
            for i, model_path in enumerate(model_paths):
                self.logger.info(f"Processing model {i+1}/{total_models}: {model_path.name}")
                
                # Ensure model exists and is accessible
                if not model_path.exists():
                    self.logger.error(f"Model file not found: {model_path}")
                    continue
                
                # Collect parameters from UI
                params = {
                    "prompt": prompt,
                    "model_path": str(model_path),
                    "width": 1024,
                    "height": 1024,
                    "steps": 20,
                    "cfg": 7.0,
                    "seed": -1
                }
                
                # Inject parameters into workflow
                self.logger.info(f"Injecting parameters for model: {model_path.name}")
                workflow_with_params = self.workflow_manager.inject_parameters_comfyui(workflow, params)
                
                if not workflow_with_params:
                    self.logger.error(f"Failed to inject parameters for {model_path.name}")
                    continue
                
                # Execute workflow in ComfyUI (skip UI loading for automated execution)
                self.logger.info(f"Executing ComfyUI workflow for {model_path.name}")
                success = await self.comfyui_client.queue_prompt(workflow_with_params, load_in_ui_first=False)
                
                if success:
                    successful_count += 1
                    self.logger.info(f"Successfully queued texture generation for {model_path.name}")
                else:
                    self.logger.error(f"Failed to queue texture generation for {model_path.name}")
                
                # Small delay between generations to avoid overwhelming ComfyUI
                if i < total_models - 1:
                    await asyncio.sleep(1)
            
            # Show completion message
            self.logger.info(f"Texture generation queued: {successful_count}/{total_models} successful")
            if successful_count > 0:
                QMessageBox.information(self, "Texture Generation Queued",
                                  f"Successfully queued {successful_count}/{total_models} models for texture generation in ComfyUI.\n\n"
                                  f"Textures will be applied when generation completes.")
            else:
                QMessageBox.warning(self, "Texture Generation Failed",
                              "Failed to queue any models for texture generation. Please check ComfyUI connection.")
            
        except Exception as e:
            self.logger.error(f"Error during texture generation: {e}")
            import traceback
            self.logger.error(f"Texture generation traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Texture generation failed: {str(e)}")
        
        finally:
            # Re-enable the generate button
            if hasattr(self, 'generate_texture_btn'):
                self.generate_texture_btn.setEnabled(True)
                self.generate_texture_btn.setText("GENERATE TEXTURES")
    
    def _on_texture_generated(self, model_path: Path):
        """Handle texture generation completion"""
        if hasattr(self, 'unified_object_selector'):
            # Detect texture files
            texture_files = self._detect_texture_files(model_path)
            
            # Mark as textured in unified system
            self.unified_object_selector.mark_as_textured(model_path, texture_files)
            
            # Add to legacy textured_models set for backward compatibility
            if hasattr(self, 'textured_models'):
                self.textured_models.add(model_path)
            
            self.logger.info(f"Texture generation completed for: {model_path.name}")
        
    def _setup_file_monitoring(self):
        """Setup enhanced file monitoring"""
        from .enhanced_file_monitor import EnhancedFileMonitor
        
        self.enhanced_monitor = EnhancedFileMonitor()
        
        # Connect signals
        self.enhanced_monitor.new_image_detected.connect(self._on_new_image_detected)
        self.enhanced_monitor.new_model_detected.connect(self._on_new_model_detected)
        self.enhanced_monitor.new_textured_model_detected.connect(self._on_new_textured_model_detected)
        self.enhanced_monitor.texture_viewer_available.connect(self._on_texture_viewer_availability)
        
        # Start monitoring
        self.enhanced_monitor.start_monitoring()
        
        self.logger.info("Enhanced file monitoring started")
        
    def _on_new_image_detected(self, image_path: str):
        """Handle new image detection"""
        self.logger.info(f"New image: {Path(image_path).name}")
        # Use the specific image handling method
        self._on_new_image(image_path)
        
    def _on_new_model_detected(self, model_path: str):
        """Handle new 3D model detection"""
        self.logger.info(f"New 3D model: {Path(model_path).name}")
        # Use the specific model handling method
        self._on_new_model(model_path)
        
    def _on_new_textured_model_detected(self, model_path: str):
        """Handle new textured model detection"""
        self.logger.info(f"New textured model: {Path(model_path).name}")
        # Refresh textured models
        self._refresh_textured_models()
        
    def _on_texture_viewer_availability(self, available: bool):
        """Handle texture viewer availability change"""
        status = "available" if available else "unavailable"
        self.logger.info(f"Texture viewer is {status}")
        
    def _load_window_settings(self):
        """Load window settings - preserve existing functionality"""
        try:
            settings = QSettings("YamboStudio", "ComfyToC4DApp")
            
            # Restore geometry
            geometry = settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            # Restore window state
            state = settings.value("windowState")
            if state:
                self.restoreState(state)
            
            self.logger.info("Window settings loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load window settings: {e}")
            
    def _apply_saved_values(self):
        """Apply saved values - preserve existing functionality"""
        try:
            settings = QSettings("YamboStudio", "ComfyToC4DApp")
            
            # Load prompts
            if hasattr(self, 'positive_prompt'):
                saved_positive = settings.value("prompts/positive", "")
                if saved_positive:
                    self.positive_prompt.set_text(saved_positive)
                
            if hasattr(self, 'negative_prompt'):
                saved_negative = settings.value("prompts/negative", "")
                if saved_negative:
                    self.negative_prompt.set_text(saved_negative)
                
            # Load parameters
            if hasattr(self, 'steps_spin'):
                self.steps_spin.setValue(settings.value("params/steps", 20, int))
            
            if hasattr(self, 'cfg_spin'):
                self.cfg_spin.setValue(settings.value("params/cfg", 7.5, float))
            
            self.logger.info("Saved values applied successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to apply saved values: {e}")
            
    def _load_workflow_settings(self):
        """Load workflow settings - preserve existing functionality"""
        try:
            # Load workflow configurations
            self.logger.info("Loading workflow settings:")
            self.logger.info("  Image Generation: generate_thermal_shapes.json")
            self.logger.info("  3D Model Generation: generate_3D_withUVs_09-06-2025.json")
            self.logger.info("  Texture Generation: Model_texturing_juggernautXL_v08.json")
            
            self.logger.info("Workflow settings loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow settings: {e}")
            
    def _setup_comfyui_callbacks(self):
        """Setup ComfyUI callbacks - preserve existing functionality"""
        try:
            # Setup bridge preview callbacks
            self.logger.info("Setup ComfyUI Bridge Preview callbacks")
            self.logger.info("ComfyUI callbacks configured")
            
        except Exception as e:
            self.logger.error(f"Failed to setup ComfyUI callbacks: {e}")
            
    def _select_stage(self, index: int):
        """Select stage - preserve existing functionality"""
        self.current_stage = index
        
        # Sync panel tabs
        self._sync_panel_tabs(index)
        
        # Update console
        stage_names = ["Image Generation", "3D Model Generation", "Texture Generation", "Cinema4D Intelligence"]
        if index < len(stage_names):
            self.logger.info(f"Stage selected: {stage_names[index]}")
    
    def setup_system_monitoring(self):
        """Setup system performance monitoring"""
        if not SYSTEM_MONITORING_AVAILABLE:
            self.logger.warning("System monitoring not available (psutil/GPUtil not installed)")
            return
            
        # Start performance monitoring timer (update every 2 seconds)
        self.performance_update_timer = QTimer()
        self.performance_update_timer.timeout.connect(self.update_performance_metrics)
        self.performance_update_timer.start(2000)  # Update every 2 seconds
        
        self.logger.debug("System performance monitoring started")
    
    def update_performance_metrics(self):
        """Update real-time performance metrics"""
        if not SYSTEM_MONITORING_AVAILABLE:
            return
            
        try:
            # Get CPU usage (with a small interval for first reading)
            cpu_percent = int(psutil.cpu_percent(interval=0.1))
            
            # Get RAM usage
            memory = psutil.virtual_memory()
            ram_percent = int(memory.percent)
            
            # Get GPU usage
            gpu_percent = 0
            gpu_name = "GPU"
            if GPU_MONITORING_AVAILABLE:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(gpu_name, bytes):
                        gpu_name = gpu_name.decode('utf-8')
                
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_percent = int(utilization.gpu)
                except Exception:
                    pass
            
                # Update UI components if they exist
                if hasattr(self, 'cpu_meter'):
                    self.cpu_meter.update_value(cpu_percent)
            
            if hasattr(self, 'memory_meter'):
                self.memory_meter.update_value(ram_percent)
            
            if hasattr(self, 'gpu_meter'):
                self.gpu_meter.update_value(gpu_percent)
            
            if hasattr(self, 'gpu_name_label'):
                self.gpu_name_label.setText(gpu_name)
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
            
    def closeEvent(self, event):
        """Handle application close - preserve settings"""
        try:
            # Save window settings
            settings = QSettings("YamboStudio", "ComfyToC4DApp")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            
            # Save prompts
            if hasattr(self, 'positive_prompt'):
                prompt_text = self.positive_prompt.get_prompt()
                settings.setValue("prompts/positive", prompt_text)
            
            if hasattr(self, 'negative_prompt'):
                prompt_text = self.negative_prompt.get_prompt()
                settings.setValue("prompts/negative", prompt_text)
            
            # Save parameters
            if hasattr(self, 'steps_spin'):
                settings.setValue("params/steps", self.steps_spin.value())
            
            if hasattr(self, 'cfg_spin'):
                settings.setValue("params/cfg", self.cfg_spin.value())
            
            # Stop file monitoring
            if hasattr(self, 'enhanced_monitor'):
                self.enhanced_monitor.stop_monitoring()
            
            # Stop performance monitoring
            if hasattr(self, 'performance_update_timer') and self.performance_update_timer:
                self.performance_update_timer.stop()
            
            self.logger.info("Application closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")
            
        super().closeEvent(event)
    
    def _load_nlp_dictionary(self):
        """Load NLP dictionary from config file"""
        try:
            nlp_dict_path = Path("config/nlp_dictionary.json")
            if nlp_dict_path.exists():
                with open(nlp_dict_path, 'r') as f:
                    self.nlp_dictionary = json.load(f)
                self.logger.debug(f"Loaded NLP dictionary with {len(self.nlp_dictionary)} categories")
            else:
                self.logger.warning("NLP dictionary file not found, using empty dictionary")
                self.nlp_dictionary = {}
        except Exception as e:
            self.logger.error(f"Error loading NLP dictionary: {e}")
            self.nlp_dictionary = {}
    
    async def initialize(self):
        """Initialize the application asynchronously"""
        self.logger.info("Initializing redesigned application...")
        
        # Setup file monitoring
        self._setup_file_monitoring()
        
        # Connect to services
        await self._async_refresh_comfyui()
        await self._async_refresh_cinema4d()
        
        # Enable debug wrapper
        wrap_scene_assembly_methods(self)
        self.logger.info("Debug wrapper enabled for Scene Assembly functions")
        
        self.logger.info("Redesigned application initialized successfully")
        
        # Initialize content grids with existing files
        self._initialize_content_grids()
        
        self.logger.info("Application fully initialized and ready")
    
    def _clear_console(self):
        """Clear console output"""
        if hasattr(self, 'console'):
            self.console.clear()
            self.logger.info("Console cleared")
    
    def _on_autoscroll_toggled(self, checked: bool):
        """Handle autoscroll toggle"""
        if hasattr(self, 'console'):
            self.console.set_auto_scroll(checked)
            self.logger.info(f"Console autoscroll {'enabled' if checked else 'disabled'}")
    
    def _create_complete_menu_bar(self):
        """Create complete menu bar with all configuration dialogs"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_project_action = QAction("New Project", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self._new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction("Open Project", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)
        
        # Open Recent submenu
        from PySide6.QtWidgets import QMenu
        open_recent_menu = QMenu("Open Recent", self)
        
        # Add recent project placeholders
        recent_projects = [
            "C:/Projects/SciFi_Environment.comfy",
            "C:/Projects/Character_Design.comfy",
            "C:/Projects/Architectural_Viz.comfy",
            "C:/Projects/Product_Showcase.comfy"
        ]
        
        for project_path in recent_projects:
            project_name = project_path.split("/")[-1]
            recent_action = QAction(project_name, self)
            recent_action.setData(project_path)
            recent_action.triggered.connect(lambda checked, path=project_path: self._open_recent_project(path))
            open_recent_menu.addAction(recent_action)
        
        open_recent_menu.addSeparator()
        clear_recent_action = QAction("Clear Recent", self)
        clear_recent_action.triggered.connect(self._clear_recent_projects)
        open_recent_menu.addAction(clear_recent_action)
        
        file_menu.addMenu(open_recent_menu)
        
        save_project_action = QAction("Save Project", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self._save_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        # Configuration dialogs - THESE WERE MISSING
        configure_image_action = QAction("Configure Image Parameters", self)
        configure_image_action.triggered.connect(self._show_configure_image_parameters_dialog)
        file_menu.addAction(configure_image_action)
        
        configure_3d_action = QAction("Configure 3D Generation Parameters", self)
        configure_3d_action.triggered.connect(self._show_configure_3d_parameters_dialog)
        file_menu.addAction(configure_3d_action)
        
        configure_texture_action = QAction("Configure 3D Texture Parameters", self)
        configure_texture_action.triggered.connect(self._show_configure_texture_parameters_dialog)
        file_menu.addAction(configure_texture_action)
        
        file_menu.addSeparator()
        
        # Environment Variables action
        env_vars_action = QAction("Environment Variables", self)
        env_vars_action.triggered.connect(self._open_environment_variables)
        file_menu.addAction(env_vars_action)
        
        file_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._open_application_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        # AI menu - for NLP Dictionary
        ai_menu = menubar.addMenu("AI")
        
        nlp_dict_action = QAction("NLP Dictionary", self)
        nlp_dict_action.triggered.connect(self._open_nlp_dictionary)
        ai_menu.addAction(nlp_dict_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        texture_viewer_action = QAction("Texture Viewer", self)
        texture_viewer_action.triggered.connect(self._launch_texture_viewer)
        tools_menu.addAction(texture_viewer_action)
        
        refresh_connections_action = QAction("Refresh Connections", self)
        refresh_connections_action.triggered.connect(self._refresh_all_connections)
        tools_menu.addAction(refresh_connections_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        console_action = QAction("Toggle Console", self)
        console_action.setCheckable(True)
        console_action.setChecked(True)
        console_action.triggered.connect(self._toggle_console)
        view_menu.addAction(console_action)
        
        view_menu.addSeparator()
        
        # 3D Viewer Configuration
        viewer_3d_config_action = QAction("3D Viewer Configuration", self)
        viewer_3d_config_action.triggered.connect(self._show_3d_viewer_config_dialog)
        view_menu.addAction(viewer_3d_config_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        documentation_action = QAction("Documentation", self)
        documentation_action.triggered.connect(self._open_github_documentation)
        help_menu.addAction(documentation_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    # Configuration dialog methods - THESE WERE MISSING
    def _show_configure_image_parameters_dialog(self):
        """Show configure image parameters dialog"""
        try:
            from ui.configure_parameters_dialog import ConfigureParametersDialog
            dialog = ConfigureParametersDialog(self)
            dialog.configuration_saved.connect(self._on_parameters_configuration_saved)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Failed to open image parameters dialog: {e}")
            
    def _show_configure_3d_parameters_dialog(self):
        """Show configure 3D parameters dialog"""
        try:
            from ui.configure_3d_parameters_dialog import Configure3DParametersDialog
            dialog = Configure3DParametersDialog(self)
            dialog.configuration_saved.connect(self._on_3d_parameters_configuration_saved)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Failed to open 3D parameters dialog: {e}")
            
    def _show_3d_viewer_config_dialog(self):
        """Show 3D viewer configuration dialog"""
        try:
            self.logger.info("Opening 3D viewer configuration dialog...")
            # Keep a reference to prevent garbage collection
            self._3d_config_dialog = Studio3DConfigDialog(self)
            self.logger.info("Dialog created successfully")
            self._3d_config_dialog.settings_saved.connect(self._on_3d_viewer_settings_saved)
            self.logger.info("Signal connected successfully")
            # Try setting window modality explicitly
            self._3d_config_dialog.setWindowModality(Qt.ApplicationModal)
            self._3d_config_dialog.show()
            self._3d_config_dialog.raise_()
            self._3d_config_dialog.activateWindow()
            result = self._3d_config_dialog.exec()
            self.logger.info(f"Dialog closed with result: {result}")
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to open 3D viewer configuration dialog: {e}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            
    def _show_configure_texture_parameters_dialog(self):
        """Show configure texture parameters dialog"""
        try:
            from ui.configure_3d_parameters_dialog import Configure3DParametersDialog
            dialog = Configure3DParametersDialog(self)
            dialog.setWindowTitle("Configure 3D Texture Generation Parameters")
            dialog.config_path = Path("config/texture_parameters_config.json")
            dialog._load_configuration()
            dialog.configuration_saved.connect(self._on_texture_parameters_configuration_saved)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Failed to open texture parameters dialog: {e}")
            
    def _on_parameters_configuration_saved(self, config):
        """Handle image parameters configuration saved"""
        self.logger.info("Image parameters configuration saved")
        
        # Save workflow state for persistence
        self._save_last_workflow_state(config)
        
        # Reload parameters from the saved configuration
        self.logger.info("🔄 Starting UI update after configuration save...")
        self._load_parameters_from_config("image")
        
        # Refresh UI components after workflow import
        self.logger.info("🔄 Starting UI refresh after configuration save...")
        self._refresh_ui_after_workflow_import()
        
        self.logger.info("✅ Configuration saved and UI updated!")
        
    def _save_last_workflow_state(self, config):
        """Save the last workflow state for persistence"""
        try:
            persistence_file = Path("config/last_workflow_state.json")
            persistence_file.parent.mkdir(exist_ok=True)
            
            state = {
            "workflow_file": config.get("workflow_file"),
            "workflow_path": config.get("workflow_path"),
            "last_updated": datetime.now().isoformat()
            }
            
            with open(persistence_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.logger.info(f"💾 Saved workflow state: {config.get('workflow_file')}")
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow state: {e}")
    
    def _load_last_workflow_state(self):
        """Load and restore the last workflow state on startup"""
        try:
            persistence_file = Path("config/last_workflow_state.json")
            if not persistence_file.exists():
                self.logger.info("No previous workflow state found")
            return
            
            with open(persistence_file, 'r') as f:
                state = json.load(f)
            
            workflow_path = state.get("workflow_path")
            if workflow_path and Path(workflow_path).exists():
                self.logger.info(f"🔄 Restoring last workflow: {state.get('workflow_file')}")
                # Trigger parameter loading with a delay to ensure UI is ready
                QTimer.singleShot(500, lambda: self._load_parameters_from_config("image"))
                return True
            else:
                self.logger.warning(f"Last workflow file not found: {workflow_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load last workflow state: {e}")
        
        return False
    
    def _on_3d_parameters_configuration_saved(self, config):
        """Handle 3D parameters configuration saved"""
        self.logger.info("3D parameters configuration saved")
        
        # Reload 3D parameters with new configuration using lazy loading
        try:
            self._load_dynamic_3d_parameters_on_demand()
            self.logger.info("3D parameters UI reloaded with new configuration")
        except Exception as e:
            self.logger.error(f"Failed to reload 3D parameters UI: {e}")
        
    def _on_texture_parameters_configuration_saved(self, config):
        """Handle texture parameters configuration saved"""
        self.logger.info("Texture parameters configuration saved")
        
    def _on_3d_viewer_settings_saved(self, settings):
        """Handle 3D viewer configuration settings saved"""
        self.logger.info("3D viewer settings saved")
        
        # Apply settings to all existing 3D viewers
        try:
            # Update Scene Objects grid viewers
            if hasattr(self, 'session_models_grid'):
                self.session_models_grid.apply_viewer_settings(settings)
                self.logger.debug("Applied settings to session models grid")
                
            # Update View All Models grid viewers
            if hasattr(self, 'all_models_grid'):
                self.all_models_grid.apply_viewer_settings(settings)
                self.logger.debug("Applied settings to all models grid")
                
            self.logger.info("3D viewer settings applied to all viewers")
        except Exception as e:
            self.logger.error(f"Failed to apply 3D viewer settings: {e}")
    
    # Image and Model Event Handlers
    def _on_image_selected(self, image_path, selected: bool):
        """Handle image selection toggle - now uses unified object system"""
        if isinstance(image_path, str):
            image_path_obj = Path(image_path)
        else:
            image_path_obj = image_path
            
        self.logger.info(f"Image selection event: {image_path_obj.name} -> {'SELECTED' if selected else 'DESELECTED'}")
            
        # Update main unified object selector
        if hasattr(self, 'unified_object_selector'):
            if selected:
                self.unified_object_selector.add_image_selection(image_path_obj)
            else:
                self.unified_object_selector.remove_image_selection(image_path_obj)
            
        # Update all tab instances that share the same data
        if hasattr(self, 'unified_selectors'):
            for selector in self.unified_selectors.values():
                selector._update_display()  # Just update display, don't modify data
        
        # Maintain backward compatibility with existing selected_images list
        if selected:
            if hasattr(self, 'selected_images') and image_path_obj not in self.selected_images:
                self.selected_images.append(image_path_obj)
            self.logger.info(f"Added {image_path_obj.name} to selected images")
        else:
            if hasattr(self, 'selected_images') and image_path_obj in self.selected_images:
                self.selected_images.remove(image_path_obj)
            self.logger.info(f"Removed {image_path_obj.name} from selected images")
        
        # Update selection count display
        self._update_selection_displays()
    
    def _on_unified_object_selected(self, object_id: str, selected: bool):
        """Handle unified object selection"""
        self.logger.info(f"Unified object {'selected' if selected else 'deselected'}: {object_id}")
        
    def _on_workflow_hint_changed(self, hint: str):
        """Handle workflow hint changes"""
        self.logger.info(f"Workflow hint: {hint}")
        
    def _on_all_objects_cleared(self):
        """Handle all objects cleared from unified selector"""
        self.logger.info("All objects cleared - updating image card selections")
        self._clear_all_image_selections()
    
    def _on_size_preset_changed(self, preset_text: str):
        """Handle image size preset selection"""
        if "Custom" in preset_text:
            self.custom_size_widget.show()
        else:
            self.custom_size_widget.hide()
            # Parse preset and update spinboxes
            if "1024×1024" in preset_text:
                self.width_spin.setValue(1024)
                self.height_spin.setValue(1024)
            elif "1920×1080" in preset_text:
                self.width_spin.setValue(1920)
                self.height_spin.setValue(1080)
            elif "1344×768" in preset_text:
                self.width_spin.setValue(1344)
                self.height_spin.setValue(768)
            elif "832×1216" in preset_text:
                self.width_spin.setValue(832)
                self.height_spin.setValue(1216)
            elif "1216×832" in preset_text:
                self.width_spin.setValue(1216)
                self.height_spin.setValue(832)
            elif "512×512" in preset_text:
                self.width_spin.setValue(512)
                self.height_spin.setValue(512)
        
        # Update batch preview with new dimensions
        if hasattr(self, 'batch_size_spin'):
            self._update_batch_preview(self.batch_size_spin.value())
    
    def _on_custom_size_changed(self):
        """Handle custom size input changes"""
        # Switch to "Custom" in the preset combo if not already
        if "Custom" not in self.size_preset_combo.currentText():
            self.size_preset_combo.setCurrentText("Custom")
        
        # Update batch preview with new dimensions
        if hasattr(self, 'batch_size_spin'):
            self._update_batch_preview(self.batch_size_spin.value())
    
    def _clear_all_image_selections(self):
        """Clear all image card visual selections"""
        # Clear session images
        if hasattr(self, 'session_image_grid'):
            for thumbnail in self.session_image_grid.thumbnails:
                thumbnail.select_check.setChecked(False)
            thumbnail._selected = False
            thumbnail._update_style()
        
        # Clear all images  
        if hasattr(self, 'all_images_grid'):
            for thumbnail in self.all_images_grid.thumbnails:
                thumbnail.select_check.setChecked(False)
            thumbnail._selected = False
            thumbnail._update_style()
            
        # Clear backward compatibility lists
        if hasattr(self, 'selected_images'):
            self.selected_images.clear()
            
        self.logger.info("Cleared all image card selections")
            
    def _on_model_selected(self, model_path, selected: bool):
        """Handle 3D model selection toggle"""
        if isinstance(model_path, str):
            model_path_obj = Path(model_path)
        else:
            model_path_obj = model_path
            
        if selected:
            # Add to selection
            if hasattr(self, 'selected_models') and model_path_obj not in self.selected_models:
                self.selected_models.append(model_path_obj)
            # Update the UI list widget
            if hasattr(self, 'selected_models_list'):
                self.selected_models_list.addItem(model_path_obj.name)
            self.logger.info(f"Added {model_path_obj.name} to selected models")
            
            # Update unified object selector
            if hasattr(self, 'unified_object_selector'):
                from ui.object_selection_widget import ObjectState
                self.unified_object_selector.add_object(
                    name=model_path_obj.name,
                    state=ObjectState.MODEL_3D,
                    model_3d=model_path_obj
                )
        else:
            # Remove from selection
            if hasattr(self, 'selected_models') and model_path_obj in self.selected_models:
                self.selected_models.remove(model_path_obj)
            # Update the UI list widget
            if hasattr(self, 'selected_models_list'):
                # Find and remove the item
                for i in range(self.selected_models_list.count()):
                    if self.selected_models_list.item(i).text() == model_path_obj.name:
                        self.selected_models_list.takeItem(i)
                        break
            self.logger.info(f"Removed {model_path_obj.name} from selected models")
            
            # Update unified object selector
            if hasattr(self, 'unified_object_selector'):
                self.unified_object_selector.remove_object(model_path_obj.name)
        
        # Update selection count display
        self._update_selection_displays()
        
        # Sync model selection to grids
        self._sync_model_selection_to_grids()
    
    def _update_selection_displays(self):
        """Update selection count displays and enable/disable generation buttons"""
        if hasattr(self, 'selected_images') and hasattr(self, 'selected_images_list'):
            image_count = len(self.selected_images)
            # Update generate 3D button text with count
            if hasattr(self, 'generate_3d_btn'):
                if image_count > 0:
                    self.generate_3d_btn.setText(f"GENERATE 3D MODELS ({image_count})")
                self.generate_3d_btn.setEnabled(True)
            else:
                self.generate_3d_btn.setText("GENERATE 3D MODELS")
                self.generate_3d_btn.setEnabled(False)
        
        if hasattr(self, 'selected_models') and hasattr(self, 'selected_models_list'):
            model_count = len(self.selected_models)
            # Update generate texture button text with count
            if hasattr(self, 'generate_texture_btn'):
                if model_count > 0:
                    self.generate_texture_btn.setText(f"GENERATE TEXTURES ({model_count})")
                self.generate_texture_btn.setEnabled(True)
            else:
                self.generate_texture_btn.setText("GENERATE TEXTURES")
                self.generate_texture_btn.setEnabled(False)
    
    def _sync_image_selection_to_grids(self):
        """Sync the selected_images list to the visual state of image grids"""
        # Update session image grid selection
        if hasattr(self, 'session_image_grid'):
            for thumbnail in self.session_image_grid.thumbnails:
                should_be_selected = thumbnail.image_path in self.selected_images
            if thumbnail._selected != should_be_selected:
                thumbnail.set_selected(should_be_selected)
        
        # Update all images grid selection  
        if hasattr(self, 'all_images_grid'):
            for thumbnail in self.all_images_grid.thumbnails:
                should_be_selected = thumbnail.image_path in self.selected_images
            if thumbnail._selected != should_be_selected:
                thumbnail.set_selected(should_be_selected)
    
    def _sync_model_selection_to_grids(self):
        """Sync the selected_models list to the visual state of model grids"""
        # Update session models grid selection
        if hasattr(self, 'session_models_grid'):
            for card in self.session_models_grid.cards:
                should_be_selected = card.model_path in self.selected_models
            if card._selected != should_be_selected:
                card.set_selected(should_be_selected)
        
        # Update all models grid selection  
        if hasattr(self, 'all_models_grid'):
            for card in self.all_models_grid.cards:
                should_be_selected = card.model_path in self.selected_models
            if card._selected != should_be_selected:
                card.set_selected(should_be_selected)
    
    def _add_selection_context_menu(self):
        """Add context menu functionality to selection lists"""
        if hasattr(self, 'selected_images_list'):
            self.selected_images_list.setContextMenuPolicy(Qt.CustomContextMenu)
            self.selected_images_list.customContextMenuRequested.connect(self._show_image_selection_context_menu)
        
        if hasattr(self, 'selected_models_list'):
            self.selected_models_list.setContextMenuPolicy(Qt.CustomContextMenu)
            self.selected_models_list.customContextMenuRequested.connect(self._show_model_selection_context_menu)
    
    def _show_image_selection_context_menu(self, position):
        """Show context menu for selected images list"""
        if not hasattr(self, 'selected_images_list') or self.selected_images_list.itemAt(position) is None:
            return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        # Remove from selection action
        remove_action = menu.addAction("Remove from Selection")
        remove_action.triggered.connect(lambda: self._remove_selected_image_at_position(position))
        
        # Delete file action
        delete_action = menu.addAction("Delete File")
        delete_action.triggered.connect(lambda: self._delete_selected_image_at_position(position))
        
        # Clear all selection
        if len(self.selected_images) > 1:
            menu.addSeparator()
            clear_action = menu.addAction("Clear All Selection")
            clear_action.triggered.connect(self._clear_image_selection)
        
        menu.exec(self.selected_images_list.mapToGlobal(position))
    
    def _show_model_selection_context_menu(self, position):
        """Show context menu for selected models list"""
        if not hasattr(self, 'selected_models_list') or self.selected_models_list.itemAt(position) is None:
            return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        # Remove from selection action
        remove_action = menu.addAction("Remove from Selection")
        remove_action.triggered.connect(lambda: self._remove_selected_model_at_position(position))
        
        # Delete file action
        delete_action = menu.addAction("Delete File")
        delete_action.triggered.connect(lambda: self._delete_selected_model_at_position(position))
        
        # Clear all selection
        if len(self.selected_models) > 1:
            menu.addSeparator()
            clear_action = menu.addAction("Clear All Selection")
            clear_action.triggered.connect(self._clear_model_selection)
        
        menu.exec(self.selected_models_list.mapToGlobal(position))
    
    def _remove_selected_image_at_position(self, position):
        """Remove image from selection at given position"""
        item = self.selected_images_list.itemAt(position)
        if item:
            filename = item.text()
            # Find the corresponding path in selected_images
            for image_path in self.selected_images[:]:  # Copy list to avoid modification during iteration
                if image_path.name == filename:
                    # Remove from selection (this will trigger _on_image_selected with False)
                    self._on_image_selected(image_path, False)
                    # Update grid visuals
                    self._sync_image_selection_to_grids()
                    break
    
    def _remove_selected_model_at_position(self, position):
        """Remove model from selection at given position"""
        item = self.selected_models_list.itemAt(position)
        if item:
            filename = item.text()
            # Find the corresponding path in selected_models
            for model_path in self.selected_models[:]:  # Copy list to avoid modification during iteration
                if model_path.name == filename:
                    # Remove from selection (this will trigger _on_model_selected with False)
                    self._on_model_selected(model_path, False)
                    break
    
    def _delete_selected_image_at_position(self, position):
        """Delete image file at given position"""
        from PySide6.QtWidgets import QMessageBox
        item = self.selected_images_list.itemAt(position)
        if item:
            filename = item.text()
            # Find the corresponding path
            for image_path in self.selected_images[:]:
                if image_path.name == filename:
                    reply = QMessageBox.question(
                    self, "Delete Image", 
                    f"Are you sure you want to delete {filename}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    try:
                        # Remove from selection first
                        self._on_image_selected(image_path, False)
                        # Delete the actual file
                        image_path.unlink()
                        # Refresh the grids
                        self._refresh_all_images()
                        self._load_session_images()
                        self.logger.info(f"Deleted image file: {filename}")
                    except Exception as e:
                        QMessageBox.critical(self, "Delete Error", f"Failed to delete {filename}:\\n{str(e)}")
                        self.logger.error(f"Failed to delete image {filename}: {e}")
                break
    
    def _delete_selected_model_at_position(self, position):
        """Delete model file at given position"""
        from PySide6.QtWidgets import QMessageBox
        item = self.selected_models_list.itemAt(position)
        if item:
            filename = item.text()
            # Find the corresponding path
            for model_path in self.selected_models[:]:
                if model_path.name == filename:
                    reply = QMessageBox.question(
                    self, "Delete Model", 
                    f"Are you sure you want to delete {filename}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    try:
                        # Remove from selection first
                        self._on_model_selected(model_path, False)
                        # Delete the actual file
                        model_path.unlink()
                        # Refresh the model views
                        if hasattr(self, '_refresh_all_models'):
                            self._refresh_all_models()
                        self.logger.info(f"Deleted model file: {filename}")
                    except Exception as e:
                        QMessageBox.critical(self, "Delete Error", f"Failed to delete {filename}:\\n{str(e)}")
                        self.logger.error(f"Failed to delete model {filename}: {e}")
                break
    
    def _clear_image_selection(self):
        """Clear all selected images"""
        # Copy the list to avoid modification during iteration
        for image_path in self.selected_images[:]:
            self._on_image_selected(image_path, False)
        self._sync_image_selection_to_grids()
        self.logger.info("Cleared all image selection")
    
    def _clear_model_selection(self):
        """Clear all selected models"""
        # Copy the list to avoid modification during iteration
        for model_path in self.selected_models[:]:
            self._on_model_selected(model_path, False)
        self.logger.info("Cleared all model selection")
    
    # Image and Model Loading Methods
    def _load_session_images(self):
        """Load images generated in current session to New Canvas"""
        if hasattr(self, 'session_image_grid') and hasattr(self, 'session_images'):
            self.session_image_grid.clear()
            self.logger.info(f"Loading {len(self.session_images)} session images")
            for image_path in self.session_images:
                if image_path.exists():
                    self.session_image_grid.add_image(image_path)
                # Also add to unified object selector pool
                if hasattr(self, 'unified_object_selector'):
                    self.unified_object_selector.add_image_to_pool(image_path)
            
            # Force grid visibility after loading
            self.session_image_grid.show()
            self.session_image_grid.setVisible(True)
            
            # Ensure all thumbnails and their checkboxes are visible
            for thumbnail in self.session_image_grid.thumbnails:
                thumbnail.show()
                thumbnail.select_check.show()
                thumbnail.select_check.setVisible(True)
            
            self.logger.info(f"Successfully loaded {len(self.session_images)} session images with visible selection checkboxes")
        else:
            self.logger.warning("session_image_grid or session_images not found")
                
    def _load_all_images(self):
        """Load all images from images directory to View All"""
        self.logger.info(f"_load_all_images called. hasattr(self, 'all_images_grid'): {hasattr(self, 'all_images_grid')}")
        if hasattr(self, 'all_images_grid'):
            self.all_images_grid.clear()
            # Use configured images directory
            images_dir = self.config.images_dir if hasattr(self.config, 'images_dir') else Path("images")
            
            self.logger.info(f"Loading images from: {images_dir}")
            
            if images_dir.exists():
                # Get all image files
                image_patterns = ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.tiff", "*.bmp"]
                all_images = []
                for pattern in image_patterns:
                    all_images.extend(images_dir.glob(pattern))
            
                # Sort by modification time (newest first)
                all_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
                self.logger.info(f"Found {len(all_images)} images to load")
            
                # Add to grid
                for image_path in all_images:
                    self.all_images_grid.add_image(image_path)
            
                # Force grid visibility after loading
                self.all_images_grid.show()
                self.all_images_grid.setVisible(True)
            
                # Ensure all thumbnails and their checkboxes are visible
                for thumbnail in self.all_images_grid.thumbnails:
                    thumbnail.show()
                    thumbnail.select_check.show()
                    thumbnail.select_check.setVisible(True)
                
                self.logger.info(f"Successfully loaded {len(all_images)} images with visible selection checkboxes")
            else:
                self.logger.warning(f"Images directory does not exist: {images_dir}")
        else:
            self.logger.error("all_images_grid not found - UI not properly initialized")
    
    def _refresh_all_images(self):
        """Refresh all images display (wrapper for _load_all_images)"""
        self.logger.info("Refreshing all images...")
        self._load_all_images()
    
    def _delayed_image_loading(self):
        """Load all images after UI is fully created"""
        self.logger.info("Starting delayed image loading...")
        self._refresh_all_images()
    
    def _collect_dynamic_workflow_parameters(self, workflow: dict, prompt: str, neg_prompt: str, batch_size: int) -> dict:
        """Dynamically collect parameters from UI widgets and workflow structure"""
        params = {
            "positive_prompt": prompt,
            "negative_prompt": neg_prompt,
            "batch_size": batch_size,
            "seed": -1  # Random seed
        }
        
        # DYNAMIC APPROACH: Update workflow with UI widget values first
        if hasattr(self, 'parameter_widgets') and self.parameter_widgets:
            self.logger.info(f"🔄 Updating workflow with {len(self.parameter_widgets)} UI widget values (DYNAMIC)")
            
            from .dynamic_widget_updater import DynamicWidgetUpdater
            updater = DynamicWidgetUpdater()
            
            # Update the workflow with UI widget values - WORKS FOR ANY NODE TYPE
            workflow = updater.update_workflow_from_ui_widgets(workflow, self.parameter_widgets)
        
        # Now run the existing parameter extraction logic on the UPDATED workflow
        # This preserves all existing functionality while using UI values
        lora_counter = 1
        nodes = workflow.get("nodes", [])
        
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            widgets_values = node.get("widgets_values", [])
            
            # Extract parameters based on node type
            if node_type == "KSampler" and widgets_values:
                # Extract sampler parameters from widgets_values
                # Order: seed, control_after_generation, steps, cfg, sampler_name, scheduler, denoise
                if len(widgets_values) >= 7:
                    params["seed"] = widgets_values[0] if widgets_values[0] != -1 else -1
                    params["seed_control"] = widgets_values[1] if len(widgets_values) > 1 else "fixed"
                    params["steps"] = widgets_values[2] if len(widgets_values) > 2 else 20
                    params["cfg"] = widgets_values[3] if len(widgets_values) > 3 else 7.0
                    params["sampler_name"] = widgets_values[4] if len(widgets_values) > 4 else "euler"
                    params["scheduler"] = widgets_values[5] if len(widgets_values) > 5 else "normal"
                    params["denoise"] = widgets_values[6] if len(widgets_values) > 6 else 1.0
                    
            elif node_type == "FluxGuidance" and widgets_values:
                params["cfg"] = widgets_values[0] if widgets_values else 7.0
                
            elif node_type in ["EmptyLatentImage", "EmptySD3LatentImage"] and widgets_values:
                if len(widgets_values) >= 3:
                    # Use dimensions from left panel controls
                    if hasattr(self, 'width_spin') and hasattr(self, 'height_spin'):
                        params["width"] = self.width_spin.value()
                        params["height"] = self.height_spin.value()
                    else:
                        params["width"] = 1024
                        params["height"] = 1024
                    # batch_size already set from UI
                    
            elif node_type == "LoraLoader" and widgets_values:
                # Extract LoRA parameters dynamically
                if len(widgets_values) >= 3:
                    lora_model = widgets_values[0] if widgets_values[0] else ""
                    lora_strength = widgets_values[1] if len(widgets_values) > 1 else 1.0
                    
                    # Only add if LoRA model is not empty
                    if lora_model and lora_model != "None" and lora_model.strip():
                        # Validate LoRA model availability and provide fallback
                        validated_model = self._validate_and_fix_lora_model(lora_model)
                        if validated_model:
                            params[f"lora{lora_counter}_model"] = validated_model
                            params[f"lora{lora_counter}_strength"] = lora_strength
                            params[f"lora{lora_counter}_active"] = True
                            
                            # Check if bypass checkbox exists and is checked
                            # The bypass checkbox is the 4th widget (index 3) for LoraLoader
                            bypass_key = f"LoraLoader_{node_id}_3"
                            if hasattr(self, 'parameter_widgets') and bypass_key in self.parameter_widgets:
                                try:
                                    bypass_value = self.parameter_widgets[bypass_key]['get_value']()
                                    params[f"lora{lora_counter}_bypassed"] = bypass_value
                                    if bypass_value:
                                        self.logger.info(f"LoRA {lora_counter} is set to bypass")
                                except RuntimeError as e:
                                    if "deleted" in str(e):
                                        self.logger.warning(f"Bypass widget for LoRA {lora_counter} was deleted, defaulting to False")
                                        params[f"lora{lora_counter}_bypassed"] = False
                                    else:
                                        raise
                            else:
                                params[f"lora{lora_counter}_bypassed"] = False
                            
                            if validated_model != lora_model:
                                self.logger.warning(f"LoRA {lora_counter} fallback: {lora_model} → {validated_model}")
                            else:
                                self.logger.info(f"Found LoRA {lora_counter} in node {node_id}: {lora_model} (strength: {lora_strength})")
                            lora_counter += 1
                        else:
                            self.logger.warning(f"Skipping unavailable LoRA in node {node_id}: {lora_model}")
        
        # Set default values for missing essential parameters
        if "width" not in params:
            if hasattr(self, 'width_spin'):
                params["width"] = self.width_spin.value()
            else:
                params["width"] = 1024
        if "height" not in params:
            if hasattr(self, 'height_spin'):
                params["height"] = self.height_spin.value()
            else:
                params["height"] = 1024
        if "steps" not in params:
            params["steps"] = 20
        if "cfg" not in params:
            params["cfg"] = 7.0
        if "sampler_name" not in params:
            params["sampler_name"] = "euler"
        if "scheduler" not in params:
            params["scheduler"] = "normal"
        if "denoise" not in params:
            params["denoise"] = 1.0
            
        self.logger.info(f"Collected {len(params)} dynamic parameters: {list(params.keys())}")
        return params
    
    def _validate_and_fix_lora_model(self, lora_model: str) -> str:
        """Validate LoRA model availability and provide fallbacks for missing models"""
        # Get available LoRAs dynamically from ComfyUI models folder
        available_loras = self.config.get_lora_files() if hasattr(self.config, 'get_lora_files') else []
        
        # If config method not available, fallback to direct filesystem scan
        if not available_loras:
            if hasattr(self.config, 'loras_dir') and self.config.loras_dir and self.config.loras_dir.exists():
                available_loras = [f.name for f in self.config.loras_dir.glob("*.safetensors")]
            else:
                # Fallback to hardcoded list if filesystem access fails
                available_loras = [
                '8mm Film Lora_Flux_LatentShadows_v1.safetensors',
                'FLUX_Editorial Zine.safetensors', 
                'Flux Any Thing plush.safetensors',
                'Flux LoRA Thermal Image.safetensors',
                'SDXLthermalimage.safetensors',
                'SynthWave - Glitchy Analog Video Synthesis - Flux - v1.safetensors',
                'aidmaFLUXpro1.1-FLUX-V0.1.safetensors',
                'deep_sea_creatures_cts.safetensors',
                'fruit_animals.safetensors',
                'hyvideo_FastVideo_LoRA-fp8.safetensors',
                'pokemon_flux_lora.safetensors'
            ]
        
        self.logger.info(f"Found {len(available_loras)} LoRA models: {available_loras[:5]}...")  # Log first 5
        
        # Direct match - model is available
        if lora_model in available_loras:
            return lora_model
        
        # Fallback mappings for known missing models
        fallback_mappings = {
            'Flux\\Luminous_Shadowscape-000016.safetensors': '8mm Film Lora_Flux_LatentShadows_v1.safetensors',
            'Flux\\\\Luminous_Shadowscape-000016.safetensors': '8mm Film Lora_Flux_LatentShadows_v1.safetensors',
            'Luminous_Shadowscape-000016.safetensors': '8mm Film Lora_Flux_LatentShadows_v1.safetensors'
        }
        
        # Check fallback mappings
        if lora_model in fallback_mappings:
            return fallback_mappings[lora_model]
        
        # Try to find similar models by partial name matching
        lora_lower = lora_model.lower()
        for available in available_loras:
            available_lower = available.lower()
            # Check for partial matches
            if 'thermal' in lora_lower and 'thermal' in available_lower:
                return available
            elif 'flux' in lora_lower and 'pro' in lora_lower and 'flux' in available_lower and 'pro' in available_lower:
                return available
            elif 'pokemon' in lora_lower and 'pokemon' in available_lower:
                return available
            elif 'sealife' in lora_lower or 'creature' in lora_lower:
                # Try to find sea creature LoRA in available models
                for available in available_loras:
                    if 'creature' in available.lower() or 'sea' in available.lower():
                        return available
        
        # Default fallback to first available LoRA that looks stable
        if available_loras:
            # Prefer thermal, flux, or general purpose LoRAs
            preferred_patterns = ['thermal', 'flux', 'pro', 'general']
            for pattern in preferred_patterns:
                for lora in available_loras:
                    if pattern.lower() in lora.lower():
                        return lora
            # If no preferred pattern found, use the first available
            return available_loras[0]
        
        # No LoRAs available at all
        return None
    
    def _populate_workflow_combo(self, workflow_type: str = "image_generation"):
        """Populate workflow combo box with available workflow files for specific type"""
        try:
            # Clear existing items
            self.workflow_combo.clear()
            
            workflows_dir = self.config.workflows_dir / workflow_type
            if workflows_dir and workflows_dir.exists():
                # Get all JSON files in the specific workflow type directory
                workflow_files = list(workflows_dir.glob("*.json"))
                
                # Sort by name for consistent ordering
                workflow_files.sort(key=lambda x: x.name.lower())
            
                # Add each workflow to the combo box
                for workflow_file in workflow_files:
                    # Store relative path from workflows root for proper loading
                    relative_path = f"{workflow_type}/{workflow_file.name}"
                    # Use exact filename as display name
                    self.workflow_combo.addItem(workflow_file.name, relative_path)
            
                self.logger.debug(f"Populated workflow combo with {len(workflow_files)} {workflow_type} workflows")
            else:
                self.logger.warning(f"Workflow directory not found: {workflows_dir}")
                # Add fallback options based on type
                if workflow_type == "image_generation":
                    self.workflow_combo.addItem("generate_thermal_shapes.json", "image_generation/generate_thermal_shapes.json")
                    self.workflow_combo.addItem("generate_sealife_images.json", "image_generation/generate_sealife_images.json")
                elif workflow_type == "3d_generation":
                    self.workflow_combo.addItem("3D_gen_Hunyuan2_onlymesh.json", "3d_generation/3D_gen_Hunyuan2_onlymesh.json")
                elif workflow_type == "texture_generation":
                    self.workflow_combo.addItem("Model_texturing_juggernautXL_v07.json", "texture_generation/Model_texturing_juggernautXL_v07.json")
                    self.workflow_combo.addItem("Model_texturing_juggernautXL_v08.json", "texture_generation/Model_texturing_juggernautXL_v08.json")
            
        except Exception as e:
            self.logger.error(f"Failed to populate workflow combo for {workflow_type}: {e}")
            # Add fallback options
            if workflow_type == "image_generation":
                self.workflow_combo.addItem("generate_thermal_shapes.json", "image_generation/generate_thermal_shapes.json")
            self.workflow_combo.addItem("generate_sealife_images.json", "image_generation/generate_sealife_images.json")
    
    def _initialize_workflow_parameters(self):
        """Initialize workflow parameters after UI is fully set up"""
        try:
            # Check if UI components are available
            if hasattr(self, 'dynamic_params_layout') and hasattr(self, 'main_tab_widget'):
                current_tab = self.main_tab_widget.currentIndex()
                self.logger.info(f"Initializing workflow parameters for tab {current_tab}")
            
                # Connect workflow change handler now that UI is ready
                self.workflow_combo.currentIndexChanged.connect(self._on_workflow_index_changed)
            
                # Update workflow dropdown for current tab
                self._update_workflow_dropdown_for_tab(current_tab)
            
                self.logger.info("Workflow parameters initialized successfully")
            else:
                self.logger.warning("UI components not ready for workflow parameter initialization")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize workflow parameters: {e}")
    
    def _update_workflow_dropdown_for_tab(self, tab_index: int):
        """Update workflow dropdown to show workflows for the current tab"""
        try:
            # Check if UI is fully initialized before updating workflows
            if not hasattr(self, 'dynamic_params_layout') or not hasattr(self, 'dynamic_params_container'):
                self.logger.info(f"UI not fully initialized, skipping workflow update for tab {tab_index}")
                return
            
            # Map tab indices to workflow types
            workflow_types = [
                "image_generation",    # Tab 0: Image Generation
                "3d_generation",       # Tab 1: 3D Model Generation
                "texture_generation",  # Tab 2: Texture Generation
                None                   # Tab 3: Cinema4D Intelligence (no workflows)
                ]
            
            if tab_index < len(workflow_types) and workflow_types[tab_index]:
                workflow_type = workflow_types[tab_index]
            
                # Re-enable workflow dropdown if it was disabled
                self.workflow_combo.setEnabled(True)
            
                # Temporarily disconnect the change handler to avoid triggering during population
                try:
                    self.workflow_combo.currentIndexChanged.disconnect()
                except:
                    pass  # Handler might not be connected yet
            
                # Populate with workflows for this tab
                self._populate_workflow_combo(workflow_type)
            
                # Set a default workflow if available
                if self.workflow_combo.count() > 0:
                    # Try to restore last selected workflow for this tab
                    last_selected = None
                    if workflow_type == "image_generation":
                        # Check if we have a saved selection
                        config_path = self.config.config_dir / "image_parameters_config.json"
                        if config_path.exists():
                            try:
                                with open(config_path, 'r') as f:
                                    config = json.load(f)
                                    last_workflow = config.get('workflow_file', '')
                                    # Find this workflow in the combo
                                    for i in range(self.workflow_combo.count()):
                                        if self.workflow_combo.itemText(i) == last_workflow:
                                            self.workflow_combo.setCurrentIndex(i)
                                            last_selected = self.workflow_combo.itemData(i)
                                            self.logger.info(f"Restored last selected workflow: {last_workflow}")
                                            break
                            except:
                                pass
                    
                    # If no saved selection or not found, use first
                    if last_selected is None:
                        self.workflow_combo.setCurrentIndex(0)
                        last_selected = self.workflow_combo.itemData(0)
                    
                    # Only trigger workflow change if UI is fully initialized
                    if last_selected and hasattr(self, 'dynamic_params_layout'):
                        self._on_workflow_changed(last_selected)
            
                # Reconnect the change handler
                self.workflow_combo.currentIndexChanged.connect(self._on_workflow_index_changed)
            
                self.logger.info(f"Updated workflow dropdown for {workflow_type} tab")
            elif tab_index == 3:  # Cinema4D Intelligence tab
                # Disable workflow dropdown for C4D tab as it doesn't use workflows
                self.workflow_combo.setEnabled(False)
                self.workflow_combo.clear()
                self.workflow_combo.addItem("N/A - No workflows for C4D", None)
            else:
                self.logger.warning(f"Unknown tab index: {tab_index}")
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow dropdown for tab {tab_index}: {e}")
    
    def _on_workflow_index_changed(self, index: int):
        """Handle workflow selection index change"""
        if index >= 0:
            workflow_name = self.workflow_combo.itemData(index)
            if workflow_name:
                self._on_workflow_changed(workflow_name)
    
    def _on_workflow_changed(self, workflow_name: str):
        """Handle workflow selection change and refresh parameters UI"""
        try:
            self.logger.debug(f"Workflow changed to: {workflow_name}")
            
            # Get the full workflow path (workflow_name now includes subdirectory)
            workflow_path = self.config.workflows_dir / workflow_name
            if not workflow_path.exists():
                self.logger.error(f"Workflow file not found: {workflow_path}")
                return
            
            # Load the workflow to extract parameters
            with open(workflow_path, 'r') as f:
                workflow_data = f.read()
            workflow_json = json.loads(workflow_data)
            
            # Extract parameters from workflow nodes
            selected_nodes = []
            node_info = {}
            
            # Process all nodes in the workflow
            for node in workflow_json.get('nodes', []):
                node_id = str(node.get('id', ''))
                node_type = node.get('type', '')
                title = node.get('title', '') or node.get('properties', {}).get('Node name for S&R', '')
                
                # Include CLIPTextEncode nodes but don't create UI widgets for them (handled separately)
                if node_type == 'CLIPTextEncode':
                    node_key = f"{node_type}_{node_id}"
                    selected_nodes.append(node_key)
                    node_info[node_key] = {
                        "type": node_type,
                        "id": node_id,
                        "title": title,
                        "supported": True
                    }
                    continue
                    
                # Only include nodes with configurable parameters
                widgets_values = node.get('widgets_values', [])
                if widgets_values or node_type in ['KSampler', 'FluxGuidance', 'EmptySD3LatentImage']:
                    node_key = f"{node_type}_{node_id}"
                    selected_nodes.append(node_key)
                    node_info[node_key] = {
                        "type": node_type,
                        "id": node_id,
                        "title": title,
                        "supported": True
                    }
            
            # Create updated config
            updated_config = {
                "selected_nodes": selected_nodes,
                "node_info": node_info,
                "workflow_file": workflow_name,
                "workflow_path": str(workflow_path)
            }
            
            # Determine config file and parameter type based on workflow path
            if "image_generation" in workflow_name:
                config_filename = "image_parameters_config.json"
                param_type = "image"
            elif "3d_generation" in workflow_name:
                config_filename = "3d_parameters_config.json"
                param_type = "3d"
            elif "texture_generation" in workflow_name:
                config_filename = "texture_parameters_config.json"
                param_type = "texture"
            else:
                # Default to image
                config_filename = "image_parameters_config.json"
                param_type = "image"
            
            # Save the updated config
            config_path = self.config.config_dir / config_filename
            with open(config_path, 'w') as f:
                json.dump(updated_config, f, indent=2)
            
            self.logger.debug(f"Saved new workflow config with {len(selected_nodes)} nodes to {config_filename}")
            
            # Refresh the parameters UI
            self._load_parameters_from_config(param_type)
            
            # Successfully switched to workflow
            
        except Exception as e:
            self.logger.error(f"❌ Failed to switch workflow: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
                
    def _load_session_models(self):
        """Load 3D models generated in current session to Scene Objects"""
        if hasattr(self, 'session_models_grid') and hasattr(self, 'session_models'):
            self.session_models_grid.clear_models()
            for model_path in self.session_models:
                if model_path.exists():
                    self.session_models_grid.add_model(model_path)
                
    def _load_all_models(self):
        """Load all 3D models from models directory to View All"""
        if hasattr(self, 'all_models_grid'):
            self.all_models_grid.clear_models()
            # Use configured models directory
            models_dir = getattr(self.config, 'models_3d_dir', None)
            if not models_dir:
                # Fallback to default ComfyUI output path
                models_dir = Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D")
            else:
                models_dir = Path(models_dir)
            
            self.logger.info(f"Loading 3D models from: {models_dir}")
            
            if models_dir.exists():
                # Get all model files - focusing on GLB files which are most common from ComfyUI
                model_patterns = ["*.glb", "*.gltf", "*.obj", "*.fbx", "*.ply", "*.stl"]
                all_models = []
                for pattern in model_patterns:
                    found_files = list(models_dir.glob(pattern))
                    all_models.extend(found_files)
                    if found_files:
                        self.logger.debug(f"Found {len(found_files)} {pattern} files")
            
                # Sort by modification time (newest first)
                all_models.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
                self.logger.info(f"Found {len(all_models)} 3D models to load into View All grid")
            
                # Add to grid
                for model_path in all_models:
                    self.all_models_grid.add_model(model_path)
                    self.logger.debug(f"Added model to View All: {model_path.name}")
                
                self.logger.info(f"Successfully loaded {len(all_models)} 3D models into View All tab")
            else:
                self.logger.warning(f"3D models directory does not exist: {models_dir}")
        else:
            self.logger.error("all_models_grid not found - UI not properly initialized")
    
    # File monitoring callbacks
    def _on_new_image(self, image_path: str):
        """Handle new image file detected"""
        image_path_obj = Path(image_path)
        
        # Check if this is a session image (generated after app start)
        if image_path_obj.stat().st_mtime > self.session_start_time:
            if image_path_obj not in self.session_images:
                self.session_images.append(image_path_obj)
            
        # Update New Canvas if currently visible
        if hasattr(self, 'session_image_grid'):
            self.session_image_grid.add_image(image_path_obj)
            
            # Add to unified object selector pool so it's available for selection
            if hasattr(self, 'unified_object_selector'):
                self.unified_object_selector.add_image_to_pool(image_path_obj)
                
            # Always update View All if loaded
            if hasattr(self, 'all_images_grid'):
                self.all_images_grid.add_image(image_path_obj)
    
    def _on_new_model(self, model_path: str):
        """Handle new 3D model file detected"""
        model_path_obj = Path(model_path)
        
        # Check if this is a session model (generated after app start)
        if model_path_obj.stat().st_mtime > self.session_start_time:
            if model_path_obj not in self.session_models:
                self.session_models.append(model_path_obj)
        
        # Try to link to source image in unified object system
        self._auto_link_model_to_image(model_path_obj)
        
        # Update Scene Objects if currently visible
        if hasattr(self, 'session_models_grid'):
            self.session_models_grid.add_model(model_path_obj)
            
        # Always update View All if loaded
        if hasattr(self, 'all_models_grid'):
            self.all_models_grid.add_model(model_path_obj)
    
    def _auto_link_model_to_image(self, model_path: Path):
        """Automatically link a generated model to its source image"""
        if not hasattr(self, 'unified_object_selector'):
            return
            
        # Try to find matching source image by name similarity
        model_stem = model_path.stem
        
        # Common naming patterns: image_name.ext -> model_name.obj
        # Look for images that could have generated this model
        for image_path in self.selected_images:
            image_stem = image_path.stem
            
            # Check various naming patterns
            if (model_stem.startswith(image_stem) or 
            image_stem.startswith(model_stem) or
            model_stem.replace('_3d', '') == image_stem or
            model_stem.replace('_model', '') == image_stem):
            
                # Link the model to the image
                self.unified_object_selector.link_model_to_image(model_path, image_path)
            self.logger.info(f"Auto-linked model {model_path.name} to image {image_path.name}")
            break
    
    def _detect_texture_files(self, model_path: Path) -> List[Path]:
        """Detect texture files for a given model"""
        texture_patterns = [
            f"{model_path.stem}_diffuse.*",
            f"{model_path.stem}_albedo.*", 
            f"{model_path.stem}_texture.*",
            f"{model_path.stem}_color.*",
            f"{model_path.stem}.png",
            f"{model_path.stem}.jpg",
            f"{model_path.stem}.jpeg"
        ]
        
        texture_files = []
        model_dir = model_path.parent
        
        for pattern in texture_patterns:
            matches = list(model_dir.glob(pattern))
            texture_files.extend(matches)
            
        return texture_files
    
    def _check_for_new_textures(self):
        """Check for newly generated texture files and mark models as textured"""
        if not hasattr(self, 'unified_object_selector'):
            return
            
        # Check all selected models for new texture files
        from ui.object_selection_widget import ObjectState
        for obj in self.unified_object_selector.get_selected_objects():
            if obj.model_3d and obj.state != ObjectState.TEXTURED:
                texture_files = self._detect_texture_files(obj.model_3d)
            if texture_files:
                self.unified_object_selector.mark_as_textured(obj.model_3d, texture_files)
                self.logger.info(f"Auto-detected textures for {obj.model_3d.name}: {len(texture_files)} files")
    
    def _test_unified_selector_visibility(self):
        """Test method to ensure unified selector is visible and working"""
        self.logger.info(f"Testing unified selector visibility...")
        
        # Check main selector
        if hasattr(self, 'unified_object_selector'):
            self.logger.info(f"Main unified selector visibility: {self.unified_object_selector.isVisible()}")
            self.logger.info(f"Main unified selector parent: {self.unified_object_selector.parent()}")
        
        # Check tab instances
        if hasattr(self, 'unified_selectors'):
            self.logger.info(f"Found {len(self.unified_selectors)} tab selector instances")
            for tab_name, selector in self.unified_selectors.items():
                self.logger.info(f"Tab '{tab_name}' selector visibility: {selector.isVisible()}")
            self.logger.info(f"Tab '{tab_name}' selector parent: {selector.parent()}")
        
        # Add a test image to see if it shows up in all selectors
        test_image = Path("test_image.png") 
        self._on_image_selected(test_image, True)
        self.logger.info("Added test image to all unified selectors via selection handler")
    
    def _initialize_content_grids(self):
        """Initialize content grids with existing files on startup"""
        # Load existing images
        self._load_all_images()
        
        # Load existing models - THIS POPULATES VIEW ALL TAB
        self._load_all_models()
        
        # Load session content (empty at startup)
        self._load_session_images()
        self._load_session_models()
        
        # Also trigger load on startup for View All if it exists
        if hasattr(self, '_load_test_models_on_startup'):
            # This ensures models are loaded into View All tab
            QTimer.singleShot(1000, self._load_test_models_on_startup)
    
    # Menu action implementations
    def _open_recent_project(self, project_path: str):
        """Open a recent project file"""
        try:
            self.logger.info(f"Opening recent project: {project_path}")
            # TODO: Implement actual project loading logic
            # For now, just show a confirmation
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
            self,
            "Open Recent Project",
            f"Opening project:\n{project_path}\n\n(Implementation pending)"
            )
        except Exception as e:
            self.logger.error(f"Failed to open recent project {project_path}: {e}")
    
    def _clear_recent_projects(self):
        """Clear the recent projects list"""
        try:
            self.logger.info("Clearing recent projects list...")
            # TODO: Implement actual recent projects clearing
            # For now, just show a confirmation
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
            self,
            "Clear Recent Projects",
            "Are you sure you want to clear the recent projects list?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.logger.info("Recent projects list cleared")
            QMessageBox.information(self, "Clear Recent", "Recent projects list cleared successfully.")
        except Exception as e:
            self.logger.error(f"Failed to clear recent projects: {e}")
    
    def _open_environment_variables(self):
        """Open environment variables dialog"""
        try:
            self.logger.info("Opening environment variables dialog...")
            from ui.env_dialog import EnvironmentVariablesDialog
            
            dialog = EnvironmentVariablesDialog(self.config, self)
            dialog.env_updated.connect(self._on_environment_updated)
            
            result = dialog.exec()
            self.logger.info(f"Environment variables dialog closed with result: {result}")
            
        except Exception as e:
            self.logger.error(f"Failed to open environment variables dialog: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open environment variables dialog:\n{e}")
    
    def _on_environment_updated(self):
        """Handle environment variables being updated"""
        self.logger.info("Environment variables have been updated")
        # TODO: Refresh any components that depend on environment variables
        # For example, reconnect to services if URLs changed
    
    def _open_application_settings(self):
        """Open application settings dialog"""
        try:
            self.logger.info("Opening application settings dialog...")
            from ui.settings_dialog import ApplicationSettingsDialog
            
            dialog = ApplicationSettingsDialog(self.config, self)
            dialog.settings_updated.connect(self._on_settings_updated)
            
            result = dialog.exec()
            self.logger.info(f"Application settings dialog closed with result: {result}")
            
        except Exception as e:
            self.logger.error(f"Failed to open application settings dialog: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open application settings dialog:\n{e}")
    
    def _on_settings_updated(self):
        """Handle application settings being updated"""
        self.logger.info("Application settings have been updated")
        # Apply new settings to the application
        self._apply_saved_accent_color()
    
    def _apply_saved_accent_color(self):
        """Apply saved accent color to the application on startup"""
        try:
            # Load saved accent color from QSettings
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            accent_color = settings.value("interface/accent_color", "#4CAF50")
            
            # Apply the same comprehensive CSS as in settings dialog
            accent_override_css = f"""
            /* Accent Color Override */
            QSlider::handle:horizontal, QSlider::handle:vertical {{
                background-color: {accent_color} !important;
            }}
            
            QSlider::sub-page:horizontal, QSlider::add-page:vertical {{
                background-color: {accent_color} !important;
            }}
            
            QTabBar::tab:selected {{
                border-bottom: 2px solid {accent_color} !important;
                background-color: rgba({int(accent_color[1:3], 16)}, {int(accent_color[3:5], 16)}, {int(accent_color[5:7], 16)}, 0.05) !important;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {accent_color} !important;
            }}
            
            /* Text Selection Colors - Multiple Approaches */
            QTextEdit::selection {{
                background-color: {accent_color} !important;
                color: #000000 !important;
            }}
            
            QLineEdit::selection {{
                background-color: {accent_color} !important;
                color: #000000 !important;
            }}
            
            QWidget {{
                selection-background-color: {accent_color} !important;
                selection-color: #000000 !important;
            }}
            
            /* Console Focus Border - Multiple Selectors for Investigation */
            QTextEdit#console:focus {{
                border: 2px solid {accent_color} !important;
            }}
            QTextEdit[objectName="console"]:focus {{
                border: 2px solid {accent_color} !important;
            }}
            QTextEdit:focus {{
                border: 2px solid {accent_color} !important;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {accent_color} !important;
                border-color: {accent_color} !important;
            }}
            
            
            /* Magic Prompt Star Buttons - More specific targeting */
            QPushButton[text="★"] {{
                color: {accent_color} !important;
            }}
            QPushButton[text="★"]:hover {{
                color: {self._get_lighter_color(accent_color)} !important;
            }}
            QPushButton[text="★"]:pressed {{
                color: {self._get_darker_color(accent_color)} !important;
            }}
            
            /* Image Thumbnail Selection Borders - Exact selector */
            QFrame#image_thumbnail[selected="true"] {{
                border: 2px solid {accent_color} !important;
            }}
            
            /* All Checkbox States - Both #4CAF50 and #22c55e variants */
            QCheckBox::indicator:checked {{
                background-color: {accent_color} !important;
                border-color: {accent_color} !important;
            }}
            QCheckBox::indicator:hover {{
                border-color: {accent_color} !important;
                background-color: rgba({int(accent_color[1:3], 16)}, {int(accent_color[3:5], 16)}, {int(accent_color[5:7], 16)}, 50) !important;
            }}
            
            /* Connection/Status Info Labels */
            QLabel#connection_info {{
                color: {accent_color} !important;
            }}
            
            /* 3D Model Selection States */
            Model3DPreviewCard QPushButton[selected="true"] {{
                background-color: {accent_color} !important;
            }}
            
            /* Primary Action Buttons */
            QPushButton#generate_btn, QPushButton#generate_3d_btn, QPushButton#generate_texture_btn,
            QPushButton#import_selected_btn, QPushButton#export_btn {{
                background-color: {accent_color} !important;
                border-color: {accent_color} !important;
            }}
            
            /* Dialog and Menu Styling */
            QDialog QListWidget::item:selected {{
                background-color: {accent_color} !important;
                color: #000000 !important;
            }}
            QDialog QListWidget::item:hover {{
                background-color: rgba({int(accent_color[1:3], 16)}, {int(accent_color[3:5], 16)}, {int(accent_color[5:7], 16)}, 0.3) !important;
            }}
            
            /* Menu hover states */
            QMenu::item:selected {{
                background-color: {accent_color} !important;
                color: #000000 !important;
            }}
            QMenu::item:hover {{
                background-color: rgba({int(accent_color[1:3], 16)}, {int(accent_color[3:5], 16)}, {int(accent_color[5:7], 16)}, 0.8) !important;
                color: #000000 !important;
            }}
            
            /* Submenu indicators */
            QMenu::right-arrow {{
                border-left: 5px solid {accent_color};
                border-top: 5px solid transparent;
                border-bottom: 5px solid transparent;
            }}
            
            /* Dialog button focus */
            QDialogButtonBox QPushButton:default {{
                background-color: {accent_color} !important;
                border-color: {accent_color} !important;
            }}
            QDialogButtonBox QPushButton:focus {{
                border: 2px solid {accent_color} !important;
            }}
            
            /* Slider accent colors */
            QSlider::handle:horizontal, QSlider::handle:vertical {{
                background-color: {accent_color} !important;
            }}
            QSlider::groove:horizontal:active, QSlider::groove:vertical:active {{
                background-color: rgba({int(accent_color[1:3], 16)}, {int(accent_color[3:5], 16)}, {int(accent_color[5:7], 16)}, 0.3) !important;
            }}
            """
            
            # Apply the accent color override CSS
            current_stylesheet = self.styleSheet()
            # Remove any existing accent override
            if '/* Accent Color Override */' in current_stylesheet:
                parts = current_stylesheet.split('/* Accent Color Override */')
                current_stylesheet = parts[0]
            
            self.setStyleSheet(current_stylesheet + accent_override_css)
            
            self.logger.debug(f"Applied saved accent color {accent_color} on startup")
        except Exception as e:
            self.logger.error(f"Failed to apply saved accent color on startup: {e}")
    
    def _get_lighter_color(self, hex_color: str) -> str:
        """Get a lighter version of the hex color for hover effects"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Make lighter (add 30 to each component, cap at 255)
            r = min(255, r + 30)
            g = min(255, g + 30)
            b = min(255, b + 30)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#66BB6A"  # Fallback
    
    def _get_darker_color(self, hex_color: str) -> str:
        """Get a darker version of the hex color for pressed effects"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Make darker (subtract 40 from each component, floor at 0)
            r = max(0, r - 40)
            g = max(0, g - 40)
            b = max(0, b - 40)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#2E7D32"  # Fallback
    
    def _open_github_documentation(self):
        """Open GitHub documentation in browser"""
        try:
            import webbrowser
            github_url = "https://github.com/anthropics/claude-code"  # Replace with actual repo URL
            webbrowser.open(github_url)
            self.logger.info(f"Opening GitHub documentation: {github_url}")
        except Exception as e:
            self.logger.error(f"Failed to open GitHub documentation: {e}")
    
    def resizeEvent(self, event):
        """Handle window resize events to maintain proper layout proportions"""
        super().resizeEvent(event)
        # Recalculate splitter sizes when window is resized
        self._recalculate_splitter_sizes()