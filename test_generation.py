#!/usr/bin/env python3
"""
Test script for image generation pipeline
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config_adapter import AppConfig
from core.workflow_manager import WorkflowManager
from mcp.comfyui_client import ComfyUIClient
from utils.logger import setup_logging

async def test_generation():
    """Test the complete image generation pipeline"""
    # Setup logging
    setup_logging()
    print("Starting ComfyUI generation test...")
    
    # Load configuration
    config = AppConfig.load()
    print(f"Loaded config - ComfyUI URL: {config.mcp.comfyui_server_url}")
    
    # Create workflow manager
    workflow_manager = WorkflowManager(config.workflows_dir)
    
    # Create ComfyUI client
    comfyui_client = ComfyUIClient(
        config.mcp.comfyui_server_url,
        config.mcp.comfyui_websocket_url
    )
    
    # Test connection
    print("Testing ComfyUI connection...")
    connected = await comfyui_client.connect()
    if not connected:
        print("❌ Failed to connect to ComfyUI")
        return False
    print("✅ Connected to ComfyUI")
    
    # Load workflow
    print("Loading workflow...")
    workflow = workflow_manager.load_workflow("generate_images.json")
    if not workflow:
        print("❌ Failed to load workflow")
        return False
    print("✅ Workflow loaded")
    
    # Test parameters
    params = {
        "positive_prompt": "a simple red cube on white background",
        "negative_prompt": "ugly, blurry, distorted",
        "width": 512,
        "height": 512,
        "steps": 10,  # Quick test
        "cfg": 1.0,
        "batch_size": 1,
        "seed": 42,
        "lora1_active": False,
        "lora2_active": False
    }
    
    # Inject parameters
    print("Injecting parameters...")
    workflow_with_params = workflow_manager.inject_parameters_comfyui(workflow, params)
    print("✅ Parameters injected")
    
    # Clear images directory for test
    images_dir = config.images_dir
    print(f"Checking images directory: {images_dir}")
    existing_images = list(images_dir.glob("*.png"))
    print(f"Found {len(existing_images)} existing images")
    
    # Queue prompt
    print("Queuing prompt...")
    prompt_id = await comfyui_client.queue_prompt(workflow_with_params)
    if not prompt_id:
        print("❌ Failed to queue prompt")
        return False
    print(f"✅ Prompt queued with ID: {prompt_id}")
    
    # Wait for completion (simple polling)
    print("Waiting for generation to complete...")
    for i in range(60):  # 60 second timeout
        await asyncio.sleep(1)
        
        # Check for new images
        current_images = list(images_dir.glob("*.png"))
        if len(current_images) > len(existing_images):
            new_images = [img for img in current_images if img not in existing_images]
            print(f"✅ Generation complete! New images: {[img.name for img in new_images]}")
            return True
        
        if i % 5 == 0:
            print(f"Still waiting... ({i}s)")
    
    print("❌ Timeout waiting for generation")
    return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_generation())
        if success:
            print("\n🎉 Image generation test PASSED!")
        else:
            print("\n💥 Image generation test FAILED!")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)