"""
Prompt Memory Manager - Handles prompt hierarchy and user modifications
Ensures user changes take precedence over file-based prompts
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
from loguru import logger
from PySide6.QtCore import QObject, Signal


class PromptMemoryManager(QObject):
    """
    Manages prompt memory with proper hierarchy:
    1. User modifications (highest priority)
    2. File-based prompts (default/fallback)
    """
    
    # Signals
    prompt_changed = Signal(str, str)  # prompt_type, value
    
    def __init__(self):
        super().__init__()
        self._file_prompts = {
            "positive": "",
            "negative": ""
        }
        self._user_prompts = {
            "positive": None,  # None means no user modification
            "negative": None
        }
        self._current_workflow = None
        self._prompt_widgets = {}
        
    def register_prompt_widget(self, prompt_type: str, widget):
        """Register a prompt widget for change tracking"""
        self._prompt_widgets[prompt_type] = widget
        
        # Connect to text changed signal to track user modifications
        if hasattr(widget, 'text_changed'):
            widget.text_changed.connect(lambda: self._on_prompt_modified(prompt_type))
        elif hasattr(widget, 'textChanged'):
            widget.textChanged.connect(lambda: self._on_prompt_modified(prompt_type))
        elif hasattr(widget, 'toPlainText'):
            # For QTextEdit
            widget.textChanged.connect(lambda: self._on_prompt_modified(prompt_type))
            
    def _on_prompt_modified(self, prompt_type: str):
        """Handle prompt modification by user"""
        if prompt_type not in self._prompt_widgets:
            return
            
        widget = self._prompt_widgets[prompt_type]
        
        # Get current text
        if hasattr(widget, 'get_text'):
            current_text = widget.get_text()
        elif hasattr(widget, 'toPlainText'):
            current_text = widget.toPlainText()
        else:
            current_text = widget.text()
            
        # Only mark as user-modified if different from file prompt
        if current_text != self._file_prompts.get(prompt_type, ""):
            self._user_prompts[prompt_type] = current_text
            logger.debug(f"{prompt_type} prompt modified by user")
        else:
            # If user reverted to file prompt, clear modification
            self._user_prompts[prompt_type] = None
            
    def load_workflow_prompts(self, workflow_path: Path, workflow_data: Dict[str, Any]):
        """Load prompts from a workflow file"""
        try:
            self._current_workflow = workflow_path.name
            
            # Extract prompts from workflow
            prompts_found = self._extract_prompts_from_workflow(workflow_data)
            
            # Update file prompts
            if "positive" in prompts_found:
                self._file_prompts["positive"] = prompts_found["positive"]
            if "negative" in prompts_found:
                self._file_prompts["negative"] = prompts_found["negative"]
                
            logger.debug(f"Loaded prompts from workflow: {workflow_path.name}")
            
            # Update UI widgets based on hierarchy
            self._update_prompt_widgets()
            
        except Exception as e:
            logger.error(f"Failed to load workflow prompts: {e}")
            
    def _extract_prompts_from_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract positive and negative prompts from workflow nodes"""
        prompts = {}
        
        try:
            nodes = workflow_data.get("nodes", [])
            
            for node in nodes:
                node_type = node.get("type", "")
                
                # Look for CLIPTextEncode nodes
                if node_type == "CLIPTextEncode":
                    widgets_values = node.get("widgets_values", [])
                    if widgets_values and len(widgets_values) > 0:
                        prompt_text = widgets_values[0]
                        
                        # Try to determine if positive or negative based on node title or connections
                        node_title = node.get("title", "").lower()
                        if "positive" in node_title:
                            prompts["positive"] = prompt_text
                        elif "negative" in node_title:
                            prompts["negative"] = prompt_text
                        else:
                            # If we can't determine, use the first as positive, second as negative
                            if "positive" not in prompts:
                                prompts["positive"] = prompt_text
                            elif "negative" not in prompts:
                                prompts["negative"] = prompt_text
                                
        except Exception as e:
            logger.error(f"Failed to extract prompts from workflow: {e}")
            
        return prompts
        
    def _update_prompt_widgets(self):
        """Update prompt widgets based on memory hierarchy"""
        for prompt_type in ["positive", "negative"]:
            if prompt_type not in self._prompt_widgets:
                logger.warning(f"Prompt widget '{prompt_type}' not registered")
                continue
                
            widget = self._prompt_widgets[prompt_type]
            
            # Get the appropriate prompt based on hierarchy
            prompt_value = self.get_prompt(prompt_type)
            logger.info(f"Updating {prompt_type} prompt widget with: {prompt_value[:50]}...")
            
            # Update widget without triggering modification detection
            try:
                # Temporarily disconnect signal
                if hasattr(widget, 'text_changed'):
                    widget.text_changed.disconnect()
                elif hasattr(widget, 'textChanged'):
                    widget.textChanged.disconnect()
                
                # Update text
                if hasattr(widget, 'set_text'):
                    widget.set_text(prompt_value)
                    logger.debug(f"Used set_text for {prompt_type} prompt")
                elif hasattr(widget, 'setText'):
                    widget.setText(prompt_value)
                    logger.debug(f"Used setText for {prompt_type} prompt")
                elif hasattr(widget, 'setPlainText'):
                    widget.setPlainText(prompt_value)
                    logger.debug(f"Used setPlainText for {prompt_type} prompt")
                else:
                    logger.error(f"Widget for {prompt_type} has no set_text, setText or setPlainText method")
                    
                # Reconnect signal
                if hasattr(widget, 'text_changed'):
                    widget.text_changed.connect(lambda: self._on_prompt_modified(prompt_type))
                elif hasattr(widget, 'textChanged'):
                    widget.textChanged.connect(lambda: self._on_prompt_modified(prompt_type))
                    
            except Exception as e:
                logger.error(f"Failed to update prompt widget: {e}")
                
    def get_prompt(self, prompt_type: str) -> str:
        """Get prompt value based on hierarchy"""
        # User modification takes precedence
        if self._user_prompts.get(prompt_type) is not None:
            return self._user_prompts[prompt_type]
            
        # Otherwise use file prompt
        return self._file_prompts.get(prompt_type, "")
        
    def set_prompt(self, prompt_type: str, value: str, is_user_edit: bool = True):
        """Set prompt value"""
        if is_user_edit:
            self._user_prompts[prompt_type] = value
        else:
            self._file_prompts[prompt_type] = value
            
        self.prompt_changed.emit(prompt_type, value)
        
    def clear_user_modifications(self):
        """Clear all user modifications and revert to file prompts"""
        self._user_prompts = {"positive": None, "negative": None}
        self._update_prompt_widgets()
        
    def reload_same_workflow(self):
        """Called when the same workflow is explicitly reloaded"""
        # Clear user modifications to allow file prompts to take effect
        self.clear_user_modifications()
        logger.info("Cleared user prompt modifications for workflow reload")
        
    def get_memory_state(self) -> Dict[str, Any]:
        """Get the current memory state for debugging"""
        return {
            "current_workflow": self._current_workflow,
            "file_prompts": self._file_prompts.copy(),
            "user_prompts": self._user_prompts.copy(),
            "active_prompts": {
                "positive": self.get_prompt("positive"),
                "negative": self.get_prompt("negative")
            }
        }