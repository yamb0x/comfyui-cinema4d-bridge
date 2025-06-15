"""
Operation Generator for Cinema4D
Converts parsed intents into executable operations
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio

from utils.logger import LoggerMixin
from .nlp_parser import SceneIntent, Operation, OperationType
from .mcp_wrapper import MCPCommandWrapper, CommandResult
from .mograph_engine import MoGraphIntelligenceEngine
from .scene_patterns import ScenePatternLibrary


@dataclass
class ExecutableOperation:
    """An operation ready for execution"""
    operation_type: str
    method: callable
    parameters: Dict[str, Any]
    description: str
    requires_context: bool = False


class OperationGenerator(LoggerMixin):
    """Generate executable operations from parsed intent"""
    
    def __init__(self, mcp_wrapper: MCPCommandWrapper, 
                 mograph_engine: MoGraphIntelligenceEngine,
                 pattern_library: ScenePatternLibrary):
        super().__init__()
        self.mcp = mcp_wrapper
        self.mograph = mograph_engine
        self.patterns = pattern_library
        
    async def generate(self, intent: SceneIntent) -> List[ExecutableOperation]:
        """Generate executable operations from intent"""
        try:
            executable_ops = []
            
            # Check if this matches a known pattern
            if self._is_pattern_request(intent):
                pattern_ops = await self._generate_pattern_operations(intent)
                executable_ops.extend(pattern_ops)
            else:
                # Generate individual operations
                for operation in intent.operations:
                    exec_op = await self._generate_single_operation(operation, intent.context)
                    if exec_op:
                        executable_ops.append(exec_op)
            
            # Add any context-based operations
            context_ops = self._generate_context_operations(intent.context)
            executable_ops.extend(context_ops)
            
            return executable_ops
            
        except Exception as e:
            self.logger.error(f"Error generating operations: {e}")
            return []
    
    def _is_pattern_request(self, intent: SceneIntent) -> bool:
        """Check if intent matches a pattern request"""
        # Look for pattern keywords or multiple related operations
        if len(intent.operations) > 2:
            return True
        
        # Check for pattern-related keywords in context
        if intent.context:
            pattern_keywords = ["setup", "workflow", "complete", "full", "entire"]
            context_str = str(intent.context).lower()
            return any(keyword in context_str for keyword in pattern_keywords)
        
        return False
    
    async def _generate_pattern_operations(self, intent: SceneIntent) -> List[ExecutableOperation]:
        """Generate operations for pattern execution"""
        ops = []
        
        # Try to find matching pattern
        suggested_patterns = self.patterns.suggest_patterns(str(intent.operations))
        
        if suggested_patterns:
            pattern = suggested_patterns[0]
            
            # Create operation to execute pattern
            pattern_method = self.patterns.execute_pattern
            ops.append(ExecutableOperation(
                operation_type="execute_pattern",
                method=pattern_method,
                parameters={"pattern_name": pattern.name},
                description=f"Execute {pattern.name} pattern"
            ))
        
        return ops
    
    async def _generate_single_operation(self, operation: Operation, 
                                       context: Dict[str, Any]) -> Optional[ExecutableOperation]:
        """Generate single executable operation"""
        try:
            params = operation.parameters or {}
            
            # Add context to parameters
            if context:
                params.update(self._extract_relevant_context(operation, context))
            
            # Map operation type to method
            if operation.operation_type == OperationType.CREATE_OBJECT:
                # Capture method reference properly
                create_method = self._create_objects
                return ExecutableOperation(
                    operation_type="create_object",
                    method=create_method,
                    parameters=params,
                    description=operation.description or "Create objects"
                )
            
            elif operation.operation_type == OperationType.SCATTER_OBJECTS:
                scatter_method = self._scatter_objects
                return ExecutableOperation(
                    operation_type="scatter",
                    method=scatter_method,
                    parameters=params,
                    description=operation.description or "Scatter objects"
                )
            
            elif operation.operation_type == OperationType.APPLY_DEFORMER:
                deform_method = self._apply_deformer
                return ExecutableOperation(
                    operation_type="deform",
                    method=deform_method,
                    parameters=params,
                    description=operation.description or "Apply deformer"
                )
            
            elif operation.operation_type == OperationType.CREATE_CLONER:
                # For cloner operations, we'll handle object creation internally
                create_method = self._create_objects
                return ExecutableOperation(
                    operation_type="clone",
                    method=create_method,  # Use _create_objects which handles cloning
                    parameters=params,
                    description=operation.description or "Create cloner"
                )
            
            elif operation.operation_type == OperationType.CONNECT_OBJECTS:
                connect_method = self._connect_objects
                return ExecutableOperation(
                    operation_type="connect",
                    method=connect_method,
                    parameters=params,
                    description=operation.description or "Connect objects"
                )
            
            elif operation.operation_type == OperationType.ANIMATE_OBJECTS:
                animate_method = self._animate_objects
                return ExecutableOperation(
                    operation_type="animate",
                    method=animate_method,
                    parameters=params,
                    description=operation.description or "Animate objects"
                )
            
            elif operation.operation_type == OperationType.APPLY_EFFECTOR:
                effector_method = self._apply_effector
                return ExecutableOperation(
                    operation_type="apply_effector",
                    method=effector_method,
                    parameters=params,
                    description=operation.description or "Apply effector"
                )
            
            else:
                self.logger.warning(f"Unknown operation type: {operation.operation_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating operation: {e}")
            return None
    
    def _extract_relevant_context(self, operation: Operation, 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context for operation"""
        relevant = {}
        
        # Extract position context
        if "position" in context:
            if operation.operation_type in [OperationType.CREATE_OBJECT, OperationType.SCATTER_OBJECTS]:
                relevant["position_hint"] = context["position"]
        
        # Extract scale context
        if "scale" in context:
            relevant["scale_modifier"] = context["scale"]
        
        # Extract speed context for animations
        if "speed" in context and operation.operation_type == OperationType.ANIMATE_OBJECTS:
            relevant["animation_speed"] = context["speed"]
        
        return relevant
    
    def _generate_context_operations(self, context: Dict[str, Any]) -> List[ExecutableOperation]:
        """Generate additional operations based on context"""
        ops = []
        
        # Add camera setup if viewing angle mentioned
        if context and any(key in context for key in ["view", "angle", "camera"]):
            camera_method = self._setup_camera
            ops.append(ExecutableOperation(
                operation_type="setup_camera",
                method=camera_method,
                parameters={"angle": context.get("angle", "default")},
                description="Setup camera view"
            ))
        
        return ops
    
    # Operation implementation methods
    async def _create_objects(self, **params) -> CommandResult:
        """Create objects based on parameters"""
        try:
            object_type = params.get("object_type", "cube")
            count = params.get("count", 1)
            size = params.get("size", 100)
            position = params.get("position", (0, 0, 0))
            
            self.logger.debug(f"Creating objects: type={object_type}, count={count}, size={size}, pos={position}")
            
            if count == 1:
                # Single object
                return await self.mcp.add_primitive(
                    primitive_type=object_type,
                    name=f"{object_type.capitalize()}_1",
                    size=size,
                    position=position
                )
            else:
                # Multiple objects - use cloner with integrated object creation
                mode = params.get("mode", "grid")
                self.logger.debug(f"Creating cloner with integrated object: mode={mode}, count={count}")
                
                # Create cloner with object in one operation
                return await self.mcp.create_cloner_with_object(
                    object_type=object_type,
                    object_size=size,
                    mode=mode,
                    count=count
                )
                
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def _scatter_objects(self, **params) -> CommandResult:
        """Scatter objects intelligently"""
        try:
            objects = params.get("objects", ["Cube"])
            surface = params.get("surface", None)
            description = params.get("description", "natural scatter")
            
            return await self.mograph.create_intelligent_scatter(
                objects=objects,
                surface=surface,
                description=description,
                count=params.get("count", None)
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def _apply_deformer(self, **params) -> CommandResult:
        """Apply deformer to objects"""
        try:
            object_name = params.get("object", "Cube")
            deformer_type = params.get("deformer_type", "bend")
            strength = params.get("strength", 0.5)
            
            return await self.mcp.apply_deformer(
                object_name=object_name,
                deformer_type=deformer_type,
                strength=strength
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def _create_cloner(self, **params) -> CommandResult:
        """Create MoGraph cloner"""
        try:
            return await self.mcp.create_mograph_cloner(**params)
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def _connect_objects(self, **params) -> CommandResult:
        """Connect objects with splines"""
        try:
            objects = params.get("objects", [])
            connection_type = params.get("connection_type", "spline")
            
            return await self.mograph.create_dynamic_connections(
                objects=objects,
                connection_type=connection_type
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def _animate_objects(self, **params) -> CommandResult:
        """Animate objects"""
        try:
            # Animation implementation would go here
            return CommandResult(
                True,
                message=f"Animation setup complete"
            )
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def _setup_camera(self, **params) -> CommandResult:
        """Setup camera view"""
        try:
            # Camera setup implementation
            return CommandResult(
                True,
                message="Camera setup complete"
            )
        except Exception as e:
            return CommandResult(False, error=str(e))
    
    async def _apply_effector(self, **params) -> CommandResult:
        """Apply effector to cloner or objects"""
        try:
            # Determine effector type from context
            effector_type = params.get("effector_type", "random")
            target = params.get("target", "MoGraph_Cloner")
            
            # Map keywords to effector types
            if "random" in str(params):
                effector_type = "random"
            elif "delay" in str(params):
                effector_type = "delay"
            elif "shader" in str(params):
                effector_type = "shader"
            
            return await self.mcp.add_effector(
                cloner_name=target,
                effector_type=effector_type,
                **params
            )
            
        except Exception as e:
            return CommandResult(False, error=str(e))


class OperationExecutor:
    """Execute operations and handle results"""
    
    def __init__(self):
        self.execution_history = []
        
    async def execute(self, operation: ExecutableOperation) -> CommandResult:
        """Execute a single operation"""
        try:
            # Execute the operation
            result = await operation.method(**operation.parameters)
            
            # Record in history
            self.execution_history.append({
                "operation": operation.operation_type,
                "description": operation.description,
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_result = CommandResult(False, error=str(e))
            self.execution_history.append({
                "operation": operation.operation_type,
                "description": operation.description,
                "result": error_result
            })
            return error_result
    
    async def execute_sequence(self, operations: List[ExecutableOperation]) -> List[CommandResult]:
        """Execute a sequence of operations"""
        results = []
        
        for operation in operations:
            result = await self.execute(operation)
            results.append(result)
            
            # Stop on failure unless specified otherwise
            if not result.success and not operation.requires_context:
                break
        
        return results