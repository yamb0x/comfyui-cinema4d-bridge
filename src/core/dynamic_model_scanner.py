"""
Dynamic Model Scanner for ComfyUI
Scans all model directories and provides lists for UI dropdowns
"""

from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time


class DynamicModelScanner:
    """Scans ComfyUI model directories dynamically for dropdown population"""
    
    # Model type to directory attribute mapping
    MODEL_DIR_MAPPING = {
        "checkpoint": "checkpoints_dir",
        "lora": "loras_dir",
        "vae": "vae_dir",
        "controlnet": "controlnet_dir",
        "clip": "clip_dir",
        "clip_vision": "clip_vision_dir",
        "diffusers": "diffusers_dir",
        "embeddings": "embeddings_dir",
        "gligen": "gligen_dir",
        "hypernetworks": "hypernetworks_dir",
        "style_models": "style_models_dir",
        "unet": "unet_dir",
        "upscale_models": "upscale_models_dir"
    }
    
    # File extensions for each model type
    MODEL_EXTENSIONS = {
        "checkpoint": [".safetensors", ".ckpt"],
        "lora": [".safetensors", ".ckpt", ".pt"],
        "vae": [".safetensors", ".ckpt", ".pt"],
        "controlnet": [".safetensors", ".pth", ".pt"],
        "clip": [".safetensors", ".pt", ".bin"],
        "clip_vision": [".safetensors", ".pt", ".bin"],
        "diffusers": [".safetensors", ".ckpt"],
        "embeddings": [".safetensors", ".pt", ".bin"],
        "gligen": [".safetensors", ".pt"],
        "hypernetworks": [".safetensors", ".pt", ".ckpt"],
        "style_models": [".safetensors", ".pt"],
        "unet": [".safetensors", ".ckpt", ".pt"],
        "upscale_models": [".safetensors", ".pt", ".pth"]
    }
    
    def __init__(self, config):
        """Initialize with application config"""
        self.config = config
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = 60  # Cache for 60 seconds
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def get_models(self, model_type: str, force_refresh: bool = False) -> List[str]:
        """
        Get list of available models for a specific type
        
        Args:
            model_type: Type of model (checkpoint, lora, vae, etc.)
            force_refresh: Force refresh of cache
            
        Returns:
            List of model filenames
        """
        # Check cache
        if not force_refresh and model_type in self._cache:
            if time.time() - self._cache_time.get(model_type, 0) < self._cache_duration:
                return self._cache[model_type]
        
        # Scan for models
        models = self._scan_model_type(model_type)
        
        # Update cache
        self._cache[model_type] = models
        self._cache_time[model_type] = time.time()
        
        return models
    
    def _scan_model_type(self, model_type: str) -> List[str]:
        """Scan for models of a specific type"""
        try:
            # Get directory attribute name
            dir_attr = self.MODEL_DIR_MAPPING.get(model_type)
            if not dir_attr:
                logger.warning(f"Unknown model type: {model_type}")
                return []
            
            # Get directory path from config
            if not hasattr(self.config, dir_attr):
                logger.warning(f"Config missing {dir_attr} for {model_type}")
                return []
            
            model_dir = getattr(self.config, dir_attr)
            if not model_dir or not model_dir.exists():
                logger.debug(f"Model directory not found: {model_dir}")
                return []
            
            # Get valid extensions
            extensions = self.MODEL_EXTENSIONS.get(model_type, [".safetensors"])
            
            # Scan directory
            model_files = []
            for ext in extensions:
                pattern = f"*{ext}"
                files = list(model_dir.glob(pattern))
                # Also check subdirectories (one level deep)
                files.extend(model_dir.glob(f"*/{pattern}"))
                model_files.extend([f.name for f in files if f.is_file()])
            
            # Remove duplicates and sort
            unique_models = sorted(list(set(model_files)))
            
            logger.info(f"Found {len(unique_models)} {model_type} models in {model_dir}")
            return unique_models
            
        except Exception as e:
            logger.error(f"Failed to scan {model_type} models: {e}")
            return []
    
    async def scan_all_async(self) -> Dict[str, List[str]]:
        """Scan all model types asynchronously"""
        loop = asyncio.get_event_loop()
        tasks = []
        
        for model_type in self.MODEL_DIR_MAPPING.keys():
            task = loop.run_in_executor(
                self.executor, 
                self.get_models, 
                model_type,
                True  # Force refresh
            )
            tasks.append((model_type, task))
        
        results = {}
        for model_type, task in tasks:
            try:
                models = await task
                results[model_type] = models
            except Exception as e:
                logger.error(f"Failed to scan {model_type}: {e}")
                results[model_type] = []
        
        return results
    
    def scan_all(self) -> Dict[str, List[str]]:
        """Scan all model types synchronously"""
        results = {}
        
        for model_type in self.MODEL_DIR_MAPPING.keys():
            results[model_type] = self.get_models(model_type, force_refresh=True)
        
        return results
    
    def get_model_info(self, model_type: str, model_name: str) -> Optional[Dict]:
        """Get detailed information about a specific model"""
        try:
            dir_attr = self.MODEL_DIR_MAPPING.get(model_type)
            if not dir_attr or not hasattr(self.config, dir_attr):
                return None
            
            model_dir = getattr(self.config, dir_attr)
            if not model_dir or not model_dir.exists():
                return None
            
            # Look for the model file
            model_path = model_dir / model_name
            if not model_path.exists():
                # Check subdirectories
                for subdir in model_dir.iterdir():
                    if subdir.is_dir():
                        subpath = subdir / model_name
                        if subpath.exists():
                            model_path = subpath
                            break
            
            if model_path.exists():
                stat = model_path.stat()
                return {
                    "name": model_name,
                    "path": str(model_path),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": stat.st_mtime,
                    "type": model_type
                }
            
        except Exception as e:
            logger.error(f"Failed to get info for {model_type}/{model_name}: {e}")
        
        return None
    
    def refresh_cache(self, model_type: Optional[str] = None):
        """Refresh cache for specific model type or all types"""
        if model_type:
            if model_type in self._cache:
                del self._cache[model_type]
                del self._cache_time[model_type]
        else:
            self._cache.clear()
            self._cache_time.clear()
    
    def get_dropdown_items(self, model_type: str, include_none: bool = True) -> List[str]:
        """Get model list formatted for dropdown menus"""
        models = self.get_models(model_type)
        
        if include_none:
            return ["None"] + models
        return models
    
    def validate_model_exists(self, model_type: str, model_name: str) -> bool:
        """Check if a model file actually exists"""
        if not model_name or model_name == "None":
            return True  # None is always valid
        
        models = self.get_models(model_type)
        return model_name in models