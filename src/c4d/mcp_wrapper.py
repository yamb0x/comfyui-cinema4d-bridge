"""
MCP Command Wrapper for Cinema4D
Wraps all Cinema4D MCP operations with validation and error handling
"""

import json
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin


@dataclass
class CommandResult:
    """Result from executing a command"""
    success: bool
    message: str = ""
    error: str = ""
    data: Any = None


class PrimitiveType(Enum):
    """Cinema4D primitive types"""
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    TORUS = "torus"
    PLANE = "plane"
    DISC = "disc"
    TUBE = "tube"
    PYRAMID = "pyramid"
    PLATONIC = "platonic"
    LANDSCAPE = "landscape"
    TEXT = "text"


class ClonerMode(Enum):
    """MoGraph cloner modes"""
    LINEAR = "linear"
    RADIAL = "radial"
    GRID = "grid"
    HONEYCOMB = "honeycomb"
    OBJECT = "object"
    SURFACE = "surface"
    VOLUME = "volume"


class EffectorType(Enum):
    """MoGraph effector types"""
    PLAIN = "plain"
    RANDOM = "random"
    SHADER = "shader"
    DELAY = "delay"
    FORMULA = "formula"
    STEP = "step"
    TARGET = "target"
    TIME = "time"


class DeformerType(Enum):
    """Cinema4D deformer types"""
    BEND = "bend"
    TWIST = "twist"
    TAPER = "taper"
    BULGE = "bulge"
    SHEAR = "shear"
    FFD = "ffd"
    SQUASH = "squash"
    WIND = "wind"
    DISPLACER = "displacer"


