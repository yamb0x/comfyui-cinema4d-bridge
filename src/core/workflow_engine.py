"""
Workflow Engine

Centralized workflow execution engine extracted from monolithic application.
Handles complete workflow lifecycle from parameter collection to completion monitoring.

Part of Phase 2 architectural decomposition - implements the multi-mind analysis
recommendation for focused workflow execution responsibility with better error
handling and monitoring.
"""

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from ..utils.advanced_logging import get_logger

logger = get_logger("workflow")

from PySide6.QtCore import QObject, Signal, QTimer

from ..utils.error_handling import handle_errors, error_context, ErrorHandler
from ..core.unified_config_manager import UnifiedConfigurationManager
from ..core.state_store import StateStore
from ..core.resource_manager import resource_manager


class WorkflowType(Enum):
    """Types of workflows supported"""
    IMAGE_GENERATION = "image_generation"
    MODEL_3D_GENERATION = "model_3d_generation"
    TEXTURE_GENERATION = "texture_generation"
    CINEMA4D_AUTOMATION = "cinema4d_automation"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    PREPARING = "preparing"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowParameters:
    """Structured workflow parameters"""
    workflow_type: WorkflowType
    workflow_file: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dynamic_parameters: Dict[str, Any] = field(default_factory=dict)
    batch_size: int = 1
    seed: Optional[int] = None
    use_random_seed: bool = True
    
    def merge_parameters(self) -> Dict[str, Any]:
        """Merge static and dynamic parameters"""
        merged = self.parameters.copy()
        merged.update(self.dynamic_parameters)
        return merged


