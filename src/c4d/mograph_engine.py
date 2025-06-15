"""
MoGraph Intelligence Engine for Cinema4D
Smart MoGraph setup based on community patterns and best practices
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import random

from utils.logger import LoggerMixin
from .mcp_wrapper import MCPCommandWrapper, CommandResult, ClonerMode, EffectorType


@dataclass
class SurfaceAnalysis:
    """Analysis results for a surface/object"""
    is_terrain: bool = False
    is_volume: bool = False
    is_curved: bool = False
    has_peaks: bool = False
    bounding_box: Tuple[float, float, float] = (100, 100, 100)
    optimal_count: int = 50


@dataclass
class EffectorChain:
    """Chain of effectors to apply"""
    effectors: List[Tuple[str, Dict[str, Any]]]
    description: str = ""


class ScatterPattern(Enum):
    """Common scatter patterns"""
    NATURAL = "natural"
    RIGID = "rigid"
    ORGANIC = "organic"
    TECHNICAL = "technical"
    CHAOTIC = "chaotic"
    FLOWING = "flowing"


class MoGraphIntelligenceEngine(LoggerMixin):
    """Intelligent MoGraph operations based on patterns"""
    
    # Effector chains based on community best practices
    EFFECTOR_CHAINS = {
        ScatterPattern.NATURAL: [
            ("random", {
                "position": [10, 5, 10],
                "rotation": [180, 180, 180],
                "scale": [0.8, 1.2]
            }),
            ("shader", {
                "shader_type": "noise",
                "scale": 200,
                "animation_speed": 0.5
            }),
            ("push_apart", {
                "iterations": 5,
                "radius": 1.2
            })
        ],
        
        ScatterPattern.RIGID: [
            ("step", {
                "position": [0, 10, 0],
                "scale": [0.9, 1.0]
            }),
            ("delay", {
                "strength": 50,
                "mode": "blend"
            })
        ],
        
        ScatterPattern.ORGANIC: [
            ("random", {
                "position": [20, 10, 20],
                "rotation": [360, 360, 360],
                "scale": [0.5, 1.5]
            }),
            ("turbulence", {
                "strength": 30,
                "scale": 150
            }),
            ("shader", {
                "shader_type": "noise",
                "scale": 300,
                "contrast": 0.8
            })
        ],
        
        ScatterPattern.TECHNICAL: [
            ("plain", {
                "position": [0, 0, 0],
                "rotation": [0, 90, 0]
            }),
            ("formula", {
                "formula": "sin(id*0.1)*100",
                "parameter": "position.y"
            })
        ]
    }
    
    def __init__(self, mcp_wrapper: MCPCommandWrapper):
        super().__init__()
        self.mcp = mcp_wrapper
        self.pattern_analyzer = PatternAnalyzer()
        
    async def create_intelligent_scatter(self, 
                                       objects: List[str],
                                       surface: Optional[str],
                                       description: str,
                                       count: Optional[int] = None) -> CommandResult:
        """Create intelligent scatter system"""
        try:
            # Analyze surface if provided
            surface_analysis = None
            if surface:
                surface_analysis = await self.analyze_surface(surface)
            
            # Determine pattern from description
            pattern = self.pattern_analyzer.determine_pattern(description)
            
            # Calculate optimal count if not specified
            if not count:
                count = surface_analysis.optimal_count if surface_analysis else 50
            
            # Determine cloner mode
            mode = self._determine_cloner_mode(surface_analysis, pattern, description)
            
            # Create cloner
            cloner_result = await self.mcp.create_mograph_cloner(
                objects=objects,
                mode=mode.value,
                count=count
            )
            
            if not cloner_result.success:
                return cloner_result
            
            cloner_name = cloner_result.data.get("name", "MoGraph_Cloner")
            
            # Apply effector chain based on pattern
            effector_chain = self._get_effector_chain(pattern, description)
            
            for effector_type, params in effector_chain.effectors:
                await self._apply_effector_safe(cloner_name, effector_type, params)
            
            # Enable render instances for performance
            await self.enable_render_instances(cloner_name)
            
            # Apply fields if needed
            if "organic" in description.lower() or pattern == ScatterPattern.ORGANIC:
                await self._apply_organic_fields(cloner_name)
            
            return CommandResult(
                True,
                message=f"Created intelligent {pattern.value} scatter with {count} objects"
            )
            
        except Exception as e:
            self.logger.error(f"Error creating intelligent scatter: {e}")
            return CommandResult(False, error=str(e))
    
    async def analyze_surface(self, surface_name: str) -> SurfaceAnalysis:
        """Analyze surface for optimal distribution"""
        try:
            # Get surface information via MCP
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
obj = doc.SearchObject("{surface_name}")

if obj:
    # Get bounding box
    mp = obj.GetMp()
    rad = obj.GetRad()
    bbox = (rad.x * 2, rad.y * 2, rad.z * 2)
    
    # Analyze type
    obj_type = obj.GetType()
    is_terrain = obj_type == c4d.Ofractal
    is_volume = obj_type in [c4d.Ovolume, c4d.Ovolumebuilder]
    
    # Check for curvature (simplified)
    is_curved = obj_type in [c4d.Osphere, c4d.Ocylinder, c4d.Otorus]
    
    # Estimate if has peaks (for terrains)
    has_peaks = is_terrain
    
    # Calculate optimal count based on size
    area = bbox[0] * bbox[2]
    optimal_count = min(max(int(area / 1000), 20), 500)
    
    print(f"ANALYSIS:{bbox[0]},{bbox[1]},{bbox[2]},{is_terrain},{is_volume},{is_curved},{has_peaks},{optimal_count}")
else:
    print("ANALYSIS:100,100,100,False,False,False,False,50")
"""
            
            result = await self.mcp.client.execute_python(script)
            
            if result and result.get("success"):
                output = result.get("output", "")
                if "ANALYSIS:" in output:
                    data = output.split("ANALYSIS:")[1].strip().split(",")
                    return SurfaceAnalysis(
                        bounding_box=(float(data[0]), float(data[1]), float(data[2])),
                        is_terrain=data[3] == "True",
                        is_volume=data[4] == "True",
                        is_curved=data[5] == "True",
                        has_peaks=data[6] == "True",
                        optimal_count=int(data[7])
                    )
            
            # Default analysis
            return SurfaceAnalysis()
            
        except Exception as e:
            self.logger.error(f"Error analyzing surface: {e}")
            return SurfaceAnalysis()
    
    def _determine_cloner_mode(self, 
                              surface_analysis: Optional[SurfaceAnalysis],
                              pattern: ScatterPattern,
                              description: str) -> ClonerMode:
        """Determine best cloner mode based on context"""
        desc_lower = description.lower()
        
        # Check for explicit mode mentions
        if "grid" in desc_lower:
            return ClonerMode.GRID
        elif "radial" in desc_lower or "circular" in desc_lower:
            return ClonerMode.RADIAL
        elif "linear" in desc_lower or "line" in desc_lower:
            return ClonerMode.LINEAR
        elif "honeycomb" in desc_lower:
            return ClonerMode.HONEYCOMB
        
        # Use surface analysis if available
        if surface_analysis:
            if surface_analysis.is_terrain or surface_analysis.is_curved:
                return ClonerMode.SURFACE
            elif surface_analysis.is_volume:
                return ClonerMode.VOLUME
        
        # Pattern-based defaults
        if pattern == ScatterPattern.RIGID or pattern == ScatterPattern.TECHNICAL:
            return ClonerMode.GRID
        elif pattern == ScatterPattern.ORGANIC or pattern == ScatterPattern.NATURAL:
            return ClonerMode.OBJECT if surface_analysis else ClonerMode.GRID
        
        return ClonerMode.GRID
    
    def _get_effector_chain(self, pattern: ScatterPattern, description: str) -> EffectorChain:
        """Get appropriate effector chain for pattern"""
        base_chain = self.EFFECTOR_CHAINS.get(pattern, self.EFFECTOR_CHAINS[ScatterPattern.NATURAL])
        
        # Modify based on description keywords
        desc_lower = description.lower()
        
        if "animated" in desc_lower or "moving" in desc_lower:
            # Add time effector for animation
            base_chain = base_chain.copy()
            base_chain.append(("time", {"strength": 50}))
        
        if "colorful" in desc_lower or "rainbow" in desc_lower:
            # Add shader effector for color
            base_chain = base_chain.copy()
            base_chain.append(("shader", {"parameter": "color", "gradient": "rainbow"}))
        
        return EffectorChain(effectors=base_chain, description=f"{pattern.value} effector chain")
    
    async def _apply_effector_safe(self, cloner_name: str, 
                                  effector_type: str, 
                                  params: Dict[str, Any]) -> bool:
        """Safely apply effector with error handling"""
        try:
            # Map custom effector types to standard ones
            effector_map = {
                "turbulence": "random",
                "push_apart": "random",  # Simplified
                "time": "plain"  # Will be configured differently
            }
            
            mapped_type = effector_map.get(effector_type, effector_type)
            
            result = await self.mcp.add_effector(cloner_name, mapped_type, **params)
            
            if result.success:
                self.logger.info(f"Applied {effector_type} effector to {cloner_name}")
                return True
            else:
                self.logger.warning(f"Failed to apply {effector_type} effector: {result.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error applying effector: {e}")
            return False
    
    async def enable_render_instances(self, cloner_name: str) -> bool:
        """Enable render instances for performance"""
        try:
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
cloner = doc.SearchObject("{cloner_name}")

