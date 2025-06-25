"""
Config adapter to make SimpleConfig compatible with the original AppConfig interface
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .config_simple import SimpleConfig


@dataclass
class PathConfigAdapter:
    """Adapter for PathConfig"""
    comfyui_path: Path
    cinema4d_path: Path


@dataclass
class WorkflowConfigAdapter:
    """Adapter for WorkflowConfig"""
    image_workflow: str = "generate_images.json"
    model_3d_workflow: str = "generate_3D.json"
    default_image_params: Dict[str, Any] = None
    default_3d_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.default_image_params is None:
            self.default_image_params = {
                "resolution": [1024, 1024],
                "sampling_steps": 20,
                "cfg_scale": 7.0,
                "sampler": "euler",
                "scheduler": "normal"
            }
        if self.default_3d_params is None:
            self.default_3d_params = {
                "mesh_density": "high",
                "texture_resolution": 2048,
                "normal_map": True,
                "optimization": "balanced"
            }


@dataclass
class MCPConfigAdapter:
    """Adapter for MCPConfig"""
    comfyui_server_url: str
    comfyui_websocket_url: str
    cinema4d_host: str
    cinema4d_port: int
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class UIConfigAdapter:
    """Adapter for UIConfig"""
    theme: str = "dark"
    window_size: tuple = (1400, 900)
    console_max_lines: int = 1000
    preview_thumbnail_size: int = 256
    grid_columns: int = 4
    enable_3d_preview: bool = True


class AppConfigAdapter:
    """Adapter to make SimpleConfig compatible with AppConfig interface"""
    
    def __init__(self, simple_config: SimpleConfig):
        self._config = simple_config
        
        # Create sub-configs
        self.paths = PathConfigAdapter(
            comfyui_path=simple_config.comfyui_path,
            cinema4d_path=simple_config.cinema4d_path
        )
        
        self.workflows = WorkflowConfigAdapter()
        
        self.mcp = MCPConfigAdapter(
            comfyui_server_url=simple_config.comfyui_server_url,
            comfyui_websocket_url=simple_config.comfyui_websocket_url,
            cinema4d_host=simple_config.cinema4d_mcp_host,
            cinema4d_port=simple_config.cinema4d_mcp_port
        )
        
        self.ui = UIConfigAdapter()
        
        # Direct attributes
        self.base_dir = simple_config.base_dir
        self.workflows_dir = simple_config.workflows_dir
        self.images_dir = simple_config.images_dir
        self.models_3d_dir = simple_config.models_3d_dir
        self.config_dir = simple_config.config_dir
        self.loras_dir = simple_config.loras_dir
        self.checkpoints_dir = simple_config.checkpoints_dir
        self.vae_dir = simple_config.vae_dir
        self.recent_projects: List[str] = []
        self.max_recent_projects = simple_config.max_recent_projects
    
    def ensure_directories(self):
        """Ensure all directories exist"""
        self._config.ensure_directories()
    
    def save(self):
        """Save configuration (no-op for now)"""
        pass
    
    def add_recent_project(self, project_path: str):
        """Add a project to recent projects list"""
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
        self.recent_projects.insert(0, project_path)
        if len(self.recent_projects) > self.max_recent_projects:
            self.recent_projects = self.recent_projects[:self.max_recent_projects]
    
    def validate_external_apps(self) -> Dict[str, bool]:
        """Validate external application paths"""
        return self._config.validate_paths()
    
    @classmethod
    def load(cls) -> "AppConfigAdapter":
        """Load configuration"""
        simple_config = SimpleConfig.load()
        return cls(simple_config)


# Make it available as AppConfig for compatibility
AppConfig = AppConfigAdapter