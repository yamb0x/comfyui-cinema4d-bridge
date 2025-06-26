"""
Unified Configuration Manager for ComfyUI Workflow Parameters
Implements centralized parameter management with observer pattern
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Callable
from copy import deepcopy
from loguru import logger
from PySide6.QtCore import QObject, Signal

from src.core.workflow_parameter_extractor import WorkflowParameterExtractor
from src.core.dynamic_parameter_extractor import DynamicParameterExtractor
from src.utils.logger import LoggerMixin


class UnifiedConfigurationManager(QObject, LoggerMixin):
    """
    Centralized configuration manager for all workflow parameters
    Ensures consistency across all tabs and UI panels
    """
    
    # Signals for observer pattern
    parameters_updated = Signal(dict)  # Emitted when parameters change
    workflow_loaded = Signal(str)      # Emitted when workflow is loaded
    prompts_extracted = Signal(dict)   # Emitted when prompts are extracted from workflow
    
    # Node types to hide from right panel (handled by left panel controls)
    HIDDEN_NODE_TYPES = {
        "Reroute", "LoadImage", "SaveImage", "PreviewImage",
        "PrimitiveNode", "Note", "MarkdownNote",
        # Nodes handled by left panel controls:
        "CLIPTextEncode",  # Handled by prompt boxes
        "EmptyLatentImage", "EmptySD3LatentImage",  # Handled by generation controls
    }
    
    # Priority order for parameter sections
    PARAMETER_PRIORITY = {
        "KSampler": 1,
        "KSamplerAdvanced": 1,
        "CheckpointLoader": 2,
        "CheckpointLoaderSimple": 2,
        "UNETLoader": 2,
        "LoraLoader": 3,
        "VAELoader": 4,
        "CLIPTextEncode": 5,
        "FluxGuidance": 6,
        "EmptyLatentImage": 7,
        "EmptySD3LatentImage": 7,
        "ControlNetLoader": 8,
        "QuadrupleCLIPLoader": 9,
        # Hunyuan3D nodes
        "Hy3DModelLoader": 10,
        "Hy3DGenerateMesh": 11,
        "Hy3DVAEDecode": 12,
        "Hy3DPostprocessMesh": 13,
        "Hy3DExportMesh": 14
    }
    
    # Node color coding for visual differentiation
    NODE_COLORS = {
        "KSampler": "#4CAF50",           # Green - Primary sampling
        "KSamplerAdvanced": "#4CAF50",
        "CheckpointLoader": "#2196F3",    # Blue - Model loading
        "CheckpointLoaderSimple": "#2196F3",
        "UNETLoader": "#2196F3",
        "LoraLoader": "#9C27B0",         # Purple - LoRA
        "VAELoader": "#FF9800",          # Orange - VAE
        "CLIPTextEncode": "#00BCD4",     # Cyan - Text encoding
        "FluxGuidance": "#FFC107",       # Amber - Guidance
        "EmptyLatentImage": "#795548",    # Brown - Latent
        "EmptySD3LatentImage": "#795548",
        "ControlNetLoader": "#E91E63",    # Pink - ControlNet
        "QuadrupleCLIPLoader": "#00BCD4", # Cyan - CLIP
        # Hunyuan3D nodes
        "Hy3DModelLoader": "#8BC34A",     # Light Green - 3D Model
        "Hy3DGenerateMesh": "#FF5722",    # Deep Orange - 3D Generation
        "Hy3DVAEDecode": "#607D8B",       # Blue Grey - 3D VAE
        "Hy3DPostprocessMesh": "#9E9E9E", # Grey - Post-processing
        "Hy3DExportMesh": "#795548"       # Brown - Export
    }
    
    def __init__(self):
        super().__init__()
        self._parameter_extractor = WorkflowParameterExtractor()
        self._dynamic_extractor = DynamicParameterExtractor()  # For nodes not in PARAMETER_MAPPINGS
        self._current_workflow: Optional[str] = None
        self._current_parameters: Dict[str, Any] = {}
        self._user_overrides: Dict[str, Any] = {}  # User modifications take precedence
        self._observers: List[Callable] = []
        self._ticked_parameters: Set[str] = set()  # Track which parameters are visible
        
        # Load saved configuration
        self._load_saved_config()
    
    def load_workflow_configuration(self, workflow_path: Path) -> Dict[str, Any]:
        """
        Load and extract parameters from a ComfyUI workflow
        Returns organized parameters with metadata
        """
        try:
            self.logger.info(f"Loading workflow configuration from: {workflow_path}")
            
            # First, try to extract parameters using static mappings
            raw_params = self._parameter_extractor.extract_parameters(workflow_path)
            
            # For texture generation, also extract parameters dynamically from selected nodes
            # Check if this is texture generation by looking for texture config
            texture_config_path = Path("config/texture_parameters_config.json")
            if texture_config_path.exists() and "texture" in str(workflow_path):
                try:
                    with open(texture_config_path, 'r') as f:
                        texture_config = json.load(f)
                    
                    selected_nodes = set(texture_config.get("selected_nodes", []))
                    self.logger.info(f"🎯 Loading dynamic parameters for {len(selected_nodes)} selected texture nodes")
                    
                    # Extract parameters dynamically for selected nodes
                    dynamic_params = self._dynamic_extractor.extract_all_parameters(workflow_path, selected_nodes)
                    
                    # Merge dynamic parameters with static ones
                    raw_params.update(dynamic_params)
                    self.logger.info(f"📊 Combined parameters: {len(raw_params)} total (static + dynamic)")
                    
                    # Also extract and emit prompts for texture generation
                    self._extract_and_emit_texture_prompts(workflow_path, texture_config)
                    
                except Exception as e:
                    self.logger.error(f"Failed to load dynamic texture parameters: {e}")
            
            # Organize parameters by node type and priority
            organized_params = self._organize_parameters(raw_params)
            
            # Apply user overrides if they exist
            self._apply_user_overrides(organized_params)
            
            # Store current state
            self._current_workflow = workflow_path.name
            self._current_parameters = organized_params
            
            # Save configuration
            self._save_current_config()
            
            # Notify observers
            self.parameters_updated.emit(organized_params)
            self.workflow_loaded.emit(workflow_path.name)
            
            return organized_params
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow configuration: {e}")
            return {}
    
    def _organize_parameters(self, raw_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organize parameters by node type with priority and metadata
        """
        organized = {}
        
        for param_key, param_data in raw_params.items():
            node_type = param_data.get("node_type", "")
            
            # Skip hidden node types
            if node_type in self.HIDDEN_NODE_TYPES:
                continue
            
            # Create section if doesn't exist
            if node_type not in organized:
                organized[node_type] = {
                    "priority": self.PARAMETER_PRIORITY.get(node_type, 99),
                    "color": self.NODE_COLORS.get(node_type, "#666666"),
                    "parameters": {},
                    "node_id": param_data.get("node_id", ""),
                    "display_name": self._get_display_name(node_type)
                }
            
            # Add parameter to section
            param_name = param_data.get("param_name", "")
            organized[node_type]["parameters"][param_name] = param_data
        
        # Sort sections by priority
        sorted_sections = dict(sorted(
            organized.items(),
            key=lambda x: x[1]["priority"]
        ))
        
        return sorted_sections
    
    def _get_display_name(self, node_type: str) -> str:
        """Get user-friendly display name for node type"""
        display_names = {
            "KSampler": "Sampling Settings",
            "KSamplerAdvanced": "Advanced Sampling",
            "CheckpointLoader": "Model Selection",
            "CheckpointLoaderSimple": "Model Selection",
            "UNETLoader": "UNET Model",
            "LoraLoader": "LoRA Settings",
            "VAELoader": "VAE Model",
            "CLIPTextEncode": "Text Prompts",
            "FluxGuidance": "Flux Guidance",
            "EmptyLatentImage": "Image Dimensions",
            "EmptySD3LatentImage": "SD3 Dimensions",
            "ControlNetLoader": "ControlNet",
            "QuadrupleCLIPLoader": "CLIP Models",
            # Hunyuan3D nodes
            "Hy3DModelLoader": "3D Model Loading",
            "Hy3DGenerateMesh": "3D Mesh Generation",
            "Hy3DVAEDecode": "3D VAE Decoding",
            "Hy3DPostprocessMesh": "Mesh Post-processing",
            "Hy3DExportMesh": "Mesh Export",
            # Dynamic node types
            "UltimateSDUpscale": "Ultimate SD Upscale",
            "ControlNetApplyAdvanced": "ControlNet Advanced",
            "ImageRemoveBackground+": "Background Removal",
            "TransparentBGSession+": "Transparent Background",
            "ImageCompositeMasked": "Image Compositing",
            "SolidMask": "Mask Settings",
            "ImageBlend": "Image Blending",
            "ImageInvert": "Image Invert",
            "ImageResizeKJv2": "Image Resize",
            "NormalMapSimple": "Normal Map",
            "CV2InpaintTexture": "Texture Inpainting",
            "Hy3DMeshVerticeInpaintTexture": "Mesh Vertex Inpainting",
            "Hy3DApplyTexture": "Apply Texture",
            "Hy3DBakeFromMultiview": "Bake Multiview",
            "Hy3DMeshUVWrap": "UV Wrapping",
            "Hy3DSetMeshPBRTextures": "PBR Textures"
        }
        return display_names.get(node_type, node_type)
    
    def update_parameter(self, param_key: str, value: Any, is_user_override: bool = True):
        """
        Update a parameter value
        If is_user_override is True, the value persists across workflow reloads
        """
        # Find the parameter in current configuration
        for node_type, section in self._current_parameters.items():
            params = section.get("parameters", {})
            for param_name, param_data in params.items():
                full_key = f"{node_type}_{section.get('node_id', '')}_{param_name}"
                if full_key == param_key or param_name == param_key:
                    # Update the value
                    param_data["current_value"] = value
                    
                    # Track as user override if specified
                    if is_user_override:
                        self._user_overrides[param_key] = value
                    
                    # Save configuration
                    self._save_current_config()
                    
                    # Notify observers
                    self.parameters_updated.emit(self._current_parameters)
                    
                    self.logger.debug(f"Updated parameter {param_key} = {value}")
                    return True
        
        self.logger.warning(f"Parameter {param_key} not found in current configuration")
        return False
    
    def get_parameter_value(self, param_key: str) -> Optional[Any]:
        """Get current value of a parameter"""
        for node_type, section in self._current_parameters.items():
            params = section.get("parameters", {})
            for param_name, param_data in params.items():
                full_key = f"{node_type}_{section.get('node_id', '')}_{param_name}"
                if full_key == param_key or param_name == param_key:
                    return param_data.get("current_value", param_data.get("default"))
        return None
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """Get all current parameters organized by section"""
        return deepcopy(self._current_parameters)
    
    def get_ticked_parameters(self) -> Set[str]:
        """Get set of parameters that should be visible in UI"""
        return self._ticked_parameters.copy()
    
    def set_parameter_visibility(self, param_key: str, visible: bool):
        """Set whether a parameter should be visible in UI"""
        if visible:
            self._ticked_parameters.add(param_key)
        else:
            self._ticked_parameters.discard(param_key)
        
        # Save configuration
        self._save_current_config()
    
    def _apply_user_overrides(self, parameters: Dict[str, Any]):
        """Apply saved user overrides to parameters"""
        for override_key, override_value in self._user_overrides.items():
            # Find and update the parameter
            for node_type, section in parameters.items():
                params = section.get("parameters", {})
                for param_name, param_data in params.items():
                    full_key = f"{node_type}_{section.get('node_id', '')}_{param_name}"
                    if full_key == override_key or param_name == override_key:
                        param_data["current_value"] = override_value
                        self.logger.debug(f"Applied user override: {override_key} = {override_value}")
    
    def _save_current_config(self):
        """Save current configuration to file"""
        try:
            config_path = Path("config/unified_parameters_state.json")
            config_path.parent.mkdir(exist_ok=True)
            
            config_data = {
                "current_workflow": self._current_workflow,
                "parameters": self._current_parameters,
                "user_overrides": self._user_overrides,
                "ticked_parameters": list(self._ticked_parameters)
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            self.logger.debug("Saved unified configuration state")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _load_saved_config(self):
        """Load saved configuration from file"""
        try:
            config_path = Path("config/unified_parameters_state.json")
            if not config_path.exists():
                return
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            self._current_workflow = config_data.get("current_workflow")
            self._current_parameters = config_data.get("parameters", {})
            self._user_overrides = config_data.get("user_overrides", {})
            self._ticked_parameters = set(config_data.get("ticked_parameters", []))
            
            self.logger.debug("Loaded saved unified configuration state")
            
        except Exception as e:
            self.logger.error(f"Failed to load saved configuration: {e}")
    
    def clear_user_overrides(self):
        """Clear all user overrides and reload from workflow"""
        self._user_overrides.clear()
        if self._current_workflow:
            workflow_path = Path("workflows") / self._current_workflow
            if workflow_path.exists():
                self.load_workflow_configuration(workflow_path)
    
    def export_configuration(self, filepath: Path) -> bool:
        """Export current configuration to file"""
        try:
            export_data = {
                "workflow": self._current_workflow,
                "parameters": self._current_parameters,
                "ticked": list(self._ticked_parameters)
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported configuration to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, filepath: Path) -> bool:
        """Import configuration from file"""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            self._current_workflow = import_data.get("workflow")
            self._current_parameters = import_data.get("parameters", {})
            self._ticked_parameters = set(import_data.get("ticked", []))
            
            # Save and notify
            self._save_current_config()
            self.parameters_updated.emit(self._current_parameters)
            
            self.logger.info(f"Imported configuration from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def update_node_colors(self, color_mapping: Dict[str, str]):
        """Update the NODE_COLORS mapping with new colors"""
        try:
            # Update the NODE_COLORS dictionary
            for node_type, color in color_mapping.items():
                if node_type in self.NODE_COLORS:
                    self.NODE_COLORS[node_type] = color
            
            # If we have current parameters, update their color information
            if self._current_parameters:
                for node_type, section in self._current_parameters.items():
                    if node_type in color_mapping:
                        section["color"] = color_mapping[node_type]
                
                # Notify observers about the color update
                self.parameters_updated.emit(self._current_parameters)
            
            self.logger.debug(f"Updated node colors for {len(color_mapping)} node types")
            
        except Exception as e:
            self.logger.error(f"Failed to update node colors: {e}")
    
    def get_node_color(self, node_type: str) -> str:
        """Get the color for a specific node type"""
        return self.NODE_COLORS.get(node_type, "#666666")
    
    def _extract_and_emit_texture_prompts(self, workflow_path: Path, texture_config: Dict[str, Any]):
        """Extract prompts from texture workflow and emit them via signal"""
        try:
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            
            prompts = {}
            
            # Get node info from texture config to map node IDs to types
            node_info = texture_config.get("node_info", {})
            
            # Look for CLIPTextEncode nodes in the workflow
            for node in workflow_data.get('nodes', []):
                node_id = str(node.get('id', ''))
                node_type = node.get('type', '')
                title = node.get('title', '')
                widgets_values = node.get('widgets_values', [])
                
                if node_type == 'CLIPTextEncode' and widgets_values and len(widgets_values) > 0:
                    prompt_text = widgets_values[0]
                    
                    # Determine if this is positive or negative based on title and known node IDs
                    if "positive" in title.lower() or node_id == "510":
                        prompts["texture_positive"] = prompt_text
                        self.logger.info(f"🎯 Extracted texture positive prompt: {prompt_text[:50]}...")
                    elif "negative" in title.lower() or node_id == "177":
                        prompts["texture_negative"] = prompt_text
                        self.logger.info(f"🎯 Extracted texture negative prompt: {prompt_text[:50]}...")
            
            # Emit the prompts via signal
            if prompts:
                self.prompts_extracted.emit(prompts)
                self.logger.info(f"✅ Emitted {len(prompts)} texture prompts via signal")
            
        except Exception as e:
            self.logger.error(f"Failed to extract texture prompts: {e}")