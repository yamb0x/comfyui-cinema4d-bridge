#!/usr/bin/env python3
"""
Test different samplers to verify they're working
"""

import json
import subprocess
import time
from pathlib import Path

def test_sampler_differences():
    """Test different samplers that should show clear differences"""
    
    print("🧪 Sampler Difference Test")
    print("=" * 60)
    
    # Load the API workflow
    workflow_path = Path("workflows/generate_images_api.json")
    with open(workflow_path, 'r') as f:
        base_workflow = json.load(f)
    
    # Test samplers that should produce very different results
    test_configs = [
        {
            "sampler": "euler",
            "scheduler": "simple", 
            "name": "euler_simple",
            "desc": "Standard Euler sampler"
        },
        {
            "sampler": "dpmpp_2m",
            "scheduler": "karras",
            "name": "dpmpp_karras", 
            "desc": "DPM++ 2M with Karras noise schedule"
        },
        {
            "sampler": "ddim",
            "scheduler": "ddim_uniform",
            "name": "ddim_uniform",
            "desc": "DDIM deterministic sampler"
        }
    ]
    
    images_dir = Path("images")
    existing_images = list(images_dir.glob("*.png"))
    print(f"Found {len(existing_images)} existing images")
    
    base_seed = 789  # Fixed seed for comparison
    
    for i, config in enumerate(test_configs):
        print(f"\n🎯 Test {i+1}: {config['sampler']} + {config['scheduler']}")
        print(f"   📝 {config['desc']}")
        
        # Create workflow with specific sampler/scheduler
        workflow = base_workflow.copy()
        
        # Fixed parameters for fair comparison
        workflow["10"]["inputs"]["seed"] = base_seed
        workflow["10"]["inputs"]["steps"] = 20
        workflow["10"]["inputs"]["cfg"] = 1.5
        workflow["10"]["inputs"]["sampler_name"] = config["sampler"]
        workflow["10"]["inputs"]["scheduler"] = config["scheduler"]
        
        # Same prompt for comparison
        workflow["12"]["inputs"]["text"] = "a majestic mountain landscape at sunset, detailed, photorealistic"
        workflow["13"]["inputs"]["text"] = "ugly, blurry, low quality, distorted"
        
        # Create prompt
        prompt_data = {
            "prompt": workflow,
            "client_id": f"sampler_test_{config['name']}"
        }
        
        prompt_file = Path(f"sampler_test_{config['name']}.json")
        with open(prompt_file, 'w') as f:
            json.dump(prompt_data, f, indent=2)
        
        print(f"   📝 Workflow: {prompt_file}")
        print(f"   🎛️  Sampler: {config['sampler']}, Scheduler: {config['scheduler']}")
        print(f"   🌱 Seed: {base_seed}, Steps: 20, CFG: 1.5")
        
        # Queue the prompt
        try:
            curl_cmd = [
                'curl', '-s', '-X', 'POST',
                'http://127.0.0.1:8188/prompt',
                '-H', 'Content-Type: application/json',
                '-d', f'@{prompt_file}'
            ]
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                prompt_id = response.get("prompt_id")
                if prompt_id:
                    print(f"   ✅ Queued with ID: {prompt_id}")
                else:
                    print(f"   ❌ Queue failed: {response}")
                    continue
            else:
                print(f"   ❌ Curl failed: {result.stderr}")
                continue
                
        except Exception as e:
            print(f"   ❌ Queue error: {e}")
            continue
        
        # Wait between tests to avoid overwhelming ComfyUI
        if i < len(test_configs) - 1:
            print("   ⏳ Waiting 8 seconds before next test...")
            time.sleep(8)
    
    print(f"\n" + "=" * 60)
    print("🎯 Sampler Test Queued!")
    print(f"🔍 Compare the outputs in {images_dir}:")
    print("   - Same seed (789) and prompt for all tests")
    print("   - Different samplers should produce noticeably different results")
    print("   - DDIM should be most different (deterministic)")
    print("   - DPM++ often produces sharper details than Euler")
    
    print(f"\n📊 Expected differences:")
    print("   - Euler: Smooth, balanced results")
    print("   - DPM++ 2M: Often sharper, more detailed")  
    print("   - DDIM: Deterministic, potentially different style")
    print("\n⚠️  If all images look identical, samplers aren't being applied!")
    
    # Cleanup temp files
    for config in test_configs:
        prompt_file = Path(f"sampler_test_{config['name']}.json")
        prompt_file.unlink(missing_ok=True)

if __name__ == "__main__":
    test_sampler_differences()