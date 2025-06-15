"""
File system monitoring for output directories
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from loguru import logger

from utils.logger import LoggerMixin


class OutputFileHandler(FileSystemEventHandler, LoggerMixin):
    """Handle file system events for output directories"""
    
    def __init__(self, callback: Callable[[Path, str], None]):
        super().__init__()
        self.callback = callback
        self.processed_files: Set[str] = set()
        self.loop = None
        
    def set_event_loop(self, loop):
        """Set the event loop for async operations"""
        self.loop = loop
        
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        self.logger.info(f"File monitor detected CREATED: {file_path.name}")
        
        # Skip if already processed
        if str(file_path) in self.processed_files:
            self.logger.info(f"File already processed, skipping: {file_path.name}")
            return
            
        # Schedule delayed processing
        self._schedule_delayed_processing(file_path, "created")
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        # Only log image files to avoid spam
        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            self.logger.info(f"File monitor detected MODIFIED: {file_path.name}")
        
        # Schedule delayed processing
        self._schedule_delayed_processing(file_path, "modified")
    
    def _schedule_delayed_processing(self, file_path: Path, event_type: str):
        """Process file immediately since delayed processing has threading issues"""
        # Reduce logging spam - only log for 3D models to debug the main issue
        if file_path.suffix.lower() in ['.glb', '.obj', '.fbx', '.gltf']:
            self.logger.info(f"🎯 IMMEDIATE PROCESSING for: {file_path.name}")
        
        # Use immediate processing to avoid threading issues
        # Add a small delay using time.sleep to ensure file write is complete
        import time
        time.sleep(0.5)
        
        self._process_file_sync(file_path, event_type)
    
    def _process_file_sync(self, file_path: Path, event_type: str):
        """Process file synchronously with proper duplicate prevention"""
        try:
            # Check if already processed to prevent duplicates
            if str(file_path) in self.processed_files:
                return
                
            if file_path.exists() and file_path.stat().st_size > 0:
                self.processed_files.add(str(file_path))
                
                # Log for 3D models only to debug the main issue
                if file_path.suffix.lower() in ['.glb', '.obj', '.fbx', '.gltf']:
                    self.logger.info(f"Processing 3D model: {file_path.name} (size: {file_path.stat().st_size} bytes)")
                    self.logger.info(f"🔥 CALLING CALLBACK for: {file_path.name}")
                
                self.callback(file_path, event_type)
                
                if file_path.suffix.lower() in ['.glb', '.obj', '.fbx', '.gltf']:
                    self.logger.info(f"✅ CALLBACK COMPLETED for: {file_path.name}")
            else:
                if file_path.suffix.lower() in ['.glb', '.obj', '.fbx', '.gltf']:
                    self.logger.warning(f"3D model file doesn't exist or is empty: {file_path.name}")
        except Exception as e:
            self.logger.error(f"Error processing file {file_path.name}: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
    
    async def _process_file_delayed(self, file_path: Path, event_type: str):
        """Process file after a delay to ensure write is complete"""
        try:
            await asyncio.sleep(0.5)  # Wait for file write to complete
            
            if file_path.exists() and file_path.stat().st_size > 0:
                self.processed_files.add(str(file_path))
                self.logger.info(f"Processing file: {file_path.name} (size: {file_path.stat().st_size} bytes)")
                self.logger.info(f"🔥 CALLING CALLBACK for: {file_path.name}")
                
                self.callback(file_path, event_type)
                self.logger.info(f"✅ CALLBACK COMPLETED for: {file_path.name}")
            else:
                self.logger.warning(f"File doesn't exist or is empty: {file_path.name}")
        except Exception as e:
            self.logger.error(f"Error processing file {file_path.name}: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def _process_file_immediate(self, file_path: Path, event_type: str):
        """Process file immediately (fallback)"""
        import time
        time.sleep(0.5)  # Simple delay without asyncio
        
        if file_path.exists() and file_path.stat().st_size > 0:
            self.processed_files.add(str(file_path))
            self.logger.info(f"New file detected: {file_path.name}")
            self.logger.info(f"🔥 CALLING CALLBACK (immediate) for: {file_path.name}")
            self.callback(file_path, event_type)
            self.logger.info(f"✅ CALLBACK COMPLETED (immediate) for: {file_path.name}")


class FileMonitor(LoggerMixin):
    """Monitor multiple directories for file changes"""
    
    def __init__(self):
        self.observers: Dict[str, Observer] = {}
        self.handlers: Dict[str, OutputFileHandler] = {}
        self._running = False
        self.loop = None
        
    def set_event_loop(self, loop):
        """Set the event loop for all handlers"""
        self.loop = loop
        for handler in self.handlers.values():
            handler.set_event_loop(loop)
        
    def add_directory(self, name: str, path: Path, 
                     callback: Callable[[Path, str], None],
                     patterns: Optional[List[str]] = None):
        """Add directory to monitor"""
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {path}")
        
        # Create handler
        handler = OutputFileHandler(callback)
        if self.loop:
            handler.set_event_loop(self.loop)
        self.handlers[name] = handler
        
        # Create observer
        observer = Observer()
        observer.schedule(handler, str(path), recursive=False)
        self.observers[name] = observer
        
        self.logger.info(f"Added monitor for {name}: {path}")
        
        # If already running, start this observer
        if self._running:
            observer.start()
    
    def remove_directory(self, name: str):
        """Remove directory from monitoring"""
        if name in self.observers:
            observer = self.observers[name]
            observer.stop()
            observer.join()
            del self.observers[name]
            del self.handlers[name]
            self.logger.info(f"Removed monitor for {name}")
    
    def start(self):
        """Start monitoring all directories"""
        if self._running:
            return
            
        self._running = True
        for name, observer in self.observers.items():
            observer.start()
            self.logger.info(f"Started monitoring {name}")
    
    def stop(self):
        """Stop monitoring all directories"""
        if not self._running:
            return
            
        self._running = False
        for name, observer in self.observers.items():
            observer.stop()
            observer.join()
            self.logger.info(f"Stopped monitoring {name}")
    
    def get_existing_files(self, directory: Path, 
                          extensions: List[str] = None) -> List[Path]:
        """Get existing files in directory"""
        if not directory.exists():
            return []
        
        files = []
        for file_path in directory.iterdir():
            if file_path.is_file():
                if extensions is None or file_path.suffix.lower() in extensions:
                    files.append(file_path)
        
        # Sort by modification time (newest first)
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files
    
    def clear_processed_files(self, name: str):
        """Clear processed files for a specific handler"""
        if name in self.handlers:
            self.handlers[name].processed_files.clear()


class AssetTracker(LoggerMixin):
    """Track relationships between generated assets"""
    
    def __init__(self):
        self.relationships: Dict[str, Dict[str, Any]] = {}
        self.asset_metadata: Dict[str, Dict[str, Any]] = {}
        
    def add_asset(self, asset_path: Path, asset_type: str,
                 metadata: Dict[str, Any] = None):
        """Add an asset to tracking"""
        asset_id = str(asset_path)
        
        self.asset_metadata[asset_id] = {
            "path": asset_path,
            "type": asset_type,
            "created": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.logger.debug(f"Added {asset_type} asset: {asset_path.name}")
    
    def link_assets(self, source_path: Path, target_path: Path,
                   relationship: str = "generated_from"):
        """Create relationship between assets"""
        source_id = str(source_path)
        target_id = str(target_path)
        
        if source_id not in self.relationships:
            self.relationships[source_id] = {}
        
        if relationship not in self.relationships[source_id]:
            self.relationships[source_id][relationship] = []
        
        self.relationships[source_id][relationship].append(target_id)
        
        self.logger.debug(f"Linked {source_path.name} -> {target_path.name} ({relationship})")
    
    def get_related_assets(self, asset_path: Path, 
                          relationship: str = None) -> List[Path]:
        """Get assets related to a given asset"""
        asset_id = str(asset_path)
        related = []
        
        if asset_id in self.relationships:
            if relationship:
                # Get specific relationship
                related_ids = self.relationships[asset_id].get(relationship, [])
            else:
                # Get all relationships
                related_ids = []
                for rel_list in self.relationships[asset_id].values():
                    related_ids.extend(rel_list)
            
            # Convert IDs back to paths
            for rel_id in related_ids:
                if rel_id in self.asset_metadata:
                    related.append(self.asset_metadata[rel_id]["path"])
        
        return related
    
    def get_asset_metadata(self, asset_path: Path) -> Optional[Dict[str, Any]]:
        """Get metadata for an asset"""
        asset_id = str(asset_path)
        return self.asset_metadata.get(asset_id)
    
    def get_assets_by_type(self, asset_type: str) -> List[Path]:
        """Get all assets of a specific type"""
        assets = []
        for asset_data in self.asset_metadata.values():
            if asset_data["type"] == asset_type:
                assets.append(asset_data["path"])
        return assets
    
    def get_images(self) -> List[Path]:
        """Get all tracked image assets"""
        return self.get_assets_by_type("image")
    
    def get_models(self) -> List[Path]:
        """Get all tracked 3D model assets"""
        return self.get_assets_by_type("model")
    
    def clear(self):
        """Clear all tracking data"""
        self.relationships.clear()
        self.asset_metadata.clear()
        self.logger.info("Cleared asset tracking data")