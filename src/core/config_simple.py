"""
Simplified configuration management with .env support
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
    cinema4d_scripts_dir: Optional[Path] = None
    checkpoints_dir: Optional[Path] = None
    loras_dir: Optional[Path] = None
    vae_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Initialize computed paths"""
        # Convert string paths to Path objects
        if isinstance(self.comfyui_path, str):
            self.comfyui_path = Path(self.comfyui_path.strip('"'))
        if isinstance(self.cinema4d_path, str):
            self.cinema4d_path = Path(self.cinema4d_path.strip('"'))
        if isinstance(self.base_dir, str):
            self.base_dir = Path(self.base_dir)
            
        # Set default directories using environment variables
        if self.workflows_dir is None:
            self.workflows_dir = Path(os.getenv("COMFYUI_WORKFLOWS", str(self.base_dir / "workflows")))
        if self.images_dir is None:
            self.images_dir = Path(os.getenv("GENERATED_IMAGES_DIR", str(self.base_dir / "images")))
        if self.models_3d_dir is None:
            self.models_3d_dir = Path(os.getenv("COMFYUI_3D_OUTPUT_DIR", str(self.comfyui_path / "output" / "3D")))
        if self.config_dir is None:
            self.config_dir = self.base_dir / "config"
        if self.logs_dir is None:
            self.logs_dir = Path(os.getenv("LOGS_DIR", str(self.base_dir / "logs")))
        if self.cinema4d_scripts_dir is None:
            self.cinema4d_scripts_dir = Path(os.getenv("CINEMA4D_PYTHON_SCRIPTS", str(self.base_dir / "scripts")))
        if self.checkpoints_dir is None:
            self.checkpoints_dir = Path(os.getenv("COMFYUI_CHECKPOINTS", str(self.comfyui_path / "models" / "checkpoints")))
        if self.loras_dir is None:
            self.loras_dir = Path(os.getenv("COMFYUI_LORAS", str(self.comfyui_path / "models" / "loras")))
        if self.vae_dir is None:
            self.vae_dir = Path(os.getenv("COMFYUI_VAE", str(self.comfyui_path / "models" / "vae")))
    
    def ensure_directories(self):
        """Ensure all directories exist"""
        dirs = [
            self.workflows_dir,
            self.images_dir,
            self.models_3d_dir,
            self.config_dir,
            self.logs_dir,
            self.base_dir / "exports",
            self.cinema4d_scripts_dir,
        ]
        for dir_path in dirs:
            if dir_path:
                dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load(cls) -> "SimpleConfig":
        """Load configuration from .env file"""
        # Get base directory
        base_dir = Path(__file__).parent.parent.parent
        env_file = base_dir / ".env"
        
        # Load .env file if it exists
        if env_file.exists():
            load_dotenv(env_file)
            print(f"Loaded environment from: {env_file}")
        else:
            print(f"No .env file found at: {env_file}")
            print("Using default values. Copy .env.example to .env and update paths.")
        
        # Get project root from env or use base_dir
        project_root = os.getenv("PROJECT_ROOT", str(base_dir))
        
        # Create config from environment variables matching our .env.example
        config = cls(
            comfyui_path=Path(os.getenv("COMFYUI_ROOT", "D:/Comfy3D_WinPortable/ComfyUI")),
            cinema4d_path=Path(os.getenv("C4D_FILES_PROJECT_DIR", f"{project_root}/c4d")),
            base_dir=Path(project_root),
            comfyui_server_url=os.getenv("COMFYUI_API_URL", "http://127.0.0.1:8188"),
            comfyui_websocket_url=os.getenv("COMFYUI_API_URL", "http://127.0.0.1:8188").replace("http", "ws") + "/ws",
            cinema4d_mcp_host="localhost",
            cinema4d_mcp_port=int(os.getenv("C4D_MCP_PORT", "54321")),
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
        results = {
            "comfyui": self.comfyui_path.exists() if self.comfyui_path else False,
            "cinema4d": self.cinema4d_path.exists() if self.cinema4d_path else False,
            "workflows_dir": self.workflows_dir.exists() if self.workflows_dir else False,
            "base_dir": self.base_dir.exists() if self.base_dir else False,
            "checkpoints_dir": self.checkpoints_dir.exists() if self.checkpoints_dir else False,
            "loras_dir": self.loras_dir.exists() if self.loras_dir else False,
        }
        return results
    
    def get_checkpoint_files(self) -> list:
        """Get list of checkpoint files"""
        if self.checkpoints_dir and self.checkpoints_dir.exists():
            return [f.name for f in self.checkpoints_dir.glob("*.safetensors")]
        return []
    
    def get_lora_files(self) -> list:
        """Get list of LoRA files"""
        if self.loras_dir and self.loras_dir.exists():
            return [f.name for f in self.loras_dir.glob("*.safetensors")]
        return []
    
    def get_workflow_files(self) -> list:
        """Get list of workflow files"""
        if self.workflows_dir and self.workflows_dir.exists():
            return [f.name for f in self.workflows_dir.glob("*.json")]
        return []


# For backward compatibility
AppConfig = SimpleConfig