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
        
        # Skip if already processed
        if str(file_path) in self.processed_files:
            return
            
        # Schedule delayed processing
        self._schedule_delayed_processing(file_path, "created")
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Schedule delayed processing
        self._schedule_delayed_processing(file_path, "modified")
    
    def _schedule_delayed_processing(self, file_path: Path, event_type: str):
        """Schedule delayed processing using the main event loop"""
        if self.loop and not self.loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(
                    self._process_file_delayed(file_path, event_type),
                    self.loop
                )
            except Exception as e:
                self.logger.error(f"Failed to schedule file processing: {e}")
        else:
            # Fallback to immediate processing without delay
            self._process_file_immediate(file_path, event_type)
    
    async def _process_file_delayed(self, file_path: Path, event_type: str):
        """Process file after a delay to ensure write is complete"""
        await asyncio.sleep(0.5)  # Wait for file write to complete
        
        if file_path.exists() and file_path.stat().st_size > 0:
            self.processed_files.add(str(file_path))
            self.logger.info(f"New file detected: {file_path.name}")
            self.callback(file_path, event_type)
    
    def _process_file_immediate(self, file_path: Path, event_type: str):
        """Process file immediately (fallback)"""
        import time
        time.sleep(0.5)  # Simple delay without asyncio
        
        if file_path.exists() and file_path.stat().st_size > 0:
            self.processed_files.add(str(file_path))
            self.logger.info(f"New file detected: {file_path.name}")
            self.callback(file_path, event_type)


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
    
    def clear(self):
        """Clear all tracking data"""
        self.relationships.clear()
        self.asset_metadata.clear()
        self.logger.info("Cleared asset tracking data")