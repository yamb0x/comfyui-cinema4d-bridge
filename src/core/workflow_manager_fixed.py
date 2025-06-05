"""
Workflow management for ComfyUI JSON workflows
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from copy import deepcopy

from loguru import logger
from jsonschema import validate, ValidationError

from utils.logger import LoggerMixin


class WorkflowManager(LoggerMixin):
    """Manage ComfyUI workflow JSON files"""
    
    def __init__(self, workflows_dir: Path):
        self.workflows_dir = workflows_dir
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self._workflow_cache: Dict[str, Dict[str, Any]] = {}
        self._backup_dir = self.workflows_dir / "backups"
        self._backup_dir.mkdir(exist_ok=True)
        
    def load_workflow(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Load workflow from file"""
        workflow_path = self.workflows_dir / workflow_name
        
        if not workflow_path.exists():
            self.logger.error(f"Workflow not found: {workflow_name}")
            return None
        
        try:
            with open(workflow_path, "r") as f:
                workflow = json.load(f)
            
            self._workflow_cache[workflow_name] = workflow
            self.logger.info(f"Loaded workflow: {workflow_name}")
            return deepcopy(workflow)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in workflow {workflow_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load workflow {workflow_name}: {e}")
            return None
    
    def save_workflow(self, workflow_name: str, workflow: Dict[str, Any],
                     create_backup: bool = True) -> bool:
        """Save workflow to file"""
        workflow_path = self.workflows_dir / workflow_name
        
        try:
            # Create backup if requested and file exists
            if create_backup and workflow_path.exists():
                self._create_backup(workflow_name)
            
            # Save workflow
            with open(workflow_path, "w") as f:
                json.dump(workflow, f, indent=2)
            
            self._workflow_cache[workflow_name] = deepcopy(workflow)
            self.logger.info(f"Saved workflow: {workflow_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow {workflow_name}: {e}")
            return False
    
    def _create_backup(self, workflow_name: str):
        """Create backup of workflow file"""
        source = self.workflows_dir / workflow_name
        if not source.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_{timestamp}{source.suffix}"
        backup_path = self._backup_dir / backup_name
        
        shutil.copy2(source, backup_path)
        self.logger.debug(f"Created backup: {backup_name}")
    
    def list_workflows(self) -> List[str]:
        """List available workflows"""
        workflows = []
        for path in self.workflows_dir.glob("*.json"):
            if path.is_file() and path.parent == self.workflows_dir:
                workflows.append(path.name)
        return sorted(workflows)
    
    def inject_parameters_comfyui(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Inject parameters into ComfyUI workflow format"""
        workflow_copy = deepcopy(workflow)
        
        # Handle ComfyUI workflow format with nodes array
        if "nodes" in workflow_copy:
            nodes = workflow_copy["nodes"]
        else:
            return workflow_copy
        
        for node in nodes:
            if not isinstance(node, dict) or "type" not in node:
                continue
                
            node_type = node["type"]
            node_id = node.get("id", "unknown")
            
            # Inject positive prompt (Node 12)
            if node_type == "CLIPTextEncode" and "Positive" in node.get("title", ""):
                if "positive_prompt" in params:
                    node["widgets_values"] = [params["positive_prompt"]]
                    self.logger.debug(f"Injected positive prompt into node {node_id}")
            
            # Inject negative prompt (Node 13) 
            elif node_type == "CLIPTextEncode" and "Negative" in node.get("title", ""):
                if "negative_prompt" in params:
                    node["widgets_values"] = [params["negative_prompt"]]
                    self.logger.debug(f"Injected negative prompt into node {node_id}")
            
            # Inject image dimensions and batch (Node 8 - EmptySD3LatentImage)
            elif node_type == "EmptySD3LatentImage":
                widgets = node.get("widgets_values", [512, 512, 1])
                if "width" in params:
                    widgets[0] = params["width"]
                if "height" in params:
                    widgets[1] = params["height"]
                if "batch_size" in params:
                    widgets[2] = params["batch_size"]
                node["widgets_values"] = widgets
                self.logger.debug(f"Injected dimensions/batch into node {node_id}: {widgets}")
            
            # Inject KSampler parameters (Node 10)
            elif node_type == "KSampler":
                widgets = node.get("widgets_values", [0, "increment", 20, 1, "euler", "simple", 1])
                if "seed" in params and params["seed"] >= 0:
                    widgets[0] = params["seed"]
                if "steps" in params:
                    widgets[2] = params["steps"]
                if "cfg" in params:
                    widgets[3] = params["cfg"]
                if "sampler_name" in params:
                    widgets[4] = params["sampler_name"]
                if "scheduler" in params:
                    widgets[5] = params["scheduler"]
                node["widgets_values"] = widgets
                self.logger.debug(f"Injected KSampler params into node {node_id}: {widgets}")
            
            # Inject checkpoint (Node 5)
            elif node_type == "CheckpointLoaderSimple":
                if "checkpoint" in params:
                    node["widgets_values"] = [params["checkpoint"]]
                    self.logger.debug(f"Injected checkpoint into node {node_id}")
            
            # Handle LoRA nodes (Nodes 6, 7, 3)
            elif node_type == "LoraLoader":
                self._inject_lora_params(node, params, node_id)
        
        return workflow_copy
    
    def _inject_lora_params(self, node: Dict[str, Any], params: Dict[str, Any], node_id: str):
        """Inject LoRA parameters with bypass functionality"""
        widgets = node.get("widgets_values", ["", 1.0, 1.0])
        
        # Determine which LoRA this is based on current model
        current_lora = widgets[0] if widgets else ""
        
        # LoRA 1 controls (deep_sea_creatures_cts.safetensors)
        if "deep_sea_creatures_cts" in current_lora:
            if "lora1_model" in params:
                widgets[0] = params["lora1_model"]
            if "lora1_strength" in params:
                widgets[1] = params["lora1_strength"]
                widgets[2] = params["lora1_strength"]
            if "lora1_active" in params and not params["lora1_active"]:
                node["mode"] = 4  # Bypass mode in ComfyUI
            else:
                node["mode"] = 0  # Active mode
        
        # LoRA 2 controls (aidmaFLUXpro1.1)
        elif "aidmaFLUXpro1.1" in current_lora:
            if "lora2_model" in params:
                widgets[0] = params["lora2_model"]
            if "lora2_strength" in params:
                widgets[1] = params["lora2_strength"]
                widgets[2] = params["lora2_strength"]
            if "lora2_active" in params and not params["lora2_active"]:
                node["mode"] = 4  # Bypass mode
            else:
                node["mode"] = 0  # Active mode
        
        node["widgets_values"] = widgets
        self.logger.debug(f"Injected LoRA params into node {node_id}: {widgets}, mode: {node.get('mode', 0)}")

    def inject_parameters(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to ComfyUI format"""
        return self.inject_parameters_comfyui(workflow, params)