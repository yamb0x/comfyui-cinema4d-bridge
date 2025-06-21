"""
Application configuration management
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from loguru import logger


class PathConfig(BaseModel):
    """Path configuration for external applications"""
    comfyui_path: Path = Field(
        default=Path("D:/Comfy3D_WinPortable"),
        description="Path to ComfyUI installation"
    )
    cinema4d_path: Path = Field(
        default=Path("C:/Program Files/Maxon Cinema 4D 2024"),
        description="Path to Cinema4D installation"
    )
    
    @validator("comfyui_path", "cinema4d_path")
    def validate_path_exists(cls, v):
        if not v.exists():
            logger.warning(f"Path does not exist: {v}")
        return v


class WorkflowConfig(BaseModel):
    """Workflow configuration"""
    image_workflow: str = "generate_images.json"
    model_3d_workflow: str = "generate_3D.json"
    default_image_params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "resolution": [1024, 1024],
            "sampling_steps": 20,
            "cfg_scale": 7.0,
            "sampler": "euler",
            "scheduler": "normal"
        }
    )
    default_3d_params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "mesh_density": "high",
            "texture_resolution": 2048,
            "normal_map": True,
            "optimization": "balanced"
        }
    )


class MCPConfig(BaseModel):
    """MCP (Model Context Protocol) configuration"""
    comfyui_server_url: str = "http://127.0.0.1:8188"
    comfyui_websocket_url: str = "ws://127.0.0.1:8188/ws"
    cinema4d_port: int = 54321
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class UIConfig(BaseModel):
    """UI configuration"""
    theme: str = "dark"
    window_size: tuple[int, int] = (1400, 900)
    console_max_lines: int = 1000
    preview_thumbnail_size: int = 256
    grid_columns: int = 4
    enable_3d_preview: bool = True


class AppConfig(BaseSettings):
    """Main application configuration"""
    paths: PathConfig = Field(default_factory=PathConfig)
    workflows: WorkflowConfig = Field(default_factory=WorkflowConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    
    # Project settings  
    base_dir: Path = Path("D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d")
    workflows_dir: Path = Field(default_factory=lambda: Path("D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d/workflows"))
    images_dir: Path = Field(default_factory=lambda: Path("D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d/images"))
    models_3d_dir: Path = Field(default_factory=lambda: Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D"))
    local_models_3d_dir: Path = Field(default_factory=lambda: Path("D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d/3d_models"))
    config_dir: Path = Field(default_factory=lambda: Path("D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d/config"))
    
    # Viewer settings
    texture_viewer_path: Path = Field(default_factory=lambda: Path("viewer/run_final_viewer.bat"))
    
    # Computed properties for commonly used paths
    @property
    def textured_models_dir(self) -> Path:
        """Get textured models directory path"""
        return Path(self.models_3d_dir) / "textured"
    
    # Recent projects
    recent_projects: list[str] = Field(default_factory=list)
    max_recent_projects: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.base_dir,
            self.workflows_dir,
            self.images_dir,
            self.local_models_3d_dir,  # Ensure local models dir exists
            self.config_dir,
            self.base_dir / "src",
            self.base_dir / "ui",
        ]
        
        # Note: models_3d_dir points to ComfyUI output, which we don't create
        # but should monitor if it exists
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def add_recent_project(self, project_path: str):
        """Add a project to recent projects list"""
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
        self.recent_projects.insert(0, project_path)
        if len(self.recent_projects) > self.max_recent_projects:
            self.recent_projects = self.recent_projects[:self.max_recent_projects]
        self.save()
    
    def save(self):
        """Save configuration to file"""
        config_file = self.config_dir / "app_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, "w") as f:
            json.dump(self.dict(), f, indent=2, default=str)
        logger.info(f"Configuration saved to {config_file}")
    
    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration from file or create default"""
        config_file = Path("D:/Yambo Studio Dropbox/Admin/_studio-dashboard-app-dev/comfy-to-c4d/config/app_config.json")
        
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                config = cls(**data)
                logger.info(f"Configuration loaded from {config_file}")
                logger.info(f"Loaded models_3d_dir: {config.models_3d_dir}")
                logger.info(f"Loaded local_models_3d_dir: {config.local_models_3d_dir}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                config = cls()
        else:
            config = cls()
            logger.info("Using default configuration")
        
        # Ensure directories exist
        config.ensure_directories()
        
        # Save configuration
        config.save()
        
        return config
    
    def validate_external_apps(self) -> Dict[str, bool]:
        """Validate external application paths"""
        return {
            "comfyui": self.paths.comfyui_path.exists(),
            "cinema4d": self.paths.cinema4d_path.exists()
        }