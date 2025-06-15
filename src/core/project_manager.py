"""
Project file management system for ComfyUI to Cinema4D Bridge
Handles saving, loading, and managing project files (.c2c format)
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger


class ProjectManager:
    """Manages project files and recent projects"""
    
    PROJECT_VERSION = "1.0"
    PROJECT_EXTENSION = ".c2c"
    
    def __init__(self, config):
        self.config = config
        self.current_project_path: Optional[Path] = None
        self.is_modified = False
        self.recent_projects: List[Path] = []
        self._load_recent_projects()
        
    def create_new_project(self) -> Dict[str, Any]:
        """Create a new empty project"""
        project = {
            "version": self.PROJECT_VERSION,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            
            "generation_settings": {
                "image": {
                    "workflow": "",
                    "prompt": "",
                    "negative_prompt": "",
                    "checkpoint": "",
                    "loras": [],
                    "sampler": "euler",
                    "steps": 20,
                    "cfg": 7.5,
                    "seed": -1,
                    "batch_size": 1,
                    "width": 512,
                    "height": 512
                },
                "model_3d": {
                    "workflow": "",
                    "source_image": "",
                    "hy3d_settings": {
                        "resolution": 512,
                        "mesh_quality": "high",
                        "texture_resolution": 2048
                    },
                    "postprocess": {
                        "smoothing": 0.5,
                        "decimation": 0.8
                    },
                    "camera_config": {
                        "fov": 60,
                        "distance": 2.5
                    }
                }
            },
            
            "scene_assembly": {
                "nlp_prompt": "",
                "objects": [],
                "hierarchy": [],
                "materials": []
            },
            
            "assets": {
                "images": [],
                "models": [],
                "textures": []
            },
            
            "ui_state": {
                "active_tab": 0,
                "image_generation_tab": 0,
                "model_generation_tab": 0,
                "scene_assembly_expanded": []
            }
        }
        
        self.current_project_path = None
        self.is_modified = False
        logger.info("Created new project")
        
        return project
        
    def save_project(self, project_data: Dict[str, Any], file_path: Optional[Path] = None) -> bool:
        """Save project to file"""
        try:
            if file_path is None:
                file_path = self.current_project_path
                
            if file_path is None:
                logger.error("No file path specified for saving")
                return False
                
            # Ensure correct extension
            if not str(file_path).endswith(self.PROJECT_EXTENSION):
                file_path = Path(str(file_path) + self.PROJECT_EXTENSION)
                
            # Update modified timestamp
            project_data["modified"] = datetime.now().isoformat()
            
            # Create backup if file exists
            if file_path.exists():
                backup_path = file_path.with_suffix(f".bak{int(time.time())}")
                file_path.rename(backup_path)
                logger.debug(f"Created backup: {backup_path}")
            
            # Save project
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
                
            self.current_project_path = file_path
            self.is_modified = False
            self._add_to_recent_projects(file_path)
            
            logger.info(f"Project saved to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False
            
    def load_project(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load project from file"""
        try:
            if not file_path.exists():
                logger.error(f"Project file not found: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            # Validate version
            version = project_data.get("version", "0.0")
            if version != self.PROJECT_VERSION:
                logger.warning(f"Project version mismatch: {version} vs {self.PROJECT_VERSION}")
                # In the future, add migration logic here
                
            self.current_project_path = file_path
            self.is_modified = False
            self._add_to_recent_projects(file_path)
            
            logger.info(f"Project loaded from: {file_path}")
            return project_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid project file format: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return None
            
    def get_project_info(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Get basic project information without fully loading it"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read only the first few lines to get basic info
                content = f.read(1024)  # Read first 1KB
                
            # Parse partial JSON to get basic info
            import re
            version_match = re.search(r'"version":\s*"([^"]+)"', content)
            created_match = re.search(r'"created":\s*"([^"]+)"', content)
            modified_match = re.search(r'"modified":\s*"([^"]+)"', content)
            
            return {
                "path": str(file_path),
                "name": file_path.stem,
                "version": version_match.group(1) if version_match else "Unknown",
                "created": created_match.group(1) if created_match else "Unknown",
                "modified": modified_match.group(1) if modified_match else "Unknown",
                "size": f"{file_path.stat().st_size / 1024:.1f} KB"
            }
            
        except Exception as e:
            logger.error(f"Failed to get project info: {e}")
            return None
            
    def _load_recent_projects(self):
        """Load recent projects list from config"""
        try:
            recent_file = self.config.config_dir / "recent_projects.json"
            if recent_file.exists():
                with open(recent_file, 'r') as f:
                    data = json.load(f)
                    self.recent_projects = [Path(p) for p in data.get("projects", [])]
                    # Filter out non-existent files
                    self.recent_projects = [p for p in self.recent_projects if p.exists()]
        except Exception as e:
            logger.error(f"Failed to load recent projects: {e}")
            self.recent_projects = []
            
    def _save_recent_projects(self):
        """Save recent projects list to config"""
        try:
            recent_file = self.config.config_dir / "recent_projects.json"
            data = {
                "projects": [str(p) for p in self.recent_projects[:self.config.max_recent_projects]]
            }
            with open(recent_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recent projects: {e}")
            
    def _add_to_recent_projects(self, file_path: Path):
        """Add project to recent projects list"""
        # Remove if already in list
        if file_path in self.recent_projects:
            self.recent_projects.remove(file_path)
            
        # Add to beginning
        self.recent_projects.insert(0, file_path)
        
        # Limit to max recent projects
        self.recent_projects = self.recent_projects[:self.config.max_recent_projects]
        
        # Save list
        self._save_recent_projects()
        
    def get_recent_projects(self) -> List[Dict[str, str]]:
        """Get list of recent projects with info"""
        recent = []
        for path in self.recent_projects:
            info = self.get_project_info(path)
            if info:
                recent.append(info)
        return recent
        
    def clear_recent_projects(self):
        """Clear recent projects list"""
        self.recent_projects = []
        self._save_recent_projects()
        
    def export_project_assets(self, project_data: Dict[str, Any], export_dir: Path) -> bool:
        """Export all project assets to a directory"""
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (export_dir / "images").mkdir(exist_ok=True)
            (export_dir / "models").mkdir(exist_ok=True)
            (export_dir / "textures").mkdir(exist_ok=True)
            
            # Copy assets
            for asset_type, asset_list in project_data.get("assets", {}).items():
                for asset_path in asset_list:
                    src = Path(asset_path)
                    if src.exists():
                        dst = export_dir / asset_type / src.name
                        import shutil
                        shutil.copy2(src, dst)
                        logger.debug(f"Exported {asset_path} to {dst}")
                        
            # Save project file
            project_file = export_dir / f"{export_dir.name}{self.PROJECT_EXTENSION}"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Project exported to: {export_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export project: {e}")
            return False