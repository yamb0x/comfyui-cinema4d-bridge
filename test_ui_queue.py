#!/usr/bin/env python3
"""
Test queuing from the UI workflow manager
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.workflow_manager import WorkflowManager
    from utils.logger import setup_logging
    
    def test_ui_workflow():
        """Test the UI workflow loading and parameter injection"""
        # Setup logging
        setup_logging()
        
        # Create workflow manager
        workflows_dir = Path("workflows")
        manager = WorkflowManager(workflows_dir)
        
        # Load API workflow
        workflow = manager.load_workflow("generate_images_api.json")
        if not workflow:
            print("❌ Failed to load API workflow")
            return False
        
        print(f"✅ Loaded API workflow with {len(workflow)} nodes")
        
        # Test parameters (similar to what UI would send)
        params = {
            "positive_prompt": "a simple test image",
            "negative_prompt": "ugly, blurry",
            "width": 512,
            "height": 512,
            "steps": 8,
            "cfg": 1.0,
            "batch_size": 1,
            "seed": 42,
            "checkpoint": "flux1-dev-fp8.safetensors",  # Valid checkpoint
            "sampler_name": "euler",
            "scheduler": "simple"
        }
        
        # Inject parameters
        workflow_with_params = manager.inject_parameters_comfyui(workflow, params)
        print("✅ Parameters injected")
        
        # Save the result for inspection
        output_file = Path("test_ui_workflow.json")
        with open(output_file, 'w') as f:
            json.dump(workflow_with_params, f, indent=2)
        print(f"✅ Saved workflow to {output_file}")
        
        # Check for any obvious issues
        if "5" in workflow_with_params:
            checkpoint = workflow_with_params["5"]["inputs"].get("ckpt_name")
            print(f"Checkpoint: {checkpoint}")
        
        if "12" in workflow_with_params:
            prompt = workflow_with_params["12"]["inputs"].get("text")
            print(f"Positive prompt: {prompt}")
        
        return True

except ImportError as e:
    print(f"Import error: {e}")
    
    def test_ui_workflow():
        return False

if __name__ == "__main__":
    success = test_ui_workflow()
    if success:
        print("\n🎉 UI workflow test completed!")
    else:
        print("\n💥 UI workflow test failed!")