@dataclass
class WorkflowExecution:
    """Workflow execution context"""
    execution_id: str
    workflow_type: WorkflowType
    parameters: WorkflowParameters
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    progress_percentage: int = 0
    current_step: str = ""
    prompt_id: Optional[str] = None
    error_message: Optional[str] = None
    results: List[str] = field(default_factory=list)
    
    def get_duration(self) -> float:
        """Get execution duration"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def is_completed(self) -> bool:
        """Check if execution is completed"""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]


class WorkflowMonitor(QObject):
    """Monitors workflow execution progress"""
    
    progress_updated = Signal(str, int, str)  # execution_id, percentage, step
    status_changed = Signal(str, str)  # execution_id, status
    completed = Signal(str, bool, list)  # execution_id, success, results
    
    def __init__(self, integration_hub):
        super().__init__()
        self.integration_hub = integration_hub
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.error_handler = ErrorHandler("workflow_monitor")
    
    @handle_errors("workflow_monitor", "start_monitoring")
    async def start_monitoring(self, execution: WorkflowExecution):
        """Start monitoring workflow execution"""
        if not execution.prompt_id:
            logger.warning(f"No prompt ID for execution {execution.execution_id}")
            return
        
        # Cancel existing monitoring for this execution
        if execution.execution_id in self.monitoring_tasks:
            self.monitoring_tasks[execution.execution_id].cancel()
        
        # Start new monitoring task
        task = asyncio.create_task(
            self._monitor_workflow_completion(execution)
        )
        self.monitoring_tasks[execution.execution_id] = task
        
        # Register task with resource manager
        resource_manager.register_task(
            f"workflow_monitor_{execution.execution_id}",
            task
        )
    
    async def _monitor_workflow_completion(self, execution: WorkflowExecution):
        """Monitor workflow completion using ComfyUI history API"""
        try:
            max_retries = 30  # 5 minutes with 10-second intervals
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Check ComfyUI history for completion
                    history = await self.integration_hub.get_comfyui_history()
                    
                    if execution.prompt_id in history:
                        prompt_info = history[execution.prompt_id]
                        
                        if "status" in prompt_info:
                            status_info = prompt_info["status"]
                            
                            if status_info.get("completed", False):
                                # Workflow completed successfully
                                await self._handle_completion(execution, prompt_info)
                                return
                            
                            elif "exception" in status_info:
                                # Workflow failed
                                error_msg = status_info["exception"].get("message", "Unknown error")
                                await self._handle_failure(execution, error_msg)
                                return
                        
                        # Update progress if available
                        if "progress" in prompt_info:
                            progress = min(90, prompt_info["progress"] * 90)  # Cap at 90% until completion
                            self._update_progress(execution, int(progress), "Processing...")
                    
                    # Wait before next check
                    await asyncio.sleep(10)
                    retry_count += 1
                    
                except Exception as e:
                    logger.warning(f"Monitoring check failed: {e}")
                    retry_count += 1
                    await asyncio.sleep(10)
            
            # Timeout reached
            await self._handle_timeout(execution)
            
        except asyncio.CancelledError:
            logger.debug(f"Monitoring cancelled for execution {execution.execution_id}")
        except Exception as e:
            self.error_handler.handle_error(
                e, "monitor_workflow_completion",
                context={"execution_id": execution.execution_id}
            )
            await self._handle_failure(execution, str(e))
        finally:
            # Cleanup
            if execution.execution_id in self.monitoring_tasks:
                del self.monitoring_tasks[execution.execution_id]
    
    async def _handle_completion(self, execution: WorkflowExecution, prompt_info: Dict[str, Any]):
        """Handle successful workflow completion"""
        try:
            # Download results
            results = await self._download_workflow_results(execution, prompt_info)
            execution.results = results
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = time.time()
            execution.progress_percentage = 100
            
            self.progress_updated.emit(execution.execution_id, 100, "Completed")
            self.status_changed.emit(execution.execution_id, WorkflowStatus.COMPLETED.value)
            self.completed.emit(execution.execution_id, True, results)
            
            logger.info(f"Workflow completed: {execution.execution_id} ({len(results)} results)")
            
        except Exception as e:
            await self._handle_failure(execution, f"Result processing failed: {e}")
    
    async def _handle_failure(self, execution: WorkflowExecution, error_message: str):
        """Handle workflow failure"""
        execution.status = WorkflowStatus.FAILED
        execution.error_message = error_message
        execution.end_time = time.time()
        
        self.status_changed.emit(execution.execution_id, WorkflowStatus.FAILED.value)
        self.completed.emit(execution.execution_id, False, [])
        
        logger.error(f"Workflow failed: {execution.execution_id} - {error_message}")
    
    async def _handle_timeout(self, execution: WorkflowExecution):
        """Handle workflow timeout"""
        execution.status = WorkflowStatus.FAILED
        execution.error_message = "Workflow execution timeout"
        execution.end_time = time.time()
        
        self.status_changed.emit(execution.execution_id, WorkflowStatus.FAILED.value)
        self.completed.emit(execution.execution_id, False, [])
        
        logger.warning(f"Workflow timeout: {execution.execution_id}")
    
    def _update_progress(self, execution: WorkflowExecution, percentage: int, step: str):
        """Update workflow progress"""
        execution.progress_percentage = percentage
        execution.current_step = step
        self.progress_updated.emit(execution.execution_id, percentage, step)
    
    async def _download_workflow_results(self, execution: WorkflowExecution, prompt_info: Dict[str, Any]) -> List[str]:
        """Download workflow results from ComfyUI"""
        results = []
        
        try:
            outputs = prompt_info.get("outputs", {})
            
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for image_info in node_output["images"]:
                        filename = image_info.get("filename")
                        if filename:
                            # Download image
                            result_path = await self.integration_hub.download_comfyui_image(
                                filename, 
                                execution.workflow_type.value
                            )
                            if result_path:
                                results.append(str(result_path))
                
                if "models" in node_output:
                    for model_info in node_output["models"]:
                        filename = model_info.get("filename")
                        if filename:
                            # Download model
                            result_path = await self.integration_hub.download_comfyui_model(
                                filename, 
                                execution.workflow_type.value
                            )
                            if result_path:
                                results.append(str(result_path))
            
        except Exception as e:
            logger.error(f"Failed to download results: {e}")
        
        return results
    
    def cancel_monitoring(self, execution_id: str):
        """Cancel monitoring for specific execution"""
        if execution_id in self.monitoring_tasks:
            self.monitoring_tasks[execution_id].cancel()
            del self.monitoring_tasks[execution_id]
    
    def cancel_all_monitoring(self):
        """Cancel all monitoring tasks"""
        for task in self.monitoring_tasks.values():
            task.cancel()
        self.monitoring_tasks.clear()


class ParameterCollector:
    """Collects and validates workflow parameters"""
    
    def __init__(self, config_manager: UnifiedConfigurationManager):
        self.config = config_manager
        self.error_handler = ErrorHandler("parameter_collector")
    
    @handle_errors("parameter_collector", "collect_parameters")
    def collect_dynamic_parameters(self, workflow: Dict[str, Any], ui_widgets: Dict[str, Any]) -> Dict[str, Any]:
        """Collect dynamic parameters from UI widgets"""
        with error_context("parameter_collector", "collect_parameters"):
            dynamic_params = {}
            
            try:
                for node_id, node_data in workflow.items():
                    if not isinstance(node_data, dict):
                        continue
                    
                    inputs = node_data.get("inputs", {})
                    
                    for input_name, input_value in inputs.items():
                        # Check if this input has a corresponding UI widget
                        widget_key = f"{node_id}_{input_name}"
                        
                        if widget_key in ui_widgets:
                            widget = ui_widgets[widget_key]
                            
                            # Extract value based on widget type
                            try:
                                if hasattr(widget, 'value'):
                                    dynamic_params[widget_key] = widget.value()
                                elif hasattr(widget, 'text'):
                                    dynamic_params[widget_key] = widget.text()
                                elif hasattr(widget, 'currentText'):
                                    dynamic_params[widget_key] = widget.currentText()
                                elif hasattr(widget, 'isChecked'):
                                    dynamic_params[widget_key] = widget.isChecked()
                                else:
                                    logger.debug(f"Unknown widget type for {widget_key}")
                            
                            except Exception as e:
                                logger.warning(f"Failed to get value from widget {widget_key}: {e}")
                
                logger.debug(f"Collected {len(dynamic_params)} dynamic parameters")
                return dynamic_params
                
            except Exception as e:
                self.error_handler.handle_error(
                    e, "collect_dynamic_parameters",
                    context={"workflow_nodes": len(workflow), "ui_widgets": len(ui_widgets)}
                )
                return {}
    
    def inject_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Inject parameters into workflow"""
        modified_workflow = workflow.copy()
        
        try:
            for param_key, param_value in parameters.items():
                # Parse parameter key (format: node_id_input_name)
                parts = param_key.split('_', 1)
                if len(parts) == 2:
                    node_id, input_name = parts
                    
                    if node_id in modified_workflow:
                        node = modified_workflow[node_id]
                        if "inputs" in node:
                            node["inputs"][input_name] = param_value
                            logger.debug(f"Injected parameter: {param_key} = {param_value}")
            
        except Exception as e:
            logger.error(f"Parameter injection failed: {e}")
        
        return modified_workflow
    
    def validate_parameters(self, parameters: WorkflowParameters) -> Tuple[bool, List[str]]:
        """Validate workflow parameters"""
        errors = []
        
        # Check required fields
        if not parameters.workflow_file:
            errors.append("Workflow file not specified")
        
        if parameters.batch_size <= 0:
            errors.append("Batch size must be positive")
        
        # Check workflow file exists
        workflow_path = Path(parameters.workflow_file)
        if not workflow_path.exists():
            errors.append(f"Workflow file not found: {workflow_path}")
        
        # Validate specific parameters based on workflow type
        if parameters.workflow_type == WorkflowType.IMAGE_GENERATION:
            self._validate_image_parameters(parameters, errors)
        elif parameters.workflow_type == WorkflowType.MODEL_3D_GENERATION:
            self._validate_3d_parameters(parameters, errors)
        elif parameters.workflow_type == WorkflowType.TEXTURE_GENERATION:
            self._validate_texture_parameters(parameters, errors)
        
        return len(errors) == 0, errors
    
    def _validate_image_parameters(self, parameters: WorkflowParameters, errors: List[str]):
        """Validate image generation parameters"""
        merged = parameters.merge_parameters()
        
        # Check resolution
        if "resolution" in merged:
            resolution = merged["resolution"]
            if isinstance(resolution, list) and len(resolution) == 2:
                width, height = resolution
                if width <= 0 or height <= 0:
                    errors.append("Resolution values must be positive")
                if width > 4096 or height > 4096:
                    errors.append("Resolution values too large (max 4096)")
            else:
                errors.append("Invalid resolution format")
        
        # Check sampling steps
        if "sampling_steps" in merged:
            steps = merged["sampling_steps"]
            if not isinstance(steps, int) or steps <= 0 or steps > 100:
                errors.append("Sampling steps must be between 1 and 100")
    
    def _validate_3d_parameters(self, parameters: WorkflowParameters, errors: List[str]):
        """Validate 3D generation parameters"""
        merged = parameters.merge_parameters()
        
        # Check mesh density
        if "mesh_density" in merged:
            density = merged["mesh_density"]
            if density not in ["low", "medium", "high"]:
                errors.append("Mesh density must be 'low', 'medium', or 'high'")
    
    def _validate_texture_parameters(self, parameters: WorkflowParameters, errors: List[str]):
        """Validate texture generation parameters"""
        merged = parameters.merge_parameters()
        
        # Check texture resolution
        if "texture_resolution" in merged:
            resolution = merged["texture_resolution"]
            if not isinstance(resolution, int) or resolution <= 0:
                errors.append("Texture resolution must be positive integer")


