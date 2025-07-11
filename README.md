<div align="center">

```
    ▄████▄   ▒█████   ███▄ ▄███▓  █████▒▓██   ██▓ █    ██  ██▓
   ▒██▀ ▀█  ▒██▒  ██▒▓██▒▀█▀ ██▒▓██   ▒  ▒██  ██▒ ██  ▓██▒▓██▒
   ▒▓█    ▄ ▒██░  ██▒▓██    ▓██░▒████ ░   ▒██ ██░▓██  ▒██░▒██▒
   ▒▓▓▄ ▄██▒▒██   ██░▒██    ▒██ ░▓█▒  ░   ░ ▐██▓░▓▓█  ░██░░██░
   ▒ ▓███▀ ░░ ████▓▒░▒██▒   ░██▒░▒█░      ░ ██▒▓░▒▒█████▓ ░██░
   ░ ░▒ ▒  ░░ ▒░▒░▒░ ░ ▒░   ░  ░ ▒ ░       ██▒▒▒ ░▒▓▒ ▒ ▒ ░▓  
   ░  ▒     ░ ▒ ▒░ ░  ░      ░ ░       ▓██ ░▒░ ░░▒░ ░ ░  ▒ ░
                                    ░      ▒ ▒ ░░   ░░░ ░ ░  ▒ ░
    ╔═╗╦╔╗╔╔═╗╔╦╗╔═╗  ╦ ╦╔╦╗     ░        ░ ░        ░      ░  
    ║  ║║║║║╣ ║║║╠═╣  ╚═╦╝ ║║                ░ ░                
    ╚═╝╩╝╚╝╚═╝╩ ╩╩ ╩    ╩══╩╝                                  
```


</div>

---

> [!CAUTION]
> **This project is experimental and not fully functional, But you should be fine connecting Claude Code to the database and ask it to connect all the environment varaibles and mcps** Most features are incomplete or broken. Do not use in production.

---

## 📽️ **Demo Video**

<div align="center">

[![Watch Demo on Vimeo](https://img.shields.io/badge/▶️_Play_Demo-2.5_minutes-00ADEF?style=for-the-badge&logo=vimeo&logoColor=white)](https://vimeo.com/1100563312)

</div>

## 🎯 **Project**

bridge **ComfyUI's AI generation capabilities** with **Cinema 4D's p tools** for a quick scene creation through an intuitive desktop application.


## 🏗️ **App Architecture**

```mermaid
graph LR
    A[PySide6 UI] --> B[Core Engine]
    B --> C[ComfyUI API]
    B --> D[Cinema4D MCP]
    C --> E[WebSocket]
    D --> F[Python Bridge]
```

---

### ✅ ** Working **
- **Basic UI Framework** - PySide6 application with tabs and responsive design
- **ComfyUI & Cinema4D connection** - WebSocket integration via MCP
- **ComfyUI Workflow Loading** - JSON workflow execution working for both image and 3D generation
- **Configuration System** - Settings and state management
- **MCP Servers** - Basic Model Context Protocol setup working
- **3D Model Generation** - Hunyuan2 mesh creation pipeline
- **Texture Generation** - JuggernautXL PBR texturing pipeline


### 📅 **WIP**
- **Cinema4D Bridge** - Direct scene import (only basic control is implemented)
- **NLP Commands** - Natural language scene control (70% c4d commands mapped via SDK and experiments)
- **3D Preview** - New Three.js viewer integrated
- **MoGraph Integration** - Smart scattering of generated objects on terreins via NLP
- **Batch Processing** - Queue multiple generations was working but need to revise fully
---

## 🛠️ **TECHNICAL STACK**

<div align="center">

| Component | Technology | Status |
|:---------:|:----------:|:------:|
| **Frontend** | PySide6 + Custom Dark Theme | ✅ 75% |
| **Backend** | Python 3.9+ Async | ✅ 60% |
| **AI Engine** | ComfyUI WebSocket API | ✅ 80% |
| **3D Bridge** | Cinema4D Python + MCP | 🔄 40% |
| **Workflows** | JSON Pipeline System | ✅ Ready |
| **Storage** | Local File + Config | ✅ Ready |

</div>

---

## 📊 **DEVELOPMENT PROGRESS**

```
Core Systems      ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░  60%
UI/UX Design      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░  75%
ComfyUI Bridge    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░  80%
C4D Integration   ▓▓▓▓▓▓▓▓░░░░░░░░░░░░  40%
Documentation     ▓▓▓▓▓▓░░░░░░░░░░░░░░  30%
Testing Suite     ▓▓▓▓░░░░░░░░░░░░░░░░  20%
```

---

## 🚀 **QUICK START** *(When Ready)*

```bash
# ⚠️ NOT RECOMMENDED - PROJECT IS NOT FUNCTIONAL YET

# Future installation:
git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
cd comfyui-cinema4d-bridge
pip install -r requirements.txt
python main.py
```

---

## 📁 **PROJECT STRUCTURE**

```
comfy-to-c4d/
├── src/
│   ├── core/          # Main application logic
│   ├── ui/            # PySide6 interface components
│   ├── mcp/           # Model Context Protocol clients
│   └── c4d/           # Cinema4D integration modules
├── workflows/         # ComfyUI workflow definitions
├── mcp_servers/       # MCP server implementations
├── config/           # Configuration files
└── mp4/              # Demo videos
```

---

## 🤝 **CONTRIBUTING**

<div align="center">

```
╔════════════════════════════════════════════╗
║  The codebase is changing rapidly.         ║
║  Watch this repo for beta announcements.   ║
╚════════════════════════════════════════════╝
```

</div>

---

<div align="center">

**Vibe coded by Yambo and Claude Code**

[⬆ Back to Top](#comfyui--cinema-4d-bridge)

</div>