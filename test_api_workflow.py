#!/usr/bin/env python3
"""
Test the API format workflow file
"""

import json
import subprocess
import time
from pathlib import Path

def test_api_workflow():
    """Test the generate_images_api.json workflow"""
    print("🧪 Testing API Workflow File")
    print("=" * 50)
    
    # Load the API workflow
    workflow_path = Path("workflows/generate_images_api.json")
    if not workflow_path.exists():
        print("❌ API workflow file not found")
        return False
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    print(f"✅ Loaded API workflow with {len(workflow)} nodes")
    
    # Create prompt
    prompt_data = {
        "prompt": workflow,
        "client_id": "api_test"
    }
    
    prompt_file = Path("api_test_prompt.json")
    with open(prompt_file, 'w') as f:
        json.dump(prompt_data, f)
    
    # Count existing images
    images_dir = Path("images")
    existing_images = list(images_dir.glob("*.png"))
    print(f"Found {len(existing_images)} existing images")
    
    # Queue prompt
    print("Queuing API workflow...")
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
                print(f"✅ API workflow queued with ID: {prompt_id}")
            else:
                print(f"❌ Failed to queue API workflow: {response}")
                prompt_file.unlink(missing_ok=True)
                return False
        else:
            print(f"❌ Curl failed: {result.stderr}")
            prompt_file.unlink(missing_ok=True)
            return False
    except Exception as e:
        print(f"❌ Failed to queue: {e}")
        prompt_file.unlink(missing_ok=True)
        return False
    
    # Wait for completion with better monitoring
    print("Waiting for generation (checking queue status)...")
    for i in range(60):  # 60 second timeout
        time.sleep(1)
        
        # Check queue status
        if i % 5 == 0:
            try:
                queue_result = subprocess.run(['curl', '-s', 'http://127.0.0.1:8188/queue'], 
                                            capture_output=True, text=True, timeout=5)
                if queue_result.returncode == 0:
                    queue_data = json.loads(queue_result.stdout)
                    running = len(queue_data.get("queue_running", []))
                    pending = len(queue_data.get("queue_pending", []))
                    print(f"   Queue status: {running} running, {pending} pending ({i}s)")
                    
                    # If queue is empty, check for new images
                    if running == 0 and pending == 0:
                        current_images = list(images_dir.glob("*.png"))
                        if len(current_images) > len(existing_images):
                            new_images = [img for img in current_images if img not in existing_images]
                            print(f"✅ Generation complete! New images: {[img.name for img in new_images]}")
                            prompt_file.unlink(missing_ok=True)
                            return True
                        elif i > 10:  # Give it some time before declaring failure
                            print("❌ Queue empty but no new images found")
                            break
            except Exception as e:
                print(f"   Queue check failed: {e}")
        
        # Direct image check
        current_images = list(images_dir.glob("*.png"))
        if len(current_images) > len(existing_images):
            new_images = [img for img in current_images if img not in existing_images]
            print(f"✅ Generation complete! New images: {[img.name for img in new_images]}")
            prompt_file.unlink(missing_ok=True)
            return True
    
    print("❌ Timeout waiting for generation")
    prompt_file.unlink(missing_ok=True)
    return False

if __name__ == "__main__":
    success = test_api_workflow()
    print("\n" + "=" * 50)
    if success:
        print("🎉 API workflow test PASSED!")
    else:
        print("💥 API workflow test FAILED!")