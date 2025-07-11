# ComfyUI to Cinema4D Bridge - Documentation Index

## 📚 Documentation Structure Overview

### 🚀 Getting Started
1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Initial setup instructions
2. **[RUN_APPLICATION_GUIDE.md](setup/RUN_APPLICATION_GUIDE.md)** - How to run the application
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick command reference

### 🔧 Development
1. **[DEVELOPER_GUIDE.md](development/DEVELOPER_GUIDE.md)** - Core development guide
2. **[DEVELOPMENT_STANDARDS.md](development/DEVELOPMENT_STANDARDS.md)** - Coding standards and practices
3. **[TECHNICAL_REFERENCE.md](development/TECHNICAL_REFERENCE.md)** - Technical implementation details
4. **[API_REFERENCE.md](API_REFERENCE.md)** - API documentation

### 🎬 Cinema4D Integration
1. **[CINEMA4D_API_REFERENCE.md](development/CINEMA4D_API_REFERENCE.md)** - ⚠️ CRITICAL: Cinema4D constants and patterns
2. **[CINEMA4D_INTEGRATION_STATUS.md](development/CINEMA4D_INTEGRATION_STATUS.md)** - Current integration status
3. **[CINEMA4D_INTELLIGENCE_GUIDE.md](CINEMA4D_INTELLIGENCE_GUIDE.md)** - Intelligence training system

### 🔄 Phase & Progress Tracking
1. **[PHASE2_QUICK_REFERENCE.md](development/PHASE2_QUICK_REFERENCE.md)** - Phase 2 bug fixes and patterns
2. **[PHASE2_BUG_FIXES_REQUIRED.md](development/PHASE2_BUG_FIXES_REQUIRED.md)** - Outstanding bug fixes
3. **[NEXT_PHASE_PLAN.md](planning/NEXT_PHASE_PLAN.md)** - Future development plans

### 🧪 Testing & Quality
1. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing procedures
2. **[LESSONS_LEARNED.md](overview/LESSONS_LEARNED.md)** - Project insights and learnings

### 🛠️ Setup & Configuration
1. **[MCP_SETUP_GUIDE.md](setup/MCP_SETUP_GUIDE.md)** - MCP server configuration
2. **[WORKFLOW_CUSTOMIZATION.md](WORKFLOW_CUSTOMIZATION.md)** - Workflow customization options

### 💾 Persistence & State Management
1. **[COMPLETE_PERSISTENCE_SYSTEM.md](COMPLETE_PERSISTENCE_SYSTEM.md)** - ✅ Full persistence implementation
2. **[PROMPT_PERSISTENCE_IMPLEMENTATION.md](PROMPT_PERSISTENCE_IMPLEMENTATION.md)** - Prompt saving/loading
3. **[3D_PARAMETERS_PERSISTENCE_FIX.md](3D_PARAMETERS_PERSISTENCE_FIX.md)** - 3D parameter persistence
4. **[DYNAMIC_3D_PARAMETERS_IMPLEMENTATION.md](DYNAMIC_3D_PARAMETERS_IMPLEMENTATION.md)** - Dynamic 3D UI system

### 🐛 Bug Fixes & Solutions
1. **[HY3D_CAMERA_CONFIG_FIX.md](HY3D_CAMERA_CONFIG_FIX.md)** - Camera validation error fix
2. **[ASYNCIO_EVENT_LOOP_FIX.md](ASYNCIO_EVENT_LOOP_FIX.md)** - Event loop error resolution
3. **[3D_IMAGE_INJECTION_FIX.md](3D_IMAGE_INJECTION_FIX.md)** - Image pass-through fix

### 📅 Session Summaries
1. **[SESSION_2025_01_13_COMPLETE.md](SESSION_2025_01_13_COMPLETE.md)** - ✅ Persistence & bug fixes session

### 📈 Strategy & Planning
1. **[STRATEGIC_ROADMAP.md](overview/STRATEGIC_ROADMAP.md)** - Long-term project vision

---

## 🚨 Critical Documents for New Developers

### Must Read First:
1. **[CLAUDE.md](../CLAUDE.md)** - Claude's development notes and critical rules
2. **[CINEMA4D_API_REFERENCE.md](development/CINEMA4D_API_REFERENCE.md)** - NEVER use numeric IDs!
3. **[DEVELOPER_QUICKSTART.md](../DEVELOPER_QUICKSTART.md)** - Fast onboarding guide

### Current Status Files:
1. **[STAGE1_IMPLEMENTATION_COMPLETE.md](../STAGE1_IMPLEMENTATION_COMPLETE.md)** - Stage 1 completion
2. **[PHASE2_FIXES_COMPLETE.md](../PHASE2_FIXES_COMPLETE.md)** - Phase 2 bug fixes
3. **[UI_OPTIMIZATION_SUMMARY.md](../UI_OPTIMIZATION_SUMMARY.md)** - UI improvements

---

## 📁 File Organization Structure

```
comfy-to-c4d/
├── docs/                    # Main documentation
│   ├── api/                # API documentation
│   ├── development/        # Development guides
│   ├── guides/            # User guides
│   ├── overview/          # Project overview
│   ├── planning/          # Planning documents
│   └── setup/             # Setup guides
├── src/                    # Source code
│   ├── c4d/               # Cinema4D integration
│   ├── core/              # Core application
│   ├── mcp/               # MCP clients
│   ├── pipeline/          # Pipeline stages
│   ├── ui/                # User interface
│   └── utils/             # Utilities
├── mcp_servers/           # MCP server implementations
├── config/                # Configuration files
├── workflows/             # ComfyUI workflows
└── logs/                  # Application logs
```

---

## 🔍 Quick Navigation by Topic

### Cinema4D Object Creation
- Primitives: See [CINEMA4D_API_REFERENCE.md](development/CINEMA4D_API_REFERENCE.md#primitives)
- Generators: See [STAGE1_IMPLEMENTATION_COMPLETE.md](../STAGE1_IMPLEMENTATION_COMPLETE.md#generators)
- Deformers: See [CINEMA4D_INTEGRATION_STATUS.md](development/CINEMA4D_INTEGRATION_STATUS.md#deformers)

### UI Components
- Settings Dialogs: See [PHASE2_FIXES_COMPLETE.md](../PHASE2_FIXES_COMPLETE.md#settings-dialog)
- Blacklist Feature: See [PHASE2_FEATURES_TESTING.md](../PHASE2_FEATURES_TESTING.md#blacklist)

### Workflow Integration
- Image Generation: See [WORKFLOW_CUSTOMIZATION.md](WORKFLOW_CUSTOMIZATION.md#image-generation)
- 3D Generation: See [WORKFLOW_CUSTOMIZATION.md](WORKFLOW_CUSTOMIZATION.md#3d-generation)

---

## 📝 Documentation Standards

1. **File Naming**: Use UPPERCASE_WITH_UNDERSCORES.md
2. **Headers**: Start with # Title and include date/status
3. **Sections**: Use ## for main sections, ### for subsections
4. **Code Blocks**: Always specify language (```python, ```json, etc.)
5. **Status Indicators**: ✅ Complete, 🚧 In Progress, ❌ Failed, ⚠️ Warning

---

Last Updated: 2025-01-13