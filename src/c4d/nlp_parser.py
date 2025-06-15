"""
Natural Language Parser for Cinema4D Commands
Converts artist-friendly language to actionable C4D operations
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin


class OperationType(Enum):
    """Types of Cinema4D operations"""
    CREATE_OBJECT = "create_object"
    SCATTER_OBJECTS = "scatter_objects"
    APPLY_DEFORMER = "apply_deformer"
    CREATE_CLONER = "create_cloner"
    ADD_DYNAMICS = "add_dynamics"
    CONNECT_OBJECTS = "connect_objects"
    APPLY_MATERIAL = "apply_material"
    ANIMATE_OBJECTS = "animate_objects"
    CREATE_HAIR = "create_hair"
    MODIFY_OBJECT = "modify_object"
    APPLY_EFFECTOR = "apply_effector"


@dataclass
class ParsedEntity:
    """Parsed entity from natural language"""
    entity_type: str  # object, number, color, etc.
    value: Any
    modifiers: List[str] = None


@dataclass
class Operation:
    """A single C4D operation to execute"""
    operation_type: OperationType
    target_objects: List[str] = None
    parameters: Dict[str, Any] = None
    description: str = ""


@dataclass
class SceneIntent:
    """Complete parsed intent from user input"""
    operations: List[Operation]
    context: Dict[str, Any] = None
    confidence: float = 1.0


class C4DNaturalLanguageParser(LoggerMixin):
    """Parse natural language into C4D operations"""
    
    # Pattern library for common artist expressions
    PATTERN_LIBRARY = {
        # Object creation patterns
        "create": {
            "keywords": ["create", "make", "generate", "build", "add"],
            "operation": OperationType.CREATE_OBJECT,
            "extract": ["object_type", "count", "arrangement"]
        },
        
        # Scattering patterns
        "scatter": {
            "keywords": ["scatter", "distribute", "spread", "populate", "place"],
            "operation": OperationType.SCATTER_OBJECTS,
            "extract": ["objects", "surface", "density", "variation"]
        },
        
        # Organic modifiers
        "organic": {
            "keywords": ["organic", "natural", "irregular", "random", "flowing"],
            "modifiers": ["noise_field", "random_effector", "shader_effector"],
            "parameters": {"variation": 0.8, "seed": "random"}
        },
        
        # Connection patterns
        "connect": {
            "keywords": ["connect", "link", "bridge", "wire", "bind"],
            "operation": OperationType.CONNECT_OBJECTS,
            "extract": ["source_objects", "connection_type"]
        },
        
        # Deformation patterns
        "deform": {
            "keywords": ["bend", "twist", "taper", "bulge", "deform", "squash", "stretch", "warp", "distort"],
            "operation": OperationType.APPLY_DEFORMER,
            "extract": ["deformer_type", "strength", "axis"]
        },
        
        # Effector patterns
        "effector": {
            "keywords": ["effector", "effect"],
            "operation": OperationType.APPLY_EFFECTOR,
            "extract": ["effector_type", "strength"]
        },
        
        # Animation patterns
        "animate": {
            "keywords": ["animate", "move", "rotate", "scale", "transform"],
            "operation": OperationType.ANIMATE_OBJECTS,
            "extract": ["animation_type", "duration", "loop"]
        },
        
        # Hair/Fiber patterns
        "hair": {
            "keywords": ["hair", "fur", "grass", "fibers", "bristles"],
            "operation": OperationType.CREATE_HAIR,
            "extract": ["hair_type", "density", "length"]
        },
        
        # Cloning patterns
        "clone": {
            "keywords": ["clone", "array", "grid", "radial", "duplicate", "repeat", "copy"],
            "operation": OperationType.CREATE_CLONER,
            "extract": ["clone_mode", "count", "spacing"]
        },
        
        # Effector patterns
        "effector": {
            "keywords": ["random", "randomize", "vary", "offset", "displace", "jitter"],
            "operation": OperationType.APPLY_EFFECTOR,
            "extract": ["effector_type", "strength"]
        }
    }
    
    # Object type mappings with expanded aliases
    OBJECT_TYPES = {
        "cube": ["cube", "box", "block", "square", "crate"],
        "sphere": ["sphere", "ball", "orb", "globe", "round"],
        "cylinder": ["cylinder", "tube", "pipe", "barrel", "can", "pillar", "column"],
        "cone": ["cone", "triangle", "spike", "funnel"],
        "pyramid": ["pyramid", "tetrahedron", "triangular"],
        "torus": ["torus", "donut", "ring", "doughnut", "loop"],
        "plane": ["plane", "floor", "ground", "surface", "flat", "sheet"],
        "disc": ["disc", "disk", "circle", "round plane"],
        "tube": ["tube", "hollow cylinder", "straw"],
        "platonic": ["platonic", "polyhedron", "icosahedron", "dodecahedron"],
        "landscape": ["landscape", "terrain", "mountain", "hills", "ground"],
        "text": ["text", "type", "letters", "words", "typography", "font"]
    }
    
    # Arrangement patterns - ORDER MATTERS (check specific before generic)
    ARRANGEMENTS = {
        "radial": ["radial", "circular", "around", "circle"],
        "linear": ["line", "row", "linear", "straight"],
        "honeycomb": ["honeycomb", "hexagonal", "hex"],
        "grid": ["grid", "matrix", "array"],  # "array" is generic, check last
        "random": ["random", "scattered", "chaotic"],
        "spiral": ["spiral", "helix", "swirl"]
    }
    
    # Size modifiers with their corresponding values
    SIZE_MODIFIERS = {
        "tiny": 25,
        "small": 50,
        "medium": 100,
        "large": 200,
        "big": 200,
        "huge": 400,
        "massive": 800,
        "giant": 1000
    }
    
    # Position modifiers
    POSITION_MODIFIERS = {
        "top": (0, 200, 0),
        "bottom": (0, -200, 0),
        "left": (-200, 0, 0),
        "right": (200, 0, 0),
        "center": (0, 0, 0),
        "middle": (0, 0, 0),
        "front": (0, 0, 200),
        "back": (0, 0, -200)
    }
    
    # Strength modifiers for deformers/effects
    STRENGTH_MODIFIERS = {
        "slightly": 0.2,
        "gently": 0.3,
        "moderately": 0.5,
        "strongly": 0.8,
        "extremely": 1.0,
        "intensely": 0.9,
        "subtly": 0.1
    }
    
    def __init__(self):
        super().__init__()
        self.entity_extractor = EntityExtractor()
        self.parameter_mapper = ParameterMapper()
        
    async def parse(self, text: str) -> SceneIntent:
        """Parse natural language text into scene intent"""
        try:
            # Normalize text
            text_lower = text.lower().strip()
            
            # Extract operations
            operations = self._extract_operations(text_lower)
            
            # Extract entities
            entities = self._extract_entities(text_lower)
            
            # Map entities to operations
            operations = self._map_entities_to_operations(operations, entities, text_lower)
            
            # Extract context
            context = self._extract_context(text_lower)
            
            # Calculate confidence
            confidence = self._calculate_confidence(operations, text_lower)
            
            return SceneIntent(
                operations=operations,
                context=context,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing natural language: {e}")
            return SceneIntent(operations=[], confidence=0.0)
    
    def _extract_operations(self, text: str) -> List[Operation]:
        """Extract operations from text"""
        operations = []
        operation_types_found = set()
        
        # Check for cloner/array patterns first (higher priority)
        if any(keyword in text for keyword in ["grid", "array", "radial", "honeycomb", "linear", "line"]):
            operations.append(Operation(
                operation_type=OperationType.CREATE_CLONER,
                parameters={},
                description="clone operation detected"
            ))
            operation_types_found.add(OperationType.CREATE_CLONER)
            return operations  # Return early to avoid duplicate CREATE_OBJECT
        
        for pattern_name, pattern_data in self.PATTERN_LIBRARY.items():
            # Skip if we already have this operation type
            op_type = pattern_data.get("operation", OperationType.CREATE_OBJECT)
            if op_type in operation_types_found:
                continue
                
            # Check if any keyword matches
            for keyword in pattern_data["keywords"]:
                if keyword in text:
                    operation = Operation(
                        operation_type=op_type,
                        parameters={},
                        description=f"{pattern_name} operation detected"
                    )
                    operations.append(operation)
                    operation_types_found.add(op_type)
                    break
        
        # If no operations found, try to infer from object mentions
        if not operations:
            for obj_type in self.OBJECT_TYPES:
                if any(alias in text for alias in self.OBJECT_TYPES[obj_type]):
                    operations.append(Operation(
                        operation_type=OperationType.CREATE_OBJECT,
                        parameters={"object_type": obj_type},
                        description=f"Create {obj_type}"
                    ))
                    break
        
        return operations
    
    def _extract_entities(self, text: str) -> List[ParsedEntity]:
        """Extract entities like objects, numbers, colors"""
        entities = []
        
        # Extract numbers (including word numbers)
        number_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "dozen": 12, "twenty": 20, "fifty": 50, "hundred": 100
        }
        
        # Extract digit numbers
        numbers = re.findall(r'\b(\d+)\b', text)
        for num in numbers:
            entities.append(ParsedEntity("number", int(num)))
            
        # Extract word numbers
        for word, value in number_words.items():
            if word in text:
                entities.append(ParsedEntity("number", value))
        
        # Extract object types
        for obj_type, aliases in self.OBJECT_TYPES.items():
            for alias in aliases:
                if alias in text:
                    entities.append(ParsedEntity("object", obj_type))
                    break
        
        # Extract size modifiers
        for size_name, size_value in self.SIZE_MODIFIERS.items():
            if size_name in text:
                entities.append(ParsedEntity("size", size_value, modifiers=[size_name]))
        
        # Extract position modifiers
        for pos_name, pos_value in self.POSITION_MODIFIERS.items():
            if pos_name in text:
                entities.append(ParsedEntity("position", pos_value, modifiers=[pos_name]))
        
        # Extract strength modifiers
        for strength_name, strength_value in self.STRENGTH_MODIFIERS.items():
            if strength_name in text:
                entities.append(ParsedEntity("strength", strength_value, modifiers=[strength_name]))
        
        # Extract arrangements
        for arr_type, aliases in self.ARRANGEMENTS.items():
            for alias in aliases:
                if alias in text:
                    entities.append(ParsedEntity("arrangement", arr_type))
                    break
        
        # Extract colors
        color_pattern = r'\b(red|blue|green|yellow|orange|purple|black|white|gray|pink|brown|cyan|magenta)\b'
        colors = re.findall(color_pattern, text)
        for color in colors:
            entities.append(ParsedEntity("color", color))
        
        # Extract deformers
        deformer_words = ["bend", "twist", "taper", "bulge", "squash", "stretch", "warp", "distort", "shear"]
        for deformer in deformer_words:
            if deformer in text:
                entities.append(ParsedEntity("deformer", deformer))
        
        # Extract effectors
        effector_words = ["random", "plain", "formula", "delay", "shader", "step", "sound", "volume"]
        for effector in effector_words:
            if effector in text and "effector" in text:  # Only if "effector" is mentioned
                entities.append(ParsedEntity("effector", effector))
        
        # Extract material types
        if "material" in text:
            if "redshift" in text:
                entities.append(ParsedEntity("material_type", "redshift"))
            else:
                entities.append(ParsedEntity("material_type", "standard"))
            
            # Extract material properties
            if "glowing" in text or "luminance" in text:
                entities.append(ParsedEntity("material_property", "luminance"))
            if "reflective" in text or "reflection" in text:
                entities.append(ParsedEntity("material_property", "reflection"))
        
        # Extract dynamics types
        dynamics_words = ["rigid body", "soft body", "cloth", "rope"]
        for dynamics in dynamics_words:
            if dynamics.replace(" ", "_") in text.replace(" ", "_"):
                entities.append(ParsedEntity("dynamics_type", dynamics.replace(" ", "_")))
        
        # Extract field types
        field_words = ["linear", "spherical", "box", "cylinder", "cone", "torus", "random", "shader"]
        for field in field_words:
            if field in text and "field" in text:
                entities.append(ParsedEntity("field_type", field))
        
        # Extract generator types
        if "loft" in text:
            entities.append(ParsedEntity("generator", "loft"))
        
        # Extract shape types for abstract shapes
        if "shape" in text:
            shape_types = ["organic", "abstract", "complex", "simple", "geometric"]
            for shape_type in shape_types:
                if shape_type in text:
                    entities.append(ParsedEntity("shape_type", shape_type))
        
        # Extract modifiers (only if not already extracted as something else)
        modifier_words = ["smooth", "sharp", "soft", "hard", "metallic", "glass", "rough", "shiny"]
        for modifier in modifier_words:
            if modifier in text:
                entities.append(ParsedEntity("modifier", modifier))
        
        return entities
    
    def _map_entities_to_operations(self, operations: List[Operation], 
                                   entities: List[ParsedEntity], 
                                   text: str) -> List[Operation]:
        """Map extracted entities to operations"""
        
        for operation in operations:
            # Map object types
            obj_entities = [e for e in entities if e.entity_type == "object"]
            if obj_entities:
                operation.parameters["object_type"] = obj_entities[0].value
            
            # Map counts
            num_entities = [e for e in entities if e.entity_type == "number"]
            if num_entities:
                if operation.operation_type == OperationType.CREATE_CLONER:
                    operation.parameters["count"] = num_entities[0].value
                elif operation.operation_type == OperationType.CREATE_OBJECT:
                    operation.parameters["count"] = num_entities[0].value
            else:
                # Default counts for cloner operations without explicit numbers
                if operation.operation_type == OperationType.CREATE_CLONER:
                    # Check for plural forms or array patterns to infer multiple objects
                    if any(word in text for word in ["cubes", "spheres", "cylinders", "objects", "clones", "array", "grid", "pattern"]):
                        operation.parameters["count"] = 10  # Default for plural or array patterns
                    else:
                        operation.parameters["count"] = 3   # Default minimum for grid (can't be 1)
            
            # Map size modifiers
            size_entities = [e for e in entities if e.entity_type == "size"]
            if size_entities:
                operation.parameters["size"] = size_entities[0].value
                
            # Map position modifiers
            pos_entities = [e for e in entities if e.entity_type == "position"]
            if pos_entities:
                operation.parameters["position"] = pos_entities[0].value
            
            # Map strength modifiers
            strength_entities = [e for e in entities if e.entity_type == "strength"]
            if strength_entities:
                operation.parameters["strength"] = strength_entities[0].value
            
            # Map arrangements
            arr_entities = [e for e in entities if e.entity_type == "arrangement"]
            if arr_entities:
                if operation.operation_type in [OperationType.CREATE_CLONER, OperationType.SCATTER_OBJECTS]:
                    operation.parameters["mode"] = arr_entities[0].value
            
            # Map colors
            color_entities = [e for e in entities if e.entity_type == "color"]
            if color_entities:
                operation.parameters["color"] = color_entities[0].value
            
            # Map deformers
            deformer_entities = [e for e in entities if e.entity_type == "deformer"]
            if deformer_entities and operation.operation_type == OperationType.APPLY_DEFORMER:
                operation.parameters["deformer_type"] = deformer_entities[0].value
            
            # Map effectors
            effector_entities = [e for e in entities if e.entity_type == "effector"]
            if effector_entities:
                operation.parameters["effector_type"] = effector_entities[0].value
            
            # Map shape types
            shape_entities = [e for e in entities if e.entity_type == "shape_type"]
            if shape_entities:
                operation.parameters["shape_type"] = shape_entities[0].value
            
            # Map modifiers
            mod_entities = [e for e in entities if e.entity_type == "modifier"]
            if mod_entities:
                operation.parameters["modifiers"] = [e.value for e in mod_entities]
        
        return operations
    
    def _extract_context(self, text: str) -> Dict[str, Any]:
        """Extract additional context from text"""
        context = {}
        
        # Check for size references
        if "big" in text or "large" in text:
            context["scale"] = "large"
        elif "small" in text or "tiny" in text:
            context["scale"] = "small"
        
        # Check for speed references
        if "fast" in text or "quickly" in text:
            context["speed"] = "fast"
        elif "slow" in text or "slowly" in text:
            context["speed"] = "slow"
        
        # Check for specific positions
        if "center" in text or "middle" in text:
            context["position"] = "center"
        elif "top" in text:
            context["position"] = "top"
        elif "bottom" in text:
            context["position"] = "bottom"
        
        return context
    
    def _calculate_confidence(self, operations: List[Operation], text: str) -> float:
        """Calculate confidence score for parsed intent"""
        if not operations:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence for each matched operation
        confidence += len(operations) * 0.1
        
        # Increase confidence for specific keywords
        high_confidence_words = ["create", "make", "scatter", "clone"]
        for word in high_confidence_words:
            if word in text:
                confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)


class EntityExtractor:
    """Extract specific entities from text"""
    
    def extract_surface_reference(self, text: str) -> Optional[str]:
        """Extract surface references like 'on the terrain'"""
        surface_patterns = [
            r'on the (\w+)',
            r'across the (\w+)',
            r'over the (\w+)',
            r'on (\w+)'
        ]
        
        for pattern in surface_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def extract_position_reference(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract position references like 'at the top'"""
        position_patterns = {
            "top": ["top", "peaks", "summit", "highest"],
            "bottom": ["bottom", "base", "lowest"],
            "center": ["center", "middle", "central"],
            "edges": ["edges", "border", "perimeter"]
        }
        
        for position, keywords in position_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    return (position, keyword)
        
        return None


class ParameterMapper:
    """Map natural language parameters to C4D values"""
    
    def map_density(self, text: str) -> int:
        """Map density descriptions to numeric values"""
        if "dense" in text or "many" in text:
            return 100
        elif "sparse" in text or "few" in text:
            return 20
        else:
            return 50
    
    def map_size(self, text: str) -> float:
        """Map size descriptions to scale values"""
        if "large" in text or "big" in text:
            return 2.0
        elif "small" in text or "tiny" in text:
            return 0.5
        else:
            return 1.0
    
    def map_strength(self, text: str) -> float:
        """Map strength descriptions to values"""
        if "strong" in text or "intense" in text:
            return 0.8
        elif "subtle" in text or "slight" in text:
            return 0.2
        else:
            return 0.5