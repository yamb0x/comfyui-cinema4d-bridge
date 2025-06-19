"""
Enhanced File Monitor for Textured Models
Monitors 3D/textured folder for automatic texture viewer integration
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtCore import QObject, Signal, QTimer
from loguru import logger


class TexturedModelHandler(FileSystemEventHandler):
    """File system event handler for textured models"""
    
    def __init__(self, callback: Callable[[Path], None]):
        super().__init__()
        self.callback = callback
        self.supported_formats = {'.obj', '.fbx', '.dae', '.gltf', '.glb'}
        
    def on_created(self, event):
        """Handle file creation"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_formats:
                logger.info(f"New textured model detected: {file_path.name}")
                self.callback(file_path)
                
    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_formats:
                logger.info(f"Textured model updated: {file_path.name}")
                self.callback(file_path)


class EnhancedFileMonitor(QObject):
    """
    Enhanced file monitor with textured model support
    Integrates with run_final_viewer.bat for texture viewing
    """
    
    # Signals
    new_image_detected = Signal(str)  # image path
    new_model_detected = Signal(str)  # model path
    new_textured_model_detected = Signal(str)  # textured model path
    texture_viewer_available = Signal(bool)  # viewer availability
    
    def __init__(self):
        super().__init__()
        self.observers: Dict[str, Observer] = {}
        self.monitored_paths: Dict[str, Path] = {}
        self.textured_models_cache: List[Path] = []
        
        # Paths to monitor
        self.base_paths = {
            'images': Path("images"),
            'models_3d': Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D"),
            'textured_models': Path("D:/Comfy3D_WinPortable/ComfyUI/output/3D/textured"),
            'texture_viewer': Path("viewer/run_final_viewer.bat")
        }
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._periodic_refresh)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def start_monitoring(self):
        """Start monitoring all configured paths"""
        logger.info("Starting enhanced file monitoring...")
        
        # Monitor images directory
        if self.base_paths['images'].exists():
            self._start_path_monitoring('images', self.base_paths['images'], self._on_image_change)
            
        # Monitor 3D models directory
        if self.base_paths['models_3d'].exists():
            self._start_path_monitoring('models_3d', self.base_paths['models_3d'], self._on_model_change)
            
        # Monitor textured models directory
        if self.base_paths['textured_models'].exists():
            self._start_path_monitoring('textured_models', self.base_paths['textured_models'], self._on_textured_model_change)
        else:
            logger.warning(f"Textured models path does not exist: {self.base_paths['textured_models']}")
            
        # Check texture viewer availability
        self._check_texture_viewer_availability()
        
        logger.info("Enhanced file monitoring started")
        
    def _start_path_monitoring(self, name: str, path: Path, callback: Callable):
        """Start monitoring a specific path"""
        try:
            observer = Observer()
            
            if name == 'textured_models':
                handler = TexturedModelHandler(callback)
            else:
                handler = FileSystemEventHandler()
                handler.on_created = lambda event: callback(Path(event.src_path)) if not event.is_directory else None
                handler.on_modified = lambda event: callback(Path(event.src_path)) if not event.is_directory else None
                
            observer.schedule(handler, str(path), recursive=True)
            observer.start()
            
            self.observers[name] = observer
            self.monitored_paths[name] = path
            
            logger.info(f"Started monitoring {name}: {path}")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring {name}: {e}")
            
    def _on_image_change(self, file_path: Path):
        """Handle image file changes"""
        if file_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp'}:
            self.new_image_detected.emit(str(file_path))
            
    def _on_model_change(self, file_path: Path):
        """Handle 3D model file changes"""
        if file_path.suffix.lower() in {'.obj', '.ply', '.stl', '.fbx', '.dae', '.gltf', '.glb'}:
            self.new_model_detected.emit(str(file_path))
            
    def _on_textured_model_change(self, file_path: Path):
        """Handle textured model file changes"""
        if file_path not in self.textured_models_cache:
            self.textured_models_cache.append(file_path)
            self.new_textured_model_detected.emit(str(file_path))
            logger.info(f"New textured model available: {file_path.name}")
            
    def _check_texture_viewer_availability(self):
        """Check if texture viewer is available"""
        viewer_available = self.base_paths['texture_viewer'].exists()
        self.texture_viewer_available.emit(viewer_available)
        
        if viewer_available:
            logger.info("Texture viewer (run_final_viewer.bat) is available")
        else:
            logger.warning("Texture viewer (run_final_viewer.bat) not found")
            
    def _periodic_refresh(self):
        """Periodic refresh of cached data"""
        # Refresh textured models cache
        if self.base_paths['textured_models'].exists():
            current_models = list(self.base_paths['textured_models'].glob("*.obj"))
            current_models.extend(self.base_paths['textured_models'].glob("*.fbx"))
            
            # Check for new models not in cache
            for model in current_models:
                if model not in self.textured_models_cache:
                    self._on_textured_model_change(model)
                    
        # Check texture viewer availability
        self._check_texture_viewer_availability()
        
    def get_textured_models(self) -> List[Path]:
        """Get list of all textured models"""
        if self.base_paths['textured_models'].exists():
            models = []
            for pattern in ["*.obj", "*.fbx", "*.dae", "*.gltf", "*.glb"]:
                models.extend(self.base_paths['textured_models'].glob(pattern))
            return sorted(models, key=lambda x: x.stat().st_mtime, reverse=True)
        return []
        
    def get_recent_textured_models(self, limit: int = 10) -> List[Path]:
        """Get most recent textured models"""
        all_models = self.get_textured_models()
        return all_models[:limit]
        
    def is_texture_viewer_available(self) -> bool:
        """Check if texture viewer is available"""
        return self.base_paths['texture_viewer'].exists()
        
    def launch_texture_viewer(self) -> bool:
        """Launch texture viewer if available"""
        if self.is_texture_viewer_available():
            try:
                import subprocess
                subprocess.Popen([str(self.base_paths['texture_viewer'])], shell=True)
                logger.info("Texture viewer launched successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to launch texture viewer: {e}")
                return False
        else:
            logger.error("Texture viewer not available")
            return False
            
    def stop_monitoring(self):
        """Stop all file monitoring"""
        logger.info("Stopping enhanced file monitoring...")
        
        for name, observer in self.observers.items():
            try:
                observer.stop()
                observer.join()
                logger.info(f"Stopped monitoring {name}")
            except Exception as e:
                logger.error(f"Error stopping monitor {name}: {e}")
                
        self.observers.clear()
        self.monitored_paths.clear()
        
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            
        logger.info("Enhanced file monitoring stopped")
        
    def get_monitoring_status(self) -> Dict[str, Dict]:
        """Get status of all monitored paths"""
        status = {}
        
        for name, path in self.monitored_paths.items():
            status[name] = {
                'path': str(path),
                'exists': path.exists(),
                'monitoring': name in self.observers and self.observers[name].is_alive(),
                'file_count': len(list(path.glob("*"))) if path.exists() else 0
            }
            
        return status