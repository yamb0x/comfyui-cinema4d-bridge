"""
Magic Prompt Widget
Enhanced prompt input with AI assistance and terminal aesthetics
"""

import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QFrame, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCursor, QFont, QAction


class MagicPromptWidget(QWidget):
    """
    Enhanced prompt widget with magic prompt functionality
    Includes AI assistance, suggestions, and terminal aesthetics
    """
    
    # Signals
    prompt_changed = Signal(str)
    magic_prompt_requested = Signal()
    
    def __init__(self, title: str = "Prompt", placeholder: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.placeholder = placeholder
        
        # Magic prompt suggestions
        self.magic_suggestions = [
            "Futuristic, cyberpunk, neon lighting, high detail",
            "Photorealistic, professional photography, studio lighting",
            "Concept art, digital painting, detailed, atmospheric",
            "3D render, octane render, volumetric lighting, cinematic",
            "Fantasy, mystical, ethereal, glowing effects",
            "Minimalist, clean, modern, architectural",
            "Vintage, retro, film grain, nostalgic",
            "Abstract, geometric, colorful, artistic",
            "Nature, organic, flowing, natural lighting",
            "Industrial, metallic, mechanical, precise"
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the magic prompt UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Title with magic button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        # Title label
        title_label = QLabel(self.title)
        title_label.setObjectName("section_title")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Magic button
        self.magic_btn = QPushButton("✨")
        self.magic_btn.setObjectName("magic_btn")
        self.magic_btn.setFixedSize(24, 24)
        self.magic_btn.setToolTip("Generate magic prompt suggestions")
        self.magic_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.magic_btn.clicked.connect(self._show_magic_menu)
        title_layout.addWidget(self.magic_btn)
        
        layout.addLayout(title_layout)
        
        # Prompt text area
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(self.placeholder)
        self.prompt_edit.setMaximumHeight(100)
        self.prompt_edit.setMinimumHeight(60)
        self.prompt_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.prompt_edit)
        
        # Character count
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setObjectName("connection_info")
        self.char_count_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.char_count_label)
        
    def _show_magic_menu(self):
        """Show magic prompt suggestions menu"""
        menu = QMenu(self)
        menu.setObjectName("magic_menu")
        
        # Add suggestion categories
        categories = {
            "🎨 Artistic Styles": [
                "Digital art, concept art, detailed illustration",
                "Oil painting, traditional art, masterpiece",
                "Watercolor, soft brushstrokes, delicate",
                "Sketch, pencil drawing, artistic"
            ],
            "📸 Photography": [
                "Professional photography, DSLR, high resolution",
                "Studio lighting, portrait photography",
                "Golden hour, natural lighting, outdoor",
                "Macro photography, close-up, detailed"
            ],
            "🌟 Enhancement": [
                "High quality, best quality, masterpiece",
                "Ultra detailed, 4K, sharp focus",
                "Vibrant colors, high contrast",
                "Cinematic lighting, dramatic shadows"
            ],
            "🎭 Moods": [
                "Mysterious, atmospheric, moody",
                "Cheerful, bright, uplifting",
                "Dark, gothic, dramatic",
                "Peaceful, serene, calm"
            ]
        }
        
        for category, suggestions in categories.items():
            category_action = QAction(category, self)
            category_action.setEnabled(False)
            menu.addAction(category_action)
            
            for suggestion in suggestions:
                action = QAction(f"  {suggestion}", self)
                action.triggered.connect(lambda checked, text=suggestion: self._apply_suggestion(text))
                menu.addAction(action)
            
            menu.addSeparator()
        
        # Random suggestion
        random_action = QAction("🎲 Random Suggestion", self)
        random_action.triggered.connect(self._apply_random_suggestion)
        menu.addAction(random_action)
        
        # Clear prompt
        menu.addSeparator()
        clear_action = QAction("🗑️ Clear Prompt", self)
        clear_action.triggered.connect(self.clear_prompt)
        menu.addAction(clear_action)
        
        # Show menu
        menu.exec(self.magic_btn.mapToGlobal(self.magic_btn.rect().bottomLeft()))
        
    def _apply_suggestion(self, suggestion: str):
        """Apply magic suggestion to prompt"""
        current_text = self.prompt_edit.toPlainText().strip()
        
        if current_text:
            # Add to existing prompt
            new_text = f"{current_text}, {suggestion}"
        else:
            # Set as new prompt
            new_text = suggestion
            
        self.prompt_edit.setPlainText(new_text)
        self._trigger_magic_effect()
        
    def _apply_random_suggestion(self):
        """Apply random magic suggestion"""
        suggestion = random.choice(self.magic_suggestions)
        self._apply_suggestion(suggestion)
        
    def _trigger_magic_effect(self):
        """Visual effect when magic is applied"""
        # Briefly change magic button text
        original_text = self.magic_btn.text()
        self.magic_btn.setText("🎯")
        
        # Reset after short delay
        QTimer.singleShot(500, lambda: self.magic_btn.setText(original_text))
        
    def _on_text_changed(self):
        """Handle text changes"""
        text = self.prompt_edit.toPlainText()
        char_count = len(text)
        self.char_count_label.setText(f"{char_count} characters")
        self.prompt_changed.emit(text)
        
    def get_prompt(self) -> str:
        """Get current prompt text"""
        return self.prompt_edit.toPlainText()
        
    def set_prompt(self, text: str):
        """Set prompt text"""
        self.prompt_edit.setPlainText(text)
        
    def clear_prompt(self):
        """Clear prompt text"""
        self.prompt_edit.clear()
        
    def append_to_prompt(self, text: str):
        """Append text to existing prompt"""
        current = self.get_prompt().strip()
        if current:
            new_text = f"{current}, {text}"
        else:
            new_text = text
        self.set_prompt(new_text)