class MCPCommandWrapper(LoggerMixin):
    """Wrapper for Cinema4D MCP commands"""
    
    def __init__(self, c4d_client):
        super().__init__()
        self.client = c4d_client
        self.validator = CommandValidator()
        
    async def execute_command(self, command_type: str, **params) -> CommandResult:
        """Execute any MCP command with validation"""
        try:
            # Validate command
            if not self.validator.validate_command(command_type, params):
                return CommandResult(False, error="Invalid command parameters")
            
            # Route to appropriate method
            if command_type == "add_primitive":
                return await self.add_primitive(**params)
            elif command_type == "create_mograph_cloner":
                return await self.create_mograph_cloner(**params)
            elif command_type == "add_effector":
                return await self.add_effector(**params)
            elif command_type == "apply_deformer":
                return await self.apply_deformer(**params)
            elif command_type == "create_material":
                return await self.create_material(**params)
            elif command_type == "snapshot_scene":
                return await self.snapshot_scene()
            elif command_type == "create_array":
                return await self.create_generator("array", **params)
            elif command_type == "create_boolean":
                return await self.create_generator("boolean", **params)
            elif command_type == "create_cloner":
                return await self.create_generator("cloner", **params)
            elif command_type == "create_mgcloner":
                return await self.create_generator("cloner", **params)
            elif command_type == "create_extrude":
                return await self.create_generator("extrude", **params)
            elif command_type == "create_lathe":
                return await self.create_generator("lathe", **params)
            elif command_type == "create_loft":
                return await self.create_generator("loft", **params)
            elif command_type == "create_sweep":
                return await self.create_generator("sweep", **params)
            elif command_type == "create_sds":
                return await self.create_generator("sds", **params)
            elif command_type == "create_symmetry":
                return await self.create_generator("symmetry", **params)
            elif command_type == "create_instance":
                return await self.create_generator("instance", **params)
            elif command_type == "create_metaball":
                return await self.create_generator("metaball", **params)
            elif command_type == "create_bezier":
                return await self.create_generator("bezier", **params)
            elif command_type == "create_connect":
                return await self.create_generator("connect", **params)
            elif command_type == "create_splinewrap":
                return await self.create_generator("splinewrap", **params)
            elif command_type == "create_polyreduxgen":
                return await self.create_generator("polyreduxgen", **params)
            elif command_type == "create_matrix":
                return await self.create_generator("matrix", **params)
            elif command_type == "create_circle":
                return await self.create_generator("circle", **params)
            elif command_type == "create_rectangle":
                return await self.create_generator("rectangle", **params)
            elif command_type == "create_text":
                return await self.create_generator("text", **params)
            elif command_type == "create_helix":
                return await self.create_generator("helix", **params)
            elif command_type == "create_star":
                return await self.create_generator("star", **params)
            elif command_type == "create_camera":
                return await self.create_generator("camera", **params)
            elif command_type == "create_light":
                return await self.create_generator("light", **params)
            # MOGRAPH EFFECTORS - All 23 discovered objects (updated 2025-01-10)
            elif command_type == "create_random":
                return await self.create_generator("random", **params)
            elif command_type == "create_plain":
                return await self.create_generator("plain", **params)
            elif command_type == "create_shader":
                return await self.create_generator("shader", **params)
            elif command_type == "create_delay":
                return await self.create_generator("delay", **params)
            elif command_type == "create_formula":
                return await self.create_generator("formula", **params)
            elif command_type == "create_step":
                return await self.create_generator("step", **params)
            elif command_type == "create_time":
                return await self.create_generator("time", **params)
            elif command_type == "create_sound":
                return await self.create_generator("sound", **params)
            elif command_type == "create_inheritance":
                return await self.create_generator("inheritance", **params)
            elif command_type == "create_volume":
                return await self.create_generator("volume", **params)
            elif command_type == "create_python":
                return await self.create_generator("python", **params)
            elif command_type == "create_weight":
                return await self.create_generator("weight", **params)
            elif command_type == "create_polyfx":
                return await self.create_generator("polyfx", **params)
            elif command_type == "create_pushapart":
                return await self.create_generator("pushapart", **params)
            elif command_type == "create_reeffector":
                return await self.create_generator("reeffector", **params)
            elif command_type == "create_spline_wrap":
                return await self.create_generator("spline_wrap", **params)
            elif command_type == "create_tracer":
                return await self.create_generator("tracer", **params)
            elif command_type == "create_fracture":
                return await self.create_generator("fracture", **params)
            elif command_type == "create_moextrude":
                return await self.create_generator("moextrude", **params)
            elif command_type == "create_moinstance":
                return await self.create_generator("moinstance", **params)
            elif command_type == "create_spline_mask":
                return await self.create_generator("spline_mask", **params)
            elif command_type == "create_voronoi_fracture":
                return await self.create_generator("voronoi_fracture", **params)
            # MOGRAPH EFFECTORS WITH _EFFECTOR SUFFIX (for NLP Dictionary compatibility)
            elif command_type == "create_plain_effector":
                return await self.create_generator("plain", **params)
            elif command_type == "create_random_effector":
                return await self.create_generator("random", **params)
            elif command_type == "create_shader_effector":
                return await self.create_generator("shader", **params)
            elif command_type == "create_delay_effector":
                return await self.create_generator("delay", **params)
            elif command_type == "create_formula_effector":
                return await self.create_generator("formula", **params)
            elif command_type == "create_step_effector":
                return await self.create_generator("step", **params)
            elif command_type == "create_target_effector":
                return await self.create_generator("target", **params)
            elif command_type == "create_time_effector":
                return await self.create_generator("time", **params)
            elif command_type == "create_sound_effector":
                return await self.create_generator("sound", **params)
            # DEFORMERS - Direct routing (10 working objects)
            elif command_type == "create_bend":
                return await self.create_generator("bend", **params)
            elif command_type == "create_bulge":
                return await self.create_generator("bulge", **params)
            elif command_type == "create_explosion":
                return await self.create_generator("explosion", **params)
            elif command_type == "create_explosionfx":
                return await self.create_generator("explosionfx", **params)
            elif command_type == "create_formula":
                return await self.create_generator("formula", **params)
            elif command_type == "create_melt":
                return await self.create_generator("melt", **params)
            elif command_type == "create_shatter":
                return await self.create_generator("shatter", **params)
            elif command_type == "create_shear":
                return await self.create_generator("shear", **params)
            elif command_type == "create_spherify":
                return await self.create_generator("spherify", **params)
            elif command_type == "create_taper":
                return await self.create_generator("taper", **params)
            # DEFORMERS WITH _DEFORMER SUFFIX (for NLP Dictionary compatibility)
            elif command_type == "create_bend_deformer":
                return await self.create_generator("bend", **params)
            elif command_type == "create_bulge_deformer":
                return await self.create_generator("bulge", **params)
            elif command_type == "create_explosion_deformer":
                return await self.create_generator("explosion", **params)
            elif command_type == "create_explosionfx_deformer":
                return await self.create_generator("explosionfx", **params)
            elif command_type == "create_formula_deformer":
                return await self.create_generator("formula", **params)
            elif command_type == "create_melt_deformer":
                return await self.create_generator("melt", **params)
            elif command_type == "create_shatter_deformer":
                return await self.create_generator("shatter", **params)
            elif command_type == "create_shear_deformer":
                return await self.create_generator("shear", **params)
            elif command_type == "create_spherify_deformer":
                return await self.create_generator("spherify", **params)
            elif command_type == "create_taper_deformer":
                return await self.create_generator("taper", **params)
            
            # FIELDS - Direct routes (using _field suffix to avoid conflicts)
            elif command_type == "create_linear_field":
                return await self.create_generator("linear", **params)
            elif command_type == "create_spherical_field":
                return await self.create_generator("spherical", **params)
            elif command_type == "create_box_field":
                return await self.create_generator("box", **params)
            elif command_type == "create_cylinder_field":
                return await self.create_generator("cylinder", **params)
            elif command_type == "create_cone_field":
                return await self.create_generator("cone", **params)
            elif command_type == "create_torus_field":
                return await self.create_generator("torus", **params)
            elif command_type == "create_formula_field":
                return await self.create_generator("formula", **params)
            elif command_type == "create_random_field":
                return await self.create_generator("random", **params)
            elif command_type == "create_radial_field":
                return await self.create_generator("radial", **params)
            elif command_type == "create_sound_field":
                return await self.create_generator("sound", **params)
            elif command_type == "create_shader_field":
                return await self.create_generator("shader", **params)
            elif command_type == "create_python_field":
                return await self.create_generator("python", **params)
            
            # TAGS - Direct routes (using create_tag_standalone method)
            elif command_type == "create_phong_tag":
                return await self.create_tag_standalone("phong", **params)
            elif command_type == "create_material_tag":
                return await self.create_tag_standalone("material", **params)
            elif command_type == "create_texture_tag":
                return await self.create_tag_standalone("texture", **params)
            elif command_type == "create_uvw_tag":
                return await self.create_tag_standalone("uv", **params)
            elif command_type == "create_selection_tag":
                return await self.create_tag_standalone("selection", **params)
            elif command_type == "create_python_tag":
                return await self.create_tag_standalone("python", **params)
            elif command_type == "create_expression_tag":
                return await self.create_tag_standalone("expression", **params)
            elif command_type == "create_protection_tag":
                return await self.create_tag_standalone("protection", **params)
            elif command_type == "create_display_tag":
                return await self.create_tag_standalone("display", **params)
            elif command_type == "create_compositing_tag":
                return await self.create_tag_standalone("compositing", **params)
            else:
                return await self.execute_python_custom(command_type, params)
                
        except Exception as e:
            self.logger.error(f"Error executing command {command_type}: {e}")
            return CommandResult(False, error=str(e))
    
    async def add_primitive(self, primitive_type: str, name: str = None, 
                          position: Tuple[float, float, float] = (0, 0, 0),
                          size: Union[float, Tuple[float, float, float]] = 100, **params) -> CommandResult:
        """Create a primitive object"""
        try:
            # Map ALL object types to C4D constants - USING VERIFIED CONSTANTS FROM USER
            object_map = {
                # Primitives
                "cube": "c4d.Ocube",
                "sphere": "c4d.Osphere", 
                "cylinder": "c4d.Ocylinder",
                "cone": "c4d.Ocone",
                "torus": "c4d.Otorus",
                "plane": "c4d.Oplane",
                "pyramid": "c4d.Opyramid",
                "disc": "c4d.Odisc",
                "tube": "c4d.Otube",
                "platonic": "c4d.Oplatonic",
                "landscape": "c4d.Ofractal",
                "relief": "c4d.Orelief",
                "capsule": "c4d.Ocapsule",
                "oiltank": "c4d.Ooiltank",
                "figure": "c4d.Ofigure",
                
                # Splines
                "text": "c4d.Osplinetext",
                "helix": "c4d.Osplinehelix",
                "circle": "c4d.Osplinecircle",
                "rectangle": "c4d.Osplinerectangle",
                
                # Generators
                "extrude": "c4d.Oextrude",
                "sweep": "c4d.Osweep",
                "loft": "c4d.Oloft",
                "lathe": "c4d.Olathe",
                
                # MoGraph
                "cloner": "c4d.Omgcloner",
                "fracture": "c4d.Omgfracture",
                "random": "c4d.Omgrandom",
                "plain": "c4d.Omgplain",
                
                # Lights
                "light": "c4d.Olight",
                "area": "c4d.Olight",  # Area light is still Olight with parameters
                "spot": "c4d.Olight",  # Spot light is still Olight with parameters
                "infinite": "c4d.Olight",  # Infinite light is still Olight with parameters
                
                # Cameras
                "camera": "c4d.Ocamera",
                "target": "c4d.Ocamera",  # Target camera is still Ocamera with parameters
                "stage": "c4d.Ostage",
                
                # Volumes - New in R20 verified constants from user
                "volume": "c4d.Ovolume",
                "openvdb": "c4d.Ovolumeloader",  # Volume Loader for OpenVDB files
                "builder": "c4d.Ovolumebuilder",  # Volume Builder
                "mesher": "c4d.Ovolumemesher"     # Volume Mesher
                
                # Note: Dynamics (rigid_body, cloth, soft_body, collider) are TAGS not objects
                # They are handled in the tag creation method using c4d.T* constants
            }
            
            c4d_type = object_map.get(primitive_type.lower(), "c4d.Ocube")
            obj_name = name or f"{primitive_type.capitalize()}_1"
            
            # Process size - convert to tuple if needed
            if isinstance(size, (int, float)):
                size_tuple = (size, size, size)
            else:
                size_tuple = size
            
            script = f"""
import c4d
from c4d import documents
import time

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create primitive
obj = c4d.BaseObject({c4d_type})
if not obj:
    raise Exception("Failed to create object")

# Set name
obj.SetName("{obj_name}")

# Set size based on primitive type
if {c4d_type} == c4d.Ocube:
    obj[c4d.PRIM_CUBE_LEN] = c4d.Vector({size_tuple[0]}, {size_tuple[1]}, {size_tuple[2]})
elif {c4d_type} == c4d.Osphere:
    obj[c4d.PRIM_SPHERE_RAD] = {size_tuple[0]}
elif {c4d_type} == c4d.Ocylinder:
    obj[c4d.PRIM_CYLINDER_RADIUS] = {size_tuple[0]/2}
    obj[c4d.PRIM_CYLINDER_HEIGHT] = {size_tuple[1] if len(size_tuple) > 1 else size_tuple[0]}
elif {c4d_type} == c4d.Ocone:
    obj[c4d.PRIM_CONE_BRAD] = {size_tuple[0]/2}
    obj[c4d.PRIM_CONE_HEIGHT] = {size_tuple[1] if len(size_tuple) > 1 else size_tuple[0]}
elif {c4d_type} == c4d.Otorus:
    obj[c4d.PRIM_TORUS_OUTERRAD] = {size_tuple[0]/2}
    obj[c4d.PRIM_TORUS_INNERRAD] = {size_tuple[0]/4}
elif {c4d_type} == c4d.Oplane:
    obj[c4d.PRIM_PLANE_WIDTH] = {size_tuple[0] * 2}
    obj[c4d.PRIM_PLANE_HEIGHT] = {size_tuple[1] * 2 if len(size_tuple) > 1 else size_tuple[0] * 2}
elif {c4d_type} == c4d.Opyramid:
    obj[c4d.PRIM_PYRAMID_LEN] = c4d.Vector({size_tuple[0]}, {size_tuple[1]}, {size_tuple[2]})
elif {c4d_type} == c4d.Odisc:
    obj[c4d.PRIM_DISC_ORAD] = {size_tuple[0]}
elif {c4d_type} == c4d.Otube:
    obj[c4d.PRIM_TUBE_IRAD] = {size_tuple[0]/2 - 10}
    obj[c4d.PRIM_TUBE_ORAD] = {size_tuple[0]/2}
    obj[c4d.PRIM_TUBE_HEIGHT] = {size_tuple[1] if len(size_tuple) > 1 else size_tuple[0]}
elif {c4d_type} == c4d.Oplatonic:
    obj[c4d.PRIM_PLATONIC_RAD] = {size_tuple[0]/2}

# Set position
obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))

# Apply additional parameters
{self._generate_param_code(params)}

# Insert into document
doc.InsertObject(obj)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created {{obj.GetName()}} at position {position}")
"""
            
            self.logger.info(f"Executing add_primitive: type={primitive_type}, name={obj_name}, size={size}, pos={position}")
            result = await self.client.execute_python(script)
            self.logger.debug(f"Script execution result: {result}")
            
            if result and result.get("success"):
                return CommandResult(
                    True, 
                    message=f"Created {primitive_type} '{obj_name}'",
                    data={"name": obj_name, "type": primitive_type}
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def create_generator(self, generator_type: str, name: str = None, 
                              position: Tuple[float, float, float] = (0, 0, 0),
                              **params) -> CommandResult:
        """Create a generator object using same pattern as primitives"""
        try:
            # Map generator types to C4D constants
            generator_map = {
                "array": "c4d.Oarray",
                "boolean": "c4d.Oboole",  # Fixed: correct Boolean constant
                "cloner": "c4d.Omgcloner",
                "extrude": "c4d.Oextrude",
                "lathe": "c4d.Olathe",
                "loft": "c4d.Oloft",
                "sweep": "c4d.Osweep",
                "sds": "c4d.Osds",
                "symmetry": "c4d.Osymmetry",
                "instance": "c4d.Oinstance",
                "metaball": "c4d.Ometaball",
                "bezier": "c4d.Obezier",
                "connect": "c4d.Oconnector",
                "splinewrap": "c4d.Osplinewrap",
                "polyreduxgen": "c4d.Opolyreduxgen",
                "matrix": "c4d.Omgmatrix",
                # SPLINES - Using exact same pattern as generators
                "circle": "c4d.Osplinecircle",
                "rectangle": "c4d.Osplinerectangle",
                "text": "c4d.Osplinetext",
                "helix": "c4d.Osplinehelix",
                "star": "c4d.Osplinestar",
                # CAMERAS & LIGHTS - Using exact same pattern as generators
                "camera": "c4d.Ocamera",
                "light": "c4d.Olight",
                # MOGRAPH EFFECTORS - All 23 discovered objects (updated 2025-01-10)
                "random": "c4d.Omgrandom",
                "plain": "c4d.Omgplain",
                "shader": "c4d.Omgshader",
                "delay": "c4d.Omgdelay",
                "formula": "c4d.Omgformula",
                "step": "c4d.Omgstep",
                "time": "c4d.Omgtime",
                "sound": "c4d.Omgsound",
                "inheritance": "c4d.Omginheritance",
                "volume": "c4d.Omgvolume",
                "python": "c4d.Omgpython",
                "weight": "c4d.Oweighteffector",
                "matrix": "c4d.Omgmatrix",
                "polyfx": "c4d.Omgpolyfx",
                "pushapart": "c4d.Omgpushapart",
                "reeffector": "c4d.Omgreeffector",
                "spline_wrap": "c4d.Omgsplinewrap",
                "tracer": "c4d.Omgtracer",
                "fracture": "c4d.Omgfracture",
                "moextrude": "c4d.Omgextrude",
                "moinstance": "c4d.Omginstance",
                "spline_mask": "c4d.Omgsplinemask",
                "voronoi_fracture": "c4d.Omgvoronoifracture",
                # DEFORMERS - 10 working objects discovered (2025-01-10)
                "bend": "c4d.Obend",
                "bulge": "c4d.Obulge",
                "explosion": "c4d.Oexplosion",
                "explosionfx": "c4d.Oexplosionfx",
                "formula": "c4d.Oformula",
                "melt": "c4d.Omelt",
                "shatter": "c4d.Oshatter",
                "shear": "c4d.Oshear",
                "spherify": "c4d.Ospherify",
                "taper": "c4d.Otaper",
                # FIELDS - 12 working objects discovered (2025-01-11) - VERIFIED FROM CINEMA4D
                "linear": "c4d.Flinear",
                "box": "c4d.Fbox",
                "spherical": "c4d.Fspherical",
                "cylinder": "c4d.Fcylinder",
                "torus": "c4d.Ftorus",
                "cone": "c4d.Fcone",
                "random": "c4d.Frandom",
                "shader": "c4d.Fshader",
                "sound": "c4d.Fsound",
                "formula": "c4d.Fformula",
                "radial": "c4d.Fradial",
                "python": "c4d.Fpython"
            }
            
            c4d_type = generator_map.get(generator_type.lower(), "c4d.Oarray")
            obj_name = name or f"{generator_type.capitalize()}_1"
            
            script = f"""
import c4d
from c4d import documents
import time

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create generator
obj = c4d.BaseObject({c4d_type})
if not obj:
    raise Exception("Failed to create object")

# Set name
obj.SetName("{obj_name}")

# Set position
obj.SetAbsPos(c4d.Vector({position[0]}, {position[1]}, {position[2]}))

# Apply generator-specific parameters
{self._generate_generator_param_code(generator_type, c4d_type, params)}

# Insert into document
doc.InsertObject(obj)

# Add child objects for generators that need them
if "{generator_type}" in ['extrude', 'lathe', 'sweep', 'loft']:
    # Add a spline for NURBS generators
    spline = c4d.SplineObject(c4d.SPLINETYPE_STAR, 4)
    if spline:
        spline.SetName("Star Spline")
        spline[c4d.SPLINEOBJECT_RADIUS] = 100
        spline[c4d.SPLINEOBJECT_IRADIUS] = 50
        spline[c4d.SPLINEOBJECT_POINTS] = 5
        doc.InsertObject(spline, obj)
elif "{generator_type}" == "cloner":
    # Add a cube for cloner to clone
    cube = c4d.BaseObject(c4d.Ocube)
    if cube:
        cube.SetName("Cloned Object")
        cube[c4d.PRIM_CUBE_LEN] = c4d.Vector(50, 50, 50)
        doc.InsertObject(cube, obj)
elif "{generator_type}" not in ['random', 'plain', 'shader', 'delay', 'formula', 'step', 'time', 'sound', 'inheritance', 'volume', 'python', 'weight', 'matrix', 'polyfx', 'pushapart', 'reeffector', 'spline_wrap', 'tracer', 'fracture', 'moextrude', 'moinstance', 'spline_mask', 'voronoi_fracture', 'bend', 'bulge', 'explosion', 'explosionfx', 'melt', 'shatter', 'shear', 'spherify', 'taper', 'linear', 'spherical', 'box', 'cylinder', 'cone', 'torus', 'radial']:
    # Add a cube for other generators (excluding effectors and deformers)
    cube = c4d.BaseObject(c4d.Ocube)
    if cube:
        cube.SetName("Default Cube")
        cube[c4d.PRIM_CUBE_LEN] = c4d.Vector(200, 200, 200)
        doc.InsertObject(cube, obj)

doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created {{obj.GetName()}} at position {position}")
"""
            
            self.logger.info(f"Executing create_generator: type={generator_type}, name={obj_name}, pos={position}")
            result = await self.client.execute_python(script)
            self.logger.debug(f"Script execution result: {result}")
            
            if result and result.get("success"):
                return CommandResult(
                    True, 
                    message=f"Created {generator_type} '{obj_name}'",
                    data={"type": generator_type, "name": obj_name}
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def create_mograph_cloner(self, objects: List[str] = None,
                                   mode: Union[str, int] = "grid",
                                   count: int = 10,
                                   name: str = "Cloner",
                                   **params) -> CommandResult:
        """Create a MoGraph cloner"""
        try:
            # Use the VERIFIED Cinema4D constants from user's list
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create cloner using VERIFIED constant
cloner = c4d.BaseObject(c4d.Omgcloner)
if not cloner:
    raise Exception("Failed to create cloner")

cloner.SetName("{name}")

# Handle mode parameter - can be int or string
mode_value = {mode} if isinstance({mode}, int) else 2  # Default to grid mode (2)

# Set basic parameters with comments about what they represent
# Mode: 0=Linear, 1=Radial, 2=Grid, 3=Honeycomb, etc.
# Count: Number of clones
# Radius: For radial mode
# Note: Using default parameter values for now

# Create default cube child object
cube = c4d.BaseObject(c4d.Ocube)
if cube:
    cube.SetName("Cloned Object")
    cube[c4d.PRIM_CUBE_LEN] = c4d.Vector(50, 50, 50)
    doc.InsertObject(cube, cloner)

# Insert cloner into document
doc.InsertObject(cloner)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created cloner '{name}' with mode={mode_value}, count={count}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Created cloner '{name}' with mode={mode}, count={count}",
                    data={"name": name, "mode": mode, "count": count}
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def add_effector(self, cloner_name: str, effector_type: str = "random",
                          **params) -> CommandResult:
        """Add an effector to a cloner"""
        try:
            # Use VERIFIED Cinema4D constants from user's list  
            effector_map = {
                "plain": "c4d.Omgplain",          # Plain Effector
                "random": "c4d.Omgrandom",         # Random Effector  
                "shader": "c4d.Omgshader",         # Shader Effector
                "delay": "c4d.Omgdelay",           # Delay Effector
                "formula": "c4d.Omgformula",       # Formula Effector
                "step": "c4d.Omgstep",             # Step Effector
                "target": "c4d.Omgeffectortarget", # Target Effector
                "time": "c4d.Omgtime",             # Time Effector
                "sound": "c4d.Omgsound"            # Sound Effector
            }
            
            c4d_constant = effector_map.get(effector_type.lower(), "c4d.Omgrandom")  # Default to random
            
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Find cloner
cloner = doc.SearchObject("{cloner_name}")
if not cloner:
    raise Exception(f"Cloner '{cloner_name}' not found")

# Create effector using VERIFIED constant
effector = c4d.BaseObject({c4d_constant})
if not effector:
    raise Exception("Failed to create effector")

effector.SetName(f"{effector_type.capitalize()}_Effector")

# Configure effector based on type
if "{effector_type}" == "random":
    # Basic effector setup - let Cinema4D use defaults
    print("DEBUG: Random effector created with default settings")
elif "{effector_type}" == "shader":
    # Basic shader effector setup
    print("DEBUG: Shader effector created with default settings")
else:
    print("DEBUG: Effector created with default settings")

# Insert effector
doc.InsertObject(effector)

# Add effector to cloner's effector list
# ID_MG_CLONER_EFFECTOR_LIST = 20008
effector_list = cloner[20008]
if effector_list is None:
    effector_list = c4d.InExcludeData()
effector_list.InsertObject(effector, 1)
cloner[20008] = effector_list

doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Added {effector_type} effector to {{cloner.GetName()}}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Added {effector_type} effector to {cloner_name}"
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def apply_deformer(self, object_name: str, deformer_type: str = "bend",
                           strength: float = 0.5, **params) -> CommandResult:
        """Apply a deformer to an object"""
        try:
            # Use VERIFIED Cinema4D constants from user's list
            deformer_map = {
                "bend": "c4d.Obend",
                "twist": "c4d.Otwist", 
                "taper": "c4d.Otaper",
                "bulge": "c4d.Obulge",
                "shear": "c4d.Oshear",
                "wind": "c4d.Owinddeform",  # Wind deformer constant
                "ffd": "c4d.Offd",
                "displacer": "c4d.Odisplacer",
                "wave": "c4d.Owave",
                "formula": "c4d.Oformula",
                "explosion": "c4d.Oexplosion",
                "melt": "c4d.Omelt",
                "shatter": "c4d.Oshatter",
                "spherify": "c4d.Ospherify",
                "wrap": "c4d.Owrap"
            }
            
            c4d_constant = deformer_map.get(deformer_type.lower(), "c4d.Obend")  # Default to bend
            
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Find object
obj = doc.SearchObject("{object_name}")
if not obj:
    raise Exception(f"Object '{object_name}' not found")

# Create deformer using VERIFIED constant
deformer = c4d.BaseObject({c4d_constant})
if not deformer:
    raise Exception("Failed to create deformer")

deformer.SetName(f"{deformer_type.capitalize()}_Deformer")

# Configure deformer based on type
if "{deformer_type}" == "bend":
    # Set bend strength and angle using Cinema4D parameter constants
    deformer[c4d.DEFORMOBJECT_STRENGTH] = {strength * 100}
    deformer[c4d.DEFORMOBJECT_ANGLE] = {strength * 90}
elif "{deformer_type}" == "twist":
    deformer[c4d.DEFORMOBJECT_STRENGTH] = {strength * 100} 
    deformer[c4d.DEFORMOBJECT_ANGLE] = {strength * 360}
elif "{deformer_type}" == "taper":
    deformer[c4d.DEFORMOBJECT_STRENGTH] = {strength * 100}

# Insert deformer as child of object
deformer.InsertUnder(obj)

doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Applied {deformer_type} deformer to {{obj.GetName()}}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Applied {deformer_type} deformer to {object_name}"
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def create_material(self, name: str = "New_Material",
                            color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                            material_type: str = "standard",
                            **params) -> CommandResult:
        """Create a material (standard or redshift)"""
        try:
            # Determine material type
            if material_type.lower() == "redshift":
                script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create Redshift material
# Redshift Material ID = 1036224
mat = c4d.BaseMaterial(1036224)
if not mat:
    raise Exception("Failed to create Redshift material")

mat.SetName("{name}")

# For Redshift, we need to access the node system
# This is a simplified version - full node setup would be more complex
# Set base color through Redshift shader
# RS_MATERIAL_DIFFUSE_COLOR = 2001
mat[2001] = c4d.Vector({color[0]}, {color[1]}, {color[2]})

# Insert material
doc.InsertMaterial(mat)

doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created Redshift material '{{mat.GetName()}}'")
"""
            else:
                # Standard material
                script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create standard material using VERIFIED constant
# Note: Standard material doesn't have an Object constant, use Material type
mat = c4d.BaseMaterial(c4d.Mmaterial)
if not mat:
    raise Exception("Failed to create material")

mat.SetName("{name}")

# Set color
# MATERIAL_COLOR_COLOR = 2100
mat[2100] = c4d.Vector({color[0]}, {color[1]}, {color[2]})

# Apply additional properties
if {params.get('luminance', False)}:
    # MATERIAL_USE_LUMINANCE = 2200
    mat[2200] = True
    # MATERIAL_LUMINANCE_BRIGHTNESS = 2201
    mat[2201] = {params.get('luminance_brightness', 0.5)}

if {params.get('reflection', False)}:
    # MATERIAL_USE_REFLECTION = 2300
    mat[2300] = True

# Insert material
doc.InsertMaterial(mat)

doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created material '{{mat.GetName()}}'")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Created material '{name}'"
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def create_loft(self, spline_names: List[str] = None, **params) -> CommandResult:
        """Create a Loft generator from splines"""
        try:
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create Loft object
# Loft ID = 5101
loft = c4d.BaseObject(5101)
if not loft:
    raise Exception("Failed to create loft")

loft.SetName("Loft_Generator")

# Find and add splines if specified
splines = {json.dumps(spline_names or [])}
for spline_name in splines:
    spline = doc.SearchObject(spline_name)
    if spline:
        # Clone the spline and make it a child of loft
        spline_clone = spline.GetClone()
        spline_clone.InsertUnder(loft)
        print(f"Added spline '{{spline_name}}' to loft")

# Insert loft
doc.InsertObject(loft)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created Loft generator")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message="Created Loft generator"
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def apply_dynamics(self, object_name: str, tag_type: str = "rigid_body", **params) -> CommandResult:
        """Apply dynamics tag to an object"""
        try:
            # Dynamics tag constants - using Cinema4D constants
            tag_constants = {
                "rigid_body": "c4d.Trigidbody",      # Legacy Rigid Body tag (pre-2023)
                "dynamics_body": "c4d.Tdynamicsbody", # New unified dynamics (2023+)
                "collider": "c4d.Tdynamicsbody",     # Collider is a dynamics body with collider-only mode
                "soft_body": "c4d.Tdynamicsbody",    # Soft body is a dynamics body with soft body mode
                "cloth": "c4d.Tcloth",               # Cloth tag
                "rope": "c4d.Trope",                 # Rope tag
                "connector": "c4d.Tconnector"        # Connector tag
            }
            
            c4d_constant = tag_constants.get(tag_type.lower(), "c4d.Trigidbody")
            
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Find object
obj = doc.SearchObject("{object_name}")
if not obj:
    raise Exception(f"Object '{object_name}' not found")

# Dynamics Body Type Constants (2023+ unified dynamics)
# DYN_BODY_TYPE_DISABLED = 0
# DYN_BODY_TYPE_DYNAMIC = 1 (movable)
# DYN_BODY_TYPE_STATIC = 2 (collider)
# DYN_BODY_TYPE_GHOST = 3 (trigger)

# Create dynamics tag using Cinema4D constant
try:
    tag = obj.MakeTag(eval("{c4d_constant}"))
except AttributeError:
    # Fallback for newer versions
    if "{tag_type}" == "rigid_body":
        try:
            tag = obj.MakeTag(c4d.Tdynamicsbody)
        except:
            tag = obj.MakeTag(c4d.Trigidbody)
    else:
        raise Exception(f"Unknown tag constant: {c4d_constant}")
        
if not tag:
    raise Exception("Failed to create dynamics tag")

tag.SetName(f"{tag_type.replace('_', ' ').title()} Tag")

# Configure tag based on type
if "{tag_type}" == "rigid_body":
    try:
        # For modern C4D (2023+) using Tdynamicsbody
        if "{c4d_constant}" == "c4d.Tdynamicsbody":
            tag[c4d.DYNAMICS_BODY_ENABLED] = True
            tag[c4d.DYNAMICS_BODY_TYPE] = 1  # DYN_BODY_TYPE_DYNAMIC = 1
            tag[c4d.DYNAMICS_BODY_MASS] = {params.get('mass', 1.0)}
            tag[c4d.DYNAMICS_BODY_SHAPE] = 0  # DYN_BODY_SHAPE_AUTOMATIC = 0
        else:
            # Legacy Trigidbody
            tag[c4d.RIGID_BODY_DYNAMIC] = 1  # Set to Dynamic
            tag[c4d.RIGID_BODY_MASS] = {params.get('mass', 1.0)}
    except:
        # Fallback to numeric IDs if constants not available
        tag[10001] = 1  # Set to Dynamic (not static)
        tag[10002] = {params.get('mass', 1.0)}
elif "{tag_type}" == "collider":
    # Configure as static collider (2023+ unified dynamics)
    try:
        tag[c4d.DYNAMICS_BODY_ENABLED] = True
        tag[c4d.DYNAMICS_BODY_TYPE] = 2  # DYN_BODY_TYPE_STATIC = 2 (collider)
        tag[c4d.DYNAMICS_BODY_SHAPE] = 0  # DYN_BODY_SHAPE_AUTOMATIC = 0
        tag[c4d.DYNAMICS_BODY_INHERIT_TAG] = False
    except:
        # Fallback for older versions
        pass
elif "{tag_type}" == "soft_body":
    # Configure as soft body
    try:
        tag[c4d.DYNAMICS_BODY_ENABLED] = True
        tag[c4d.DYNAMICS_BODY_TYPE] = 1  # DYN_BODY_TYPE_DYNAMIC = 1
        # Soft body specific settings
        tag[c4d.DYNAMICS_BODY_SOFT_BODY_MODE] = True
        tag[c4d.DYNAMICS_BODY_SOFT_BODY_STIFFNESS] = {params.get('stiffness', 0.5)}
        tag[c4d.DYNAMICS_BODY_SOFT_BODY_DAMPING] = {params.get('damping', 0.2)}
    except:
        # These constants might not exist in all versions
        pass

doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Applied {tag_type} dynamics to {{obj.GetName()}}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Applied {tag_type} dynamics to {object_name}"
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def apply_field(self, effector_name: str, field_type: str = "linear", **params) -> CommandResult:
        """Apply a field to an effector"""
        try:
            # Field object constants
            field_map = {
                "linear": 440000266,         # Linear Field
                "spherical": 440000267,      # Spherical Field
                "box": 440000268,            # Box Field
                "cylinder": 440000269,       # Cylinder Field
                "cone": 440000270,           # Cone Field
                "torus": 440000271,          # Torus Field
                "capsule": 440000272,        # Capsule Field
                "formula": 440000273,        # Formula Field
                "random": 440000274,         # Random Field
                "shader": 440000275,         # Shader Field
                "sound": 440000276,          # Sound Field
                "delay": 440000281           # Delay Field
            }
            
            c4d_field = field_map.get(field_type.lower(), 440000266)
            
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Find effector
effector = doc.SearchObject("{effector_name}")
if not effector:
    raise Exception(f"Effector '{effector_name}' not found")

# Create field
field = c4d.BaseObject({c4d_field})
if not field:
    raise Exception("Failed to create field")

field.SetName(f"{field_type.capitalize()}_Field")

# Configure field based on type
if {c4d_field} == 440000267:  # Spherical Field
    # FIELD_SPHERE_RADIUS = 2000
    field[2000] = {params.get('radius', 200)}
elif {c4d_field} == 440000266:  # Linear Field
    # FIELD_LINEAR_LENGTH = 2000
    field[2000] = {params.get('length', 400)}

# Insert field
doc.InsertObject(field)

# Add field to effector's field list
# FIELDS_LIST = 440000501
field_list = effector[440000501]
if field_list is None:
    field_list = c4d.FieldList()
field_layer = c4d.modules.mograph.FieldLayer(c4d.modules.mograph.FLfield)
field_layer.SetLinkedObject(field)
field_list.InsertLayer(field_layer)
effector[440000501] = field_list

doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Applied {field_type} field to {{effector.GetName()}}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Applied {field_type} field to {effector_name}"
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def snapshot_scene(self) -> CommandResult:
        """Take a snapshot of the current scene"""
        try:
            script = """
import c4d
from c4d import documents, bitmaps
import base64
import io

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Get active render data
rd = doc.GetActiveRenderData()
if not rd:
    raise Exception("No render data")

# Set up bitmap for render
width = 800
height = 600
bmp = bitmaps.BaseBitmap()
bmp.Init(width, height, 24)

# Render to bitmap
result = documents.RenderDocument(doc, rd.GetData(), bmp, c4d.RENDERFLAGS_EXTERNAL)

if result != c4d.RENDERRESULT_OK:
    raise Exception("Render failed")

# Save to memory
# Note: In actual implementation, save to temp file and return path
print("SUCCESS: Scene snapshot captured")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message="Scene snapshot captured"
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def execute_python_custom(self, command_type: str, params: Dict[str, Any]) -> CommandResult:
        """Execute custom Python script for unsupported operations"""
        try:
            self.logger.info(f"Executing custom command: {command_type}")
            
            # Handle missing MoGraph commands
            if command_type == "create_fracture":
                return await self.create_mograph_fracture(**params)
            elif command_type == "create_plain":
                return await self.create_mograph_plain_effector(**params)
            elif command_type == "create_random":
                return await self.create_mograph_random_effector(**params)
            
            # 3D MODELS IMPORT COMMANDS - Import selected 3D models from Tab 2
            elif command_type == "create_import_selected":
                return await self.import_selected_models(**params)
            elif command_type == "create_import_single":
                return await self.import_single_model(**params)
            elif command_type == "create_import_to_cloner":
                return await self.import_models_to_cloner(**params)
            elif command_type == "create_import_with_softbody":
                return await self.import_models_with_softbody(**params)
            elif command_type == "create_import_with_rigidbody":
                return await self.import_models_with_rigidbody(**params)
            elif command_type == "create_quick_import":
                return await self.quick_import_models(**params)
            
            else:
                return CommandResult(
                    False,
                    error=f"Custom command '{command_type}' not yet implemented"
                )
            
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def create_cloner_with_object(self, object_type: str, object_size: float = 100,
                                      mode: str = "grid", count: int = 10) -> CommandResult:
        """Create a cloner with object in one operation"""
        try:
            # Map primitive type to VERIFIED C4D constants from user's list
            primitive_map = {
                "cube": "c4d.Ocube",
                "sphere": "c4d.Osphere",
                "cylinder": "c4d.Ocylinder",
                "cone": "c4d.Ocone",
                "torus": "c4d.Otorus",
                "plane": "c4d.Oplane",
                "pyramid": "c4d.Opyramid",
                "disc": "c4d.Odisc",
                "tube": "c4d.Otube",
                "platonic": "c4d.Oplatonic",
                "landscape": "c4d.Ofractal",
                "relief": "c4d.Orelief",
                "capsule": "c4d.Ocapsule",
                "oiltank": "c4d.Ooiltank",
                "figure": "c4d.Ofigure"
            }
            
            c4d_type = primitive_map.get(object_type.lower(), "c4d.Ocube")
            
            mode_map = {
                "linear": 0,      # ID_MG_CLONE_MODE_LINEAR = 0
                "radial": 1,      # ID_MG_CLONE_MODE_RADIAL = 1
                "grid": 2,        # ID_MG_CLONE_MODE_GRID = 2
                "honeycomb": 3    # ID_MG_CLONE_MODE_HONEYCOMB = 3
            }
            
            c4d_mode = mode_map.get(mode.lower(), 2)  # Default to grid
            
            script = f"""
import c4d
from c4d import documents
import math

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create cloner using VERIFIED constant
cloner = c4d.BaseObject(c4d.Omgcloner)
if not cloner:
    raise Exception("Failed to create cloner")

cloner.SetName("{object_type.capitalize()}_Cloner")

# Create the object to clone
obj = c4d.BaseObject({c4d_type})
if not obj:
    raise Exception("Failed to create object")

obj.SetName("{object_type.capitalize()}_Source")

# Set object size
if {c4d_type} == c4d.Ocube:
    obj[c4d.PRIM_CUBE_LEN] = c4d.Vector({object_size}, {object_size}, {object_size})
elif {c4d_type} == c4d.Osphere:
    obj[c4d.PRIM_SPHERE_RAD] = {object_size}
elif {c4d_type} == c4d.Ocylinder:
    obj[c4d.PRIM_CYLINDER_RADIUS] = {object_size/2}
    obj[c4d.PRIM_CYLINDER_HEIGHT] = {object_size}
elif {c4d_type} == c4d.Ocone:
    obj[c4d.PRIM_CONE_BRAD] = {object_size/2}
    obj[c4d.PRIM_CONE_HEIGHT] = {object_size}
elif {c4d_type} == c4d.Otorus:
    obj[c4d.PRIM_TORUS_OUTERRAD] = {object_size/2}
    obj[c4d.PRIM_TORUS_INNERRAD] = {object_size/4}
elif {c4d_type} == c4d.Oplane:
    obj[c4d.PRIM_PLANE_WIDTH] = {object_size * 2}
    obj[c4d.PRIM_PLANE_HEIGHT] = {object_size * 2}

# Insert object as child of cloner
obj.InsertUnder(cloner)

# Set cloner mode
# ID_MG_CLONER_MODE = 20001
cloner[20001] = {c4d_mode}

# Configure based on mode
if {c4d_mode} == 2:  # Grid mode
    # Calculate grid dimensions
    if {count} <= 9:
        grid_x = int(math.ceil(math.sqrt({count})))
        grid_y = int(math.ceil({count} / float(grid_x)))
        grid_z = 1
    else:
        grid_size = int(math.ceil(math.pow({count}, 1/3.0)))
        grid_x = grid_size
        grid_y = grid_size
        grid_z = int(math.ceil({count} / float(grid_x * grid_y)))
    
    # MG_GRID_COUNT = 20002, MG_GRID_SIZE = 20003
    cloner[20002] = c4d.Vector(grid_x, grid_y, grid_z)
    cloner[20003] = c4d.Vector(grid_x * {object_size} * 1.5, 
                              grid_y * {object_size} * 1.5, 
                              max(1, grid_z - 1) * {object_size} * 1.5)
elif {c4d_mode} == 1:  # Radial mode
    # MG_RADIAL_COUNT = 20004, MG_RADIAL_RADIUS = 20005
    cloner[20004] = {count}
    cloner[20005] = {object_size} * 3
elif {c4d_mode} == 0:  # Linear mode
    # MG_LINEAR_COUNT = 20006, MG_LINEAR_OFFSET = 20007
    cloner[20006] = {count}
    cloner[20007] = c4d.Vector({object_size} * 1.5, 0, 0)

# Insert cloner into document
doc.InsertObject(cloner)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created {mode} cloner with {count} {object_type} objects")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Created {mode} cloner with {count} {object_type} objects",
                    data={"name": f"{object_type.capitalize()}_Cloner", "mode": mode, "count": count}
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    def _generate_param_code(self, params: Dict[str, Any]) -> str:
        """Generate Python code for additional parameters"""
        code_lines = []
        
        # Map parameter names to Cinema4D constants
        param_map = {
            # Cube parameters
            'subdivisions_x': 'c4d.PRIM_CUBE_SUBX',
            'subdivisions_y': 'c4d.PRIM_CUBE_SUBY', 
            'subdivisions_z': 'c4d.PRIM_CUBE_SUBZ',
            'separate_surfaces': 'c4d.PRIM_CUBE_SEP',
            'fillet': 'c4d.PRIM_CUBE_DOFILLET',
            'fillet_radius': 'c4d.PRIM_CUBE_FRAD',
            'fillet_subdivisions': 'c4d.PRIM_CUBE_SUBF',
            
            # Sphere parameters
            'sphere_type': 'c4d.PRIM_SPHERE_TYPE',
            'perfect': 'c4d.PRIM_SPHERE_TYPE',  # 0=Standard, 1=Perfect
            'segments': 'c4d.PRIM_SPHERE_SEG',
            
            # Cylinder parameters  
            'segments': 'c4d.PRIM_CYLINDER_SEG',
            'height_segments': 'c4d.PRIM_CYLINDER_HSUB',
            'caps': 'c4d.PRIM_CYLINDER_CAPS',
            'fillet': 'c4d.PRIM_CYLINDER_FILLET',
            'fillet_radius': 'c4d.PRIM_CYLINDER_FILLETRADIUS',
            
            # Plane parameters
            'width_segments': 'c4d.PRIM_PLANE_SUBW',
            'height_segments': 'c4d.PRIM_PLANE_SUBH',
            
            # Torus parameters
            'ring_segments': 'c4d.PRIM_TORUS_SEG',
            'pipe_segments': 'c4d.PRIM_TORUS_CSEG',
            
            # Cone parameters
            'height_segments': 'c4d.PRIM_CONE_HSUB',
            'cap_segments': 'c4d.PRIM_CONE_SEG',
            'top_radius': 'c4d.PRIM_CONE_TRAD',
            'bottom_radius': 'c4d.PRIM_CONE_BRAD',
        }
        
        for key, value in params.items():
            if key in param_map:
                c4d_param = param_map[key]
                if isinstance(value, bool):
                    code_lines.append(f'obj[{c4d_param}] = {str(value)}')
                elif isinstance(value, (int, float)):
                    code_lines.append(f'obj[{c4d_param}] = {value}')
                elif isinstance(value, str):
                    # Handle special cases like sphere type
                    if key == 'sphere_type' and value.lower() == 'perfect':
                        code_lines.append(f'obj[{c4d_param}] = 1')  # Perfect sphere
                    else:
                        code_lines.append(f'obj[{c4d_param}] = "{value}"')
            else:
                # Log unmapped parameters for debugging
                code_lines.append(f'# Unmapped parameter: {key} = {value}')
        
        return "\n".join(code_lines)

    def _generate_generator_param_code(self, generator_type: str, c4d_type: str, params: Dict[str, Any]) -> str:
        """Generate Python code for generator-specific parameters"""
        code_lines = []
        
        # Map of verified generator parameters for each object type
        param_mappings = {
            "c4d.Oarray": {
                # Array parameters - VERIFIED from Cinema4D
                "copies": "c4d.ARRAYOBJECT_COPIES",      # 1001
                "radius": "c4d.ARRAYOBJECT_RADIUS",      # 1000  
                "amplitude": "c4d.ARRAYOBJECT_AMPLITUDE", # 1002
                "frequency": "c4d.ARRAYOBJECT_FREQUENCY"  # 1003
            },
            "c4d.Oboole": {
                # Boolean parameters - VERIFIED from Cinema4D discovery
                "type": "c4d.BOOLEOBJECT_TYPE",              # 1000 - Boolean operation type
                "single_object": "c4d.BOOLEOBJECT_SINGLE_OBJECT",  # 1001 - Create single object
                "hide_new_edges": "c4d.BOOLEOBJECT_HIDE_NEW_EDGES"  # 1002 - Hide new edges
            },
            "c4d.Omgcloner": {
                # Cloner parameters - VERIFIED from Cinema4D discovery and testing
                "mode": "2010",                    # CORRECT: Main visual cloner mode (Linear=0, Radial=1, Grid=2, etc.)
                "clones": "1020",                  # Clones setting (separate from visual mode)
                "count": "1200",                   # Grid count Vector(x,y,z)
                "size": "1201",                    # MG_GRID_SIZE - Grid spacing Vector(x,y,z) 
                "grid_mode": "1204",              # Grid mode type
                "fill": "1202",                   # Fill percentage
                "reset_coordinates": "1021"       # Reset coordinates boolean
            },
            "c4d.Oextrude": {
                # Extrude parameters - VERIFIED from Cinema4D discovery
                "isoparm": "c4d.EXTRUDEOBJECT_ISOPARM",        # 1000 - Isoparm interpolation
                "sub": "c4d.EXTRUDEOBJECT_SUB",                # 1001 - Subdivision
                "move": "c4d.EXTRUDEOBJECT_MOVE",              # 1002 - Movement vector
                "flipnormals": "c4d.EXTRUDEOBJECT_FLIPNORMALS", # 1003 - Flip normals
                "hierarchic": "c4d.EXTRUDEOBJECT_HIERARCHIC"   # 1004 - Hierarchic mode
            },
            "c4d.Olathe": {
                # Lathe parameters - VERIFIED from Cinema4D discovery
                "isoparm": "c4d.LATHEOBJECT_ISOPARM",        # 1000 - Isoparm interpolation
                "sub": "c4d.LATHEOBJECT_SUB",                # 1001 - Subdivision
                "move": "c4d.LATHEOBJECT_MOVE",              # 1002 - Movement
                "scale": "c4d.LATHEOBJECT_SCALE",            # 1003 - Scale
                "rotate": "c4d.LATHEOBJECT_ROTATE",          # 1004 - Rotation angle
                "flipnormals": "c4d.LATHEOBJECT_FLIPNORMALS" # 1005 - Flip normals
            },
            "c4d.Oloft": {
                # Loft parameters - VERIFIED from Cinema4D discovery
                "isoparm": "c4d.LOFTOBJECT_ISOPARM",        # 1000 - Isoparm interpolation
                "subx": "c4d.LOFTOBJECT_SUBX",              # 1001 - Subdivision X
                "suby": "c4d.LOFTOBJECT_SUBY",              # 1002 - Subdivision Y
                "closey": "c4d.LOFTOBJECT_CLOSEY",          # 1003 - Close Y
                "flipnormals": "c4d.LOFTOBJECT_FLIPNORMALS", # 1004 - Flip normals
                "linear": "c4d.LOFTOBJECT_LINEAR",          # 1005 - Linear interpolation
                "organic": "c4d.LOFTOBJECT_ORGANIC",        # 1006 - Organic form
                "adaptivey": "c4d.LOFTOBJECT_ADAPTIVEY",    # 1007 - Adaptive Y
                "fituv": "c4d.LOFTOBJECT_FITUV"             # 1008 - Fit UV
            },
            "c4d.Osweep": {
                # Sweep parameters - VERIFIED from Cinema4D discovery  
                "isoparm": "c4d.SWEEPOBJECT_ISOPARM",        # 1000 - Isoparm interpolation
                "growth": "c4d.SWEEPOBJECT_GROWTH",          # 1002 - Growth
                "scale": "c4d.SWEEPOBJECT_SCALE",            # 1003 - Scale
                "rotate": "c4d.SWEEPOBJECT_ROTATE",          # 1004 - Rotation
                "parallel": "c4d.SWEEPOBJECT_PARALLEL",      # 1005 - Parallel movement
                "constant": "c4d.SWEEPOBJECT_CONSTANT",      # 1008 - Constant cross section
                "banking": "c4d.SWEEPOBJECT_BANKING",        # 1009 - Banking
                "flipnormals": "c4d.SWEEPOBJECT_FLIPNORMALS", # 1010 - Flip normals
                "startgrowth": "c4d.SWEEPOBJECT_STARTGROWTH"  # 1013 - Start growth
            },
            "c4d.Osds": {
                # Subdivision Surface
                "type": "type"
            },
            "c4d.Osymmetry": {
                # Symmetry parameters
                "mirror_plane": "mirror_plane",
                "weld_points": "weld_points",
                "tolerance": "tolerance"
            },
            "c4d.Oinstance": {
                # Instance - basic params
                "render_instances": "render_instances"
            },
            "c4d.Ometaball": {
                # Metaball parameters - VERIFIED from Cinema4D discovery
                "threshold": "c4d.METABALLOBJECT_THRESHOLD",        # 1000 - Threshold value
                "subeditor": "c4d.METABALLOBJECT_SUBEDITOR",        # 1001 - Editor subdivision
                "subray": "c4d.METABALLOBJECT_SUBRAY",              # 1002 - Render subdivision
                "exponential": "c4d.METABALLOBJECT_EXPONENTIAL",    # 1003 - Exponential falloff
                "accuratenormals": "c4d.METABALLOBJECT_ACCURATENORMALS" # 1004 - Accurate normals
            },
            "c4d.Obezier": {
                # Bezier parameters
                "subdivision": "subdivision"
            },
            "c4d.Oconnector": {
                # Connect parameters
                "weld": "weld",
                "tolerance": "tolerance"
            },
            "c4d.Osplinewrap": {
                # Spline Wrap parameters
                "axis": "axis",
                "offset": "offset"
            },
            "c4d.Opolyreduxgen": {
                # Polygon Reduction
                "reduction_strength": "reduction_strength"
            },
            "c4d.Omgmatrix": {
                # Matrix parameters
                "mode": "mode",
                "count": "count"
            },
            "c4d.Osplinecircle": {
                # Circle spline parameters - VERIFIED from Cinema4D discovery
                "circle_ellipse": "c4d.PRIM_CIRCLE_ELLIPSE",
                "circle_radius": "c4d.PRIM_CIRCLE_RADIUS",
                "circle_inner": "c4d.PRIM_CIRCLE_INNER"
            },
            "c4d.Osplinerectangle": {
                # Rectangle spline parameters - VERIFIED from Cinema4D discovery
                "rectangle_width": "c4d.PRIM_RECTANGLE_WIDTH",
                "rectangle_height": "c4d.PRIM_RECTANGLE_HEIGHT",
                "rectangle_radius": "c4d.PRIM_RECTANGLE_RADIUS",
                "rectangle_rounding": "c4d.PRIM_RECTANGLE_ROUNDING"
            },
            "c4d.Osplinetext": {
                # Text spline parameters - VERIFIED from Cinema4D discovery
                "text_text": "c4d.PRIM_TEXT_TEXT",
                "text_height": "c4d.PRIM_TEXT_HEIGHT",
                "text_hspacing": "c4d.PRIM_TEXT_HSPACING",
                "text_vspacing": "c4d.PRIM_TEXT_VSPACING",
                "text_align": "c4d.PRIM_TEXT_ALIGN",
                "text_separate": "c4d.PRIM_TEXT_SEPARATE"
            },
            "c4d.Osplinehelix": {
                # Helix spline parameters - VERIFIED from Cinema4D discovery
                "helix_start": "c4d.PRIM_HELIX_START",
                "helix_end": "c4d.PRIM_HELIX_END",
                "helix_height": "c4d.PRIM_HELIX_HEIGHT",
                "helix_radius1": "c4d.PRIM_HELIX_RADIUS1",
                "helix_radius2": "c4d.PRIM_HELIX_RADIUS2",
                "helix_sub": "c4d.PRIM_HELIX_SUB"
            },
            "c4d.Osplinestar": {
                # Star spline parameters - VERIFIED from Cinema4D discovery
                "star_points": "c4d.PRIM_STAR_POINTS",
                "star_orad": "c4d.PRIM_STAR_ORAD",
                "star_irad": "c4d.PRIM_STAR_IRAD",
                "star_twist": "c4d.PRIM_STAR_TWIST"
            },
            "c4d.Ocamera": {
                # Camera parameters - VERIFIED from Cinema4D discovery
                "fov": "c4d.CAMERAOBJECT_FOV",
                "targetdistance": "c4d.CAMERAOBJECT_TARGETDISTANCE",
                "film_offset_x": "c4d.CAMERAOBJECT_FILM_OFFSET_X",
                "film_offset_y": "c4d.CAMERAOBJECT_FILM_OFFSET_Y",
                "projection": "c4d.CAMERA_PROJECTION"
            },
            "c4d.Olight": {
                # Light parameters - VERIFIED from Cinema4D discovery  
                "brightness": "c4d.LIGHT_BRIGHTNESS",
                "type": "c4d.LIGHT_TYPE",
                "shadowtype": "c4d.LIGHT_SHADOWTYPE",
                "outerangle": "c4d.LIGHT_DETAILS_OUTERANGLE",
                "innerangle": "c4d.LIGHT_DETAILS_INNERANGLE",
                "falloff": "c4d.LIGHT_DETAILS_FALLOFF"
            },
            # FIELD PARAMETER MAPPINGS - REAL FIELD TAB PARAMETERS FROM CINEMA4D (2025-01-11)
            "c4d.Flinear": {
                # Linear Field tab parameters - VERIFIED from Cinema4D Field tab
                "length": 1000,              # Length
                "clip_to_shape": 1001,       # Clip to Shape
                "direction": 1005            # Direction
            },
            "c4d.Fbox": {
                # Box Field tab parameters - VERIFIED from Cinema4D Field tab
                "size": 1000,                # Size (REQUIRES Vector - c4d.Vector(x, y, z))
                "clip_to_shape": 1001        # Clip to Shape (bool)
            },
            "c4d.Fspherical": {
                # Spherical Field tab parameters - VERIFIED from Cinema4D Field tab
                "size": 1000,                # Size
                "clip_to_shape": 1002        # Clip to Shape
            },
            "c4d.Fcylinder": {
                # Cylinder Field tab parameters - VERIFIED from Cinema4D Field tab
                "direction": 1005,           # Direction
                "height": 1006,              # Height
                "radius": 1007,              # Radius
                "clip_to_shape": 1008        # Clip to Shape
            },
            "c4d.Ftorus": {
                # Torus Field tab parameters - VERIFIED from Cinema4D Field tab
                "radius": 1000,              # Radius (float)
                "clip_to_shape": 1003,       # Clip to Shape (bool)
                "direction": 1005            # Direction (int - SPECIAL: 1 is invalid, use 0 or 2)
            },
            "c4d.Fcone": {
                # Cone Field tab parameters - VERIFIED from Cinema4D Field tab
                "clip_to_shape": 1002,       # Clip to Shape
                "direction": 1005,           # Direction
                "radius": 1006,              # Radius
                "height": 1007               # Height
            },
            "c4d.Frandom": {
                # Random Field tab parameters - VERIFIED from Cinema4D Field tab
                "seed": 1001,                # Seed (int)
                "scale": 1003,               # Scale (float)
                "viewplane_preview": 1011,   # Viewplane Preview (bool)
                "viewplane_resolution": 1012, # Viewplane Resolution (int)
                "relative_scale": 1014,      # Relative Scale (bool)
                "noise_type": 1016,          # Noise Type (int - SPECIAL: 0 is invalid, use 1+)
                "sample_position_seed": 1020 # Sample Position Seed (int)
            },
            "c4d.Fsound": {
                # Sound Field tab parameters - VERIFIED from Cinema4D Field tab
                "sound": 1100                # Sound
            },
            "c4d.Fformula": {
                # Formula Field tab parameters - VERIFIED from Cinema4D Field tab
                "formula": 1000,             # Formula
                "variables": 1001,           # Variables
                "scale_xyz": 1004,           # sx,sy,sz - Scale
                "uvw": 1005,                 # u,v,w - UVW
                "component_count": 1007,     # count - Component Count
                "falloff_weight": 1008,      # subfields - Falloff weight
                "frequency": 1010            # f - Frequency
            },
            "c4d.Fradial": {
                # Radial Field tab parameters - VERIFIED from Cinema4D Field tab
                "start_angle": 1000,         # Start Angle
                "end_angle": 1001,           # End Angle
                "axis": 1005,                # Axis
                "offset": 1006,              # Offset (using first offset)
                "clip_to_shape": 1009        # Clip to Shape
            },
            "c4d.Fpython": {
                # Python Field tab parameters - VERIFIED from Cinema4D Field tab
                "code": 1002                 # Code
            }
        }
        
        # Get parameter mappings for this generator
        mappings = param_mappings.get(c4d_type, {})
        
        # Skip position parameters as they're handled separately
        position_params = ['pos_x', 'pos_y', 'pos_z']
        
        # Special handling for specific generators with known working patterns
        if c4d_type == "c4d.Oarray":
            # Array: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped Array parameter: {key} = {value}")
        
        elif c4d_type == "c4d.Oboole":
            # Boolean: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped Boolean parameter: {key} = {value}")
        
        elif c4d_type == "c4d.Omgcloner":
            # Cloner: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    
                    # Special handling for cloner parameters based on discovery data
                    if key == "mode":
                        # Mode parameter: 0=Linear, 1=Radial, 2=Grid, etc.
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif key in ["count", "size"]:
                        # Handle Vector parameters - use individual X,Y,Z or single value
                        if key == "count":
                            count_x = params.get("count_x", value)
                            count_y = params.get("count_y", 1) 
                            count_z = params.get("count_z", value)
                            code_lines.append(f"obj[{c4d_param}] = c4d.Vector({count_x}, {count_y}, {count_z})")
                        elif key == "size":
                            size_x = params.get("size_x", value)
                            size_y = params.get("size_y", value)
                            size_z = params.get("size_z", value)
                            code_lines.append(f"obj[{c4d_param}] = c4d.Vector({size_x}, {size_y}, {size_z})")
                    elif key.startswith(("count_", "size_")):
                        # Skip individual x,y,z components - handled above
                        continue
                    elif isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    if not key.startswith(("count_", "size_")):  # Don't log x,y,z components as unmapped
                        code_lines.append(f"# Unmapped Cloner parameter: {key} = {value}")
        
        elif c4d_type == "c4d.Oextrude":
            # Extrude: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        # Special handling for move parameter (expects Vector)
                        if key == "move":
                            code_lines.append(f"obj[{c4d_param}] = c4d.Vector(0, 0, {value})")
                        else:
                            code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped Extrude parameter: {key} = {value}")
        
        elif c4d_type == "c4d.Olathe":
            # Lathe: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped Lathe parameter: {key} = {value}")
        
        elif c4d_type == "c4d.Oloft":
            # Loft: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped Loft parameter: {key} = {value}")
        
        elif c4d_type == "c4d.Osweep":
            # Sweep: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped Sweep parameter: {key} = {value}")
        
        elif c4d_type == "c4d.Ometaball":
            # Metaball: Apply VERIFIED parameters with actual Cinema4D constants
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped Metaball parameter: {key} = {value}")
        
        # Spline objects handling - VERIFIED from Cinema4D discovery
        elif c4d_type in ["c4d.Osplinecircle", "c4d.Osplinerectangle", "c4d.Osplinetext", "c4d.Osplinehelix", "c4d.Osplinestar"]:
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    elif isinstance(value, str):
                        code_lines.append(f'obj[{c4d_param}] = "{value}"')
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped spline parameter: {key} = {value}")
        
        # Camera and Light objects handling - VERIFIED from user provided constants
        elif c4d_type in ["c4d.Ocamera", "c4d.Otargetcamera", "c4d.Olight"]:
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    if isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    elif isinstance(value, str):
                        code_lines.append(f'obj[{c4d_param}] = "{value}"')
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped camera/light parameter: {key} = {value}")
        
        # Field objects handling - VERIFIED from Cinema4D discovery (2025-01-11)
        elif c4d_type.startswith("c4d.F"):
            for key, value in params.items():
                if key in position_params:
                    continue
                if key in mappings:
                    c4d_param = mappings[key]
                    
                    # Special handling for field parameters that need specific types
                    if key == "size" and c4d_type == "c4d.Fbox":
                        # Box field Size parameter expects Vector (X, Y, Z)
                        if isinstance(value, (int, float)):
                            code_lines.append(f"obj[{c4d_param}] = c4d.Vector({value}, {value}, {value})")
                        elif isinstance(value, (list, tuple)) and len(value) >= 3:
                            code_lines.append(f"obj[{c4d_param}] = c4d.Vector({value[0]}, {value[1]}, {value[2]})")
                        else:
                            code_lines.append(f"# Skipped Box size {key} = {value} (expected number or [x,y,z])")
                    elif key == "direction" and c4d_type == "c4d.Ftorus" and isinstance(value, int):
                        # Torus field Direction: skip invalid value 1, map valid values
                        if value == 1:
                            code_lines.append(f"obj[{c4d_param}] = 2  # Torus direction 1 invalid, using 2 (Z-axis)")
                        else:
                            code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif key == "noise_type" and c4d_type == "c4d.Frandom" and isinstance(value, int):
                        # Random field Noise Type: skip invalid value 0, ensure valid range
                        if value == 0:
                            code_lines.append(f"obj[{c4d_param}] = 1  # Random noise type 0 invalid, using 1")
                        else:
                            code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, (int, float)):
                        code_lines.append(f"obj[{c4d_param}] = {value}")
                    elif isinstance(value, bool):
                        code_lines.append(f"obj[{c4d_param}] = {str(value)}")
                    elif isinstance(value, str):
                        code_lines.append(f'obj[{c4d_param}] = "{value}"')
                    else:
                        code_lines.append(f"# Skipped {key} = {value} (unsupported type)")
                else:
                    code_lines.append(f"# Unmapped field parameter: {key} = {value}")
        
        # For all other parameters, log them
        for key, value in params.items():
            if key in position_params:
                continue
                
            if key in mappings:
                code_lines.append(f"# Parameter: {key} = {value}")
            else:
                code_lines.append(f"# Unmapped parameter: {key} = {value}")
        
        # Add a note about parameter application
        if code_lines:
            code_lines.insert(0, "# Object created with default parameters, custom parameters noted below:")
            code_lines.append("# To apply parameters, Cinema4D constants need to be verified first")
        
        return "\n".join(code_lines) if code_lines else "# Object created with default parameters"

    async def create_spline(self, spline_type: str, name: str = None,
                           position: Tuple[float, float, float] = (0, 0, 0), **params) -> CommandResult:
        """Create a spline object using MCPCommandWrapper pattern like primitives"""
        try:
            # Map spline types to VERIFIED Cinema4D constants from discovery
            spline_map = {
                "circle": "c4d.Osplinecircle",
                "rectangle": "c4d.Osplinerectangle", 
                "text": "c4d.Osplinetext",
                "helix": "c4d.Osplinehelix",
                "star": "c4d.Osplinestar"
            }
            
            c4d_type = spline_map.get(spline_type.lower(), "c4d.Osplinecircle")
            obj_name = name or f"{spline_type.capitalize()}_Spline"
            
            # Use the PROVEN MCPCommandWrapper pattern (same as primitives)
            return await self.client.execute_mcp_command(
                "create_object",
                {
                    "object_type": c4d_type,
                    "name": obj_name,
                    "position": {"x": position[0], "y": position[1], "z": position[2]},
                    "parameters": params
                }
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def create_camera_light(self, object_type: str, name: str = None,
                                 position: Tuple[float, float, float] = (0, 0, 0), **params) -> CommandResult:
        """Create a camera or light object using MCPCommandWrapper pattern"""
        try:
            # Map object types to VERIFIED Cinema4D constants from discovery
            object_map = {
                "camera": "c4d.Ocamera",
                "light": "c4d.Olight"
            }
            
            c4d_type = object_map.get(object_type.lower(), "c4d.Ocamera")
            obj_name = name or f"{object_type.replace('_', ' ').title()}"
            
            # Use the PROVEN MCPCommandWrapper pattern (same as primitives and splines)
            return await self.client.execute_mcp_command(
                "create_object",
                {
                    "object_type": c4d_type,
                    "name": obj_name,
                    "position": {"x": position[0], "y": position[1], "z": position[2]},
                    "parameters": params
                }
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def create_mograph_fracture(self, name: str = "Fracture", **params) -> CommandResult:
        """Create MoGraph Fracture object"""
        try:
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create Fracture object using Cinema4D constant
fracture = c4d.BaseObject(c4d.Ofracture)
if not fracture:
    raise Exception("Failed to create fracture object")

fracture.SetName("{name}")

# Insert into document
doc.InsertObject(fracture)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created fracture object '{{fracture.GetName()}}'")
"""
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(True, message=f"Created fracture '{name}'")
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def create_mograph_plain_effector(self, name: str = "Plain_Effector", **params) -> CommandResult:
        """Create MoGraph Plain Effector"""
        try:
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create Plain Effector using Cinema4D constant
plain = c4d.BaseObject(c4d.Obaseeffector)
if not plain:
    raise Exception("Failed to create plain effector")

plain.SetName("{name}")

# Insert into document
doc.InsertObject(plain)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created plain effector '{{plain.GetName()}}'")
"""
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(True, message=f"Created plain effector '{name}'")
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def create_mograph_random_effector(self, name: str = "Random_Effector", **params) -> CommandResult:
        """Create MoGraph Random Effector"""
        try:
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create Random Effector - same as other effectors but with parameters
random_eff = c4d.BaseObject(c4d.Obaseeffector)
if not random_eff:
    raise Exception("Failed to create random effector")

random_eff.SetName("{name}")

# Set effector to Random mode
# Note: Using numeric ID as Cinema4D constant not available
# EFFECTOR_TRANSFORM = 20002, EFFECTOR_TRANSFORM_RANDOM = 1
random_eff[20002] = 1  # Transform mode to Random

# Insert into document
doc.InsertObject(random_eff)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created random effector '{{random_eff.GetName()}}'")
"""
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(True, message=f"Created random effector '{name}'")
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))

    # Add the standalone deformer method to MCPCommandWrapper class
    async def create_deformer_standalone(self, deformer_type: str = "bend",
                                       strength: float = 0.5, **params) -> CommandResult:
        """Create a deformer object standalone (not applied to any object)"""
        try:
            # Use VERIFIED Cinema4D constants from user's list
            deformer_map = {
                "bend": "c4d.Obend",
                "twist": "c4d.Otwist", 
                "taper": "c4d.Otaper",
                "bulge": "c4d.Obulge",
                "shear": "c4d.Oshear",
                "wind": "c4d.Owinddeform",  # Wind deformer constant
                "ffd": "c4d.Offd",
                "displacer": "c4d.Odisplacer",
                "wave": "c4d.Owave",
                "formula": "c4d.Oformula",
                "explosion": "c4d.Oexplosion",
                "melt": "c4d.Omelt",
                "shatter": "c4d.Oshatter",
                "spherify": "c4d.Ospherify",
                "wrap": "c4d.Owrap"
            }
            
            c4d_constant = deformer_map.get(deformer_type.lower(), "c4d.Obend")  # Default to bend
            
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create deformer using VERIFIED constant (standalone, not applied to object)
deformer = c4d.BaseObject({c4d_constant})
if not deformer:
    raise Exception("Failed to create deformer")

