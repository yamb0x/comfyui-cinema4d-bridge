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
            "control_after_generation": {"ui_name": "Control After Generation", "type": "choice", "options": ["fixed", "increment", "decrement", "randomize"], "default": "randomize"},
            "steps": {"ui_name": "Steps", "type": "int", "min": 1, "max": 150, "default": 20},
            "cfg": {"ui_name": "CFG Scale", "type": "float", "min": 1.0, "max": 30.0, "default": 7.0},
            "sampler_name": {"ui_name": "Sampler", "type": "choice", "options": ["euler", "euler_a", "heun", "dpm_2", "dpm_2_a", "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_a", "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_3m_sde", "ddpm", "lcm"], "default": "dpmpp_2m"},
            "scheduler": {"ui_name": "Scheduler", "type": "choice", "options": ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"], "default": "karras"},
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
        "UNETLoader": {
            "unet_name": {"ui_name": "UNET Model", "type": "choice", "default": "hidream_i1_fast_fp8.safetensors"},
            "weight_dtype": {"ui_name": "Weight Data Type", "type": "choice", "default": "default"}
        },
        "QuadrupleCLIPLoader": {
            "clip_name1": {"ui_name": "CLIP L Model", "type": "choice", "default": "clip_l_hidream.safetensors"},
            "clip_name2": {"ui_name": "CLIP G Model", "type": "choice", "default": "clip_g_hidream.safetensors"},
            "clip_name3": {"ui_name": "T5XXL Model", "type": "choice", "default": "t5xxl_fp8_e4m3fn_scaled.safetensors"},
            "clip_name4": {"ui_name": "LLaMA Model", "type": "choice", "default": "llama_3.1_8b_instruct_fp8_scaled.safetensors"}
        },
        "ControlNetLoader": {
            "control_net_name": {"ui_name": "ControlNet Model", "type": "choice", "default": ""}
        },
        "Note": {
            "text": {"ui_name": "Note", "type": "text", "default": "", "multiline": True}
        },
        # Hunyuan3D specific nodes
        "Hy3DVAEDecode": {
            "threshold": {"ui_name": "Decode Threshold", "type": "float", "min": 0.1, "max": 2.0, "default": 1.01},
            "resolution": {"ui_name": "Voxel Resolution", "type": "int", "min": 64, "max": 1024, "default": 384},
            "iterations": {"ui_name": "Decode Iterations", "type": "int", "min": 1000, "max": 20000, "default": 8000},
            "start_index": {"ui_name": "Start Index", "type": "int", "min": 0, "max": 100, "default": 0},
            "algorithm": {"ui_name": "Algorithm", "type": "choice", "options": ["mc", "dual_contouring"], "default": "mc"},
            "enable_smoothing": {"ui_name": "Enable Smoothing", "type": "bool", "default": True},
            "enable_postprocess": {"ui_name": "Enable Post-processing", "type": "bool", "default": True}
        },
        "Hy3DGenerateMesh": {
            "guidance_scale": {"ui_name": "Guidance Scale", "type": "float", "min": 1.0, "max": 20.0, "default": 5.5},
            "steps": {"ui_name": "Generation Steps", "type": "int", "min": 10, "max": 200, "default": 100},
            "seed": {"ui_name": "Seed", "type": "int", "min": 0, "max": 2147483647, "default": 123},
            "seed_mode": {"ui_name": "Seed Mode", "type": "choice", "options": ["fixed", "random"], "default": "fixed"},
            "scheduler": {"ui_name": "Scheduler", "type": "choice", "options": ["FlowMatchEulerDiscreteScheduler", "DDIMScheduler", "EulerDiscreteScheduler"], "default": "FlowMatchEulerDiscreteScheduler"},
            "enable_feature": {"ui_name": "Enable Enhancement", "type": "bool", "default": True}
        },
        "Hy3DModelLoader": {
            "model_name": {"ui_name": "Model File", "type": "choice", "default": "hunyun3D-2\\hunyuan3d-dit-v2-0-fp16.safetensors"},
            "attention_mode": {"ui_name": "Attention Mode", "type": "choice", "options": ["sdpa", "flash_attention", "default"], "default": "sdpa"},
            "compile_model": {"ui_name": "Compile Model", "type": "bool", "default": False}
        },
        "Hy3DPostprocessMesh": {
            "smooth_mesh": {"ui_name": "Smooth Mesh", "type": "bool", "default": True},
            "remove_isolated": {"ui_name": "Remove Isolated", "type": "bool", "default": True},
            "simplify_mesh": {"ui_name": "Simplify Mesh", "type": "bool", "default": True},
            "target_faces": {"ui_name": "Target Faces", "type": "int", "min": 1000, "max": 1000000, "default": 500000},
            "clean_mesh": {"ui_name": "Clean Mesh", "type": "bool", "default": True}
        },
        "Hy3DExportMesh": {
            "filename_prefix": {"ui_name": "Filename Prefix", "type": "text", "default": "3D/Hy3D"},
            "export_format": {"ui_name": "Export Format", "type": "choice", "options": ["glb", "obj", "ply", "stl"], "default": "glb"},
            "overwrite": {"ui_name": "Overwrite Files", "type": "bool", "default": True}
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
                self.logger.info(f"🎯 KSampler {node.get('id')} widgets_values: {widgets_values}")
                if param_name == "seed" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                    self.logger.info(f"✅ Set {param_name} = {widgets_values[0]}")
                elif param_name == "control_after_generation" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                    self.logger.info(f"✅ Set {param_name} = {widgets_values[1]}")
                elif param_name == "steps" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                    self.logger.info(f"✅ Set {param_name} = {widgets_values[2]}")
                elif param_name == "cfg" and len(widgets_values) > 3:
                    param_data["current_value"] = widgets_values[3]
                    self.logger.info(f"✅ Set {param_name} = {widgets_values[3]}")
                elif param_name == "sampler_name" and len(widgets_values) > 4:
                    param_data["current_value"] = widgets_values[4]
                    self.logger.info(f"✅ Set {param_name} = {widgets_values[4]}")
                elif param_name == "scheduler" and len(widgets_values) > 5:
                    param_data["current_value"] = widgets_values[5]
                    self.logger.info(f"✅ Set {param_name} = {widgets_values[5]}")
                elif param_name == "denoise" and len(widgets_values) > 6:
                    param_data["current_value"] = widgets_values[6]
                    self.logger.info(f"✅ Set {param_name} = {widgets_values[6]}")
                else:
                    self.logger.warning(f"⚠️ No value found for {param_name} in widgets_values: {widgets_values}")
                    
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
                    
            elif node_type == "VAELoader" and widgets_values:
                if param_name == "vae_name" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                    
            elif node_type == "UNETLoader" and widgets_values:
                if param_name == "unet_name" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "weight_dtype" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                    
            elif node_type == "QuadrupleCLIPLoader" and widgets_values:
                if param_name == "clip_name1" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "clip_name2" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "clip_name3" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                elif param_name == "clip_name4" and len(widgets_values) > 3:
                    param_data["current_value"] = widgets_values[3]
                    
            elif node_type == "Note" and widgets_values:
                if param_name == "text" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
            
            # Hunyuan3D specific nodes
            elif node_type == "Hy3DVAEDecode" and widgets_values:
                if param_name == "threshold" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "resolution" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "iterations" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                elif param_name == "start_index" and len(widgets_values) > 3:
                    param_data["current_value"] = widgets_values[3]
                elif param_name == "algorithm" and len(widgets_values) > 4:
                    param_data["current_value"] = widgets_values[4]
                elif param_name == "enable_smoothing" and len(widgets_values) > 5:
                    param_data["current_value"] = widgets_values[5]
                elif param_name == "enable_postprocess" and len(widgets_values) > 6:
                    param_data["current_value"] = widgets_values[6]
                    
            elif node_type == "Hy3DGenerateMesh" and widgets_values:
                if param_name == "guidance_scale" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "steps" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "seed" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                elif param_name == "seed_mode" and len(widgets_values) > 3:
                    param_data["current_value"] = widgets_values[3]
                elif param_name == "scheduler" and len(widgets_values) > 4:
                    param_data["current_value"] = widgets_values[4]
                elif param_name == "enable_feature" and len(widgets_values) > 5:
                    param_data["current_value"] = widgets_values[5]
                    
            elif node_type == "Hy3DModelLoader" and widgets_values:
                if param_name == "model_name" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "attention_mode" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "compile_model" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                    
            elif node_type == "Hy3DPostprocessMesh" and widgets_values:
                if param_name == "smooth_mesh" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "remove_isolated" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "simplify_mesh" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
                elif param_name == "target_faces" and len(widgets_values) > 3:
                    param_data["current_value"] = widgets_values[3]
                elif param_name == "clean_mesh" and len(widgets_values) > 4:
                    param_data["current_value"] = widgets_values[4]
                    
            elif node_type == "Hy3DExportMesh" and widgets_values:
                if param_name == "filename_prefix" and len(widgets_values) > 0:
                    param_data["current_value"] = widgets_values[0]
                elif param_name == "export_format" and len(widgets_values) > 1:
                    param_data["current_value"] = widgets_values[1]
                elif param_name == "overwrite" and len(widgets_values) > 2:
                    param_data["current_value"] = widgets_values[2]
            
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
            # Ensure we have enough values (KSampler has 7 parameters: seed, control, steps, cfg, sampler, scheduler, denoise)
            while len(widgets_values) < 7:
                widgets_values.append(None)
            
            if param_name == "seed":
                widgets_values[0] = int(value)
            elif param_name == "control_after_generation":
                widgets_values[1] = str(value)
            elif param_name == "steps":
                widgets_values[2] = int(value)
            elif param_name == "cfg":
                widgets_values[3] = float(value)
            elif param_name == "sampler_name":
                widgets_values[4] = str(value)
            elif param_name == "scheduler":
                widgets_values[5] = str(value)
            elif param_name == "denoise":
                widgets_values[6] = float(value)
                
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