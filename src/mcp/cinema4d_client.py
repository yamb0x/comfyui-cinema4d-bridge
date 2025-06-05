"""
Cinema4D MCP (Model Context Protocol) Client
Integrates with Cinema4D using the cinema4d-mcp server
"""

import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

import httpx
from loguru import logger

from utils.logger import LoggerMixin


class C4DDeformerType(Enum):
    """Cinema4D deformer types"""
    BEND = "bend"
    TWIST = "twist"
    BULGE = "bulge"
    WIND = "wind"
    DISPLACER = "displacer"
    JIGGLE = "jiggle"
    SPLINE_WRAP = "spline_wrap"
    SQUASH_STRETCH = "squash_stretch"


class C4DClonerMode(Enum):
    """Cinema4D cloner modes"""
    LINEAR = "linear"
    RADIAL = "radial"
    GRID = "grid"
    HONEYCOMB = "honeycomb"
    OBJECT = "object"
    SURFACE = "surface"
    VOLUME = "volume"


class Cinema4DClient(LoggerMixin):
    """
    Client for interacting with Cinema4D through MCP
    Based on https://github.com/ttiimmaacc/cinema4d-mcp
    """
    
    def __init__(self, c4d_path: Path, port: int = 5000):
        self.c4d_path = Path(c4d_path)
        self.c4d_exe = self.c4d_path / "Cinema 4D.exe"
        self.port = port
        self.server_url = f"http://localhost:{port}"
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.c4d_process = None
        self._connected = False
        
    async def connect(self) -> bool:
        """Connect to Cinema4D socket server"""
        try:
            # Check if socket connection is available
            if await self._check_socket_connection():
                self._connected = True
                self.logger.info("Connected to Cinema4D socket server")
                return True
            
            self.logger.warning("Cinema4D socket server not available. Please:")
            self.logger.warning("1. Start Cinema4D")
            self.logger.warning("2. Load c4d_mcp_server.py in Script Manager")
            self.logger.warning("3. Run the script to start socket server")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Cinema4D: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Cinema4D"""
        self._connected = False
        await self.http_client.aclose()
        
        if self.c4d_process:
            self.logger.info("Closing Cinema4D...")
            self.c4d_process.terminate()
            self.c4d_process = None
    
    async def _check_socket_connection(self) -> bool:
        """Check if socket server is running"""
        try:
            import socket
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex(('localhost', 54321))
            test_socket.close()
            return result == 0
        except:
            return False
    
    async def execute_python(self, script: str) -> Dict[str, Any]:
        """Execute Python script in Cinema4D via socket"""
        if not self._connected:
            self.logger.error("Not connected to Cinema4D")
            return {"success": False, "error": "Not connected"}
        
        try:
            import socket
            import json
            
            # Create socket connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30)
            client_socket.connect(('localhost', 54321))
            
            # Send script
            message = json.dumps({"script": script})
            client_socket.send(message.encode('utf-8'))
            
            # Receive response
            response_data = client_socket.recv(4096).decode('utf-8')
            client_socket.close()
            
            # Parse response
            result = json.loads(response_data)
            return result
                
        except Exception as e:
            self.logger.error(f"Failed to execute script: {e}")
            return {"success": False, "error": str(e)}
    
    async def import_obj(self, obj_path: Path, 
                        position: tuple[float, float, float] = (0, 0, 0),
                        scale: float = 1.0) -> bool:
        """Import OBJ file into Cinema4D"""
        script = f"""
import c4d
from c4d import documents, plugins

