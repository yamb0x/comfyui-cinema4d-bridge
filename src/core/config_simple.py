"""
Simplified configuration management
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class SimpleConfig:
    """Simple configuration class that works with .env files"""
    
    # Paths
    comfyui_path: Path
    cinema4d_path: Path
    base_dir: Path
    
    # ComfyUI settings
    comfyui_server_url: str = "http://localhost:8188"
    comfyui_websocket_url: str = "ws://localhost:8188/ws"
    
    # Cinema4D settings
    cinema4d_mcp_host: str = "localhost"
    cinema4d_mcp_port: int = 5000
    
    # Application settings
    log_level: str = "INFO"
    file_monitor_delay: float = 1.0
    auto_save_interval: int = 300
    max_recent_projects: int = 10
    
    # Directories (computed)
    workflows_dir: Optional[Path] = None
    images_dir: Optional[Path] = None
    models_3d_dir: Optional[Path] = None
    config_dir: Optional[Path] = None
    logs_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Initialize computed paths"""
        # Convert string paths to Path objects
        if isinstance(self.comfyui_path, str):
            self.comfyui_path = Path(self.comfyui_path.strip('"'))
        if isinstance(self.cinema4d_path, str):
            self.cinema4d_path = Path(self.cinema4d_path.strip('"'))
        if isinstance(self.base_dir, str):
            self.base_dir = Path(self.base_dir)
            
        # Set default directories
        if self.workflows_dir is None:
            self.workflows_dir = self.base_dir / "workflows"
        if self.images_dir is None:
            self.images_dir = self.base_dir / "images"
        if self.models_3d_dir is None:
            self.models_3d_dir = self.base_dir / "3D" / "Hy3D"
        if self.config_dir is None:
            self.config_dir = self.base_dir / "config"
        if self.logs_dir is None:
            self.logs_dir = self.base_dir / "logs"
    
    def ensure_directories(self):
        """Ensure all directories exist"""
        dirs = [
            self.workflows_dir,
            self.images_dir,
            self.models_3d_dir,
            self.config_dir,
            self.logs_dir,
            self.base_dir / "exports",
            self.base_dir / "scripts" / "c4d",
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load(cls) -> "SimpleConfig":
        """Load configuration from .env file"""
        # Get base directory
        base_dir = Path(__file__).parent.parent.parent
        env_file = base_dir / ".env"
        
        # Load .env file
        if env_file.exists():
            load_dotenv(env_file)
        
        # Create config from environment variables
        config = cls(
            comfyui_path=os.getenv("COMFYUI_PATH", "D:/Comfy3D_WinPortable"),
            cinema4d_path=os.getenv("CINEMA4D_PATH", "C:/Program Files/Maxon Cinema 4D 2024"),
            base_dir=base_dir,
            comfyui_server_url=os.getenv("COMFYUI_SERVER_URL", "http://localhost:8188"),
            comfyui_websocket_url=os.getenv("COMFYUI_WEBSOCKET_URL", "ws://localhost:8188/ws"),
            cinema4d_mcp_host=os.getenv("CINEMA4D_MCP_HOST", "localhost"),
            cinema4d_mcp_port=int(os.getenv("CINEMA4D_MCP_PORT", "5000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            file_monitor_delay=float(os.getenv("FILE_MONITOR_DELAY", "1.0")),
            auto_save_interval=int(os.getenv("AUTO_SAVE_INTERVAL", "300")),
            max_recent_projects=int(os.getenv("MAX_RECENT_PROJECTS", "10")),
        )
        
        # Ensure directories exist
        config.ensure_directories()
        
        return config
    
    def validate_paths(self) -> dict:
        """Validate that required paths exist"""
        return {
            "comfyui": self.comfyui_path.exists(),
            "cinema4d": self.cinema4d_path.exists(),
            "workflows_dir": self.workflows_dir.exists(),
            "base_dir": self.base_dir.exists(),
        }


# For backward compatibility
AppConfig = SimpleConfig