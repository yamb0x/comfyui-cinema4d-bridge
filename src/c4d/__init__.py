"""
Cinema4D Intelligence Module
Natural language processing and intelligent scene assembly
"""

from .nlp_parser import C4DNaturalLanguageParser, SceneIntent, Operation, OperationType
from .mcp_wrapper import MCPCommandWrapper, CommandResult, PrimitiveType, ClonerMode, EffectorType, DeformerType
from .mograph_engine import MoGraphIntelligenceEngine, ScatterPattern
from .scene_patterns import ScenePatternLibrary, ScenePattern, PatternStep
from .operation_generator import OperationGenerator, ExecutableOperation

__all__ = [
    'C4DNaturalLanguageParser',
    'SceneIntent',
    'Operation',
    'OperationType',
    'MCPCommandWrapper',
    'CommandResult',
    'PrimitiveType',
    'ClonerMode',
    'EffectorType',
    'DeformerType',
    'MoGraphIntelligenceEngine',
    'ScatterPattern',
    'ScenePatternLibrary',
    'ScenePattern',
    'PatternStep',
    'OperationGenerator',
    'ExecutableOperation'
]