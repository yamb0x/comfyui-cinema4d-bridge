"""
UI Controller

Extracted UI management logic from monolithic application.
Handles all UI creation, theming, and layout management with clear separation
from business logic.

Part of Phase 2 architectural decomposition - implements the multi-mind analysis
recommendation for breaking down the 4,483-line monolithic class.
"""

from typing import Dict, Any, Optional, List, Tuple, Callable
from pathlib import Path
from ..utils.advanced_logging import get_logger

logger = get_logger("ui")

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QLabel, QPushButton, QFrame, QSplitter, QScrollArea,
    QComboBox, QCheckBox, QSpinBox, QSlider, QTextEdit, QLineEdit,
    QGroupBox, QProgressBar, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QPixmap, QAction

from ..utils.error_handling import handle_errors, error_context
from ..core.unified_config_manager import UnifiedConfigurationManager


class UIState(QObject):
    """UI state management with signals for communication"""
    
    # UI state change signals
    tab_changed = Signal(int)
    workflow_changed = Signal(str)
    theme_changed = Signal(str)
    selection_changed = Signal(list)
    
    def __init__(self):
        super().__init__()
        self._current_tab = 0
        self._current_workflow = ""
        self._current_theme = "dark"
        self._selected_objects = []
    
    @property
    def current_tab(self) -> int:
        return self._current_tab
    
    @current_tab.setter
    def current_tab(self, value: int):
        if self._current_tab != value:
            self._current_tab = value
            self.tab_changed.emit(value)
    
    @property
    def current_workflow(self) -> str:
        return self._current_workflow
    
    @current_workflow.setter
    def current_workflow(self, value: str):
        if self._current_workflow != value:
            self._current_workflow = value
            self.workflow_changed.emit(value)
    
    @property
    def current_theme(self) -> str:
        return self._current_theme
    
    @current_theme.setter
    def current_theme(self, value: str):
        if self._current_theme != value:
            self._current_theme = value
            self.theme_changed.emit(value)
    
    @property
    def selected_objects(self) -> List[str]:
        return self._selected_objects.copy()
    
    @selected_objects.setter
    def selected_objects(self, value: List[str]):
        if self._selected_objects != value:
            self._selected_objects = value.copy()
            self.selection_changed.emit(value)


