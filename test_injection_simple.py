#!/usr/bin/env python3
"""
Simple parameter injection test without unicode issues
"""

import json
import sys
from pathlib import Path

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.workflow_manager import WorkflowManager
    
    def test_parameter_injection():
        """Test parameter injection with the workflow manager"""
        
        print("Parameter Injection Verification")
        print("=" * 50)
        
        # Create workflow manager
        workflows_dir = Path("workflows")
        manager = WorkflowManager(workflows_dir)
        
        # Load the API workflow
        workflow = manager.load_workflow("generate_images_api.json")
        if not workflow:
            print("Failed to load workflow")
            return False
        
        print("Workflow loaded successfully")
        
        # Check if workflow is UI format (has nodes array)
        if "nodes" in workflow:
            print("Detected UI format workflow")
            
            # Find node 10 (KSampler)
            node_10 = None
            for node in workflow["nodes"]:
                if node.get("id") == 10:
                    node_10 = node
                    break
            
            if not node_10:
                print("ERROR: KSampler node (10) not found")
                return False
                
            # Get original widgets_values
            original_widgets = node_10.get("widgets_values", [])
            print(f"Original KSampler widgets: {original_widgets}")
            
        else:
            print("Detected API format workflow")
            # Check original node 10 values
            if "10" in workflow:
                original_inputs = workflow["10"]["inputs"]
                print(f"Original KSampler inputs: {original_inputs}")
        
        # Test parameters
        test_params = {
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras", 
            "cfg": 2.5,
            "steps": 15,
            "seed_control": "randomize",
            "positive_prompt": "test prompt",
            "negative_prompt": "test negative",
            "seed": 999,
            "lora1_model": "deep_sea_creatures_cts.safetensors",
            "lora1_strength": 0.9,
            "lora1_active": True,
            "lora2_model": "aidmaFLUXpro1.1-FLUX-V0.1.safetensors", 
            "lora2_strength": 0.7,
            "lora2_active": True
        }
        
        print(f"\nInjecting test parameters:")
        for key, value in test_params.items():
            print(f"  {key}: {value}")
        
        # Inject parameters
        result_workflow = manager.inject_parameters_comfyui(workflow, test_params)
        
        # Verify results
        print(f"\nAfter injection:")
        
        if "nodes" in result_workflow:
            # UI format verification
            node_10 = None
            node_18 = None
            node_19 = None
            
            for node in result_workflow["nodes"]:
                if node.get("id") == 10:
                    node_10 = node
                elif node.get("id") == 18:
                    node_18 = node
                elif node.get("id") == 19:
                    node_19 = node
            
            if node_10:
                widgets = node_10.get("widgets_values", [])
                print(f"  KSampler widgets after injection: {widgets}")
                
                if len(widgets) >= 6:
                    print(f"    Seed: {widgets[0]}")
                    print(f"    Control after generate: {widgets[1]}")
                    print(f"    Steps: {widgets[2]}")
                    print(f"    CFG: {widgets[3]}")
                    print(f"    Sampler: {widgets[4]}")
                    print(f"    Scheduler: {widgets[5]}")
            
            if node_18:
                widgets = node_18.get("widgets_values", [])
                print(f"  LoRA 1 widgets: {widgets}")
                
            if node_19:
                widgets = node_19.get("widgets_values", [])
                print(f"  LoRA 2 widgets: {widgets}")
                
        else:
            # API format verification 
            if "10" in result_workflow:
                inputs = result_workflow["10"]["inputs"]
                print(f"  KSampler inputs: {inputs}")
        
        # Save result
        output_file = Path("test_injected_workflow.json")
        with open(output_file, 'w') as f:
            json.dump(result_workflow, f, indent=2)
        print(f"\nSaved result to {output_file}")
        
        return True

except ImportError as e:
    print(f"Import error: {e}")
    def test_parameter_injection():
        return False

if __name__ == "__main__":
    success = test_parameter_injection()
    print("\n" + "=" * 50)
    if success:
        print("Parameter injection test completed!")
    else:
        print("Parameter injection test failed!")