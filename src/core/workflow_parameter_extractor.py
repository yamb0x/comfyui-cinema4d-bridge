"""
Dynamic workflow parameter extraction and UI synchronization
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger


class WorkflowParameterExtractor:
    """Extract and manage parameters from ComfyUI workflow JSON files"""
    
    # Known parameter mappings for common nodes
    PARAMETER_MAPPINGS = {
        "KSampler": {
            "seed": {"ui_name": "Seed", "type": "int", "min": 0, "max": 2147483647, "default": 42},
            "steps": {"ui_name": "Steps", "type": "int", "min": 1, "max": 150, "default": 20},
            "cfg": {"ui_name": "CFG Scale", "type": "float", "min": 1.0, "max": 30.0, "default": 7.0},
            "sampler_name": {"ui_name": "Sampler", "type": "choice", "default": "dpmpp_2m"},
            "scheduler": {"ui_name": "Scheduler", "type": "choice", "default": "karras"},
            "denoise": {"ui_name": "Denoise", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
        },
        "KSamplerAdvanced": {
            "noise_seed": {"ui_name": "Seed", "type": "int", "min": 0, "max": 2147483647, "default": 42},
            "steps": {"ui_name": "Steps", "type": "int", "min": 1, "max": 150, "default": 20},
            "cfg": {"ui_name": "CFG Scale", "type": "float", "min": 1.0, "max": 30.0, "default": 7.0},
            "sampler_name": {"ui_name": "Sampler", "type": "choice", "default": "dpmpp_2m"},
            "scheduler": {"ui_name": "Scheduler", "type": "choice", "default": "karras"}
        },
        "FluxGuidance": {
            "guidance": {"ui_name": "Guidance", "type": "float", "min": 1.0, "max": 10.0, "default": 3.5}
        },
        "CLIPTextEncode": {
            "text": {"ui_name": "Prompt", "type": "text", "default": ""}
        },
        "EmptyLatentImage": {
            "width": {"ui_name": "Width", "type": "int", "min": 64, "max": 4096, "default": 512},
            "height": {"ui_name": "Height", "type": "int", "min": 64, "max": 4096, "default": 512},
            "batch_size": {"ui_name": "Batch Size", "type": "int", "min": 1, "max": 64, "default": 1}
        },
        "EmptySD3LatentImage": {
            "width": {"ui_name": "Width", "type": "int", "min": 16, "max": 2048, "default": 1024},
            "height": {"ui_name": "Height", "type": "int", "min": 16, "max": 2048, "default": 1024},
            "batch_size": {"ui_name": "Batch Size", "type": "int", "min": 1, "max": 64, "default": 1}
        },
        "LoraLoader": {
            "lora_name": {"ui_name": "LoRA Model", "type": "choice", "default": "None"},
            "strength_model": {"ui_name": "Model Strength", "type": "float", "min": -10.0, "max": 10.0, "default": 1.0},
            "strength_clip": {"ui_name": "CLIP Strength", "type": "float", "min": -10.0, "max": 10.0, "default": 1.0}
        },
        "CheckpointLoader": {
            "ckpt_name": {"ui_name": "Checkpoint", "type": "choice", "default": ""}
        },
        "CheckpointLoaderSimple": {
            "ckpt_name": {"ui_name": "Checkpoint", "type": "choice", "default": ""}
        },
        "VAELoader": {
            "vae_name": {"ui_name": "VAE Model", "type": "choice", "default": ""}
        },
        "ControlNetLoader": {
            "control_net_name": {"ui_name": "ControlNet Model", "type": "choice", "default": ""}
        },
        "Note": {
            "text": {"ui_name": "Note", "type": "text", "default": "", "multiline": True}
        }
    }
    
    # Sampler choices
    SAMPLER_CHOICES = [
        "euler", "euler_ancestral", "heun", "heunpp2", "dpm_2", "dpm_2_ancestral",
        "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde",
        "dpmpp_sde_gpu", "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu",
        "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", "ddpm", "lcm", "ddim", "uni_pc",
        "uni_pc_bh2"
    ]
    
    # Scheduler choices
    SCHEDULER_CHOICES = [
        "normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"
    ]
    
    def __init__(self):
        self.logger = logger
    
    def extract_parameters(self, workflow_path: Path) -> Dict[str, Any]:
        """Extract all configurable parameters from a workflow JSON"""
        try:
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
            
            parameters = {}
            nodes = workflow.get("nodes", [])
            
            for node in nodes:
                node_type = node.get("type", "")
                node_id = node.get("id", "")
                
                # Check if we have parameter mappings for this node type
                if node_type in self.PARAMETER_MAPPINGS:
                    node_params = self._extract_node_parameters(node, node_type)
                    for param_key, param_data in node_params.items():
                        # Use node_id to make parameters unique
                        unique_key = f"{node_type}_{node_id}_{param_key}"
                        parameters[unique_key] = param_data
            
            self.logger.info(f"Extracted {len(parameters)} parameters from {workflow_path.name}")
            return parameters
            
        except Exception as e:
            self.logger.error(f"Failed to extract parameters from {workflow_path}: {e}")
            return {}
    
    def _extract_node_parameters(self, node: Dict[str, Any], node_type: str) -> Dict[str, Any]:
        """Extract parameters from a specific node"""
        params = {}
        param_mappings = self.PARAMETER_MAPPINGS.get(node_type, {})
        widgets_values = node.get("widgets_values", [])
        
        # For each known parameter in this node type
        for param_name, param_info in param_mappings.items():
            param_data = param_info.copy()
            
            # Try to find the current value in widgets_values
            # This is workflow-specific and may need adjustment based on node structure
            if node_type == "KSampler" and widgets_values:
                if param_name == "seed" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "steps" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                elif param_name == "cfg" and len(widgets_values) > 3:
                    param_data["current_value"] = widgets_values[3]
                elif param_name == "sampler_name" and len(widgets_values) > 4:
                    param_data["current_value"] = widgets_values[4]
                elif param_name == "scheduler" and len(widgets_values) > 5:
                    param_data["current_value"] = widgets_values[5]
                    
            elif node_type == "CLIPTextEncode" and widgets_values:
                if param_name == "text" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                    
            elif node_type == "EmptyLatentImage" and widgets_values:
                if param_name == "width" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "height" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "batch_size" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                    
            elif node_type == "EmptySD3LatentImage" and widgets_values:
                if param_name == "width" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "height" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "batch_size" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                    
            elif node_type == "FluxGuidance" and widgets_values:
                if param_name == "guidance" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                    
            elif node_type == "LoraLoader" and widgets_values:
                if param_name == "lora_name" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "strength_model" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "strength_clip" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                    
            elif node_type in ["CheckpointLoader", "CheckpointLoaderSimple"] and widgets_values:
                if param_name == "ckpt_name" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                    
            elif node_type == "Note" and widgets_values:
                if param_name == "text" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
            
            # Add node context
            param_data["node_id"] = node.get("id")
            param_data["node_type"] = node_type
            param_data["param_name"] = param_name
            
            params[param_name] = param_data
        
        return params
    
    def get_sampler_choices(self) -> List[str]:
        """Get list of available samplers"""
        return self.SAMPLER_CHOICES
    
    def get_scheduler_choices(self) -> List[str]:
        """Get list of available schedulers"""
        return self.SCHEDULER_CHOICES
    
    def update_workflow_parameters(self, workflow_path: Path, parameters: Dict[str, Any]) -> bool:
        """Update workflow JSON with new parameter values"""
        try:
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
            
            nodes = workflow.get("nodes", [])
            
            # Update each node's parameters
            for param_key, param_value in parameters.items():
                # Parse the parameter key
                parts = param_key.split('_', 2)
                if len(parts) >= 3:
                    node_type, node_id, param_name = parts[0], parts[1], parts[2]
                    
                    # Find the node
                    for node in nodes:
                        if str(node.get("id")) == node_id and node.get("type") == node_type:
                            self._update_node_parameter(node, node_type, param_name, param_value)
            
            # Save updated workflow
            with open(workflow_path, 'w') as f:
                json.dump(workflow, f, indent=2)
            
            self.logger.info(f"Updated workflow parameters in {workflow_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow parameters: {e}")
            return False
    
    def _update_node_parameter(self, node: Dict[str, Any], node_type: str, param_name: str, value: Any):
        """Update a specific parameter in a node"""
        widgets_values = node.get("widgets_values", [])
        
        # Ensure widgets_values exists
        if not widgets_values:
            node["widgets_values"] = []
            widgets_values = node["widgets_values"]
        
        # Update based on node type and parameter
        if node_type == "KSampler":
            # Ensure we have enough values
            while len(widgets_values) < 8:
                widgets_values.append(None)
            
            if param_name == "seed":
                widgets_values[0] = int(value)
            elif param_name == "steps":
                widgets_values[2] = int(value)
            elif param_name == "cfg":
                widgets_values[3] = float(value)
            elif param_name == "sampler_name":
                widgets_values[4] = str(value)
            elif param_name == "scheduler":
                widgets_values[5] = str(value)
                
        elif node_type == "CLIPTextEncode":
            if len(widgets_values) == 0:
                widgets_values.append("")
            if param_name == "text":
                widgets_values[0] = str(value)
                
        elif node_type == "EmptyLatentImage":
            while len(widgets_values) < 3:
                widgets_values.append(512)
            
            if param_name == "width":
                widgets_values[0] = int(value)
            elif param_name == "height":
                widgets_values[1] = int(value)
            elif param_name == "batch_size":
                widgets_values[2] = int(value)
                
        elif node_type == "EmptySD3LatentImage":
            while len(widgets_values) < 3:
                widgets_values.append(1024)
            
            if param_name == "width":
                widgets_values[0] = int(value)
            elif param_name == "height":
                widgets_values[1] = int(value)
            elif param_name == "batch_size":
                widgets_values[2] = int(value)
                
        elif node_type == "FluxGuidance":
            if len(widgets_values) == 0:
                widgets_values.append(3.5)
            if param_name == "guidance":
                widgets_values[0] = float(value)
                
        elif node_type == "LoraLoader":
            while len(widgets_values) < 3:
                widgets_values.extend(["None", 1.0, 1.0][len(widgets_values):])
            
            if param_name == "lora_name":
                widgets_values[0] = str(value)
            elif param_name == "strength_model":
                widgets_values[1] = float(value)
            elif param_name == "strength_clip":
                widgets_values[2] = float(value)
                
        elif node_type in ["CheckpointLoader", "CheckpointLoaderSimple"]:
            if len(widgets_values) == 0:
                widgets_values.append("")
            if param_name == "ckpt_name":
                widgets_values[0] = str(value)
                
        elif node_type == "Note":
            if len(widgets_values) == 0:
                widgets_values.append("")
            if param_name == "text":
                widgets_values[0] = str(value)