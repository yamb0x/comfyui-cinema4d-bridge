"""
Integration Hub

Centralized hub for managing all external system integrations.
Extracted from monolithic application to provide unified interface for
ComfyUI, Cinema4D, and other external services.

Part of Phase 2 architectural decomposition - implements the multi-mind analysis
recommendation for isolating external dependencies and improving integration
reliability with proper error handling and retry logic.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from ..utils.advanced_logging import get_logger

logger = get_logger("integration")

from PySide6.QtCore import QObject, Signal, QTimer

from ..utils.error_handling import handle_errors, error_context, ErrorHandler, NetworkErrorHandler
from ..core.unified_config_manager import UnifiedConfigurationManager
from ..core.resource_manager import resource_manager
from ..mcp.comfyui_client import ComfyUIClient
from ..mcp.cinema4d_client import Cinema4DClient


class ServiceType(Enum):
    """Types of integrated services"""
    COMFYUI = "comfyui"
    CINEMA4D = "cinema4d"
    MCP_SERVER = "mcp_server"


class ConnectionStatus(Enum):
    """Connection status for services"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class ServiceInfo:
    """Information about integrated service"""
    service_type: ServiceType
    name: str
    url: str
    port: Optional[int] = None
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_check: float = 0
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 5.0
    
    def is_available(self) -> bool:
        """Check if service is available for use"""
        return self.status == ConnectionStatus.CONNECTED
    
    def needs_retry(self) -> bool:
        """Check if service needs retry"""
        return (self.status == ConnectionStatus.ERROR and 
                self.retry_count < self.max_retries)


class ServiceIntegration(ABC):
    """Abstract base class for service integrations"""
    
    def __init__(self, service_info: ServiceInfo, config_manager: UnifiedConfigurationManager):
        self.service_info = service_info
        self.config = config_manager
        self.error_handler = ErrorHandler(f"integration_{service_info.service_type.value}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to service"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from service"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check service health"""
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, parameters: Dict[str, Any]) -> Any:
        """Execute command on service"""
        pass


class ComfyUIIntegration(ServiceIntegration):
    """ComfyUI service integration"""
    
    def __init__(self, service_info: ServiceInfo, config_manager: UnifiedConfigurationManager):
        super().__init__(service_info, config_manager)
        self.client = ComfyUIClient(
            server_url=service_info.url,
            logger_name=f"comfyui_integration"
        )
    
    @handle_errors("comfyui_integration", "connect")
    async def connect(self) -> bool:
        """Connect to ComfyUI service"""
        try:
            self.service_info.status = ConnectionStatus.CONNECTING
            
            # Test basic connectivity
            is_connected = await self.client.check_web_interface()
            
            if is_connected:
                self.service_info.status = ConnectionStatus.CONNECTED
                self.service_info.retry_count = 0
                self.service_info.error_message = ""
                logger.info(f"Connected to ComfyUI: {self.service_info.url}")
                return True
            else:
                self.service_info.status = ConnectionStatus.ERROR
                self.service_info.error_message = "ComfyUI web interface not accessible"
                return False
                
        except Exception as e:
            self.service_info.status = ConnectionStatus.ERROR
            self.service_info.error_message = str(e)
            self.error_handler.handle_error(e, "connect")
            return False
        finally:
            self.service_info.last_check = time.time()
    
    async def disconnect(self) -> bool:
        """Disconnect from ComfyUI service"""
        try:
            # ComfyUI client doesn't maintain persistent connection
            self.service_info.status = ConnectionStatus.DISCONNECTED
            logger.info("Disconnected from ComfyUI")
            return True
        except Exception as e:
            self.error_handler.handle_error(e, "disconnect")
            return False
    
    @handle_errors("comfyui_integration", "health_check")
    async def health_check(self) -> bool:
        """Check ComfyUI health"""
        try:
            # Check system stats endpoint
            stats = await self.client.get_system_stats()
            return stats is not None
        except Exception as e:
            self.error_handler.handle_error(e, "health_check")
            return False
    
    async def execute_command(self, command: str, parameters: Dict[str, Any]) -> Any:
        """Execute command on ComfyUI"""
        if command == "submit_workflow":
            workflow = parameters.get("workflow")
            batch_size = parameters.get("batch_size", 1)
            return await self.client.queue_prompt(workflow, batch_size)
        
        elif command == "get_history":
            return await self.client.get_history()
        
        elif command == "get_models":
            return await self.client.get_models()
        
        elif command == "download_image":
            filename = parameters.get("filename")
            output_dir = parameters.get("output_dir", "images")
            return await self.client.fetch_image(filename, output_dir)
        
        elif command == "get_system_stats":
            return await self.client.get_system_stats()
        
        else:
            raise ValueError(f"Unknown ComfyUI command: {command}")


