#!/usr/bin/env python3
"""
Verify that sampler parameters are being injected correctly
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
        
        print("🔍 Parameter Injection Verification")
        print("=" * 50)
        
        # Create workflow manager
        workflows_dir = Path("workflows")
        manager = WorkflowManager(workflows_dir)
        
        # Load the API workflow
        workflow = manager.load_workflow("generate_images_api.json")
        if not workflow:
            print("❌ Failed to load API workflow")
            return False
        
        print(f"✅ Loaded workflow with {len(workflow)} nodes")
        
        # Check original values
        original_sampler = workflow["10"]["inputs"]["sampler_name"]
        original_scheduler = workflow["10"]["inputs"]["scheduler"]
        original_cfg = workflow["10"]["inputs"]["cfg"]
        original_steps = workflow["10"]["inputs"]["steps"]
        
        print(f"📋 Original values:")
        print(f"   Sampler: {original_sampler}")
        print(f"   Scheduler: {original_scheduler}")
        print(f"   CFG: {original_cfg}")
        print(f"   Steps: {original_steps}")
        
        # Test parameters that should override defaults
        test_params = {
            "sampler_name": "dpmpp_2m",        # Different from "euler"
            "scheduler": "karras",             # Different from "simple"
            "cfg": 2.5,                       # Different from 1.0
            "steps": 15,                      # Different from 20
            "positive_prompt": "test prompt",
            "negative_prompt": "test negative",
            "seed": 999
        }
        
        print(f"\n🧪 Injecting test parameters:")
        for key, value in test_params.items():
            print(f"   {key}: {value}")
        
        # Inject parameters
        result_workflow = manager.inject_parameters_comfyui(workflow, test_params)
        
        # Check if parameters were applied
        print(f"\n✅ After injection:")
        injected_sampler = result_workflow["10"]["inputs"]["sampler_name"]
        injected_scheduler = result_workflow["10"]["inputs"]["scheduler"]
        injected_cfg = result_workflow["10"]["inputs"]["cfg"]
        injected_steps = result_workflow["10"]["inputs"]["steps"]
        
        print(f"   Sampler: {injected_sampler}")
        print(f"   Scheduler: {injected_scheduler}")
        print(f"   CFG: {injected_cfg}")
        print(f"   Steps: {injected_steps}")
        
        # Verify changes
        success = True
        if injected_sampler != test_params["sampler_name"]:
            print(f"❌ Sampler injection FAILED: expected {test_params['sampler_name']}, got {injected_sampler}")
            success = False
        else:
            print(f"✅ Sampler injection SUCCESS")
            
        if injected_scheduler != test_params["scheduler"]:
            print(f"❌ Scheduler injection FAILED: expected {test_params['scheduler']}, got {injected_scheduler}")
            success = False
        else:
            print(f"✅ Scheduler injection SUCCESS")
            
        if injected_cfg != test_params["cfg"]:
            print(f"❌ CFG injection FAILED: expected {test_params['cfg']}, got {injected_cfg}")
            success = False
        else:
            print(f"✅ CFG injection SUCCESS")
            
        if injected_steps != test_params["steps"]:
            print(f"❌ Steps injection FAILED: expected {test_params['steps']}, got {injected_steps}")
            success = False
        else:
            print(f"✅ Steps injection SUCCESS")
        
        # Save the result for inspection
        output_file = Path("test_injected_workflow.json")
        with open(output_file, 'w') as f:
            json.dump(result_workflow, f, indent=2)
        print(f"\n📁 Saved result to {output_file}")
        
        return success

except ImportError as e:
    print(f"Import error: {e}")
    def test_parameter_injection():
        return False

if __name__ == "__main__":
    success = test_parameter_injection()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Parameter injection is working correctly!")
    else:
        print("💥 Parameter injection has issues!")