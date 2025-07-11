"""
Magic Prompts Selector Dialog
Quick selection dialog for inserting prompt templates
"""

import json
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QTextEdit, QDialogButtonBox, QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from loguru import logger


class MagicPromptsSelector(QDialog):
    """Quick selector dialog for magic prompt templates"""
    
    def __init__(self, prompt_type: str, parent=None):
        super().__init__(parent)
        self.prompt_type = prompt_type
        self.selected_template = ""
        
        self.setWindowTitle(f"Select {prompt_type.title()} Magic Prompt")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(600, 400)
        
        # Data file paths
        self.config_dir = Path("config")
        self.prompts_file = self.config_dir / f"magic_prompts_{prompt_type}.json"
        
        # Load prompts
        self.prompts: Dict[str, str] = {}
        self._load_prompts()
        
        self._setup_ui()
        self._populate_list()
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        emoji = "✅" if self.prompt_type == "positive" else "❌"
        header_label = QLabel(f"{emoji} Select {self.prompt_type.title()} Prompt Template")
        header_label.setObjectName("section_title")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header_label.setFont(font)
        layout.addWidget(header_label)
        
        # Main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Template list
        left_panel = QVBoxLayout()
        
        list_label = QLabel("Available Templates:")
        left_panel.addWidget(list_label)
        
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        self.template_list.itemDoubleClicked.connect(self._on_template_double_clicked)
        left_panel.addWidget(self.template_list)
        
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        splitter.addWidget(left_widget)
        
        # Right panel - Preview
        right_panel = QVBoxLayout()
        
        preview_label = QLabel("Template Preview:")
        right_panel.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select a template to preview its content...")
        self.preview_text.setMaximumHeight(200)
        right_panel.addWidget(self.preview_text)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([250, 350])
        layout.addWidget(splitter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Open database button
        database_btn = QPushButton("📝 Manage Database")
        database_btn.clicked.connect(self._open_database_manager)
        button_layout.addWidget(database_btn)
        
        button_layout.addStretch()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        
        # Store button box for enabling/disabling OK
        self.button_box = button_box
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        
    def _load_prompts(self):
        """Load prompts from JSON file"""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {self.prompt_type} prompts: {e}")
        else:
            # Create default prompts if file doesn't exist
            if self.prompt_type == "positive":
                self.prompts = {
                    "Photorealistic Portrait": "professional photo, sharp focus, detailed, high quality, realistic lighting, 8k resolution",
                    "Fantasy Landscape": "epic fantasy landscape, mystical atmosphere, dramatic lighting, highly detailed, concept art style",
                    "Sci-Fi Scene": "futuristic setting, advanced technology, cyberpunk aesthetic, neon lighting, highly detailed",
                    "Artistic Style": "masterpiece, best quality, highly detailed, artistic composition, perfect lighting"
                }
            else:  # negative
                self.prompts = {
                    "General Quality Issues": "blurry, low quality, pixelated, jpeg artifacts, oversaturated",
                    "Deformed Features": "deformed, disfigured, bad anatomy, extra limbs, missing limbs, mutated",
                    "Poor Composition": "cropped, out of frame, duplicate, poorly composed, bad framing",
                    "Technical Issues": "noise, grain, low resolution, watermark, signature, text"
                }
            
            # Save default prompts
            self._save_prompts()
    
    def _save_prompts(self):
        """Save prompts to JSON file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save {self.prompt_type} prompts: {e}")
    
    def _populate_list(self):
        """Populate the template list"""
        self.template_list.clear()
        
        if not self.prompts:
            item = QListWidgetItem("No templates available")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.template_list.addItem(item)
            return
        
        for name in sorted(self.prompts.keys()):
            item = QListWidgetItem(name)
            self.template_list.addItem(item)
    
    def _on_template_selected(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        """Handle template selection"""
        if current_item and current_item.text() in self.prompts:
            template_name = current_item.text()
            template_content = self.prompts[template_name]
            
            self.preview_text.setPlainText(template_content)
            self.selected_template = template_content
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.preview_text.clear()
            self.selected_template = ""
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def _on_template_double_clicked(self, item: QListWidgetItem):
        """Handle double-click to immediately select and close"""
        if item and item.text() in self.prompts:
            self.selected_template = self.prompts[item.text()]
            self.accept()
    
    def _open_database_manager(self):
        """Open the full database manager"""
        try:
            from ui.magic_prompts_dialog import MagicPromptsDialog
            dialog = MagicPromptsDialog(self)
            if dialog.exec() == QDialog.Accepted:
                # Reload prompts after potential changes
                self._load_prompts()
                self._populate_list()
        except Exception as e:
            logger.error(f"Failed to open database manager: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open database manager:\\n{e}")
    
    def get_selected_template(self) -> str:
        """Get the selected template content"""
        return self.selected_template