"""
ComfyUI MCP (Model Context Protocol) Client
Integrates with ComfyUI using the comfyui-mcp-server
"""

import json
import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

import httpx
import websockets
from loguru import logger

from utils.logger import LoggerMixin


class ComfyUIClient(LoggerMixin):
    """
    Client for interacting with ComfyUI through MCP
    Based on https://github.com/joenorton/comfyui-mcp-server
    """
    
    def __init__(self, server_url: str = "http://127.0.0.1:8188", 
                 websocket_url: str = "ws://127.0.0.1:8188/ws"):
        self.server_url = server_url
        self.websocket_url = websocket_url
        self.client_id = str(uuid.uuid4())
        self.ws_connection = None
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.callbacks: Dict[str, List[Callable]] = {
            "progress": [],
            "execution_start": [],
            "execution_complete": [],
            "execution_error": [],
            "image_saved": [],
            "status": []
        }
        self._running = False
        self._ws_task = None
        
    async def connect(self) -> bool:
        """Connect to ComfyUI server"""
        try:
            # Test HTTP connection
            response = await self.http_client.get(f"{self.server_url}/system_stats")
            if response.status_code == 200:
                self.logger.info(f"Connected to ComfyUI at {self.server_url}")
                
                # Start WebSocket connection
                self._running = True
                self._ws_task = asyncio.create_task(self._websocket_handler())
                
                return True
            else:
                self.logger.error(f"Failed to connect to ComfyUI: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from ComfyUI server"""
        self._running = False
        
        if self.ws_connection:
            await self.ws_connection.close()
            
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
                
        await self.http_client.aclose()
        self.logger.info("Disconnected from ComfyUI")
    
    async def _websocket_handler(self):
        """Handle WebSocket connection and messages"""
        while self._running:
            try:
                async with websockets.connect(
                    f"{self.websocket_url}?clientId={self.client_id}"
                ) as ws:
                    self.ws_connection = ws
                    self.logger.info("WebSocket connected to ComfyUI")
                    
                    async for message in ws:
                        await self._handle_ws_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("WebSocket connection closed, reconnecting...")
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)
    
    async def _handle_ws_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "status":
                await self._emit_callback("status", data.get("data", {}))
                
            elif msg_type == "progress":
                progress_data = data.get("data", {})
                self.logger.debug(f"Progress: {progress_data.get('value', 0)}/{progress_data.get('max', 1)}")
                await self._emit_callback("progress", progress_data)
                
            elif msg_type == "executing":
                node = data.get("data", {}).get("node")
                if node:
                    self.logger.debug(f"Executing node: {node}")
                else:
                    # Execution complete
                    await self._emit_callback("execution_complete", {})
                    
            elif msg_type == "executed":
                output = data.get("data", {}).get("output", {})
                if "images" in output:
                    for img in output["images"]:
                        await self._emit_callback("image_saved", img)
                        
            elif msg_type == "execution_start":
                await self._emit_callback("execution_start", data.get("data", {}))
                
            elif msg_type == "execution_error":
                error_data = data.get("data", {})
                self.logger.error(f"Execution error: {error_data}")
                await self._emit_callback("execution_error", error_data)
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _emit_callback(self, event: str, data: Any):
        """Emit callback for event"""
        for callback in self.callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                self.logger.error(f"Callback error for {event}: {e}")
    
    def on(self, event: str, callback: Callable):
        """Register callback for event"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            self.logger.debug(f"Registered callback for {event}")
        else:
            self.logger.warning(f"Unknown event type: {event}")
    
    async def load_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Load workflow from JSON file"""
        try:
            with open(workflow_path, "r") as f:
                workflow = json.load(f)
            self.logger.info(f"Loaded workflow: {workflow_path}")
            return workflow
        except Exception as e:
            self.logger.error(f"Failed to load workflow: {e}")
            raise
    
    async def queue_prompt(self, workflow: Dict[str, Any], 
                          number: int = 1) -> Optional[str]:
        """Queue a workflow for execution"""
        try:
            prompt = {
                "prompt": workflow,
                "client_id": self.client_id
            }
            
            if number > 1:
                prompt["extra_data"] = {"batch_count": number}
            
            self.logger.debug(f"Queuing prompt with {len(prompt.get('prompt', {}))} nodes")
            response = await self.http_client.post(
                f"{self.server_url}/prompt",
                json=prompt
            )
            
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")
                self.logger.info(f"Queued prompt: {prompt_id}")
                return prompt_id
            else:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = f" - {error_data}"
                except:
                    error_detail = f" - {response.text}"
                self.logger.error(f"Failed to queue prompt: HTTP {response.status_code}{error_detail}")
                return None
                
        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout queuing prompt: {e}")
            return None
        except httpx.ConnectError as e:
            self.logger.error(f"Connection error queuing prompt: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error queuing prompt: {e}")
            try:
                self.logger.error(f"Prompt data: {json.dumps(prompt, indent=2)[:500]}...")
            except:
                self.logger.error("Could not serialize prompt data for debugging")
            return None
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            response = await self.http_client.get(f"{self.server_url}/queue")
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get queue status: HTTP {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get queue status: {e}")
            return {}
    
    async def interrupt_execution(self):
        """Interrupt current execution"""
        try:
            response = await self.http_client.post(f"{self.server_url}/interrupt")
            if response.status_code == 200:
                self.logger.info("Execution interrupted")
                return True
            else:
                self.logger.error(f"Failed to interrupt: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to interrupt execution: {e}")
            return False
    
    async def get_history(self, prompt_id: Optional[str] = None) -> Dict[str, Any]:
        """Get execution history"""
        try:
            url = f"{self.server_url}/history"
            if prompt_id:
                url += f"/{prompt_id}"
                
            response = await self.http_client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get history: HTTP {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get history: {e}")
            return {}
    
    async def get_models(self) -> Dict[str, List[str]]:
        """Get available models"""
        try:
            response = await self.http_client.get(f"{self.server_url}/object_info")
            if response.status_code == 200:
                object_info = response.json()
                
                # Extract model lists from various loader nodes
                models = {
                    "checkpoints": [],
                    "vae": [],
                    "loras": [],
                    "embeddings": []
                }
                
                # Find checkpoint models
                if "CheckpointLoaderSimple" in object_info:
                    checkpoint_info = object_info["CheckpointLoaderSimple"]["input"]["required"]
                    if "ckpt_name" in checkpoint_info:
                        models["checkpoints"] = checkpoint_info["ckpt_name"][0]
                
                # Find VAE models
                if "VAELoader" in object_info:
                    vae_info = object_info["VAELoader"]["input"]["required"]
                    if "vae_name" in vae_info:
                        models["vae"] = vae_info["vae_name"][0]
                
                return models
            else:
                self.logger.error(f"Failed to get models: HTTP {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get models: {e}")
            return {}
    
    def inject_prompt_into_workflow(self, workflow: Dict[str, Any], 
                                   positive_prompt: str, 
                                   negative_prompt: str = "") -> Dict[str, Any]:
        """Inject prompts into workflow nodes"""
        workflow_copy = json.loads(json.dumps(workflow))  # Deep copy
        
        # Find and update prompt nodes
        for node_id, node_data in workflow_copy.items():
            class_type = node_data.get("class_type", "")
            
            # Update positive prompt nodes
            if class_type in ["CLIPTextEncode", "CLIPTextEncodeSDXL"]:
                if "positive" in str(node_data.get("_meta", {}).get("title", "")).lower():
                    node_data["inputs"]["text"] = positive_prompt
                    self.logger.debug(f"Updated positive prompt in node {node_id}")
                    
                # Update negative prompt nodes
                elif "negative" in str(node_data.get("_meta", {}).get("title", "")).lower():
                    node_data["inputs"]["text"] = negative_prompt
                    self.logger.debug(f"Updated negative prompt in node {node_id}")
        
        return workflow_copy
    
    def update_workflow_parameters(self, workflow: Dict[str, Any], 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """Update various workflow parameters"""
        workflow_copy = json.loads(json.dumps(workflow))  # Deep copy
        
        for node_id, node_data in workflow_copy.items():
            class_type = node_data.get("class_type", "")
            
            # Update sampler settings
            if class_type in ["KSampler", "KSamplerAdvanced"]:
                if "sampling_steps" in params:
                    node_data["inputs"]["steps"] = params["sampling_steps"]
                if "cfg_scale" in params:
                    node_data["inputs"]["cfg"] = params["cfg_scale"]
                if "sampler" in params:
                    node_data["inputs"]["sampler_name"] = params["sampler"]
                if "scheduler" in params:
                    node_data["inputs"]["scheduler"] = params["scheduler"]
                if "seed" in params:
                    node_data["inputs"]["seed"] = params["seed"]
                    
            # Update image size
            elif class_type == "EmptyLatentImage":
                if "resolution" in params and len(params["resolution"]) == 2:
                    node_data["inputs"]["width"] = params["resolution"][0]
                    node_data["inputs"]["height"] = params["resolution"][1]
                    
            # Update model
            elif class_type == "CheckpointLoaderSimple":
                if "model" in params:
                    node_data["inputs"]["ckpt_name"] = params["model"]
        
        return workflow_copy