"""
Application Settings Dialog
"""

import os
import json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QLineEdit, QGroupBox, 
    QDialogButtonBox, QTabWidget, QWidget, QCheckBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QSlider,
    QMessageBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont, QColor
from loguru import logger



class ApplicationSettingsDialog(QDialog):
    """Dialog for configuring application settings"""
    
    settings_updated = Signal()  # Emitted when settings are saved
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Application Settings")
        self.setModal(True)
        self.resize(800, 600)
        
        
        # Apply terminal theme styling
        self._apply_terminal_theme()
        
        self._setup_ui()
        self._load_current_values()
        
    def _apply_terminal_theme(self):
        """Apply terminal theme styling to the dialog"""
        from src.ui.terminal_theme_complete import get_complete_terminal_theme
        self.setStyleSheet(get_complete_terminal_theme())
        
    def _setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Configure application preferences and behavior")
        header.setStyleSheet("font-size: 14px; margin-bottom: 10px; color: #fafafa;")
        layout.addWidget(header)
        
        # Create tabs for different settings sections
        tabs = QTabWidget()
        
        # General Settings tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Interface Settings tab
        interface_tab = self._create_interface_tab()
        tabs.addTab(interface_tab, "Interface")
        
        # Performance Settings tab
        performance_tab = self._create_performance_tab()
        tabs.addTab(performance_tab, "Performance")
        
        # Logging Settings tab
        logging_tab = self._create_logging_tab()
        tabs.addTab(logging_tab, "Logging")
        
        # Advanced Settings tab
        advanced_tab = self._create_advanced_tab()
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._save_settings)
        
        # Reset to defaults button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_box.addButton(reset_btn, QDialogButtonBox.ActionRole)
        
        layout.addWidget(button_box)
        
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Application behavior
        behavior_group = QGroupBox("Application Behavior")
        behavior_layout = QFormLayout(behavior_group)
        
        # Auto-save projects
        self.auto_save_check = QCheckBox("Enable auto-save for projects")
        self.auto_save_check.stateChanged.connect(self._on_auto_save_changed)
        behavior_layout.addRow("Auto-save:", self.auto_save_check)
        
        # Auto-save interval
        self.auto_save_interval_spin = QSpinBox()
        self.auto_save_interval_spin.setRange(1, 60)
        self.auto_save_interval_spin.setValue(5)
        self.auto_save_interval_spin.setSuffix(" minutes")
        self.auto_save_interval_spin.valueChanged.connect(self._on_auto_save_interval_changed)
        behavior_layout.addRow("Auto-save interval:", self.auto_save_interval_spin)
        
        # Remember window position
        self.remember_window_check = QCheckBox("Remember window position and size")
        behavior_layout.addRow("Window state:", self.remember_window_check)
        
        # Recent files count
        self.recent_files_spin = QSpinBox()
        self.recent_files_spin.setRange(1, 20)
        self.recent_files_spin.setValue(10)
        behavior_layout.addRow("Recent files count:", self.recent_files_spin)
        
        layout.addWidget(behavior_group)
        
        # File handling
        file_group = QGroupBox("File Handling")
        file_layout = QFormLayout(file_group)
        
        # Default project location
        self.default_project_edit = QLineEdit()
        browse_project_btn = QPushButton("Browse...")
        browse_project_btn.clicked.connect(self._browse_default_project_location)
        project_layout = QHBoxLayout()
        project_layout.addWidget(self.default_project_edit)
        project_layout.addWidget(browse_project_btn)
        file_layout.addRow("Default project location:", project_layout)
        
        # File associations
        self.associate_files_check = QCheckBox("Associate .json files with this application")
        file_layout.addRow("File associations:", self.associate_files_check)
        
        layout.addWidget(file_group)
        
        return widget
        
    def _create_interface_tab(self) -> QWidget:
        """Create interface settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Appearance settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setSuffix(" px")
        self.font_size_spin.valueChanged.connect(self._on_font_size_changed)
        appearance_layout.addRow("Font size:", self.font_size_spin)
        
        # Accent color
        self.accent_color = "#4CAF50"  # Store the actual color
        self.accent_color_btn = QPushButton("Choose Color")
        self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color}; color: white; padding: 8px;")
        self.accent_color_btn.clicked.connect(self._choose_accent_color)
        appearance_layout.addRow("Accent color:", self.accent_color_btn)
        
        layout.addWidget(appearance_group)
        
        # Workflow Parameter Colors section
        colors_group = QGroupBox("Workflow Parameter Colors")
        colors_layout = QFormLayout(colors_group)
        
        # Color palette for workflow parameter outlines
        colors_info = QLabel("Choose colors for workflow parameter section outlines:")
        colors_info.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 8px;")
        colors_layout.addRow(colors_info)
        
        # Initialize default color palette
        self.workflow_colors = [
            "#4CAF50",  # Green - Primary sampling
            "#2196F3",  # Blue - Model loading  
            "#9C27B0",  # Purple - LoRA
            "#FF9800",  # Orange - VAE
            "#00BCD4"   # Cyan - Text encoding
        ]
        
        # Create color palette buttons
        self.color_buttons = []
        palette_layout = QHBoxLayout()
        
        for i, color in enumerate(self.workflow_colors):
            color_btn = QPushButton(f"Color {i+1}")
            color_btn.setStyleSheet(f"background-color: {color}; color: white; padding: 8px; min-width: 80px;")
            color_btn.clicked.connect(lambda checked, idx=i: self._choose_workflow_color(idx))
            self.color_buttons.append(color_btn)
            palette_layout.addWidget(color_btn)
        
        colors_layout.addRow("Color Palette:", palette_layout)
        
        # Reset colors button
        reset_colors_btn = QPushButton("Reset to Default Colors")
        reset_colors_btn.clicked.connect(self._reset_workflow_colors)
        colors_layout.addRow("", reset_colors_btn)
        
        layout.addWidget(colors_group)
        
        # Console settings
        console_group = QGroupBox("Console Settings")
        console_layout = QFormLayout(console_group)
        
        # Console auto-scroll
        self.console_autoscroll_check = QCheckBox("Enable console auto-scroll")
        self.console_autoscroll_check.stateChanged.connect(self._on_console_autoscroll_changed)
        console_layout.addRow("Auto-scroll:", self.console_autoscroll_check)
        
        # Console buffer size
        self.console_buffer_spin = QSpinBox()
        self.console_buffer_spin.setRange(100, 10000)
        self.console_buffer_spin.setValue(1000)
        self.console_buffer_spin.setSuffix(" lines")
        self.console_buffer_spin.valueChanged.connect(self._on_console_buffer_changed)
        console_layout.addRow("Buffer size:", self.console_buffer_spin)
        
        # Console timestamp format
        self.timestamp_combo = QComboBox()
        self.timestamp_combo.addItems(["HH:MM:SS", "HH:MM:SS.mmm", "DD/MM HH:MM:SS", "ISO 8601"])
        self.timestamp_combo.currentTextChanged.connect(self._on_timestamp_format_changed)
        console_layout.addRow("Timestamp format:", self.timestamp_combo)
        
        layout.addWidget(console_group)
        
        return widget
        
    def _create_performance_tab(self) -> QWidget:
        """Create performance settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Processing settings
        processing_group = QGroupBox("Processing Settings")
        processing_layout = QFormLayout(processing_group)
        
        # Max concurrent operations
        self.max_operations_spin = QSpinBox()
        self.max_operations_spin.setRange(1, 16)
        self.max_operations_spin.setValue(4)
        self.max_operations_spin.valueChanged.connect(self._on_max_operations_changed)
        processing_layout.addRow("Max concurrent operations:", self.max_operations_spin)
        
        # Memory limit
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(512, 32768)
        self.memory_limit_spin.setValue(8192)
        self.memory_limit_spin.setSuffix(" MB")
        self.memory_limit_spin.valueChanged.connect(self._on_memory_limit_changed)
        processing_layout.addRow("Memory limit:", self.memory_limit_spin)
        
        # GPU acceleration
        self.gpu_acceleration_check = QCheckBox("Enable GPU acceleration when available")
        self.gpu_acceleration_check.stateChanged.connect(self._on_gpu_acceleration_changed)
        processing_layout.addRow("GPU acceleration:", self.gpu_acceleration_check)
        
        layout.addWidget(processing_group)
        
        # Cache settings
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QFormLayout(cache_group)
        
        # Cache size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 10000)
        self.cache_size_spin.setValue(1000)
        self.cache_size_spin.setSuffix(" MB")
        self.cache_size_spin.valueChanged.connect(self._on_cache_size_changed)
        cache_layout.addRow("Cache size:", self.cache_size_spin)
        
        # Auto-clear cache
        self.auto_clear_cache_check = QCheckBox("Auto-clear cache on startup")
        self.auto_clear_cache_check.stateChanged.connect(self._on_auto_clear_cache_changed)
        cache_layout.addRow("Auto-clear:", self.auto_clear_cache_check)
        
        # Clear cache button
        clear_cache_btn = QPushButton("Clear Cache Now")
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addRow("", clear_cache_btn)
        
        layout.addWidget(cache_group)
        
        return widget
        
    def _create_logging_tab(self) -> QWidget:
        """Create logging settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Logging configuration group
        logging_group = QGroupBox("Logging Configuration")
        logging_layout = QFormLayout(logging_group)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        logging_layout.addRow("Log level:", self.log_level_combo)
        
        # Log to file
        self.log_to_file_check = QCheckBox("Save logs to file")
        self.log_to_file_check.stateChanged.connect(self._on_log_to_file_changed)
        logging_layout.addRow("File logging:", self.log_to_file_check)
        
        # Log file rotation
        self.log_rotation_check = QCheckBox("Enable log file rotation")
        self.log_rotation_check.stateChanged.connect(self._on_log_rotation_changed)
        logging_layout.addRow("Log rotation:", self.log_rotation_check)
        
        # Max log file size
        self.max_log_size_spin = QSpinBox()
        self.max_log_size_spin.setRange(1, 1000)
        self.max_log_size_spin.setValue(50)
        self.max_log_size_spin.setSuffix(" MB")
        self.max_log_size_spin.valueChanged.connect(self._on_max_log_size_changed)
        logging_layout.addRow("Max log file size:", self.max_log_size_spin)
        
        layout.addWidget(logging_group)
        
        # Debug mode with explanation
        debug_group = QGroupBox("Debug Mode")
        debug_layout = QFormLayout(debug_group)
        
        self.debug_mode_check = QCheckBox("Enable debug mode (COMFY_C4D_DEBUG)")
        self.debug_mode_check.setToolTip("When enabled, sets log level to DEBUG and enables verbose output.\nEquivalent to setting COMFY_C4D_DEBUG=true environment variable.")
        self.debug_mode_check.stateChanged.connect(self._on_debug_mode_changed)
        debug_layout.addRow(self.debug_mode_check)
        
        debug_info = QLabel("Note: Debug mode overrides the log level setting above.")
        debug_info.setStyleSheet("color: #888888; font-size: 11px;")
        debug_layout.addRow(debug_info)
        
        layout.addWidget(debug_group)
        
        return widget
        
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Network settings
        network_group = QGroupBox("Network Settings")
        network_layout = QFormLayout(network_group)
        
        # Connection timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        network_layout.addRow("Connection timeout:", self.timeout_spin)
        
        # Retry attempts
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setValue(3)
        network_layout.addRow("Retry attempts:", self.retry_spin)
        
        layout.addWidget(network_group)
        
        # ComfyUI settings
        comfyui_group = QGroupBox("ComfyUI Settings")
        comfyui_layout = QFormLayout(comfyui_group)
        
        # Texture wait time
        self.texture_wait_spin = QSpinBox()
        self.texture_wait_spin.setRange(5, 120)
        self.texture_wait_spin.setValue(20)  # Default value
        self.texture_wait_spin.setSuffix(" seconds")
        self.texture_wait_spin.setToolTip("Time to wait for ComfyUI to release texture files before copying")
        comfyui_layout.addRow("Texture file wait time:", self.texture_wait_spin)
        
        layout.addWidget(comfyui_group)
        
        # Privacy settings
        privacy_group = QGroupBox("Privacy Settings")
        privacy_layout = QFormLayout(privacy_group)
        
        # Telemetry
        self.telemetry_check = QCheckBox("Send anonymous usage statistics")
        self.telemetry_check.stateChanged.connect(self._on_telemetry_changed)
        privacy_layout.addRow("Telemetry:", self.telemetry_check)
        
        layout.addWidget(privacy_group)
        
        return widget
        
    def _choose_accent_color(self):
        """Choose accent color"""
        current_color = QColor(self.accent_color)
        color = QColorDialog.getColor(current_color, self, "Choose Accent Color")
        if color.isValid():
            self.accent_color = color.name()
            self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color}; color: white; padding: 8px;")
            self._apply_accent_color()
            
    def _clear_cache(self):
        """Clear application cache"""
        try:
            parent_app = self.parent()
            cache_cleared = False
            
            if parent_app:
                # Clear file monitor cache
                if hasattr(parent_app, 'file_monitor'):
                    file_monitor = parent_app.file_monitor
                    if hasattr(file_monitor, 'clear_cache'):
                        file_monitor.clear_cache()
                        cache_cleared = True
                        
                # Clear workflow manager cache
                if hasattr(parent_app, 'workflow_manager'):
                    workflow_manager = parent_app.workflow_manager
                    if hasattr(workflow_manager, 'clear_cache'):
                        workflow_manager.clear_cache()
                        cache_cleared = True
                        
                # Clear any temp directories
                temp_dirs = [
                    self.config.base_dir / "temp",
                    self.config.base_dir / "cache"
                ]
                
                for temp_dir in temp_dirs:
                    if temp_dir.exists():
                        import shutil
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        temp_dir.mkdir(exist_ok=True)
                        cache_cleared = True
            
            if cache_cleared:
                QMessageBox.information(self, "Clear Cache", "Cache cleared successfully!")
                logger.info("Application cache cleared")
            else:
                QMessageBox.information(self, "Clear Cache", "No cache to clear or cache clearing not supported.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear cache:\n{str(e)}")
            logger.error(f"Failed to clear cache: {e}")
        
    def _load_current_values(self):
        """Load current settings values"""
        from PySide6.QtCore import QSettings
        settings = QSettings("ComfyUI-Cinema4D", "Bridge")
        
        # General settings
        self.auto_save_check.setChecked(settings.value("general/auto_save", True, type=bool))
        self.auto_save_interval_spin.setValue(settings.value("general/auto_save_interval", 5, type=int))
        self.remember_window_check.setChecked(settings.value("general/remember_window", True, type=bool))
        self.recent_files_spin.setValue(settings.value("general/recent_files_count", 10, type=int))
        self.default_project_edit.setText(settings.value("general/default_project_location", str(self.config.base_dir / "projects")))
        self.associate_files_check.setChecked(settings.value("general/associate_files", False, type=bool))
        
        # Interface settings
        font_size = settings.value("interface/font_size", 12, type=int)
        self.font_size_spin.setValue(font_size)
        
        self.accent_color = settings.value("interface/accent_color", "#4CAF50")
        self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color}; color: white; padding: 8px;")
        
        # Load workflow colors (only if color_buttons exist)
        if hasattr(self, 'color_buttons') and self.color_buttons:
            saved_colors = settings.value("interface/workflow_colors", self.workflow_colors)
            if saved_colors:
                self.workflow_colors = saved_colors
                for i, color in enumerate(self.workflow_colors):
                    if i < len(self.color_buttons):
                        self.color_buttons[i].setStyleSheet(f"background-color: {color}; color: white; padding: 8px; min-width: 80px;")
        
        self.console_autoscroll_check.setChecked(settings.value("interface/console_autoscroll", True, type=bool))
        self.console_buffer_spin.setValue(settings.value("interface/console_buffer", 1000, type=int))
        self.timestamp_combo.setCurrentText(settings.value("interface/timestamp_format", "HH:MM:SS"))
        
        # Performance settings
        self.max_operations_spin.setValue(settings.value("performance/max_operations", 4, type=int))
        self.memory_limit_spin.setValue(settings.value("performance/memory_limit", 8192, type=int))
        self.gpu_acceleration_check.setChecked(settings.value("performance/gpu_acceleration", True, type=bool))
        self.cache_size_spin.setValue(settings.value("performance/cache_size", 1000, type=int))
        self.auto_clear_cache_check.setChecked(settings.value("performance/auto_clear_cache", False, type=bool))
        
        # Logging settings
        # Check for both old and new settings keys for compatibility
        log_level = settings.value("logging/log_level", settings.value("logging/level", "INFO"))
        self.log_level_combo.setCurrentText(log_level)
        self.log_to_file_check.setChecked(settings.value("logging/file_enabled", True, type=bool))
        self.log_rotation_check.setChecked(settings.value("logging/rotation_enabled", True, type=bool))
        self.max_log_size_spin.setValue(settings.value("logging/max_log_size", 50, type=int))
        
        # Check environment variable for debug mode as well
        import os
        env_debug = os.getenv('COMFY_C4D_DEBUG', '').lower() in ('true', '1', 'yes', 'on')
        saved_debug = settings.value("logging/debug_mode", False, type=bool)
        self.debug_mode_check.setChecked(env_debug or saved_debug)
        
        # Apply logging configuration on startup
        try:
            self._apply_log_level(log_level)
        except Exception as e:
            logger.error(f"Failed to apply logging configuration on startup: {e}")
        
        # Advanced settings
        self.timeout_spin.setValue(settings.value("advanced/timeout", 30, type=int))
        self.retry_spin.setValue(settings.value("advanced/retry_attempts", 3, type=int))
        self.telemetry_check.setChecked(settings.value("advanced/telemetry", False, type=bool))
        
        # ComfyUI settings
        self.texture_wait_spin.setValue(settings.value("comfyui/texture_wait_time", 20, type=int))
        
        # Setup auto-save timer before applying settings
        try:
            self._setup_auto_save()
        except Exception as e:
            logger.error(f"Failed to setup auto-save: {e}")
            
        # Apply loaded settings immediately
        self._apply_loaded_settings()
        
    def _save_settings(self):
        """Save settings"""
        try:
            # Save settings using QSettings
            from PySide6.QtCore import QSettings
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            
            # General settings
            settings.setValue("general/auto_save", self.auto_save_check.isChecked())
            settings.setValue("general/auto_save_interval", self.auto_save_interval_spin.value())
            settings.setValue("general/remember_window", self.remember_window_check.isChecked())
            settings.setValue("general/recent_files_count", self.recent_files_spin.value())
            settings.setValue("general/default_project_location", self.default_project_edit.text())
            settings.setValue("general/associate_files", self.associate_files_check.isChecked())
            
            # Interface settings
            settings.setValue("interface/font_size", self.font_size_spin.value())
            settings.setValue("interface/accent_color", self.accent_color)
            settings.setValue("interface/workflow_colors", self.workflow_colors)
            settings.setValue("interface/console_autoscroll", self.console_autoscroll_check.isChecked())
            settings.setValue("interface/console_buffer", self.console_buffer_spin.value())
            settings.setValue("interface/timestamp_format", self.timestamp_combo.currentText())
            
            # Performance settings
            settings.setValue("performance/max_operations", self.max_operations_spin.value())
            settings.setValue("performance/memory_limit", self.memory_limit_spin.value())
            settings.setValue("performance/gpu_acceleration", self.gpu_acceleration_check.isChecked())
            settings.setValue("performance/cache_size", self.cache_size_spin.value())
            settings.setValue("performance/auto_clear_cache", self.auto_clear_cache_check.isChecked())
            
            # Logging settings
            # Save with consistent key
            settings.setValue("logging/level", self.log_level_combo.currentText())
            settings.setValue("logging/file_enabled", self.log_to_file_check.isChecked())
            settings.setValue("logging/rotation_enabled", self.log_rotation_check.isChecked())
            settings.setValue("logging/max_log_size", self.max_log_size_spin.value())
            settings.setValue("logging/debug_mode", self.debug_mode_check.isChecked())
            
            # Advanced settings
            settings.setValue("advanced/timeout", self.timeout_spin.value())
            settings.setValue("advanced/retry_attempts", self.retry_spin.value())
            settings.setValue("advanced/telemetry", self.telemetry_check.isChecked())
            
            # ComfyUI settings
            settings.setValue("comfyui/texture_wait_time", self.texture_wait_spin.value())
            
            self.settings_updated.emit()
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            logger.info("Application settings saved")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
            logger.error(f"Failed to save settings: {e}")
            
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                # Clear all QSettings
                from PySide6.QtCore import QSettings
                settings = QSettings("ComfyUI-Cinema4D", "Bridge")
                settings.clear()
                
                # Reset all UI controls to default values
                # General settings
                self.auto_save_check.setChecked(True)
                self.auto_save_interval_spin.setValue(5)
                self.remember_window_check.setChecked(True)
                self.recent_files_spin.setValue(10)
                self.default_project_edit.setText(str(self.config.base_dir / "projects"))
                self.associate_files_check.setChecked(False)
                
                # Interface settings
                self.font_size_spin.setValue(12)
                self.accent_color = "#4CAF50"
                self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color}; color: white; padding: 8px;")
                self._reset_workflow_colors()
                self.console_autoscroll_check.setChecked(True)
                self.console_buffer_spin.setValue(1000)
                self.timestamp_combo.setCurrentText("HH:MM:SS")
                
                # Performance settings
                self.max_operations_spin.setValue(4)
                self.memory_limit_spin.setValue(8192)
                self.gpu_acceleration_check.setChecked(True)
                self.cache_size_spin.setValue(1000)
                self.auto_clear_cache_check.setChecked(False)
                
                # Logging settings
                self.log_level_combo.setCurrentText("INFO")
                self.log_to_file_check.setChecked(True)
                self.log_rotation_check.setChecked(True)
                self.max_log_size_spin.setValue(50)
                self.debug_mode_check.setChecked(False)
                
                # Advanced settings
                self.timeout_spin.setValue(30)
                self.retry_spin.setValue(3)
                self.telemetry_check.setChecked(False)
                
                # Apply the reset values immediately
                self._apply_loaded_settings()
                
                QMessageBox.information(self, "Reset Complete", "All settings have been reset to default values.")
                logger.info("Settings reset to defaults")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset settings:\n{str(e)}")
                logger.error(f"Failed to reset settings: {e}")
            
    def _save_and_close(self):
        """Save and close the dialog"""
        self._save_settings()
        self.accept()
    
    def _apply_loaded_settings(self):
        """Apply loaded settings to the application immediately"""
        try:
            # Apply font size
            font_size = self.font_size_spin.value()
            font = self.font()
            font.setPointSize(font_size)
            self.setFont(font)
            if self.parent():
                self.parent().setFont(font)
            
            # Apply accent color to terminal theme
            self._apply_accent_color_to_theme()
            
            # Apply workflow colors
            self._apply_workflow_colors()
            
            # Apply console settings using the safe methods
            self._on_console_autoscroll_changed(self.console_autoscroll_check.isChecked())
            self._on_console_buffer_changed(self.console_buffer_spin.value())
            self._on_timestamp_format_changed(self.timestamp_combo.currentText())
            
            # Apply logging settings
            log_level = self.log_level_combo.currentText()
            self._apply_log_level(log_level)
            
            # Apply debug mode
            if self.debug_mode_check.isChecked():
                self._apply_log_level("DEBUG")
            
            logger.info("Loaded settings applied to application")
            
        except Exception as e:
            logger.error(f"Failed to apply loaded settings: {e}")
    
    def _apply_accent_color_to_theme(self):
        """Apply the accent color to the terminal theme"""
        try:
            # Store the accent color in application config for future use
            parent_app = self.parent()
            if parent_app and hasattr(parent_app, 'config'):
                parent_app.config.accent_color = self.accent_color
            
            # Update only the specific accent color elements, not all green colors
            accent_override_css = f"""
            /* Accent Color Override */
            QPushButton#generate_btn, QPushButton#primary_btn, QPushButton#generate_image_btn, 
            QPushButton#generate_3d_btn, QPushButton#generate_texture_btn {{
                background-color: {self.accent_color} !important;
                border-color: {self.accent_color} !important;
            }}
            
            QTabBar::tab:selected {{
                border-bottom: 2px solid {self.accent_color} !important;
                background-color: rgba({int(self.accent_color[1:3], 16)}, {int(self.accent_color[3:5], 16)}, {int(self.accent_color[5:7], 16)}, 0.05) !important;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {self.accent_color} !important;
            }}
            
            /* Text Selection Colors */
            QTextEdit::selection {{
                background-color: {self.accent_color} !important;
                color: #000000 !important;
            }}
            
            QLineEdit::selection {{
                background-color: {self.accent_color} !important;
                color: #000000 !important;
            }}
            
            /* Console Focus Border */
            QTextEdit#console:focus {{
                border: 1px solid {self.accent_color} !important;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {self.accent_color} !important;
                border-color: {self.accent_color} !important;
            }}
            
            
            /* Magic Prompt Star Buttons - More specific targeting */
            QPushButton[text="★"] {{
                color: {self.accent_color} !important;
            }}
            QPushButton[text="★"]:hover {{
                color: {self._get_lighter_color(self.accent_color)} !important;
            }}
            QPushButton[text="★"]:pressed {{
                color: {self._get_darker_color(self.accent_color)} !important;
            }}
            
            /* Image Thumbnail Selection Borders - Exact selector */
            QFrame#image_thumbnail[selected="true"] {{
                border: 2px solid {self.accent_color} !important;
            }}
            
            /* All Checkbox States - Both #4CAF50 and #22c55e variants */
            QCheckBox::indicator:checked {{
                background-color: {self.accent_color} !important;
                border-color: {self.accent_color} !important;
            }}
            QCheckBox::indicator:hover {{
                border-color: {self.accent_color} !important;
                background-color: rgba({int(self.accent_color[1:3], 16)}, {int(self.accent_color[3:5], 16)}, {int(self.accent_color[5:7], 16)}, 50) !important;
            }}
            
            /* Connection/Status Info Labels */
            QLabel#connection_info {{
                color: {self.accent_color} !important;
            }}
            
            /* 3D Model Selection States */
            Model3DPreviewCard QPushButton[selected="true"] {{
                background-color: {self.accent_color} !important;
            }}
            
            /* Primary Action Buttons - Comprehensive list */
            QPushButton#generate_btn, QPushButton#generate_3d_btn, QPushButton#generate_texture_btn,
            QPushButton#import_selected_btn, QPushButton#export_btn {{
                background-color: {self.accent_color} !important;
                border-color: {self.accent_color} !important;
            }}
            
            /* Dialog and Menu Styling */
            QDialog QListWidget::item:selected {{
                background-color: {self.accent_color} !important;
                color: #000000 !important;
            }}
            QDialog QListWidget::item:hover {{
                background-color: rgba({int(self.accent_color[1:3], 16)}, {int(self.accent_color[3:5], 16)}, {int(self.accent_color[5:7], 16)}, 0.3) !important;
            }}
            
            /* Menu hover states */
            QMenu::item:selected {{
                background-color: {self.accent_color} !important;
                color: #000000 !important;
            }}
            QMenu::item:hover {{
                background-color: rgba({int(self.accent_color[1:3], 16)}, {int(self.accent_color[3:5], 16)}, {int(self.accent_color[5:7], 16)}, 0.8) !important;
                color: #000000 !important;
            }}
            
            /* Submenu indicators */
            QMenu::right-arrow {{
                border-left: 5px solid {self.accent_color};
                border-top: 5px solid transparent;
                border-bottom: 5px solid transparent;
            }}
            
            /* Dialog button focus */
            QDialogButtonBox QPushButton:default {{
                background-color: {self.accent_color} !important;
                border-color: {self.accent_color} !important;
            }}
            QDialogButtonBox QPushButton:focus {{
                border: 2px solid {self.accent_color} !important;
            }}
            
            /* Slider accent colors */
            QSlider::handle:horizontal, QSlider::handle:vertical {{
                background-color: {self.accent_color} !important;
            }}
            QSlider::groove:horizontal:active, QSlider::groove:vertical:active {{
                background-color: rgba({int(self.accent_color[1:3], 16)}, {int(self.accent_color[3:5], 16)}, {int(self.accent_color[5:7], 16)}, 0.3) !important;
            }}
            """
            
            # Apply the accent color override CSS
            if parent_app:
                current_stylesheet = parent_app.styleSheet()
                # Remove any existing accent override
                if '/* Accent Color Override */' in current_stylesheet:
                    parts = current_stylesheet.split('/* Accent Color Override */')
                    current_stylesheet = parts[0]
                
                parent_app.setStyleSheet(current_stylesheet + accent_override_css)
            
            logger.info(f"Applied accent color {self.accent_color} to theme")
        except Exception as e:
            logger.error(f"Failed to apply accent color to theme: {e}")
    
    def _apply_log_level(self, level):
        """Apply log level change"""
        try:
            # Update the COMFY_C4D_DEBUG environment variable based on level
            import os
            if level == "DEBUG":
                os.environ['COMFY_C4D_DEBUG'] = 'true'
            else:
                os.environ['COMFY_C4D_DEBUG'] = 'false'
            
            # Re-initialize logger with new settings
            from src.utils.logger import setup_logging
            
            # Determine if debug mode should be enabled
            debug_enabled = (level == "DEBUG") or (os.getenv('COMFY_C4D_DEBUG', '').lower() in ('true', '1', 'yes', 'on'))
            
            # Get log directory from config
            log_dir = None
            if hasattr(self, 'config') and hasattr(self.config, 'base_dir'):
                log_dir = self.config.base_dir / "logs"
            
            # Reinitialize logging with new settings
            setup_logging(log_dir=log_dir, debug=debug_enabled)
            
            # Save to settings for persistence
            settings = QSettings("ComfyUI-Cinema4D", "Bridge")
            settings.setValue("logging/level", level)
            settings.setValue("logging/file_enabled", getattr(self, 'log_to_file_check', None) and self.log_to_file_check.isChecked())
            settings.setValue("logging/rotation_enabled", getattr(self, 'log_rotation_check', None) and self.log_rotation_check.isChecked())
            
            # Log the configuration change
            logger.info(f"Log level configured to {level} (Debug mode: {debug_enabled})")
            
        except Exception as e:
            logger.error(f"Failed to apply log level: {e}")
    
    # Auto-save functionality
    def _setup_auto_save(self):
        """Setup auto-save timer"""
        try:
            from PySide6.QtCore import QTimer
            if not hasattr(self, 'auto_save_timer'):
                self.auto_save_timer = QTimer()
                self.auto_save_timer.timeout.connect(self._auto_save_project)
            
            # Only start if auto-save is enabled and controls are initialized
            if (hasattr(self, 'auto_save_check') and 
                hasattr(self, 'auto_save_interval_spin') and 
                self.auto_save_check.isChecked()):
                interval = self.auto_save_interval_spin.value() * 60 * 1000  # Convert to milliseconds
                self.auto_save_timer.start(interval)
                logger.info(f"Auto-save timer started with {self.auto_save_interval_spin.value()} minute interval")
            else:
                logger.debug("Auto-save timer setup complete (not started - disabled or controls not ready)")
        except Exception as e:
            logger.error(f"Failed to setup auto-save timer: {e}")
    
    def _auto_save_project(self):
        """Auto-save the current project"""
        try:
            logger.info("Auto-saving project...")
            
            # Check if parent has project manager and current project
            parent_app = self.parent()
            if not parent_app:
                logger.warning("No parent application found for auto-save")
                return
                
            # Try to save current project state
            if hasattr(parent_app, 'project_manager') and parent_app.project_manager:
                project_manager = parent_app.project_manager
                
                # Create auto-save data
                project_data = {
                    "timestamp": datetime.now().isoformat(),
                    "selected_images": [str(p) for p in getattr(parent_app, 'selected_images', [])],
                    "selected_models": [str(p) for p in getattr(parent_app, 'selected_models', [])],
                    "current_stage": getattr(parent_app, 'current_stage', 0),
                    "session_data": {
                        "images": getattr(parent_app, 'session_images', []),
                        "models": getattr(parent_app, 'session_models', [])
                    }
                }
                
                # Save to auto-save file
                auto_save_dir = self.config.base_dir / "autosave"
                auto_save_dir.mkdir(exist_ok=True)
                auto_save_file = auto_save_dir / f"autosave_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(auto_save_file, 'w') as f:
                    json.dump(project_data, f, indent=2)
                
                # Keep only last 10 auto-save files
                auto_save_files = sorted(auto_save_dir.glob("autosave_*.json"))
                while len(auto_save_files) > 10:
                    oldest_file = auto_save_files.pop(0)
                    oldest_file.unlink()
                
                logger.info(f"Project auto-saved to {auto_save_file}")
                
            else:
                logger.warning("Project manager not available for auto-save")
                
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
    
    # Interface settings methods
    def _on_font_size_changed(self, value):
        """Handle font size change"""
        try:
            # Apply font size change immediately
            font = self.font()
            font.setPointSize(value)
            self.setFont(font)
            if self.parent():
                self.parent().setFont(font)
            logger.debug(f"Font size changed to {value}px")
        except Exception as e:
            logger.error(f"Failed to change font size: {e}")
    
    def _apply_accent_color(self):
        """Apply accent color to the application"""
        try:
            # Apply the accent color immediately
            self._apply_accent_color_to_theme()
            
            # Notify parent application about the accent color change
            parent_app = self.parent()
            if parent_app and hasattr(parent_app, '_apply_saved_accent_color'):
                parent_app._apply_saved_accent_color()
                
            logger.debug(f"Accent color changed to {self.accent_color}")
        except Exception as e:
            logger.error(f"Failed to apply accent color: {e}")
    
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
    
    # Console settings methods
    def _on_console_autoscroll_changed(self, checked):
        """Handle console auto-scroll change"""
        try:
            # Store the setting for the console to use
            parent_app = self.parent()
            if parent_app:
                # Store in config for console to pick up
                if hasattr(parent_app, 'config'):
                    parent_app.config.console_auto_scroll = checked
                    
                # Try to apply to existing console if available
                if hasattr(parent_app, 'console'):
                    console = parent_app.console
                    # Check for various console implementations
                    for attr_name in ['setAutoScroll', 'set_auto_scroll', 'auto_scroll']:
                        if hasattr(console, attr_name):
                            attr = getattr(console, attr_name)
                            if callable(attr):
                                attr(checked)
                            else:
                                setattr(console, attr_name, checked)
                            break
                            
            logger.debug(f"Console auto-scroll {'enabled' if checked else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to change console auto-scroll: {e}")
    
    def _on_console_buffer_changed(self, value):
        """Handle console buffer size change"""
        try:
            # Store the setting for the console to use
            parent_app = self.parent()
            if parent_app:
                # Store in config
                if hasattr(parent_app, 'config'):
                    parent_app.config.console_buffer_size = value
                    
                # Try to apply to existing console if available
                if hasattr(parent_app, 'console'):
                    console = parent_app.console
                    # Check for various buffer size implementations
                    for attr_name in ['setMaximumBlockCount', 'set_buffer_size', 'buffer_size', 'max_block_count']:
                        if hasattr(console, attr_name):
                            attr = getattr(console, attr_name)
                            if callable(attr):
                                attr(value)
                            else:
                                setattr(console, attr_name, value)
                            break
                            
            logger.debug(f"Console buffer size changed to {value} lines")
        except Exception as e:
            logger.error(f"Failed to change console buffer size: {e}")
    
    def _on_timestamp_format_changed(self, format_str):
        """Handle timestamp format change"""
        try:
            # Store the setting for the console to use
            parent_app = self.parent()
            if parent_app:
                # Store in config
                if hasattr(parent_app, 'config'):
                    parent_app.config.console_timestamp_format = format_str
                    
                # Try to apply to existing console if available
                if hasattr(parent_app, 'console'):
                    console = parent_app.console
                    # Check for various timestamp format implementations
                    for attr_name in ['set_timestamp_format', 'timestamp_format', 'setTimestampFormat']:
                        if hasattr(console, attr_name):
                            attr = getattr(console, attr_name)
                            if callable(attr):
                                attr(format_str)
                            else:
                                setattr(console, attr_name, format_str)
                            break
                            
            logger.debug(f"Timestamp format changed to {format_str}")
        except Exception as e:
            logger.error(f"Failed to change timestamp format: {e}")
    
    # Performance settings methods
    def _on_max_operations_changed(self, value):
        """Handle max concurrent operations change"""
        try:
            # Apply to workflow manager if available
            parent_app = self.parent()
            if parent_app and hasattr(parent_app, 'workflow_manager'):
                workflow_manager = parent_app.workflow_manager
                if hasattr(workflow_manager, 'set_max_concurrent_operations'):
                    workflow_manager.set_max_concurrent_operations(value)
                elif hasattr(workflow_manager, 'max_concurrent_operations'):
                    workflow_manager.max_concurrent_operations = value
            logger.debug(f"Max concurrent operations changed to {value}")
        except Exception as e:
            logger.error(f"Failed to change max operations: {e}")
    
    def _on_memory_limit_changed(self, value):
        """Handle memory limit change"""
        try:
            # Apply memory limit to processing components
            parent_app = self.parent()
            if parent_app:
                # Store in config for use by processing components
                if hasattr(parent_app, 'config'):
                    parent_app.config.memory_limit_mb = value
                    
                # Apply to workflow manager if available
                if hasattr(parent_app, 'workflow_manager'):
                    workflow_manager = parent_app.workflow_manager
                    if hasattr(workflow_manager, 'set_memory_limit'):
                        workflow_manager.set_memory_limit(value)
            logger.debug(f"Memory limit changed to {value}MB")
        except Exception as e:
            logger.error(f"Failed to change memory limit: {e}")
    
    def _on_gpu_acceleration_changed(self, checked):
        """Handle GPU acceleration change"""
        try:
            # Apply GPU acceleration setting
            parent_app = self.parent()
            if parent_app:
                # Store in config
                if hasattr(parent_app, 'config'):
                    parent_app.config.gpu_acceleration = checked
                    
                # Apply to ComfyUI client if available
                if hasattr(parent_app, 'comfyui_client'):
                    comfyui_client = parent_app.comfyui_client
                    if hasattr(comfyui_client, 'set_gpu_acceleration'):
                        comfyui_client.set_gpu_acceleration(checked)
            logger.debug(f"GPU acceleration {'enabled' if checked else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to change GPU acceleration: {e}")
    
    def _on_cache_size_changed(self, value):
        """Handle cache size change"""
        try:
            # Apply cache size limit
            parent_app = self.parent()
            if parent_app:
                # Store in config
                if hasattr(parent_app, 'config'):
                    parent_app.config.cache_size_mb = value
                    
                # Apply to any cache managers
                if hasattr(parent_app, 'file_monitor'):
                    file_monitor = parent_app.file_monitor
                    if hasattr(file_monitor, 'set_cache_size'):
                        file_monitor.set_cache_size(value)
            logger.debug(f"Cache size changed to {value}MB")
        except Exception as e:
            logger.error(f"Failed to change cache size: {e}")
    
    def _on_auto_clear_cache_changed(self, checked):
        """Handle auto-clear cache change"""
        try:
            logger.debug(f"Auto-clear cache {'enabled' if checked else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to change auto-clear cache: {e}")
    
    # Logging settings methods
    def _on_log_level_changed(self, level):
        """Handle log level change"""
        try:
            # Use the centralized log level application method
            self._apply_log_level(level)
        except Exception as e:
            logger.error(f"Failed to change log level: {e}")
    
    def _on_log_to_file_changed(self, checked):
        """Handle log to file change"""
        try:
            # Re-apply the current log level which will handle file logging
            current_level = self.log_level_combo.currentText()
            self._apply_log_level(current_level)
            logger.debug(f"File logging {'enabled' if checked else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to change file logging: {e}")
    
    def _on_log_rotation_changed(self, checked):
        """Handle log rotation change"""
        try:
            logger.debug(f"Log rotation {'enabled' if checked else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to change log rotation: {e}")
    
    def _on_max_log_size_changed(self, value):
        """Handle max log size change"""
        try:
            logger.debug(f"Max log file size changed to {value}MB")
        except Exception as e:
            logger.error(f"Failed to change max log size: {e}")
    
    def _on_debug_mode_changed(self, checked):
        """Handle debug mode change"""
        try:
            if checked:
                self._apply_log_level("DEBUG")
                self.log_level_combo.setCurrentText("DEBUG")
            else:
                self._apply_log_level("INFO")
                self.log_level_combo.setCurrentText("INFO")
            logger.debug(f"Debug mode {'enabled' if checked else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to change debug mode: {e}")
    
    # Advanced settings methods
    def _on_telemetry_changed(self, checked):
        """Handle telemetry change"""
        try:
            logger.debug(f"Telemetry {'enabled' if checked else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to change telemetry: {e}")
    
    def _browse_default_project_location(self):
        """Browse for default project location"""
        from PySide6.QtWidgets import QFileDialog
        current_path = self.default_project_edit.text()
        if not current_path:
            current_path = str(self.config.base_dir)
        
        path = QFileDialog.getExistingDirectory(
            self, "Select Default Project Location", current_path
        )
        if path:
            self.default_project_edit.setText(path)
    
    def _on_auto_save_changed(self, checked):
        """Handle auto-save enable/disable"""
        try:
            if not hasattr(self, 'auto_save_timer'):
                self._setup_auto_save()
                
            if checked:
                interval = self.auto_save_interval_spin.value() * 60 * 1000
                self.auto_save_timer.start(interval)
                logger.info(f"Auto-save enabled with {self.auto_save_interval_spin.value()} minute interval")
            else:
                self.auto_save_timer.stop()
                logger.info("Auto-save disabled")
        except Exception as e:
            logger.error(f"Failed to change auto-save: {e}")
    
    def _on_auto_save_interval_changed(self, value):
        """Handle auto-save interval change"""
        try:
            if not hasattr(self, 'auto_save_timer'):
                self._setup_auto_save()
                
            if self.auto_save_check.isChecked():
                interval = value * 60 * 1000
                self.auto_save_timer.start(interval)
                logger.debug(f"Auto-save interval changed to {value} minutes")
            else:
                logger.debug(f"Auto-save interval set to {value} minutes (currently disabled)")
        except Exception as e:
            logger.error(f"Failed to change auto-save interval: {e}")
    
    def _choose_workflow_color(self, color_index):
        """Choose a workflow color for the specified index"""
        try:
            current_color = QColor(self.workflow_colors[color_index])
            color = QColorDialog.getColor(current_color, self, f"Choose Workflow Color {color_index + 1}")
            if color.isValid():
                self.workflow_colors[color_index] = color.name()
                self.color_buttons[color_index].setStyleSheet(
                    f"background-color: {color.name()}; color: white; padding: 8px; min-width: 80px;"
                )
                self._apply_workflow_colors()
                logger.debug(f"Workflow color {color_index + 1} changed to {color.name()}")
        except Exception as e:
            logger.error(f"Failed to choose workflow color: {e}")
    
    def _reset_workflow_colors(self):
        """Reset workflow colors to default values"""
        try:
            default_colors = [
                "#4CAF50",  # Green - Primary sampling
                "#2196F3",  # Blue - Model loading  
                "#9C27B0",  # Purple - LoRA
                "#FF9800",  # Orange - VAE
                "#00BCD4"   # Cyan - Text encoding
            ]
            
            self.workflow_colors = default_colors.copy()
            
            for i, color in enumerate(self.workflow_colors):
                if i < len(self.color_buttons):
                    self.color_buttons[i].setStyleSheet(
                        f"background-color: {color}; color: white; padding: 8px; min-width: 80px;"
                    )
            
            self._apply_workflow_colors()
            logger.info("Workflow colors reset to defaults")
        except Exception as e:
            logger.error(f"Failed to reset workflow colors: {e}")
    
    def _apply_workflow_colors(self):
        """Apply workflow colors to the unified configuration manager"""
        try:
            parent_app = self.parent()
            if not parent_app:
                logger.debug("No parent application found for workflow colors")
                return
                
            # Ensure we have valid workflow colors
            if not hasattr(self, 'workflow_colors') or len(self.workflow_colors) < 5:
                logger.warning("Invalid workflow colors - using defaults")
                return
            
            # Create a mapping for the most common node types
            color_mapping = {
                "KSampler": self.workflow_colors[0],
                "KSamplerAdvanced": self.workflow_colors[0],
                "CheckpointLoader": self.workflow_colors[1], 
                "CheckpointLoaderSimple": self.workflow_colors[1],
                "UNETLoader": self.workflow_colors[1],
                "LoraLoader": self.workflow_colors[2],
                "VAELoader": self.workflow_colors[3],
                "CLIPTextEncode": self.workflow_colors[4],
                "FluxGuidance": self.workflow_colors[3],
                "EmptyLatentImage": self.workflow_colors[1],
                "EmptySD3LatentImage": self.workflow_colors[1],
                "ControlNetLoader": self.workflow_colors[2],
                "QuadrupleCLIPLoader": self.workflow_colors[4],
                # Hunyuan3D nodes
                "Hy3DModelLoader": self.workflow_colors[1],
                "Hy3DGenerateMesh": self.workflow_colors[0],
                "Hy3DVAEDecode": self.workflow_colors[3],
                "Hy3DPostprocessMesh": self.workflow_colors[2],
                "Hy3DExportMesh": self.workflow_colors[1]
            }
            
            # Try different possible locations for the unified config manager
            config_manager = None
            for attr_name in ['unified_config_manager', 'config_manager', 'parameter_manager']:
                if hasattr(parent_app, attr_name):
                    config_manager = getattr(parent_app, attr_name)
                    if hasattr(config_manager, 'update_node_colors'):
                        config_manager.update_node_colors(color_mapping)
                        logger.debug(f"Updated workflow colors via {attr_name}")
                        break
            
            if not config_manager:
                logger.debug("No unified configuration manager found - storing colors in app config")
                # Store colors in parent app for later use
                if hasattr(parent_app, 'config'):
                    parent_app.config.workflow_colors = self.workflow_colors
                    parent_app.config.workflow_color_mapping = color_mapping
            
            # Also update any existing parameter UI elements
            if hasattr(parent_app, '_refresh_workflow_parameter_colors'):
                parent_app._refresh_workflow_parameter_colors()
            elif hasattr(parent_app, '_load_parameters_unified'):
                # Try to refresh the current tab's parameters
                try:
                    current_tab = getattr(parent_app, 'current_tab_index', 0)
                    if current_tab == 0:
                        parent_app._load_parameters_unified('image')
                    elif current_tab == 1:
                        parent_app._load_parameters_unified('3d_parameters')
                    elif current_tab == 2:
                        parent_app._load_parameters_unified('texture_parameters')
                except Exception as refresh_error:
                    logger.debug(f"Could not refresh parameters UI: {refresh_error}")
                    
            logger.debug("Applied workflow colors successfully")
        except Exception as e:
            logger.error(f"Failed to apply workflow colors: {e}")