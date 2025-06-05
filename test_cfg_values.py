#!/usr/bin/env python3
"""
Test CFG values in the workflow
"""

import json
import subprocess
from pathlib import Path

def test_cfg_extremes():
    """Test with extreme CFG values to see clear differences"""
    
    # Load the API workflow
    workflow_path = Path("workflows/generate_images_api.json")
    with open(workflow_path, 'r') as f:
        base_workflow = json.load(f)
    
    # Test two extreme CFG values
    test_configs = [
        {"cfg": 0.5, "name": "very_low_cfg"},
        {"cfg": 15.0, "name": "very_high_cfg"}
    ]
    
    for config in test_configs:
        print(f"\n🧪 Testing CFG = {config['cfg']}")
        
        # Create workflow with specific CFG
        workflow = base_workflow.copy()
        workflow["10"]["inputs"]["cfg"] = config["cfg"]
        workflow["10"]["inputs"]["seed"] = 123  # Fixed seed for comparison
        workflow["10"]["inputs"]["steps"] = 8   # Fast generation
        workflow["12"]["inputs"]["text"] = "a red sports car, professional photography"
        workflow["13"]["inputs"]["text"] = "ugly, blurry, distorted, low quality"
        
        # Create prompt
        prompt_data = {
            "prompt": workflow,
            "client_id": f"cfg_test_{config['name']}"
        }
        
        prompt_file = Path(f"test_cfg_{config['name']}.json")
        with open(prompt_file, 'w') as f:
            json.dump(prompt_data, f, indent=2)
        
        print(f"✅ Created test with CFG={config['cfg']}")
        print(f"   Workflow saved to: {prompt_file}")
        print(f"   Expected output: ComfyUI_cfg_{config['name']}_*.png")
        
        # Optional: Queue immediately
        # (commenting out to avoid flooding ComfyUI)
        # try:
        #     curl_cmd = [
        #         'curl', '-s', '-X', 'POST',
        #         'http://127.0.0.1:8188/prompt',
        #         '-H', 'Content-Type: application/json',
        #         '-d', f'@{prompt_file}'
        #     ]
        #     result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
        #     if result.returncode == 0:
        #         response = json.loads(result.stdout)
        #         prompt_id = response.get("prompt_id")
        #         print(f"   Queued with ID: {prompt_id}")
        # except Exception as e:
        #     print(f"   Queue failed: {e}")
    
    print("\n" + "="*50)
    print("CFG Test Workflows Created!")
    print("Compare the outputs to verify CFG is working:")
    print("- CFG 0.5 should be very creative/chaotic")
    print("- CFG 15.0 should be very strict to prompt")
    print("Both should be noticeably different!")

if __name__ == "__main__":
    test_cfg_extremes()