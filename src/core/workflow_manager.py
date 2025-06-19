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
    
    # C long limits for integer overflow protection
    MAX_C_LONG = 2147483647
    MIN_C_LONG = -2147483648
    
    def __init__(self, workflows_dir: Path, config=None):
        self.workflows_dir = workflows_dir
        self.config = config
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self._workflow_cache: Dict[str, Dict[str, Any]] = {}
        self._backup_dir = self.workflows_dir / "backups"
        self._backup_dir.mkdir(exist_ok=True)
        
    def safe_int(self, value, param_name: str = "parameter", default_val: int = 0) -> int:
        """
        Safely convert value to integer with C long overflow protection.
        Prevents 'Python int too large to convert to C long' errors.
        """
        try:
            int_val = int(value)
            if int_val > self.MAX_C_LONG:
                self.logger.warning(f"🔧 INTEGER OVERFLOW: {param_name} value {int_val} exceeds C long limit, clamping to {self.MAX_C_LONG}")
                return self.MAX_C_LONG
            elif int_val < self.MIN_C_LONG:
                self.logger.warning(f"🔧 INTEGER UNDERFLOW: {param_name} value {int_val} below C long limit, clamping to {self.MIN_C_LONG}")
                return self.MIN_C_LONG
            return int_val
        except (ValueError, TypeError):
            self.logger.warning(f"🔧 INVALID INTEGER: {param_name} value '{value}' cannot be converted to int, using default {default_val}")
            return default_val
    
    def load_workflow(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Load workflow from file"""
        workflow_path = self.workflows_dir / workflow_name
        
        if not workflow_path.exists():
            self.logger.error(f"Workflow not found: {workflow_name}")
            return None
        
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
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
                    inputs["seed"] = self.safe_int(params["seed"], "KSampler_seed", 42)
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
            
            # Inject custom dynamic parameters if they exist
            if hasattr(self, 'custom_parameters') and node_id in self.custom_parameters:
                custom_params = self.custom_parameters[node_id]
                for param_name, param_value in custom_params.items():
                    if param_name in inputs:
                        inputs[param_name] = param_value
                        self.logger.debug(f"Injected custom parameter {param_name} into node {node_id}")
            
            # Handle LoRA nodes - inject based on node position
            elif node_type == "LoraLoader":
                # Find which LoRA parameters to use for this node (same logic as UI format)
                original_node = None
                for orig_node in workflow.get("nodes", []):
                    if str(orig_node.get("id")) == node_id:
                        original_node = orig_node
                        break
                
                if original_node:
                    current_widgets = original_node.get("widgets_values", [])
                    current_model = current_widgets[0] if current_widgets else ""
                    
                    # Try to match by model name first
                    lora_found = False
                    for i in range(1, 10):  # Support up to 10 LoRAs
                        lora_key = f"lora{i}"
                        if f"{lora_key}_model" in params and params[f"{lora_key}_model"] == current_model:
                            inputs["lora_name"] = params[f"{lora_key}_model"]
                            inputs["strength_model"] = params.get(f"{lora_key}_strength", 1.0)
                            inputs["strength_clip"] = params.get(f"{lora_key}_strength", 1.0)
                            self.logger.debug(f"Injected {lora_key} params into node {node_id}: {inputs['lora_name']}")
                            lora_found = True
                            break
                    
                    if not lora_found:
                        self.logger.debug(f"No matching LoRA parameters found for node {node_id} model: {current_model}")
                else:
                    self.logger.debug(f"Could not find original node for LoRA node {node_id}")
            
            # Handle FluxGuidance node
            elif node_type == "FluxGuidance":
                # FluxGuidance uses CFG value as guidance
                if "cfg" in params:
                    inputs["guidance"] = params["cfg"]
                    self.logger.debug(f"Injected guidance (cfg) into FluxGuidance node {node_id}: {inputs['guidance']}")
        
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
        
        self.logger.info(f"Converting UI workflow with {len(ui_workflow.get('nodes', []))} nodes to API format")
        
        # Debug: List all nodes in the UI workflow
        all_node_ids = [str(node.get("id", "")) for node in ui_workflow.get("nodes", [])]
        self.logger.info(f"All node IDs in UI workflow: {all_node_ids}")
        
        # First pass: Create basic nodes with widget values
        for node in ui_workflow.get("nodes", []):
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "")
            
            # Skip Note nodes - they're UI-only and not executable
            if node_type == "Note":
                self.logger.debug(f"Skipping Note node {node_id} in API conversion")
                continue
            
            # Skip Reroute nodes entirely - ComfyUI handles them differently in API format
            if node_type == "Reroute":
                self.logger.info(f"Skipping Reroute node {node_id} - handled through link resolution")
                continue
            
            # Skip Anything Everywhere nodes - they distribute values globally
            if "Anything Everywhere" in node_type:
                self.logger.info(f"Skipping {node_type} node {node_id} - will handle distributed connections")
                continue
            
            # Check if node is bypassed and should be skipped
            node_mode = node.get("mode", 0)
            if node_mode == 4 and node_type in ["LoraLoader"]:
                self.logger.info(f"Skipping bypassed {node_type} node {node_id} in API conversion")
                continue
            
            # Use the node type as-is for API
            api_class_type = node_type
            
            # Handle missing node types with replacements
            node_replacements = {
                "PrimitiveNode": "PrimitiveInt",  # Replace missing PrimitiveNode with PrimitiveInt
                # Add more replacements as needed
            }
            
            if api_class_type in node_replacements:
                original_type = api_class_type
                api_class_type = node_replacements[api_class_type]
                self.logger.warning(f"Replacing missing node type '{original_type}' with '{api_class_type}' for node {node_id}")
            
            # Create API format node
            api_node = {
                "class_type": api_class_type,
                "inputs": {}
            }
            
            # Preserve mode (bypass state) if present
            if "mode" in node:
                api_node["mode"] = node["mode"]
            
            # Convert widgets_values to inputs based on node type
            widgets = node.get("widgets_values", [])
            
            if node_type == "CLIPTextEncode" and widgets:
                api_node["inputs"]["text"] = widgets[0] if widgets else ""
            elif node_type == "EmptySD3LatentImage" and len(widgets) >= 3:
                api_node["inputs"]["width"] = widgets[0]
                api_node["inputs"]["height"] = widgets[1] 
                api_node["inputs"]["batch_size"] = widgets[2]
            elif node_type == "KSampler" and len(widgets) >= 7:
                # Correct order: seed, control_after_generation, steps, cfg, sampler_name, scheduler, denoise
                api_node["inputs"]["seed"] = widgets[0]
                api_node["inputs"]["control_after_generate"] = widgets[1] if len(widgets) > 1 else "fixed"
                api_node["inputs"]["steps"] = widgets[2]
                api_node["inputs"]["cfg"] = widgets[3]
                api_node["inputs"]["sampler_name"] = widgets[4]
                api_node["inputs"]["scheduler"] = widgets[5]
                api_node["inputs"]["denoise"] = widgets[6] if len(widgets) > 6 else 1.0
            elif node_type == "CheckpointLoaderSimple" and widgets:
                api_node["inputs"]["ckpt_name"] = widgets[0] if widgets else "flux1-dev-fp8.safetensors"
            elif node_type == "LoraLoader" and len(widgets) >= 3:
                lora_name = widgets[0] if widgets[0] else ""
                # Convert "None" to empty string for ComfyUI
                if lora_name == "None":
                    lora_name = ""
                self.logger.debug(f"Converting LoraLoader node {node_id}: lora_name='{lora_name}'")
                api_node["inputs"]["lora_name"] = lora_name
                api_node["inputs"]["strength_model"] = widgets[1] if len(widgets) > 1 else 1.0
                api_node["inputs"]["strength_clip"] = widgets[2] if len(widgets) > 2 else 1.0
            elif node_type == "FluxGuidance" and widgets:
                # FluxGuidance expects a 'guidance' parameter from widgets_values[0]
                api_node["inputs"]["guidance"] = widgets[0] if widgets else 3.5
            elif node_type == "LoadImage" and widgets:
                # widgets: [image_filename, upload_type]
                if len(widgets) >= 2:
                    api_node["inputs"]["image"] = widgets[0]  # image filename
                    # upload_type (widgets[1]) is usually "image" - not needed for API
                elif len(widgets) >= 1:
                    api_node["inputs"]["image"] = widgets[0]
            
            # Hunyuan3D nodes
            elif node_type == "Hy3DGenerateMesh" and widgets:
                # widgets: [guidance_scale, inference_steps, seed, seed_control, scheduler, use_karras]
                if len(widgets) >= 6:
                    api_node["inputs"]["guidance_scale"] = widgets[0]
                    api_node["inputs"]["steps"] = widgets[1] 
                    api_node["inputs"]["seed"] = widgets[2]
                    api_node["inputs"]["seed_control"] = widgets[3]
                    api_node["inputs"]["scheduler"] = widgets[4]
                    api_node["inputs"]["use_karras"] = widgets[5]
            
            elif node_type == "Hy3DVAEDecode" and widgets:
                # widgets: [simplify_ratio, resolution, max_faces, start_resolution, algorithm, remove_dups, merge_vertices]
                if len(widgets) >= 7:
                    api_node["inputs"]["box_v"] = widgets[0]  # simplify_ratio -> box_v
                    api_node["inputs"]["octree_resolution"] = widgets[1]  # resolution
                    api_node["inputs"]["num_chunks"] = widgets[2]  # max_faces -> num_chunks  
                    api_node["inputs"]["mc_level"] = widgets[3]  # start_resolution -> mc_level
                    api_node["inputs"]["mc_algo"] = widgets[4]  # algorithm
                    # Skip remove_dups and merge_vertices - handled in post-processing
            
            elif node_type == "Hy3DPostprocessMesh" and widgets:
                # widgets: [remove_duplicates, merge_vertices, optimize_mesh, target_faces, use_mask]
                if len(widgets) >= 5:
                    api_node["inputs"]["remove_degenerate_faces"] = widgets[0]  # remove_duplicates
                    api_node["inputs"]["smooth_normals"] = widgets[1]  # merge_vertices  
                    api_node["inputs"]["reduce_faces"] = widgets[2]  # optimize_mesh
                    api_node["inputs"]["max_facenum"] = widgets[3]  # target_faces
                    api_node["inputs"]["remove_floaters"] = widgets[4]  # use_mask -> remove_floaters
            
            elif node_type == "Hy3DDelightImage" and widgets:
                # widgets: [delight_steps, width, height, guidance_scale, num_images, seed]
                if len(widgets) >= 6:
                    api_node["inputs"]["steps"] = self.safe_int(widgets[0], "Hy3DDelightImage_steps", 20) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).isdigit() else 20
                    api_node["inputs"]["width"] = self.safe_int(widgets[1], "Hy3DDelightImage_width", 512) if isinstance(widgets[1], (int, float, str)) and str(widgets[1]).isdigit() else 512
                    api_node["inputs"]["height"] = self.safe_int(widgets[2], "Hy3DDelightImage_height", 512) if isinstance(widgets[2], (int, float, str)) and str(widgets[2]).isdigit() else 512
                    api_node["inputs"]["cfg_image"] = float(widgets[3]) if isinstance(widgets[3], (int, float, str)) and str(widgets[3]).replace('.','',1).isdigit() else 7.0
                    # Skip num_images
                    api_node["inputs"]["seed"] = self.safe_int(widgets[5], "Hy3DDelightImage_seed", 42) if isinstance(widgets[5], (int, float, str)) and str(widgets[5]).isdigit() else 42
            
            elif node_type == "Hy3DLoadMesh" and widgets:
                # NEW: Hy3DLoadMesh node - takes direct file path
                if len(widgets) >= 1:
                    mesh_path = widgets[0]
                    api_node["inputs"]["glb_path"] = mesh_path  # Direct path to mesh file (parameter name is glb_path)
                    self.logger.debug(f"CONVERSION FIX: Hy3DLoadMesh node {node_id} glb_path={mesh_path}")
                else:
                    self.logger.warning(f"Hy3DLoadMesh node {node_id} has no widgets_values - mesh path will be missing")
            
            elif node_type == "Hy3DUploadMesh" and widgets:
                # LEGACY: Hy3DUploadMesh node - takes filename only (kept for backward compatibility)
                if len(widgets) >= 1:
                    mesh_filename = widgets[0]
                    api_node["inputs"]["mesh"] = mesh_filename  # mesh filename/path
                    self.logger.debug(f"CONVERSION FIX: Hy3DUploadMesh node {node_id} mesh={mesh_filename}")
                    
                    # upload_type (widgets[1]) is usually "mesh" - not needed for API
                else:
                    self.logger.warning(f"Hy3DUploadMesh node {node_id} has no widgets_values - mesh input will be missing")
            
            elif node_type == "SolidMask" and widgets:
                # widgets: [value, width, height] - ensure minimum dimensions
                if len(widgets) >= 3:
                    api_node["inputs"]["value"] = float(widgets[0]) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).replace('.','',1).isdigit() else 1.0
                    # Ensure minimum mask dimensions to prevent PIL errors
                    width = max(self.safe_int(widgets[1], "SolidMask_width", 512) if isinstance(widgets[1], (int, float, str)) and str(widgets[1]).isdigit() else 512, 64)
                    height = max(self.safe_int(widgets[2], "SolidMask_height", 512) if isinstance(widgets[2], (int, float, str)) and str(widgets[2]).isdigit() else 512, 64)
                    api_node["inputs"]["width"] = width
                    api_node["inputs"]["height"] = height
                    self.logger.debug(f"CONVERSION FIX: SolidMask node {node_id} {width}x{height}")
            
            elif node_type == "TransparentBGSession+" and widgets:
                # widgets: [mode, use_jit]
                if len(widgets) >= 2:
                    api_node["inputs"]["mode"] = widgets[0]
                    api_node["inputs"]["use_jit"] = widgets[1]
            
            elif node_type == "ImageCompositeMasked" and widgets:
                # widgets: [x, y, resize_source]
                if len(widgets) >= 3:
                    api_node["inputs"]["x"] = widgets[0]
                    api_node["inputs"]["y"] = widgets[1]
                    api_node["inputs"]["resize_source"] = widgets[2]
            
            # Custom nodes that might not have specific handling
            elif node_type == "SetNode":
                # SetNode stores a value with a name
                if widgets and len(widgets) >= 1:
                    api_node["inputs"]["key"] = widgets[0]  # The storage key name
                # SetNode also needs the value input connected via links
                self.logger.debug(f"Processing SetNode {node_id} with key: {widgets[0] if widgets else 'unknown'}")
            
            elif node_type == "GetNode":
                # GetNode retrieves a value by name
                if widgets and len(widgets) >= 1:
                    api_node["inputs"]["key"] = widgets[0]  # The retrieval key name
                self.logger.debug(f"Processing GetNode {node_id} with key: {widgets[0] if widgets else 'unknown'}")
            
            elif node_type == "PrimitiveNode" and widgets:
                # PrimitiveNode outputs a value
                if len(widgets) >= 1:
                    api_node["inputs"]["value"] = widgets[0]
            
            elif node_type == "PrimitiveInt" and widgets:
                # PrimitiveInt outputs an integer
                if len(widgets) >= 1:
                    api_node["inputs"]["value"] = widgets[0]
            
            elif node_type == "PrimitiveStringMultiline" and widgets:
                # String input node
                if len(widgets) >= 1:
                    api_node["inputs"]["string"] = widgets[0]
            
            elif node_type == "SimpleMath+" and widgets:
                # Math expression node - widgets: [expression]
                if len(widgets) >= 1:
                    api_node["inputs"]["value"] = widgets[0]  # Math expression like "a-1"
                    self.logger.debug(f"CONVERSION FIX: SimpleMath+ node {node_id} value={widgets[0]}")
                else:
                    self.logger.warning(f"SimpleMath+ node {node_id} has no widgets_values - value input will be missing")
            
            elif node_type == "DownloadAndLoadHy3DDelightModel" and widgets:
                # widgets: [model]
                if widgets:
                    api_node["inputs"]["model"] = widgets[0]
            
            elif node_type == "Hy3DModelLoader" and widgets:
                # widgets: [model, attention, compile]
                if widgets:
                    api_node["inputs"]["model"] = widgets[0]
                    if len(widgets) > 1:
                        api_node["inputs"]["attention"] = widgets[1]
                    if len(widgets) > 2:
                        api_node["inputs"]["compile"] = widgets[2]
            
            elif node_type == "Hy3DExportMesh" and widgets:
                # widgets: [output_path, file_format, save_file]
                if len(widgets) >= 3:
                    api_node["inputs"]["filename_prefix"] = widgets[0]  # output_path -> filename_prefix
                    api_node["inputs"]["file_format"] = widgets[1]
                    # RESPECT original save_file setting from workflow
                    api_node["inputs"]["save_file"] = bool(widgets[2])  # Use actual save_file value from workflow
                    self.logger.info(f"🔧 Hy3DExportMesh node {node_id}: save_file={widgets[2]} (respecting workflow setting)")
            elif node_type == "ImageResize+" and widgets:
                # widgets: [width, height, interpolation, method, condition, multiple_of]
                if len(widgets) >= 6:
                    api_node["inputs"]["width"] = widgets[0]
                    api_node["inputs"]["height"] = widgets[1]
                    api_node["inputs"]["interpolation"] = widgets[2]
                    api_node["inputs"]["method"] = widgets[3]
                    api_node["inputs"]["condition"] = widgets[4]
                    api_node["inputs"]["multiple_of"] = widgets[5]
            
            elif node_type == "ImageScaleBy" and widgets:
                # widgets: [upscale_method, scale_by]
                if len(widgets) >= 2:
                    api_node["inputs"]["upscale_method"] = widgets[0]
                    api_node["inputs"]["scale_by"] = widgets[1]
            
            elif node_type == "Hy3DRenderMultiView" and widgets:
                # widgets: [render_size, texture_size]
                if len(widgets) >= 2:
                    api_node["inputs"]["render_size"] = widgets[0]
                    api_node["inputs"]["texture_size"] = widgets[1]
            
            elif node_type == "Hy3DCameraConfig" and widgets:
                # widgets: [camera_elevations, camera_azimuths, view_weights, camera_distance, ortho_scale]
                if len(widgets) >= 5:
                    # CRITICAL FIX: Hunyuan3D has a KeyError bug with unsupported angles
                    # Supported angles ONLY: {-90, -45, -20, 0, 20, 45, 90}
                    # Any other angles (180, 270, etc.) cause KeyError in the Hunyuan3D node
                    # This applies to BOTH elevations and azimuths!
                    
                    camera_elevations = str(widgets[0])
                    camera_azimuths = str(widgets[1])
                    
                    # Fix elevations first (check for problematic 180°, 270° angles)
                    if "180" in camera_elevations:
                        camera_elevations = camera_elevations.replace("180", "90")
                        self.logger.info(f"🔧 CAMERA FIX: Replaced 180° elevation with 90°")
                    if "270" in camera_elevations:
                        camera_elevations = camera_elevations.replace("270", "-90")
                        self.logger.info(f"🔧 CAMERA FIX: Replaced 270° elevation with -90°")
                    if "0, 90, 90, -90, 0, 90" in camera_elevations:
                        camera_elevations = "0, 20, 45, -20, -45, 0"  # 6 safe elevation angles
                        self.logger.info(f"🔧 CAMERA FIX: Replaced elevation string with safe angles")
                    
                    # Fix azimuths 
                    if "180" in camera_azimuths:
                        camera_azimuths = camera_azimuths.replace("180", "90")
                        self.logger.info(f"🔧 CAMERA FIX: Replaced 180° azimuth with 90°")
                    if "270" in camera_azimuths:
                        camera_azimuths = camera_azimuths.replace("270", "-90")
                        self.logger.info(f"🔧 CAMERA FIX: Replaced 270° azimuth with -90°")
                    if "360" in camera_azimuths:
                        camera_azimuths = camera_azimuths.replace("360", "0")
                        self.logger.info(f"🔧 CAMERA FIX: Replaced 360° azimuth with 0°")
                    
                    # Additional angle fixes for other unsupported angles commonly used
                    camera_azimuths = camera_azimuths.replace("135", "90")  # 135° -> 90°
                    camera_azimuths = camera_azimuths.replace("225", "-45") # 225° -> -45°
                    camera_azimuths = camera_azimuths.replace("315", "-45") # 315° -> -45°
                    
                    # If we still have the problematic string from workflow, replace with safe defaults
                    if "0, 90, 180, 270, 0, 180" in camera_azimuths:
                        camera_azimuths = "0, 45, 90, -45, -90, 0"  # 6 safe angles
                        self.logger.info(f"🔧 CAMERA FIX: Replaced entire azimuth string with safe angles")
                    
                    api_node["inputs"]["camera_elevations"] = camera_elevations
                    api_node["inputs"]["camera_azimuths"] = camera_azimuths
                    api_node["inputs"]["view_weights"] = widgets[2]
                    api_node["inputs"]["camera_distance"] = widgets[3]
                    api_node["inputs"]["ortho_scale"] = widgets[4]
                    self.logger.info(f"🔧 CONVERSION FIX: Hy3DCameraConfig node {node_id} - angles validated and safe")
            
            elif node_type == "UpscaleModelLoader" and widgets:
                # widgets: [model_name]
                if len(widgets) >= 1:
                    api_node["inputs"]["model_name"] = widgets[0]
            
            elif node_type == "DownloadAndLoadHy3DPaintModel" and widgets:
                # widgets: [model]
                if len(widgets) >= 1:
                    api_node["inputs"]["model"] = widgets[0]
            
            elif node_type == "Hy3DSampleMultiView" and widgets:
                # widgets: [seed, steps, view_size]
                if len(widgets) >= 3:
                    # Fix: Validate integer values to prevent "Python int too large to convert to C long"
                    api_node["inputs"]["seed"] = self.safe_int(widgets[0], "Hy3DSampleMultiView_seed", 42)
                    api_node["inputs"]["steps"] = self.safe_int(widgets[1], "Hy3DSampleMultiView_steps", 20)
                    api_node["inputs"]["view_size"] = self.safe_int(widgets[2], "Hy3DSampleMultiView_view_size", 512)
                    self.logger.info(f"🔧 Hy3DSampleMultiView node {node_id}: seed={api_node['inputs']['seed']}, steps={api_node['inputs']['steps']}, view_size={api_node['inputs']['view_size']}")
            
            elif node_type == "CV2InpaintTexture" and widgets:
                # widgets: [inpaint_radius, inpaint_method]
                if len(widgets) >= 2:
                    api_node["inputs"]["inpaint_radius"] = widgets[0]
                    api_node["inputs"]["inpaint_method"] = widgets[1]
            
            elif node_type == "Image Save" and widgets:
                # Map widgets_values to Image Save node inputs
                # Based on actual UI workflow: [output_path, filename_prefix, filename_delimiter, 
                # filename_number_start, overwrite_mode, extension, quality, dpi, optimize_image,
                # lossless_webp, embed_workflow, show_previews, show_history, show_history_by_prefix,
                # filename_number_padding]
                if len(widgets) >= 13:  # Minimum required fields
                    # Override the output path to ensure it goes to our configured images directory
                    if hasattr(self, 'config') and hasattr(self.config, 'images_dir'):
                        correct_images_path = str(self.config.images_dir)
                    else:
                        from pathlib import Path
                        correct_images_path = str(Path(__file__).parent.parent.parent / "images")
                    
                    self.logger.info(f"Setting Image Save output_path to: {correct_images_path}")
                    api_node["inputs"]["output_path"] = correct_images_path
                    api_node["inputs"]["filename_prefix"] = widgets[1] if len(widgets) > 1 else "ComfyUI" 
                    api_node["inputs"]["filename_delimiter"] = widgets[2] if len(widgets) > 2 else "_"
                    
                    # Handle filename_number_start - it's an integer in widgets
                    if len(widgets) > 3:
                        start_val = widgets[3]
                        if isinstance(start_val, int):
                            api_node["inputs"]["filename_number_start"] = "true" if start_val > 0 else "false"
                        else:
                            api_node["inputs"]["filename_number_start"] = str(start_val).lower()
                    
                    # Handle overwrite_mode
                    if len(widgets) > 4:
                        api_node["inputs"]["overwrite_mode"] = widgets[4]
                    
                    # Extension
                    if len(widgets) > 5:
                        api_node["inputs"]["extension"] = widgets[5]
                    
                    # Quality and DPI - ensure they are integers
                    if len(widgets) > 6:
                        try:
                            quality_val = widgets[6]
                            self.logger.debug(f"Image Save quality value: {repr(quality_val)} (type: {type(quality_val).__name__})")
                            api_node["inputs"]["quality"] = min(self.safe_int(quality_val, "SaveImage_quality", 95), 100)
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f"Failed to convert quality to int: {e}")
                            api_node["inputs"]["quality"] = 95  # Default quality
                    
                    if len(widgets) > 7:
                        try:
                            dpi_val = widgets[7]
                            self.logger.debug(f"Image Save DPI value: {repr(dpi_val)} (type: {type(dpi_val).__name__})")
                            api_node["inputs"]["dpi"] = self.safe_int(dpi_val, "SaveImage_dpi", 72)
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f"Failed to convert DPI to int: {e}")
                            api_node["inputs"]["dpi"] = 72  # Default DPI
                    
                    # Boolean string values
                    bool_fields = [
                        (8, "optimize_image"),
                        (9, "lossless_webp"),
                        (10, "embed_workflow"),
                        (11, "show_previews"),
                        (12, "show_history"),
                        (13, "show_history_by_prefix")
                    ]
                    
                    for idx, field_name in bool_fields:
                        if len(widgets) > idx:
                            val = widgets[idx]
                            if isinstance(val, bool):
                                api_node["inputs"][field_name] = "true" if val else "false"
                            else:
                                api_node["inputs"][field_name] = str(val).lower()
                    
                    # Handle filename_number_padding
                    if len(widgets) > 14:
                        padding_val = widgets[14]
                        self.logger.debug(f"Image Save padding value: {repr(padding_val)} (type: {type(padding_val).__name__})")
                        if isinstance(padding_val, str) and padding_val.lower() in ["false", "true"]:
                            api_node["inputs"]["filename_number_padding"] = 4  # Default value for boolean strings
                        else:
                            try:
                                api_node["inputs"]["filename_number_padding"] = self.safe_int(padding_val, "SaveImage_filename_number_padding", 4)
                            except (ValueError, TypeError) as e:
                                self.logger.warning(f"Failed to convert padding to int: {e}, using default")
                                api_node["inputs"]["filename_number_padding"] = 4
            
            # Additional critical node mappings for texture workflow
            elif node_type == "ImageResizeKJv2" and len(widgets) >= 7:
                # Ensure minimum dimensions and avoid lanczos
                width = max(self.safe_int(widgets[0], "ImageResizeKJv2_width", 512) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).isdigit() else 512, 64)
                height = max(self.safe_int(widgets[1], "ImageResizeKJv2_height", 512) if isinstance(widgets[1], (int, float, str)) and str(widgets[1]).isdigit() else 512, 64)
                api_node["inputs"]["width"] = width
                api_node["inputs"]["height"] = height
                # CRITICAL: Force nearest-exact for ImageResize to avoid PIL errors
                api_node["inputs"]["upscale_method"] = "nearest-exact"
                api_node["inputs"]["keep_proportion"] = widgets[3]
                api_node["inputs"]["crop_position"] = widgets[4] if widgets[4] in ["center", "top", "bottom", "left", "right"] else "center"
                api_node["inputs"]["divisible_by"] = widgets[5] if isinstance(widgets[5], (int, float)) and widgets[5] != "center" else 2
                api_node["inputs"]["pad_color"] = widgets[6]
                self.logger.info(f"🔧 CONVERSION FIX: ImageResizeKJv2 node {node_id} with {len(widgets)} widgets")
            
            elif node_type == "ImageRemoveBackground+" and widgets:
                api_node["inputs"]["mode"] = widgets[0] if widgets else "auto"
                self.logger.info(f"🔧 CONVERSION FIX: ImageRemoveBackground+ node {node_id}")
                # Add note about potential mask shape issues
                self.logger.warning(f"ImageRemoveBackground+ node {node_id} - ensure input image has proper dimensions")
            
            elif node_type == "ImageBlend" and len(widgets) >= 2:
                # Fix parameter order: mode should be string, factor should be float
                if isinstance(widgets[0], str) and widgets[0] in ["normal", "multiply", "screen", "overlay", "soft_light", "difference"]:
                    api_node["inputs"]["blend_mode"] = widgets[0]
                    api_node["inputs"]["blend_factor"] = float(widgets[1]) if isinstance(widgets[1], (int, float, str)) and str(widgets[1]).replace('.','',1).isdigit() else 0.5
                else:
                    # Reversed order - factor first, then mode
                    api_node["inputs"]["blend_factor"] = float(widgets[0]) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).replace('.','',1).isdigit() else 0.5
                    api_node["inputs"]["blend_mode"] = widgets[1] if widgets[1] in ["normal", "multiply", "screen", "overlay", "soft_light", "difference"] else "normal"
                self.logger.info(f"🔧 CONVERSION FIX: ImageBlend node {node_id}")
            
            elif node_type == "ResizeMask" and len(widgets) >= 5:
                # Ensure minimum reasonable dimensions for masks
                width = max(self.safe_int(widgets[0], "ResizeMask_width", 512) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).isdigit() else 512, 64)
                height = max(self.safe_int(widgets[1], "ResizeMask_height", 512) if isinstance(widgets[1], (int, float, str)) and str(widgets[1]).isdigit() else 512, 64)
                
                api_node["inputs"]["width"] = width
                api_node["inputs"]["height"] = height
                # CRITICAL: ALWAYS use "nearest-exact" to avoid PIL errors with small masks
                # Lanczos can cause "(1, 1, 1), |u1" errors when processing very small mask tensors
                # Force nearest-exact for all ResizeMask operations regardless of original method
                api_node["inputs"]["upscale_method"] = "nearest-exact"
                api_node["inputs"]["keep_proportions"] = bool(widgets[3]) if len(widgets) > 3 and widgets[3] in [True, False, "true", "false"] else False
                api_node["inputs"]["crop"] = widgets[4] if len(widgets) > 4 and widgets[4] in ["disabled", "center"] else "disabled"
                self.logger.info(f"🔧 CONVERSION FIX: ResizeMask node {node_id} {width}x{height} method=nearest-exact (forced)")
            
            elif node_type == "ImageFromBatch" and len(widgets) >= 2:
                api_node["inputs"]["batch_index"] = widgets[0]
                api_node["inputs"]["length"] = widgets[1]
                self.logger.info(f"🔧 CONVERSION FIX: ImageFromBatch node {node_id}")
            
            elif node_type == "SomethingToString" and widgets:
                api_node["inputs"]["value"] = widgets[0] if widgets else ""
                self.logger.info(f"🔧 CONVERSION FIX: SomethingToString node {node_id}")
            
            elif node_type == "Hy3DRenderMultiViewDepth" and len(widgets) >= 2:
                api_node["inputs"]["render_size"] = widgets[0]
                api_node["inputs"]["texture_size"] = widgets[1]
                self.logger.info(f"🔧 CONVERSION FIX: Hy3DRenderMultiViewDepth node {node_id}")
            
            elif node_type == "Hy3DDiffusersSchedulerConfig" and len(widgets) >= 2:
                api_node["inputs"]["scheduler"] = widgets[0] if widgets else "ddim"
                api_node["inputs"]["sigmas"] = widgets[1] if len(widgets) > 1 else "karras"
                self.logger.info(f"🔧 CONVERSION FIX: Hy3DDiffusersSchedulerConfig node {node_id}")
            
            elif node_type == "UltimateSDUpscale" and len(widgets) >= 18:
                # CORRECT PARAMETER MAPPING based on actual workflow analysis
                # widgets_values order: [upscale_by, seed, "fixed", steps, cfg, sampler_name, scheduler, denoise, mode_type, tile_width, tile_height, mask_blur, tile_padding, seam_fix_mode, seam_fix_denoise, seam_fix_width, seam_fix_mask_blur, seam_fix_padding, force_uniform_tiles, tiled_decode]
                api_node["inputs"]["upscale_by"] = float(widgets[0]) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).replace('.','',1).isdigit() else 2.0
                api_node["inputs"]["seed"] = self.safe_int(widgets[1], "UltimateSDUpscale_seed", 123456) if isinstance(widgets[1], (int, float, str)) and str(widgets[1]).isdigit() else 123456
                # widgets[2] is "fixed" (seed_control) - skip it
                api_node["inputs"]["steps"] = self.safe_int(widgets[3], "UltimateSDUpscale_steps", 20) if isinstance(widgets[3], (int, float, str)) and str(widgets[3]).isdigit() else 20
                api_node["inputs"]["cfg"] = float(widgets[4]) if isinstance(widgets[4], (int, float, str)) and str(widgets[4]).replace('.','',1).isdigit() else 7.0
                api_node["inputs"]["sampler_name"] = widgets[5] if isinstance(widgets[5], str) else "euler"
                api_node["inputs"]["scheduler"] = widgets[6] if widgets[6] in ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta", "linear_quadratic", "kl_optimal"] else "normal"
                api_node["inputs"]["denoise"] = float(widgets[7]) if isinstance(widgets[7], (int, float, str)) and str(widgets[7]).replace('.','',1).isdigit() else 0.3
                api_node["inputs"]["mode_type"] = widgets[8] if widgets[8] in ["Linear", "Chess", "None"] else "Linear"
                api_node["inputs"]["tile_width"] = self.safe_int(widgets[9], "UltimateSDUpscale_tile_width", 512) if isinstance(widgets[9], (int, float, str)) and str(widgets[9]).isdigit() else 512
                api_node["inputs"]["tile_height"] = self.safe_int(widgets[10], "UltimateSDUpscale_tile_height", 512) if isinstance(widgets[10], (int, float, str)) and str(widgets[10]).isdigit() else 512
                api_node["inputs"]["mask_blur"] = min(self.safe_int(widgets[11], "UltimateSDUpscale_mask_blur", 8) if isinstance(widgets[11], (int, float, str)) and str(widgets[11]).isdigit() else 8, 64)  # Cap at max 64
                api_node["inputs"]["tile_padding"] = self.safe_int(widgets[12], "UltimateSDUpscale_tile_padding", 32) if isinstance(widgets[12], (int, float, str)) and str(widgets[12]).isdigit() else 32
                api_node["inputs"]["seam_fix_mode"] = widgets[13] if widgets[13] in ["None", "Band Pass", "Half Tile", "Half Tile + Intersections"] else "None"
                api_node["inputs"]["seam_fix_denoise"] = float(widgets[14]) if isinstance(widgets[14], (int, float, str)) and str(widgets[14]).replace('.','',1).isdigit() and widgets[14] != "None" else 1.0
                api_node["inputs"]["seam_fix_width"] = self.safe_int(widgets[15], "UltimateSDUpscale_seam_fix_width", 64) if isinstance(widgets[15], (int, float, str)) and str(widgets[15]).isdigit() else 64
                api_node["inputs"]["seam_fix_mask_blur"] = self.safe_int(widgets[16], "UltimateSDUpscale_seam_fix_mask_blur", 8) if isinstance(widgets[16], (int, float, str)) and str(widgets[16]).isdigit() else 8
                api_node["inputs"]["seam_fix_padding"] = self.safe_int(widgets[17], "UltimateSDUpscale_seam_fix_padding", 16) if isinstance(widgets[17], (int, float, str)) and str(widgets[17]).isdigit() else 16
                api_node["inputs"]["force_uniform_tiles"] = bool(widgets[18]) if len(widgets) > 18 else True
                if len(widgets) > 19:
                    api_node["inputs"]["tiled_decode"] = bool(widgets[19])
                self.logger.info(f"🔧 UPSCALE FIX: UltimateSDUpscale node {node_id} - steps={widgets[3] if len(widgets) > 3 else 'default'}, tiles={widgets[9] if len(widgets) > 9 else 'default'}x{widgets[10] if len(widgets) > 10 else 'default'}")
            
            elif node_type == "FaceDetailer" and len(widgets) >= 20:
                # Complex face detailing node - validate each parameter
                api_node["inputs"]["guide_size"] = self.safe_int(widgets[0], "FaceDetailer_guide_size", 384) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).isdigit() else 384
                api_node["inputs"]["guide_size_for"] = bool(widgets[1]) if len(widgets) > 1 else True
                api_node["inputs"]["max_size"] = self.safe_int(widgets[2], "FaceDetailer_max_size", 1024) if isinstance(widgets[2], (int, float, str)) and str(widgets[2]).isdigit() else 1024
                api_node["inputs"]["seed"] = self.safe_int(widgets[3], "FaceDetailer_seed", 123456) if isinstance(widgets[3], (int, float, str)) and str(widgets[3]).isdigit() else 123456
                api_node["inputs"]["steps"] = self.safe_int(widgets[4], "FaceDetailer_steps", 20) if isinstance(widgets[4], (int, float, str)) and str(widgets[4]).isdigit() else 20
                api_node["inputs"]["cfg"] = float(widgets[5]) if isinstance(widgets[5], (int, float, str)) and str(widgets[5]).replace('.','',1).isdigit() else 7.0
                api_node["inputs"]["sampler_name"] = widgets[6] if isinstance(widgets[6], str) else "euler"
                api_node["inputs"]["scheduler"] = widgets[7] if widgets[7] in ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta", "linear_quadratic", "kl_optimal", "AYS SDXL", "AYS SD1", "AYS SVD"] else "normal"
                api_node["inputs"]["denoise"] = float(widgets[8]) if isinstance(widgets[8], (int, float, str)) and str(widgets[8]).replace('.','',1).isdigit() else 0.5
                api_node["inputs"]["feather"] = self.safe_int(widgets[9], "FaceDetailer_feather", 5) if isinstance(widgets[9], (int, float, str)) and str(widgets[9]).isdigit() else 5
                api_node["inputs"]["noise_mask"] = bool(widgets[10]) if len(widgets) > 10 else True
                api_node["inputs"]["force_inpaint"] = bool(widgets[11]) if len(widgets) > 11 else True
                api_node["inputs"]["bbox_threshold"] = float(widgets[12]) if isinstance(widgets[12], (int, float, str)) and str(widgets[12]).replace('.','',1).isdigit() else 0.5
                api_node["inputs"]["bbox_dilation"] = self.safe_int(widgets[13], "FaceDetailer_bbox_dilation", 10) if isinstance(widgets[13], (int, float, str)) and str(widgets[13]).isdigit() else 10
                api_node["inputs"]["bbox_crop_factor"] = float(widgets[14]) if isinstance(widgets[14], (int, float, str)) and str(widgets[14]).replace('.','',1).isdigit() else 3.0
                api_node["inputs"]["sam_detection_hint"] = widgets[15] if widgets[15] in ["center-1", "horizontal-2", "vertical-2", "rect-4", "diamond-4", "mask-area", "mask-points", "mask-point-bbox", "none"] else "center-1"
                api_node["inputs"]["sam_dilation"] = self.safe_int(widgets[16], "FaceDetailer_sam_dilation", 0) if isinstance(widgets[16], (int, float, str)) and str(widgets[16]).lstrip('-').isdigit() else 0
                api_node["inputs"]["sam_threshold"] = float(widgets[17]) if isinstance(widgets[17], (int, float, str)) and str(widgets[17]).replace('.','',1).isdigit() else 0.93
                api_node["inputs"]["sam_bbox_expansion"] = self.safe_int(widgets[18], "FaceDetailer_sam_bbox_expansion", 0) if isinstance(widgets[18], (int, float, str)) and str(widgets[18]).isdigit() else 0
                api_node["inputs"]["sam_mask_hint_threshold"] = float(widgets[19]) if isinstance(widgets[19], (int, float, str)) and str(widgets[19]).replace('.','',1).isdigit() else 0.7
                if len(widgets) > 20:
                    api_node["inputs"]["sam_mask_hint_use_negative"] = widgets[20] if widgets[20] in ["False", "Small", "Outter"] else "False"
                if len(widgets) > 21:
                    api_node["inputs"]["drop_size"] = self.safe_int(widgets[21], "FaceDetailer_drop_size", 10) if isinstance(widgets[21], (int, float, str)) and str(widgets[21]).isdigit() else 10
                if len(widgets) > 22:
                    api_node["inputs"]["wildcard"] = str(widgets[22])
                if len(widgets) > 23:
                    api_node["inputs"]["cycle"] = self.safe_int(widgets[23], "FaceDetailer_cycle", 1) if isinstance(widgets[23], (int, float, str)) and str(widgets[23]).isdigit() and widgets[23] != "" else 1
                self.logger.info(f"🔧 CONVERSION FIX: FaceDetailer node {node_id} with {len(widgets)} widgets")
            
            elif node_type == "SaveImage" and widgets:
                api_node["inputs"]["filename_prefix"] = widgets[0] if widgets else "ComfyUI"
                self.logger.info(f"🔧 CONVERSION FIX: SaveImage node {node_id}")
            
            elif node_type == "ControlNetLoader" and widgets:
                api_node["inputs"]["control_net_name"] = widgets[0] if widgets else ""
                self.logger.info(f"🔧 CONVERSION FIX: ControlNetLoader node {node_id}")
            
            elif node_type == "ControlNetApplyAdvanced" and len(widgets) >= 3:
                api_node["inputs"]["strength"] = widgets[0] if len(widgets) > 0 else 1.0
                api_node["inputs"]["start_percent"] = widgets[1] if len(widgets) > 1 else 0.0
                api_node["inputs"]["end_percent"] = widgets[2] if len(widgets) > 2 else 1.0
                self.logger.info(f"🔧 CONVERSION FIX: ControlNetApplyAdvanced node {node_id}")
            
            elif node_type == "EmptyLatentImage" and len(widgets) >= 3:
                # Ensure minimum reasonable latent dimensions
                width = max(self.safe_int(widgets[0], "EmptyLatentImage_width", 1024) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).isdigit() else 1024, 512)
                height = max(self.safe_int(widgets[1], "EmptyLatentImage_height", 1024) if isinstance(widgets[1], (int, float, str)) and str(widgets[1]).isdigit() else 1024, 512)
                batch_size = max(self.safe_int(widgets[2], "EmptyLatentImage_batch_size", 1) if isinstance(widgets[2], (int, float, str)) and str(widgets[2]).isdigit() else 1, 1)
                
                api_node["inputs"]["width"] = width
                api_node["inputs"]["height"] = height
                api_node["inputs"]["batch_size"] = batch_size
                self.logger.info(f"🔧 CONVERSION FIX: EmptyLatentImage node {node_id} {width}x{height}x{batch_size}")
            
            elif node_type == "UltralyticsDetectorProvider" and widgets:
                api_node["inputs"]["model_name"] = widgets[0] if widgets else "bbox/face_yolov8m.pt"
                self.logger.info(f"🔧 CONVERSION FIX: UltralyticsDetectorProvider node {node_id}")
            
            elif node_type == "Upscale Model Loader" and widgets:
                api_node["inputs"]["model_name"] = widgets[0] if widgets else ""
                self.logger.info(f"🔧 CONVERSION FIX: Upscale Model Loader node {node_id}")
            
            # Generic fallback for nodes with widgets but no specific mapping
            elif node_type == "NormalMapSimple" and widgets:
                # Handle NormalMapSimple with scale_XY parameter
                if len(widgets) >= 1:
                    api_node["inputs"]["scale_XY"] = float(widgets[0]) if isinstance(widgets[0], (int, float, str)) and str(widgets[0]).replace('.','',1).isdigit() else 1.0
                    self.logger.info(f"🔧 CONVERSION FIX: NormalMapSimple node {node_id} scale_XY={api_node['inputs']['scale_XY']}")
            
            elif node_type == "SetUnionControlNetType" and widgets:
                # Handle SetUnionControlNetType - needs "type" parameter, not "value"
                if len(widgets) >= 1:
                    api_node["inputs"]["type"] = widgets[0] if widgets[0] in ["depth", "normal", "canny", "openpose", "mlsd", "lineart", "scribble", "fake_scribble", "seg"] else "depth"
                    self.logger.info(f"🔧 CONVERSION FIX: SetUnionControlNetType node {node_id} type={api_node['inputs']['type']}")
            
            elif node_type == "Image Comparer (rgthree)" and widgets:
                # Handle Image Comparer - skip complex dict widgets that cause ComfyUI errors
                # The rgthree Image Comparer node has complex dict structures that can't be serialized
                self.logger.info(f"🔧 CONVERSION FIX: Skipping Image Comparer (rgthree) node {node_id} - uses complex dict widgets")
                # Only include basic inputs, skip the problematic "value" widget
                # The node will use default comparison behavior
            
            elif node_type == "Constant Number" and widgets:
                # Handle Constant Number node - needs number_type and number inputs
                if len(widgets) >= 2:
                    number_type = widgets[0] if widgets[0] in ["int", "float"] else "float"
                    number_value = widgets[1] if len(widgets) > 1 else 1.0
                    api_node["inputs"]["number_type"] = number_type
                    api_node["inputs"]["number"] = float(number_value) if number_type == "float" else self.safe_int(number_value, "ConstantNumber_number", 1)
                    self.logger.info(f"🔧 CONVERSION FIX: Constant Number node {node_id} type={number_type} value={api_node['inputs']['number']}")
            
            elif node_type == "Bridge Preview UI" and widgets:
                # Handle Bridge Preview UI node - convert to PreviewImage for ComfyUI compatibility
                api_node["class_type"] = "PreviewImage"
                # Bridge Preview UI nodes will be captured by the app through image callbacks
                # Add special metadata to identify as bridge preview
                api_node["_meta"] = {
                    "title": widgets[0] if widgets else "Bridge Preview",
                    "bridge_preview": True
                }
                self.logger.info(f"🔧 BRIDGE PREVIEW: Converting Bridge Preview UI node {node_id} to PreviewImage")
                    
            elif node_type == "Hy3DSetMeshPBRTextures":
                # CORRECT FIX: Based on actual node definition from GitHub
                # INPUT_TYPES: "trimesh": (TRIMESH,), "image": (IMAGE,), "texture": (dropdown selection)
                # The "texture" input is NOT an image connection but a string parameter!
                self.logger.info(f"🔧 DEBUG: Hy3DSetMeshPBRTextures node {node_id} - setting texture type parameter")
                
                if widgets and len(widgets) >= 1:
                    texture_type = widgets[0]  # e.g., "normal"
                    # The "texture" input expects a string value, not an image connection
                    api_node["inputs"]["texture"] = texture_type
                    self.logger.info(f"🔧 PBR FIX: Set texture type parameter to '{texture_type}'")
                else:
                    self.logger.warning(f"Hy3DSetMeshPBRTextures node {node_id} has no widgets_values")
            
            elif widgets and node_type not in ["Note", "Reroute"] and not any("Anything Everywhere" in node_type for _ in [1]) and "Image Comparer" not in node_type:
                if len(widgets) == 1:
                    api_node["inputs"]["value"] = widgets[0]
                    self.logger.warning(f"Generic widget mapping for {node_type} node {node_id}: value={widgets[0]}")
            
            api_workflow[node_id] = api_node
        
        # Second pass: Add connections based on links
        link_map = self._build_link_map(ui_workflow)
        self.logger.info(f"Built link map with {len(link_map)} links")
        
        # Build a map to resolve Reroute nodes
        reroute_map = self._build_reroute_map(ui_workflow)
        self.logger.info(f"Built reroute resolution map with {len(reroute_map)} entries")
        
        # Build bypass map for nodes that need to be skipped
        bypass_map = self._build_bypass_map(ui_workflow)
        self.logger.info(f"Built bypass map with {len(bypass_map)} bypassed nodes")
        
        for node in ui_workflow.get("nodes", []):
            node_id = str(node.get("id", ""))
            node_type = node.get("type", "")
            
            # Skip Note nodes here too
            if node_type == "Note":
                continue
            
            # Skip if this node wasn't added to the API workflow
            if node_id not in api_workflow:
                continue
                
            api_node = api_workflow[node_id]
            
            # Add input connections
            for input_def in node.get("inputs", []):
                input_name = input_def.get("name", "")
                if "link" in input_def and input_def["link"] is not None:
                    link_id = input_def["link"]
                    if link_id in link_map:
                        source_node_id, output_index = link_map[link_id]
                        
                        # If source is a Reroute node, resolve to its ultimate source
                        if source_node_id in reroute_map:
                            resolved_source = reroute_map[source_node_id]
                            source_node_id, output_index = resolved_source
                            self.logger.info(f"Resolved Reroute chain: node {node_id} input '{input_name}' -> {source_node_id}[{output_index}]")
                        
                        # Check if source node was bypassed and removed from API workflow
                        original_source_node_id = source_node_id
                        attempts = 0
                        max_attempts = 10  # Prevent infinite loops
                        
                        # Recursively resolve through bypassed nodes
                        while source_node_id not in api_workflow and attempts < max_attempts:
                            attempts += 1
                            resolved = False
                            
                            # Try to resolve through bypass map with output index
                            lookup_key = f"{source_node_id}_{output_index}"
                            if lookup_key in bypass_map:
                                resolved_source = bypass_map[lookup_key]
                                if resolved_source:
                                    prev_node_id = source_node_id
                                    source_node_id, output_index = resolved_source
                                    self.logger.info(f"Resolved through bypassed node {prev_node_id} output {output_index} (attempt {attempts}): -> {source_node_id}[{output_index}]")
                                    resolved = True
                            # Fallback: check if we have a dict mapping for this node
                            elif source_node_id in bypass_map and isinstance(bypass_map[source_node_id], dict):
                                mapping = bypass_map[source_node_id]
                                # Determine which output based on index (0=model, 1=clip for LoRA)
                                if output_index == 0 and "model" in mapping and mapping["model"]:
                                    source_node_id, output_index = mapping["model"]
                                    self.logger.info(f"Resolved MODEL through bypassed LoRA (attempt {attempts}): -> {source_node_id}[{output_index}]")
                                    resolved = True
                                elif output_index == 1 and "clip" in mapping and mapping["clip"]:
                                    source_node_id, output_index = mapping["clip"]
                                    self.logger.info(f"Resolved CLIP through bypassed LoRA (attempt {attempts}): -> {source_node_id}[{output_index}]")
                                    resolved = True
                            
                            if not resolved:
                                self.logger.warning(f"Could not resolve connection from bypassed node {source_node_id} to {node_id} after {attempts} attempts")
                                break
                        
                        # Skip if we couldn't resolve to a valid node
                        if source_node_id not in api_workflow:
                            self.logger.error(f"Failed to resolve connection: {node_id} input '{input_name}' cannot find source node {source_node_id}")
                            continue
                        
                        # Check if this input already has a direct value that should be preserved
                        # Some nodes like EmptyLatentImage should keep their direct values instead of connections
                        preserve_direct_values = {
                            "EmptyLatentImage": ["width", "height", "batch_size"],
                            "PrimitiveInt": ["value"],
                            "ConstantNumber": ["value"],
                        }
                        
                        node_type = api_node.get("class_type", "")
                        should_preserve = node_type in preserve_direct_values and input_name in preserve_direct_values[node_type]
                        
                        if should_preserve and input_name in api_node["inputs"]:
                            # Keep the direct value, don't overwrite with connection
                            self.logger.info(f"🔧 PRESERVING direct value for {node_type} node {node_id} input '{input_name}': {api_node['inputs'][input_name]}")
                        else:
                            # Use connection as normal
                            api_node["inputs"][input_name] = [str(source_node_id), output_index]
                    else:
                        self.logger.warning(f"Link {link_id} not found in link_map for node {node_id}")
                else:
                    # Some inputs might not have links (None or missing)
                    if input_def.get("link") is None and node_type != "Reroute":
                        self.logger.debug(f"Node {node_id} input '{input_name}' has no link (None)")
        
        # Third pass: Handle special connection nodes
        # Handle Anything Everywhere nodes - distribute values globally
        distributed_connections = self._handle_anything_everywhere_nodes(ui_workflow, api_workflow, link_map)
        if distributed_connections:
            self.logger.info(f"Applying {len(distributed_connections)} distributed connections from Anything Everywhere nodes")
            self._apply_distributed_connections(api_workflow, distributed_connections)
        
        # Handle SetNode/GetNode connections
        setget_connections = self._handle_setnode_getnode(ui_workflow, api_workflow, link_map)
        if setget_connections:
            self.logger.info(f"Resolving {len(setget_connections)} SetNode/GetNode connections")
            self._apply_setget_connections(api_workflow, setget_connections)
        
        # Debug: List final API nodes
        final_node_ids = list(api_workflow.keys())
        self.logger.info(f"Final API workflow node IDs: {final_node_ids}")
        self.logger.info(f"Converted UI workflow to API format with {len(api_workflow)} nodes")
        
        # Debug: Log the complete API workflow
        self.logger.debug("API Workflow structure:")
        for node_id, node_data in api_workflow.items():
            self.logger.debug(f"  Node {node_id}: {node_data.get('class_type')} - inputs: {list(node_data.get('inputs', {}).keys())}")
        
        # Ensure SaveImage node exists and is properly configured
        self._ensure_save_image_node(api_workflow)
        
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
    
    def _build_reroute_map(self, ui_workflow: Dict[str, Any]) -> Dict[str, tuple]:
        """Build a map to resolve Reroute nodes to their ultimate sources"""
        reroute_map = {}
        
        # Find all Reroute nodes and their connections
        reroute_nodes = {}
        for node in ui_workflow.get("nodes", []):
            if node.get("type") == "Reroute":
                node_id = str(node.get("id", ""))
                reroute_nodes[node_id] = node
        
        # For each Reroute node, resolve its ultimate source
        for reroute_id, reroute_node in reroute_nodes.items():
            source = self._resolve_reroute_source(reroute_node, reroute_nodes, ui_workflow)
            if source:
                reroute_map[reroute_id] = source
                self.logger.debug(f"Reroute {reroute_id} resolves to {source}")
        
        return reroute_map
    
    def _build_bypass_map(self, ui_workflow: Dict[str, Any]) -> Dict[str, tuple]:
        """Build a map to resolve connections through bypassed nodes"""
        bypass_map = {}
        link_map = self._build_link_map(ui_workflow)
        
        # Find all bypassed nodes (mode: 4)
        for node in ui_workflow.get("nodes", []):
            if node.get("mode", 0) == 4:
                node_id = str(node.get("id", ""))
                node_type = node.get("type", "")
                
                # For LoRA nodes, map outputs to their corresponding inputs
                if node_type == "LoraLoader":
                    # Find what connects to this node's inputs
                    input_sources = {}
                    for input_def in node.get("inputs", []):
                        input_name = input_def.get("name")
                        if "link" in input_def and input_def["link"] is not None:
                            link_id = input_def["link"]
                            if link_id in link_map:
                                source_node_id, output_index = link_map[link_id]
                                input_sources[input_name] = (source_node_id, output_index)
                    
                    # Map this node's outputs to the corresponding inputs
                    # LoRA has two outputs: 0=MODEL, 1=CLIP
                    # We need to map based on which output is being requested
                    if "model" in input_sources:
                        bypass_map[f"{node_id}_0"] = input_sources["model"]  # MODEL output (index 0)
                    if "clip" in input_sources:
                        bypass_map[f"{node_id}_1"] = input_sources["clip"]  # CLIP output (index 1)
                    
                    # Also store a simple mapping for easy lookup
                    bypass_map[node_id] = {"model": input_sources.get("model"), "clip": input_sources.get("clip")}
                    
                    self.logger.info(f"Bypassed LoRA node {node_id} will pass through: {input_sources}")
        
        return bypass_map
    
    def _resolve_reroute_source(self, reroute_node: Dict[str, Any], reroute_nodes: Dict[str, Any], ui_workflow: Dict[str, Any]) -> Optional[tuple]:
        """Resolve a Reroute node to its ultimate source (non-Reroute)"""
        visited = set()
        current_node = reroute_node
        
        while True:
            current_id = str(current_node.get("id", ""))
            if current_id in visited:  # Circular reference
                self.logger.warning(f"Circular Reroute reference detected at node {current_id}")
                return None
            visited.add(current_id)
            
            # Get the input of this Reroute node
            inputs = current_node.get("inputs", [])
            if not inputs:
                return None
            
            input_def = inputs[0]  # Reroute nodes have one input
            if "link" not in input_def or input_def["link"] is None:
                return None
            
            link_id = input_def["link"]
            
            # Find the source of this link
            source_node_id = None
            output_index = 0
            
            for node in ui_workflow.get("nodes", []):
                for out_idx, output in enumerate(node.get("outputs", [])):
                    if output.get("links") and link_id in output["links"]:
                        source_node_id = str(node.get("id", ""))
                        output_index = out_idx
                        break
                if source_node_id:
                    break
            
            if not source_node_id:
                return None
            
            # If source is not a Reroute, we found our answer
            if source_node_id not in reroute_nodes:
                return (source_node_id, output_index)
            
            # Continue following the Reroute chain
            current_node = reroute_nodes[source_node_id]
    
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
        
        # TEXTURE FIX: Preserve mesh nodes in API format too
        # Check all nodes for mesh preservation (though mesh injection happens before this)
        mesh_nodes_found = []
        for node_id, node_data in workflow_copy.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type")
                if class_type == "Hy3DLoadMesh":
                    mesh_path = node_data.get("inputs", {}).get("glb_path", "NO_GLB_PATH")
                    mesh_nodes_found.append(f"Hy3DLoadMesh Node {node_id}: {mesh_path}")
                elif class_type == "Hy3DUploadMesh":
                    mesh_filename = node_data.get("inputs", {}).get("mesh", "NO_MESH_INPUT")
                    mesh_nodes_found.append(f"Hy3DUploadMesh Node {node_id}: {mesh_filename}")
        
        if mesh_nodes_found:
            self.logger.info(f"🔧 TEXTURE FIX: API format mesh nodes preserved: {mesh_nodes_found}")
        
        return workflow_copy
    
    def _inject_params_ui_format(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Inject parameters into UI format workflow (with nodes array)"""
        workflow_copy = deepcopy(workflow)
        
        # TEXTURE FIX: Log mesh nodes before parameter injection to track preservation
        mesh_nodes_before = []
        for node in workflow_copy.get("nodes", []):
            node_type = node.get("type")
            if node_type == "Hy3DLoadMesh":
                widgets = node.get("widgets_values", [])
                mesh_path = widgets[0] if widgets else "NO_WIDGETS"
                mesh_nodes_before.append(f"Hy3DLoadMesh Node {node.get('id')}: {mesh_path}")
            elif node_type == "Hy3DUploadMesh":
                widgets = node.get("widgets_values", [])
                mesh_filename = widgets[0] if widgets else "NO_WIDGETS"
                mesh_nodes_before.append(f"Hy3DUploadMesh Node {node.get('id')}: {mesh_filename}")
        
        if mesh_nodes_before:
            self.logger.info(f"🔧 TEXTURE FIX: Mesh nodes before parameter injection: {mesh_nodes_before}")
        
        # Reset LoRA usage tracking for dynamic assignment
        for i in range(1, 10):
            if hasattr(self, f"_lora{i}_used"):
                delattr(self, f"_lora{i}_used")
        
        for node in workflow_copy["nodes"]:
            node_id = node.get("id")
            node_type = node.get("type")
            widgets = node.get("widgets_values", [])
            
            # Debug logging for LoRA nodes
            if node_type == "LoraLoader":
                self.logger.debug(f"Processing LoraLoader node {node_id} with widgets: {widgets}")
            
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
            
            # Handle LoRA Loaders - inject dynamically based on available parameters
            elif node_type == "LoraLoader":
                # Try to find a LoRA parameter set that matches this node's current model
                current_widgets = node.get("widgets_values", [])
                current_model = current_widgets[0] if current_widgets else ""
                
                lora_assigned = False
                # Try to match by model name first
                for i in range(1, 10):  # Support up to 10 LoRAs
                    lora_key = f"lora{i}"
                    if f"{lora_key}_model" in params:
                        if params[f"{lora_key}_model"] == current_model:
                            default_strength = current_widgets[1] if len(current_widgets) > 1 else 1.0
                            self._inject_lora_ui_format(node, params, lora_key, default_strength)
                            lora_assigned = True
                            break
                
                # If no match found, use the first available LoRA parameters
                if not lora_assigned:
                    for i in range(1, 10):  # Support up to 10 LoRAs
                        lora_key = f"lora{i}"
                        if f"{lora_key}_model" in params and not getattr(self, f"_{lora_key}_used", False):
                            default_strength = current_widgets[1] if len(current_widgets) > 1 else 1.0
                            self._inject_lora_ui_format(node, params, lora_key, default_strength)
                            setattr(self, f"_{lora_key}_used", True)  # Mark as used
                            break
            
            # Handle FluxGuidance node
            elif node_type == "FluxGuidance":
                # FluxGuidance uses CFG value as guidance
                if "cfg" in params and widgets:
                    widgets[0] = params["cfg"]
                    self.logger.info(f"Injected guidance (cfg) into FluxGuidance node {node_id}: {widgets[0]}")
                elif "cfg" in params:
                    node["widgets_values"] = [params["cfg"]]
                    self.logger.info(f"Created guidance widgets for FluxGuidance node {node_id}: {params['cfg']}")
            
            # CRITICAL FIX: Handle Hy3DLoadMesh node to preserve mesh injection
            elif node_type == "Hy3DLoadMesh":
                # DON'T modify mesh nodes during parameter injection
                # The mesh path was already injected by inject_3d_model_path()
                # We just need to preserve it during parameter injection
                if widgets:
                    mesh_path = widgets[0] if widgets else ""
                    self.logger.info(f"🔧 TEXTURE FIX: Preserving mesh path in Hy3DLoadMesh node {node_id}: {mesh_path}")
                    # Keep existing widgets as-is to preserve mesh injection
                else:
                    self.logger.warning(f"Hy3DLoadMesh node {node_id} has no widgets - mesh injection may have been lost")
            
            # LEGACY: Handle Hy3DUploadMesh node to preserve mesh injection
            elif node_type == "Hy3DUploadMesh":
                # DON'T modify mesh nodes during parameter injection
                # The mesh filename was already injected by inject_3d_model_path()
                # We just need to preserve it during parameter injection
                if widgets:
                    mesh_filename = widgets[0] if widgets else ""
                    self.logger.info(f"🔧 TEXTURE FIX: Preserving mesh filename in Hy3DUploadMesh node {node_id}: {mesh_filename}")
                    # Keep existing widgets as-is to preserve mesh injection
                else:
                    self.logger.warning(f"Hy3DUploadMesh node {node_id} has no widgets - mesh injection may have been lost")
        
        # TEXTURE FIX: Log mesh nodes after parameter injection to confirm preservation
        mesh_nodes_after = []
        for node in workflow_copy.get("nodes", []):
            node_type = node.get("type")
            if node_type == "Hy3DLoadMesh":
                widgets = node.get("widgets_values", [])
                mesh_path = widgets[0] if widgets else "NO_WIDGETS"
                mesh_nodes_after.append(f"Hy3DLoadMesh Node {node.get('id')}: {mesh_path}")
            elif node_type == "Hy3DUploadMesh":
                widgets = node.get("widgets_values", [])
                mesh_filename = widgets[0] if widgets else "NO_WIDGETS"
                mesh_nodes_after.append(f"Hy3DUploadMesh Node {node.get('id')}: {mesh_filename}")
        
        if mesh_nodes_after:
            self.logger.info(f"🔧 TEXTURE FIX: Mesh nodes after parameter injection: {mesh_nodes_after}")
        
        return workflow_copy
    
    def _inject_lora_ui_format(self, node: Dict[str, Any], params: Dict[str, Any], lora_prefix: str, default_strength: float):
        """Inject LoRA parameters into UI format node"""
        node_id = node.get("id")
        widgets = node.get("widgets_values", ["", default_strength, default_strength])
        
        # Log current widget values
        self.logger.debug(f"Node {node_id} current widgets: {widgets}")
        
        lora_model_key = f"{lora_prefix}_model"
        lora_strength_key = f"{lora_prefix}_strength"
        lora_active_key = f"{lora_prefix}_active"
        lora_bypassed_key = f"{lora_prefix}_bypassed"
        
        # Check if LoRA is bypassed first
        if params.get(lora_bypassed_key, False):
            # LoRA is bypassed - set empty string and bypass mode
            if not widgets:
                widgets = ["", default_strength, default_strength]
            widgets[0] = ""  # Empty string for bypassed
            node["widgets_values"] = widgets
            node["mode"] = 4  # Set to bypass mode
            self.logger.info(f"Bypassed {lora_prefix} in node {node_id}")
        # Check if LoRA is active and has a valid model
        elif params.get(lora_active_key, True) and lora_model_key in params:
            lora_model = params[lora_model_key]
            if lora_model and lora_model != "None":
                # Store original value for comparison
                original_value = widgets[0] if widgets else ""
                
                # Ensure we have a proper widgets array
                if not widgets:
                    widgets = ["", default_strength, default_strength]
                
                # widgets_values format: [lora_name, strength_model, strength_clip]
                widgets[0] = lora_model
                if lora_strength_key in params:
                    strength = params[lora_strength_key]
                    widgets[1] = strength  # strength_model
                    widgets[2] = strength  # strength_clip
                
                node["widgets_values"] = widgets
                # Clear bypass mode when activating a LoRA
                if "mode" in node:
                    node["mode"] = 0  # Set to active mode
                self.logger.info(f"Injected {lora_prefix} into node {node_id}: '{lora_model}' @ {widgets[1]} (was: '{original_value}')")
            else:
                # Disable LoRA by setting empty string (not "None")
                if not widgets:
                    widgets = ["", default_strength, default_strength]
                widgets[0] = ""  # Empty string, not "None"
                node["widgets_values"] = widgets
                # Set bypass mode when disabling
                node["mode"] = 4  # Set to bypass mode
                self.logger.info(f"Disabled {lora_prefix} in node {node_id} (empty string for 'None' selection)")
        elif not params.get(lora_active_key, True):
            # LoRA explicitly disabled
            if not widgets:
                widgets = ["", default_strength, default_strength]
            widgets[0] = ""  # Empty string, not "None"
            node["widgets_values"] = widgets
            # Set bypass mode when explicitly disabled
            node["mode"] = 4  # Set to bypass mode
            self.logger.info(f"Disabled {lora_prefix} in node {node_id} (explicitly disabled)")
            self.logger.info(f"Disabled {lora_prefix} (inactive)")

    def inject_parameters_3d(self, workflow: Dict[str, Any], params: Dict[str, Any], image_path: str = None) -> Dict[str, Any]:
        """Inject parameters into 3D generation workflow"""
        workflow_copy = deepcopy(workflow)
        
        self.logger.info(f"Injecting 3D parameters. Workflow format check: has 'nodes'={('nodes' in workflow_copy)}")
        self.logger.info(f"Image path provided: {image_path}")
        
        # Check if this is UI format and convert if needed
        if "nodes" in workflow_copy and isinstance(workflow_copy["nodes"], list):
            self.logger.info("Processing UI format workflow for 3D generation")
            # Inject parameters into UI format first
            ui_workflow_with_params = self._inject_params_3d_ui_format(workflow_copy, params, image_path)
            # Then convert to API format for ComfyUI execution
            api_workflow = self._convert_ui_to_api_format(ui_workflow_with_params)
            self.logger.info(f"Converted 3D UI workflow to API format with {len(api_workflow)} nodes")
            return api_workflow
        
        # Handle API format directly
        self.logger.info("Processing API format workflow for 3D generation")
        return self._inject_params_3d_api_format(workflow_copy, params, image_path)
    
    def _inject_params_3d_ui_format(self, workflow: Dict[str, Any], params: Dict[str, Any], image_path: str = None) -> Dict[str, Any]:
        """Inject 3D parameters into UI format workflow"""
        workflow_copy = deepcopy(workflow)
        
        for node in workflow_copy["nodes"]:
            node_id = node.get("id")
            node_type = node.get("type")
            widgets = node.get("widgets_values", [])
            
            # LoadImage node - inject selected image (handle any node ID)
            if node_type == "LoadImage" and image_path:
                import os
                import shutil
                from pathlib import Path
                
                self.logger.info(f"Found LoadImage node {node_id}, injecting image: {image_path}")
                
                image_filename = os.path.basename(image_path)
                source_path = Path(image_path)
                
                # Copy image to ComfyUI input directory if needed
                # Try multiple possible ComfyUI input directories
                possible_input_dirs = [
                    Path("D:/Comfy3D_WinPortable/ComfyUI/input"),
                    Path("D:/ComfyUI_windows_portable/ComfyUI/input"),
                    Path("C:/ComfyUI/input"),
                    Path.home() / "ComfyUI" / "input"
                ]
                
                comfyui_input_dir = None
                for dir_path in possible_input_dirs:
                    if dir_path.exists():
                        comfyui_input_dir = dir_path
                        self.logger.info(f"Found ComfyUI input directory: {comfyui_input_dir}")
                        break
                
                if comfyui_input_dir:
                    dest_path = comfyui_input_dir / image_filename
                    if source_path.exists() and not dest_path.exists():
                        try:
                            shutil.copy2(source_path, dest_path)
                            self.logger.info(f"Copied image to ComfyUI input: {dest_path}")
                        except Exception as e:
                            self.logger.error(f"Failed to copy image to ComfyUI input: {e}")
                    else:
                        self.logger.info(f"Image already exists in ComfyUI input or source doesn't exist")
                else:
                    self.logger.warning(f"ComfyUI input directory not found in any of the expected locations")
                
                if not widgets:
                    widgets = [image_filename, "image"]
                    node["widgets_values"] = widgets
                else:
                    widgets[0] = image_filename
                self.logger.info(f"Injected image path into LoadImage node {node_id}: {image_filename}")
            
            # Node 53: Hy3DGenerateMesh - mesh generation parameters
            elif node_id == 53 and node_type == "Hy3DGenerateMesh":
                if not widgets:
                    widgets = [5.5, 50, 123, "fixed", "FlowMatchEulerDiscreteScheduler", True]
                    node["widgets_values"] = widgets
                
                # widgets format: [guidance_scale, inference_steps, seed, seed_control, scheduler, use_karras]
                if "guidance_scale_3d" in params:
                    widgets[0] = params["guidance_scale_3d"]
                if "inference_steps_3d" in params:
                    widgets[1] = params["inference_steps_3d"]
                if "seed_3d" in params and params["seed_3d"] >= 0:
                    widgets[2] = params["seed_3d"]
                if "scheduler_3d" in params:
                    widgets[4] = params["scheduler_3d"]
                
                self.logger.info(f"Injected Hy3DGenerateMesh params into node {node_id}")
            
            # Node 54: Hy3DVAEDecode - VAE parameters
            elif node_id == 54 and node_type == "Hy3DVAEDecode":
                if not widgets:
                    widgets = [1.01, 384, 8000, 0, "mc", True, True]
                    node["widgets_values"] = widgets
                
                # widgets format: [simplify_ratio, resolution, max_faces, start_resolution, algorithm, remove_dups, merge_vertices]
                if "simplify_ratio" in params:
                    widgets[0] = params["simplify_ratio"]
                if "mesh_resolution" in params:
                    widgets[1] = params["mesh_resolution"]
                if "max_faces" in params:
                    widgets[2] = params["max_faces"]
                
                self.logger.info(f"Injected Hy3DVAEDecode params into node {node_id}")
            
            # Node 55: Hy3DPostprocessMesh - post-processing parameters
            elif node_id == 55 and node_type == "Hy3DPostprocessMesh":
                if not widgets:
                    widgets = [True, True, True, 50000, False]
                    node["widgets_values"] = widgets
                
                # widgets format: [remove_duplicates, merge_vertices, optimize_mesh, target_faces, use_mask]
                if "remove_duplicates" in params:
                    widgets[0] = params["remove_duplicates"]
                if "merge_vertices" in params:
                    widgets[1] = params["merge_vertices"]
                if "optimize_mesh" in params:
                    widgets[2] = params["optimize_mesh"]
                if "target_faces" in params:
                    widgets[3] = params["target_faces"]
                
                self.logger.info(f"Injected Hy3DPostprocessMesh params into node {node_id}")
            
            # Node 72: Hy3DDelightImage - delighting parameters
            elif node_id == 72 and node_type == "Hy3DDelightImage":
                if not widgets:
                    widgets = [50, 512, 512, 1.5, 1, 42]
                    node["widgets_values"] = widgets
                
                # widgets format: [delight_steps, width, height, guidance_scale, num_images, seed]
                if "delight_steps" in params:
                    widgets[0] = params["delight_steps"]
                if "delight_guidance" in params:
                    widgets[3] = params["delight_guidance"]
                
                self.logger.info(f"Injected Hy3DDelightImage params into node {node_id}")
            
            # Node 56: SolidMask - background level parameter
            elif node_id == 56 and node_type == "SolidMask":
                if not widgets:
                    widgets = [0.5, 512, 512]
                    node["widgets_values"] = widgets
                
                if "background_level" in params:
                    widgets[0] = params["background_level"]
                
                self.logger.info(f"Injected SolidMask background level into node {node_id}")
            
            # Additional nodes for UV workflow
            # Node 62: Hy3DRenderMultiView
            elif node_id == 62 and node_type == "Hy3DRenderMultiView":
                if not widgets:
                    widgets = [512, 1024]  # default render_size, texture_size
                    node["widgets_values"] = widgets
                
                if "render_size" in params:
                    widgets[0] = params["render_size"]
                if "texture_size" in params:
                    widgets[1] = params["texture_size"]
                
                self.logger.info(f"Injected Hy3DRenderMultiView params into node {node_id}")
            
            # Node 63: Hy3DCameraConfig
            elif node_id == 63 and node_type == "Hy3DCameraConfig":
                if not widgets:
                    # Order: [camera_elevations, camera_azimuths, view_weights, camera_distance, ortho_scale]
                    widgets = ["0,30,90,120,150,180,210,240,270,300,330", "0,45,90,135,180,225,270,315", "1,1,1,1,1,1,1,1,1,1,1,1", 1.5, 1.0]
                    node["widgets_values"] = widgets
                
                # Fix camera values - the ComfyUI node requires specific angle values
                # The node's dictionary only accepts: -90, -45, -20, 0, 20, 45, 90
                if widgets and len(widgets) >= 2:
                    # IMPORTANT: The Hunyuan3D node has a bug where it expects azimuth values
                    # to be exactly from the set: {-90, -45, -20, 0, 20, 45, 90}
                    # Using any other values (like 270, 180) causes KeyError
                    
                    # Use only the supported angle values for 6 views
                    widgets[0] = "0, 20, 45, -20, -45, 0"      # Elevation angles
                    widgets[1] = "0, 45, 90, -45, -90, 0"      # Azimuth - ONLY use supported values!
                    
                    # Ensure we have matching weights for 6 views
                    if len(widgets) > 2:
                        widgets[2] = "1, 1, 1, 1, 1, 1"  # Equal weight for all views
                
                # Preserve existing string values, only update numeric parameters
                if "camera_distance" in params:
                    widgets[3] = params["camera_distance"]
                if "ortho_scale" in params:
                    widgets[4] = params["ortho_scale"]
                
                self.logger.info(f"Injected Hy3DCameraConfig params into node {node_id}")
            
            # Node 82: Hy3DSampleMultiView
            elif node_id == 82 and node_type == "Hy3DSampleMultiView":
                if not widgets:
                    widgets = [42, 20, 512]  # seed, steps, view_size
                    node["widgets_values"] = widgets
                
                # Validate integer values to prevent "Python int too large to convert to C long"
                if "sample_seed" in params:
                    widgets[0] = self.safe_int(params["sample_seed"], "UI_sample_seed", 42)
                if "sample_steps" in params:
                    widgets[1] = self.safe_int(params["sample_steps"], "UI_sample_steps", 20)
                if "view_size" in params:
                    widgets[2] = self.safe_int(params["view_size"], "UI_view_size", 512)
                
                self.logger.info(f"Injected Hy3DSampleMultiView params into node {node_id}")
            
            # Hy3DExportMesh nodes - preserve original save_file settings
            elif node_type == "Hy3DExportMesh":
                if not widgets:
                    widgets = ["3D/Hy3D", "glb", True]  # Default with texture saving enabled
                    node["widgets_values"] = widgets
                    self.logger.info(f"Set default Hy3DExportMesh values for node {node_id}")
                else:
                    # RESPECT original save_file setting - DO NOT override
                    original_save_file = widgets[2] if len(widgets) >= 3 else True
                    self.logger.info(f"Hy3DExportMesh node {node_id}: preserving save_file={original_save_file}")
        
        return workflow_copy
    
    def _inject_params_3d_api_format(self, workflow: Dict[str, Any], params: Dict[str, Any], image_path: str = None) -> Dict[str, Any]:
        """Inject 3D parameters into API format workflow"""
        workflow_copy = deepcopy(workflow)
        
        # Find LoadImage node (could be node 92, 93, or any ID)
        load_image_node_id = None
        for node_id, node_data in workflow_copy.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "LoadImage":
                load_image_node_id = node_id
                break
        
        # Inject image into LoadImage node
        if load_image_node_id and image_path:
            import os
            import shutil
            from pathlib import Path
            
            image_filename = os.path.basename(image_path)
            source_path = Path(image_path)
            
            # Copy image to ComfyUI input directory if needed
            # Try multiple possible ComfyUI input directories
            possible_input_dirs = [
                Path("D:/Comfy3D_WinPortable/ComfyUI/input"),
                Path("D:/ComfyUI_windows_portable/ComfyUI/input"),
                Path("C:/ComfyUI/input"),
                Path.home() / "ComfyUI" / "input"
            ]
            
            comfyui_input_dir = None
            for dir_path in possible_input_dirs:
                if dir_path.exists():
                    comfyui_input_dir = dir_path
                    self.logger.info(f"Found ComfyUI input directory: {comfyui_input_dir}")
                    break
            
            if comfyui_input_dir:
                dest_path = comfyui_input_dir / image_filename
                if source_path.exists() and not dest_path.exists():
                    try:
                        shutil.copy2(source_path, dest_path)
                        self.logger.info(f"Copied image to ComfyUI input: {dest_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to copy image to ComfyUI input: {e}")
                else:
                    self.logger.info(f"Image already exists in ComfyUI input or source doesn't exist")
            else:
                self.logger.warning(f"ComfyUI input directory not found in any of the expected locations")
            
            # Ensure inputs dict exists and inject image parameter
            if "inputs" not in workflow_copy[load_image_node_id]:
                workflow_copy[load_image_node_id]["inputs"] = {}
            workflow_copy[load_image_node_id]["inputs"]["image"] = image_filename
            self.logger.info(f"Injected image into LoadImage node {load_image_node_id}: {image_filename}")
        else:
            if not load_image_node_id:
                self.logger.warning("No LoadImage node found in workflow")
            if not image_path:
                self.logger.warning("No image path provided for 3D generation")
        
        # Node 53: Hy3DGenerateMesh
        if "53" in workflow_copy:
            inputs = workflow_copy["53"]["inputs"]
            if "guidance_scale_3d" in params:
                inputs["guidance_scale"] = params["guidance_scale_3d"]
            if "inference_steps_3d" in params:
                inputs["steps"] = params["inference_steps_3d"]
            if "seed_3d" in params and params["seed_3d"] >= 0:
                inputs["seed"] = params["seed_3d"]
            if "scheduler_3d" in params:
                inputs["scheduler"] = params["scheduler_3d"]
            self.logger.info(f"Injected Hy3DGenerateMesh params")
        
        # Node 54: Hy3DVAEDecode
        if "54" in workflow_copy:
            inputs = workflow_copy["54"]["inputs"]
            if "simplify_ratio" in params:
                inputs["simplify_ratio"] = params["simplify_ratio"]
            if "mesh_resolution" in params:
                inputs["resolution"] = params["mesh_resolution"]
            if "max_faces" in params:
                inputs["max_faces"] = params["max_faces"]
            self.logger.info(f"Injected Hy3DVAEDecode params")
        
        # Node 55: Hy3DPostprocessMesh
        if "55" in workflow_copy:
            inputs = workflow_copy["55"]["inputs"]
            if "remove_duplicates" in params:
                inputs["remove_duplicates"] = params["remove_duplicates"]
            if "merge_vertices" in params:
                inputs["merge_vertices"] = params["merge_vertices"]
            if "optimize_mesh" in params:
                inputs["optimize_mesh"] = params["optimize_mesh"]
            if "target_faces" in params:
                inputs["target_faces"] = params["target_faces"]
            self.logger.info(f"Injected Hy3DPostprocessMesh params")
        
        # Node 72: Hy3DDelightImage
        if "72" in workflow_copy:
            inputs = workflow_copy["72"]["inputs"]
            if "delight_steps" in params:
                inputs["steps"] = params["delight_steps"]
            if "delight_guidance" in params:
                inputs["guidance_scale"] = params["delight_guidance"]
            self.logger.info(f"Injected Hy3DDelightImage params")
        
        # Node 56: SolidMask
        if "56" in workflow_copy:
            inputs = workflow_copy["56"]["inputs"]
            if "background_level" in params:
                inputs["value"] = params["background_level"]
            self.logger.info(f"Injected SolidMask background level")
        
        # Additional nodes for UV workflow
        # Node 62: Hy3DRenderMultiView
        if "62" in workflow_copy:
            inputs = workflow_copy["62"]["inputs"]
            if "render_size" in params:
                inputs["render_size"] = params["render_size"]
            if "texture_size" in params:
                inputs["texture_size"] = params["texture_size"]
            self.logger.info(f"Injected Hy3DRenderMultiView params")
        
        # Node 63: Hy3DCameraConfig
        if "63" in workflow_copy:
            inputs = workflow_copy["63"]["inputs"]
            if "camera_distance" in params:
                inputs["camera_distance"] = params["camera_distance"]
            if "ortho_scale" in params:
                inputs["ortho_scale"] = params["ortho_scale"]
            self.logger.info(f"Injected Hy3DCameraConfig params")
        
        # Node 82: Hy3DSampleMultiView
        if "82" in workflow_copy:
            inputs = workflow_copy["82"]["inputs"]
            
            # Validate integer values to prevent "Python int too large to convert to C long"
            if "sample_seed" in params:
                inputs["seed"] = self.safe_int(params["sample_seed"], "API_seed", 42)
            if "sample_steps" in params:
                inputs["steps"] = self.safe_int(params["sample_steps"], "API_steps", 20)
            if "view_size" in params:
                inputs["view_size"] = self.safe_int(params["view_size"], "API_view_size", 512)
            self.logger.info(f"Injected Hy3DSampleMultiView params")
        
        return workflow_copy

    def _handle_anything_everywhere_nodes(self, ui_workflow: Dict[str, Any], api_workflow: Dict[str, Any], link_map: Dict[int, tuple]) -> Dict[str, tuple]:
        """Handle Anything Everywhere nodes which distribute values globally"""
        distributed_connections = {}
        
        for node in ui_workflow.get("nodes", []):
            node_type = node.get("type", "")
            node_id = str(node.get("id", ""))
            
            if "Anything Everywhere" in node_type:
                # Track what this node is distributing
                for input_def in node.get("inputs", []):
                    if "link" in input_def and input_def["link"] is not None:
                        link_id = input_def["link"]
                        if link_id in link_map:
                            source_node_id, output_index = link_map[link_id]
                            # Get the label which indicates the type (MODEL, CLIP, VAE, etc.)
                            input_label = input_def.get("label", "")
                            if input_label:
                                distributed_connections[input_label] = (str(source_node_id), output_index)
                                self.logger.info(f"Anything Everywhere node {node_id} distributes {input_label} from {source_node_id}[{output_index}]")
        
        return distributed_connections
    
    def _apply_distributed_connections(self, api_workflow: Dict[str, Any], distributed_connections: Dict[str, tuple]):
        """Apply distributed connections to nodes that need them"""
        # Map of distributed labels to actual input names
        label_to_inputs = {
            "MODEL": ["model"],
            "CLIP": ["clip"],
            "VAE": ["vae"],
            "CONTROL_NET": ["control_net"],
            "UPSCALE_MODEL": ["upscale_model"],
            "BBOX_DETECTOR": ["bbox_detector"]
        }
        
        # Check each node for missing inputs that can be filled from distributed values
        for node_id, node_data in api_workflow.items():
            if not isinstance(node_data, dict) or "inputs" not in node_data:
                continue
            
            inputs = node_data["inputs"]
            class_type = node_data.get("class_type", "")
            
            # Skip Hy3D model nodes for MODEL distribution - they need string model names, not MODEL connections
            skip_model_distribution = class_type in ["DownloadAndLoadHy3DPaintModel", "DownloadAndLoadHy3DDelightModel"]
            
            # Check each distributed connection
            for label, (source_node_id, output_index) in distributed_connections.items():
                # Skip MODEL distribution for Hy3D model nodes
                if label == "MODEL" and skip_model_distribution:
                    continue
                    
                if label in label_to_inputs:
                    # Check each possible input name for this label
                    for input_name in label_to_inputs[label]:
                        # Apply if the input exists but has no connection OR has None value
                        if input_name in inputs and (not isinstance(inputs[input_name], list) or inputs[input_name] is None):
                            inputs[input_name] = [source_node_id, output_index]
                            self.logger.debug(f"Applied distributed {label} to {node_id}.{input_name} from {source_node_id}[{output_index}]")
            
            # Special handling for nodes that commonly need these connections but might not have explicit None values
            # Use aggressive connection filling for critical nodes
            
            if class_type in ["CLIPTextEncode", "FaceDetailer"] and "clip" not in inputs:
                if "CLIP" in distributed_connections:
                    source_node_id, output_index = distributed_connections["CLIP"]
                    inputs["clip"] = [source_node_id, output_index]
                    self.logger.info(f"🔧 APPLIED missing CLIP to {class_type} node {node_id}")
            
            if class_type in ["KSampler", "UltimateSDUpscale", "FaceDetailer"] and "model" not in inputs:
                if "MODEL" in distributed_connections:
                    source_node_id, output_index = distributed_connections["MODEL"]
                    inputs["model"] = [source_node_id, output_index]
                    self.logger.info(f"🔧 APPLIED missing MODEL to {class_type} node {node_id}")
            
            # Special handling for Hy3D model nodes - they should NOT receive regular MODEL connections
            # They expect specific model names as string inputs, not MODEL type connections
            if class_type == "DownloadAndLoadHy3DPaintModel" and "model" not in inputs:
                # Set default Hy3D paint model name
                inputs["model"] = "hunyuan3d-paint-v2-0"
                self.logger.info(f"🔧 SET default Hy3D paint model for node {node_id}")
            
            elif class_type == "DownloadAndLoadHy3DDelightModel" and "model" not in inputs:
                # Set default Hy3D delight model name
                inputs["model"] = "hunyuan3d-delight-v2-0"
                self.logger.info(f"🔧 SET default Hy3D delight model for node {node_id}")
            
            if class_type in ["VAEDecode", "UltimateSDUpscale", "FaceDetailer"] and "vae" not in inputs:
                if "VAE" in distributed_connections:
                    source_node_id, output_index = distributed_connections["VAE"]
                    inputs["vae"] = [source_node_id, output_index]
                    self.logger.info(f"🔧 APPLIED missing VAE to {class_type} node {node_id}")
            
            if class_type == "ControlNetApplyAdvanced" and "control_net" not in inputs:
                if "CONTROL_NET" in distributed_connections:
                    source_node_id, output_index = distributed_connections["CONTROL_NET"]
                    inputs["control_net"] = [source_node_id, output_index]
                    self.logger.info(f"🔧 APPLIED missing CONTROL_NET to {class_type} node {node_id}")
            
            if class_type == "UltimateSDUpscale" and "upscale_model" not in inputs:
                if "UPSCALE_MODEL" in distributed_connections:
                    source_node_id, output_index = distributed_connections["UPSCALE_MODEL"]
                    inputs["upscale_model"] = [source_node_id, output_index]
                    self.logger.info(f"🔧 APPLIED missing UPSCALE_MODEL to {class_type} node {node_id}")
            
            if class_type == "FaceDetailer" and "bbox_detector" not in inputs:
                if "BBOX_DETECTOR" in distributed_connections:
                    source_node_id, output_index = distributed_connections["BBOX_DETECTOR"]
                    inputs["bbox_detector"] = [source_node_id, output_index]
                    self.logger.info(f"🔧 APPLIED missing BBOX_DETECTOR to {class_type} node {node_id}")
            
            # Special handling for UltimateSDUpscale positive/negative conditioning
            if class_type == "UltimateSDUpscale":
                # Try to find conditioning nodes in the workflow for positive/negative
                if "positive" not in inputs:
                    # Look for CLIPTextEncode nodes that could provide positive conditioning
                    for other_node_id, other_node_data in api_workflow.items():
                        if (isinstance(other_node_data, dict) and 
                            other_node_data.get("class_type") == "CLIPTextEncode" and
                            other_node_id in ["352", "510"]):  # Common positive conditioning node IDs
                            inputs["positive"] = [other_node_id, 0]
                            self.logger.info(f"🔧 APPLIED positive conditioning to UltimateSDUpscale node {node_id} from {other_node_id}")
                            break
                
                if "negative" not in inputs:
                    # Look for negative conditioning nodes
                    for other_node_id, other_node_data in api_workflow.items():
                        if (isinstance(other_node_data, dict) and 
                            other_node_data.get("class_type") == "CLIPTextEncode" and
                            other_node_id == "177"):  # Common negative conditioning node ID
                            inputs["negative"] = [other_node_id, 0]
                            self.logger.info(f"🔧 APPLIED negative conditioning to UltimateSDUpscale node {node_id} from {other_node_id}")
                            break
            
            # DISABLED: Hy3DSetMeshPBRTextures bypass to debug validation errors
            # This node was being removed due to "texture type validation errors"
            # Temporarily disabled to identify and fix the actual issue
            if False and class_type == "Hy3DSetMeshPBRTextures":
                # The texture processing works fine without this specific PBR node
                # Remove this node from the workflow to allow the export to complete
                self.logger.info(f"🔧 TEXTURE BYPASS: Removing problematic Hy3DSetMeshPBRTextures node {node_id} to allow export")
                
                # Find what node connects to this node's output and redirect it
                redirections = []
                if "trimesh" in inputs and isinstance(inputs["trimesh"], list):
                    source_node_id, output_index = inputs["trimesh"]
                    
                    # Collect nodes that need to be redirected (don't modify during iteration)
                    for other_node_id, other_node_data in api_workflow.items():
                        if isinstance(other_node_data, dict) and "inputs" in other_node_data:
                            other_inputs = other_node_data["inputs"]
                            for input_name, input_value in other_inputs.items():
                                if (isinstance(input_value, list) and len(input_value) >= 2 and 
                                    input_value[0] == node_id):
                                    # Collect redirection info
                                    redirections.append((other_node_id, input_name, source_node_id, input_value[1]))
                    
                    # Apply redirections
                    for other_node_id, input_name, source_node_id, output_index in redirections:
                        api_workflow[other_node_id]["inputs"][input_name] = [source_node_id, output_index]
                        self.logger.info(f"🔧 TEXTURE BYPASS: Redirected {other_node_id}.{input_name} from {node_id} to {source_node_id}")
                
                # Mark node for removal (don't delete during iteration)
                nodes_to_remove = getattr(self, '_nodes_to_remove', [])
                nodes_to_remove.append(node_id)
                self._nodes_to_remove = nodes_to_remove
                self.logger.info(f"🔧 TEXTURE BYPASS: Marked node {node_id} for removal")
                continue  # Skip further processing of this node
            
            # CRITICAL FIX: Check for any image/mask generation nodes that might produce invalid dimensions
            # and ensure they have minimum viable sizes to prevent PIL errors
            if class_type in ["VAEDecode", "ImageFromBatch", "ImageConcatFromBatch", "Hy3DRenderMultiView", 
                              "Hy3DBakeFromMultiview", "Hy3DDelightImage", "CV2InpaintTexture"]:
                # These nodes can potentially output images - ensure they're not creating 1x1 images
                self.logger.warning(f"Monitoring {class_type} node {node_id} for potential dimension issues - check input sizes")
            
            # Special validation for VAEDecode which commonly produces the problematic tensors
            if class_type == "VAEDecode":
                # Make sure this node has proper connections
                if "samples" not in inputs or "vae" not in inputs:
                    self.logger.error(f"VAEDecode node {node_id} missing critical inputs - this may cause dimension errors")
        
        # Clean up nodes marked for removal (after iteration is complete)
        nodes_to_remove = getattr(self, '_nodes_to_remove', [])
        for node_id in nodes_to_remove:
            if node_id in api_workflow:
                del api_workflow[node_id]
                self.logger.info(f"🔧 CLEANUP: Removed node {node_id} from workflow")
        
        # Clear the removal list
        if hasattr(self, '_nodes_to_remove'):
            delattr(self, '_nodes_to_remove')
    
    def _handle_setnode_getnode(self, ui_workflow: Dict[str, Any], api_workflow: Dict[str, Any], link_map: Dict[int, tuple]) -> Dict[str, Dict]:
        """Handle SetNode/GetNode connections by tracking what connects through them"""
        # Track SetNode sources by key name
        set_nodes = {}  # key -> (source_node_id, output_index)
        get_nodes = {}  # node_id -> key
        
        for node in ui_workflow.get("nodes", []):
            node_type = node.get("type", "")
            node_id = str(node.get("id", ""))
            widgets = node.get("widgets_values", [])
            
            if node_type == "SetNode" and widgets:
                key = widgets[0]  # The key name
                # Find what connects to this SetNode
                for input_def in node.get("inputs", []):
                    if "link" in input_def and input_def["link"] is not None:
                        link_id = input_def["link"]
                        if link_id in link_map:
                            source_node_id, output_index = link_map[link_id]
                            set_nodes[key] = (str(source_node_id), output_index)
                            self.logger.info(f"SetNode {node_id} stores key '{key}' from {source_node_id}[{output_index}]")
            
            elif node_type == "GetNode" and widgets:
                key = widgets[0]  # The key name
                get_nodes[node_id] = key
                self.logger.info(f"GetNode {node_id} retrieves key '{key}'")
        
        # Build connections map: get_node_id -> (source_node_id, output_index)
        connections = {}
        for get_node_id, key in get_nodes.items():
            if key in set_nodes:
                connections[get_node_id] = set_nodes[key]
                self.logger.info(f"Mapped GetNode {get_node_id} (key: {key}) to source {set_nodes[key]}")
        
        return connections
    
    def _apply_setget_connections(self, api_workflow: Dict[str, Any], connections: Dict[str, tuple]):
        """Apply connections from SetNode/GetNode resolution"""
        # Find nodes that have inputs connected to GetNodes
        for node_id, node_data in api_workflow.items():
            if not isinstance(node_data, dict) or "inputs" not in node_data:
                continue
            
            inputs = node_data["inputs"]
            for input_name, input_value in list(inputs.items()):
                if isinstance(input_value, list) and len(input_value) == 2:
                    source_id = str(input_value[0])
                    # Check if this input is connected to a GetNode that we need to resolve
                    if source_id in connections:
                        # Replace with the actual source
                        real_source_id, real_output_index = connections[source_id]
                        inputs[input_name] = [real_source_id, real_output_index]
                        self.logger.info(f"Resolved GetNode connection: {node_id}.{input_name} -> {real_source_id}[{real_output_index}]")
    
    def inject_3d_model_path(self, workflow: Dict[str, Any], model_path: str) -> Dict[str, Any]:
        """Inject 3D model path into texture generation workflow
        
        Now uses Hy3DLoadMesh node that accepts relative file paths from ComfyUI base directory
        """
        workflow_copy = deepcopy(workflow)
        
        self.logger.info(f"Injecting 3D model path: {model_path} into texture workflow")
        
        # Convert full path to ComfyUI relative path
        def get_comfyui_relative_path(full_path: str) -> str:
            """Convert full path to ComfyUI relative path"""
            path_obj = Path(full_path)
            
            # ComfyUI expects paths relative to its output directory
            # Example: D:\Comfy3D_WinPortable\ComfyUI\output\3D\Hy3D_00326_.glb -> 3D/Hy3D_00326_.glb
            
            parts = path_obj.parts
            try:
                # Find the 3D directory in the path and get everything from there
                if '3D' in parts:
                    three_d_index = parts.index('3D')
                    # Get 3D and everything after it
                    relative_parts = parts[three_d_index:]
                    relative_path = '/'.join(relative_parts)
                    return relative_path
                
                # Fallback: if we can't find 3D, try to find output and skip it
                elif 'output' in parts:
                    output_index = parts.index('output')
                    # Get everything after output directory
                    relative_parts = parts[output_index + 1:]
                    relative_path = '/'.join(relative_parts)
                    return relative_path
                
                # Last resort: just use filename
                return path_obj.name
            except (ValueError, IndexError):
                # If any errors, fallback to filename
                return path_obj.name
        
        comfyui_relative_path = get_comfyui_relative_path(model_path)
        self.logger.info(f"Converted to ComfyUI relative path: {comfyui_relative_path}")
        
        # IMPORTANT: Hy3DLoadMesh node looks for files in ComfyUI's input directory, not output
        # We need to copy the output file to the input directory for ComfyUI to find it
        try:
            import shutil
            
            source_path = Path(model_path)
            if source_path.exists():
                # Determine ComfyUI input directory based on source path structure
                source_parts = source_path.parts
                if 'ComfyUI' in source_parts:
                    comfyui_index = next(i for i, part in enumerate(source_parts) if 'ComfyUI' in part)
                    comfyui_base = Path(*source_parts[:comfyui_index + 1])
                    input_dir = comfyui_base / "input" / "3D"
                    
                    # Create input/3D directory if it doesn't exist
                    input_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file to input directory
                    destination_path = input_dir / source_path.name
                    shutil.copy2(source_path, destination_path)
                    
                    self.logger.info(f"✅ Copied model to ComfyUI input directory: {destination_path}")
                    self.logger.info(f"ComfyUI will load from: input/{comfyui_relative_path}")
                else:
                    self.logger.warning(f"Could not determine ComfyUI base directory from path: {model_path}")
            else:
                self.logger.error(f"Source model file not found: {source_path}")
        except Exception as e:
            self.logger.error(f"Failed to copy model to input directory: {e}")
            # Continue anyway - maybe the file is already there
        
        # For UI workflows - update nodes directly
        if "nodes" in workflow_copy:
            for node in workflow_copy.get("nodes", []):
                node_type = node.get("type", "")
                
                # Handle the new Hy3DLoadMesh node that takes relative paths
                if node_type == "Hy3DLoadMesh":
                    widgets = node.get("widgets_values", [""])
                    widgets[0] = comfyui_relative_path  # Set the ComfyUI relative path
                    node["widgets_values"] = widgets
                    self.logger.info(f"✅ Updated Hy3DLoadMesh node with relative path: {comfyui_relative_path}")
                    
                # Keep support for old Hy3DUploadMesh nodes (for backward compatibility)
                elif node_type == "Hy3DUploadMesh":
                    model_filename = Path(model_path).name
                    widgets = node.get("widgets_values", ["", "image"])
                    widgets[0] = model_filename
                    node["widgets_values"] = widgets
                    self.logger.info(f"Updated legacy Hy3DUploadMesh node with filename: {model_filename}")
        
        # For API workflows - update inputs
        else:
            for node_id, node_data in workflow_copy.items():
                if isinstance(node_data, dict):
                    class_type = node_data.get("class_type", "")
                    
                    # Handle the new Hy3DLoadMesh node
                    if class_type == "Hy3DLoadMesh":
                        inputs = node_data.get("inputs", {})
                        inputs["glb_path"] = comfyui_relative_path  # ComfyUI relative path (parameter name is glb_path)
                        node_data["inputs"] = inputs
                        self.logger.info(f"✅ Updated Hy3DLoadMesh node {node_id} with relative path: {comfyui_relative_path}")
                        
                    # Keep support for old Hy3DUploadMesh nodes
                    elif class_type == "Hy3DUploadMesh":
                        model_filename = Path(model_path).name
                        inputs = node_data.get("inputs", {})
                        inputs["mesh"] = model_filename
                        node_data["inputs"] = inputs
                        self.logger.info(f"Updated legacy Hy3DUploadMesh node {node_id} with filename: {model_filename}")
        
        return workflow_copy
    
    def _ensure_save_image_node(self, api_workflow: Dict[str, Any]):
        """Ensure the workflow has a SaveImage node and redirect it to correct path"""
        # Check if any SaveImage or "Image Save" nodes exist
        save_nodes = []
        vae_decode_nodes = []
        
        for node_id, node_data in api_workflow.items():
            class_type = node_data.get("class_type", "")
            if class_type in ["SaveImage", "Image Save"]:
                save_nodes.append(node_id)
            elif class_type == "VAEDecode":
                vae_decode_nodes.append(node_id)
        
        if save_nodes:
            # SaveImage nodes exist, ensure they have correct path
            for node_id in save_nodes:
                node_data = api_workflow[node_id]
                inputs = node_data.get("inputs", {})
                
                # Get configured images directory
                if hasattr(self, 'config') and hasattr(self.config, 'images_dir'):
                    correct_images_path = str(self.config.images_dir)
                else:
                    from pathlib import Path
                    correct_images_path = str(Path(__file__).parent.parent.parent / "images")
                
                # Update or add output_path
                if node_data.get("class_type") == "Image Save":
                    # Convert WAS "Image Save" to standard "SaveImage" for compatibility
                    self.logger.warning(f"🔄 Converting WAS 'Image Save' node {node_id} to standard 'SaveImage' for compatibility")
                    
                    # Change class_type to standard SaveImage
                    node_data["class_type"] = "SaveImage"
                    
                    # Convert to standard SaveImage inputs (preserve image connection)
                    image_connection = inputs.get("images", ["11", 0])  # Default fallback
                    inputs.clear()  # Clear all WAS-specific inputs
                    inputs["images"] = image_connection
                    inputs["filename_prefix"] = "ComfyUI"
                    
                    self.logger.info(f"✅ Converted to SaveImage node {node_id} with standard inputs")
                else:  # SaveImage
                    inputs["filename_prefix"] = inputs.get("filename_prefix", "ComfyUI")
                    self.logger.info(f"✅ Updated SaveImage node {node_id} filename prefix")
                
                node_data["inputs"] = inputs
        
        else:
            # No SaveImage nodes found, add one if we have VAEDecode output
            if vae_decode_nodes:
                # Find the last VAEDecode node to connect to
                vae_decode_id = vae_decode_nodes[-1]
                
                # Create new SaveImage node
                save_node_id = str(max([int(k) for k in api_workflow.keys() if k.isdigit()], default=0) + 1)
                
                # Get configured images directory
                if hasattr(self, 'config') and hasattr(self.config, 'images_dir'):
                    correct_images_path = str(self.config.images_dir)
                else:
                    from pathlib import Path
                    correct_images_path = str(Path(__file__).parent.parent.parent / "images")
                
                save_node = {
                    "class_type": "SaveImage", 
                    "inputs": {
                        "images": [vae_decode_id, 0],  # Connect to VAEDecode output
                        "filename_prefix": "ComfyUI"
                    }
                }
                
                api_workflow[save_node_id] = save_node
                self.logger.info(f"✅ Added SaveImage node {save_node_id} connected to VAEDecode {vae_decode_id}")
                self.logger.info(f"✅ SaveImage will save to ComfyUI default output directory")

    def inject_parameters(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to ComfyUI format"""
        return self.inject_parameters_comfyui(workflow, params)