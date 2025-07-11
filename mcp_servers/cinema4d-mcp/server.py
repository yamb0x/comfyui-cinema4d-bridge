#!/usr/bin/env python3

import asyncio
import json
import logging
import socket
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cinema4d-mcp-server")

class Cinema4DMCPServer:
    def __init__(self):
        self.server = Server("cinema4d-mcp-server")
        self.c4d_socket = None
        self.socket_port = 54321
        self.socket_server = None
        self.c4d_connected = False
        
        # Set up server handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="execute_python",
                    description="Execute Python script in Cinema4D",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script": {
                                "type": "string",
                                "description": "Python script to execute in Cinema4D"
                            }
                        },
                        "required": ["script"]
                    }
                ),
                types.Tool(
                    name="import_object",
                    description="Import 3D object into Cinema4D",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to 3D file (OBJ, FBX, etc.)"
                            },
                            "position": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Position [x, y, z]",
                                "default": [0, 0, 0]
                            },
                            "scale": {
                                "type": "number",
                                "description": "Scale factor",
                                "default": 1.0
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="create_primitive",
                    description="Create primitive object in Cinema4D",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "primitive_type": {
                                "type": "string",
                                "enum": ["cube", "sphere", "cylinder", "plane", "cone", "torus"],
                                "description": "Type of primitive to create"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name for the object",
                                "default": "Primitive"
                            },
                            "position": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Position [x, y, z]",
                                "default": [0, 0, 0]
                            },
                            "size": {
                                "type": "number",
                                "description": "Size of the primitive",
                                "default": 100.0
                            }
                        },
                        "required": ["primitive_type"]
                    }
                ),
                types.Tool(
                    name="create_material",
                    description="Create material in Cinema4D",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Material name"
                            },
                            "color": {
                                "type": "array",
                                "items": {"type": "number", "minimum": 0, "maximum": 1},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "RGB color [r, g, b]",
                                "default": [0.8, 0.8, 0.8]
                            },
                            "roughness": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Material roughness",
                                "default": 0.3
                            },
                            "metallic": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Metallic value",
                                "default": 0.0
                            }
                        },
                        "required": ["name"]
                    }
                ),
                types.Tool(
                    name="assign_material",
                    description="Assign material to object",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_name": {
                                "type": "string",
                                "description": "Name of the object"
                            },
                            "material_name": {
                                "type": "string",
                                "description": "Name of the material"
                            }
                        },
                        "required": ["object_name", "material_name"]
                    }
                ),
                types.Tool(
                    name="create_light",
                    description="Create light in Cinema4D",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "light_type": {
                                "type": "string",
                                "enum": ["omni", "spot", "distant", "area"],
                                "description": "Type of light"
                            },
                            "name": {
                                "type": "string",
                                "description": "Light name",
                                "default": "Light"
                            },
                            "position": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "Position [x, y, z]",
                                "default": [0, 200, 0]
                            },
                            "intensity": {
                                "type": "number",
                                "description": "Light intensity",
                                "default": 100.0
                            },
                            "color": {
                                "type": "array",
                                "items": {"type": "number", "minimum": 0, "maximum": 1},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "RGB color [r, g, b]",
                                "default": [1.0, 1.0, 1.0]
                            }
                        },
                        "required": ["light_type"]
                    }
                ),
                types.Tool(
                    name="save_project",
                    description="Save Cinema4D project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to save the project"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="get_scene_objects",
                    description="Get list of objects in the scene",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="get_status",
                    description="Get Cinema4D connection status",
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
                if name == "execute_python":
                    return await self._execute_python(arguments or {})
                elif name == "import_object":
                    return await self._import_object(arguments or {})
                elif name == "create_primitive":
                    return await self._create_primitive(arguments or {})
                elif name == "create_material":
                    return await self._create_material(arguments or {})
                elif name == "assign_material":
                    return await self._assign_material(arguments or {})
                elif name == "create_light":
                    return await self._create_light(arguments or {})
                elif name == "save_project":
                    return await self._save_project(arguments or {})
                elif name == "get_scene_objects":
                    return await self._get_scene_objects()
                elif name == "get_status":
                    return await self._get_status()
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

    def start_socket_server(self):
        """Start socket server for Cinema4D communication"""
        def socket_server_thread():
            try:
                self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket_server.bind(('localhost', self.socket_port))
                self.socket_server.listen(1)
                logger.info(f"Socket server listening on port {self.socket_port}")
                
                while True:
                    try:
                        client_socket, addr = self.socket_server.accept()
                        logger.info(f"Cinema4D connected from {addr}")
                        self.c4d_socket = client_socket
                        self.c4d_connected = True
                        
                        # Keep connection alive
                        while self.c4d_connected:
                            try:
                                data = client_socket.recv(1024)
                                if not data:
                                    break
                                # Handle incoming data from C4D if needed
                            except socket.error:
                                break
                                
                    except socket.error as e:
                        if self.socket_server:
                            logger.error(f"Socket error: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Socket server error: {e}")
            finally:
                self.c4d_connected = False
                if self.c4d_socket:
                    self.c4d_socket.close()
                if self.socket_server:
                    self.socket_server.close()
        
        # Start socket server in background thread
        threading.Thread(target=socket_server_thread, daemon=True).start()

    async def send_to_c4d(self, script: str) -> str:
        """Send Python script to Cinema4D and get response"""
        if not self.c4d_connected or not self.c4d_socket:
            return "Error: Not connected to Cinema4D"
        
        try:
            # Send script
            message = json.dumps({"script": script})
            self.c4d_socket.send(message.encode('utf-8'))
            
            # Receive response
            response = self.c4d_socket.recv(4096).decode('utf-8')
            return response
            
        except Exception as e:
            logger.error(f"Error communicating with Cinema4D: {e}")
            return f"Error: {str(e)}"

    async def _execute_python(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Execute Python script in Cinema4D"""
        script = args.get("script", "")
        if not script:
            return [types.TextContent(type="text", text="No script provided")]
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _import_object(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Import 3D object into Cinema4D"""
        file_path = args.get("file_path", "")
        position = args.get("position", [0, 0, 0])
        scale = args.get("scale", 1.0)
        
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return "No active document"
    
    # Import file
    file_path = r"{file_path}"
    if not c4d.documents.LoadFile(file_path):
        return f"Failed to import file: {{file_path}}"
    
    # Get the imported object (assume it's the last object added)
    obj = doc.GetLastObject()
    if obj:
        obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))
        obj.SetAbsScale(c4d.Vector({scale}, {scale}, {scale}))
        c4d.EventAdd()
        return f"Successfully imported {{file_path}}"
    else:
        return "Failed to find imported object"