class Cinema4DIntegration(ServiceIntegration):
    """Cinema4D service integration"""
    
    def __init__(self, service_info: ServiceInfo, config_manager: UnifiedConfigurationManager):
        super().__init__(service_info, config_manager)
        self.client = Cinema4DClient()
    
    @handle_errors("cinema4d_integration", "connect")
    async def connect(self) -> bool:
        """Connect to Cinema4D service"""
        try:
            self.service_info.status = ConnectionStatus.CONNECTING
            
            # Test Cinema4D connection
            is_connected = await self.client.test_connection()
            
            if is_connected:
                self.service_info.status = ConnectionStatus.CONNECTED
                self.service_info.retry_count = 0
                self.service_info.error_message = ""
                logger.info(f"Connected to Cinema4D on port {self.service_info.port}")
                return True
            else:
                self.service_info.status = ConnectionStatus.ERROR
                self.service_info.error_message = "Cinema4D command port not accessible"
                return False
                
        except Exception as e:
            self.service_info.status = ConnectionStatus.ERROR
            self.service_info.error_message = str(e)
            self.error_handler.handle_error(e, "connect")
            return False
        finally:
            self.service_info.last_check = time.time()
    
    async def disconnect(self) -> bool:
        """Disconnect from Cinema4D service"""
        try:
            # Cinema4D client doesn't maintain persistent connection
            self.service_info.status = ConnectionStatus.DISCONNECTED
            logger.info("Disconnected from Cinema4D")
            return True
        except Exception as e:
            self.error_handler.handle_error(e, "disconnect")
            return False
    
    async def health_check(self) -> bool:
        """Check Cinema4D health"""
        try:
            return await self.client.test_connection()
        except Exception as e:
            self.error_handler.handle_error(e, "health_check")
            return False
    
    async def execute_command(self, command: str, parameters: Dict[str, Any]) -> Any:
        """Execute command on Cinema4D"""
        if command == "create_object":
            object_type = parameters.get("object_type")
            object_params = parameters.get("parameters", {})
            return await self.client.create_object(object_type, object_params)
        
        elif command == "import_model":
            model_path = parameters.get("model_path")
            return await self.client.import_3d_model(model_path)
        
        elif command == "execute_script":
            script = parameters.get("script")
            return await self.client.execute_python_script(script)
        
        elif command == "get_scene_info":
            return await self.client.get_scene_objects()
        
        else:
            raise ValueError(f"Unknown Cinema4D command: {command}")


