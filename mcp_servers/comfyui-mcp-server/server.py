#!/usr/bin/env python3

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from comfyui_client import ComfyUIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("comfyui-mcp-server")

class ComfyUIMCPServer:
    def __init__(self):
        self.server = Server("comfyui-mcp-server")
        self.comfyui_client = ComfyUIClient()
        self.workflows_dir = Path(__file__).parent / "workflows"
        self.workflows_dir.mkdir(exist_ok=True)
        
        # Set up server handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="generate_image",
                    description="Generate an image using ComfyUI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Text prompt for image generation"
                            },
                            "negative_prompt": {
                                "type": "string", 
                                "description": "Negative prompt (optional)",
                                "default": ""
                            },
                            "width": {
                                "type": "integer",
                                "description": "Image width",
                                "default": 1024
                            },
                            "height": {
                                "type": "integer",
                                "description": "Image height", 
                                "default": 1024
                            },
                            "steps": {
                                "type": "integer",
                                "description": "Number of sampling steps",
                                "default": 20
                            },
                            "cfg_scale": {
                                "type": "number",
                                "description": "CFG scale",
                                "default": 7.0
                            },
                            "workflow": {
                                "type": "string",
                                "description": "Workflow filename (optional)",
                                "default": "basic_api_test.json"
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                types.Tool(
                    name="get_models",
                    description="Get available ComfyUI models",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="get_queue_status", 
                    description="Get ComfyUI queue status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="interrupt_execution",
                    description="Interrupt current ComfyUI execution",
                    inputSchema={
                        "type": "object", 
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]]
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool calls"""
            try:
                if name == "generate_image":
                    return await self._generate_image(arguments or {})
                elif name == "get_models":
                    return await self._get_models()
                elif name == "get_queue_status":
                    return await self._get_queue_status()
                elif name == "interrupt_execution":
                    return await self._interrupt_execution()
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

    async def _generate_image(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Generate image using ComfyUI"""
        try:
            # Connect to ComfyUI if not connected
            if not self.comfyui_client._running:
                success = await self.comfyui_client.connect()
                if not success:
                    return [types.TextContent(
                        type="text",
                        text="Failed to connect to ComfyUI. Make sure ComfyUI is running on http://localhost:8188"
                    )]
            
            # Load workflow
            workflow_name = args.get("workflow", "basic_api_test.json")
            workflow_path = self.workflows_dir / workflow_name
            
            if not workflow_path.exists():
                # Try to load from main workflows directory
                main_workflows = Path(__file__).parent.parent.parent / "workflows"
                workflow_path = main_workflows / "generate_images.json"
                
            if not workflow_path.exists():
                return [types.TextContent(
                    type="text", 
                    text=f"Workflow file not found: {workflow_name}"
                )]
            
            workflow = await self.comfyui_client.load_workflow(workflow_path)
            
            # Inject prompts and parameters
            workflow = self.comfyui_client.inject_prompt_into_workflow(
                workflow,
                args["prompt"],
                args.get("negative_prompt", "")
            )
            
            # Update workflow parameters
            params = {
                "resolution": [args.get("width", 1024), args.get("height", 1024)],
                "sampling_steps": args.get("steps", 20),
                "cfg_scale": args.get("cfg_scale", 7.0)
            }
            workflow = self.comfyui_client.update_workflow_parameters(workflow, params)
            
            # Queue the prompt
            prompt_id = await self.comfyui_client.queue_prompt(workflow)
            
            if prompt_id:
                return [types.TextContent(
                    type="text",
                    text=f"Image generation started with prompt ID: {prompt_id}. Monitor progress via WebSocket or check ComfyUI interface."
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="Failed to queue image generation request"
                )]
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error generating image: {str(e)}"
            )]

    async def _get_models(self) -> List[types.TextContent]:
        """Get available models"""
        try:
            if not self.comfyui_client._running:
                success = await self.comfyui_client.connect()
                if not success:
                    return [types.TextContent(
                        type="text",
                        text="Failed to connect to ComfyUI"
                    )]
            
            models = await self.comfyui_client.get_models()
            return [types.TextContent(
                type="text",
                text=json.dumps(models, indent=2)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting models: {str(e)}"
            )]

    async def _get_queue_status(self) -> List[types.TextContent]:
        """Get queue status"""
        try:
            if not self.comfyui_client._running:
                return [types.TextContent(
                    type="text",
                    text="Not connected to ComfyUI"
                )]
            
            status = await self.comfyui_client.get_queue_status()
            return [types.TextContent(
                type="text",
                text=json.dumps(status, indent=2)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting queue status: {str(e)}"
            )]

    async def _interrupt_execution(self) -> List[types.TextContent]:
        """Interrupt execution"""
        try:
            if not self.comfyui_client._running:
                return [types.TextContent(
                    type="text",
                    text="Not connected to ComfyUI"
                )]
            
            success = await self.comfyui_client.interrupt_execution()
            if success:
                return [types.TextContent(
                    type="text",
                    text="Execution interrupted successfully"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="Failed to interrupt execution"
                )]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error interrupting execution: {str(e)}"
            )]

    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="comfyui-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    """Main entry point"""
    server = ComfyUIMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        if server.comfyui_client:
            await server.comfyui_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())