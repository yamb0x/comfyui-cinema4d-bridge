"""
Prompt Widget with Embedded Magic Button
Restores the original behavior where magic button is inside prompt boxes
"""

import random
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
        
        # Style the text area with terminal theme
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
            QTextEdit:focus {
                border: 1px solid #4CAF50;
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
        
        # Style magic button as simple text without background
        self.magic_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #4CAF50;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
            QPushButton:hover {
                color: #66BB6A;
            }
            QPushButton:pressed {
                color: #2E7D32;
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
        
        # Generate random prompt
        creative_prompts = [
            "A mystical forest with glowing mushrooms and ethereal light",
            "Futuristic cityscape with neon lights and flying vehicles",
            "Ancient temple ruins covered in vines and morning mist",
            "Steampunk laboratory with brass machinery and glowing tubes",
            "Underwater scene with bioluminescent creatures and coral reefs",
            "Desert oasis with palm trees and crystal clear water",
            "Medieval castle on a cliff overlooking stormy seas",
            "Space station orbiting a distant alien planet",
            "Enchanted garden with floating islands and waterfalls",
            "Cyberpunk street market with holographic signs and robots"
        ]
        
        random_prompt = random.choice(creative_prompts)
        self.text_area.setPlainText(random_prompt)
        
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
        
        # Different prompts for negative
        self.negative_prompts = [
            "blurry, low quality, distorted, ugly, bad anatomy",
            "worst quality, low resolution, jpeg artifacts, watermark",
            "text, signature, username, error, cropped",
            "duplicate, morbid, mutilated, out of frame",
            "extra fingers, mutated hands, poorly drawn hands",
            "extra limbs, disfigured, deformed, body out of frame",
            "bad art, beginner, amateur, distorted face",
            "b&w, black and white, monochrome",
            "nsfw, nude, explicit content",
            "violence, gore, disturbing content"
        ]
        
    def _on_magic_clicked(self):
        """Handle magic button click for negative prompts"""
        self.magic_prompt_requested.emit()
        
        random_prompt = random.choice(self.negative_prompts)
        self.text_area.setPlainText(random_prompt)