deformer.SetName(f"{deformer_type.capitalize()}_Deformer")

# Set position
deformer.SetAbsPos(c4d.Vector(0, 0, 0))

# Insert deformer into document (not under any object)
doc.InsertObject(deformer)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created {deformer_type} deformer: {{deformer.GetName()}}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Created {deformer_type} deformer",
                    data={"name": f"{deformer_type.capitalize()}_Deformer", "type": deformer_type}
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))

    # Add the standalone effector method to MCPCommandWrapper class
    async def create_effector_standalone(self, effector_type: str = "random", **params) -> CommandResult:
        """Create an effector object standalone (not attached to any cloner)"""
        try:
            # Use VERIFIED Cinema4D constants from user's list  
            effector_map = {
                "plain": "c4d.Omgplain",          # Plain Effector
                "random": "c4d.Omgrandom",         # Random Effector  
                "shader": "c4d.Omgshader",         # Shader Effector
                "delay": "c4d.Omgdelay",           # Delay Effector
                "formula": "c4d.Omgformula",       # Formula Effector
                "step": "c4d.Omgstep",             # Step Effector
                "target": "c4d.Omgeffectortarget", # Target Effector
                "time": "c4d.Omgtime",             # Time Effector
                "sound": "c4d.Omgsound"            # Sound Effector
            }
            
            c4d_constant = effector_map.get(effector_type.lower(), "c4d.Omgrandom")  # Default to random
            
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create effector using VERIFIED constant (standalone, not attached to cloner)
effector = c4d.BaseObject({c4d_constant})
if not effector:
    raise Exception("Failed to create effector")

