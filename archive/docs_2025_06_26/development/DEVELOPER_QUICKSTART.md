# Developer Quick Start Guide - Cinema4D Intelligence

## 🚀 Getting Started in 5 Minutes

### 1. Launch the Application
```bash
# On Windows
launch.bat
```

### 2. Navigate to Scene Assembly Tab
The Cinema4D Intelligence interface is in the **Scene Assembly** tab.

### 3. Test Basic Commands
Try these in the chat:
- "create a cube"
- "create a sphere"
- "test connection"

## 📁 Project Structure for C4D Intelligence

```
src/
├── c4d/                      # Cinema4D logic
│   ├── nlp_parser.py        # Add patterns here
│   ├── mcp_wrapper.py       # Add C4D commands here
│   └── operation_generator.py # Connect patterns to commands
└── ui/
    └── knowledge_dictionary.py # Add examples here
```

## 🎯 Adding Your First Command

### Example: "create a red cube"

#### 1. Add Pattern (`src/c4d/nlp_parser.py`)
```python
# In PATTERN_LIBRARY
"colored_cube": {
    "keywords": ["red cube", "blue cube", "colored cube"],
    "operation": OperationType.CREATE_COLORED_CUBE,
    "extract": ["color"]
}

# In OperationType enum
CREATE_COLORED_CUBE = "create_colored_cube"
```

#### 2. Add C4D Command (`src/c4d/mcp_wrapper.py`)
```python
async def create_colored_cube(self, color: str = "red") -> OperationResult:
    """Create a colored cube"""
    # Map color names to RGB
    colors = {
        "red": (1, 0, 0),
        "blue": (0, 0, 1),
        "green": (0, 1, 0)
    }
    rgb = colors.get(color, (1, 1, 1))
    
    script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
cube = c4d.BaseObject(c4d.Ocube)
cube.SetName("{color.title()} Cube")

# Create material
mat = c4d.BaseMaterial(c4d.Mmaterial)
mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector{rgb}
doc.InsertMaterial(mat)

# Assign material
tag = cube.MakeTag(c4d.Ttexture)
tag[c4d.TEXTURETAG_MATERIAL] = mat

doc.InsertObject(cube)
c4d.EventAdd()
"""
    return await self.execute_command(
        command="execute_python",
        parameters={"code": script}
    )
```

#### 3. Connect in Generator (`src/c4d/operation_generator.py`)
```python
# In generate() method
elif intent.operation_type == OperationType.CREATE_COLORED_CUBE:
    color = "white"  # default
    for word in ["red", "blue", "green", "yellow"]:
        if word in intent.original_text.lower():
            color = word
            break
    
    operations.append(C4DOperation(
        operation_type=OperationType.CREATE_COLORED_CUBE,
        description=f"Creating {color} cube",
        parameters={"color": color}
    ))
```

#### 4. Test It!
1. Restart the app
2. Type "create a red cube" in chat
3. See the result in Cinema4D

## 🔍 Debugging Tips

### Enable Debug Output
```python
# In any module
self.logger.info(f"Debug: {variable}")
self.logger.debug(f"Detailed: {data}")
```

### Check Console Output
The app shows debug info in the console where you launched it.

### Test C4D Scripts
1. Copy script from `mcp_wrapper.py`
2. Paste in Cinema4D Script Manager
3. Run to verify it works

## 📚 Essential Cinema4D Python

### Object IDs
```python
c4d.Ocube      # Cube
c4d.Osphere    # Sphere  
c4d.Ocylinder  # Cylinder
c4d.Oplane     # Plane
c4d.Mocloner   # Cloner
c4d.Obend      # Bend deformer
```

### Common Operations
```python
# Create object
obj = c4d.BaseObject(c4d.Ocube)

# Set name
obj.SetName("My Cube")

# Set position
obj.SetAbsPos(c4d.Vector(100, 0, 0))

# Set size (for primitives)
obj[c4d.PRIM_CUBE_LEN] = c4d.Vector(200, 200, 200)

# Insert to scene
doc.InsertObject(obj)

# Update viewport
c4d.EventAdd()
```

## 🎨 Command Ideas to Implement

### Easy (Start Here)
- [ ] "create a pyramid"
- [ ] "make a large sphere"
- [ ] "create 5 cubes"

### Medium
- [ ] "create cubes in a line"
- [ ] "make a grid of spheres"
- [ ] "add a bend deformer"

### Advanced
- [ ] "scatter cubes randomly"
- [ ] "create bouncing animation"
- [ ] "make objects glow"

## 🔧 Common Issues

### Command Not Recognized
- Check pattern keywords in `nlp_parser.py`
- Verify OperationType enum is defined
- Look for typos in pattern name

### C4D Script Error
- Test script in C4D directly
- Check Cinema4D console for errors
- Verify object IDs are correct

### Nothing Happens
- Check console for Python errors
- Verify MCP connection (green indicator)
- Ensure Cinema4D has active document

## 📈 Next Steps

1. **Start Simple**: Implement one primitive at a time
2. **Test Often**: Use chat after each addition
3. **Build Up**: Add parameters once basics work
4. **Document**: Update knowledge dictionary

## 🔗 Quick Links

- **Main Guide**: `docs/CINEMA4D_INTELLIGENCE_GUIDE.md`
- **Command Expansion**: `docs/COMMAND_EXPANSION_QUICKSTART.md`
- **Pattern Library**: `src/c4d/nlp_parser.py`
- **MCP Wrapper**: `src/c4d/mcp_wrapper.py`

## 💡 Pro Tips

1. **Use existing commands as templates**
2. **Start with hardcoded values, add parameters later**
3. **Test C4D scripts separately first**
4. **Add logging to track execution flow**
5. **Keep commands simple and focused**

Happy coding! The framework is ready - just add your creativity! 🎬✨