def main():
    # Get active document
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Import OBJ
    obj_path = r"{obj_path}"
    
    # Load the file
    loaded_objects = c4d.documents.LoadFile(obj_path)
    if not loaded_objects:
        return False
    
    # Insert objects into scene
    for obj in loaded_objects:
        # Set position
        obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))
        
        # Set scale
        obj.SetAbsScale(c4d.Vector({scale}, {scale}, {scale}))
        
        # Insert into document
        doc.InsertObject(obj)
    
    # Update scene
    c4d.EventAdd()
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")
"""
        
        result = await self.execute_python(script)
        success = result.get("success", False) and "SUCCESS" in result.get("output", "")
        
        if success:
            self.logger.info(f"Successfully imported {obj_path}")
        else:
            self.logger.error(f"Failed to import {obj_path}")
        
        return success
    
    async def create_deformer(self, obj_name: str, 
                             deformer_type: C4DDeformerType,
                             params: Dict[str, Any] = None) -> bool:
        """Create and apply a deformer to an object"""
        deformer_map = {
            C4DDeformerType.BEND: "c4d.Obend",
            C4DDeformerType.TWIST: "c4d.Otwist",
            C4DDeformerType.BULGE: "c4d.Obulge",
            C4DDeformerType.WIND: "c4d.Owind",
            C4DDeformerType.DISPLACER: "c4d.Odisplace",
            C4DDeformerType.JIGGLE: "c4d.Ojiggle",
            C4DDeformerType.SPLINE_WRAP: "c4d.Osplinewrap",
            C4DDeformerType.SQUASH_STRETCH: "c4d.Osquash"
        }
        
        params_str = json.dumps(params or {})
        
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Find object by name
    obj = doc.SearchObject("{obj_name}")
    if not obj:
        print(f"Object '{obj_name}' not found")
        return False
    
    # Create deformer
    deformer = c4d.BaseObject({deformer_map[deformer_type]})
    if not deformer:
        return False
    
    # Apply parameters
    params = {params_str}
    for key, value in params.items():
        if hasattr(deformer, key):
            setattr(deformer, key, value)
    
    # Insert deformer as child of object
    deformer.InsertUnder(obj)
    
    # Update scene
    c4d.EventAdd()
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")
"""
        
        result = await self.execute_python(script)
        return result.get("success", False) and "SUCCESS" in result.get("output", "")
    
    async def create_mograph_cloner(self, objects: List[str],
                                   mode: C4DClonerMode,
                                   count: int = 10,
                                   params: Dict[str, Any] = None) -> bool:
        """Create MoGraph cloner with objects"""
        mode_map = {
            C4DClonerMode.LINEAR: "c4d.ID_MG_CLONE_MODE_LINEAR",
            C4DClonerMode.RADIAL: "c4d.ID_MG_CLONE_MODE_RADIAL",
            C4DClonerMode.GRID: "c4d.ID_MG_CLONE_MODE_GRID",
            C4DClonerMode.HONEYCOMB: "c4d.ID_MG_CLONE_MODE_HONEYCOMB",
            C4DClonerMode.OBJECT: "c4d.ID_MG_CLONE_MODE_OBJECT",
            C4DClonerMode.SURFACE: "c4d.ID_MG_CLONE_MODE_SURFACE",
            C4DClonerMode.VOLUME: "c4d.ID_MG_CLONE_MODE_VOLUME"
        }
        
        objects_str = json.dumps(objects)
        params_str = json.dumps(params or {})
        
        script = f"""
import c4d
from c4d import documents
from c4d.modules import mograph

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Create cloner
    cloner = c4d.BaseObject(c4d.Ocloner)
    if not cloner:
        return False
    
    # Set mode
    cloner[c4d.ID_MG_CLONER_MODE] = {mode_map[mode]}
    cloner[c4d.MG_CLONER_COUNT] = {count}
    
    # Apply additional parameters
    params = {params_str}
    for key, value in params.items():
        if hasattr(cloner, key):
            setattr(cloner, key, value)
    
    # Find and add objects
    objects = {objects_str}
    for obj_name in objects:
        obj = doc.SearchObject(obj_name)
        if obj:
            obj.InsertUnder(cloner)
    
    # Insert cloner into document
    doc.InsertObject(cloner)
    
    # Update scene
    c4d.EventAdd()
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")
"""
        
        result = await self.execute_python(script)
        return result.get("success", False) and "SUCCESS" in result.get("output", "")
    
    async def apply_dynamics(self, obj_name: str,
                           body_type: str = "rigid",
                           params: Dict[str, Any] = None) -> bool:
        """Apply dynamics to an object"""
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Find object
    obj = doc.SearchObject("{obj_name}")
    if not obj:
        return False
    
    # Create dynamics tag
    if "{body_type}" == "rigid":
        tag = obj.MakeTag(c4d.Tdynamicsbody)
        tag[c4d.RIGID_BODY_DYNAMIC] = c4d.RIGID_BODY_DYNAMIC_ON
    elif "{body_type}" == "soft":
        tag = obj.MakeTag(c4d.Tsoftbody)
    else:
        return False
    
    # Apply parameters
    params = {json.dumps(params or {})}
    for key, value in params.items():
        if hasattr(tag, key):
            setattr(tag, key, value)
    
    # Update scene
    c4d.EventAdd()
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")
"""
        
        result = await self.execute_python(script)
        return result.get("success", False) and "SUCCESS" in result.get("output", "")
    
    async def save_project(self, project_path: Path) -> bool:
        """Save Cinema4D project"""
        script = f"""
import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Save project
    path = r"{project_path}"
    success = documents.SaveDocument(doc, path, c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPORT)
    
    return success

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")
"""
        
        result = await self.execute_python(script)
        success = result.get("success", False) and "SUCCESS" in result.get("output", "")
        
        if success:
            self.logger.info(f"Project saved to {project_path}")
        else:
            self.logger.error(f"Failed to save project")
        
        return success
    
    async def get_scene_objects(self) -> List[Dict[str, Any]]:
        """Get list of objects in the scene"""
        script = """
import c4d
import json
from c4d import documents

def get_object_info(obj):
    info = {
        "name": obj.GetName(),
        "type": obj.GetTypeName(),
        "id": obj.GetUniqueID(),
        "position": list(obj.GetAbsPos()),
        "rotation": list(obj.GetAbsRot()),
        "scale": list(obj.GetAbsScale()),
        "children": []
    }
    
    # Get children
    child = obj.GetDown()
    while child:
        info["children"].append(get_object_info(child))
        child = child.GetNext()
    
    return info

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return []
    
    objects = []
    obj = doc.GetFirstObject()
    
    while obj:
        objects.append(get_object_info(obj))
        obj = obj.GetNext()
    
    return objects

if __name__ == '__main__':
    objects = main()
    print(json.dumps(objects))
"""
        
        result = await self.execute_python(script)
        if result.get("success") and result.get("output"):
            try:
                return json.loads(result["output"])
            except:
                return []
        return []