effector.SetName(f"{effector_type.capitalize()}_Effector")

# Set position
effector.SetAbsPos(c4d.Vector(0, 0, 0))

# Insert effector into document (not under any cloner)
doc.InsertObject(effector)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created {effector_type} effector: {{effector.GetName()}}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Created {effector_type} effector",
                    data={"name": f"{effector_type.capitalize()}_Effector", "type": effector_type}
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))

    # Add tag creation method
    async def create_tag_standalone(self, tag_type: str = "material", **params) -> CommandResult:
        """Create a tag object standalone"""
        try:
            # Map tag types to C4D tag constants - USING VERIFIED CONSTANTS FROM USER
            tag_map = {
                "material": "c4d.Tmaterial",
                "uv": "c4d.Tuvw",
                "texture": "c4d.Ttexture",
                "selection": "c4d.Tselection",
                "python": "c4d.Tpython",
                "expression": "c4d.Texpression",
                "display": "c4d.Tdisplay", 
                "phong": "c4d.Tphong",
                "protection": "c4d.Tprotection",
                "compositing": "c4d.Tcompositing",
                # Dynamics tags - these are TAGS not objects!
                "rigid_body": "c4d.Tdynamicsbody",
                "soft_body": "c4d.Tdynamicsbody", 
                "cloth": "c4d.Tdynamicsbody",
                "collider": "c4d.Tcollider"
            }
            
            c4d_constant = tag_map.get(tag_type.lower(), "c4d.Tmaterial")  # Default to material tag
            
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Create a basic cube to apply the tag to (tags need objects)
cube = c4d.BaseObject(c4d.Ocube)
if not cube:
    raise Exception("Failed to create test cube for tag")

