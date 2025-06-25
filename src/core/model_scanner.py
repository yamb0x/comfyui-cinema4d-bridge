"""
Dynamic Model Scanner for ComfyUI
Scans all model directories and provides models for any node type
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


class ComfyUIModelScanner:
    """Dynamically scans ComfyUI model directories for available models"""
    
    # Map node types to their model directories
    NODE_TO_MODEL_DIR = {
        "CheckpointLoaderSimple": "checkpoints",
        "CheckpointLoader": "checkpoints",
        "LoraLoader": "loras",
        "LoRALoader": "loras",
        "VAELoader": "vae",
        "CLIPLoader": "clip",
        "CLIPVisionLoader": "clip_vision",
        "ControlNetLoader": "controlnet",
        "UNETLoader": "diffusion_models",  # UNETLoader uses diffusion_models directory
        "DiffusersLoader": "diffusers",
        "HypernetworkLoader": "hypernetworks",
        "StyleModelLoader": "style_models",
        "UpscaleModelLoader": "upscale_models",
        "GLIGENLoader": "gligen",
        "EmbeddingLoader": "embeddings",
        # SD3 and Flux specific loaders
        "QuadrupleCLIPLoader": "text_encoders",  # Special directory for text encoders
        "DualCLIPLoader": "clip",
        "TripleCLIPLoader": "clip",
        "SD3ModelLoader": "checkpoints",
        "FluxModelLoader": "checkpoints",
        # Add more mappings as needed
    }
    
    # File extensions for each model type
    MODEL_EXTENSIONS = {
        "checkpoints": [".ckpt", ".safetensors", ".pt", ".pth", ".bin"],
        "loras": [".safetensors", ".pt", ".ckpt"],
        "vae": [".safetensors", ".pt", ".ckpt", ".vae"],
        "clip": [".safetensors", ".pt", ".bin"],
        "clip_vision": [".safetensors", ".pt", ".bin"],
        "controlnet": [".safetensors", ".pt", ".pth"],
        "unet": [".safetensors", ".pt", ".onnx"],
        "diffusers": [".safetensors", ".bin"],
        "hypernetworks": [".pt", ".safetensors", ".ckpt"],
        "style_models": [".safetensors", ".pt"],
        "upscale_models": [".pth", ".pt", ".safetensors"],
        "gligen": [".safetensors", ".pt"],
        "embeddings": [".pt", ".safetensors", ".bin"],
        "text_encoders": [".safetensors", ".pt", ".bin"],  # For CLIP text encoders
        "diffusion_models": [".safetensors", ".pt", ".onnx"],  # For diffusion models
    }
    
    def __init__(self, comfyui_models_dir: Optional[Path] = None, config=None):
        """
        Initialize scanner with ComfyUI models directory
        
        Args:
            comfyui_models_dir: Path to ComfyUI/models directory
            config: Application config with model directory paths
        """
        self.logger = logger
        self.config = config
        
        # Try to find ComfyUI models directory
        if comfyui_models_dir:
            self.models_dir = Path(comfyui_models_dir)
        else:
            # Try common locations
            possible_paths = [
                Path("D:/Comfy3D_WinPortable/ComfyUI/models"),
                Path("C:/ComfyUI/models"),
                Path.home() / "ComfyUI" / "models",
                Path("./ComfyUI/models"),
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.models_dir = path
                    break
            else:
                self.models_dir = None
                self.logger.warning("ComfyUI models directory not found")
        
        if self.models_dir:
            self.logger.info(f"Using ComfyUI models directory: {self.models_dir}")
        
        # Cache for scanned models
        self._model_cache: Dict[str, List[str]] = {}
    
    def get_models_for_node(self, node_type: str, force_rescan: bool = False) -> List[str]:
        """
        Get available models for a specific node type
        
        Args:
            node_type: The ComfyUI node type (e.g., "CheckpointLoaderSimple")
            force_rescan: Force rescan of directory instead of using cache
            
        Returns:
            List of available model filenames
        """
        if not self.models_dir:
            return []
        
        # Check cache first
        if not force_rescan and node_type in self._model_cache:
            return self._model_cache[node_type]
        
        # Get model directory for this node type
        model_subdir = self.NODE_TO_MODEL_DIR.get(node_type)
        if not model_subdir:
            self.logger.debug(f"No model directory mapping for node type: {node_type}")
            return []
        
        # Scan the directory
        models = self._scan_model_directory(model_subdir)
        
        # Cache the results
        self._model_cache[node_type] = models
        
        return models
    
    def _scan_model_directory(self, subdir: str) -> List[str]:
        """
        Scan a specific model subdirectory
        
        Args:
            subdir: Subdirectory name (e.g., "checkpoints", "loras")
            
        Returns:
            List of model filenames found
        """
        # Try to use config directory first if available
        model_path = None
        
        if self.config:
            # Map subdirectory names to config attributes
            config_dir_mapping = {
                "checkpoints": "checkpoints_dir",
                "loras": "loras_dir",
                "vae": "vae_dir",
                "clip": "clip_dir",
                "clip_vision": "clip_vision_dir",
                "controlnet": "controlnet_dir",
                "diffusers": "diffusers_dir",
                "embeddings": "embeddings_dir",
                "gligen": "gligen_dir",
                "hypernetworks": "hypernetworks_dir",
                "style_models": "style_models_dir",
                "diffusion_models": "unet_dir",  # UNETLoader uses unet_dir
                "upscale_models": "upscale_models_dir",
                "text_encoders": "clip_dir"  # QuadrupleCLIPLoader uses clip directory
            }
            
            config_attr = config_dir_mapping.get(subdir)
            if config_attr and hasattr(self.config, config_attr):
                config_path = getattr(self.config, config_attr)
                if config_path and config_path.exists():
                    model_path = config_path
                    self.logger.debug(f"Using config directory for {subdir}: {model_path}")
        
        # Fallback to default models_dir structure
        if not model_path and self.models_dir:
            model_path = self.models_dir / subdir
        
        if not model_path or not model_path.exists():
            self.logger.debug(f"Model directory does not exist: {model_path}")
            return []
        
        models = []
        extensions = self.MODEL_EXTENSIONS.get(subdir, [".safetensors", ".pt", ".ckpt", ".pth"])
        
        # Recursively scan for model files
        for root, dirs, files in os.walk(model_path):
            # Calculate relative path from model_path
            rel_path = Path(root).relative_to(model_path)
            
            for file in files:
                # Check if file has valid extension
                if any(file.lower().endswith(ext) for ext in extensions):
                    # Store relative path if in subdirectory, otherwise just filename
                    if rel_path != Path("."):
                        model_name = str(rel_path / file)
                    else:
                        model_name = file
                    
                    models.append(model_name)
        
        # Sort models alphabetically
        models.sort()
        
        self.logger.info(f"Found {len(models)} models in {subdir}")
        return models
    
    def get_all_model_directories(self) -> Dict[str, Path]:
        """
        Get all model directories that exist
        
        Returns:
            Dictionary of model type to directory path
        """
        if not self.models_dir:
            return {}
        
        directories = {}
        
        for node_type, subdir in self.NODE_TO_MODEL_DIR.items():
            dir_path = self.models_dir / subdir
            if dir_path.exists():
                directories[subdir] = dir_path
        
        return directories
    
    def scan_all_models(self, force_rescan: bool = False) -> Dict[str, List[str]]:
        """
        Scan all model directories
        
        Args:
            force_rescan: Force rescan even if cached
            
        Returns:
            Dictionary of model type to list of models
        """
        if not force_rescan and self._model_cache:
            return self._model_cache
        
        all_models = {}
        
        for node_type, subdir in self.NODE_TO_MODEL_DIR.items():
            models = self.get_models_for_node(node_type, force_rescan=True)
            if models:
                all_models[node_type] = models
        
        return all_models
    
    def add_node_mapping(self, node_type: str, model_directory: str):
        """
        Add a new node type to model directory mapping
        
        Args:
            node_type: The ComfyUI node type
            model_directory: The subdirectory in models/ for this node type
        """
        self.NODE_TO_MODEL_DIR[node_type] = model_directory
        self.logger.info(f"Added mapping: {node_type} -> {model_directory}")
    
    def get_model_info(self, model_path: str, model_type: str) -> Dict[str, any]:
        """
        Get information about a specific model
        
        Args:
            model_path: Relative path to model file
            model_type: Type of model (checkpoints, loras, etc.)
            
        Returns:
            Dictionary with model information
        """
        if not self.models_dir:
            return {}
        
        full_path = self.models_dir / model_type / model_path
        
        if not full_path.exists():
            return {}
        
        stat = full_path.stat()
        
        return {
            "name": model_path,
            "type": model_type,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": stat.st_mtime,
            "full_path": str(full_path)
        }