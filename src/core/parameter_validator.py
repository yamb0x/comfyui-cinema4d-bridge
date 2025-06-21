"""
Parameter Validator for ComfyUI Workflows
Validates and sanitizes parameters before sending to ComfyUI
"""

from typing import Dict, Any, Union, List, Optional
from loguru import logger


class ParameterValidator:
    """Validates workflow parameters before sending to ComfyUI"""
    
    def __init__(self):
        self.logger = logger
        
        # Define parameter constraints
        self.constraints = {
            # Image generation parameters
            "width": {"min": 64, "max": 8192, "multiple_of": 8, "type": int},
            "height": {"min": 64, "max": 8192, "multiple_of": 8, "type": int},
            "batch_size": {"min": 1, "max": 16, "type": int},
            "steps": {"min": 1, "max": 150, "type": int},
            "cfg": {"min": 0.0, "max": 30.0, "type": float},
            "denoise": {"min": 0.0, "max": 1.0, "type": float},
            "seed": {"min": 0, "max": 4294967295, "type": int},  # Max uint32
            
            # 3D generation parameters
            "guidance_scale_3d": {"min": 0.0, "max": 20.0, "type": float},
            "inference_steps_3d": {"min": 1, "max": 100, "type": int},
            "seed_3d": {"min": 0, "max": 4294967295, "type": int},
            "mesh_density": {"min": 0.1, "max": 10.0, "type": float},
            
            # LoRA parameters
            "lora_strength": {"min": -2.0, "max": 2.0, "type": float},
            "strength_model": {"min": -2.0, "max": 2.0, "type": float},
            "strength_clip": {"min": -2.0, "max": 2.0, "type": float},
            
            # Texture parameters
            "roughness": {"min": 0.0, "max": 1.0, "type": float},
            "metallic": {"min": 0.0, "max": 1.0, "type": float},
            
            # Upscale parameters
            "upscale_by": {"min": 1.0, "max": 8.0, "type": float},
            "tile_width": {"min": 64, "max": 2048, "multiple_of": 8, "type": int},
            "tile_height": {"min": 64, "max": 2048, "multiple_of": 8, "type": int},
        }
        
        # Define valid string options
        self.valid_options = {
            "sampler_name": ["euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral", 
                           "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", 
                           "dpmpp_sde", "dpmpp_2m", "ddim", "uni_pc", "uni_pc_bh2"],
            "scheduler": ["normal", "karras", "exponential", "sgm_uniform", "simple", 
                         "ddim_uniform", "beta", "linear_quadratic", "kl_optimal"],
            "quality_3d": ["low", "medium", "high", "ultra"],
            "material_type": ["PBR (Physical)", "Stylized", "Photorealistic", 
                            "Cartoon", "Metallic", "Fabric"],
            "blend_mode": ["normal", "multiply", "screen", "overlay", "soft_light", "difference"],
            "upscale_method": ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"],
            "controlnet_type": ["depth", "normal", "canny", "openpose", "mlsd", 
                              "lineart", "scribble", "fake_scribble", "seg"]
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize parameters
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            Validated and sanitized parameters
        """
        validated = {}
        errors = []
        warnings = []
        
        for key, value in params.items():
            try:
                # Check if we have constraints for this parameter
                if key in self.constraints:
                    validated_value = self._validate_numeric(key, value, self.constraints[key])
                    if validated_value is not None:
                        validated[key] = validated_value
                    else:
                        errors.append(f"{key}: Invalid value {value}")
                        
                # Check string options
                elif key in self.valid_options:
                    validated_value = self._validate_string_option(key, value, self.valid_options[key])
                    if validated_value is not None:
                        validated[key] = validated_value
                    else:
                        warnings.append(f"{key}: Unknown option '{value}', using default")
                        
                # Special handling for specific parameters
                elif key == "prompt" or key.endswith("_prompt"):
                    # Validate prompt strings
                    validated[key] = self._sanitize_prompt(value)
                    
                elif key.startswith("lora") and key.endswith("_model"):
                    # LoRA model names - just ensure it's a string
                    validated[key] = str(value) if value else ""
                    
                elif key.endswith("_active") or key.endswith("_enabled"):
                    # Boolean parameters
                    validated[key] = bool(value)
                    
                else:
                    # Pass through unknown parameters with warning
                    validated[key] = value
                    self.logger.debug(f"Unknown parameter '{key}' passed through without validation")
                    
            except Exception as e:
                errors.append(f"{key}: Validation error - {str(e)}")
                self.logger.error(f"Error validating {key}: {e}")
        
        # Log validation results
        if errors:
            self.logger.error(f"Parameter validation errors: {errors}")
        if warnings:
            self.logger.warning(f"Parameter validation warnings: {warnings}")
            
        self.logger.info(f"Validated {len(validated)} parameters (original: {len(params)})")
        
        return validated
    
    def _validate_numeric(self, name: str, value: Any, constraint: Dict[str, Any]) -> Optional[Union[int, float]]:
        """Validate numeric parameter against constraints"""
        try:
            # Convert to appropriate type
            target_type = constraint.get("type", float)
            if target_type == int:
                num_value = int(float(str(value)))
            else:
                num_value = float(str(value))
            
            # Check min/max bounds
            if "min" in constraint and num_value < constraint["min"]:
                self.logger.warning(f"{name}: Value {num_value} below minimum {constraint['min']}, clamping")
                num_value = constraint["min"]
                
            if "max" in constraint and num_value > constraint["max"]:
                self.logger.warning(f"{name}: Value {num_value} above maximum {constraint['max']}, clamping")
                num_value = constraint["max"]
            
            # Check multiple_of constraint
            if "multiple_of" in constraint and target_type == int:
                multiple = constraint["multiple_of"]
                if num_value % multiple != 0:
                    # Round to nearest multiple
                    num_value = round(num_value / multiple) * multiple
                    self.logger.debug(f"{name}: Rounded to multiple of {multiple}: {num_value}")
            
            return target_type(num_value)
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Cannot convert {name} value '{value}' to {constraint.get('type', 'number')}: {e}")
            return None
    
    def _validate_string_option(self, name: str, value: Any, valid_options: List[str]) -> Optional[str]:
        """Validate string parameter against valid options"""
        str_value = str(value)
        
        # Exact match
        if str_value in valid_options:
            return str_value
            
        # Case-insensitive match
        lower_value = str_value.lower()
        for option in valid_options:
            if option.lower() == lower_value:
                return option
                
        # Use first option as default
        self.logger.warning(f"{name}: Invalid option '{str_value}', using default '{valid_options[0]}'")
        return valid_options[0]
    
    def _sanitize_prompt(self, prompt: Any) -> str:
        """Sanitize prompt text"""
        if not prompt:
            return ""
            
        # Convert to string
        str_prompt = str(prompt)
        
        # Remove potentially problematic characters
        # But keep common prompt syntax like (), [], <>, :, etc.
        sanitized = str_prompt.strip()
        
        # Limit length to prevent issues
        max_length = 2000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            self.logger.warning(f"Prompt truncated to {max_length} characters")
            
        return sanitized
    
    def validate_workflow_inputs(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all inputs in a workflow
        
        Args:
            workflow: Complete workflow dictionary (API format)
            
        Returns:
            Validated workflow
        """
        validated_workflow = workflow.copy()
        
        # Validate each node's inputs
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and "inputs" in node_data:
                node_type = node_data.get("class_type", "unknown")
                
                # Validate numeric inputs based on node type
                if node_type == "EmptyLatentImage":
                    if "width" in node_data["inputs"]:
                        node_data["inputs"]["width"] = self._ensure_multiple_of_8(
                            node_data["inputs"]["width"], "width", 512
                        )
                    if "height" in node_data["inputs"]:
                        node_data["inputs"]["height"] = self._ensure_multiple_of_8(
                            node_data["inputs"]["height"], "height", 512
                        )
                        
                elif node_type == "KSampler":
                    # Validate sampler parameters
                    inputs = node_data["inputs"]
                    if "steps" in inputs:
                        inputs["steps"] = max(1, min(150, int(inputs.get("steps", 20))))
                    if "cfg" in inputs:
                        inputs["cfg"] = max(0.0, min(30.0, float(inputs.get("cfg", 7.0))))
                    if "denoise" in inputs:
                        inputs["denoise"] = max(0.0, min(1.0, float(inputs.get("denoise", 1.0))))
        
        return validated_workflow
    
    def _ensure_multiple_of_8(self, value: Any, name: str, default: int = 512) -> int:
        """Ensure value is multiple of 8 (required for many models)"""
        try:
            int_value = int(float(str(value)))
            if int_value % 8 != 0:
                # Round to nearest multiple of 8
                int_value = round(int_value / 8) * 8
                self.logger.debug(f"{name}: Rounded to multiple of 8: {int_value}")
            return max(64, int_value)  # Minimum 64
        except:
            self.logger.error(f"Cannot convert {name} to valid dimension, using {default}")
            return default