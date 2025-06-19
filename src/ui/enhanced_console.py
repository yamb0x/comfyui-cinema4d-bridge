"""
Enhanced Console Widget with Terminal Color Coding
Professional logging system with JetBrains Mono and terminal aesthetics
"""

from datetime import datetime
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QTextCursor
from loguru import logger

from .terminal_theme_complete import get_console_color_map, format_console_message


class TerminalConsoleWidget(QTextEdit):
    """
    Enhanced console widget with terminal aesthetics and color coding
    Integrates with loguru for comprehensive logging
    """
    
    log_message = Signal(str, str)  # level, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("console")
        self.setReadOnly(True)
        
        # Terminal console properties
        self.max_lines = 2000
        self.auto_scroll_enabled = True
        self.color_map = get_console_color_map()
        
        # Setup console appearance
        self._setup_console()
        
        # Connect signals
        self.log_message.connect(self._append_formatted_message)
        
        # Setup logging integration
        self._setup_logging_handler()
        
    def _setup_console(self):
        """Setup console appearance and behavior"""
        # Set font to JetBrains Mono for terminal aesthetic
        font = QFont("JetBrains Mono", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        
        # Enable rich text
        self.setAcceptRichText(True)
        
        # Set placeholder
        self.setPlaceholderText("Console ready - waiting for application events...")
        
    def _setup_logging_handler(self):
        """Setup loguru handler for console integration"""
        try:
            logger.add(
                self._log_sink,
                format="{time:HH:mm:ss} | {level: <8} | {message}",
                level="DEBUG",
                colorize=False,
                backtrace=False,
                diagnose=False
            )
        except Exception as e:
            print(f"Failed to setup logging handler: {e}")
    
    def _log_sink(self, message):
        """Loguru sink function - thread-safe message capture"""
        record = message.record
        level = record["level"].name.lower()
        msg = record["message"]
        timestamp = record["time"].strftime("%H:%M:%S")
        
        # Emit signal for thread-safe GUI update
        self.log_message.emit(level, f"[{timestamp}] {msg}")
    
    @Slot(str, str)
    def _append_formatted_message(self, level: str, message: str):
        """Append formatted message with proper color coding"""
        # Parse timestamp and content
        if message.startswith("[") and "] " in message:
            timestamp_end = message.find("] ") + 1
            timestamp = message[1:timestamp_end-1]
            content = message[timestamp_end+1:]
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            content = message
        
        # Get colors
        timestamp_color = self.color_map['timestamp']
        level_color = self.color_map.get(level, self.color_map['info'])
        message_color = self.color_map['message']
        
        # Create formatted HTML
        html_message = f'''
        <div style="margin-bottom: 1px; font-family: 'JetBrains Mono', monospace; font-size: 10px;">
            <span style="color: {timestamp_color};">[{timestamp}]</span>
            <span style="color: {level_color}; margin: 0 6px;">{level.upper()}</span>
            <span style="color: {message_color};">{content}</span>
        </div>
        '''
        
        # Append to console
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html_message)
        
        # Manage line count
        self._manage_line_count()
        
        # Auto scroll if enabled
        if self.auto_scroll_enabled:
            self._scroll_to_bottom()
    
    def _manage_line_count(self):
        """Keep console lines within limit"""
        if self.document().blockCount() > self.max_lines:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(
                QTextCursor.Down, 
                QTextCursor.KeepAnchor, 
                self.document().blockCount() - self.max_lines
            )
            cursor.removeSelectedText()
    
    def _scroll_to_bottom(self):
        """Scroll console to bottom"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_system_message(self, message: str, level: str = "info"):
        """Add system message directly to console"""
        self.log_message.emit(level, message)
    
    def add_success_message(self, message: str):
        """Add success message"""
        self.add_system_message(message, "success")
    
    def add_error_message(self, message: str):
        """Add error message"""
        self.add_system_message(message, "error")
    
    def add_warning_message(self, message: str):
        """Add warning message"""
        self.add_system_message(message, "warning")
    
    def set_auto_scroll(self, enabled: bool):
        """Enable/disable auto scroll"""
        self.auto_scroll_enabled = enabled
    
    def clear_console(self):
        """Clear console content"""
        self.clear()
        self.add_system_message("Console cleared", "info")


class ConsoleContainer(QWidget):
    """
    Complete console container with controls and status
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("console_container")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the console container UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Console widget
        self.console = TerminalConsoleWidget()
        layout.addWidget(self.console)
        
        # Status bar
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)
    
    def _create_status_bar(self) -> QWidget:
        """Create console status bar"""
        status_widget = QWidget()
        status_widget.setObjectName("status_bar")
        status_widget.setFixedHeight(24)
        
        layout = QHBoxLayout(status_widget)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)
        
        # Auto scroll checkbox
        self.auto_scroll_checkbox = QPushButton("Auto Scroll")
        self.auto_scroll_checkbox.setObjectName("status_text")
        self.auto_scroll_checkbox.setCheckable(True)
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.clicked.connect(self._toggle_auto_scroll)
        layout.addWidget(self.auto_scroll_checkbox)
        
        layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("status_text")
        clear_btn.clicked.connect(self.console.clear_console)
        layout.addWidget(clear_btn)
        
        return status_widget
    
    def _toggle_auto_scroll(self, checked: bool):
        """Toggle auto scroll"""
        self.console.set_auto_scroll(checked)
        self.auto_scroll_checkbox.setText("Auto Scroll ✓" if checked else "Auto Scroll")
    
    def add_message(self, message: str, level: str = "info"):
        """Add message to console"""
        self.console.add_system_message(message, level)
    
    def add_separator(self):
        """Add visual separator to console"""
        separator = "─" * 60
        self.console.add_system_message(separator, "info")


# Legacy compatibility
class ConsoleWidget(TerminalConsoleWidget):
    """Legacy console widget for backward compatibility"""
    pass