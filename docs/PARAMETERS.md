# UI Parameters System

> [!WARNING]
> This system is partially implemented. Many features described here don't work as intended.

## Overview

The UI parameter system dynamically generates interface elements based on ComfyUI workflow nodes.

## How It Works (When It Works)

1. **Workflow Parsing**
   - Reads JSON workflow files
   - Extracts node parameters
   - Maps to UI widgets

2. **Dynamic UI Generation**
   - Creates input fields for each parameter
   - Supports text, numbers, dropdowns, sliders
   - Attempts to maintain state

## Current Issues

### What Works ✅
- Basic parameter extraction
- Simple text/number inputs
- Some state persistence

### What's Broken ❌
- Complex widget types
- Many parameter mappings
- Reliable state sync
- Error handling

## Parameter Types

### Text Parameters
```json
{
  "widget_type": "text",
  "default": "a beautiful landscape",
  "multiline": true
}
```

### Number Parameters
```json
{
  "widget_type": "number",
  "default": 20,
  "min": 1,
  "max": 100,
  "step": 1
}
```

### Dropdown Parameters
```json
{
  "widget_type": "combo",
  "options": ["option1", "option2", "option3"],
  "default": 0
}
```

## Configuration Files

- `3d_parameters_config.json` - 3D workflow parameters
- `image_parameters_config.json` - Image workflow parameters
- `texture_parameters_config.json` - Texture workflow parameters
- `unified_parameters_state.json` - Cross-tab persistence

## Known Problems

1. **State Loss** - Parameters reset unexpectedly
2. **Widget Errors** - Complex widgets show as "unsupported"
3. **Sync Issues** - UI doesn't always reflect actual values
4. **Save Failures** - State sometimes doesn't persist

## Debugging with Claude Code

Ask Claude Code:
- "Why are my parameters resetting?"
- "Help debug the parameter extraction"
- "Fix the widget generation for this node type"

## Development Notes

The parameter system needs major refactoring. Current implementation has:
- Incomplete error handling
- Fragile state management
- Limited widget support
- Poor separation of concerns

Focus on fixing core functionality before adding new parameter types.