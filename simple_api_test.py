#!/usr/bin/env python3
"""
Simple API format test for ComfyUI
"""

import json
import subprocess
import time
from pathlib import Path

def create_simple_api_workflow():
    """Create a simple workflow in API format"""
    # Minimal FLUX workflow in API format
    workflow = {
        "5": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "flux1-dev-fp8.safetensors"
            }
        },
        "8": {
            "class_type": "EmptySD3LatentImage", 
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            }
        },
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 42,
                "steps": 8,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["5", 0],
                "positive": ["12", 0], 
                "negative": ["13", 0],
                "latent_image": ["8", 0]
            }
        },
        "11": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["10", 0],
                "vae": ["5", 2]
            }
        },
        "12": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "a simple red cube on white background",
                "clip": ["5", 1]
            }
        },
        "13": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": "ugly, blurry",
                "clip": ["5", 1]
            }
        },
        "17": {
            "class_type": "PreviewImage",
            "inputs": {
                "images": ["11", 0]
            }
        }
    }
    return workflow

def test_simple_api():
    """Test with simple API format"""
    print("🧪 Simple API Format Test")
    print("=" * 50)
    
    # Check ComfyUI
    print("1. Testing ComfyUI connection...")
    try:
        result = subprocess.run(['curl', '-s', 'http://127.0.0.1:8188/system_stats'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ ComfyUI is running")
        else:
            print("❌ ComfyUI not responding")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    # Create workflow
    print("2. Creating simple API workflow...")
    workflow = create_simple_api_workflow()
    print(f"✅ Created workflow with {len(workflow)} nodes")
    
    # Save for debugging
    temp_workflow = Path("simple_workflow.json")
    with open(temp_workflow, 'w') as f:
        json.dump(workflow, f, indent=2)
    print(f"✅ Saved workflow to {temp_workflow}")
    
    # Create prompt
    prompt_data = {
        "prompt": workflow,
        "client_id": "simple_test"
    }
    
    prompt_file = Path("simple_prompt.json")
    with open(prompt_file, 'w') as f:
        json.dump(prompt_data, f)
    
    # Count existing images
    images_dir = Path("images")
    existing_images = list(images_dir.glob("*.png"))
    print(f"3. Found {len(existing_images)} existing images")
    
    # Queue prompt
    print("4. Queuing simple prompt...")
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
                print(f"✅ Simple prompt queued with ID: {prompt_id}")
            else:
                print(f"❌ Failed to queue simple prompt: {response}")
                return False
        else:
            print(f"❌ Curl failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to queue simple prompt: {e}")
        return False
    
    # Wait for completion
    print("5. Waiting for generation...")
    for i in range(45):  # 45 second timeout for FLUX
        time.sleep(1)
        
        # Check for new images
        current_images = list(images_dir.glob("*.png"))
        if len(current_images) > len(existing_images):
            new_images = [img for img in current_images if img not in existing_images]
            print(f"✅ Generation complete! New images: {[img.name for img in new_images]}")
            
            # Cleanup
            temp_workflow.unlink(missing_ok=True)
            prompt_file.unlink(missing_ok=True)
            return True
        
        if i % 5 == 0:
            print(f"   Waiting... ({i}s)")
    
    print("❌ Timeout waiting for generation")
    return False

if __name__ == "__main__":
    success = test_simple_api()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Simple API test PASSED!")
    else:
        print("💥 Simple API test FAILED!")