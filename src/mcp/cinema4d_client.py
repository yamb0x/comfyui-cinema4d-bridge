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
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Cinema4D MCP connection with simple script"""
        simple_test_script = '''import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    print("SUCCESS: Connection test passed")
    return True

result = main()
print("Result: " + str(result))
'''
        
        self.logger.info("Testing Cinema4D MCP connection...")
        result = await self.execute_python(simple_test_script, max_retries=1)
        
        if result.get("success"):
            self.logger.info("✅ Cinema4D MCP connection test successful")
        else:
            self.logger.warning(f"❌ Cinema4D MCP connection test failed: {result.get('error')}")
        
        return result
    
    async def execute_python(self, script: str) -> Dict[str, Any]:
        """Execute Python script in Cinema4D via socket with enhanced error handling"""
        if not self._connected:
            self.logger.error("Not connected to Cinema4D")
            return {"success": False, "error": "Not connected"}
        
        try:
            import socket
            import json
            
            # Create socket connection with retry logic
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30)
            
            # Connect with error handling
            try:
                client_socket.connect(('localhost', 54321))
            except ConnectionRefusedError:
                return {"success": False, "error": "Cinema4D MCP server not running on port 54321"}
            except socket.timeout:
                return {"success": False, "error": "Connection timeout - Cinema4D may be busy"}
            
            # Prepare and send script (simple protocol - no length prefix)
            message = json.dumps({"script": script})
            message_bytes = message.encode('utf-8')
            
            # Send message directly (matching server expectation)
            client_socket.send(message_bytes)
            
            # Receive response (simple protocol - no length prefix)
            response_data = client_socket.recv(4096)
            
            client_socket.close()
            
            # Parse response with enhanced error handling
            try:
                result = json.loads(response_data.decode('utf-8'))
                
                # Enhanced result validation
                if isinstance(result, dict):
                    return result
                else:
                    # Legacy response format - convert to standard format
                    return {
                        "success": True,
                        "output": str(result),
                        "error": None
                    }
                    
            except json.JSONDecodeError as e:
                # Handle non-JSON responses (legacy Cinema4D responses)
                response_text = response_data.decode('utf-8', errors='ignore')
                self.logger.warning(f"Non-JSON response received: {response_text[:100]}...")
                
                # Try to determine success from response text
                success = "Result: True" in response_text or "SUCCESS" in response_text
                return {
                    "success": success,
                    "output": response_text,
                    "error": None if success else "Script execution may have failed"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to execute script: {e}")
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    async def import_obj(self, obj_path: Path, 
                        position: tuple[float, float, float] = (0, 0, 0),
                        scale: float = 1.0) -> bool:
        """Import 3D model into Cinema4D using proven working pattern"""
        
        # Convert path for Cinema4D
        c4d_path = str(obj_path).replace('\\', '/')
        
        # Use the exact same pattern as the working import_model_to_cloner method
        script = f'''import c4d
from c4d import documents
import time

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Count objects BEFORE import to identify NEW objects
        objects_before = len(doc.GetObjects())
        print("INFO: Objects before import: " + str(objects_before))
        
        # Import model using proven method (same as working quick import)
        model_path = r"{c4d_path}"
        success = c4d.documents.MergeDocument(doc, model_path, c4d.SCENEFILTER_OBJECTS)
        
        if not success:
            print("ERROR: Failed to import model")
            return False
        
        # Find imported object - debug all objects first
        print("DEBUG: All objects in scene after import:")
        all_objects = doc.GetObjects()
        for i, obj in enumerate(all_objects):
            print("  Object " + str(i) + ": '" + obj.GetName() + "' (Type: " + obj.GetTypeName() + ")")
        
        print("INFO: Objects after import: " + str(len(all_objects)))
        
        # Find the actual mesh object (Polygon type, not container) in NEW objects only
        imported_obj = None
        
        def find_mesh_in_hierarchy(obj):
            """Recursively find the actual mesh object (Polygon type)"""
            # Check if this object is a polygon (actual mesh)
            if obj.GetType() == c4d.Opolygon:  # Polygon object
                return obj
            
            # Check children recursively
            child = obj.GetDown()
            while child:
                mesh = find_mesh_in_hierarchy(child)
                if mesh:
                    return mesh
                child = child.GetNext()
            
            return None
        
        # Search through all objects for the newest mesh (back to working pattern)
        for obj in reversed(all_objects):  # Check newest first
            mesh = find_mesh_in_hierarchy(obj)
            if mesh:
                # Check if this mesh already has an ImportedModel name (skip old ones)
                if not mesh.GetName().startswith("ImportedModel_"):
                    imported_obj = mesh
                    print("INFO: Found actual mesh object: " + mesh.GetName() + " (Type: " + mesh.GetTypeName() + ")")
                    break
        
        # Fallback: use the newest object that doesn't have ImportedModel name
        if not imported_obj:
            for obj in reversed(all_objects):
                if not obj.GetName().startswith("ImportedModel_"):
                    imported_obj = obj
                    print("INFO: Using newest non-ImportedModel object: " + imported_obj.GetName())
                    break
        
        if not imported_obj:
            print("ERROR: Could not find imported object after all attempts")
            return False
        
        # Give object a unique name immediately
        unique_name = "ImportedModel_" + str(int(time.time() * 1000000))  # Microsecond precision
        imported_obj.SetName(unique_name)
        print("INFO: Set unique name: " + unique_name)
        
        # Apply transforms using working pattern
        if imported_obj:
            # Set position
            imported_obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))
            
            # Set scale
            imported_obj.SetAbsScale(c4d.Vector({scale}, {scale}, {scale}))
        
        # Update scene (same as working quick import)
        c4d.EventAdd()
        
        print("SUCCESS: Imported " + imported_obj.GetName())
        print("UNIQUE_NAME: " + unique_name)  # For reference
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
        
        result = await self.execute_python(script)
        success = result.get("success", False) and "SUCCESS" in result.get("output", "")
        
        if success:
            self.logger.info(f"Successfully imported {obj_path}")
        else:
            self.logger.error(f"Failed to import {obj_path}")
            self.logger.error(f"Script output: {result.get('output', 'No output')}")
            self.logger.error(f"Script error: {result.get('error', 'No error message')}")
        
        return success
    
    async def import_obj_with_physics(self, obj_path: Path, 
                                     position: tuple[float, float, float] = (0, 0, 0),
                                     scale: float = 1.0,
                                     physics_type: str = "rigid_body",
                                     mass: float = 1.0) -> bool:
        """Import 3D model and immediately apply physics tag to avoid name conflicts"""
        
        # Convert path for Cinema4D
        c4d_path = str(obj_path).replace('\\\\', '/')
        
        # Map physics types to C4D constants
        tag_map = {
            "rigid_body": "c4d.Tdynamicsbody",
            "soft_body": "c4d.Tdynamicsbody", 
            "collider": "c4d.Tcollider"
        }
        
        c4d_constant = tag_map.get(physics_type, "c4d.Tdynamicsbody")
        
        script = f'''import c4d
from c4d import documents
import time

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Get count of objects before import
        objects_before = len(doc.GetObjects())
        
        # Import model using proven method
        model_path = r"{c4d_path}"
        success = c4d.documents.MergeDocument(doc, model_path, c4d.SCENEFILTER_OBJECTS)
        
        if not success:
            print("ERROR: Failed to import model")
            return False
        
        # Get new objects after import
        objects_after = doc.GetObjects()
        print("DEBUG: Objects before: " + str(objects_before) + ", after: " + str(len(objects_after)))
        
        # Debug: show all objects after import
        print("DEBUG: All objects after import:")
        for i, obj in enumerate(objects_after):
            print("  Object " + str(i) + ": '" + obj.GetName() + "' (Type: " + obj.GetTypeName() + ")")
        
        # Find the actual mesh object (not the container)
        imported_obj = None
        if len(objects_after) > objects_before:
            # Look through newly imported objects for the actual mesh (Polygon type)
            new_objects = objects_after[objects_before:]  # Only check new objects
            
            def find_mesh_in_hierarchy(obj):
                """Recursively find the actual mesh object (Polygon type)"""
                # Check if this object is a polygon (actual mesh)
                if obj.GetType() == c4d.Opolygon:  # Polygon object
                    return obj
                
                # Check children recursively
                child = obj.GetDown()
                while child:
                    mesh = find_mesh_in_hierarchy(child)
                    if mesh:
                        return mesh
                    child = child.GetNext()
                
                return None
            
            # Search through new objects for the actual mesh
            for obj in new_objects:
                mesh = find_mesh_in_hierarchy(obj)
                if mesh:
                    imported_obj = mesh
                    print("INFO: Found actual mesh object: " + mesh.GetName() + " (Type: " + mesh.GetTypeName() + ")")
                    break
            
            # Fallback: use the newest object container
            if not imported_obj:
                imported_obj = objects_after[-1]
                print("INFO: Using newest container object: " + imported_obj.GetName())
        
        if not imported_obj:
            print("ERROR: Could not find newly imported object")
            return False
        
        # Give object a unique name immediately
        import time
        unique_name = "ImportedModel_" + str(int(time.time() * 1000000))  # Microsecond precision
        imported_obj.SetName(unique_name)
        print("INFO: Set unique name: " + unique_name)
        
        # Apply transforms immediately
        imported_obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))
        imported_obj.SetAbsScale(c4d.Vector({scale}, {scale}, {scale}))
        
        # Create and apply physics tag immediately to this specific object
        tag = imported_obj.MakeTag({c4d_constant})
        if not tag:
            print("ERROR: Failed to create physics tag")
            return False
        
        tag.SetName("{physics_type}".replace("_", " ").title() + " Tag")
        
        # Set physics properties with fallback
        if "{physics_type}" == "rigid_body":
            try:
                tag[c4d.RIGID_BODY_DYNAMIC] = 1
                tag[c4d.RIGID_BODY_MASS] = {mass}
                print("INFO: Configured rigid body tag with mass " + str({mass}))
            except:
                tag[10001] = 1  # Dynamic
                tag[10002] = {mass}  # Mass
                print("INFO: Configured rigid body tag (numeric) with mass " + str({mass}))
        elif "{physics_type}" == "soft_body":
            try:
                tag[c4d.RIGID_BODY_DYNAMIC] = 1
                tag[c4d.RIGID_BODY_MASS] = {mass}
                print("INFO: Configured soft body tag with mass " + str({mass}))
            except:
                tag[10001] = 1  # Dynamic
                tag[10002] = {mass}  # Mass  
                print("INFO: Configured soft body tag (numeric) with mass " + str({mass}))
        
        # Update scene
        c4d.EventAdd()
        
        print("SUCCESS: Imported " + imported_obj.GetName() + " with " + "{physics_type}" + " tag")
        print("UNIQUE_NAME: " + unique_name)  # For reference
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
        
        result = await self.execute_python(script)
        success = result.get("success", False) and "SUCCESS" in result.get("output", "")
        
        if success:
            self.logger.info(f"Successfully imported {obj_path} with {physics_type} physics")
        else:
            self.logger.error(f"Failed to import {obj_path} with physics")
            self.logger.error(f"Script output: {result.get('output', 'No output')}")
        
        return success
    
    async def test_scene_objects(self) -> Dict[str, Any]:
        """Test script to list all objects in the scene"""
        script = '''import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    print("INFO: Testing scene object listing")
    all_objects = doc.GetObjects()
    print(f"INFO: Found {len(all_objects)} total objects in scene")
    
    for i, obj in enumerate(all_objects):
        print(f"  Object {i}: '{obj.GetName()}' (Type: {obj.GetTypeName()}) (ID: {obj.GetType()})")
    
    print("SUCCESS: Scene object test completed")
    return True

result = main()
print("Result: " + str(result))
'''
        
        return await self.execute_python(script)
    
    async def add_dynamics_tag(self, object_name: str, tag_type: str = "rigid_body", 
                              mass: float = 1.0, bounce: float = 0.3, friction: float = 0.3) -> bool:
        """Add dynamics tag to an existing object"""
        
        # Map tag types to C4D constants
        tag_map = {
            "rigid_body": "c4d.Tdynamicsbody",
            "soft_body": "c4d.Tdynamicsbody", 
            "collider": "c4d.Tcollider"
        }
        
        c4d_constant = tag_map.get(tag_type, "c4d.Tdynamicsbody")
        
        script = f'''import c4d
from c4d import documents

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Find the NEWEST ImportedModel object by timestamp (CRITICAL for multiple imports)
        def find_newest_imported_model():
            best_obj = None
            best_timestamp = 0
            
            # Check all root level objects
            for obj in doc.GetObjects():
                if obj.GetName().startswith("ImportedModel_"):
                    try:
                        timestamp_str = obj.GetName().split("_")[-1]
                        timestamp = int(timestamp_str)
                        if timestamp > best_timestamp:
                            best_timestamp = timestamp
                            best_obj = obj
                    except:
                        pass
                
                # Check one level down for nested objects
                child = obj.GetDown()
                while child:
                    if child.GetName().startswith("ImportedModel_"):
                        try:
                            timestamp_str = child.GetName().split("_")[-1]
                            timestamp = int(timestamp_str)
                            if timestamp > best_timestamp:
                                best_timestamp = timestamp
                                best_obj = child
                        except:
                            pass
                    
                    # Check grandchildren
                    grandchild = child.GetDown()
                    while grandchild:
                        if grandchild.GetName().startswith("ImportedModel_"):
                            try:
                                timestamp_str = grandchild.GetName().split("_")[-1]
                                timestamp = int(timestamp_str)
                                if timestamp > best_timestamp:
                                    best_timestamp = timestamp
                                    best_obj = grandchild
                            except:
                                pass
                        grandchild = grandchild.GetNext()
                    child = child.GetNext()
            
            return best_obj
        
        target_obj = find_newest_imported_model()
        if not target_obj:
            print("ERROR: No ImportedModel found")
            return False
        
        print("INFO: Found target: " + target_obj.GetName())
        
        # Create physics tag
        tag = target_obj.MakeTag({c4d_constant})
        if not tag:
            print("ERROR: Failed to create tag")
            return False
        
        # Set physics properties
        try:
            tag[c4d.RIGID_BODY_DYNAMIC] = 1
            tag[c4d.RIGID_BODY_MASS] = {mass}
        except:
            tag[10001] = 1
            tag[10002] = {mass}
        
        c4d.EventAdd()
        print("SUCCESS: Added tag to " + target_obj.GetName())
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
        
        result = await self.execute_python(script)
        success = result.get("success", False) and "SUCCESS" in result.get("output", "")
        
        if success:
            self.logger.info(f"Successfully added {tag_type} tag to {object_name}")
        else:
            self.logger.error(f"Failed to add {tag_type} tag to {object_name}")
            self.logger.error(f"Script output: {result.get('output', 'No output')}")
        
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
    
    # ===== OPTIMIZED HELPER METHODS FOR PROVEN WORKING PATTERNS =====
    
    async def create_primitive(self, primitive_type: str, name: str = None, 
                              size: tuple[float, float, float] = (100, 100, 100),
                              position: tuple[float, float, float] = (0, 0, 0)) -> Dict[str, Any]:
        """Create primitive object using verified working patterns"""
        
        # Verified object IDs from our testing
        primitive_ids = {
            'cube': 5159,
            'sphere': 5160, 
            'cylinder': 5161,
            'plane': 5162
        }
        
        # Parameter IDs for primitives
        size_params = {
            'cube': 1117,      # PRIM_CUBE_LEN
            'sphere': 1118,    # PRIM_SPHERE_RAD (single value)
            'cylinder': 1120,  # PRIM_CYLINDER_HEIGHT
            'plane': 1121      # PRIM_PLANE_WIDTH
        }
        
        if primitive_type not in primitive_ids:
            return {"success": False, "error": f"Unsupported primitive type: {primitive_type}"}
        
        obj_id = primitive_ids[primitive_type]
        size_param = size_params.get(primitive_type, 1117)
        
        if name is None:
            import time
            name = f"{primitive_type.title()}_{int(time.time() * 1000)}"
        
        # Use proven script pattern with JSON-safe formatting
        script = f'''import c4d
from c4d import documents
import time

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Create object using verified ID
        obj = c4d.BaseObject({obj_id})
        if not obj:
            print("ERROR: Failed to create object")
            return False
        
        obj.SetName("{name}")
        
        # Set size based on primitive type
        if "{primitive_type}" == "sphere":
            obj[{size_param}] = {size[0]}  # Radius only
        else:
            obj[{size_param}] = c4d.Vector({size[0]}, {size[1]}, {size[2]})
        
        # Set position
        obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))
        
        # Insert and update
        doc.InsertObject(obj)
        c4d.EventAdd()
        
        print("SUCCESS: Created " + obj.GetName())
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
        
        return await self.execute_python(script)
    
    async def create_cloner(self, mode: str = "grid", count: int = 25, 
                           spacing: tuple[float, float, float] = (100, 100, 100)) -> Dict[str, Any]:
        """Create MoGraph cloner using verified working patterns"""
        
        # Verified cloner modes
        cloner_modes = {
            'grid': 0,
            'linear': 1, 
            'radial': 2,
            'random': 3
        }
        
        if mode not in cloner_modes:
            return {"success": False, "error": f"Unsupported cloner mode: {mode}"}
        
        mode_id = cloner_modes[mode]
        
        # Use proven cloner script pattern with JSON-safe formatting
        script = f'''import c4d
from c4d import documents
import time

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Create cloner using verified ID
        cloner = c4d.BaseObject(1018544)  # MoGraph Cloner
        if not cloner:
            print("ERROR: Failed to create cloner")
            return False
        
        cloner.SetName("Cloner_{mode}_" + str(int(time.time() * 1000)))
        
        # Set cloner parameters using verified IDs
        cloner[1018617] = {mode_id}  # Mode
        cloner[1018618] = {count}    # Count
        
        # Set spacing if grid mode
        if {mode_id} == 0:  # Grid mode
            cloner[1018619] = c4d.Vector({spacing[0]}, {spacing[1]}, {spacing[2]})  # Grid spacing
        
        # Insert and update
        doc.InsertObject(cloner)
        c4d.EventAdd()
        
        print("SUCCESS: Created cloner with mode {mode}, count {count}")
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
        
        return await self.execute_python(script)
    
    async def import_model_to_cloner(self, model_path: Path, cloner_mode: str = "grid", 
                                    count: int = 25) -> Dict[str, Any]:
        """Import 3D model and add to cloner - our proven working pattern"""
        
        cloner_modes = {'grid': 0, 'linear': 1, 'radial': 2, 'random': 3}
        mode_id = cloner_modes.get(cloner_mode, 0)
        
        # Convert path for Cinema4D
        c4d_path = str(model_path).replace('\\', '/')
        
        # Use our proven working script pattern with JSON-safe formatting
        script = f'''import c4d
from c4d import documents
import time

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Create cloner first
        cloner = c4d.BaseObject(1018544)
        if not cloner:
            print("ERROR: Failed to create cloner")
            return False
        
        cloner.SetName("Model_Cloner_" + str(int(time.time() * 1000)))
        cloner[1018617] = {mode_id}  # Mode
        cloner[1018618] = {count}    # Count
        
        # Import model using proven method
        model_path = r"{c4d_path}"
        success = c4d.documents.MergeDocument(doc, model_path, c4d.SCENEFILTER_OBJECTS)
        
        if not success:
            print("ERROR: Failed to import model")
            return False
        
        # Debug all objects first
        print("DEBUG: All objects in scene after import for cloner:")
        all_objects = doc.GetObjects()
        for i, obj in enumerate(all_objects):
            print("  Object " + str(i) + ": '" + obj.GetName() + "' (Type: " + obj.GetTypeName() + ")")
        
        # Find imported object using the ACTUAL object names from working import
        imported_obj = None
        for obj in doc.GetObjects():
            obj_name = obj.GetName()
            # Look for the actual mesh object "temp.mesh.ply" (skip cloner)
            if ("temp.mesh" in obj_name or ".ply" in obj_name or ".mesh" in obj_name) and obj != cloner:
                imported_obj = obj
                print("INFO: Found mesh object for cloner: " + obj_name)
                break
        
        # Fallback: look for scene hierarchy objects  
        if not imported_obj:
            for obj in all_objects:
                obj_name = obj.GetName().lower()
                if any(pattern in obj_name for pattern in ["scene", "world", "mesh", "model"]) and obj != cloner:
                    # Make sure it's the actual mesh, not a parent container
                    if obj_name not in ["scene 0", "world"]:  # Skip container objects
                        imported_obj = obj
                        print("INFO: Found object by fallback pattern: " + obj.GetName())
                        break
        
        # Last resort: use the newest object (excluding cloner)
        if not imported_obj:
            if all_objects:
                for obj in reversed(all_objects):  # Check newest objects first
                    if obj != cloner:
                        imported_obj = obj
                        print("INFO: Using newest object for cloner: " + imported_obj.GetName())
                        break
        
        if not imported_obj:
            print("ERROR: Could not find imported object after all attempts")
            return False
        
        # Move to cloner using proven method
        imported_obj.Remove()
        imported_obj.InsertUnder(cloner)
        
        # Insert cloner and update
        doc.InsertObject(cloner)
        c4d.EventAdd()
        
        print("SUCCESS: Imported " + imported_obj.GetName() + " to cloner")
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
        
        return await self.execute_python(script)
    
    async def get_scene_info(self) -> Dict[str, Any]:
        """Get comprehensive scene information for debugging"""
        
        script = '''import c4d
from c4d import documents
import json

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return {"error": "No active document"}
    
    scene_info = {
        "document_name": doc.GetDocumentName(),
        "object_count": 0,
        "objects": [],
        "cloners": [],
        "imported_models": []
    }
    
    def process_object(obj, level=0):
        obj_info = {
            "name": obj.GetName(),
            "type": obj.GetTypeName(),
            "type_id": obj.GetType(),
            "level": level,
            "children_count": 0
        }
        
        # Check for specific object types
        if obj.GetType() == 1018544:  # Cloner
            obj_info["is_cloner"] = True
            scene_info["cloners"].append(obj_info)
        elif "Hy3D" in obj.GetName():
            obj_info["is_imported_model"] = True
            scene_info["imported_models"].append(obj_info)
        
        scene_info["objects"].append(obj_info)
        scene_info["object_count"] += 1
        
        # Process children
        child = obj.GetDown()
        while child:
            process_object(child, level + 1)
            obj_info["children_count"] += 1
            child = child.GetNext()
    
    # Process all top-level objects
    obj = doc.GetFirstObject()
    while obj:
        process_object(obj)
        obj = obj.GetNext()
    
    return scene_info

result = main()
print(json.dumps(result, indent=2))
'''
        
        return await self.execute_python(script)
    
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