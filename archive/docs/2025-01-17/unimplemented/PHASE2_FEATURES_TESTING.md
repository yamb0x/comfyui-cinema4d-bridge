# Phase 2 Features - Testing Guide

## New Features Implemented (2025-01-09)

### 1. ⚙️ **Settings Button - Save Default Parameters**
- **Purpose**: Configure and save default settings for each object type
- **How it works**:
  - Click the ⚙️ button next to any primitive
  - Configure size and position values
  - Click OK to save defaults
  - These defaults are used when creating new objects
  - Settings persist between sessions

### 2. ✗ **Remove Button - Blacklist Commands**
- **Purpose**: Remove buggy or unwanted commands from UI
- **How it works**:
  - Click the ✗ button to remove a command
  - Command is added to blacklist file
  - Button disappears from UI immediately
  - Blacklisted commands won't appear on restart
  - To restore: manually edit `config/command_blacklist.json`

### 3. 💾 **Persistent Configuration Files**
- **Location**: `config/` directory
- **Files created**:
  - `primitive_defaults.json` - Saved default settings
  - `command_blacklist.json` - Removed commands
  - `nl_triggers.json` - Natural language triggers
  - `nl_patterns.json` - NL pattern recognition data

---

## Testing Checklist - Primitives

### Basic Functionality Tests
- [ ] **Cube** - Create with default settings
- [ ] **Sphere** - Create with default settings  
- [ ] **Cylinder** - Create with default settings
- [ ] **Cone** - Create with default settings
- [ ] **Torus** - Create with default settings
- [ ] **Disc** - Create with default settings
- [ ] **Tube** - Create with default settings
- [ ] **Pyramid** - Create with default settings
- [ ] **Plane** - Create with default settings
- [ ] **Figure** - Create with default settings
- [ ] **Landscape** - Create with default settings
- [ ] **Platonic** - Create with default settings
- [ ] **Oil Tank** - Create with default settings
- [ ] **Relief** - Create with default settings
- [ ] **Capsule** - Create with default settings
- [ ] **Single Polygon** - Create with default settings
- [ ] **Fractal** - Create with default settings
- [ ] **Formula** - Create with default settings

### Settings Dialog Tests
- [ ] Open settings for Cube - verify controls match object type
- [ ] Save custom size (200x300x400) and position (100, 50, -50)
- [ ] Create new Cube - verify it uses saved settings
- [ ] Test different primitives have appropriate controls:
  - [ ] Sphere shows Radius only
  - [ ] Cylinder shows Radius + Height
  - [ ] Torus shows Major + Minor radius
  - [ ] Cube/Plane show Width/Height/Depth

### Blacklist Tests
- [ ] Click ✗ on a primitive button
- [ ] Verify button disappears immediately
- [ ] Check `config/command_blacklist.json` contains the object
- [ ] Restart app - verify blacklisted button doesn't appear
- [ ] Remove entry from JSON - verify button returns on restart

### Performance Tests
- [ ] Type rapidly in NL trigger fields - no lag
- [ ] Open/close settings dialogs multiple times - no crashes
- [ ] Create 20+ objects in succession - stable performance

---

## Known Issues & Workarounds

### Issue 1: Settings not applying to some primitives
**Workaround**: The MCP wrapper may need primitive-specific parameter handling

### Issue 2: Blacklisted items can only be restored via JSON
**Planned**: Add "Show Hidden Commands" option in settings

### Issue 3: NL triggers save after 1 second delay
**By Design**: Performance optimization to reduce disk I/O

---

## Next Steps

1. **Extend to Generators** - Add settings dialogs for all 22 generators
2. **Extend to Deformers** - Add strength/axis controls
3. **Batch Operations** - Apply settings to multiple objects
4. **Import/Export Settings** - Share configurations between users
5. **Stage 2 Implementation** - Hierarchy operations with saved defaults