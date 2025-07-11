# Using Claude Code with ComfyUI-Cinema4D Bridge

> [!NOTE]
> Claude Code is essential for working with this experimental project. It can help you navigate the complex codebase and fix broken features.

## Getting Started with Claude Code

### 1. Connect to the Project
```bash
# In your project directory
claude-code .
```

### 2. Key Tasks for Claude Code

#### Environment Setup
Ask Claude Code to:
- "Help me connect all environment variables"
- "Set up the MCP servers for ComfyUI and Cinema4D"
- "Configure the database connections"

#### Debugging
- "Why is the Cinema4D connection failing?"
- "Help me fix the workflow execution errors"
- "Debug the WebSocket connection to ComfyUI"

#### Understanding the Code
- "Explain how the workflow manager works"
- "What's the current state of Cinema4D integration?"
- "Which features are actually working?"

### 3. MCP Server Configuration

The project uses Model Context Protocol (MCP) servers:

#### ComfyUI MCP Server
Location: `mcp_servers/comfyui-mcp-server/`
- Handles ComfyUI API communication
- Manages workflow execution

#### Cinema4D MCP Server  
Location: `mcp_servers/cinema4d-mcp/`
- Controls Cinema4D via Python API
- Currently 40% functional

### 4. Common Claude Code Commands

```bash
# Analyze the codebase
"Review the current implementation status"

# Fix issues
"Help me fix the texture generation pipeline"
"Debug why 3D models aren't loading"

# Add features
"Implement the missing NLP commands"
"Complete the batch processing functionality"
```

### 5. Database and Configuration

Ask Claude Code to help with:
- Setting up the SQLite database (if used)
- Configuring the JSON workflow files
- Managing the state persistence

### 6. Development Workflow

1. Use Claude Code to understand existing code
2. Ask it to identify broken features
3. Work together to implement fixes
4. Test incrementally

## Important Notes

- Many features appear complete but don't work
- Claude Code can help identify non-functional code
- Focus on fixing core features before adding new ones
- The codebase is experimental and rapidly changing