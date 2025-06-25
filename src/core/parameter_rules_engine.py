"""
Parameter Rules Engine for ComfyUI to Cinema4D Bridge
Intelligent parameter organization and filtering based on priority rules
"""

from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class ParameterPriority(Enum):
    """Parameter priority levels for display ordering"""
    ESSENTIAL = 1      # Critical parameters like seed, steps, cfg
    MODEL = 2          # Model selection parameters
    DIMENSIONS = 3     # Size and dimension parameters
    ADVANCED = 4       # Advanced technical parameters
    EXPERIMENTAL = 5   # Experimental or rarely used parameters
    HIDDEN = 99        # Parameters that should be hidden


@dataclass
class ParameterRule:
    """Rule definition for parameter handling"""
    node_type: str
    param_name: str
    priority: ParameterPriority
    group: str
    visible: bool = True
    display_name: Optional[str] = None


class ParameterRulesEngine:
    """Engine for applying parameter organization and filtering rules"""
    
    # Default parameter rules by node type and parameter name
    DEFAULT_RULES = [
        # KSampler - Essential parameters
        ParameterRule("KSampler", "seed", ParameterPriority.ESSENTIAL, "Generation", display_name="Seed"),
        ParameterRule("KSampler", "steps", ParameterPriority.ESSENTIAL, "Generation", display_name="Steps"),
        ParameterRule("KSampler", "cfg", ParameterPriority.ESSENTIAL, "Generation", display_name="CFG Scale"),
        ParameterRule("KSampler", "sampler_name", ParameterPriority.ESSENTIAL, "Generation", display_name="Sampler"),
        ParameterRule("KSampler", "scheduler", ParameterPriority.ADVANCED, "Generation", display_name="Scheduler"),
        ParameterRule("KSampler", "denoise", ParameterPriority.ADVANCED, "Generation", display_name="Denoise"),
        
        # KSamplerAdvanced
        ParameterRule("KSamplerAdvanced", "noise_seed", ParameterPriority.ESSENTIAL, "Generation", display_name="Seed"),
        ParameterRule("KSamplerAdvanced", "steps", ParameterPriority.ESSENTIAL, "Generation", display_name="Steps"),
        ParameterRule("KSamplerAdvanced", "cfg", ParameterPriority.ESSENTIAL, "Generation", display_name="CFG Scale"),
        ParameterRule("KSamplerAdvanced", "sampler_name", ParameterPriority.ESSENTIAL, "Generation", display_name="Sampler"),
        
        # Model loading - High priority
        ParameterRule("CheckpointLoaderSimple", "ckpt_name", ParameterPriority.MODEL, "Models", display_name="Checkpoint"),
        ParameterRule("CheckpointLoader", "ckpt_name", ParameterPriority.MODEL, "Models", display_name="Checkpoint"),
        ParameterRule("UNETLoader", "unet_name", ParameterPriority.MODEL, "Models", display_name="UNET Model"),
        ParameterRule("VAELoader", "vae_name", ParameterPriority.MODEL, "Models", display_name="VAE Model"),
        ParameterRule("LoraLoader", "lora_name", ParameterPriority.MODEL, "Models", display_name="LoRA Model"),
        ParameterRule("LoraLoader", "strength_model", ParameterPriority.MODEL, "Models", display_name="LoRA Strength"),
        ParameterRule("LoraLoader", "strength_clip", ParameterPriority.MODEL, "Models", display_name="CLIP Strength"),
        
        # Dimensions - Medium priority
        ParameterRule("EmptyLatentImage", "width", ParameterPriority.DIMENSIONS, "Dimensions", display_name="Width"),
        ParameterRule("EmptyLatentImage", "height", ParameterPriority.DIMENSIONS, "Dimensions", display_name="Height"),
        ParameterRule("EmptyLatentImage", "batch_size", ParameterPriority.DIMENSIONS, "Dimensions", display_name="Batch Size"),
        ParameterRule("EmptySD3LatentImage", "width", ParameterPriority.DIMENSIONS, "Dimensions", display_name="Width"),
        ParameterRule("EmptySD3LatentImage", "height", ParameterPriority.DIMENSIONS, "Dimensions", display_name="Height"),
        
        # CLIP/Prompt - Hidden (handled separately in UI)
        ParameterRule("CLIPTextEncode", "text", ParameterPriority.HIDDEN, "Prompts", visible=False),
        
        # Flux specific
        ParameterRule("FluxGuidance", "guidance", ParameterPriority.ESSENTIAL, "Generation", display_name="Guidance"),
        
        # Hidden nodes
        ParameterRule("Reroute", "*", ParameterPriority.HIDDEN, "Hidden", visible=False),
        ParameterRule("LoadImage", "*", ParameterPriority.HIDDEN, "Hidden", visible=False),
        ParameterRule("SaveImage", "*", ParameterPriority.HIDDEN, "Hidden", visible=False),
        ParameterRule("PreviewImage", "*", ParameterPriority.HIDDEN, "Hidden", visible=False),
    ]
    
    # Node type priority overrides
    NODE_PRIORITY_ORDER = [
        "KSampler",
        "KSamplerAdvanced",
        "CheckpointLoaderSimple",
        "CheckpointLoader", 
        "UNETLoader",
        "VAELoader",
        "LoraLoader",
        "FluxGuidance",
        "EmptyLatentImage",
        "EmptySD3LatentImage",
        "ControlNetLoader",
        "ControlNetApplyAdvanced",
    ]
    
    def __init__(self):
        """Initialize the rules engine"""
        self.logger = logger
        self._rules_map = self._build_rules_map()
        self._custom_rules: List[ParameterRule] = []
    
    def _build_rules_map(self) -> Dict[str, Dict[str, ParameterRule]]:
        """Build a map of rules for quick lookup"""
        rules_map = {}
        
        for rule in self.DEFAULT_RULES:
            if rule.node_type not in rules_map:
                rules_map[rule.node_type] = {}
            
            rules_map[rule.node_type][rule.param_name] = rule
        
        return rules_map
    
    def add_custom_rule(self, rule: ParameterRule) -> None:
        """Add a custom parameter rule
        
        Args:
            rule: Custom rule to add
        """
        self._custom_rules.append(rule)
        
        # Update rules map
        if rule.node_type not in self._rules_map:
            self._rules_map[rule.node_type] = {}
        
        self._rules_map[rule.node_type][rule.param_name] = rule
        
        self.logger.debug(f"Added custom rule for {rule.node_type}.{rule.param_name}")
    
    def get_parameter_priority(self, node_type: str, param_name: str) -> ParameterPriority:
        """Get the priority for a specific parameter
        
        Args:
            node_type: Type of the node
            param_name: Name of the parameter
            
        Returns:
            Parameter priority
        """
        # Check for specific rule
        if node_type in self._rules_map:
            # Check for exact match
            if param_name in self._rules_map[node_type]:
                return self._rules_map[node_type][param_name].priority
            
            # Check for wildcard match
            if "*" in self._rules_map[node_type]:
                return self._rules_map[node_type]["*"].priority
        
        # Default priority based on common patterns
        if param_name in ["seed", "steps", "cfg", "sampler_name"]:
            return ParameterPriority.ESSENTIAL
        elif "model" in param_name.lower() or "checkpoint" in param_name.lower():
            return ParameterPriority.MODEL
        elif param_name in ["width", "height", "size", "resolution"]:
            return ParameterPriority.DIMENSIONS
        else:
            return ParameterPriority.ADVANCED
    
    def get_parameter_group(self, node_type: str, param_name: str) -> str:
        """Get the group for a specific parameter
        
        Args:
            node_type: Type of the node
            param_name: Name of the parameter
            
        Returns:
            Parameter group name
        """
        # Check for specific rule
        if node_type in self._rules_map:
            if param_name in self._rules_map[node_type]:
                return self._rules_map[node_type][param_name].group
            elif "*" in self._rules_map[node_type]:
                return self._rules_map[node_type]["*"].group
        
        # Default grouping
        priority = self.get_parameter_priority(node_type, param_name)
        if priority == ParameterPriority.ESSENTIAL:
            return "Generation"
        elif priority == ParameterPriority.MODEL:
            return "Models"
        elif priority == ParameterPriority.DIMENSIONS:
            return "Dimensions"
        else:
            return "Advanced"
    
    def is_parameter_visible(self, node_type: str, param_name: str) -> bool:
        """Check if a parameter should be visible
        
        Args:
            node_type: Type of the node
            param_name: Name of the parameter
            
        Returns:
            True if parameter should be visible
        """
        # Check for specific rule
        if node_type in self._rules_map:
            if param_name in self._rules_map[node_type]:
                return self._rules_map[node_type][param_name].visible
            elif "*" in self._rules_map[node_type]:
                return self._rules_map[node_type]["*"].visible
        
        # Default to visible
        return True
    
    def get_display_name(self, node_type: str, param_name: str) -> str:
        """Get the display name for a parameter
        
        Args:
            node_type: Type of the node
            param_name: Name of the parameter
            
        Returns:
            Display name for the parameter
        """
        # Check for specific rule with display name
        if node_type in self._rules_map:
            if param_name in self._rules_map[node_type]:
                rule = self._rules_map[node_type][param_name]
                if rule.display_name:
                    return rule.display_name
        
        # Default formatting - convert snake_case to Title Case
        return param_name.replace("_", " ").title()
    
    def organize_parameters(self, parameters: Dict[str, Any]) -> OrderedDict:
        """Organize parameters by priority and groups
        
        Args:
            parameters: Raw parameters dictionary
            
        Returns:
            Organized parameters in OrderedDict
        """
        # Group parameters by priority and group
        grouped = {}
        
        for param_key, param_data in parameters.items():
            node_type = param_data.get("node_type", "Unknown")
            param_name = param_data.get("param_name", param_key)
            
            priority = self.get_parameter_priority(node_type, param_name)
            group = self.get_parameter_group(node_type, param_name)
            
            # Add display name
            param_data["display_name"] = self.get_display_name(node_type, param_name)
            param_data["priority"] = priority.value
            param_data["group"] = group
            
            # Create group structure
            if priority.value not in grouped:
                grouped[priority.value] = {}
            if group not in grouped[priority.value]:
                grouped[priority.value][group] = OrderedDict()
            
            grouped[priority.value][group][param_key] = param_data
        
        # Build ordered result
        result = OrderedDict()
        
        # Add parameters in priority order
        for priority in sorted(grouped.keys()):
            for group in sorted(grouped[priority].keys()):
                # Add group header in result
                for param_key, param_data in grouped[priority][group].items():
                    result[param_key] = param_data
        
        self.logger.debug(f"Organized {len(result)} parameters into groups")
        return result
    
    def filter_visible_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Filter parameters to only include visible ones
        
        Args:
            parameters: Parameters dictionary
            
        Returns:
            Filtered parameters
        """
        filtered = {}
        
        for param_key, param_data in parameters.items():
            node_type = param_data.get("node_type", "Unknown")
            param_name = param_data.get("param_name", param_key)
            
            if self.is_parameter_visible(node_type, param_name):
                filtered[param_key] = param_data
        
        self.logger.debug(f"Filtered {len(parameters)} parameters to {len(filtered)} visible")
        return filtered
    
    def get_parameter_groups(self, parameters: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """Get parameters organized by groups
        
        Args:
            parameters: Parameters dictionary
            
        Returns:
            List of (group_name, parameter_keys) tuples
        """
        groups = {}
        
        for param_key, param_data in parameters.items():
            group = param_data.get("group", "Other")
            
            if group not in groups:
                groups[group] = []
            
            groups[group].append(param_key)
        
        # Sort groups by priority
        group_priority = {
            "Generation": 1,
            "Models": 2,
            "Dimensions": 3,
            "Advanced": 4,
            "Other": 5
        }
        
        sorted_groups = sorted(
            groups.items(),
            key=lambda x: group_priority.get(x[0], 99)
        )
        
        return sorted_groups
    
    def apply_node_type_ordering(self, parameters: Dict[str, Any]) -> OrderedDict:
        """Apply node type ordering to parameters
        
        Args:
            parameters: Parameters dictionary
            
        Returns:
            Ordered parameters by node type priority
        """
        # Group by node type
        by_node_type = {}
        
        for param_key, param_data in parameters.items():
            node_type = param_data.get("node_type", "Unknown")
            
            if node_type not in by_node_type:
                by_node_type[node_type] = OrderedDict()
            
            by_node_type[node_type][param_key] = param_data
        
        # Build result in priority order
        result = OrderedDict()
        
        # Add known node types in order
        for node_type in self.NODE_PRIORITY_ORDER:
            if node_type in by_node_type:
                result.update(by_node_type[node_type])
        
        # Add remaining node types
        for node_type, params in by_node_type.items():
            if node_type not in self.NODE_PRIORITY_ORDER:
                result.update(params)
        
        return result