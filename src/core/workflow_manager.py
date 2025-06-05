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
        
        # Check if this is already API format (dict with string keys like "5", "10", etc.)
        if self._is_api_format(workflow_copy):
            return self._inject_params_api_format(workflow_copy, params)
        
        # Handle UI format (ComfyUI export format with nodes array)
        if "nodes" in workflow_copy and isinstance(workflow_copy["nodes"], list):
            # Inject parameters into UI format first
            ui_workflow_with_params = self._inject_params_ui_format(workflow_copy, params)
            # Then convert to API format for ComfyUI execution
            api_workflow = self._convert_ui_to_api_format(ui_workflow_with_params)
            self.logger.info(f"Converted UI workflow to API format with {len(api_workflow)} nodes")
            return api_workflow
        
        # Fallback: Convert UI format to API format if needed
        if "nodes" in workflow_copy and isinstance(workflow_copy["nodes"], list):
            workflow_copy = self._convert_ui_to_api_format(workflow_copy)
        
        # Handle ComfyUI API format (dict of nodes)
        if isinstance(workflow_copy, dict):
            nodes = workflow_copy
        else:
            return workflow_copy
        
        for node_id, node in nodes.items():
            if not isinstance(node, dict) or "class_type" not in node:
                continue
                
            node_type = node["class_type"]
            inputs = node.get("inputs", {})
            
            # Handle parameter injection based on node type
            if node_type == "CLIPTextEncode":
                # Check node id for positive/negative prompt
                if node_id == "12":  # Positive prompt node
                    if "positive_prompt" in params:
                        inputs["text"] = params["positive_prompt"]
                        self.logger.debug(f"Injected positive prompt into node {node_id}")
                elif node_id == "13":  # Negative prompt node
                    if "negative_prompt" in params:
                        inputs["text"] = params["negative_prompt"]
                        self.logger.debug(f"Injected negative prompt into node {node_id}")
            
            # Inject image dimensions and batch (Node 8 - EmptySD3LatentImage)
            elif node_type == "EmptySD3LatentImage" and node_id == "8":
                if "width" in params:
                    inputs["width"] = params["width"]
                if "height" in params:
                    inputs["height"] = params["height"]
                if "batch_size" in params:
                    inputs["batch_size"] = params["batch_size"]
                self.logger.debug(f"Injected dimensions/batch into node {node_id}")
            
            # Inject KSampler parameters (Node 10)
            elif node_type == "KSampler" and node_id == "10":
                if "seed" in params and params["seed"] >= 0:
                    inputs["seed"] = params["seed"]
                if "steps" in params:
                    inputs["steps"] = params["steps"]
                if "cfg" in params:
                    inputs["cfg"] = params["cfg"]
                if "sampler_name" in params:
                    inputs["sampler_name"] = params["sampler_name"]
                if "scheduler" in params:
                    inputs["scheduler"] = params["scheduler"]
                self.logger.debug(f"Injected sampler params into node {node_id}")
            
            # Inject checkpoint (Node 5)
            elif node_type == "CheckpointLoaderSimple" and node_id == "5":
                if "checkpoint" in params:
                    inputs["ckpt_name"] = params["checkpoint"]
                    self.logger.debug(f"Injected checkpoint into node {node_id}")
            
            # Handle LoRA nodes (Nodes 6, 7, 3) - Skip for now, they're complex
            elif node_type == "LoraLoader":
                self.logger.debug(f"Skipping LoRA injection for node {node_id} - complex connections")
        
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

    def _convert_ui_to_api_format(self, ui_workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ComfyUI UI format to API format"""
        api_workflow = {}
        
        # First pass: Create basic nodes with widget values
        for node in ui_workflow.get("nodes", []):
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "")
            
            # Skip Note nodes - they're UI-only and not executable
            if node_type == "Note":
                self.logger.debug(f"Skipping Note node {node_id} in API conversion")
                continue
            
            # Create API format node
            api_node = {
                "class_type": node_type,
                "inputs": {}
            }
            
            # Convert widgets_values to inputs based on node type
            widgets = node.get("widgets_values", [])
            
            if node_type == "CLIPTextEncode" and widgets:
                api_node["inputs"]["text"] = widgets[0] if widgets else ""
            elif node_type == "EmptySD3LatentImage" and len(widgets) >= 3:
                api_node["inputs"]["width"] = widgets[0]
                api_node["inputs"]["height"] = widgets[1] 
                api_node["inputs"]["batch_size"] = widgets[2]
            elif node_type == "KSampler" and len(widgets) >= 7:
                api_node["inputs"]["seed"] = widgets[0]
                api_node["inputs"]["steps"] = widgets[2]
                api_node["inputs"]["cfg"] = widgets[3]
                api_node["inputs"]["sampler_name"] = widgets[4]
                api_node["inputs"]["scheduler"] = widgets[5]
                api_node["inputs"]["denoise"] = 1.0  # Add missing denoise parameter
            elif node_type == "CheckpointLoaderSimple" and widgets:
                api_node["inputs"]["ckpt_name"] = widgets[0] if widgets else "flux1-dev-fp8.safetensors"
            elif node_type == "LoraLoader" and len(widgets) >= 3:
                api_node["inputs"]["lora_name"] = widgets[0] if widgets[0] else "None"
                api_node["inputs"]["strength_model"] = widgets[1] if len(widgets) > 1 else 1.0
                api_node["inputs"]["strength_clip"] = widgets[2] if len(widgets) > 2 else 1.0
            elif node_type == "Image Save" and widgets:
                # Map widgets_values to Image Save node inputs
                # Based on actual UI workflow: [output_path, filename_prefix, filename_delimiter, 
                # filename_number_start, overwrite_mode, extension, quality, dpi, optimize_image,
                # lossless_webp, embed_workflow, show_previews, show_history, show_history_by_prefix,
                # filename_number_padding]
                if len(widgets) >= 15:
                    api_node["inputs"]["output_path"] = widgets[0]
                    api_node["inputs"]["filename_prefix"] = widgets[1] 
                    api_node["inputs"]["filename_delimiter"] = widgets[2]
                    # filename_number_start expects "true"/"false" strings, not int
                    start_val = widgets[3]
                    if isinstance(start_val, int) and start_val > 0:
                        api_node["inputs"]["filename_number_start"] = "true"  # Use numbering
                    else:
                        api_node["inputs"]["filename_number_start"] = "false"  # No numbering
                    # Keep as strings - ComfyUI expects "true"/"false" strings  
                    api_node["inputs"]["overwrite_mode"] = widgets[4]  # "false" or "prefix_as_filename"
                    api_node["inputs"]["extension"] = widgets[5]
                    api_node["inputs"]["quality"] = min(int(widgets[6]), 100)  # Max 100
                    api_node["inputs"]["dpi"] = int(widgets[7])
                    api_node["inputs"]["optimize_image"] = widgets[8]  # "true"/"false" string
                    api_node["inputs"]["lossless_webp"] = widgets[9]   # "true"/"false" string
                    api_node["inputs"]["embed_workflow"] = widgets[10] # "true"/"false" string
                    api_node["inputs"]["show_previews"] = widgets[11]  # "true"/"false" string
                    api_node["inputs"]["show_history"] = widgets[12]   # "true"/"false" string
                    api_node["inputs"]["show_history_by_prefix"] = widgets[13] # "true"/"false" string
                    # Handle filename_number_padding - convert false to default int value
                    padding_val = widgets[14]
                    if isinstance(padding_val, str) and padding_val.lower() == "false":
                        api_node["inputs"]["filename_number_padding"] = 4  # Default value
                    else:
                        api_node["inputs"]["filename_number_padding"] = int(padding_val)
            
            api_workflow[node_id] = api_node
        
        # Second pass: Add connections based on links
        link_map = self._build_link_map(ui_workflow)
        
        for node in ui_workflow.get("nodes", []):
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "")
            
            # Skip Note nodes here too
            if node_type == "Note":
                continue
                
            api_node = api_workflow[node_id]
            
            # Add input connections
            for input_def in node.get("inputs", []):
                input_name = input_def.get("name", "")
                if "link" in input_def:
                    link_id = input_def["link"]
                    if link_id in link_map:
                        source_node_id, output_index = link_map[link_id]
                        api_node["inputs"][input_name] = [str(source_node_id), output_index]
        
        self.logger.debug(f"Converted UI workflow to API format with {len(api_workflow)} nodes")
        return api_workflow
    
    def _build_link_map(self, ui_workflow: Dict[str, Any]) -> Dict[int, tuple]:
        """Build a map of link_id -> (source_node_id, output_index)"""
        link_map = {}
        
        for node in ui_workflow.get("nodes", []):
            node_id = str(node.get("id", ""))
            for output_index, output in enumerate(node.get("outputs", [])):
                if output.get("links"):
                    for link_id in output["links"]:
                        link_map[link_id] = (node_id, output_index)
        
        return link_map
    
    def _find_source_node(self, ui_workflow: Dict[str, Any], link_id: int) -> Optional[str]:
        """Find the source node for a given link ID"""
        for node in ui_workflow.get("nodes", []):
            for output in node.get("outputs", []):
                if output.get("links") and link_id in output["links"]:
                    return str(node.get("id", ""))
        return None

    def _is_api_format(self, workflow: Dict[str, Any]) -> bool:
        """Check if workflow is in API format (dict of nodes with string IDs)"""
        if not isinstance(workflow, dict):
            return False
        # API format has string keys and class_type properties
        for key, value in workflow.items():
            if isinstance(value, dict) and "class_type" in value:
                return True
        return False
    
    def _inject_params_api_format(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Inject parameters into API format workflow"""
        workflow_copy = deepcopy(workflow)
        
        # Node 12: Positive prompt
        if "12" in workflow_copy and "positive_prompt" in params:
            workflow_copy["12"]["inputs"]["text"] = params["positive_prompt"]
            self.logger.debug(f"Injected positive prompt")
        
        # Node 13: Negative prompt  
        if "13" in workflow_copy and "negative_prompt" in params:
            workflow_copy["13"]["inputs"]["text"] = params["negative_prompt"]
            self.logger.debug(f"Injected negative prompt")
        
        # Node 8: Dimensions and batch
        if "8" in workflow_copy:
            if "width" in params:
                workflow_copy["8"]["inputs"]["width"] = params["width"]
            if "height" in params:
                workflow_copy["8"]["inputs"]["height"] = params["height"]
            if "batch_size" in params:
                workflow_copy["8"]["inputs"]["batch_size"] = params["batch_size"]
            self.logger.debug(f"Injected dimensions/batch")
        
        # Node 10: Sampler parameters
        if "10" in workflow_copy:
            if "seed" in params and params["seed"] >= 0:
                workflow_copy["10"]["inputs"]["seed"] = params["seed"]
            if "steps" in params:
                workflow_copy["10"]["inputs"]["steps"] = params["steps"]
            if "cfg" in params:
                cfg_value = params["cfg"]
                workflow_copy["10"]["inputs"]["cfg"] = cfg_value
                self.logger.info(f"Injecting CFG value: {cfg_value}")
            if "sampler_name" in params:
                sampler_value = params["sampler_name"]
                workflow_copy["10"]["inputs"]["sampler_name"] = sampler_value
                self.logger.info(f"Injecting Sampler: {sampler_value}")
            if "scheduler" in params:
                scheduler_value = params["scheduler"]
                workflow_copy["10"]["inputs"]["scheduler"] = scheduler_value
                self.logger.info(f"Injecting Scheduler: {scheduler_value}")
            if "steps" in params:
                steps_value = params["steps"]
                self.logger.info(f"Injecting Steps: {steps_value}")
            self.logger.info(f"KSampler node updated with all parameters")
        
        # Node 5: Checkpoint (only if valid)
        if "5" in workflow_copy and "checkpoint" in params:
            checkpoint = params["checkpoint"]
            # Only inject if it's not empty and not a placeholder
            if checkpoint and checkpoint.strip() and not checkpoint.startswith("Select"):
                workflow_copy["5"]["inputs"]["ckpt_name"] = checkpoint
                self.logger.debug(f"Injected checkpoint: {checkpoint}")
            else:
                self.logger.debug(f"Skipping invalid checkpoint: '{checkpoint}', keeping default")
        
        return workflow_copy
    
    def _inject_params_ui_format(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Inject parameters into UI format workflow (with nodes array)"""
        workflow_copy = deepcopy(workflow)
        
        for node in workflow_copy["nodes"]:
            node_id = node.get("id")
            node_type = node.get("type")
            widgets = node.get("widgets_values", [])
            
            # Node 12: Positive prompt (CLIPTextEncode)
            if node_id == 12 and node_type == "CLIPTextEncode" and "positive_prompt" in params:
                if widgets:
                    widgets[0] = params["positive_prompt"]
                else:
                    node["widgets_values"] = [params["positive_prompt"]]
                self.logger.info(f"Injected positive prompt into node {node_id}")
            
            # Node 13: Negative prompt (CLIPTextEncode)
            elif node_id == 13 and node_type == "CLIPTextEncode" and "negative_prompt" in params:
                if widgets:
                    widgets[0] = params["negative_prompt"]
                else:
                    node["widgets_values"] = [params["negative_prompt"]]
                self.logger.info(f"Injected negative prompt into node {node_id}")
            
            # Node 8: Dimensions and batch (EmptySD3LatentImage)
            elif node_id == 8 and node_type == "EmptySD3LatentImage":
                if not widgets:
                    widgets = [512, 512, 1]
                    node["widgets_values"] = widgets
                if "width" in params:
                    widgets[0] = params["width"]
                if "height" in params:
                    widgets[1] = params["height"]
                if "batch_size" in params:
                    widgets[2] = params["batch_size"]
                self.logger.info(f"Injected dimensions/batch into node {node_id}: {widgets}")
            
            # Node 10: KSampler
            elif node_id == 10 and node_type == "KSampler":
                if not widgets:
                    widgets = [1, "increment", 20, 1, "euler", "simple", 1]
                    node["widgets_values"] = widgets
                
                # widgets_values format: [seed, control_after_generate, steps, cfg, sampler, scheduler, denoise]
                if "seed" in params and params["seed"] >= 0:
                    widgets[0] = params["seed"]
                if "seed_control" in params:
                    widgets[1] = params["seed_control"]
                if "steps" in params:
                    widgets[2] = params["steps"]
                if "cfg" in params:
                    widgets[3] = params["cfg"]
                if "sampler_name" in params:
                    widgets[4] = params["sampler_name"]
                if "scheduler" in params:
                    widgets[5] = params["scheduler"]
                # Keep denoise as is (widgets[6])
                self.logger.info(f"Injected KSampler params into node {node_id}")
            
            # Node 5: Checkpoint (CheckpointLoaderSimple)
            elif node_id == 5 and node_type == "CheckpointLoaderSimple" and "checkpoint" in params:
                checkpoint = params["checkpoint"]
                if checkpoint and checkpoint.strip() and not checkpoint.startswith("Select"):
                    if not widgets:
                        widgets = [checkpoint]
                        node["widgets_values"] = widgets
                    else:
                        widgets[0] = checkpoint
                    self.logger.info(f"Injected checkpoint into node {node_id}: {checkpoint}")
            
            # Node 18: First LoRA Loader
            elif node_id == 18 and node_type == "LoraLoader":
                self._inject_lora_ui_format(node, params, "lora1", 0.8)
            
            # Node 19: Second LoRA Loader  
            elif node_id == 19 and node_type == "LoraLoader":
                self._inject_lora_ui_format(node, params, "lora2", 0.6)
        
        return workflow_copy
    
    def _inject_lora_ui_format(self, node: Dict[str, Any], params: Dict[str, Any], lora_prefix: str, default_strength: float):
        """Inject LoRA parameters into UI format node"""
        widgets = node.get("widgets_values", ["", default_strength, default_strength])
        
        lora_model_key = f"{lora_prefix}_model"
        lora_strength_key = f"{lora_prefix}_strength"
        lora_active_key = f"{lora_prefix}_active"
        
        # Check if LoRA is active and has a valid model
        if params.get(lora_active_key, True) and lora_model_key in params:
            lora_model = params[lora_model_key]
            if lora_model and lora_model != "None":
                # widgets_values format: [lora_name, strength_model, strength_clip]
                widgets[0] = lora_model
                if lora_strength_key in params:
                    strength = params[lora_strength_key]
                    widgets[1] = strength  # strength_model
                    widgets[2] = strength  # strength_clip
                
                node["widgets_values"] = widgets
                self.logger.info(f"Injected {lora_prefix}: {lora_model} @ {widgets[1]}")
            else:
                # Disable LoRA by setting empty model
                widgets[0] = ""
                node["widgets_values"] = widgets
                self.logger.info(f"Disabled {lora_prefix} (empty model)")
        elif not params.get(lora_active_key, True):
            # LoRA explicitly disabled
            widgets[0] = ""
            node["widgets_values"] = widgets
            self.logger.info(f"Disabled {lora_prefix} (inactive)")

    def inject_parameters(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to ComfyUI format"""
        return self.inject_parameters_comfyui(workflow, params)