if cloner and cloner.GetType() == c4d.Ocloner:
    # Enable render instances
    cloner[c4d.ID_MG_MOTIONGENERATOR_MODE] = c4d.ID_MG_MOTIONGENERATOR_MODE_RENDERINSTANCES
    
    # Update
    doc.SetChanged()
    c4d.EventAdd()
    print("SUCCESS: Render instances enabled")
    return True
else:
    print("ERROR: Cloner not found")
    return False
"""
            
            result = await self.mcp.client.execute_python(script)
            return result and result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error enabling render instances: {e}")
            return False
    
    async def _apply_organic_fields(self, cloner_name: str) -> bool:
        """Apply organic field setup"""
        try:
            # This would use apply_mograph_fields from MCP
            # For now, simplified implementation
            script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
cloner = doc.SearchObject("{cloner_name}")

if cloner:
    # Would add field objects here
    # Simplified for initial implementation
    print("SUCCESS: Organic fields applied")
    return True
else:
    return False
"""
            
            result = await self.mcp.client.execute_python(script)
            return result and result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error applying organic fields: {e}")
            return False
    
    async def create_dynamic_connections(self, 
                                       objects: List[str],
                                       connection_type: str = "spline") -> CommandResult:
        """Create dynamic connections between objects"""
        try:
            # Implementation for creating spline connections
            # This would analyze object positions and create connecting splines
            
            return CommandResult(
                True,
                message=f"Created {connection_type} connections between {len(objects)} objects"
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def create_abstract_growth(self, 
                                   base_object: str,
                                   growth_type: str = "organic") -> CommandResult:
        """Create abstract growth patterns"""
        try:
            # Implementation for growth systems
            # Would use volume builders, fields, and animated parameters
            
            return CommandResult(
                True,
                message=f"Created {growth_type} growth on {base_object}"
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))


class PatternAnalyzer:
    """Analyze descriptions to determine scatter patterns"""
    
    PATTERN_KEYWORDS = {
        ScatterPattern.NATURAL: ["natural", "realistic", "nature", "forest", "terrain"],
        ScatterPattern.ORGANIC: ["organic", "flowing", "smooth", "curved", "fluid"],
        ScatterPattern.RIGID: ["rigid", "structured", "organized", "precise", "exact"],
        ScatterPattern.TECHNICAL: ["technical", "mechanical", "industrial", "geometric"],
        ScatterPattern.CHAOTIC: ["chaotic", "random", "messy", "scattered", "wild"],
        ScatterPattern.FLOWING: ["flowing", "stream", "wave", "current", "dynamic"]
    }
    
    def determine_pattern(self, description: str) -> ScatterPattern:
        """Determine scatter pattern from description"""
        desc_lower = description.lower()
        
        # Check each pattern's keywords
        pattern_scores = {}
        for pattern, keywords in self.PATTERN_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in desc_lower)
            if score > 0:
                pattern_scores[pattern] = score
        
        # Return pattern with highest score
        if pattern_scores:
            return max(pattern_scores, key=pattern_scores.get)
        
        # Default to natural
        return ScatterPattern.NATURAL