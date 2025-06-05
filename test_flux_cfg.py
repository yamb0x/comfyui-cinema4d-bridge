#!/usr/bin/env python3
"""
Test CFG values specifically for FLUX models
"""

import json
import subprocess
import time
from pathlib import Path

def test_flux_cfg():
    """Test FLUX-appropriate CFG values"""
    
    print("🧪 FLUX CFG Test")
    print("=" * 50)
    
    # Load the API workflow
    workflow_path = Path("workflows/generate_images_api.json")
    with open(workflow_path, 'r') as f:
        base_workflow = json.load(f)
    
    # FLUX-appropriate CFG values
    test_configs = [
        {"cfg": 0.7, "name": "low", "desc": "Very creative, less prompt adherence"},
        {"cfg": 3.5, "name": "high", "desc": "Strict prompt adherence, may reduce quality"}
    ]
    
    images_dir = Path("images")
    existing_images = list(images_dir.glob("*.png"))
    print(f"Found {len(existing_images)} existing images")
    
    for i, config in enumerate(test_configs):
        print(f"\n🎯 Test {i+1}: CFG = {config['cfg']} ({config['desc']})")
        
        # Create workflow with specific CFG
        workflow = base_workflow.copy()
        workflow["10"]["inputs"]["cfg"] = config["cfg"]
        workflow["10"]["inputs"]["seed"] = 456 + i  # Different seeds for comparison
        workflow["10"]["inputs"]["steps"] = 12      # Reasonable for FLUX
        workflow["12"]["inputs"]["text"] = "a cute robot in a garden, detailed, high quality"
        workflow["13"]["inputs"]["text"] = "ugly, blurry, distorted, low quality, monochrome"
        
        # Create prompt
        prompt_data = {
            "prompt": workflow,
            "client_id": f"flux_cfg_test_{config['name']}"
        }
        
        prompt_file = Path(f"flux_cfg_{config['name']}.json")
        with open(prompt_file, 'w') as f:
            json.dump(prompt_data, f, indent=2)
        
        print(f"   📝 Workflow created: {prompt_file}")
        print(f"   🎛️  CFG: {config['cfg']}, Seed: {456 + i}, Steps: 12")
        
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
        
        # Wait between tests
        if i < len(test_configs) - 1:
            print("   ⏳ Waiting 5 seconds before next test...")
            time.sleep(5)
    
    print(f"\n" + "=" * 50)
    print("🎯 FLUX CFG Test Queued!")
    print(f"🔍 Compare the outputs in {images_dir}:")
    print("   - Low CFG (0.7) should be more creative/diverse")
    print("   - High CFG (3.5) should follow prompt more strictly")
    print("   - Both should be visibly different!")
    print("\n📊 Expected behavior with FLUX:")
    print("   - CFG 0.7: More artistic freedom, varied interpretations")
    print("   - CFG 3.5: Stricter prompt adherence, potentially sharper details")
    
    # Cleanup
    for config in test_configs:
        prompt_file = Path(f"flux_cfg_{config['name']}.json")
        prompt_file.unlink(missing_ok=True)

if __name__ == "__main__":
    test_flux_cfg()