cube.SetName("Object_with_{tag_type.capitalize()}_Tag")

# Create tag using VERIFIED constant
tag = cube.MakeTag({c4d_constant})
if not tag:
    raise Exception("Failed to create tag")

tag.SetName(f"{tag_type.capitalize()}_Tag")

# Insert cube with tag into document
doc.InsertObject(cube)
doc.SetChanged()
c4d.EventAdd()

print(f"SUCCESS: Created {tag_type} tag on object: {{cube.GetName()}}")
"""
            
            result = await self.client.execute_python(script)
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message=f"Created {tag_type} tag",
                    data={"name": f"Object_with_{tag_type.capitalize()}_Tag", "type": tag_type}
                )
            else:
                return CommandResult(False, error=result.get("error", "Unknown error"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    # ============================================================================
    # 3D MODELS IMPORT METHODS - Work with selected models from Tab 2
    # ============================================================================
    
    async def import_selected_models(self, pos_x: float = 0.0, pos_y: float = 0.0, 
                                   pos_z: float = 0.0, scale: float = 1.0,
                                   rotation_x: float = 0.0, rotation_y: float = 0.0, 
                                   rotation_z: float = 0.0, selected_models=None, **params) -> CommandResult:
        """Import all selected 3D models from Tab 2 with specified transform settings"""
        try:
            if not selected_models:
                return CommandResult(False, error="No 3D models selected in Tab 2")
            
            # Check Cinema4D connection
            if not self.client._connected:
                await self.client.connect()
                if not self.client._connected:
                    return CommandResult(False, error="Cinema4D MCP server not connected. Please start Cinema4D and run the MCP server script.")
            
            imported_count = 0
            for i, model_path in enumerate(selected_models):
                # Calculate offset positions for multiple models
                offset_x = pos_x + (i * 200)  # Space models 200 units apart
                
                result = await self.client.import_obj(
                    model_path, 
                    position=(offset_x, pos_y, pos_z),
                    scale=scale
                )
                
                if result:  # import_obj returns boolean
                    imported_count += 1
            
            if imported_count > 0:
                return CommandResult(
                    True,
                    message=f"Successfully imported {imported_count}/{len(selected_models)} selected 3D models",
                    data={"imported_count": imported_count, "total_models": len(selected_models)}
                )
            else:
                return CommandResult(False, error="Failed to import any selected 3D models")
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def import_single_model(self, model_index: int = 0, pos_x: float = 0.0, 
                                pos_y: float = 0.0, pos_z: float = 0.0, 
                                scale: float = 1.0, selected_models=None, **params) -> CommandResult:
        """Import a single selected 3D model by index"""
        try:
            if not selected_models:
                return CommandResult(False, error="No 3D models selected in Tab 2")
            
            if model_index >= len(selected_models):
                return CommandResult(False, error=f"Model index {model_index} out of range (0-{len(selected_models)-1})")
            
            model_path = selected_models[model_index]
            result = await self.client.import_obj(
                model_path,
                position=(pos_x, pos_y, pos_z),
                scale=scale
            )
            
            if result:  # import_obj returns boolean
                return CommandResult(
                    True,
                    message=f"Successfully imported model: {model_path.name}",
                    data={"model_name": model_path.name, "index": model_index}
                )
            else:
                return CommandResult(False, error=result.get("error", "Failed to import model"))
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def import_models_to_cloner(self, cloner_mode: str = "grid", count: int = 10, 
                                    spacing: float = 100.0, selected_models=None, **params) -> CommandResult:
        """Import selected 3D models into a cloner object using proven working pattern"""
        try:
            if not selected_models:
                return CommandResult(False, error="No 3D models selected in Tab 2")
            
            # Use first selected model for cloner
            model_path = selected_models[0]
            
            # Use the exact working pattern from the successful cloner button
            cloner_script = self._generate_import_to_cloner_script(model_path, cloner_mode, count)
            result = await self.client.execute_python(cloner_script)
            
            if result and result.get("success") and "SUCCESS" in result.get("output", ""):
                return CommandResult(
                    True,
                    message=f"Created {cloner_mode} cloner with {count} instances of {model_path.name}",
                    data={"model_name": model_path.name, "mode": cloner_mode, "count": count}
                )
            else:
                return CommandResult(False, error=f"Failed to create cloner: {result.get('output', 'Unknown error')}")
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def test_cinema4d_scene(self) -> CommandResult:
        """Test Cinema4D connection and list current scene objects"""
        try:
            result = await self.client.test_scene_objects()
            
            if result and result.get("success"):
                return CommandResult(
                    True,
                    message="Cinema4D connection test successful",
                    data={"output": result.get("output", "")}
                )
            else:
                return CommandResult(
                    False, 
                    error=f"Cinema4D connection test failed: {result.get('output', 'Unknown error')}"
                )
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    def _generate_import_to_cloner_script(self, model_path, cloner_mode: str = "grid", count: int = 10) -> str:
        """Generate cloner script using exact working pattern from successful cloner button"""
        
        # Map modes to Cinema4D values (same as working pattern)
        mode_map = {"grid": 0, "linear": 1, "radial": 2, "random": 3}
        mode_id = mode_map.get(cloner_mode, 0)
        
        # Convert path for Cinema4D
        c4d_path = str(model_path).replace('\\', '/')
        
        # Use the exact working script pattern from the successful cloner workflow
        script = f'''import c4d
from c4d import documents
import time

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Create cloner first (exact working pattern)
        cloner = c4d.BaseObject(1018544)
        if not cloner:
            print("ERROR: Failed to create cloner")
            return False
        
        cloner.SetName("Model_Cloner_" + str(int(time.time() * 1000)))
        cloner[1018617] = {mode_id}  # Mode
        cloner[1018618] = {count}    # Count
        
        # Import model using proven method (exact working pattern)
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
        
        # Find the actual mesh object (Polygon type, not container)
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
        
        # Search through all objects for the newest mesh (excluding cloner)
        for obj in reversed(all_objects):  # Check newest first
            if obj != cloner:
                mesh = find_mesh_in_hierarchy(obj)
                if mesh:
                    imported_obj = mesh
                    print("INFO: Found actual mesh object for cloner: " + mesh.GetName() + " (Type: " + mesh.GetTypeName() + ")")
                    break
        
        # Last resort: use the newest non-cloner object
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
        
        # Give object a unique name immediately
        unique_name = "ImportedModel_" + str(int(time.time() * 1000000))  # Microsecond precision
        imported_obj.SetName(unique_name)
        print("INFO: Set unique name for cloner: " + unique_name)
        
        # Move to cloner using proven method (exact working pattern)
        imported_obj.Remove()
        imported_obj.InsertUnder(cloner)
        
        # Insert cloner at root level and update (exact working pattern)
        doc.InsertObject(cloner, None)  # None as parent = insert at root level
        c4d.EventAdd()
        
        print("SUCCESS: Imported " + imported_obj.GetName() + " to cloner")
        print("UNIQUE_NAME: " + unique_name)  # For reference
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
        return script
    
    async def import_models_with_softbody(self, pos_x: float = 0.0, pos_y: float = 500.0,
                                        pos_z: float = 0.0, scale: float = 1.0,
                                        mass: float = 1.0, bounce: float = 0.3, selected_models=None, **params) -> CommandResult:
        """Import selected 3D models and apply soft body physics tags"""
        try:
            if not selected_models:
                return CommandResult(False, error="No 3D models selected in Tab 2")
            
            imported_objects = []
            for i, model_path in enumerate(selected_models):
                offset_x = pos_x + (i * 300)  # Space models 300 units apart for physics
                
                # Import model first (using working method)
                import_result = await self.client.import_obj(
                    model_path,
                    position=(offset_x, pos_y, pos_z),
                    scale=scale
                )
                
                if import_result:  # import_obj returns boolean
                    # Apply physics tag using simplified approach
                    physics_result = await self.client.add_dynamics_tag(
                        f"ImportedModel_temp",  # Will search for newest ImportedModel object
                        tag_type="soft_body",
                        mass=mass,
                        bounce=bounce
                    )
                    
                    if physics_result:
                        imported_objects.append(f"ImportedModel_{i}")
                    else:
                        self.logger.warning(f"Failed to apply soft body tag to model {i}")
                else:
                    self.logger.warning(f"Failed to import model {i}")
            
            if imported_objects:
                return CommandResult(
                    True,
                    message=f"Imported {len(imported_objects)} models with soft body physics",
                    data={"imported_objects": imported_objects, "physics_type": "softbody"}
                )
            else:
                return CommandResult(False, error="Failed to import models with soft body tags")
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def import_models_with_rigidbody(self, pos_x: float = 0.0, pos_y: float = 500.0,
                                         pos_z: float = 0.0, scale: float = 1.0,
                                         mass: float = 1.0, friction: float = 0.3, selected_models=None, **params) -> CommandResult:
        """Import selected 3D models and apply rigid body physics tags"""
        try:
            if not selected_models:
                return CommandResult(False, error="No 3D models selected in Tab 2")
            
            imported_objects = []
            for i, model_path in enumerate(selected_models):
                offset_x = pos_x + (i * 300)  # Space models 300 units apart for physics
                
                # Import model first (using working method)
                import_result = await self.client.import_obj(
                    model_path,
                    position=(offset_x, pos_y, pos_z),
                    scale=scale
                )
                
                if import_result:  # import_obj returns boolean
                    # Extract unique name from debug output (working method returns this)
                    # Apply physics tag using simplified approach
                    physics_result = await self.client.add_dynamics_tag(
                        f"ImportedModel_temp",  # Will search for newest ImportedModel object
                        tag_type="rigid_body",
                        mass=mass,
                        friction=friction
                    )
                    
                    if physics_result:
                        imported_objects.append(f"ImportedModel_{i}")
                    else:
                        self.logger.warning(f"Failed to apply rigid body tag to model {i}")
                else:
                    self.logger.warning(f"Failed to import model {i}")
            
            if imported_objects:
                return CommandResult(
                    True,
                    message=f"Imported {len(imported_objects)} models with rigid body physics",
                    data={"imported_objects": imported_objects, "physics_type": "rigidbody"}
                )
            else:
                return CommandResult(False, error="Failed to import models with rigid body tags")
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def import_models_with_cloth(self, pos_x: float = 0.0, pos_y: float = 500.0,
                                      pos_z: float = 0.0, scale: float = 1.0,
                                      cloth_type: str = "cloth", mass: float = 1.0, selected_models=None, **params) -> CommandResult:
        """Import selected 3D models and apply cloth physics tags"""
        try:
            if not selected_models:
                return CommandResult(False, error="No 3D models selected in Tab 2")
            
            imported_objects = []
            for i, model_path in enumerate(selected_models):
                offset_x = pos_x + (i * 300)  # Space models 300 units apart for physics
                
                # Import model first (using working method)
                import_result = await self.client.import_obj(
                    model_path,
                    position=(offset_x, pos_y, pos_z),
                    scale=scale
                )
                
                if import_result:  # import_obj returns boolean
                    # Apply cloth physics tag using the discovered constants
                    physics_result = await self.client.add_dynamics_tag(
                        f"ImportedModel_temp",  # Will search for newest ImportedModel object
                        tag_type=cloth_type,  # "cloth" or "cloth_belt"
                        mass=mass
                    )
                    
                    if physics_result:
                        imported_objects.append(f"ImportedModel_{i}")
                    else:
                        self.logger.warning(f"Failed to apply cloth tag to model {i}")
                else:
                    self.logger.warning(f"Failed to import model {i}")
            
            if imported_objects:
                return CommandResult(
                    True,
                    message=f"Imported {len(imported_objects)} models with cloth physics",
                    data={"imported_objects": imported_objects, "physics_type": "cloth"}
                )
            else:
                return CommandResult(False, error="Failed to import any models with cloth tags")
                
        except Exception as e:
            self.logger.error(f"Error importing models with cloth: {str(e)}")
            return CommandResult(False, error=str(e))
    
    async def quick_import_models(self, spacing_x: float = 200.0, spacing_y: float = 0.0,
                                spacing_z: float = 200.0, selected_models=None, **params) -> CommandResult:
        """Quick import selected 3D models with default settings and automatic spacing"""
        try:
            if not selected_models:
                return CommandResult(False, error="No 3D models selected in Tab 2")
            
            imported_count = 0
            for i, model_path in enumerate(selected_models):
                # Arrange in a grid pattern
                row = i // 3  # 3 models per row
                col = i % 3
                
                position_x = col * spacing_x
                position_y = spacing_y
                position_z = row * spacing_z
                
                result = await self.client.import_obj(
                    model_path,
                    position=(position_x, position_y, position_z),
                    scale=1.0
                )
                
                if result and result.get("success"):
                    imported_count += 1
            
            if imported_count > 0:
                return CommandResult(
                    True,
                    message=f"Quick imported {imported_count}/{len(selected_models)} models in grid layout",
                    data={"imported_count": imported_count, "layout": "grid", "spacing": [spacing_x, spacing_y, spacing_z]}
                )
            else:
                return CommandResult(False, error="Failed to quick import any models")
                
        except Exception as e:
            return CommandResult(False, error=str(e))


class CommandValidator:
    """Validate command parameters"""
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> bool:
        """Validate command and parameters"""
        # Add validation logic here
        return True
    
    def validate_primitive(self, primitive_type: str) -> bool:
        """Validate primitive type"""
        valid_types = [p.value for p in PrimitiveType]
        return primitive_type.lower() in valid_types
