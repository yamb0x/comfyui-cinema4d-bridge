# API Reference

MCP endpoints and integration points for ComfyUI and Cinema4D.

## ComfyUI MCP Integration

### Connection
- **Protocol**: HTTP REST + WebSocket
- **Default Port**: 8188
- **Base URL**: `http://localhost:8188`

### Endpoints

#### Queue Workflow
```python
POST /prompt
Content-Type: application/json

{
  "prompt": {workflow_json},
  "client_id": "comfy2c4d_client"
}

Response:
{
  "prompt_id": "uuid-string",
  "number": 1
}
```

#### Get History
```python
GET /history/{prompt_id}

Response:
{
  "prompt_id": {
    "outputs": {
      "node_id": {
        "images": [{
          "filename": "image.png",
          "subfolder": "",
          "type": "output"
        }]
      }
    }
  }
}
```

#### WebSocket Updates
```python
WS /ws?clientId=comfy2c4d_client

Messages:
{
  "type": "executing",
  "data": {"node": "node_id"}
}
{
  "type": "progress",
  "data": {"value": 50, "max": 100}
}
{
  "type": "executed",
  "data": {"node": "node_id", "output": {...}}
}
```

### Image Retrieval
```python
GET /view?filename={filename}&subfolder={subfolder}&type={type}
```

## Cinema4D MCP Integration

### Connection
- **Protocol**: TCP Socket (MCP)
- **Default Port**: 54321
- **Format**: JSON messages

### Available Tools

#### Execute Python
```python
{
  "tool": "execute_python",
  "code": "import c4d\nprint('Hello')"
}
```

#### Create Primitive
```python
{
  "tool": "create_primitive",
  "primitive_type": "cube",
  "name": "MyCube",
  "parameters": {
    "size": [200, 200, 200],
    "position": [0, 0, 0]
  }
}
```

#### Import Object
```python
{
  "tool": "import_object",
  "file_path": "/path/to/model.obj",
  "name": "ImportedModel"
}
```

#### Create Material
```python
{
  "tool": "create_material",
  "name": "MyMaterial",
  "color": [1.0, 0.5, 0.0],
  "properties": {
    "reflection": 0.5,
    "roughness": 0.3
  }
}
```

#### Natural Language Processing
```python
{
  "tool": "nlp_command",
  "command": "create a red sphere at position 100,200,0"
}
```

## Client Implementation

### ComfyUI Client
```python
class ComfyUIClient:
    async def queue_workflow(self, workflow: dict) -> str:
        """Submit workflow for processing"""
        
    async def get_history(self, prompt_id: str) -> dict:
        """Get execution results"""
        
    async def download_image(self, filename: str) -> bytes:
        """Download generated image"""
```

### Cinema4D Client
```python
class Cinema4DClient:
    async def execute_command(self, command: str) -> dict:
        """Execute NLP command"""
        
    async def create_primitive(self, prim_type: str, **params) -> bool:
        """Create C4D primitive"""
        
    async def import_model(self, path: str) -> bool:
        """Import 3D model"""
```

## Error Handling

### ComfyUI Errors
```python
{
  "error": {
    "type": "validation_error",
    "message": "Missing required input",
    "details": {
      "node": "7",
      "input": "model"
    }
  }
}
```

### Cinema4D Errors
```python
{
  "success": false,
  "error": "Failed to create object: Invalid parameters"
}
```

## Rate Limiting

- ComfyUI: No built-in limits
- Cinema4D: Sequential command processing
- Recommended: Queue management in client

## Authentication

Currently no authentication required for local connections.

## Best Practices

1. **Connection Management**
   - Implement reconnection logic
   - Handle WebSocket disconnects
   - Timeout long-running operations

2. **Error Recovery**
   - Retry failed requests
   - Validate workflows before submission
   - Handle partial failures

3. **Performance**
   - Cache model listings
   - Batch operations when possible
   - Use WebSocket for real-time updates

## Extension Points

### Custom Nodes
ComfyUI custom nodes are automatically supported through dynamic UI generation.

### Cinema4D Scripts
Additional Python scripts can be loaded through the execute_python tool.

## Testing

### ComfyUI Test
```bash
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": {...}}'
```

### Cinema4D Test
```python
# In Script Manager
from mcp_server import test_connection
test_connection()
```