class WorkflowEngine(QObject):
    """
    Centralized workflow execution engine
    
    Extracted from monolithic application to handle complete workflow lifecycle
    with proper error handling, monitoring, and state management.
    """
    
    # Workflow execution signals
    execution_started = Signal(str, str)  # execution_id, workflow_type
    execution_progress = Signal(str, int, str)  # execution_id, percentage, step
    execution_completed = Signal(str, bool, list)  # execution_id, success, results
    execution_failed = Signal(str, str)  # execution_id, error_message
    
    def __init__(self, 
                 config_manager: UnifiedConfigurationManager,
                 state_store: StateStore,
                 integration_hub):
        super().__init__()
        self.config = config_manager
        self.state_store = state_store
        self.integration_hub = integration_hub
        
        # Components
        self.parameter_collector = ParameterCollector(config_manager)
        self.workflow_monitor = WorkflowMonitor(integration_hub)
        
        # Execution tracking
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []
        
        # Error handling
        self.error_handler = ErrorHandler("workflow_engine")
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.workflow_monitor.progress_updated.connect(self._on_progress_updated)
        self.workflow_monitor.status_changed.connect(self._on_status_changed)
        self.workflow_monitor.completed.connect(self._on_execution_completed)
    
    @handle_errors("workflow_engine", "execute_workflow")
    async def execute_workflow(self, 
                             workflow_type: WorkflowType,
                             workflow_file: str,
                             parameters: Dict[str, Any] = None,
                             ui_widgets: Dict[str, Any] = None) -> str:
        """Execute workflow and return execution ID"""
        
        execution_id = str(uuid.uuid4())
        
        with error_context("workflow_engine", "execute_workflow",
                          execution_id=execution_id,
                          workflow_type=workflow_type.value):
            
            try:
                # Create workflow parameters
                workflow_params = WorkflowParameters(
                    workflow_type=workflow_type,
                    workflow_file=workflow_file,
                    parameters=parameters or {},
                    batch_size=1
                )
                
                # Collect dynamic parameters from UI
                if ui_widgets:
                    # Load workflow file to get structure
                    workflow_path = Path(workflow_file)
                    if workflow_path.exists():
                        with open(workflow_path, 'r') as f:
                            workflow_data = json.load(f)
                        
                        dynamic_params = self.parameter_collector.collect_dynamic_parameters(
                            workflow_data, ui_widgets
                        )
                        workflow_params.dynamic_parameters = dynamic_params
                
                # Validate parameters
                is_valid, validation_errors = self.parameter_collector.validate_parameters(workflow_params)
                if not is_valid:
                    error_msg = "; ".join(validation_errors)
                    logger.error(f"Parameter validation failed: {error_msg}")
                    self.execution_failed.emit(execution_id, error_msg)
                    return execution_id
                
                # Create execution context
                execution = WorkflowExecution(
                    execution_id=execution_id,
                    workflow_type=workflow_type,
                    parameters=workflow_params,
                    status=WorkflowStatus.PREPARING
                )
                
                # Store execution
                self.active_executions[execution_id] = execution
                
                # Update state store
                self.state_store.start_workflow_execution(workflow_file, workflow_params.merge_parameters())
                
                # Start execution
                await self._start_workflow_execution(execution)
                
                return execution_id
                
            except Exception as e:
                self.error_handler.handle_error(
                    e, "execute_workflow",
                    context={"execution_id": execution_id, "workflow_type": workflow_type.value}
                )
                self.execution_failed.emit(execution_id, str(e))
                return execution_id
    
    async def _start_workflow_execution(self, execution: WorkflowExecution):
        """Start workflow execution process"""
        try:
            execution.status = WorkflowStatus.EXECUTING
            execution.current_step = "Loading workflow"
            
            # Load and prepare workflow
            workflow_path = Path(execution.parameters.workflow_file)
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            
            # Inject parameters
            final_workflow = self.parameter_collector.inject_parameters(
                workflow_data, execution.parameters.merge_parameters()
            )
            
            execution.current_step = "Submitting to ComfyUI"
            
            # Submit to ComfyUI
            prompt_id = await self.integration_hub.submit_comfyui_workflow(
                final_workflow, execution.parameters.batch_size
            )
            
            if prompt_id:
                execution.prompt_id = prompt_id
                execution.status = WorkflowStatus.MONITORING
                execution.current_step = "Monitoring execution"
                
                # Start monitoring
                await self.workflow_monitor.start_monitoring(execution)
                
                # Emit started signal
                self.execution_started.emit(execution.execution_id, execution.workflow_type.value)
                
                logger.info(f"Workflow execution started: {execution.execution_id}")
            else:
                await self._handle_execution_failure(execution, "Failed to submit workflow to ComfyUI")
                
        except Exception as e:
            await self._handle_execution_failure(execution, str(e))
    
    async def _handle_execution_failure(self, execution: WorkflowExecution, error_message: str):
        """Handle execution failure"""
        execution.status = WorkflowStatus.FAILED
        execution.error_message = error_message
        execution.end_time = time.time()
        
        # Update state store
        self.state_store.complete_workflow_execution(success=False)
        
        # Move to history
        self._move_to_history(execution)
        
        # Emit signals
        self.execution_failed.emit(execution.execution_id, error_message)
        
        logger.error(f"Workflow execution failed: {execution.execution_id} - {error_message}")
    
    def _on_progress_updated(self, execution_id: str, percentage: int, step: str):
        """Handle progress update from monitor"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.progress_percentage = percentage
            execution.current_step = step
            
            # Update state store
            self.state_store.update_workflow_progress(percentage, step)
            
            # Emit signal
            self.execution_progress.emit(execution_id, percentage, step)
    
    def _on_status_changed(self, execution_id: str, status: str):
        """Handle status change from monitor"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus(status)
    
    def _on_execution_completed(self, execution_id: str, success: bool, results: List[str]):
        """Handle execution completion from monitor"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.results = results
            execution.end_time = time.time()
            
            if success:
                execution.status = WorkflowStatus.COMPLETED
                
                # Add results to session state
                for result_path in results:
                    if execution.workflow_type == WorkflowType.IMAGE_GENERATION:
                        self.state_store.add_generated_item("image", result_path)
                    elif execution.workflow_type == WorkflowType.MODEL_3D_GENERATION:
                        self.state_store.add_generated_item("model", result_path)
                    elif execution.workflow_type == WorkflowType.TEXTURE_GENERATION:
                        self.state_store.add_generated_item("texture", result_path)
                
                # Update state store
                self.state_store.complete_workflow_execution(success=True)
                
                logger.info(f"Workflow execution completed: {execution_id} ({len(results)} results)")
            else:
                execution.status = WorkflowStatus.FAILED
                self.state_store.complete_workflow_execution(success=False)
            
            # Move to history
            self._move_to_history(execution)
            
            # Emit completion signal
            self.execution_completed.emit(execution_id, success, results)
    
    def _move_to_history(self, execution: WorkflowExecution):
        """Move execution to history"""
        if execution.execution_id in self.active_executions:
            del self.active_executions[execution.execution_id]
        
        self.execution_history.append(execution)
        
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    # Public Interface Methods
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel active execution"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = time.time()
            
            # Cancel monitoring
            self.workflow_monitor.cancel_monitoring(execution_id)
            
            # Move to history
            self._move_to_history(execution)
            
            logger.info(f"Workflow execution cancelled: {execution_id}")
            return True
        
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution status"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # Check history
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return execution
        
        return None
    
    def get_active_executions(self) -> List[WorkflowExecution]:
        """Get all active executions"""
        return list(self.active_executions.values())
    
    def get_execution_history(self, limit: int = 10) -> List[WorkflowExecution]:
        """Get execution history"""
        return self.execution_history[-limit:] if limit > 0 else self.execution_history
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        total_executions = len(self.execution_history)
        successful = len([e for e in self.execution_history if e.status == WorkflowStatus.COMPLETED])
        failed = len([e for e in self.execution_history if e.status == WorkflowStatus.FAILED])
        
        avg_duration = 0
        if self.execution_history:
            durations = [e.get_duration() for e in self.execution_history if e.end_time]
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_executions": total_executions,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
            "average_duration": avg_duration,
            "active_executions": len(self.active_executions)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        # Cancel all monitoring
        self.workflow_monitor.cancel_all_monitoring()
        
        # Cancel active executions
        for execution_id in list(self.active_executions.keys()):
            self.cancel_execution(execution_id)
        
        logger.info("Workflow engine cleanup completed")