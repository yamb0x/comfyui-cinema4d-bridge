#!/usr/bin/env python3
"""
Manual test script that uses the workflow manager to test ComfyUI
"""

import json
import subprocess
import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.workflow_manager import WorkflowManager
    from utils.logger import setup_logging
    
    def load_and_inject_workflow():
        """Load workflow and inject parameters using WorkflowManager"""
        # Setup basic logging
        setup_logging()
        
        # Create workflow manager
        workflows_dir = Path("workflows")
        manager = WorkflowManager(workflows_dir)
        
        # Load workflow
        workflow = manager.load_workflow("generate_images.json")
        if not workflow:
            print("❌ Failed to load workflow")
            return None
        
        # Test parameters
        params = {
            "positive_prompt": "a simple red cube on white background",
            "negative_prompt": "ugly, blurry", 
            "width": 512,
            "height": 512,
            "steps": 10,
            "cfg": 1.0,
            "batch_size": 1,
            "seed": 42
        }
        
        # Inject parameters
        api_workflow = manager.inject_parameters_comfyui(workflow, params)
        print(f"✅ Converted and injected parameters")
        
        return api_workflow

except ImportError as e:
    print(f"Import error: {e}")
    print("Falling back to simple parameter injection...")
    
    def load_and_inject_workflow():
        """Fallback: simple workflow loading without conversion"""
        workflow_path = Path("workflows/generate_images.json")
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # Simple parameter injection for testing
        print("✅ Loaded workflow (no parameter injection)")
        return workflow

def test_comfyui():
    """Test ComfyUI generation"""
    print("🧪 Manual ComfyUI Test")
    print("=" * 50)
    
    # Check ComfyUI is running
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
    
    # Load workflow and inject parameters
    print("2. Loading workflow and injecting parameters...")
    try:
        workflow = load_and_inject_workflow()
        if not workflow:
            return False
        print(f"✅ Processed workflow")
    except Exception as e:
        print(f"❌ Failed to process workflow: {e}")
        return False
    
    # Save workflow to temp file for debugging
    temp_workflow = Path("temp_workflow.json")
    with open(temp_workflow, 'w') as f:
        json.dump(workflow, f, indent=2)
    print(f"✅ Saved processed workflow to {temp_workflow}")
    
    # Create prompt payload
    prompt_data = {
        "prompt": workflow,
        "client_id": "test_client"
    }
    
    # Save prompt for curl
    prompt_file = Path("temp_prompt.json")
    with open(prompt_file, 'w') as f:
        json.dump(prompt_data, f)
    
    # Count existing images
    images_dir = Path("images")
    existing_images = list(images_dir.glob("*.png"))
    print(f"3. Found {len(existing_images)} existing images")
    
    # Queue prompt using curl
    print("4. Queuing prompt...")
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
                print(f"✅ Prompt queued with ID: {prompt_id}")
            else:
                print(f"❌ Failed to queue: {response}")
                return False
        else:
            print(f"❌ Curl failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to queue prompt: {e}")
        return False
    
    # Wait for completion
    print("5. Waiting for generation...")
    for i in range(30):  # 30 second timeout
        time.sleep(1)
        
        # Check for new images
        current_images = list(images_dir.glob("*.png"))
        if len(current_images) > len(existing_images):
            new_images = [img for img in current_images if img not in existing_images]
            print(f"✅ Generation complete! New images: {[img.name for img in new_images]}")
            
            # Cleanup temp files
            temp_workflow.unlink(missing_ok=True)
            prompt_file.unlink(missing_ok=True)
            return True
        
        if i % 5 == 0:
            print(f"   Waiting... ({i}s)")
    
    print("❌ Timeout waiting for generation")
    return False

if __name__ == "__main__":
    success = test_comfyui()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Manual test PASSED!")
    else:
        print("💥 Manual test FAILED!")