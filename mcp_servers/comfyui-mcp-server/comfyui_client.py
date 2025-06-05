"""
ComfyUI Client for MCP Server
Handles communication with ComfyUI API
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import websockets
from loguru import logger


class ComfyUIClient:
    """Client for communicating with ComfyUI API"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8188"):
        self.server_url = server_url
        self.websocket_url = server_url.replace("http", "ws") + "/ws"
        self.client_id = str(uuid.uuid4())
        self.session = None
        self.ws_connection = None
        self._running = False
        self._ws_task = None
        
    async def connect(self) -> bool:
        """Connect to ComfyUI server"""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
            
            # Test HTTP connection
            async with self.session.get(f"{self.server_url}/system_stats") as response:
                if response.status == 200:
                    logger.info(f"Connected to ComfyUI at {self.server_url}")
                    self._running = True
                    return True
                else:
                    logger.error(f"Failed to connect to ComfyUI: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            if self.session:
                await self.session.close()
                self.session = None
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
                
        if self.session:
            await self.session.close()
            self.session = None
            
        logger.info("Disconnected from ComfyUI")
    
    async def load_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Load workflow from JSON file"""
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)
            logger.info(f"Loaded workflow: {workflow_path}")
            return workflow
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            raise
    
    async def queue_prompt(self, workflow: Dict[str, Any], number: int = 1) -> Optional[str]:
        """Queue a workflow for execution"""
        if not self.session:
            raise RuntimeError("Not connected to ComfyUI")
            
        try:
            prompt = {
                "prompt": workflow,
                "client_id": self.client_id,
                "extra_data": {
                    "extra_pnginfo": {"workflow": workflow}
                }
            }
            
            if number > 1:
                prompt["extra_data"]["batch_count"] = number
            
            async with self.session.post(
                f"{self.server_url}/prompt",
                json=prompt
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    prompt_id = result.get("prompt_id")
                    logger.info(f"Queued prompt: {prompt_id}")
                    return prompt_id
                else:
                    logger.error(f"Failed to queue prompt: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to queue prompt: {e}")
            return None
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        if not self.session:
            return {}
            
        try:
            async with self.session.get(f"{self.server_url}/queue") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get queue status: HTTP {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {}
    
    async def interrupt_execution(self) -> bool:
        """Interrupt current execution"""
        if not self.session:
            return False
            
        try:
            async with self.session.post(f"{self.server_url}/interrupt") as response:
                if response.status == 200:
                    logger.info("Execution interrupted")
                    return True
                else:
                    logger.error(f"Failed to interrupt: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Failed to interrupt execution: {e}")
            return False
    
    async def get_history(self, prompt_id: Optional[str] = None) -> Dict[str, Any]:
        """Get execution history"""
        if not self.session:
            return {}
            
        try:
            url = f"{self.server_url}/history"
            if prompt_id:
                url += f"/{prompt_id}"
                
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get history: HTTP {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {}
    
    async def get_models(self) -> Dict[str, List[str]]:
        """Get available models"""
        if not self.session:
            return {}
            
        try:
            async with self.session.get(f"{self.server_url}/object_info") as response:
                if response.status == 200:
                    object_info = await response.json()
                    
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
                    logger.error(f"Failed to get models: HTTP {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
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
                node_title = str(node_data.get("_meta", {}).get("title", "")).lower()
                
                if "positive" in node_title or node_title == "":
                    # Default to positive if no title specified
                    if "inputs" not in node_data:
                        node_data["inputs"] = {}
                    node_data["inputs"]["text"] = positive_prompt
                    logger.debug(f"Updated positive prompt in node {node_id}")
                    
                # Update negative prompt nodes
                elif "negative" in node_title:
                    if "inputs" not in node_data:
                        node_data["inputs"] = {}
                    node_data["inputs"]["text"] = negative_prompt
                    logger.debug(f"Updated negative prompt in node {node_id}")
        
        return workflow_copy
    
    def update_workflow_parameters(self, workflow: Dict[str, Any], 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """Update various workflow parameters"""
        workflow_copy = json.loads(json.dumps(workflow))  # Deep copy
        
        for node_id, node_data in workflow_copy.items():
            class_type = node_data.get("class_type", "")
            
            # Update sampler settings
            if class_type in ["KSampler", "KSamplerAdvanced"]:
                if "inputs" not in node_data:
                    node_data["inputs"] = {}
                    
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
                if "inputs" not in node_data:
                    node_data["inputs"] = {}
                    
                if "resolution" in params and len(params["resolution"]) == 2:
                    node_data["inputs"]["width"] = params["resolution"][0]
                    node_data["inputs"]["height"] = params["resolution"][1]
                    
            # Update model
            elif class_type == "CheckpointLoaderSimple":
                if "inputs" not in node_data:
                    node_data["inputs"] = {}
                    
                if "model" in params:
                    node_data["inputs"]["ckpt_name"] = params["model"]
        
        return workflow_copy