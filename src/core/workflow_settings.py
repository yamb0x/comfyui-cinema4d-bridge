"""
Workflow settings persistence manager
Saves and loads last used workflows for each tab
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class WorkflowSettings:
    """Manages workflow selection persistence across app sessions"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.settings_file = config_dir / "workflow_settings.json"
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load workflow settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load workflow settings: {e}")
        
        # Default settings
        return {
            "image_generation": {
                "last_workflow": "generate_images.json",
                "recent_workflows": []
            },
            "model_3d_generation": {
                "last_workflow": "generate_3D_withUVs_09-06-2025.json",
                "recent_workflows": []
            },
            "texture_generation": {
                "last_workflow": "3DModel_texturing_juggernautXL_v01.json",
                "recent_workflows": []
            }
        }
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logger.debug("Workflow settings saved")
        except Exception as e:
            logger.error(f"Failed to save workflow settings: {e}")
    
    def get_last_workflow(self, tab: str) -> Optional[str]:
        """Get last used workflow for a tab"""
        return self.settings.get(tab, {}).get("last_workflow")
    
    def set_last_workflow(self, tab: str, workflow: str):
        """Set last used workflow for a tab"""
        if tab not in self.settings:
            self.settings[tab] = {"last_workflow": "", "recent_workflows": []}
        
        self.settings[tab]["last_workflow"] = workflow
        
        # Update recent workflows list
        recent = self.settings[tab].get("recent_workflows", [])
        if workflow in recent:
            recent.remove(workflow)
        recent.insert(0, workflow)
        # Keep only last 10
        self.settings[tab]["recent_workflows"] = recent[:10]
        
        self.save_settings()
    
    def get_recent_workflows(self, tab: str) -> list:
        """Get list of recently used workflows for a tab"""
        return self.settings.get(tab, {}).get("recent_workflows", [])