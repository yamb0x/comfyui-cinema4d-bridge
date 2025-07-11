"""
Magic Prompts Database Management Dialog
Allows users to manage positive and negative prompt templates
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QLabel,
    QLineEdit, QMessageBox, QSplitter, QGroupBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from loguru import logger


class MagicPromptsDialog(QDialog):
    """Dialog for managing magic prompt templates database"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Magic Prompts Database")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(800, 600)
        
        # Data file paths
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.positive_file = self.config_dir / "magic_prompts_positive.json"
        self.negative_file = self.config_dir / "magic_prompts_negative.json"
        
        # Initialize data
        self.positive_prompts: Dict[str, str] = {}
        self.negative_prompts: Dict[str, str] = {}
        
        self._setup_ui()
        self._load_prompts()
        self._populate_lists()
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header_label = QLabel("Magic Prompts Database")
        header_label.setObjectName("section_title")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        header_label.setFont(font)
        layout.addWidget(header_label)
        
        # Tab widget for positive/negative
        self.tab_widget = QTabWidget()
        
        # Positive prompts tab
        self.positive_tab = self._create_prompts_tab("positive")
        self.tab_widget.addTab(self.positive_tab, "✅ Positive Prompts")
        
        # Negative prompts tab
        self.negative_tab = self._create_prompts_tab("negative")
        self.tab_widget.addTab(self.negative_tab, "❌ Negative Prompts")
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _create_prompts_tab(self, prompt_type: str) -> QWidget:
        """Create tab for managing prompts of specific type"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - List of prompts
        left_panel = QGroupBox(f"{prompt_type.title()} Prompt Templates")
        left_layout = QVBoxLayout(left_panel)
        
        # Add button
        add_btn = QPushButton(f"➕ Add New {prompt_type.title()} Template")
        add_btn.clicked.connect(lambda: self._add_new_template(prompt_type))
        left_layout.addWidget(add_btn)
        
        # List widget
        list_widget = QListWidget()
        list_widget.currentItemChanged.connect(lambda: self._on_template_selected(prompt_type))
        left_layout.addWidget(list_widget)
        
        # Delete button
        delete_btn = QPushButton(f"🗑️ Delete Selected")
        delete_btn.clicked.connect(lambda: self._delete_template(prompt_type))
        left_layout.addWidget(delete_btn)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Edit template
        right_panel = QGroupBox("Template Editor")
        right_layout = QVBoxLayout(right_panel)
        
        # Template name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Template Name:"))
        name_edit = QLineEdit()
        name_edit.textChanged.connect(lambda: self._on_template_edited(prompt_type))
        name_layout.addWidget(name_edit)
        right_layout.addLayout(name_layout)
        
        # Template content
        content_label = QLabel("Template Content:")
        right_layout.addWidget(content_label)
        
        content_edit = QTextEdit()
        content_edit.setPlaceholderText(f"Enter your {prompt_type} prompt template here...")
        content_edit.textChanged.connect(lambda: self._on_template_edited(prompt_type))
        right_layout.addWidget(content_edit)
        
        # Save button
        save_btn = QPushButton(f"💾 Save Template")
        save_btn.clicked.connect(lambda: self._save_template(prompt_type))
        right_layout.addWidget(save_btn)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Store references
        setattr(self, f"{prompt_type}_list", list_widget)
        setattr(self, f"{prompt_type}_name", name_edit)
        setattr(self, f"{prompt_type}_content", content_edit)
        setattr(self, f"{prompt_type}_save_btn", save_btn)
        
        return tab
        
    def _load_prompts(self):
        """Load prompts from JSON files"""
        # Load positive prompts
        if self.positive_file.exists():
            try:
                with open(self.positive_file, 'r', encoding='utf-8') as f:
                    self.positive_prompts = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load positive prompts: {e}")
        else:
            # Create default positive prompts
            self.positive_prompts = {
                "Photorealistic Portrait": "professional photo, sharp focus, detailed, high quality, realistic lighting, 8k resolution",
                "Fantasy Landscape": "epic fantasy landscape, mystical atmosphere, dramatic lighting, highly detailed, concept art style",
                "Sci-Fi Scene": "futuristic setting, advanced technology, cyberpunk aesthetic, neon lighting, highly detailed",
                "Artistic Style": "masterpiece, best quality, highly detailed, artistic composition, perfect lighting"
            }
            
        # Load negative prompts
        if self.negative_file.exists():
            try:
                with open(self.negative_file, 'r', encoding='utf-8') as f:
                    self.negative_prompts = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load negative prompts: {e}")
        else:
            # Create default negative prompts
            self.negative_prompts = {
                "General Quality Issues": "blurry, low quality, pixelated, jpeg artifacts, oversaturated",
                "Deformed Features": "deformed, disfigured, bad anatomy, extra limbs, missing limbs, mutated",
                "Poor Composition": "cropped, out of frame, duplicate, poorly composed, bad framing",
                "Technical Issues": "noise, grain, low resolution, watermark, signature, text"
            }
    
    def _populate_lists(self):
        """Populate the list widgets with templates"""
        # Populate positive list
        self.positive_list.clear()
        for name in sorted(self.positive_prompts.keys()):
            item = QListWidgetItem(name)
            self.positive_list.addItem(item)
            
        # Populate negative list
        self.negative_list.clear()
        for name in sorted(self.negative_prompts.keys()):
            item = QListWidgetItem(name)
            self.negative_list.addItem(item)
    
    def _on_template_selected(self, prompt_type: str):
        """Handle template selection"""
        list_widget = getattr(self, f"{prompt_type}_list")
        name_edit = getattr(self, f"{prompt_type}_name")
        content_edit = getattr(self, f"{prompt_type}_content")
        
        current_item = list_widget.currentItem()
        if current_item:
            template_name = current_item.text()
            prompts_dict = getattr(self, f"{prompt_type}_prompts")
            
            name_edit.setText(template_name)
            content_edit.setPlainText(prompts_dict.get(template_name, ""))
    
    def _on_template_edited(self, prompt_type: str):
        """Handle template editing"""
        # Enable save button when content is edited
        save_btn = getattr(self, f"{prompt_type}_save_btn")
        save_btn.setEnabled(True)
    
    def _add_new_template(self, prompt_type: str):
        """Add new template"""
        name_edit = getattr(self, f"{prompt_type}_name")
        content_edit = getattr(self, f"{prompt_type}_content")
        
        # Clear the editor for new template
        name_edit.setText("New Template")
        content_edit.setPlainText("")
        name_edit.selectAll()
        name_edit.setFocus()
    
    def _save_template(self, prompt_type: str):
        """Save current template"""
        name_edit = getattr(self, f"{prompt_type}_name")
        content_edit = getattr(self, f"{prompt_type}_content")
        save_btn = getattr(self, f"{prompt_type}_save_btn")
        
        template_name = name_edit.text().strip()
        template_content = content_edit.toPlainText().strip()
        
        if not template_name:
            QMessageBox.warning(self, "Warning", "Please enter a template name.")
            return
            
        if not template_content:
            QMessageBox.warning(self, "Warning", "Please enter template content.")
            return
        
        # Save to data
        prompts_dict = getattr(self, f"{prompt_type}_prompts")
        prompts_dict[template_name] = template_content
        
        # Refresh list
        self._populate_lists()
        
        # Select the saved item
        list_widget = getattr(self, f"{prompt_type}_list")
        for i in range(list_widget.count()):
            if list_widget.item(i).text() == template_name:
                list_widget.setCurrentRow(i)
                break
        
        save_btn.setEnabled(False)
        logger.info(f"Saved {prompt_type} template: {template_name}")
    
    def _delete_template(self, prompt_type: str):
        """Delete selected template"""
        list_widget = getattr(self, f"{prompt_type}_list")
        current_item = list_widget.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a template to delete.")
            return
        
        template_name = current_item.text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete the template '{template_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from data
            prompts_dict = getattr(self, f"{prompt_type}_prompts")
            if template_name in prompts_dict:
                del prompts_dict[template_name]
            
            # Refresh list
            self._populate_lists()
            
            # Clear editor
            name_edit = getattr(self, f"{prompt_type}_name")
            content_edit = getattr(self, f"{prompt_type}_content")
            name_edit.clear()
            content_edit.clear()
            
            logger.info(f"Deleted {prompt_type} template: {template_name}")
    
    def accept(self):
        """Save data and close dialog"""
        try:
            # Save positive prompts
            with open(self.positive_file, 'w', encoding='utf-8') as f:
                json.dump(self.positive_prompts, f, indent=2, ensure_ascii=False)
            
            # Save negative prompts
            with open(self.negative_file, 'w', encoding='utf-8') as f:
                json.dump(self.negative_prompts, f, indent=2, ensure_ascii=False)
            
            logger.info("Magic prompts database saved successfully")
            super().accept()
            
        except Exception as e:
            logger.error(f"Failed to save magic prompts database: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save database:\\n{e}")