class NegativePromptWidget(MagicPromptWidget):
    """
    Specialized negative prompt widget with relevant suggestions
    """
    
    def __init__(self, parent=None):
        super().__init__(
            title="Negative Prompt",
            placeholder="Describe what you don't want in the image...",
            parent=parent
        )
        
        # Negative prompt specific suggestions
        self.magic_suggestions = [
            "blurry, low quality, pixelated, compression artifacts",
            "out of focus, motion blur, camera shake",
            "overexposed, underexposed, poor lighting",
            "distorted, deformed, anatomical errors",
            "cropped, cut off, incomplete",
            "text, watermark, signature, copyright",
            "duplicate, multiple, repetitive elements",
            "cartoon, anime, unrealistic (for photorealistic)",
            "noise, grain, digital artifacts",
            "oversaturated, washed out colors"
        ]
        
    def _show_magic_menu(self):
        """Show negative prompt specific magic menu"""
        menu = QMenu(self)
        
        # Negative prompt categories
        categories = {
            "❌ Quality Issues": [
                "blurry, low quality, poor resolution",
                "pixelated, compression artifacts",
                "noise, grain, digital artifacts",
                "overexposed, underexposed"
            ],
            "🚫 Unwanted Elements": [
                "text, watermark, signature",
                "duplicate, multiple copies",
                "cropped, cut off, incomplete",
                "distorted, deformed"
            ],
            "⚠️ Technical Problems": [
                "out of focus, motion blur",
                "poor lighting, bad shadows",
                "oversaturated, washed out",
                "anatomical errors, unrealistic"
            ]
        }
        
        for category, suggestions in categories.items():
            category_action = QAction(category, self)
            category_action.setEnabled(False)
            menu.addAction(category_action)
            
            for suggestion in suggestions:
                action = QAction(f"  {suggestion}", self)
                action.triggered.connect(lambda checked, text=suggestion: self._apply_suggestion(text))
                menu.addAction(action)
            
            menu.addSeparator()
        
        # Random and clear options
        random_action = QAction("🎲 Random Negative Terms", self)
        random_action.triggered.connect(self._apply_random_suggestion)
        menu.addAction(random_action)
        
        menu.addSeparator()
        clear_action = QAction("🗑️ Clear Negative Prompt", self)
        clear_action.triggered.connect(self.clear_prompt)
        menu.addAction(clear_action)
        
        menu.exec(self.magic_btn.mapToGlobal(self.magic_btn.rect().bottomLeft()))