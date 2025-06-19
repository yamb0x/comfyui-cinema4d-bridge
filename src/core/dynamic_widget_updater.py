"""
Dynamic Widget Updater - Truly Dynamic Parameter Collection
Updates workflow widgets_values from UI widgets for ANY node type
"""

from typing import Dict, Any, List
from loguru import logger


class DynamicWidgetUpdater:
    """
    Dynamically updates workflow widgets_values from UI widgets
    Works for ANY node type without hardcoding
    """
    
    def __init__(self):
        self.logger = logger
    
    def update_workflow_from_ui_widgets(self, workflow: Dict[str, Any], parameter_widgets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update workflow widgets_values from UI widgets - COMPLETELY DYNAMIC
        
        Args:
            workflow: The ComfyUI workflow dictionary
            parameter_widgets: Dictionary of tracked UI widgets
            
        Returns:
            Updated workflow with UI widget values
        """
        if not parameter_widgets:
            self.logger.info("No UI widgets to process - using original workflow values")
            return workflow
        
        updated_nodes = {}  # Track updates for logging
        
        # Process each UI widget and update corresponding workflow node
        for widget_key, widget_info in parameter_widgets.items():
            try:
                # Parse widget key: NodeType_NodeID_ParamIndex
                parts = widget_key.split('_')
                if len(parts) >= 3:
                    node_id = parts[-2]
                    param_idx = int(parts[-1])
                    node_type = '_'.join(parts[:-2])
                    
                    # Get current value from UI widget
                    current_value = widget_info['get_value']()
                    
                    # Find and update the corresponding workflow node
                    workflow_nodes = workflow.get("nodes", [])
                    for node in workflow_nodes:
                        if str(node.get("id")) == node_id and node.get("type") == node_type:
                            # Get or create widgets_values array
                            widgets_values = node.get("widgets_values", [])
                            
                            # Ensure array is long enough
                            while len(widgets_values) <= param_idx:
                                widgets_values.append(None)
                            
                            # Store old value for logging
                            old_value = widgets_values[param_idx]
                            
                            # Update with UI widget value
                            widgets_values[param_idx] = current_value
                            node["widgets_values"] = widgets_values
                            
                            # Track update for logging
                            if node_id not in updated_nodes:
                                updated_nodes[node_id] = {'type': node_type, 'changes': []}
                            updated_nodes[node_id]['changes'].append({
                                'param': param_idx,
                                'old': old_value,
                                'new': current_value
                            })
                            
                            break
                    
            except Exception as e:
                self.logger.warning(f"Failed to update workflow from widget {widget_key}: {e}")
        
        # Log summary of dynamic updates
        if updated_nodes:
            self.logger.debug(f"Dynamically updated {len(updated_nodes)} nodes from UI widgets")
            for node_id, info in updated_nodes.items():
                self.logger.debug(f"  {info['type']} node {node_id}: {len(info['changes'])} parameters updated")
        else:
            self.logger.debug("No workflow nodes were updated from UI widgets")
        
        return workflow