# Documentation Index

> [!WARNING]
> **EXPERIMENTAL PROJECT** - This documentation covers a project that is NOT fully functional. Many features described are broken or incomplete.

## Getting Started (For Developers)

- **[README.md](../README.md)** - Project overview with clear warnings
- **[QUICKSTART.md](../QUICKSTART.md)** - Developer setup (NOT a working app guide)
- **[CLAUDE.md](../CLAUDE.md)** - Using Claude Code to fix the project

## 📚 Core Documentation

### Setup & Configuration
- **[SETUP.md](SETUP.md)** - Installation guide (for development only)
- **[CONFIG.md](CONFIG.md)** - Configuration reference
- **[.env.example](../.env.example)** - Environment variables template

### Technical Reference
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System design (partially implemented)
- **[API.md](API.md)** - API endpoints (many non-functional)
- **[PARAMETERS.md](PARAMETERS.md)** - UI parameter system

### Development
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to help fix this project
- **[issues/](../issues/)** - Known problems and bugs

## 📂 Feature Status

### What's Actually Working ✅
- Basic UI Framework (PySide6 tabs)
- ComfyUI Connection (80% functional)
- Some workflow loading
- Basic configuration system

### What's Partially Working ⚠️
- 3D Model Generation (Hunyuan3D pipeline)
- Texture Generation (JuggernautXL pipeline)
- Three.js viewer (limited functionality)

### What's Broken ❌
- Most Cinema4D features (40% complete)
- NLP commands (70% mapped but not working)
- Batch processing
- Many error handlers

## 🔍 Quick Links by Need

### To Understand the Project
1. Read [README.md](../README.md) warnings first
2. Check [ARCHITECTURE.md](../ARCHITECTURE.md) for intended design
3. Use [CLAUDE.md](../CLAUDE.md) to navigate code

### To Fix Issues
1. See [CLAUDE.md](../CLAUDE.md) for debugging help
2. Check [issues/](../issues/) for known problems
3. Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

### To Configure
1. Copy `.env.example` to `.env`
2. See [CONFIG.md](CONFIG.md) for settings
3. Ask Claude Code for help with MCP setup

## 📊 Documentation Status

| Document | Reality Check | Actual Status |
|----------|---------------|---------------|
| README | Accurate warnings | ✅ Updated |
| QUICKSTART | For developers only | ✅ Updated |
| ARCHITECTURE | Describes goals, not reality | ⚠️ Aspirational |
| CLAUDE | Essential for this project | ✅ Updated |
| SETUP | Missing experimental warnings | ⚠️ Needs update |
| CONFIG | Mostly accurate | ⚠️ Needs review |
| API | Many endpoints don't work | ❌ Misleading |
| PARAMETERS | Partially implemented | ⚠️ Incomplete |
| CONTRIBUTING | Needs experimental context | ⚠️ Needs update |

## 🗂️ Legacy Documentation

Archived documentation from previous attempts:
- `/archive/` - Historical fixes and sessions
- `/docs/archive/` - Old guides (likely outdated)

## ⚠️ Important Notes

1. **This is NOT production software** - It's an experimental project
2. **Many features don't work** - Despite appearing complete in code
3. **Use Claude Code** - Essential for understanding and fixing
4. **Check the README warnings** - Before attempting to use
5. **Focus on core fixes** - Before adding new features

---

*Last accurate update: 2025-07-11*
*Original docs claimed: 2025-06-26 (inaccurate)*