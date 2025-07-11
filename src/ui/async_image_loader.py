"""
Asynchronous image loading system for improved UI performance.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import time
import weakref
from functools import lru_cache

from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker, QTimer
from PySide6.QtGui import QPixmap, QImage
from PIL import Image
from loguru import logger


class AsyncImageLoader(QThread):
    """Background thread for loading and processing images"""
    
    image_loaded = Signal(Path, QPixmap, int)  # path, pixmap, size
    loading_failed = Signal(Path, str)  # path, error_message
    
    def __init__(self, image_path: Path, size: int, cache_manager=None):
        super().__init__()
        self.image_path = image_path
        self.size = size
        self.cache_manager = cache_manager
        self._cancelled = False
        
    def cancel(self):
        """Cancel the loading operation"""
        self._cancelled = True
        
    def run(self):
        """Load image in background thread"""
        if self._cancelled:
            return
            
        try:
            # Check cache first if cache manager is available
            if self.cache_manager:
                cached_pixmap = self.cache_manager.get_cached_pixmap(self.image_path, self.size)
                if cached_pixmap and not self._cancelled:
                    self.image_loaded.emit(self.image_path, cached_pixmap, self.size)
                    return
            
            # Load and process image
            img = Image.open(self.image_path)
            
            if self._cancelled:
                return
                
            # Create thumbnail
            img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
            
            if self._cancelled:
                return
            
            # Convert to QPixmap
            if img.mode == "RGBA":
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            else:
                img = img.convert("RGB")
                data = img.tobytes("raw", "RGB")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGB888)
            
            if self._cancelled:
                return
                
            pixmap = QPixmap.fromImage(qimage)
            
            # Cache the result if cache manager is available
            if self.cache_manager and not self._cancelled:
                self.cache_manager.cache_pixmap(self.image_path, self.size, pixmap)
            
            # Emit result
            if not self._cancelled:
                self.image_loaded.emit(self.image_path, pixmap, self.size)
                
        except Exception as e:
            if not self._cancelled:
                logger.error(f"Failed to load {self.image_path}: {e}")
                self.loading_failed.emit(self.image_path, str(e))


class QPixmapCache:
    """Thread-safe QPixmap cache with LRU eviction"""
    
    def __init__(self, max_size_mb: int = 50):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size = 0
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.mutex = QMutex()
        
    def _generate_cache_key(self, image_path: Path, size: int) -> str:
        """Generate cache key for image and size"""
        return f"{image_path.as_posix()}_{size}"
    
    def get_cached_pixmap(self, image_path: Path, size: int) -> Optional[QPixmap]:
        """Get cached pixmap if available"""
        cache_key = self._generate_cache_key(image_path, size)
        
        with QMutexLocker(self.mutex):
            if cache_key in self.cache:
                self.access_times[cache_key] = time.time()
                return self.cache[cache_key]['pixmap']
        
        return None
    
    def cache_pixmap(self, image_path: Path, size: int, pixmap: QPixmap):
        """Cache a pixmap with size management"""
        cache_key = self._generate_cache_key(image_path, size)
        
        # Estimate pixmap size (width * height * 4 bytes for RGBA)
        pixmap_size = pixmap.width() * pixmap.height() * 4
        
        with QMutexLocker(self.mutex):
            # Check if we need to evict items
            while self.current_size + pixmap_size > self.max_size_bytes and self.cache:
                self._evict_oldest_item()
            
            # Add new item
            self.cache[cache_key] = {
                'pixmap': pixmap,
                'size': pixmap_size,
                'timestamp': time.time()
            }
            self.access_times[cache_key] = time.time()
            self.current_size += pixmap_size
            
            logger.debug(f"Cached pixmap {cache_key}, cache size: {self.current_size / 1024 / 1024:.1f}MB")
    
    def _evict_oldest_item(self):
        """Evict the least recently used item"""
        if not self.access_times:
            return
            
        # Find oldest item
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove from cache
        if oldest_key in self.cache:
            item_size = self.cache[oldest_key]['size']
            self.current_size -= item_size
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            logger.debug(f"Evicted {oldest_key} from cache")
    
    def clear(self):
        """Clear entire cache"""
        with QMutexLocker(self.mutex):
            self.cache.clear()
            self.access_times.clear()
            self.current_size = 0
            logger.info("Cleared image cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with QMutexLocker(self.mutex):
            return {
                'size_mb': self.current_size / 1024 / 1024,
                'max_size_mb': self.max_size_bytes / 1024 / 1024,
                'item_count': len(self.cache),
                'utilization': self.current_size / self.max_size_bytes
            }


class AsyncImageManager:
    """Manages asynchronous image loading with caching"""
    
    def __init__(self, cache_size_mb: int = 50):
        self.cache = QPixmapCache(cache_size_mb)
        self.active_loaders: Dict[str, AsyncImageLoader] = {}
        self.pending_requests: Dict[str, list] = {}  # Track multiple requests for same image
        
    def load_image_async(self, image_path: Path, size: int, callback=None):
        """Load image asynchronously with caching"""
        cache_key = f"{image_path.as_posix()}_{size}"
        
        # Check cache first
        cached_pixmap = self.cache.get_cached_pixmap(image_path, size)
        if cached_pixmap:
            if callback:
                callback(image_path, cached_pixmap, size)
            return
        
        # Check if already loading
        if cache_key in self.active_loaders:
            # Add callback to pending requests
            if cache_key not in self.pending_requests:
                self.pending_requests[cache_key] = []
            if callback:
                self.pending_requests[cache_key].append(callback)
            return
        
        # Start new loading task
        loader = AsyncImageLoader(image_path, size, self.cache)
        loader.image_loaded.connect(lambda path, pixmap, sz: self._on_image_loaded(path, pixmap, sz, cache_key))
        loader.loading_failed.connect(lambda path, error: self._on_loading_failed(path, error, cache_key))
        
        # Add initial callback
        if cache_key not in self.pending_requests:
            self.pending_requests[cache_key] = []
        if callback:
            self.pending_requests[cache_key].append(callback)
        
        self.active_loaders[cache_key] = loader
        loader.start()
        
    def _on_image_loaded(self, image_path: Path, pixmap: QPixmap, size: int, cache_key: str):
        """Handle successful image loading"""
        # Call all pending callbacks
        if cache_key in self.pending_requests:
            for callback in self.pending_requests[cache_key]:
                try:
                    callback(image_path, pixmap, size)
                except Exception as e:
                    logger.error(f"Error in image load callback: {e}")
            del self.pending_requests[cache_key]
        
        # Clean up loader
        if cache_key in self.active_loaders:
            self.active_loaders[cache_key].deleteLater()
            del self.active_loaders[cache_key]
    
    def _on_loading_failed(self, image_path: Path, error: str, cache_key: str):
        """Handle failed image loading"""
        logger.error(f"Failed to load image {image_path}: {error}")
        
        # Clean up pending requests
        if cache_key in self.pending_requests:
            del self.pending_requests[cache_key]
        
        # Clean up loader
        if cache_key in self.active_loaders:
            self.active_loaders[cache_key].deleteLater()
            del self.active_loaders[cache_key]
    
    def cancel_all_loading(self):
        """Cancel all active loading operations"""
        for loader in self.active_loaders.values():
            loader.cancel()
            loader.wait(1000)  # Wait up to 1 second for thread to finish
            loader.deleteLater()
        
        self.active_loaders.clear()
        self.pending_requests.clear()
    
    def preload_images(self, image_paths: list, size: int = 256):
        """Preload multiple images in background"""
        for image_path in image_paths:
            if isinstance(image_path, str):
                image_path = Path(image_path)
            self.load_image_async(image_path, size)
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return self.cache.get_cache_stats()
    
    def clear_cache(self):
        """Clear the image cache"""
        self.cache.clear()


# Global instance
_async_image_manager = None

def get_async_image_manager() -> AsyncImageManager:
    """Get global async image manager instance"""
    global _async_image_manager
    if _async_image_manager is None:
        _async_image_manager = AsyncImageManager()
    return _async_image_manager