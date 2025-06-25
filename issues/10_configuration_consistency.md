# Issue #10: Configuration Consistency & UI Parameter Management

## Problem Summary
The application has multiple configuration consistency issues across different tabs, particularly with how ComfyUI workflow parameters are loaded, displayed, and synchronized with the UI.

## Core Issues

### 1. Configuration Panel Logic Fragmentation
**Problem**: Configuration panels are created separately for each tab, leading to inconsistent behavior
**Symptoms**:
- Different tabs handle parameter importing differently
- Some tabs don't properly expose all ticked parameters from ComfyUI JSON files
- UI parameter visibility is inconsistent across tabs (trapped inside container in tab 1, have unwanted responsive behvior on tab 2, etc)

**Requirements**:
- When importing ComfyUI JSON workflow configuration, ALL selected/ticked parameters should be exposed in the right panel UI
- Each tab should follow the same rules for parameter promotion
- Consider creating unified configuration management logic
- organize the parameters by importance rules could be added to the file-settings menu (e.g image generation priority tabs by order: Ksampler, Checkpoints, Lora, Rest)

### 2. Workflow Forwarding & Conversion
**Current State**: The existing implementation mostly works well but sometimes break
**Requirement**: 
- Maintain minimal conversion when forwarding ComfyUI workflows to avoid breaking them - we should have documentation about this trial and error, worth reading to avoid previous mistakes 
**Note**: The current implementation should be preserved as much as possible - avoid introducing new logic that could break workflow compatibility, too many moving parameters right now

### 3. UI Layout Issues
**Problem**: Configuration panel import page becomes too wide with long parameter lists
**Symptoms**:
- No line breaks for extensive parameter lists
- Window extends beyond reasonable width
- Poor user experience with horizontal dragging to close the window

**Problem**: Right panel configuration in the image generation tab is looking off (look here: "/temp/python_XI8K9bGmzh.png")
**Symptoms**:
- The menu is trapped inside a small container, like in this screenshot: 
- should createed in a consistent way accross the tabs, and respect the rules in the settings we added
- Poor user experience with horizontal scrolling

**Problem**: Importing parameters should be smarter
**Symptoms**:
- There are certein parameters that ALWAYS go to specific nodes, like ClipEncode with positive word -> going to the positive prompt, Rerout nodes we already hiding, Load Image we dont need to show since we anyway forward an input for this - we need to hide them for better UX
- we can have visual difference between the type of nodes by colors to identify what is what easier

### 4. Workflow Dropdown Synchronization
**Problems**:
- Workflow dropdowns in left panel don't always show the latest loaded configuration
- Changing dropdown selection doesn't consistently trigger full parameter reload

**Requirements**:
1. Dropdown should display by default the latest workflow important, in a working state
2. When dropdown selection changes, it should trigger a complete reload of all parameters (as if loaded from config menu)

### 5. Prompt Memory Management
**Current Behavior**: Inconsistent prompt handling when switching workflows
**Required Behavior**:
1. When loading a workflow JSON, import positive and negative prompts from the file
2. If user modifies prompts, remember the user's changes (user changes take precedence)
3. Only update prompts from file when the SAME workflow is explicitly reloaded

### 6. Magic Prompt Configuration menu
**Current Behavior**: Magic Prompt Configuration menu is lost from the file menu and logic need to be improved
**Required Behavior**:
1. Initially we set up a prompt memory feature, to trigger new prompts by the star icon in the writing area
2. this have existing good logic which store prompt in positive or negative lists, and allow loading them to the prompt area - this works
3. The menu is working fine, UI is improved, and we able to load it from the top file menu 



**Memory Hierarchy**:
- User modifications (highest priority)
- File-based prompts (default/fallback)

## Technical Details

### Affected Components
- Configuration panel UI generation
- Workflow loading mechanism
- Parameter extraction from ComfyUI JSON
- Dropdown synchronization logic
- Prompt management system

### Current Implementation Notes
- Each tab appears to have its own configuration handling
- Parameter promotion logic varies by tab
- Workflow forwarding is mostly functional but fragile

## Reproduction Steps
1. Load a ComfyUI workflow JSON with multiple parameters
2. Check which parameters appear in the UI (should be different for each tab)
3. Switch workflows via dropdown and observe parameter updates
4. Modify prompts and switch workflows to test memory behavior
5. Load workflow with many parameters to observe UI width issues

## Proposed Solution Approach
1. Audit current parameter extraction logic across all tabs
2. Create unified configuration manager component
3. Implement consistent parameter promotion rules
4. Add proper line wrapping for long parameter lists
5. Fix dropdown synchronization to always reflect current state
6. Implement prompt memory hierarchy system

## Priority
HIGH - These issues affect core functionality and user experience across the entire application
HIGH - The UI stay dynamic in size for the height of the overal panel container is a persistent problem we unable to solve - parameters should show from start to buttom in a scrollable list (works fine for most cases but for small amount of value, the ui strech in a weird way)

## Related Files
- `/src/core/app_redesigned.py` - Main application with tab implementations
- `/src/core/workflow_manager.py` - Workflow loading and conversion
- `/src/ui/widgets.py` - UI components including configuration panels
- `/config/*.json` - Configuration files that need proper loading

## Testing Checklist
- [ ] All tabs show the right parameters for the tab imported workflow workflow
- [ ] Dropdown always shows current workflow loaded correctly
- [ ] Dropdown changes trigger full reload
- [ ] Long parameter lists wrap properly in the UI
- [ ] User prompt changes persist appropriately
- [ ] Workflow forwarding remains stable
- [ ] The UI in all right and left panels has no responsive behvior of fitting the size to the height of the panel container