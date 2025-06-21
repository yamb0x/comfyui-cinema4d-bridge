"""
Prompt Widget with Embedded Magic Button
Restores the original behavior where magic button is inside prompt boxes
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


class PromptWithMagicButton(QWidget):
    """Prompt text area with embedded magic button"""
    
    text_changed = Signal()
    magic_prompt_requested = Signal()
    
    def __init__(self, placeholder="Enter prompt...", parent=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the prompt widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Create text area
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText(self.placeholder)
        self.text_area.setMinimumHeight(80)
        self.text_area.setMaximumHeight(120)
        self.text_area.textChanged.connect(self.text_changed.emit)
        
        # Style the text area with terminal theme - focus colors handled by accent color CSS
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #fafafa;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 8px;
                font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        
        # Create container for text area and magic button
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addWidget(self.text_area)
        
        # Create magic button positioned in bottom-right corner
        self.magic_btn = QPushButton("★")
        self.magic_btn.setFixedSize(24, 24)
        self.magic_btn.setToolTip("Open Magic Prompts Database")
        self.magic_btn.clicked.connect(self._on_magic_clicked)
        
        # Style magic button as simple text without background - colors handled by accent color CSS
        self.magic_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
        """)
        
        # Ensure button is always visible and on top
        self.magic_btn.raise_()
        self.magic_btn.show()
        
        # Position magic button in bottom-right corner
        self.magic_btn.setParent(self.text_area)
        self.magic_btn.move(
            self.text_area.width() - self.magic_btn.width() - 5,
            self.text_area.height() - self.magic_btn.height() - 5
        )
        
        layout.addWidget(text_container)
        
        # Connect resize event to reposition button
        self.text_area.resizeEvent = self._on_text_area_resize
        
    def _on_text_area_resize(self, event):
        """Reposition magic button when text area resizes"""
        # Call original resize event
        QTextEdit.resizeEvent(self.text_area, event)
        
        # Reposition magic button
        if hasattr(self, 'magic_btn'):
            self.magic_btn.move(
                self.text_area.width() - self.magic_btn.width() - 5,
                self.text_area.height() - self.magic_btn.height() - 5
            )
            # Ensure button stays on top after resize
            self.magic_btn.raise_()
            
    def _on_magic_clicked(self):
        """Handle magic button click"""
        self.magic_prompt_requested.emit()
        
    def get_text(self) -> str:
        """Get current text"""
        return self.text_area.toPlainText()
        
    def get_prompt(self) -> str:
        """Get current prompt text (alias for get_text for compatibility)"""
        return self.get_text()
        
    def set_text(self, text: str):
        """Set text"""
        self.text_area.setPlainText(text)
        
    def clear(self):
        """Clear text"""
        self.text_area.clear()


class PositivePromptWidget(PromptWithMagicButton):
    """Positive prompt widget with magic button"""
    
    def __init__(self, parent=None):
        super().__init__("Enter positive prompt...", parent)


class NegativePromptWidget(PromptWithMagicButton):
    """Negative prompt widget with magic button"""
    
    def __init__(self, parent=None):
        super().__init__("Enter negative prompt...", parent)
        
    def _on_magic_clicked(self):
        """Handle magic button click for negative prompts"""
        self.magic_prompt_requested.emit()