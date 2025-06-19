# 🎨 ComfyUI to Cinema4D Bridge

<p align="center">
  <img src="https://img.shields.io/badge/Status-80%25%20Complete-success?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Qt-6-green?style=for-the-badge&logo=qt" alt="Qt6">
  <img src="https://img.shields.io/badge/Cinema4D-2024+-red?style=for-the-badge" alt="Cinema4D">
</p>

<p align="center">
  <b>AI-Powered Creative Pipeline • From Text to Professional 3D Scenes</b>
</p>

---

## 🚀 Overview

Transform your creative ideas into complete 3D scenes using the power of AI. This production-ready desktop application seamlessly bridges ComfyUI's generative capabilities with Cinema4D's professional 3D workflow.

### ✨ Key Features

- 🖼️ **AI Image Generation** - FLUX workflows with real-time parameter control
- 🎭 **3D Model Creation** - Convert images to 3D models automatically  
- 🎨 **Smart Texturing** - Generate PBR materials for your 3D models
- 🎬 **Cinema4D Intelligence** - Create 83+ objects using natural language
- 🌙 **Professional Dark UI** - Qt6 interface designed for creative professionals

---

## 📸 Screenshots

<details>
<summary>Click to view interface screenshots</summary>

### Main Interface
![Main Interface](docs/images/interface_main.png)

### Image Generation Tab
![Image Generation](docs/images/tab_image_generation.png)

### 3D Model Creation
![3D Models](docs/images/tab_3d_models.png)

### Cinema4D Intelligence
![Cinema4D Chat](docs/images/tab_cinema4d.png)

</details>

---

## 🛠️ Installation

### Prerequisites
- 🐍 Python 3.12 or higher
- 🎨 ComfyUI installation with API enabled
- 🎬 Cinema4D R2024 or newer
- 💾 16GB RAM recommended
- 🖥️ Windows 10/11 (Linux/Mac support coming)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YourUsername/comfy-to-c4d.git
cd comfy-to-c4d

# 2. Run automated setup (Windows)
install_dependencies.bat

# 3. Configure your paths
# Edit .env file with your installations:
COMFYUI_PATH="C:/Path/To/ComfyUI"
CINEMA4D_PATH="C:/Program Files/Maxon Cinema 4D 2024"

# 4. Launch the application
launch.bat
```

📖 **Detailed Setup**: See [docs/setup/SETUP_GUIDE.md](docs/setup/SETUP_GUIDE.md)

---

## 🎯 Features & Capabilities

### 🖼️ Image Generation
- **FLUX Model Support** with LoRA integration
- **Dynamic UI** from any ComfyUI workflow
- **Batch Generation** with real-time monitoring
- **Session Management** for organized workflows

### 🎭 3D Model Generation  
- **Image-to-3D** conversion using Hy3D
- **Interactive Viewers** with rotation and zoom
- **Multiple Formats**: GLB, OBJ, FBX, GLTF
- **Smart Resource Management** (50 viewer limit)

### 🎨 Texture Generation
- **PBR Materials** from AI-generated textures
- **Workflow Integration** with automatic UI
- **Material Preview** before application
- **Batch Processing** for multiple models

### 🎬 Cinema4D Intelligence
```python
# Natural language commands:
"Create a red sphere"
"Add 10 cubes in a circle"
"Make a glass material"
"Animate with random effector"
```

**83+ Supported Objects** across 6 categories:
- ✅ Primitives (18 objects)
- ✅ Generators (25+ objects)  
- ✅ MoGraph Effectors (23 objects)
- ✅ Deformers (10 objects)
- ✅ Splines & Lights
- 🔄 Coming: Tags, Fields, Dynamics

---

## 📚 Documentation

### 🚀 Getting Started
- [**Setup Guide**](docs/setup/SETUP_GUIDE.md) - Complete installation walkthrough
- [**Quick Start**](docs/setup/QUICK_SETUP_REFERENCE.md) - Get running in 5 minutes
- [**Windows Guide**](docs/setup/WINDOWS_SETUP_GUIDE.md) - Windows-specific setup

### 👩‍💻 Development
- [**Developer Guide**](docs/DEVELOPMENT_GUIDE.md) - Architecture and patterns
- [**API Reference**](docs/development/TECHNICAL_REFERENCE.md) - Technical documentation
- [**Contributing**](CONTRIBUTING.md) - How to contribute

### 📖 User Guides
- [**Tab Guides**](docs/TAB_GUIDES.md) - Detailed guide for each feature
- [**Cinema4D Guide**](docs/CINEMA4D_GUIDE.md) - Cinema4D integration reference
- [**Troubleshooting**](docs/TROUBLESHOOTING.md) - Common issues and solutions

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Qt6 UI Layer  │────▶│  Core Engine     │────▶│ MCP Servers     │
│                 │     │                  │     │                 │
│ • Dark Theme    │     │ • Workflow Mgmt  │     │ • ComfyUI API   │
│ • Dynamic Forms │     │ • File Monitor   │     │ • Cinema4D MCP  │
│ • 3D Viewers    │     │ • Async Tasks    │     │ • WebSocket     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Tech Stack
- **Frontend**: PySide6 (Qt6), vispy for 3D
- **Backend**: Python 3.12+, asyncio, qasync  
- **Integration**: MCP protocol, REST APIs
- **Storage**: JSON configs, file monitoring

---

## 🎯 Roadmap

### ✅ Completed (80%)
- [x] Complete image generation pipeline
- [x] 3D model creation from images
- [x] Texture generation system
- [x] Cinema4D object creation (83+ objects)
- [x] Professional UI with dark theme
- [x] Session and file management

### 🚧 In Progress (15%)
- [ ] Remaining Cinema4D categories
- [ ] Advanced 3D viewer with PBR
- [ ] Natural language scene composition
- [ ] Performance optimizations

### 🔮 Future Plans (5%)
- [ ] Cloud rendering support
- [ ] Multi-user collaboration
- [ ] Plugin marketplace
- [ ] Mobile companion app

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Ways to Contribute
- 🐛 Report bugs and issues
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📚 Improve documentation
- 🎨 Share your creations

---

## 📊 Project Status

### Latest Updates (June 19, 2025)
- ✅ Fixed critical application stability issues
- ✅ Reduced console verbosity by 95%
- ✅ Improved error handling and recovery
- ✅ Enhanced documentation structure

### Statistics
- **Lines of Code**: 15,000+
- **Cinema4D Objects**: 83/120 implemented
- **Test Coverage**: 70%
- **Active Development**: Yes

---

## 🙏 Acknowledgments

This project wouldn't be possible without:
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - The amazing node-based UI
- [Cinema4D Python API](https://developers.maxon.net/) - Professional 3D integration
- [MCP Protocol](https://github.com/mcp/spec) - Standardized communication
- Our amazing community of testers and contributors

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>🎨 Built with ❤️ for Creative Professionals</b><br>
  <sub>Transform your imagination into reality</sub>
</p>

<p align="center">
  <a href="https://github.com/YourUsername/comfy-to-c4d/issues">Report Bug</a> •
  <a href="https://github.com/YourUsername/comfy-to-c4d/issues">Request Feature</a> •
  <a href="docs/CHANGELOG.md">Changelog</a>
</p>