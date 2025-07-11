# NLP Dictionary Guide

## Overview

The NLP Dictionary is a centralized command management system for Cinema4D operations. It provides a user-friendly interface to manage, configure, and execute Cinema4D commands through natural language processing (NLP) keywords.

## Features

### 1. **Command Categories**
The dictionary organizes commands into logical categories:
- **Primitives**: Basic geometric shapes (cube, sphere, cylinder, etc.)
- **Generators**: NURBS and modeling generators (extrude, lathe, sweep, etc.)
- **Splines**: Spline creation tools
- **Deformers**: Object deformation tools
- **Cameras & Lights**: Scene illumination and viewing
- **Tags**: Object properties and behaviors
- **MoGraph**: Motion graphics tools
- **Effectors**: MoGraph effectors
- **Fields**: Field objects
- **Dynamic Tags**: Physics simulation
- **Volumes**: Volume objects
- **Modeling Tools**: Mesh editing operations
- **Materials**: Material and texture management
- **Render Settings**: Rendering configuration

### 2. **Command Management**
Each command entry includes:
- **Name**: Display name for the command
- **C4D Constant**: The Cinema4D API constant (e.g., `c4d.Ocube`)
- **Keywords**: NLP trigger words for the command
- **Description**: Brief explanation of what the command does
- **Parameters**: Default values for command parameters

### 3. **Actions**
For each command, you can:
- **Create in C4D**: Execute the command with current parameters
- **⚙️ Settings**: Configure detailed parameters
- **🗑️ Remove**: Permanently remove the command (with confirmation)
- **🧪 Test**: Test the command execution

## Usage

### Accessing the NLP Dictionary
1. Click on **AI** menu in the main application
2. Select **NLP Dictionary**

### Adding Commands
1. Select a category tab
2. Click **+ Add New Command**
3. Fill in the command details:
   - Name
   - C4D Constant
   - Keywords (comma-separated)
   - Description
   - Default parameters

### Editing Commands
1. Select a command from the list
2. Modify fields in the right panel
3. Click **Save Changes** to persist modifications

### Removing Commands
1. Select a command to remove
2. Click **🗑️ Remove**
3. Confirm the removal in the popup dialog
4. Note: Removed commands can only be restored by manually editing the configuration file

### Creating Objects
1. Select a command
2. Adjust parameters if needed
3. Click **Create in C4D**
4. The object will be created in the active Cinema4D scene

## File Storage

The dictionary data is stored in:
```
config/nlp_dictionary.json
```

This file contains all command definitions and can be manually edited if needed.

## Default Commands

### Primitives (18 objects)
- Cube, Sphere, Cylinder, Cone, Torus
- Plane, Disc, Pyramid, Tube
- Figure, Platonic, Landscape
- Oil Tank, Capsule, Relief
- Single Polygon, Fractal, Formula

### Generators (25+ objects)
- Array, Boolean, Cloner, Matrix
- Extrude, Lathe, Loft, Sweep
- Subdivision Surface, Symmetry
- Instance, Metaball, Bezier
- Connect, Spline Wrap, Polygon Reduction
- Fracture, Voronoi Fracture, Tracer, MoSpline
- Hair, Fur, Grass, Feather, Explosion FX, Text

## Integration with NLP

The keywords defined for each command will be used by the chat interface to:
1. Recognize user intent
2. Map natural language to Cinema4D commands
3. Execute appropriate actions

Example:
- User types: "create a donut"
- System recognizes keyword "donut" → Torus primitive
- Creates torus with default parameters

## Best Practices

1. **Keywords**: Use multiple variations of words users might type
   - Good: ["sphere", "ball", "orb", "globe"]
   - Bad: ["sphere"]

2. **Descriptions**: Keep them brief but informative
   - Good: "Creates a sphere primitive with customizable segments"
   - Bad: "Sphere"

3. **Parameters**: Set sensible defaults that work for most cases
   - Size: 100-200 units
   - Segments: Balanced between quality and performance
   - Position: Origin (0, 0, 0) or slightly elevated

4. **Organization**: Keep related commands in appropriate categories

## Troubleshooting

### Commands not creating
1. Check Cinema4D is connected
2. Verify the C4D constant is correct
3. Check the console for error messages

### Dictionary not saving
1. Ensure config directory exists
2. Check file permissions
3. Look for error messages in logs

### Missing commands
1. Check if the nlp_dictionary.json file exists
2. Verify the file isn't corrupted
3. Restore from backup if needed

## Future Enhancements

- Import/Export command sets
- Command templates
- Batch operations
- Advanced parameter editors
- Command history and undo
- Integration with AI chat interface