class IntegrationHub(QObject):
    """
    Centralized hub for managing all external system integrations
    
    Provides unified interface for ComfyUI, Cinema4D, and other external services
    with proper error handling, retry logic, and connection monitoring.
    """
    
    # Connection status signals
    service_connected = Signal(str, str)  # service_name, status
    service_disconnected = Signal(str, str)  # service_name, reason
    service_error = Signal(str, str)  # service_name, error_message
    
    # Operation signals
    command_completed = Signal(str, str, object)  # service_name, command, result
    command_failed = Signal(str, str, str)  # service_name, command, error
    
    def __init__(self, config_manager: UnifiedConfigurationManager):
        super().__init__()
        self.config = config_manager
        
        # Service registry
        self.services: Dict[str, ServiceInfo] = {}
        self.integrations: Dict[str, ServiceIntegration] = {}
        
        # Connection monitoring
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self._check_connections)
        self.connection_check_interval = 30000  # 30 seconds
        
        # Error handling
        self.error_handler = ErrorHandler("integration_hub")
        self.network_error_handler = NetworkErrorHandler()
        
        # Initialize services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize service configurations"""
        # ComfyUI service
        comfyui_url = self.config.get_setting("mcp.comfyui_server_url", "http://127.0.0.1:8188")
        comfyui_info = ServiceInfo(
            service_type=ServiceType.COMFYUI,
            name="ComfyUI",
            url=comfyui_url,
            max_retries=3,
            retry_delay=5.0
        )
        self.services["comfyui"] = comfyui_info
        self.integrations["comfyui"] = ComfyUIIntegration(comfyui_info, self.config)
        
        # Cinema4D service
        cinema4d_port = self.config.get_setting("mcp.cinema4d_port", 54321)
        cinema4d_info = ServiceInfo(
            service_type=ServiceType.CINEMA4D,
            name="Cinema4D",
            url=f"localhost:{cinema4d_port}",
            port=cinema4d_port,
            max_retries=3,
            retry_delay=5.0
        )
        self.services["cinema4d"] = cinema4d_info
        self.integrations["cinema4d"] = Cinema4DIntegration(cinema4d_info, self.config)
        
        logger.info(f"Initialized {len(self.services)} service integrations")
    
    def start_monitoring(self):
        """Start connection monitoring"""
        if not self.connection_timer.isActive():
            self.connection_timer.start(self.connection_check_interval)
            logger.info("Connection monitoring started")
    
    def stop_monitoring(self):
        """Stop connection monitoring"""
        if self.connection_timer.isActive():
            self.connection_timer.stop()
            logger.info("Connection monitoring stopped")
    
    async def _check_connections(self):
        """Check all service connections"""
        for service_name, service_info in self.services.items():
            try:
                if service_info.status == ConnectionStatus.CONNECTED:
                    # Health check for connected services
                    integration = self.integrations[service_name]
                    is_healthy = await integration.health_check()
                    
                    if not is_healthy:
                        service_info.status = ConnectionStatus.ERROR
                        service_info.error_message = "Health check failed"
                        self.service_error.emit(service_name, "Health check failed")
                        logger.warning(f"Health check failed for {service_name}")
                
                elif service_info.needs_retry():
                    # Retry connection for failed services
                    await self._retry_connection(service_name)
                
            except Exception as e:
                self.error_handler.handle_error(e, "check_connections", 
                                              context={"service": service_name})
    
    async def _retry_connection(self, service_name: str):
        """Retry connection for specific service"""
        service_info = self.services[service_name]
        integration = self.integrations[service_name]
        
        service_info.retry_count += 1
        service_info.status = ConnectionStatus.RECONNECTING
        
        logger.info(f"Retrying connection to {service_name} (attempt {service_info.retry_count})")
        
        try:
            success = await integration.connect()
            if success:
                self.service_connected.emit(service_name, "reconnected")
                logger.info(f"Successfully reconnected to {service_name}")
            else:
                if service_info.retry_count >= service_info.max_retries:
                    logger.error(f"Max retries reached for {service_name}")
                    self.service_error.emit(service_name, "Max retries reached")
        
        except Exception as e:
            self.error_handler.handle_error(e, "retry_connection",
                                          context={"service": service_name})
    
    # Public Interface Methods
    
    @handle_errors("integration_hub", "connect_service")
    async def connect_service(self, service_name: str) -> bool:
        """Connect to specific service"""
        if service_name not in self.integrations:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        with error_context("integration_hub", "connect_service", service=service_name):
            integration = self.integrations[service_name]
            service_info = self.services[service_name]
            
            success = await integration.connect()
            
            if success:
                self.service_connected.emit(service_name, "connected")
            else:
                self.service_error.emit(service_name, service_info.error_message)
            
            return success
    
    async def disconnect_service(self, service_name: str) -> bool:
        """Disconnect from specific service"""
        if service_name not in self.integrations:
            return False
        
        integration = self.integrations[service_name]
        success = await integration.disconnect()
        
        if success:
            self.service_disconnected.emit(service_name, "manual_disconnect")
        
        return success
    
    async def connect_all_services(self) -> Dict[str, bool]:
        """Connect to all services"""
        results = {}
        
        for service_name in self.services.keys():
            results[service_name] = await self.connect_service(service_name)
        
        return results
    
    async def disconnect_all_services(self) -> Dict[str, bool]:
        """Disconnect from all services"""
        results = {}
        
        for service_name in self.services.keys():
            results[service_name] = await self.disconnect_service(service_name)
        
        return results
    
    @handle_errors("integration_hub", "execute_command")
    async def execute_command(self, 
                            service_name: str, 
                            command: str, 
                            parameters: Dict[str, Any] = None) -> Any:
        """Execute command on specific service"""
        if service_name not in self.integrations:
            raise ValueError(f"Unknown service: {service_name}")
        
        service_info = self.services[service_name]
        if not service_info.is_available():
            raise ConnectionError(f"Service not available: {service_name}")
        
        with error_context("integration_hub", "execute_command",
                          service=service_name, command=command):
            
            integration = self.integrations[service_name]
            
            try:
                result = await integration.execute_command(command, parameters or {})
                self.command_completed.emit(service_name, command, result)
                return result
            
            except Exception as e:
                self.command_failed.emit(service_name, command, str(e))
                self.error_handler.handle_error(e, "execute_command",
                                              context={"service": service_name, "command": command})
                raise
    
    # ComfyUI-specific methods
    
    async def submit_comfyui_workflow(self, workflow: Dict[str, Any], batch_size: int = 1) -> Optional[str]:
        """Submit workflow to ComfyUI"""
        try:
            return await self.execute_command("comfyui", "submit_workflow", {
                "workflow": workflow,
                "batch_size": batch_size
            })
        except Exception as e:
            logger.error(f"Failed to submit ComfyUI workflow: {e}")
            return None
    
    async def get_comfyui_history(self) -> Dict[str, Any]:
        """Get ComfyUI execution history"""
        try:
            return await self.execute_command("comfyui", "get_history")
        except Exception as e:
            logger.error(f"Failed to get ComfyUI history: {e}")
            return {}
    
    async def download_comfyui_image(self, filename: str, output_dir: str = "images") -> Optional[Path]:
        """Download image from ComfyUI"""
        try:
            return await self.execute_command("comfyui", "download_image", {
                "filename": filename,
                "output_dir": output_dir
            })
        except Exception as e:
            logger.error(f"Failed to download ComfyUI image: {e}")
            return None
    
    async def download_comfyui_model(self, filename: str, output_dir: str = "models") -> Optional[Path]:
        """Download model from ComfyUI"""
        # Similar to image download but for 3D models
        try:
            # This would need to be implemented in ComfyUI client
            return await self.execute_command("comfyui", "download_model", {
                "filename": filename,
                "output_dir": output_dir
            })
        except Exception as e:
            logger.error(f"Failed to download ComfyUI model: {e}")
            return None
    
    async def get_comfyui_models(self) -> List[str]:
        """Get available models from ComfyUI"""
        try:
            return await self.execute_command("comfyui", "get_models")
        except Exception as e:
            logger.error(f"Failed to get ComfyUI models: {e}")
            return []
    
    # Cinema4D-specific methods
    
    async def create_cinema4d_object(self, object_type: str, parameters: Dict[str, Any] = None) -> bool:
        """Create object in Cinema4D"""
        try:
            result = await self.execute_command("cinema4d", "create_object", {
                "object_type": object_type,
                "parameters": parameters or {}
            })
            return result is not None
        except Exception as e:
            logger.error(f"Failed to create Cinema4D object: {e}")
            return False
    
    async def import_model_to_cinema4d(self, model_path: str) -> bool:
        """Import 3D model to Cinema4D"""
        try:
            result = await self.execute_command("cinema4d", "import_model", {
                "model_path": model_path
            })
            return result is not None
        except Exception as e:
            logger.error(f"Failed to import model to Cinema4D: {e}")
            return False
    
    async def execute_cinema4d_script(self, script: str) -> Any:
        """Execute Python script in Cinema4D"""
        try:
            return await self.execute_command("cinema4d", "execute_script", {
                "script": script
            })
        except Exception as e:
            logger.error(f"Failed to execute Cinema4D script: {e}")
            return None
    
    # Status and information methods
    
    def get_service_status(self, service_name: str) -> Optional[ServiceInfo]:
        """Get status of specific service"""
        return self.services.get(service_name)
    
    def get_all_service_status(self) -> Dict[str, ServiceInfo]:
        """Get status of all services"""
        return self.services.copy()
    
    def get_connected_services(self) -> List[str]:
        """Get list of connected services"""
        return [name for name, info in self.services.items() 
                if info.status == ConnectionStatus.CONNECTED]
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if service is available"""
        service_info = self.services.get(service_name)
        return service_info.is_available() if service_info else False
    
    def are_all_services_connected(self) -> bool:
        """Check if all services are connected"""
        return all(info.status == ConnectionStatus.CONNECTED 
                  for info in self.services.values())
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        total_services = len(self.services)
        connected_services = len(self.get_connected_services())
        
        return {
            "total_services": total_services,
            "connected_services": connected_services,
            "connection_rate": (connected_services / total_services * 100) if total_services > 0 else 0,
            "monitoring_active": self.connection_timer.isActive(),
            "services": {name: {
                "status": info.status.value,
                "last_check": info.last_check,
                "retry_count": info.retry_count,
                "error_message": info.error_message
            } for name, info in self.services.items()}
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        
        # Disconnect all services
        import asyncio
        asyncio.create_task(self.disconnect_all_services())
        
        logger.info("Integration hub cleanup completed")