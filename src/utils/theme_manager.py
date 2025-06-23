"""
Unified Theme Manager

Manages consistent theming across all UI components with proper accent color inheritance.
Fixes inconsistencies in selection colors, hover states, and other UI elements.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor

from loguru import logger


class UnifiedThemeManager(QObject):
    """Manages unified theming across the entire application"""
    
    theme_changed = Signal(str)  # theme_name
    accent_color_changed = Signal(str)  # hex_color
    
    def __init__(self):
        super().__init__()
        self.current_theme = "dark"
        self.accent_color = "#4CAF50"
        self.themes_config_path = Path("config/themes.json")
        self.load_themes_config()
    
    def load_themes_config(self):
        """Load themes configuration"""
        try:
            if self.themes_config_path.exists():
                with open(self.themes_config_path, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get("current_theme", "dark")
                    self.accent_color = config.get("accent_color", "#4CAF50")
            else:
                self.save_themes_config()
        except Exception as e:
            logger.error(f"Failed to load themes config: {e}")
    
    def save_themes_config(self):
        """Save themes configuration"""
        try:
            self.themes_config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                "current_theme": self.current_theme,
                "accent_color": self.accent_color
            }
            with open(self.themes_config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save themes config: {e}")
    
    def set_accent_color(self, color: str):
        """Set accent color and update all components"""
        self.accent_color = color
        self.save_themes_config()
        self.accent_color_changed.emit(color)
        logger.debug(f"Accent color changed to: {color}")
    
    def set_theme(self, theme_name: str):
        """Set theme and update all components"""
        self.current_theme = theme_name
        self.save_themes_config()
        self.theme_changed.emit(theme_name)
        logger.info(f"Theme changed to: {theme_name}")
    
    def get_complete_stylesheet(self) -> str:
        """Get complete stylesheet with proper accent color inheritance"""
        base_style = self._get_base_theme_stylesheet()
        accent_style = self._get_accent_color_stylesheet()
        return base_style + "\n" + accent_style
    
    def _get_base_theme_stylesheet(self) -> str:
        """Get base theme stylesheet"""
        if self.current_theme == "dark":
            return """
            /* Dark Theme Base */
            QMainWindow, QWidget, QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 9pt;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 20px;
                color: #e0e0e0;
            }
            
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: var(--accent-color);
            }
            
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
            
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
                border-color: #333333;
            }
            
            /* Tabs */
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1e1e1e;
            }
            
            QTabBar::tab {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                padding: 8px 16px;
                margin-right: 2px;
                color: #e0e0e0;
            }
            
            QTabBar::tab:selected {
                background-color: var(--accent-color);
                color: #000000;
                font-weight: bold;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #3d3d3d;
                border-color: var(--accent-color);
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                selection-background-color: var(--accent-color);
                selection-color: #000000;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: var(--accent-color);
                background-color: #323232;
            }
            
            /* ComboBox */
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                min-width: 100px;
            }
            
            QComboBox:hover {
                border-color: var(--accent-color);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
                margin-right: 5px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid var(--accent-color);
                selection-background-color: var(--accent-color);
                selection-color: #000000;
            }
            
            /* Lists */
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
                color: #e0e0e0;
                selection-background-color: var(--accent-color);
                selection-color: #000000;
            }
            
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #333333;
            }
            
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            
            QListWidget::item:selected {
                background-color: var(--accent-color);
                color: #000000;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            
            QProgressBar::chunk {
                background-color: var(--accent-color);
                border-radius: 3px;
            }
            
            /* Sliders */
            QSlider::groove:horizontal {
                border: 1px solid #404040;
                height: 8px;
                background: #2d2d2d;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: var(--accent-color);
                border: 1px solid #404040;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: var(--accent-color-light);
            }
            
            /* Checkboxes */
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #404040;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            
            QCheckBox::indicator:hover {
                border-color: var(--accent-color);
            }
            
            QCheckBox::indicator:checked {
                background-color: var(--accent-color);
                border-color: var(--accent-color);
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: var(--accent-color);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            /* Group Boxes */
            QGroupBox {
                font-weight: bold;
                border: 1px solid #404040;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: #e0e0e0;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: var(--accent-color);
            }
            
            /* Splitters */
            QSplitter::handle {
                background-color: #404040;
            }
            
            QSplitter::handle:hover {
                background-color: var(--accent-color);
            }
            
            /* Menu Bar */
            QMenuBar {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border-bottom: 1px solid #404040;
            }
            
            QMenuBar::item {
                padding: 4px 8px;
                background: transparent;
            }
            
            QMenuBar::item:selected {
                background-color: var(--accent-color);
                color: #000000;
            }
            
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                color: #e0e0e0;
            }
            
            QMenu::item {
                padding: 4px 8px;
            }
            
            QMenu::item:selected {
                background-color: var(--accent-color);
                color: #000000;
            }
            """
        else:
            # Light theme would go here
            return self._get_base_theme_stylesheet()
    
    def _get_accent_color_stylesheet(self) -> str:
        """Generate accent color CSS variables and overrides"""
        # Parse accent color to get variations
        color = QColor(self.accent_color)
        
        # Create lighter and darker variations
        lighter = color.lighter(120)
        darker = color.darker(120)
        
        # Convert to hex
        accent_light = lighter.name()
        accent_dark = darker.name()
        
        return f"""
        /* Accent Color Variables */
        * {{
            --accent-color: {self.accent_color};
            --accent-color-light: {accent_light};
            --accent-color-dark: {accent_dark};
        }}
        
        /* Override any hardcoded accent colors */
        QPushButton:hover {{
            border-color: {self.accent_color} !important;
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.accent_color} !important;
        }}
        
        QTabBar::tab:hover:!selected {{
            border-color: {self.accent_color} !important;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {self.accent_color} !important;
        }}
        
        QComboBox:hover {{
            border-color: {self.accent_color} !important;
        }}
        
        QListWidget::item:selected {{
            background-color: {self.accent_color} !important;
        }}
        
        QProgressBar::chunk {{
            background-color: {self.accent_color} !important;
        }}
        
        QSlider::handle:horizontal {{
            background: {self.accent_color} !important;
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {self.accent_color} !important;
            border-color: {self.accent_color} !important;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.accent_color} !important;
        }}
        
        QGroupBox::title {{
            color: {self.accent_color} !important;
        }}
        
        QSplitter::handle:hover {{
            background-color: {self.accent_color} !important;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.accent_color} !important;
        }}
        
        QMenu::item:selected {{
            background-color: {self.accent_color} !important;
        }}
        
        /* Special cases for selection colors */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            selection-background-color: {self.accent_color} !important;
        }}
        
        QComboBox QAbstractItemView {{
            selection-background-color: {self.accent_color} !important;
        }}
        
        QListWidget {{
            selection-background-color: {self.accent_color} !important;
        }}
        """
    
    def apply_to_widget(self, widget):
        """Apply current theme to a specific widget"""
        if widget:
            stylesheet = self.get_complete_stylesheet()
            widget.setStyleSheet(stylesheet)
    
    def get_accent_color(self) -> str:
        """Get current accent color"""
        return self.accent_color
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get theme color palette"""
        return {
            "accent": self.accent_color,
            "accent_light": QColor(self.accent_color).lighter(120).name(),
            "accent_dark": QColor(self.accent_color).darker(120).name(),
            "background": "#1e1e1e" if self.current_theme == "dark" else "#ffffff",
            "surface": "#2d2d2d" if self.current_theme == "dark" else "#f5f5f5",
            "text": "#e0e0e0" if self.current_theme == "dark" else "#333333",
            "border": "#404040" if self.current_theme == "dark" else "#cccccc"
        }


# Global theme manager instance
_global_theme_manager: Optional[UnifiedThemeManager] = None


def get_theme_manager() -> UnifiedThemeManager:
    """Get global theme manager instance"""
    global _global_theme_manager
    if _global_theme_manager is None:
        _global_theme_manager = UnifiedThemeManager()
    return _global_theme_manager


def apply_unified_theme(widget, accent_color: Optional[str] = None):
    """Apply unified theme to widget with optional accent color override"""
    theme_manager = get_theme_manager()
    if accent_color:
        theme_manager.set_accent_color(accent_color)
    theme_manager.apply_to_widget(widget)