"""
Scene Pattern Library for Cinema4D
Common scene construction patterns based on tutorials and community workflows
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

from utils.logger import LoggerMixin
from .mcp_wrapper import MCPCommandWrapper, CommandResult
from .mograph_engine import MoGraphIntelligenceEngine


@dataclass
class PatternStep:
    """A single step in a scene pattern"""
    name: str
    operation: str
    parameters: Dict[str, Any]
    description: str = ""


@dataclass
class ScenePattern:
    """Complete scene construction pattern"""
    name: str
    description: str
    steps: List[PatternStep]
    tags: List[str] = None


class PatternCategory(Enum):
    """Categories of scene patterns"""
    LANDSCAPE = "landscape"
    ABSTRACT = "abstract"
    ARCHITECTURAL = "architectural"
    MOTION_GRAPHICS = "motion_graphics"
    PRODUCT_VIZ = "product_viz"
    ORGANIC = "organic"
    TECHNICAL = "technical"


class ScenePatternLibrary(LoggerMixin):
    """Library of common scene construction patterns"""
    
    # Pattern definitions based on community workflows
    WORKFLOW_PATTERNS = {
        "landscape_scatter": ScenePattern(
            name="Landscape Scatter",
            description="Scatter objects on terrain with natural distribution",
            steps=[
                PatternStep(
                    "create_terrain",
                    "add_primitive",
                    {"primitive_type": "landscape", "size": 1000, "subdivision": 100}
                ),
                PatternStep(
                    "analyze_heights",
                    "analyze_surface",
                    {"method": "vertex_map", "target": "peaks"}
                ),
                PatternStep(
                    "scatter_objects",
                    "intelligent_scatter",
                    {"mode": "surface", "pattern": "natural", "density": "variable"}
                ),
                PatternStep(
                    "add_variation",
                    "add_effectors",
                    {"types": ["random", "shader"], "parameters": "size_rotation"}
                ),
                PatternStep(
                    "optimize_instances",
                    "enable_render_instances",
                    {"threshold": 100}
                )
            ],
            tags=["nature", "environment", "exterior"]
        ),
        
        "dynamic_connections": ScenePattern(
            name="Dynamic Connections",
            description="Create dynamic connections between objects",
            steps=[
                PatternStep(
                    "analyze_positions",
                    "get_object_positions",
                    {"method": "nearest_neighbor", "max_distance": 500}
                ),
                PatternStep(
                    "create_splines",
                    "create_connection_splines",
                    {"type": "bezier", "subdivisions": 20}
                ),
                PatternStep(
                    "add_dynamics",
                    "apply_dynamics",
                    {"type": "hair", "stiffness": 0.5}
                ),
                PatternStep(
                    "style_splines",
                    "apply_sweep_nurbs",
                    {"profile": "cable", "radius": 2}
                )
            ],
            tags=["technical", "network", "connections"]
        ),
        
        "abstract_growth": ScenePattern(
            name="Abstract Growth",
            description="Create organic growth animation",
            steps=[
                PatternStep(
                    "base_geometry",
                    "add_primitive",
                    {"primitive_type": "sphere", "size": 100}
                ),
                PatternStep(
                    "add_noise_field",
                    "create_field",
                    {"type": "noise", "scale": 200, "animated": True}
                ),
                PatternStep(
                    "volume_mesher",
                    "create_volume_mesh",
                    {"adaptive": True, "voxel_size": 5}
                ),
                PatternStep(
                    "animate_growth",
                    "animate_parameter",
                    {"parameter": "field_strength", "from": 0, "to": 100}
                )
            ],
            tags=["abstract", "animation", "organic"]
        ),
        
        "product_studio": ScenePattern(
            name="Product Studio",
            description="Professional product visualization setup",
            steps=[
                PatternStep(
                    "create_backdrop",
                    "create_studio_backdrop",
                    {"type": "cyc", "size": 1000}
                ),
                PatternStep(
                    "setup_lighting",
                    "create_three_point_lighting",
                    {"key_intensity": 100, "fill_intensity": 50, "rim_intensity": 150}
                ),
                PatternStep(
                    "add_reflections",
                    "create_reflection_plane",
                    {"material": "glossy", "roughness": 0.1}
                ),
                PatternStep(
                    "camera_setup",
                    "create_camera_rig",
                    {"focal_length": 85, "aperture": 2.8}
                )
            ],
            tags=["product", "studio", "visualization"]
        ),
        
        "mograph_array": ScenePattern(
            name="MoGraph Array",
            description="Complex MoGraph array with effectors",
            steps=[
                PatternStep(
                    "create_base",
                    "add_primitive",
                    {"primitive_type": "cube", "size": 50}
                ),
                PatternStep(
                    "create_cloner",
                    "create_mograph_cloner",
                    {"mode": "grid", "count": [10, 10, 10]}
                ),
                PatternStep(
                    "add_effectors",
                    "create_effector_stack",
                    {"effectors": ["plain", "random", "shader", "delay"]}
                ),
                PatternStep(
                    "add_fields",
                    "create_field_layer",
                    {"fields": ["spherical", "linear"], "blend_mode": "add"}
                ),
                PatternStep(
                    "animate_effectors",
                    "animate_effector_parameters",
                    {"parameter": "strength", "loop": True}
                )
            ],
            tags=["mograph", "array", "animation"]
        )
    }
    
    def __init__(self, mcp_wrapper: MCPCommandWrapper, mograph_engine: MoGraphIntelligenceEngine):
        super().__init__()
        self.mcp = mcp_wrapper
        self.mograph = mograph_engine
        self.pattern_executor = PatternExecutor(mcp_wrapper, mograph_engine)
        
    async def execute_pattern(self, pattern_name: str, 
                            context: Dict[str, Any] = None) -> CommandResult:
        """Execute a named pattern"""
        try:
            pattern = self.WORKFLOW_PATTERNS.get(pattern_name)
            if not pattern:
                # Try to find by partial match
                pattern = self._find_pattern_by_description(pattern_name)
                if not pattern:
                    return CommandResult(False, error=f"Pattern '{pattern_name}' not found")
            
            self.logger.info(f"Executing pattern: {pattern.name}")
            
            # Execute pattern steps
            results = []
            execution_context = context or {}
            
            for step in pattern.steps:
                self.logger.info(f"Executing step: {step.name}")
                
                result = await self.pattern_executor.execute_step(
                    step, 
                    execution_context
                )
                
                results.append(result)
                
                if not result.success:
                    self.logger.error(f"Step '{step.name}' failed: {result.error}")
                    return CommandResult(
                        False, 
                        error=f"Pattern failed at step '{step.name}': {result.error}"
                    )
                
                # Update context with results
                if result.data:
                    execution_context.update(result.data)
            
            return CommandResult(
                True,
                message=f"Successfully executed pattern: {pattern.name}",
                data={"results": results, "context": execution_context}
            )
            
        except Exception as e:
            self.logger.error(f"Error executing pattern: {e}")
            return CommandResult(False, error=str(e))
    
    def _find_pattern_by_description(self, description: str) -> Optional[ScenePattern]:
        """Find pattern by description or tags"""
        desc_lower = description.lower()
        
        # Check pattern names and descriptions
        for pattern in self.WORKFLOW_PATTERNS.values():
            if desc_lower in pattern.name.lower() or desc_lower in pattern.description.lower():
                return pattern
            
            # Check tags
            if pattern.tags:
                for tag in pattern.tags:
                    if tag.lower() in desc_lower or desc_lower in tag.lower():
                        return pattern
        
        return None
    
    def get_patterns_by_category(self, category: PatternCategory) -> List[ScenePattern]:
        """Get all patterns in a category"""
        patterns = []
        
        for pattern in self.WORKFLOW_PATTERNS.values():
            if pattern.tags and category.value in pattern.tags:
                patterns.append(pattern)
        
        return patterns
    
    def suggest_patterns(self, description: str) -> List[ScenePattern]:
        """Suggest patterns based on description"""
        suggestions = []
        desc_lower = description.lower()
        
        # Score each pattern
        pattern_scores = {}
        
        for name, pattern in self.WORKFLOW_PATTERNS.items():
            score = 0
            
            # Check name match
            if any(word in pattern.name.lower() for word in desc_lower.split()):
                score += 2
            
            # Check description match
            if any(word in pattern.description.lower() for word in desc_lower.split()):
                score += 1
            
            # Check tag matches
            if pattern.tags:
                for tag in pattern.tags:
                    if tag in desc_lower:
                        score += 1
            
            if score > 0:
                pattern_scores[name] = score
        
        # Sort by score
        sorted_patterns = sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top suggestions
        for name, score in sorted_patterns[:3]:
            suggestions.append(self.WORKFLOW_PATTERNS[name])
        
        return suggestions


class PatternExecutor:
    """Executes individual pattern steps"""
    
    def __init__(self, mcp_wrapper: MCPCommandWrapper, mograph_engine: MoGraphIntelligenceEngine):
        self.mcp = mcp_wrapper
        self.mograph = mograph_engine
        
    async def execute_step(self, step: PatternStep, context: Dict[str, Any]) -> CommandResult:
        """Execute a single pattern step"""
        try:
            # Map operation to actual implementation
            if step.operation == "add_primitive":
                return await self.mcp.add_primitive(**step.parameters)
            
            elif step.operation == "intelligent_scatter":
                objects = context.get("objects", ["Cube"])
                surface = context.get("surface", None)
                return await self.mograph.create_intelligent_scatter(
                    objects, surface, step.parameters.get("pattern", "natural")
                )
            
            elif step.operation == "create_mograph_cloner":
                return await self.mcp.create_mograph_cloner(**step.parameters)
            
            elif step.operation == "analyze_surface":
                surface_name = context.get("terrain_name", "Landscape")
                analysis = await self.mograph.analyze_surface(surface_name)
                return CommandResult(
                    True, 
                    message="Surface analyzed",
                    data={"surface_analysis": analysis}
                )
            
            elif step.operation == "enable_render_instances":
                cloner_name = context.get("cloner_name", "MoGraph_Cloner")
                success = await self.mograph.enable_render_instances(cloner_name)
                return CommandResult(success, message="Render instances enabled")
            
            else:
                # Custom operations would be implemented here
                return CommandResult(
                    False,
                    error=f"Operation '{step.operation}' not implemented"
                )
                
        except Exception as e:
            return CommandResult(False, error=str(e))


class PatternBuilder:
    """Build custom patterns from commands"""
    
    def __init__(self):
        self.current_pattern = None
        self.steps = []
        
    def start_pattern(self, name: str, description: str = ""):
        """Start building a new pattern"""
        self.current_pattern = name
        self.steps = []
        
    def add_step(self, name: str, operation: str, parameters: Dict[str, Any]):
        """Add a step to the current pattern"""
        step = PatternStep(name, operation, parameters)
        self.steps.append(step)
        
    def finish_pattern(self, tags: List[str] = None) -> ScenePattern:
        """Finish and return the pattern"""
        pattern = ScenePattern(
            name=self.current_pattern,
            description="Custom pattern",
            steps=self.steps,
            tags=tags
        )
        
        # Reset
        self.current_pattern = None
        self.steps = []
        
        return pattern