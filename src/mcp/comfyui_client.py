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
        self.http_client = None  # Create lazily to avoid event loop binding
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
    
    def add_callback(self, event: str, callback: Callable):
        """Add callback for ComfyUI events"""
        if event not in self.callbacks:
            self.logger.warning(f"Unknown event type: {event}")
            return
        
        if callback not in self.callbacks[event]:
            self.callbacks[event].append(callback)
            self.logger.debug(f"Added callback for event: {event}")
    
    def remove_callback(self, event: str, callback: Callable):
        """Remove callback for ComfyUI events"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)
            self.logger.debug(f"Removed callback for event: {event}")
        
    async def _ensure_http_client(self):
        """Ensure HTTP client exists in the current event loop"""
        # Always create a new client if we're in a different event loop
        try:
            current_loop = asyncio.get_running_loop()
            if not hasattr(self, '_last_loop') or self._last_loop != current_loop:
                if self.http_client:
                    try:
                        await self.http_client.aclose()
                    except:
                        pass
                self.http_client = httpx.AsyncClient(timeout=60.0)
                self._last_loop = current_loop
            elif self.http_client is None or self.http_client.is_closed:
                self.http_client = httpx.AsyncClient(timeout=60.0)
        except Exception as e:
            self.logger.error(f"Error ensuring HTTP client: {e}")
            # Fallback: create new client
            self.http_client = httpx.AsyncClient(timeout=60.0)
        
    async def connect(self) -> bool:
        """Connect to ComfyUI server"""
        try:
            # Ensure HTTP client exists in current event loop
            await self._ensure_http_client()
            
            # Test HTTP connection with timeout
            self.logger.info(f"Testing HTTP connection to {self.server_url}")
                
            response = await self.http_client.get(f"{self.server_url}/system_stats", timeout=5.0)
            if response.status_code == 200:
                self.logger.info(f"Connected to ComfyUI at {self.server_url}")
                
                # Start WebSocket connection (non-blocking)
                self._running = True
                self._ws_task = asyncio.create_task(self._websocket_handler())
                
                # Give WebSocket a moment to connect, but don't wait too long
                await asyncio.sleep(0.5)
                
                return True
            else:
                self.logger.error(f"Failed to connect to ComfyUI: HTTP {response.status_code}")
                return False
                
        except asyncio.TimeoutError:
            self.logger.error(f"ComfyUI connection timed out - is ComfyUI running at {self.server_url}?")
            return False
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    async def check_connection(self) -> bool:
        """Check if ComfyUI server is accessible"""
        try:
            # Ensure HTTP client exists in current event loop
            await self._ensure_http_client()
            
            # Quick connection test with short timeout
            response = await self.http_client.get(f"{self.server_url}/system_stats", timeout=3.0)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.debug(f"Connection check failed: {e}")
            return False
    
    async def get_node_types(self) -> Optional[Dict[str, Any]]:
        """Get available node types from ComfyUI"""
        try:
            await self._ensure_http_client()
            response = await self.http_client.get(f"{self.server_url}/object_info")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"Failed to get node types: {e}")
            return None
    
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
                
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        self.logger.info("Disconnected from ComfyUI")
    
    async def _websocket_handler(self):
        """Handle WebSocket connection and messages"""
        while self._running:
            try:
                self.logger.info(f"Attempting WebSocket connection to: {self.websocket_url}")
                
                # Add connection options (removed timeout due to compatibility issues)
                async with websockets.connect(
                    f"{self.websocket_url}?clientId={self.client_id}",
                    ping_interval=20,
                    ping_timeout=10
                ) as ws:
                    self.ws_connection = ws
                    self.logger.info("WebSocket connected to ComfyUI")
                    
                    async for message in ws:
                        await self._handle_ws_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("WebSocket connection closed, reconnecting...")
                await asyncio.sleep(2)
            except asyncio.TimeoutError:
                self.logger.warning("WebSocket connection timed out, retrying...")
                await asyncio.sleep(3)
            except ConnectionRefusedError:
                self.logger.error("ComfyUI WebSocket connection refused - is ComfyUI running?")
                await asyncio.sleep(10)
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
    
    async def load_workflow_to_ui(self, workflow: Dict[str, Any]) -> bool:
        """Load workflow into ComfyUI web interface (without executing)"""
        try:
            await self._ensure_http_client()
            
            # Send workflow to ComfyUI for loading in UI
            # This loads the workflow into the web interface without executing it
            response = await self.http_client.post(
                f"{self.server_url}/api/workflow/load",
                json={"workflow": workflow}
            )
            
            if response.status_code == 200:
                self.logger.info(f"✅ Workflow loaded into ComfyUI web interface")
                self.logger.info(f"🌐 View at: {self.server_url}")
                return True
            else:
                # Fallback: try alternative method
                self.logger.info(f"Standard load failed, trying alternative method...")
                return await self._load_workflow_fallback(workflow)
                
        except Exception as e:
            self.logger.debug(f"Load workflow error: {e}")
            return await self._load_workflow_fallback(workflow)
    
    async def _load_workflow_fallback(self, workflow: Dict[str, Any]) -> bool:
        """Fallback method to load workflow using drag-and-drop"""
        try:
            # Save workflow to a user-accessible location
            import tempfile
            import os
            from pathlib import Path
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Try to save to Desktop first, fallback to temp
            desktop_path = Path.home() / "Desktop"
            if desktop_path.exists():
                workflow_file = desktop_path / f"bridge_workflow_{timestamp}.json"
            else:
                temp_dir = tempfile.gettempdir()
                workflow_file = Path(temp_dir) / f"bridge_workflow_{timestamp}.json"
            
            with open(workflow_file, 'w') as f:
                json.dump(workflow, f, indent=2)
            
            self.logger.info(f"💾 Workflow saved to: {workflow_file}")
            self.logger.info(f"📋 INSTRUCTIONS:")
            self.logger.info(f"  1. ComfyUI should open in your browser")
            self.logger.info(f"  2. Drag the file '{workflow_file.name}' from your Desktop into ComfyUI")
            self.logger.info(f"  3. The workflow will load with your parameters (1024x1024 tiles, 30 steps)")
            
            # Try to open browser automatically
            try:
                import webbrowser
                webbrowser.open(self.server_url)
                self.logger.info(f"🚀 Opened ComfyUI in browser: {self.server_url}")
            except Exception as e:
                self.logger.debug(f"Could not auto-open browser: {e}")
                self.logger.info(f"🌐 Please open ComfyUI manually: {self.server_url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fallback load workflow failed: {e}")
            return False

    async def queue_prompt(self, workflow: Dict[str, Any], 
                          number: int = 1, load_in_ui_first: bool = True) -> Optional[str]:
        """Queue a workflow for execution"""
        try:
            # First, try to load workflow into ComfyUI web interface
            if load_in_ui_first:
                self.logger.info("🔄 Loading workflow into ComfyUI web interface first...")
                await self.load_workflow_to_ui(workflow)
                
                # Give user a moment to see the workflow in browser
                import asyncio
                await asyncio.sleep(2)
            
            prompt = {
                "prompt": workflow,
                "client_id": self.client_id
            }
            
            if number > 1:
                prompt["extra_data"] = {"batch_count": number}
            
            self.logger.debug(f"Queuing prompt with {len(prompt.get('prompt', {}))} nodes")
            
            # Check if ComfyUI web interface is accessible before queuing
            try:
                test_response = await self.http_client.get(self.server_url, timeout=5.0)
                if test_response.status_code == 200:
                    self.logger.info(f"✅ ComfyUI Web Interface ACTIVE: {self.server_url}")
                    self.logger.info("💡 Open the above URL in your browser to watch the workflow execution in real-time!")
                else:
                    self.logger.warning(f"⚠️ ComfyUI web interface returned HTTP {test_response.status_code}")
            except Exception as e:
                self.logger.error(f"❌ ComfyUI web interface NOT accessible: {e}")
                self.logger.error("📋 Make sure ComfyUI is running with: python main.py")
                return None
            
            # Debug: Save the final workflow JSON for comparison
            try:
                import tempfile
                import os
                from datetime import datetime
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = tempfile.gettempdir()
                final_workflow_path = os.path.join(temp_dir, f"comfyui_final_workflow_{timestamp}.json")
                
                with open(final_workflow_path, 'w') as f:
                    json.dump(prompt.get('prompt', {}), f, indent=2)
                
                self.logger.info(f"🔍 SAVED FINAL WORKFLOW for comparison: {final_workflow_path}")
                self.logger.info(f"🔍 Compare this with the original workflow file to see parameter differences")
                
            except Exception as e:
                self.logger.error(f"Failed to save final workflow for comparison: {e}")
            
            # Debug: Check for mesh nodes in the prompt being sent
            for node_id, node_data in prompt.get('prompt', {}).items():
                if isinstance(node_data, dict):
                    class_type = node_data.get('class_type')
                    if class_type == 'Hy3DLoadMesh':
                        mesh_path = node_data.get('inputs', {}).get('glb_path', 'NOT_SET')
                        self.logger.info(f"🚀 SENDING TO COMFYUI: Hy3DLoadMesh node {node_id} glb_path='{mesh_path}'")
                    elif class_type == 'Hy3DUploadMesh':
                        mesh_input = node_data.get('inputs', {}).get('mesh', 'NOT_SET')
                        self.logger.info(f"🚀 SENDING TO COMFYUI: Hy3DUploadMesh node {node_id} mesh='{mesh_input}'")
            
            # Ensure HTTP client exists in current event loop
            await self._ensure_http_client()
            
            response = await self.http_client.post(
                f"{self.server_url}/prompt",
                json=prompt
            )
            
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")
                self.logger.info(f"Workflow queued successfully: {prompt_id}")
                
                # Check queue status to confirm
                try:
                    queue_status = await self.get_queue_status()
                    queue_pending = len(queue_status.get("queue_pending", []))
                    queue_running = len(queue_status.get("queue_running", []))
                    self.logger.debug(f"Queue status: {queue_running} running, {queue_pending} pending")
                    
                    # If no queue activity, check history for errors
                    if queue_running == 0 and queue_pending == 0:
                        self.logger.debug("No workflow in queue - checking history for errors...")
                        try:
                            history_response = await self.http_client.get(f"{self.server_url}/history")
                            if history_response.status_code == 200:
                                history = history_response.json()
                                if prompt_id in history:
                                    history_item = history[prompt_id]
                                    status = history_item.get("status", {})
                                    if "completed" in status:
                                        self.logger.debug(f"Workflow {prompt_id} completed successfully")
                                    elif "error" in status:
                                        error_info = status["error"]
                                        self.logger.error(f"Workflow {prompt_id} failed with error: {error_info}")
                                    else:
                                        self.logger.debug(f"Workflow {prompt_id} status: {status}")
                        except Exception as hist_e:
                            self.logger.debug(f"Could not check history: {hist_e}")
                            
                except Exception as e:
                    self.logger.debug(f"Could not get queue status: {e}")
                
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
    
    async def check_web_interface(self) -> bool:
        """Check if ComfyUI web interface is accessible"""
        try:
            await self._ensure_http_client()
            response = await self.http_client.get(self.server_url, timeout=5.0)
            if response.status_code == 200:
                self.logger.debug(f"ComfyUI web interface is accessible at {self.server_url}")
                
                # Also check if it's the actual ComfyUI interface
                content = response.text
                if "ComfyUI" in content or "queue" in content.lower():
                    self.logger.debug("Confirmed: This is a ComfyUI web interface")
                else:
                    self.logger.warning("URL responds but doesn't appear to be ComfyUI")
                
                return True
            else:
                self.logger.warning(f"ComfyUI web interface returned HTTP {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"ComfyUI web interface not accessible: {e}")
            self.logger.error("Make sure ComfyUI is running: cd ComfyUI && python main.py")
            return False

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            await self._ensure_http_client()
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
            await self._ensure_http_client()
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
            await self._ensure_http_client()
            
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
            # Debug: log current event loop
            try:
                current_loop = asyncio.get_running_loop()
                self.logger.debug(f"get_models called in event loop: {id(current_loop)}")
            except:
                self.logger.debug("get_models called outside event loop")
            
            # Ensure HTTP client exists in current event loop
            await self._ensure_http_client()
            
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
                
                # Find LoRA models
                if "LoraLoader" in object_info:
                    lora_info = object_info["LoraLoader"]["input"]["required"]
                    if "lora_name" in lora_info:
                        models["loras"] = lora_info["lora_name"][0]
                
                # Find embeddings/textual inversions
                if "LoadTextualInversion" in object_info:
                    embedding_info = object_info["LoadTextualInversion"]["input"]["required"]
                    if "embedding_name" in embedding_info:
                        models["embeddings"] = embedding_info["embedding_name"][0]
                
                # Log what we found
                self.logger.info(f"Found models from ComfyUI:")
                self.logger.info(f"  Checkpoints: {len(models['checkpoints'])} models")
                self.logger.info(f"  LoRAs: {len(models['loras'])} models")
                self.logger.info(f"  VAE: {len(models['vae'])} models")
                self.logger.debug(f"  Checkpoint list: {models['checkpoints'][:3]}..." if models['checkpoints'] else "  No checkpoints found")
                self.logger.debug(f"  LoRA list: {models['loras'][:3]}..." if models['loras'] else "  No LoRAs found")
                
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
    
    async def fetch_image(self, image_info: Dict[str, Any]) -> Optional[bytes]:
        """
        Fetch image data from ComfyUI server
        
        Args:
            image_info: Image info dict from ComfyUI callback with keys:
                       - filename: image filename
                       - subfolder: subfolder path
                       - type: image type (temp/output)
        
        Returns:
            Image bytes data or None if failed
        """
        try:
            await self._ensure_http_client()
            
            filename = image_info.get("filename", "")
            subfolder = image_info.get("subfolder", "")
            image_type = image_info.get("type", "output")
            
            if not filename:
                self.logger.error("No filename provided in image_info")
                return None
            
            # Build ComfyUI view URL
            url = f"{self.server_url}/view"
            params = {
                "filename": filename,
                "type": image_type
            }
            if subfolder:
                params["subfolder"] = subfolder
            
            self.logger.debug(f"Fetching image: {filename} from {url}")
            
            response = await self.http_client.get(url, params=params)
            if response.status_code == 200:
                self.logger.debug(f"Successfully fetched image: {filename}")
                return response.content
            else:
                self.logger.error(f"Failed to fetch image {filename}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching image {image_info}: {e}")
            return None