if __name__ == '__main__':
    result = main()
    print(result)
"""
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _create_primitive(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Create primitive object"""
        primitive_type = args.get("primitive_type", "cube")
        name = args.get("name", "Primitive")
        position = args.get("position", [0, 0, 0])
        size = args.get("size", 100.0)
        
        # Map primitive types to Cinema4D object IDs
        primitive_map = {
            "cube": "c4d.Ocube",
            "sphere": "c4d.Osphere", 
            "cylinder": "c4d.Ocylinder",
            "plane": "c4d.Oplane",
            "cone": "c4d.Ocone",
            "torus": "c4d.Otorus"
        }
        
        c4d_type = primitive_map.get(primitive_type, "c4d.Ocube")
        
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return "No active document"
    
    # Create primitive
    obj = c4d.BaseObject({c4d_type})
    if not obj:
        return "Failed to create primitive"
    
    obj.SetName("{name}")
    obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))
    
    # Set size parameters based on primitive type
    if "{primitive_type}" == "cube":
        obj[c4d.PRIM_CUBE_LEN] = c4d.Vector({size}, {size}, {size})
    elif "{primitive_type}" == "sphere":
        obj[c4d.PRIM_SPHERE_RAD] = {size}
    elif "{primitive_type}" == "cylinder":
        obj[c4d.PRIM_CYLINDER_RADIUS] = {size/2}
        obj[c4d.PRIM_CYLINDER_HEIGHT] = {size}
    elif "{primitive_type}" == "plane":
        obj[c4d.PRIM_PLANE_WIDTH] = {size}
        obj[c4d.PRIM_PLANE_HEIGHT] = {size}
    elif "{primitive_type}" == "cone":
        obj[c4d.PRIM_CONE_BRAD] = {size/2}
        obj[c4d.PRIM_CONE_HEIGHT] = {size}
    elif "{primitive_type}" == "torus":
        obj[c4d.PRIM_TORUS_OUTERRAD] = {size/2}
        obj[c4d.PRIM_TORUS_INNERRAD] = {size/4}
    
    doc.InsertObject(obj)
    c4d.EventAdd()
    
    return f"Created {{obj.GetName()}} at position {position}"

if __name__ == '__main__':
    result = main()
    print(result)