class ThemeManager:
    """Manages application theming and styling"""
    
    def __init__(self, config_manager: UnifiedConfigurationManager):
        self.config = config_manager
        self._current_theme = config_manager.get_setting("ui.theme", "dark")
    
    def get_theme_stylesheet(self, theme_name: str = None) -> str:
        """Get complete stylesheet for theme"""
        if theme_name is None:
            theme_name = self._current_theme
        
        if theme_name == "dark":
            return self._get_dark_theme_stylesheet()
        elif theme_name == "light":
            return self._get_light_theme_stylesheet()
        else:
            return self._get_dark_theme_stylesheet()  # Default fallback
    
    def _get_dark_theme_stylesheet(self) -> str:
        """Dark theme stylesheet"""
        return """
        /* Main Application Dark Theme */
        QMainWindow {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        
        /* Tab Widget */
        QTabWidget::pane {
            border: 1px solid #3d3d3d;
            background-color: #2d2d2d;
        }
        
        QTabWidget::tab-bar {
            alignment: center;
        }
        
        QTabBar::tab {
            background-color: #3d3d3d;
            color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #4CAF50;
            color: #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #505050;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #66BB6A;
        }
        
        QPushButton:pressed {
            background-color: #2E7D32;
        }
        
        QPushButton:disabled {
            background-color: #5d5d5d;
            color: #9d9d9d;
        }
        
        QPushButton#secondary_btn {
            background-color: #757575;
        }
        
        QPushButton#secondary_btn:hover {
            background-color: #9E9E9E;
        }
        
        /* Input Controls */
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3d3d3d;
            color: #e0e0e0;
            border: 1px solid #5d5d5d;
            padding: 4px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 1px solid #4CAF50;
        }
        
        QComboBox::drop-down {
            border: none;
            background-color: #5d5d5d;
        }
        
        QComboBox::down-arrow {
            border: none;
            color: #e0e0e0;
        }
        
        QComboBox QAbstractItemView {
            background-color: #3d3d3d;
            color: #e0e0e0;
            selection-background-color: #4CAF50;
        }
        
        /* Sliders and Spin Boxes */
        QSlider::groove:horizontal {
            border: 1px solid #5d5d5d;
            height: 8px;
            background-color: #3d3d3d;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal {
            background-color: #4CAF50;
            border: 1px solid #2E7D32;
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }
        
        QSpinBox {
            background-color: #3d3d3d;
            color: #e0e0e0;
            border: 1px solid #5d5d5d;
            padding: 4px;
            border-radius: 3px;
        }
        
        /* Labels and Text */
        QLabel {
            color: #e0e0e0;
        }
        
        QLabel#title {
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
        }
        
        QLabel#subtitle {
            font-size: 14px;
            font-weight: bold;
            color: #e0e0e0;
        }
        
        QLabel#section_title {
            font-size: 16px;
            font-weight: bold;
            color: #4CAF50;
            padding: 8px 0;
        }
        
        /* Frames and Containers */
        QFrame {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
        }
        
        QGroupBox {
            font-weight: bold;
            color: #4CAF50;
            border: 2px solid #3d3d3d;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        /* Scroll Areas */
        QScrollArea {
            border: none;
            background-color: #2d2d2d;
        }
        
        QScrollBar:vertical {
            background-color: #3d3d3d;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #5d5d5d;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #4CAF50;
        }
        
        /* Progress Bar */
        QProgressBar {
            border: 1px solid #3d3d3d;
            border-radius: 5px;
            text-align: center;
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 5px;
        }
        """
    
    def _get_light_theme_stylesheet(self) -> str:
        """Light theme stylesheet"""
        return """
        /* Main Application Light Theme */
        QMainWindow {
            background-color: #ffffff;
            color: #212121;
        }
        
        /* Tab Widget */
        QTabWidget::pane {
            border: 1px solid #e0e0e0;
            background-color: #fafafa;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            color: #212121;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #4CAF50;
            color: #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #f5f5f5;
        }
        
        /* Continue with light theme variations... */
        """
    
    def apply_theme(self, widget: QWidget, theme_name: str = None):
        """Apply theme to widget and all children"""
        stylesheet = self.get_theme_stylesheet(theme_name)
        widget.setStyleSheet(stylesheet)
        self._current_theme = theme_name or self._current_theme


