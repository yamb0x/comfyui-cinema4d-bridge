# ComfyUI Data Conversion & Workflow Submission Issues

## Priority: HIGH

## Status: ACTIVE

## Overview
Problems with parameter data formatting, conversion, and submission to ComfyUI workflows causing execution failures.

## Core Issues
- **Parameter Data Formatting** - UI parameter values not properly converted for ComfyUI workflow format
- **Workflow Submission** - Data structure mismatches between UI and ComfyUI API expectations
- **Type Conversion** - String/numeric/boolean parameter types not handled correctly
- **Node Mapping** - Workflow node parameter mapping inconsistencies

## Impact
- Workflow generation fails despite UI showing correct parameters
- ComfyUI receives malformed data causing execution errors
- User parameter changes not properly reflected in generated outputs

## Technical Areas
- `/src/core/workflow_manager.py` - Node conversion logic
- `/src/mcp/comfyui_client.py` - API data formatting
- `/src/core/app_ui_methods.py` - Parameter collection and conversion
- Parameter → workflow JSON transformation pipeline

## Next Steps
1. Trace parameter flow from UI to ComfyUI
2. Identify data format mismatches
3. Fix conversion pipeline
4. Test workflow submission end-to-end

---
*Issue created: 2025-06-25*
*Previous issue (workflow parameter loading) completed successfully*