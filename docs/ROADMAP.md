# Development Roadmap

> [!WARNING]
> **EXPERIMENTAL PROJECT** - This roadmap is aspirational. The project has fundamental issues that need fixing before these features can work.

Current priorities for completing the ComfyUI to Cinema4D bridge.

## Priority 1: Texture Generation

**Status**: Working with debug issues
**Timeline**: Current focus

### Tasks
- [ ] Fix Texture Generation Workflow debugging
- [ ] Test batch texture generation for multiple models
- [ ] Verify PBR material pipeline integration
- [ ] Test Three.js viewer with PBR material support

### Technical Notes
- Workflow execution issues need investigation
- Batch processing architecture needs validation
- Material application to 3D models requires testing

## Priority 2: Cinema4D Integration

**Status**: 40% complete (NOT 80% as previously claimed)
**Timeline**: Major work needed

### Current State
- [x] Model Context Protocol communication setup
- [x] NLP Dictionary configured (80% - needs retesting)
- [x] 3D model import to Cinema4D working

### Next Steps
- [ ] Test existing NLP Dictionary commands
- [ ] Validate all Cinema4D object creation capabilities
- [ ] **NEW PLAN**: Replace NLP system with Claude Code SDK
  - Integrate https://docs.anthropic.com/en/docs/claude-code/sdk
  - Leverage existing NLP dictionary with Claude AI intelligence
  - Enable complex scene creation using Python capabilities

### Technical Approach
- Maintain existing MCP infrastructure
- Add Claude Code SDK layer for enhanced intelligence
- Use NLP dictionary as command reference for Claude AI
- Enable natural language to complex Cinema4D scene generation

## Priority 3: Settings, Debug, Optimizations

**Status**: Needs attention for stability
**Timeline**: Ongoing alongside other priorities

### Tasks
- [ ] Consistent settings menu across all tabs
- [ ] Fix heavy debug logging and performance issues
- [ ] Optimize speed and memory usage
- [ ] Fix and improve "magic prompt configuration" menu
- [ ] Implement unified configuration management

### Technical Focus
- UI consistency across tab system
- Performance profiling and optimization
- Debug logging cleanup and structured logging
- Memory management improvements

## Priority 4: 3D Model Creation Enhancements

**Status**: Complete but needs additional features
**Timeline**: Lower priority

### Tasks
- [ ] Add support for different 3D view modes
- [ ] Enhanced untextured model display options
- [ ] Additional 3D model format support
- [ ] Improved Three.js viewer performance

## Long-term Vision

### Complete Bridge Architecture
1. **Unified Creative Pipeline**
   - Image → 3D Model → Texture → Cinema4D Scene
   - Seamless cross-application workflow
   - AI-assisted scene composition

2. **Intelligence Layer**
   - Claude Code SDK integration
   - Natural language scene description
   - Automated asset organization
   - Smart material assignment

3. **Professional Integration**
   - Cinema4D plugin distribution
   - Enterprise workflow support
   - Batch processing capabilities
   - Advanced material systems

## Technical Debt

### Current Issues
- Heavy debug logging impacting performance
- Inconsistent settings management
- Memory leaks in image/3D model loading
- UI thread blocking during heavy operations

### Planned Improvements
- Async operation improvements
- Smart caching strategies
- UI responsiveness optimizations
- Error handling and recovery

---

*Updated: 2025-06-26*
*Next Review: Weekly during active development*