"""
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _create_material(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Create material"""
        name = args.get("name", "Material")
        color = args.get("color", [0.8, 0.8, 0.8])
        roughness = args.get("roughness", 0.3)
        metallic = args.get("metallic", 0.0)
        
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return "No active document"
    
    # Create material
    mat = c4d.BaseMaterial(c4d.Mmaterial)
    if not mat:
        return "Failed to create material"
    
    mat.SetName("{name}")
    
    # Set color
    mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector({color[0]}, {color[1]}, {color[2]})
    mat[c4d.MATERIAL_USE_COLOR] = True
    
    # Set reflection properties
    mat[c4d.MATERIAL_USE_REFLECTION] = True
    mat[c4d.MATERIAL_REFLECTION_BRIGHTNESS] = {1.0 - roughness}
    
    # Insert material into document
    doc.InsertMaterial(mat)
    c4d.EventAdd()
    
    return f"Created material: {{mat.GetName()}}"

if __name__ == '__main__':
    result = main()
    print(result)
"""
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _assign_material(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Assign material to object"""
        object_name = args.get("object_name", "")
        material_name = args.get("material_name", "")
        
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return "No active document"
    
    # Find object
    obj = doc.SearchObject("{object_name}")
    if not obj:
        return f"Object '{object_name}' not found"
    
    # Find material
    mat = doc.SearchMaterial("{material_name}")
    if not mat:
        return f"Material '{material_name}' not found"
    
    # Create texture tag and assign material
    tag = obj.MakeTag(c4d.Ttexture)
    if tag:
        tag[c4d.TEXTURETAG_MATERIAL] = mat
        c4d.EventAdd()
        return f"Assigned material '{material_name}' to '{object_name}'"
    else:
        return "Failed to create texture tag"

if __name__ == '__main__':
    result = main()
    print(result)
"""
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _create_light(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Create light"""
        light_type = args.get("light_type", "omni")
        name = args.get("name", "Light")
        position = args.get("position", [0, 200, 0])
        intensity = args.get("intensity", 100.0)
        color = args.get("color", [1.0, 1.0, 1.0])
        
        # Map light types
        light_map = {
            "omni": "c4d.Olight",
            "spot": "c4d.Olight", 
            "distant": "c4d.Olight",
            "area": "c4d.Olight"
        }
        
        light_type_map = {
            "omni": "c4d.LIGHT_TYPE_OMNI",
            "spot": "c4d.LIGHT_TYPE_SPOT",
            "distant": "c4d.LIGHT_TYPE_DISTANT", 
            "area": "c4d.LIGHT_TYPE_AREA"
        }
        
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return "No active document"
    
    # Create light
    light = c4d.BaseObject(c4d.Olight)
    if not light:
        return "Failed to create light"
    
    light.SetName("{name}")
    light.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))
    
    # Set light properties
    light[c4d.LIGHT_TYPE] = {light_type_map.get(light_type, "c4d.LIGHT_TYPE_OMNI")}
    light[c4d.LIGHT_BRIGHTNESS] = {intensity}
    light[c4d.LIGHT_COLOR] = c4d.Vector({color[0]}, {color[1]}, {color[2]})
    
    doc.InsertObject(light)
    c4d.EventAdd()
    
    return f"Created {{light.GetName()}} light at position {position}"

if __name__ == '__main__':
    result = main()
    print(result)
"""
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _save_project(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Save project"""
        file_path = args.get("file_path", "")
        
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return "No active document"
    
    file_path = r"{file_path}"
    success = documents.SaveDocument(doc, file_path, c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPORT)
    
    if success:
        return f"Project saved to: {{file_path}}"
    else:
        return f"Failed to save project to: {{file_path}}"

if __name__ == '__main__':
    result = main()
    print(result)
"""
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _get_scene_objects(self) -> List[types.TextContent]:
        """Get scene objects"""
        script = """
import c4d
import json
from c4d import documents

def get_object_info(obj):
    info = {
        "name": obj.GetName(),
        "type": obj.GetTypeName(),
        "position": list(obj.GetAbsPos()),
        "rotation": list(obj.GetAbsRot()),
        "scale": list(obj.GetAbsScale())
    }
    return info

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return "No active document"
    
    objects = []
    obj = doc.GetFirstObject()
    
    while obj:
        objects.append(get_object_info(obj))
        obj = obj.GetNext()
    
    return json.dumps(objects, indent=2)

if __name__ == '__main__':
    result = main()
    print(result)
"""
        
        result = await self.send_to_c4d(script)
        return [types.TextContent(type="text", text=result)]

    async def _get_status(self) -> List[types.TextContent]:
        """Get connection status"""
        status = {
            "connected": self.c4d_connected,
            "socket_port": self.socket_port,
            "has_socket": self.c4d_socket is not None
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(status, indent=2)
        )]

    async def run(self):
        """Run the MCP server"""
        # Start socket server for Cinema4D communication
        self.start_socket_server()
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="cinema4d-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    """Main entry point"""
    server = Cinema4DMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        if server.socket_server:
            server.socket_server.close()

if __name__ == "__main__":
    asyncio.run(main())