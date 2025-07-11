# QUICKSTART Guide

> [!CAUTION]
> **This project is EXPERIMENTAL and NOT fully functional.** Many features are incomplete or broken. This guide is for developers who want to help fix the project, not for production use.

## Prerequisites

- Python 3.9+
- ComfyUI installed and running
- Cinema 4D R21+ (for C4D features)
- Claude Code (for development assistance)

## Quick Setup for Developers

1. **Clone the repository**
   ```bash
   git clone https://github.com/yamb0x/comfyui-cinema4d-bridge.git
   cd comfyui-cinema4d-bridge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Connect MCP servers** (if using Claude Code)
   - Ask Claude Code to help connect environment variables
   - Configure MCP servers for ComfyUI and Cinema4D

5. **Run the application**
   ```bash
   python main.py
   ```

## What's Actually Working

-  Basic UI launches
-  ComfyUI connection (if configured correctly)
-  Some workflow loading
-   Limited 3D generation
-   Basic texture generation
- L Most Cinema4D features broken

## Getting Help

Use Claude Code to:
- Connect database and environment variables
- Debug connection issues
- Understand the codebase
- Fix broken features

## Warning

This is NOT a "quick start" to a working application. This is a guide for developers who want to help build and fix an experimental project.