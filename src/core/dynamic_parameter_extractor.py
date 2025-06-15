"""
Dynamic workflow parameter extraction with automatic node type discovery
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from loguru import logger


class DynamicParameterExtractor:
    """Extract parameters from ANY ComfyUI workflow nodes dynamically"""
    
    def __init__(self, config_dir: Path = Path("config")):
        self.logger = logger
        self.config_dir = config_dir
        self.discovered_types_path = config_dir / "discovered_node_types.json"
        self.parameter_config_path = config_dir / "3d_parameters_config.json"
        
        # Load any previously discovered node types
        self.discovered_types = self._load_discovered_types()
        
    def _load_discovered_types(self) -> Dict[str, Any]:
        """Load previously discovered node types and their widget mappings"""
        if self.discovered_types_path.exists():
            try:
                with open(self.discovered_types_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load discovered types: {e}")
        return {}
    
    def extract_all_parameters(self, workflow_path: Path, selected_nodes: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Extract parameters from all nodes in workflow, not just known types
        
        Args:
            workflow_path: Path to workflow JSON file
            selected_nodes: Optional set of node keys (type_id) to extract parameters from
        
        Returns:
            Dictionary of parameters with their metadata
        """
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            parameters = {}
            nodes = workflow.get("nodes", [])
            
            # If selected_nodes is provided, load from config
            if selected_nodes is None and self.parameter_config_path.exists():
                try:
                    with open(self.parameter_config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        selected_nodes = set(config.get("selected_nodes", []))
                except Exception as e:
                    self.logger.error(f"Failed to load parameter config: {e}")
                    selected_nodes = set()
            
            for node in nodes:
                node_type = node.get("type", "")
                node_id = str(node.get("id", ""))
                node_key = f"{node_type}_{node_id}"
                
                # Skip if we have a selection and this node isn't selected
                if selected_nodes and node_key not in selected_nodes:
                    continue
                
                # Extract parameters for this node
                node_params = self._extract_node_parameters_dynamic(node)
                
                # Add each parameter with unique key
                for param_idx, param_data in node_params.items():
                    unique_key = f"{node_type}_{node_id}_{param_idx}"
                    parameters[unique_key] = param_data
            
            self.logger.info(f"Extracted {len(parameters)} parameters from {workflow_path.name}")
            return parameters
            
        except Exception as e:
            self.logger.error(f"Failed to extract parameters from {workflow_path}: {e}")
            return {}
    
    def _extract_node_parameters_dynamic(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically extract parameters from any node based on its widgets_values
        """
        params = {}
        node_type = node.get("type", "")
        widgets_values = node.get("widgets_values", [])
        
        if not widgets_values:
            return params
        
        # Get node inputs to help identify parameter names
        inputs = node.get("inputs", [])
        
        # Try to intelligently map widget values to parameters
        for idx, value in enumerate(widgets_values):
            param_data = {
                "node_id": node.get("id"),
                "node_type": node_type,
                "widget_index": idx,
                "current_value": value
            }
            
            # Determine parameter type and constraints based on value
            if isinstance(value, bool):
                param_data.update({
                    "type": "bool",
                    "ui_name": f"Parameter {idx}",
                    "default": value
                })
            elif isinstance(value, int):
                # Try to guess reasonable bounds
                if 0 <= value <= 1:
                    param_data.update({
                        "type": "int",
                        "ui_name": f"Parameter {idx}",
                        "min": 0,
                        "max": 1,
                        "default": value
                    })
                elif 0 <= value <= 100:
                    param_data.update({
                        "type": "int",
                        "ui_name": f"Parameter {idx}",
                        "min": 0,
                        "max": 100,
                        "default": value
                    })
                else:
                    param_data.update({
                        "type": "int",
                        "ui_name": f"Parameter {idx}",
                        "min": 0,
                        "max": max(value * 2, 10000),
                        "default": value
                    })
            elif isinstance(value, float):
                # Try to guess reasonable bounds for floats
                if 0.0 <= value <= 1.0:
                    param_data.update({
                        "type": "float",
                        "ui_name": f"Parameter {idx}",
                        "min": 0.0,
                        "max": 1.0,
                        "default": value
                    })
                else:
                    param_data.update({
                        "type": "float",
                        "ui_name": f"Parameter {idx}",
                        "min": 0.0,
                        "max": max(value * 2, 100.0),
                        "default": value
                    })
            elif isinstance(value, str):
                # Check if it's a choice (filename pattern) or text
                if value.endswith(('.png', '.jpg', '.safetensors', '.ckpt', '.pt', '.pth')):
                    param_data.update({
                        "type": "choice",
                        "ui_name": f"Parameter {idx}",
                        "default": value
                    })
                else:
                    param_data.update({
                        "type": "text",
                        "ui_name": f"Parameter {idx}",
                        "default": value,
                        "multiline": len(value) > 50
                    })
            else:
                # Unknown type, store as is
                param_data.update({
                    "type": "unknown",
                    "ui_name": f"Parameter {idx}",
                    "default": value
                })
            
            # Try to improve parameter names based on common patterns
            param_data["ui_name"] = self._guess_parameter_name(node_type, idx, value, inputs)
            
            params[idx] = param_data
        
        return params
    
    def _guess_parameter_name(self, node_type: str, idx: int, value: Any, inputs: List[Dict]) -> str:
        """
        Try to guess a meaningful parameter name based on node type and value patterns
        """
        # Common parameter patterns
        if isinstance(value, str):
            if 'checkpoint' in value.lower() or value.endswith('.ckpt'):
                return "Checkpoint"
            elif 'lora' in value.lower():
                return "LoRA Model"
            elif 'vae' in value.lower():
                return "VAE Model"
            elif 'controlnet' in value.lower():
                return "ControlNet Model"
            elif value.endswith('.png') or value.endswith('.jpg'):
                return "Image"
        
        # Check specific node types
        if node_type == "KSampler":
            names = ["Seed", "Control After Generate", "Steps", "CFG", "Sampler", "Scheduler", "Denoise"]
            if idx < len(names):
                return names[idx]
        elif node_type == "CLIPTextEncode":
            return "Prompt"
        elif node_type == "EmptyLatentImage":
            names = ["Width", "Height", "Batch Size"]
            if idx < len(names):
                return names[idx]
        elif node_type == "FluxGuidance":
            return "Guidance"
        elif node_type == "Note":
            return "Note Text"
        
        # Try to use input information if available
        if inputs and idx < len(inputs):
            input_name = inputs[idx].get("name", "")
            if input_name:
                return input_name.replace("_", " ").title()
        
        # Default with type hint
        if isinstance(value, bool):
            return f"Toggle {idx}"
        elif isinstance(value, (int, float)):
            return f"Value {idx}"
        elif isinstance(value, str):
            return f"Text {idx}"
        
        return f"Parameter {idx}"
    
    def update_workflow_with_parameters(self, workflow_path: Path, parameters: Dict[str, Any]) -> bool:
        """
        Update workflow with new parameter values, supporting dynamic nodes
        """
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            nodes = workflow.get("nodes", [])
            
            # Update each node's parameters
            for param_key, param_value in parameters.items():
                # Parse the parameter key: node_type_node_id_widget_index
                parts = param_key.rsplit('_', 1)
                if len(parts) == 2:
                    node_key, widget_idx = parts
                    widget_idx = int(widget_idx)
                    
                    # Split node_key into type and id
                    type_parts = node_key.rsplit('_', 1)
                    if len(type_parts) == 2:
                        node_type, node_id = type_parts
                        
                        # Find and update the node
                        for node in nodes:
                            if str(node.get("id")) == node_id and node.get("type") == node_type:
                                widgets_values = node.get("widgets_values", [])
                                
                                # Ensure list is long enough
                                while len(widgets_values) <= widget_idx:
                                    widgets_values.append(None)
                                
                                # Update the value
                                widgets_values[widget_idx] = param_value
                                node["widgets_values"] = widgets_values
                                break
            
            # Save updated workflow
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2)
            
            self.logger.info(f"Updated workflow parameters in {workflow_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow parameters: {e}")
            return False
    
    def save_discovered_mappings(self, node_type: str, mappings: Dict[int, str]):
        """
        Save user-defined parameter name mappings for a node type
        """
        discovered = self._load_discovered_types()
        
        if node_type not in discovered:
            discovered[node_type] = {
                "first_seen": datetime.now().isoformat(),
                "parameter_names": {}
            }
        
        discovered[node_type]["parameter_names"] = mappings
        
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.discovered_types_path, 'w', encoding='utf-8') as f:
                json.dump(discovered, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved parameter mappings for {node_type}")
        except Exception as e:
            self.logger.error(f"Failed to save discovered mappings: {e}")