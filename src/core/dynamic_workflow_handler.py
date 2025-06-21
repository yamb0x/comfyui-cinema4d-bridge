"""
Dynamic Workflow Handler - Truly Dynamic System for ANY ComfyUI Workflow
Handles prompt injection, parameter updates, and node management dynamically
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from loguru import logger


class DynamicWorkflowHandler:
    """
    Handles any ComfyUI workflow dynamically without hardcoding node types
    """
    
    def __init__(self):
        self.logger = logger
        
    def inject_prompts_dynamic(self, workflow: Dict[str, Any], positive_prompt: str, negative_prompt: str) -> Dict[str, Any]:
        """
        Inject prompts into any workflow format dynamically
        
        Args:
            workflow: The workflow dictionary (can be API or UI format)
            positive_prompt: The positive prompt text
            negative_prompt: The negative prompt text
            
        Returns:
            Updated workflow with prompts injected
        """
        if not workflow:
            return workflow
            
        # Deep copy to avoid modifying original
        workflow_copy = json.loads(json.dumps(workflow))
        
        # Detect workflow format
        is_ui_format = "nodes" in workflow_copy and isinstance(workflow_copy.get("nodes"), list)
        
        positive_injected = False
        negative_injected = False
        
        if is_ui_format:
            # UI format - nodes is an array
            nodes = workflow_copy.get("nodes", [])
            
            # First pass: find prompt nodes by type and title
            for node in nodes:
                if self._is_text_encode_node(node):
                    node_id = node.get("id", "unknown")
                    title = str(node.get("title", "")).lower()
                    
                    # Inject based on title
                    if not positive_injected and self._is_positive_prompt(title):
                        if "widgets_values" in node and len(node["widgets_values"]) > 0:
                            node["widgets_values"][0] = positive_prompt
                            self.logger.info(f"Injected positive prompt into node {node_id}")
                            positive_injected = True
                    
                    elif not negative_injected and self._is_negative_prompt(title):
                        if "widgets_values" in node and len(node["widgets_values"]) > 0:
                            node["widgets_values"][0] = negative_prompt
                            self.logger.info(f"Injected negative prompt into node {node_id}")
                            negative_injected = True
            
            # Second pass: if not found by title, use connection analysis
            if not positive_injected or not negative_injected:
                self._inject_by_connections(workflow_copy, positive_prompt, negative_prompt, 
                                           positive_injected, negative_injected)
                                           
        else:
            # API format - nodes is a dict
            for node_id, node_data in workflow_copy.items():
                if isinstance(node_data, dict) and self._is_text_encode_node(node_data):
                    # Try to identify by metadata or connections
                    title = str(node_data.get("_meta", {}).get("title", "")).lower()
                    
                    if not positive_injected and self._is_positive_prompt(title):
                        if "inputs" in node_data:
                            node_data["inputs"]["text"] = positive_prompt
                            self.logger.info(f"Injected positive prompt into API node {node_id}")
                            positive_injected = True
                    
                    elif not negative_injected and self._is_negative_prompt(title):
                        if "inputs" in node_data:
                            node_data["inputs"]["text"] = negative_prompt
                            self.logger.info(f"Injected negative prompt into API node {node_id}")
                            negative_injected = True
        
        if not positive_injected:
            self.logger.warning("Could not find positive prompt node to inject")
        if not negative_injected:
            self.logger.warning("Could not find negative prompt node to inject")
            
        return workflow_copy
    
    def update_latent_size_dynamic(self, workflow: Dict[str, Any], width: int, height: int, batch_size: int) -> Dict[str, Any]:
        """
        Update any latent/empty image node with size parameters dynamically
        
        Args:
            workflow: The workflow dictionary
            width: Image width
            height: Image height
            batch_size: Number of images to generate
            
        Returns:
            Updated workflow
        """
        workflow_copy = json.loads(json.dumps(workflow))
        
        # Detect workflow format
        is_ui_format = "nodes" in workflow_copy and isinstance(workflow_copy.get("nodes"), list)
        
        if is_ui_format:
            # UI format
            for node in workflow_copy.get("nodes", []):
                if self._is_latent_node(node):
                    node_id = node.get("id", "unknown")
                    
                    # Update widgets_values for size parameters
                    if "widgets_values" in node:
                        # Most latent nodes have [width, height, batch_size] order
                        if len(node["widgets_values"]) >= 3:
                            node["widgets_values"][0] = width
                            node["widgets_values"][1] = height
                            node["widgets_values"][2] = batch_size
                            self.logger.info(f"Updated latent node {node_id}: {width}x{height}, batch={batch_size}")
        else:
            # API format
            for node_id, node_data in workflow_copy.items():
                if isinstance(node_data, dict) and self._is_latent_node(node_data):
                    if "inputs" in node_data:
                        node_data["inputs"]["width"] = width
                        node_data["inputs"]["height"] = height
                        node_data["inputs"]["batch_size"] = batch_size
                        self.logger.info(f"Updated API latent node {node_id}: {width}x{height}, batch={batch_size}")
        
        return workflow_copy
    
    def organize_parameters_by_category(self, workflow: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize workflow parameters by category for UI display
        
        Returns:
            Dictionary with categories as keys and node info as values
        """
        categories = {
            "samplers": [],
            "models": [],
            "loras": [],
            "prompts": [],
            "latents": [],
            "other": []
        }
        
        # Detect workflow format
        is_ui_format = "nodes" in workflow and isinstance(workflow.get("nodes"), list)
        
        if is_ui_format:
            nodes = workflow.get("nodes", [])
        else:
            # Convert API format to list for uniform processing
            nodes = [{"id": nid, **ndata} for nid, ndata in workflow.items() if isinstance(ndata, dict)]
        
        for node in nodes:
            node_info = self._extract_node_info(node, is_ui_format)
            category = self._categorize_node(node_info["type"])
            categories[category].append(node_info)
        
        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}
        
        return categories
    
    def _is_text_encode_node(self, node: Dict[str, Any]) -> bool:
        """Check if node is a text encoding node"""
        node_type = node.get("type") or node.get("class_type", "")
        return "textencod" in node_type.lower() or "clip" in node_type.lower()
    
    def _is_latent_node(self, node: Dict[str, Any]) -> bool:
        """Check if node is a latent/empty image node"""
        node_type = node.get("type") or node.get("class_type", "")
        return "emptylatent" in node_type.lower() or "latentimage" in node_type.lower()
    
    def _is_positive_prompt(self, text: str) -> bool:
        """Check if text indicates positive prompt"""
        positive_keywords = ["positive", "pos", "prompt", "main"]
        return any(keyword in text.lower() for keyword in positive_keywords) and "negative" not in text.lower()
    
    def _is_negative_prompt(self, text: str) -> bool:
        """Check if text indicates negative prompt"""
        negative_keywords = ["negative", "neg"]
        return any(keyword in text.lower() for keyword in negative_keywords)
    
    def _inject_by_connections(self, workflow: Dict[str, Any], positive_prompt: str, 
                              negative_prompt: str, positive_done: bool, negative_done: bool):
        """Inject prompts by analyzing node connections"""
        # This is a more complex analysis that looks at how nodes are connected
        # to determine which is positive and which is negative
        # For now, we'll use a simple heuristic based on node order
        
        nodes = workflow.get("nodes", [])
        text_nodes = [n for n in nodes if self._is_text_encode_node(n)]
        
        if len(text_nodes) >= 2 and not positive_done and not negative_done:
            # Assume first is positive, second is negative
            if "widgets_values" in text_nodes[0]:
                text_nodes[0]["widgets_values"][0] = positive_prompt
                self.logger.info(f"Injected positive prompt by position (node {text_nodes[0].get('id')})")
            
            if "widgets_values" in text_nodes[1]:
                text_nodes[1]["widgets_values"][0] = negative_prompt
                self.logger.info(f"Injected negative prompt by position (node {text_nodes[1].get('id')})")
    
    def _extract_node_info(self, node: Dict[str, Any], is_ui_format: bool) -> Dict[str, Any]:
        """Extract relevant info from a node"""
        if is_ui_format:
            return {
                "id": node.get("id", ""),
                "type": node.get("type", ""),
                "title": node.get("title", "") or node.get("properties", {}).get("Node name for S&R", ""),
                "widgets_values": node.get("widgets_values", []),
                "inputs": node.get("inputs", []),
                "outputs": node.get("outputs", [])
            }
        else:
            # API format
            return {
                "id": node.get("id", ""),
                "type": node.get("class_type", ""),
                "title": node.get("_meta", {}).get("title", ""),
                "inputs": node.get("inputs", {}),
                "outputs": []  # API format doesn't include outputs
            }
    
    def _categorize_node(self, node_type: str) -> str:
        """Categorize node by type"""
        node_type_lower = node_type.lower()
        
        if "sampler" in node_type_lower:
            return "samplers"
        elif any(word in node_type_lower for word in ["loader", "checkpoint", "unet", "vae"]):
            return "models"
        elif "lora" in node_type_lower:
            return "loras"
        elif any(word in node_type_lower for word in ["textencod", "clip", "prompt"]):
            return "prompts"
        elif any(word in node_type_lower for word in ["latent", "emptylatent"]):
            return "latents"
        else:
            return "other"
    
    def add_bypass_control(self, node_id: str, node_type: str) -> Dict[str, Any]:
        """
        Create bypass control info for a node
        
        Returns:
            Control widget info for bypassing the node
        """
        return {
            "type": "checkbox",
            "label": "Bypass",
            "node_id": node_id,
            "node_type": node_type,
            "action": "bypass",
            "default": False
        }
    
    def remove_node_from_workflow(self, workflow: Dict[str, Any], node_id: str) -> Tuple[Dict[str, Any], bool]:
        """
        Remove a node from workflow and reconnect links
        
        Returns:
            (Updated workflow, success)
        """
        workflow_copy = json.loads(json.dumps(workflow))
        
        try:
            # Handle UI format
            if "nodes" in workflow_copy and isinstance(workflow_copy.get("nodes"), list):
                # Find and remove node
                nodes = workflow_copy["nodes"]
                node_to_remove = None
                node_index = -1
                
                for i, node in enumerate(nodes):
                    if str(node.get("id")) == str(node_id):
                        node_to_remove = node
                        node_index = i
                        break
                
                if node_to_remove:
                    # Remove the node
                    nodes.pop(node_index)
                    
                    # Update links to bypass removed node
                    if "links" in workflow_copy:
                        self._reconnect_links(workflow_copy, node_id, node_to_remove)
                    
                    self.logger.info(f"Removed node {node_id} from workflow")
                    return workflow_copy, True
                else:
                    self.logger.warning(f"Node {node_id} not found in workflow")
                    return workflow_copy, False
                    
            else:
                # API format
                if str(node_id) in workflow_copy:
                    del workflow_copy[str(node_id)]
                    self.logger.info(f"Removed node {node_id} from API workflow")
                    return workflow_copy, True
                else:
                    self.logger.warning(f"Node {node_id} not found in API workflow")
                    return workflow_copy, False
                    
        except Exception as e:
            self.logger.error(f"Error removing node {node_id}: {e}")
            return workflow_copy, False
    
    def _reconnect_links(self, workflow: Dict[str, Any], removed_node_id: str, removed_node: Dict[str, Any]):
        """Reconnect links after removing a node"""
        # This is a simplified version - a full implementation would need to
        # analyze input/output types and properly reconnect compatible links
        links = workflow.get("links", [])
        
        # Find links connected to the removed node
        input_links = []
        output_links = []
        
        for link in links:
            if len(link) >= 5:
                # link format: [link_id, from_node, from_slot, to_node, to_slot, type]
                if str(link[3]) == str(removed_node_id):
                    input_links.append(link)
                elif str(link[1]) == str(removed_node_id):
                    output_links.append(link)
        
        # For simple cases (1 input, 1 output), we can reconnect directly
        if len(input_links) == 1 and len(output_links) == 1:
            # Create new link bypassing the removed node
            new_link = [
                max([l[0] for l in links]) + 1,  # New link ID
                input_links[0][1],  # From node
                input_links[0][2],  # From slot
                output_links[0][3],  # To node
                output_links[0][4],  # To slot
                input_links[0][5] if len(input_links[0]) > 5 else "UNKNOWN"  # Type
            ]
            
            # Remove old links and add new one
            workflow["links"] = [l for l in links if l not in input_links + output_links]
            workflow["links"].append(new_link)
            
            self.logger.info(f"Reconnected links bypassing removed node {removed_node_id}")