class LayoutManager:
    """Manages UI layout creation and organization"""
    
    def __init__(self):
        self.layouts = {}
        self.widgets = {}
    
    def create_main_layout(self) -> QHBoxLayout:
        """Create main application layout"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        return layout
    
    def create_tab_layout(self, tab_name: str) -> QVBoxLayout:
        """Create layout for specific tab"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.layouts[f"{tab_name}_layout"] = layout
        return layout
    
    def create_splitter_layout(self, orientation: Qt.Orientation = Qt.Horizontal) -> QSplitter:
        """Create splitter layout"""
        splitter = QSplitter(orientation)
        return splitter
    
    def create_control_panel_layout(self) -> QVBoxLayout:
        """Create control panel layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        return layout
    
    def create_grid_layout(self, rows: int = 0, cols: int = 0) -> QGridLayout:
        """Create grid layout"""
        layout = QGridLayout()
        if rows > 0 and cols > 0:
            layout.setRowMinimumHeight(rows - 1, 50)
            layout.setColumnMinimumWidth(cols - 1, 100)
        return layout


class UIController(QObject):
    """
    Centralized UI management controller
    
    Extracted from monolithic application to handle all UI creation,
    theming, and layout management with clear separation from business logic.
    """
    
    # Signals for communication with other components
    action_requested = Signal(str, dict)  # action_name, parameters
    workflow_triggered = Signal(str, dict)  # workflow_type, parameters
    settings_changed = Signal(str, object)  # setting_name, value
    
    def __init__(self, config_manager: UnifiedConfigurationManager):
        super().__init__()
        self.config = config_manager
        self.ui_state = UIState()
        self.theme_manager = ThemeManager(config_manager)
        self.layout_manager = LayoutManager()
        
        # UI component registry
        self.widgets = {}
        self.layouts = {}
        self.actions = {}
        
        # Connect internal signals
        self._connect_ui_signals()
    
    def _connect_ui_signals(self):
        """Connect internal UI signals"""
        self.ui_state.tab_changed.connect(self._on_tab_changed)
        self.ui_state.workflow_changed.connect(self._on_workflow_changed)
        self.ui_state.theme_changed.connect(self._on_theme_changed)
    
    @handle_errors("ui_controller", "create_main_window")
    def create_main_window(self) -> QMainWindow:
        """Create main application window"""
        with error_context("ui_controller", "create_main_window"):
            window = QMainWindow()
            window.setWindowTitle("ComfyUI to Cinema4D Bridge")
            
            # Set window properties from config
            window_size = self.config.get_setting("ui.window_size", [1400, 900])
            window.resize(window_size[0], window_size[1])
            
            # Create central widget
            central_widget = QWidget()
            window.setCentralWidget(central_widget)
            
            # Apply theme
            self.theme_manager.apply_theme(window)
            
            # Store reference
            self.widgets["main_window"] = window
            
            logger.debug("Main window created successfully")
            return window
    
    @handle_errors("ui_controller", "create_main_interface")
    def create_main_interface(self, parent_window: QMainWindow) -> QWidget:
        """Create main interface layout"""
        with error_context("ui_controller", "create_main_interface", parent=str(parent_window)):
            # Create main splitter
            main_splitter = self.layout_manager.create_splitter_layout(Qt.Horizontal)
            
            # Create left panel (controls)
            left_panel = self._create_left_control_panel()
            main_splitter.addWidget(left_panel)
            
            # Create right panel (tabs)
            right_panel = self._create_right_tab_panel()
            main_splitter.addWidget(right_panel)
            
            # Set splitter ratios
            main_splitter.setSizes([400, 1000])  # 400px left, 1000px right
            
            # Store reference
            self.widgets["main_interface"] = main_splitter
            
            return main_splitter
    
    def _create_left_control_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QFrame()
        panel.setObjectName("control_panel")
        layout = self.layout_manager.create_control_panel_layout()
        
        # Title
        title = QLabel("Control Panel")
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Workflow selector
        workflow_group = self._create_workflow_selector()
        layout.addWidget(workflow_group)
        
        # Object manager
        object_group = self._create_object_manager()
        layout.addWidget(object_group)
        
        # Connection status
        status_group = self._create_connection_status()
        layout.addWidget(status_group)
        
        # Add stretch
        layout.addStretch()
        
        panel.setLayout(layout)
        self.widgets["left_panel"] = panel
        
        return panel
    
    def _create_workflow_selector(self) -> QGroupBox:
        """Create workflow selector group"""
        group = QGroupBox("Workflow Selection")
        layout = QVBoxLayout()
        
        # Workflow combo box
        workflow_combo = QComboBox()
        workflow_combo.setObjectName("workflow_combo")
        workflow_combo.currentTextChanged.connect(
            lambda text: setattr(self.ui_state, 'current_workflow', text)
        )
        layout.addWidget(QLabel("Current Workflow:"))
        layout.addWidget(workflow_combo)
        
        # Generate button
        generate_btn = QPushButton("Generate")
        generate_btn.setObjectName("generate_btn")
        generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(generate_btn)
        
        group.setLayout(layout)
        self.widgets["workflow_group"] = group
        self.widgets["workflow_combo"] = workflow_combo
        self.widgets["generate_btn"] = generate_btn
        
        return group
    
    def _create_object_manager(self) -> QGroupBox:
        """Create object manager group"""
        group = QGroupBox("Object Manager")
        layout = QVBoxLayout()
        
        # Object list (placeholder)
        object_list = QTextEdit()
        object_list.setMaximumHeight(200)
        object_list.setPlaceholderText("Selected objects will appear here...")
        layout.addWidget(object_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.clicked.connect(self._on_clear_selection)
        button_layout.addWidget(clear_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondary_btn")
        refresh_btn.clicked.connect(self._on_refresh_objects)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        self.widgets["object_group"] = group
        self.widgets["object_list"] = object_list
        
        return group
    
    def _create_connection_status(self) -> QGroupBox:
        """Create connection status group"""
        group = QGroupBox("Connection Status")
        layout = QVBoxLayout()
        
        # ComfyUI status
        comfyui_layout = QHBoxLayout()
        comfyui_layout.addWidget(QLabel("ComfyUI:"))
        comfyui_status = QLabel("Disconnected")
        comfyui_status.setObjectName("status_disconnected")
        comfyui_layout.addWidget(comfyui_status)
        comfyui_layout.addStretch()
        layout.addLayout(comfyui_layout)
        
        # Cinema4D status
        c4d_layout = QHBoxLayout()
        c4d_layout.addWidget(QLabel("Cinema4D:"))
        c4d_status = QLabel("Disconnected")
        c4d_status.setObjectName("status_disconnected")
        c4d_layout.addWidget(c4d_status)
        c4d_layout.addStretch()
        layout.addLayout(c4d_layout)
        
        # Refresh button
        refresh_status_btn = QPushButton("Refresh Status")
        refresh_status_btn.setObjectName("secondary_btn")
        refresh_status_btn.clicked.connect(self._on_refresh_status)
        layout.addWidget(refresh_status_btn)
        
        group.setLayout(layout)
        self.widgets["status_group"] = group
        self.widgets["comfyui_status"] = comfyui_status
        self.widgets["c4d_status"] = c4d_status
        
        return group
    
    def _create_right_tab_panel(self) -> QWidget:
        """Create right tab panel"""
        tab_widget = QTabWidget()
        tab_widget.setObjectName("main_tabs")
        
        # Create tabs
        tabs = {
            "Image Generation": self._create_image_generation_tab(),
            "3D Model Generation": self._create_3d_generation_tab(),
            "Texture Generation": self._create_texture_generation_tab(),
            "Cinema4D Intelligence": self._create_cinema4d_tab()
        }
        
        for tab_name, tab_widget_content in tabs.items():
            tab_widget.addTab(tab_widget_content, tab_name)
        
        # Connect tab change signal
        tab_widget.currentChanged.connect(
            lambda index: setattr(self.ui_state, 'current_tab', index)
        )
        
        self.widgets["tab_widget"] = tab_widget
        
        return tab_widget
    
    def _create_image_generation_tab(self) -> QWidget:
        """Create image generation tab"""
        widget = QWidget()
        layout = self.layout_manager.create_tab_layout("image_generation")
        
        # Tab title
        title = QLabel("AI Image Generation")
        title.setObjectName("section_title")
        layout.addWidget(title)
        
        # Content area
        content_area = QScrollArea()
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Placeholder content
        info_label = QLabel("Image generation controls will be displayed here.")
        content_layout.addWidget(info_label)
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        content_area.setWidget(content_widget)
        content_area.setWidgetResizable(True)
        
        layout.addWidget(content_area)
        
        widget.setLayout(layout)
        self.widgets["image_tab"] = widget
        
        return widget
    
    def _create_3d_generation_tab(self) -> QWidget:
        """Create 3D generation tab"""
        widget = QWidget()
        layout = self.layout_manager.create_tab_layout("3d_generation")
        
        # Tab title
        title = QLabel("3D Model Generation")
        title.setObjectName("section_title")
        layout.addWidget(title)
        
        # Content area
        content_area = QScrollArea()
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Placeholder content
        info_label = QLabel("3D model generation controls will be displayed here.")
        content_layout.addWidget(info_label)
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        content_area.setWidget(content_widget)
        content_area.setWidgetResizable(True)
        
        layout.addWidget(content_area)
        
        widget.setLayout(layout)
        self.widgets["3d_tab"] = widget
        
        return widget
    
    def _create_texture_generation_tab(self) -> QWidget:
        """Create texture generation tab"""
        widget = QWidget()
        layout = self.layout_manager.create_tab_layout("texture_generation")
        
        # Tab title
        title = QLabel("Texture Generation")
        title.setObjectName("section_title")
        layout.addWidget(title)
        
        # Content area
        content_area = QScrollArea()
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Placeholder content
        info_label = QLabel("Texture generation controls will be displayed here.")
        content_layout.addWidget(info_label)
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        content_area.setWidget(content_widget)
        content_area.setWidgetResizable(True)
        
        layout.addWidget(content_area)
        
        widget.setLayout(layout)
        self.widgets["texture_tab"] = widget
        
        return widget
    
    def _create_cinema4d_tab(self) -> QWidget:
        """Create Cinema4D intelligence tab"""
        widget = QWidget()
        layout = self.layout_manager.create_tab_layout("cinema4d")
        
        # Tab title
        title = QLabel("Cinema4D Intelligence")
        title.setObjectName("section_title")
        layout.addWidget(title)
        
        # Content area
        content_area = QScrollArea()
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Placeholder content
        info_label = QLabel("Cinema4D intelligence controls will be displayed here.")
        content_layout.addWidget(info_label)
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        content_area.setWidget(content_widget)
        content_area.setWidgetResizable(True)
        
        layout.addWidget(content_area)
        
        widget.setLayout(layout)
        self.widgets["cinema4d_tab"] = widget
        
        return widget
    
    # Event Handlers
    
    def _on_tab_changed(self, index: int):
        """Handle tab change"""
        logger.debug(f"Tab changed to index: {index}")
        self.action_requested.emit("tab_changed", {"index": index})
    
    def _on_workflow_changed(self, workflow: str):
        """Handle workflow change"""
        logger.debug(f"Workflow changed to: {workflow}")
        self.action_requested.emit("workflow_changed", {"workflow": workflow})
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change"""
        logger.debug(f"Theme changed to: {theme}")
        if "main_window" in self.widgets:
            self.theme_manager.apply_theme(self.widgets["main_window"], theme)
    
    def _on_generate_clicked(self):
        """Handle generate button click"""
        workflow = self.ui_state.current_workflow
        tab_index = self.ui_state.current_tab
        
        logger.info(f"Generate requested: workflow={workflow}, tab={tab_index}")
        self.workflow_triggered.emit(workflow, {"tab_index": tab_index})
    
    def _on_clear_selection(self):
        """Handle clear selection"""
        self.ui_state.selected_objects = []
        self.action_requested.emit("clear_selection", {})
    
    def _on_refresh_objects(self):
        """Handle refresh objects"""
        self.action_requested.emit("refresh_objects", {})
    
    def _on_refresh_status(self):
        """Handle refresh status"""
        self.action_requested.emit("refresh_status", {})
    
    # Public Interface Methods
    
    def update_workflow_list(self, workflows: List[str]):
        """Update workflow combo box"""
        if "workflow_combo" in self.widgets:
            combo = self.widgets["workflow_combo"]
            combo.clear()
            combo.addItems(workflows)
    
    def update_connection_status(self, service: str, connected: bool):
        """Update connection status display"""
        status_widget_name = f"{service.lower()}_status"
        if status_widget_name in self.widgets:
            status_widget = self.widgets[status_widget_name]
            if connected:
                status_widget.setText("Connected")
                status_widget.setObjectName("status_connected")
            else:
                status_widget.setText("Disconnected")
                status_widget.setObjectName("status_disconnected")
            # Reapply style
            status_widget.style().unpolish(status_widget)
            status_widget.style().polish(status_widget)
    
    def update_object_list(self, objects: List[str]):
        """Update object list display"""
        if "object_list" in self.widgets:
            object_list = self.widgets["object_list"]
            object_list.clear()
            object_list.setText("\n".join(objects) if objects else "No objects selected")
    
    def show_progress(self, message: str, progress: int = -1):
        """Show progress indication"""
        # TODO: Implement progress dialog or status bar
        logger.info(f"Progress: {message} ({progress}%)" if progress >= 0 else f"Progress: {message}")
    
    def show_error(self, title: str, message: str):
        """Show error message"""
        # TODO: Implement error dialog
        logger.error(f"UI Error - {title}: {message}")
    
    def get_widget(self, widget_name: str) -> Optional[QWidget]:
        """Get widget by name"""
        return self.widgets.get(widget_name)
    
    def get_ui_state(self) -> UIState:
        """Get current UI state"""
        return self.ui_state