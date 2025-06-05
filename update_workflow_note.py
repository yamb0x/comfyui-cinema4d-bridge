#!/usr/bin/env python3
"""
Update the workflow documentation note with LoRA information
"""

import json
from pathlib import Path

def update_workflow_note():
    """Update the Note node with complete parameter documentation"""
    
    workflow_path = Path("workflows/generate_images_api.json")
    
    # Load the workflow
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    # Find the Note node (should be node ID 1)
    note_node = None
    for node in workflow.get("nodes", []):
        if node.get("type") == "Note" and node.get("id") == 1:
            note_node = node
            break
    
    if not note_node:
        print("❌ Note node not found")
        return False
    
    # Updated documentation text
    updated_text = """🎛️ ComfyUI to Cinema4D Bridge - Updated Workflow

📋 PARAMETERS CONTROLLED BY APPLICATION:

Node 12 (Positive Prompt):
  • text: Injected from UI 'Scene Description' field

Node 13 (Negative Prompt):
  • text: Injected from UI 'Negative Prompt' field

Node 8 (Dimensions & Batch):
  • width: UI Width spinner (default 512)
  • height: UI Height spinner (default 512)
  • batch_size: UI Batch Size spinner (1-12)

Node 10 (KSampler):
  • seed: UI Seed (-1 = random, or specific value)
  • control_after_generate: UI "After Generate" dropdown
    - increment (default), decrement, randomize, fixed
  • steps: UI Steps spinner (default 20)
  • cfg: UI CFG Scale (0.5-10.0, default 1.0 for FLUX)
  • sampler_name: UI Sampler dropdown (euler, dpmpp_2m, etc.)
  • scheduler: UI Scheduler dropdown (simple, karras, etc.)

Node 5 (Checkpoint) - CONDITIONAL:
  • ckpt_name: Only if valid model selected in UI
  • Default: flux1-dev-fp8.safetensors

Node 18 (LoRA 1) - CONNECTED ✅:
  • lora_name: UI LoRA 1 dropdown
  • strength_model & strength_clip: UI LoRA 1 Strength (0.0-2.0)
  • Active checkbox controls if LoRA is applied

Node 19 (LoRA 2) - CONNECTED ✅:
  • lora_name: UI LoRA 2 dropdown
  • strength_model & strength_clip: UI LoRA 2 Strength (0.0-2.0)
  • Active checkbox controls if LoRA is applied

Node 17 (Image Save):
  • output_path: Fixed to project/images directory
  • All other save settings are static

⚠️ EDITING NOTES:
• You can modify any static values in this file
• UI-controlled parameters will be overridden at runtime
• To change UI defaults, edit src/core/app.py
• For advanced workflow changes, modify node connections

🔄 WORKFLOW FLOW:
Checkpoint(5) → LoRA1(18) → LoRA2(19) → CLIP(12,13) → KSampler(10) → VAEDecode(11) → ImageSave(17)
                                     ↘ EmptyLatent(8) ↗

🎯 AVAILABLE LORAS:
• deep_sea_creatures_cts.safetensors
• aidmaFLUXpro1.1-FLUX-V0.1.safetensors
• Luminous_Shadowscape-000016.safetensors"""
    
    # Update the note text
    note_node["widgets_values"][0] = updated_text
    
    # Save the updated workflow
    with open(workflow_path, 'w') as f:
        json.dump(workflow, f, indent=2)
    
    print("✅ Updated workflow documentation note")
    return True

if __name__ == "__main__":
    update_workflow_note()