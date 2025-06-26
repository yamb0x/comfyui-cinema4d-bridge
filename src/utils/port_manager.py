"""
Port pool manager for ThreeJS viewers to prevent socket binding errors
"""

import threading
import socket
from typing import Optional, Set
from loguru import logger


class PortPoolManager:
    """
    Manages a pool of ports for ThreeJS viewers to prevent port conflicts
    and socket permission errors.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._base_port = 8890
            self._max_port = 9000
            self._allocated_ports: Set[int] = set()
            self._port_lock = threading.Lock()
            logger.debug("PortPoolManager initialized")
    
    def allocate_port(self) -> Optional[int]:
        """
        Allocate an available port from the pool.
        
        Returns:
            Available port number or None if no ports available
        """
        with self._port_lock:
            for port in range(self._base_port, self._max_port):
                if port not in self._allocated_ports and self._is_port_available(port):
                    self._allocated_ports.add(port)
                    logger.debug(f"Allocated port {port}")
                    return port
            
            logger.warning(f"No available ports in range {self._base_port}-{self._max_port}")
            return None
    
    def release_port(self, port: int):
        """Release a port back to the pool"""
        with self._port_lock:
            if port in self._allocated_ports:
                self._allocated_ports.remove(port)
                logger.debug(f"Released port {port}")
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', port))
                return True
        except (OSError, socket.error) as e:
            logger.debug(f"Port {port} is not available: {e}")
            return False
    
    def get_allocated_ports(self) -> Set[int]:
        """Get set of currently allocated ports"""
        with self._port_lock:
            return self._allocated_ports.copy()
    
    def reset(self):
        """Reset the port pool (useful for testing)"""
        with self._port_lock:
            self._allocated_ports.clear()
            logger.debug("Port pool reset")


# Global instance
port_manager = PortPoolManager()