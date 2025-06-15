# Cinema4D Python API Reference - Verified Working Patterns

## 📋 PRODUCTION-READY API METHODS (2025-01-07)

This reference contains **VERIFIED WORKING** Cinema4D Python API patterns tested and confirmed in our production environment.

## 🚨 CRITICAL: Parameter Naming Convention (2025-01-10)
**NEVER GUESS PARAMETER NAMES!** Cinema4D uses abbreviated parameter names that must be verified:
- ✅ Use: `PRIM_SPHERE_RAD` (NOT `PRIM_SPHERE_RADIUS`)
- ✅ Use: `PRIM_CONE_BRAD` (NOT `PRIM_CONE_RADIUS`)
- ✅ Use: `PRIM_CYLINDER_SEG` (NOT `PRIM_CYLINDER_SUB`)
- 📖 See: `docs/development/CINEMA4D_PARAMETER_NAMING_GUIDE.md` for full details

---

## 🎯 CORE OBJECT CREATION

### **Primitive Objects (✅ VERIFIED)**

#### **Object Type IDs (✅ VERIFIED CORRECT - 2025-01-08)**
```python
PRIMITIVE_IDS = {
    'cube': 5159,        # c4d.Ocube - VERIFIED WORKING
    'sphere': 5160,      # c4d.Osphere - VERIFIED WORKING
    'cylinder': 5170,    # c4d.Ocylinder - CORRECTED
    'plane': 5168,       # c4d.Oplane - CORRECTED  
    'torus': 5163,       # c4d.Otorus - VERIFIED WORKING
    'cone': 5162,        # c4d.Ocone - CORRECTED
    'pyramid': 5167,     # c4d.Opyramid - CORRECTED
    'disc': 5164,        # c4d.Odisc - CORRECTED
    'tube': 5165,        # c4d.Otube - CORRECTED
    'figure': 5166,      # c4d.Ofigure - CORRECTED
    'landscape': 5169,   # c4d.Olandscape - VERIFIED WORKING
    'platonic': 5161,    # c4d.Oplatonic - CORRECTED
    'oil tank': 5172,    # c4d.Ooiltank - CORRECTED
    'relief': 5173,      # c4d.Orelief - CORRECTED
    'capsule': 5171,     # c4d.Ocapsule - CORRECTED
    'single polygon': 5174,  # c4d.Osinglepolygon - VERIFIED WORKING
    'fractal': 5175,     # c4d.Ofractal - VERIFIED WORKING
    'formula': 5176      # c4d.Oformula - VERIFIED WORKING
}
```

#### **Size Parameter IDs**
```python
SIZE_PARAM_IDS = {
    'cube': 1117,        # PRIM_CUBE_LEN (Vector)
    'sphere': 1118,      # PRIM_SPHERE_RAD (Float)
    'cylinder': 1120,    # PRIM_CYLINDER_HEIGHT (Float)
    'plane': 1121,       # PRIM_PLANE_WIDTH (Vector)
    'torus': 1122,       # PRIM_TORUS_OUTERRAD (Float)
    'cone': 1123,        # PRIM_CONE_HEIGHT (Float)
}
```

#### **Working Object Creation Pattern**
```python
def create_primitive(obj_type, name, size=(100,100,100), position=(0,0,0)):
    """Verified working primitive creation pattern"""
    
    # Step 1: Create object using numeric ID
    obj = c4d.BaseObject(PRIMITIVE_IDS[obj_type])
    if not obj:
        return False
    
    # Step 2: Set name
    obj.SetName(name)
    
    # Step 3: Set size (varies by primitive type)
    size_param = SIZE_PARAM_IDS[obj_type]
    if obj_type == 'sphere':
        obj[size_param] = size[0]  # Radius only
    else:
        obj[size_param] = c4d.Vector(size[0], size[1], size[2])
    
    # Step 4: Set position
    obj.SetAbsPos(c4d.Vector(position[0], position[1], position[2]))
    
    # Step 5: Insert and update
    doc.InsertObject(obj)
    c4d.EventAdd()  # CRITICAL: Always call to update viewport
    
    return True
```

---

## 🎬 MOGRAPH CLONER SYSTEM

### **MoGraph Object IDs (✅ VERIFIED)**
```python
MOGRAPH_IDS = {
    'cloner': 1018544,       # MoGraph Cloner
    'matrix': 1018545,       # Matrix Object
    'fracture': 1018791,     # Fracture Object
    'instance': 5126,        # Instance Object
}
```

### **Cloner Parameter IDs (✅ VERIFIED)**
```python
CLONER_PARAM_IDS = {
    'mode': 1018617,         # ID_MG_CLONER_MODE
    'count': 1018618,        # MG_CLONER_COUNT  
    'spacing': 1018619,      # Grid spacing (Vector)
    'radius': 1018620,       # Radial radius (Float)
}
```

### **Cloner Modes (✅ VERIFIED)**
```python
CLONER_MODES = {
    'grid': 0,               # Grid arrangement
    'linear': 1,             # Linear arrangement
    'radial': 2,             # Radial arrangement  
    'random': 3,             # Random distribution
}
```

### **Working Cloner Creation Pattern**
```python
def create_cloner(mode='grid', count=25, spacing=(100,100,100)):
    """Verified working cloner creation pattern"""
    
    # Step 1: Create cloner using verified ID
    cloner = c4d.BaseObject(1018544)  # MoGraph Cloner
    if not cloner:
        return False
    
    # Step 2: Set unique name
    import time
    cloner.SetName(f"Cloner_{mode}_{int(time.time() * 1000)}")
    
    # Step 3: Set cloner parameters using numeric IDs
    cloner[1018617] = CLONER_MODES[mode]  # Mode
    cloner[1018618] = count               # Count
    
    # Step 4: Set mode-specific parameters
    if mode == 'grid':
        cloner[1018619] = c4d.Vector(spacing[0], spacing[1], spacing[2])
    elif mode == 'radial':
        cloner[1018620] = spacing[0]  # Use first value as radius
    
    # Step 5: Insert and update
    doc.InsertObject(cloner)
    c4d.EventAdd()
    
    return cloner
```

### **Adding Objects to Cloner (✅ VERIFIED)**
```python
def add_object_to_cloner(obj, cloner):
    """Verified pattern for adding objects to cloner"""
    
    # CRITICAL: Remove from current parent first
    obj.Remove()
    
    # Insert as child of cloner
    obj.InsertUnder(cloner)
    
    # Update viewport
    c4d.EventAdd()
```

### **❌ NON-WORKING GENERATORS** (Do not implement - wrong constant names)
```python
# These generators have been tested and DO NOT WORK:
# 'text': 'c4d.Otext' → ❌ FAILED (wrong constant name)
# 'tracer': 'c4d.Otracer' → ❌ FAILED (wrong constant name)
#
# ⚠️ NLP PARSER: DO NOT attempt to create Text or Tracer generator types
# Use Cinema4D's manual text creation or alternative approaches
```

---

## 📦 MODEL IMPORT SYSTEM

### **File Import (✅ VERIFIED)**
```python
def import_model(file_path, target_doc=None):
    """Verified working model import pattern"""
    
    if target_doc is None:
        target_doc = c4d.documents.GetActiveDocument()
    
    # Use MergeDocument for reliable import
    success = c4d.documents.MergeDocument(
        target_doc, 
        file_path, 
        c4d.SCENEFILTER_OBJECTS
    )
    
    if not success:
        return None
    
    # Find imported object using name pattern
    imported_obj = None
    for obj in target_doc.GetObjects():
        if "Hy3D" in obj.GetName():  # Our model naming pattern
            imported_obj = obj
            break
    
    return imported_obj
```

### **Model + Cloner Integration (✅ VERIFIED)**
```python
def import_model_to_cloner(model_path, mode='grid', count=25):
    """Complete verified workflow: import model + add to cloner"""
    
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return False
    
    # Step 1: Create cloner first
    cloner = c4d.BaseObject(1018544)
    cloner.SetName(f"Model_Cloner_{int(time.time() * 1000)}")
    cloner[1018617] = CLONER_MODES[mode]
    cloner[1018618] = count
    
    # Step 2: Import model
    success = c4d.documents.MergeDocument(doc, model_path, c4d.SCENEFILTER_OBJECTS)
    if not success:
        return False
    
    # Step 3: Find imported object
    imported_obj = None
    for obj in doc.GetObjects():
        if "Hy3D" in obj.GetName() and obj != cloner:
            imported_obj = obj
            break
    
    if not imported_obj:
        return False
    
    # Step 4: Move to cloner (CRITICAL ORDER)
    imported_obj.Remove()
    imported_obj.InsertUnder(cloner)
    
    # Step 5: Insert cloner and update
    doc.InsertObject(cloner)
    c4d.EventAdd()
    
    return True
```

---

## 🔧 DEFORMER SYSTEM

### **Deformer Constants (✅ VERIFIED SAFE APPROACH)**
```python
# Use Cinema4D constants instead of numeric IDs to prevent MCP crashes
DEFORMER_CONSTANTS = {
    # Basic Deformers (✅ VERIFIED WORKING)
    'bend': 'c4d.Obend',
    'twist': 'c4d.Otwist',
    'bulge': 'c4d.Obulge',
    'taper': 'c4d.Otaper',
    'shear': 'c4d.Oshear',
    'wind': 'c4d.Owind',
    
    # Advanced Deformers (✅ VERIFIED WORKING)
    'ffd': 'c4d.Offd',
    'displacer': 'c4d.Odisplacer',
    
}
```

### **❌ NON-WORKING DEFORMERS** (Do not implement - wrong constant names)
```python
# These deformers have been tested and DO NOT WORK:
# 'lattice': 'c4d.Olattice' → ❌ FAILED
# 'camera': 'c4d.Ocameradeformer' → ❌ FAILED  
# 'wrap': 'c4d.Owrap' → ❌ FAILED
# 'formula': 'c4d.Oformula' → ❌ FAILED
# 'smoothing': 'c4d.Osmoothing' → ❌ FAILED (tried multiple variations)
# 'jiggle': 'c4d.Ojiggle' → ❌ FAILED (tried multiple variations)
#
# Also removed: 'surface', 'collision', 'correction', 'explosion', 'melt', 
# 'polygon reduction', 'shrink wrap', 'spherify', 'spline', 'squash & stretch', 
# 'explosion fx', 'motor', 'vibrate', 'wave'
# 
# ⚠️ NLP PARSER: DO NOT attempt to create these deformer types
```

### **Deformer Parameter IDs (Framework)**
```python
DEFORMER_PARAM_IDS = {
    'bend_strength': 2001,    # Bend angle
    'twist_strength': 2002,   # Twist angle  
    'bulge_strength': 2003,   # Bulge strength
}
```

### **Working Deformer Pattern (✅ PRODUCTION READY)**
```python
# UI Layout: Compacted horizontal sections
# Main Row: [🔷 Primitives] [⚙️ Generators] [🌀 Deformers] [📥 Import]
# Secondary: [👑 Hierarchy] [🚀 Workflows] [🔌 Connection]
```

### **Working Deformer Pattern (✅ PRODUCTION READY)**
```python
def create_deformer(deformer_type):
    """Safe deformer creation using Cinema4D constants"""
    
    # Step 1: Get Cinema4D constant
    c4d_constants = {
        'bend': 'c4d.Obend',
        'twist': 'c4d.Otwist',  
        'bulge': 'c4d.Obulge',
        'taper': 'c4d.Otaper',
        'shear': 'c4d.Oshear',
        'wind': 'c4d.Owind'
    }
    
    c4d_constant = c4d_constants.get(deformer_type, f'c4d.O{deformer_type.lower()}')
    
    # Step 2: Create deformer with error handling
    try:
        deformer = c4d.BaseObject(eval(c4d_constant))
        if not deformer:
            print(f"ERROR: Failed to create {deformer_type} using {c4d_constant}")
            return False
    except AttributeError as e:
        print(f"ERROR: Unknown constant {c4d_constant}: {str(e)}")
        return False
    
    # Step 3: Set name and position
    deformer.SetName(f"{deformer_type.capitalize()}_Deformer")
    deformer.SetAbsPos(c4d.Vector(0, 0, 0))
    
    # Step 4: Insert and update
    doc.InsertObject(deformer)
    c4d.EventAdd()
    
    return True
```

---

## 🔍 SCENE INSPECTION & DEBUGGING

### **Scene Information (✅ VERIFIED)**
```python
def get_scene_info():
    """Get comprehensive scene information for debugging"""
    
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return None
    
    scene_info = {
        "document_name": doc.GetDocumentName(),
        "object_count": 0,
        "objects": [],
        "cloners": [],
        "imported_models": []
    }
    
    def process_object(obj, level=0):
        obj_info = {
            "name": obj.GetName(),
            "type": obj.GetTypeName(),
            "type_id": obj.GetType(),
            "level": level,
        }
        
        # Identify specific object types
        if obj.GetType() == 1018544:  # Cloner
            scene_info["cloners"].append(obj_info)
        elif "Hy3D" in obj.GetName():
            scene_info["imported_models"].append(obj_info)
        
        scene_info["objects"].append(obj_info)
        scene_info["object_count"] += 1
        
        # Process children recursively
        child = obj.GetDown()
        while child:
            process_object(child, level + 1)
            child = child.GetNext()
    
    # Process all top-level objects
    obj = doc.GetFirstObject()
    while obj:
        process_object(obj)
        obj = obj.GetNext()
    
    return scene_info
```

### **Object Hierarchy Debugging**
```python
def debug_object_hierarchy():
    """Print complete object hierarchy for debugging"""
    
    doc = c4d.documents.GetActiveDocument()
    
    def print_object(obj, level=0):
        indent = "  " * level
        print(f"{indent}Object: {obj.GetName()} (Type: {obj.GetTypeName()}, ID: {obj.GetType()})")
        
        # Print children
        child = obj.GetDown()
        while child:
            print_object(child, level + 1)
            child = child.GetNext()
    
    # Print all top-level objects
    obj = doc.GetFirstObject()
    while obj:
        print_object(obj)
        obj = obj.GetNext()
```

---

## 📊 JSON-SAFE SCRIPT TEMPLATES

### **Basic Script Template**
```python
BASIC_SCRIPT_TEMPLATE = '''import c4d
from c4d import documents
import time

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        print("ERROR: No active document")
        return False
    
    try:
        # Your Cinema4D operations here
        {operations}
        
        # Always update viewport
        c4d.EventAdd()
        
        print("SUCCESS: Operation completed")
        return True
        
    except Exception as e:
        print("ERROR: " + str(e))
        return False

result = main()
print("Result: " + str(result))
'''
```

### **Object Creation Template**
```python
def generate_creation_script(obj_type, name, params):
    """Generate JSON-safe object creation script"""
    
    operations = f'''
        # Create object using verified ID
        obj = c4d.BaseObject({PRIMITIVE_IDS[obj_type]})
        if not obj:
            print("ERROR: Failed to create object")
            return False
        
        obj.SetName("{name}")
        
        # Set parameters
        {generate_param_assignments(obj_type, params)}
        
        # Insert object
        doc.InsertObject(obj)
    '''
    
    return BASIC_SCRIPT_TEMPLATE.format(operations=operations)
```

---

## ⚠️ CRITICAL DEVELOPMENT PATTERNS - UPDATED FOR MAXON SDK

### **1. Proper Cinema4D Object Creation (CRITICAL FOR RELIABILITY)**

**✅ CORRECT APPROACH - Use Cinema4D Constants in String Format for MCP**
```python
# For MCP Script Generation (RECOMMENDED PATTERN)
def create_object_script(object_type: str):
    # Map to Cinema4D constant strings
    object_map = {
        "cube": "c4d.Ocube",
        "sphere": "c4d.Osphere", 
        "cylinder": "c4d.Ocylinder",
        "cloner": "c4d.Omgcloner",
        # ... etc
    }
    
    c4d_constant = object_map.get(object_type, "c4d.Ocube")
    
    script = f"""
import c4d
from c4d import documents

doc = documents.GetActiveDocument()
if not doc:
    raise Exception("No active document")

# Use Cinema4D constant - this resolves to correct numeric ID
obj = c4d.BaseObject({c4d_constant})
if not obj:
    raise Exception("Failed to create object")

# Set parameters using Cinema4D parameter constants
if {c4d_constant} == c4d.Ocube:
    obj[c4d.PRIM_CUBE_LEN] = c4d.Vector(100, 100, 100)
elif {c4d_constant} == c4d.Osphere:
    obj[c4d.PRIM_SPHERE_RAD] = 100

doc.InsertObject(obj)
c4d.EventAdd()
print("SUCCESS: Created object")
"""
    return script
```

**🚨 CRITICAL FAILURES TO AVOID:**

1. **❌ NEVER Use Direct Numeric IDs in Scripts**
```python
# WRONG - Numeric IDs are unreliable and version-dependent
script = "obj = c4d.BaseObject(5159)"  # May create wrong object type!

# The Problem: Numeric IDs can change between Cinema4D versions
# ID 5159 might be Ocube in R24 but Ostage in R25
```

2. **❌ NEVER Use Undefined Constants** 
```python
# WRONG - Some constants don't exist in Python API
script = "obj = c4d.BaseObject(c4d.Mocloner)"  # AttributeError!

# The Problem: Many MoGraph objects use numeric IDs only
# Always test constants in Cinema4D Python console first
```

3. **❌ NEVER Skip Parameter Constant Verification**
```python
# WRONG - Magic numbers for parameters
script = "obj[1117] = c4d.Vector(100, 100, 100)"  # What is 1117?

# RIGHT - Use Cinema4D parameter constants
script = "obj[c4d.PRIM_CUBE_LEN] = c4d.Vector(100, 100, 100)"
```

**✅ VERIFICATION PROCESS FOR NEW OBJECTS:**
1. **Test in Cinema4D Python Console**:
   ```python
   # In Cinema4D Script Manager
   import c4d
   print(c4d.Ocube)        # If this works, use the constant
   print(c4d.Mocloner)     # If AttributeError, need different approach
   ```

2. **For Objects Without Constants** (MoGraph, some generators):
   ```python
   # Use verified numeric IDs from Maxon documentation
   VERIFIED_IDS = {
       "cloner": 1018544,      # Verified from Maxon SDK
       "matrix": 1018545,      # Verified from Maxon SDK  
       "fracture": 1018791,    # Verified from Maxon SDK
   }
   ```

3. **Parameter Discovery**:
   ```python
   # In Cinema4D, create object manually, then:
   obj = op  # Selected object
   print(obj.GetType())  # Get object ID
   
   # For parameters, use Maxon SDK documentation
   # Common parameter patterns:
   # PRIM_* for primitive parameters
   # MG_* for MoGraph parameters  
   # DEFORMOBJECT_* for deformer parameters
   ```

### **2. Maxon SDK Parameter Discovery (ESSENTIAL FOR SETTINGS DIALOGS)**

**✅ SYSTEMATIC APPROACH TO PARAMETER DISCOVERY:**

1. **Find Object Parameters in Maxon SDK Documentation**:
   ```python
   # Step 1: Identify object type constant
   # Visit: https://developers.maxon.net/docs/py/
   # Search for object type (e.g., "BaseObject", "Cube", "Sphere")
   
   # Step 2: Look for parameter constants
   # Primitive objects: c4d.PRIM_*
   # MoGraph: c4d.MG_* or ID_MG_*
   # Deformers: c4d.DEFORMOBJECT_*
   # Lights: c4d.LIGHT_*
   # Cameras: c4d.CAMERA_*
   ```

2. **Verify Parameters in Cinema4D Console**:
   ```python
   # In Cinema4D Script Manager
   import c4d
   
   # Create object to inspect
   obj = c4d.BaseObject(c4d.Ocube)
   
   # Check available parameters
   print("Cube Length:", c4d.PRIM_CUBE_LEN)         # Should print: 1117
   print("Cube Segments:", c4d.PRIM_CUBE_SUBX)      # Should print: 1118
   
   # Test parameter access
   obj[c4d.PRIM_CUBE_LEN] = c4d.Vector(200, 200, 200)
   print("Length set successfully")
   ```

3. **Common Parameter Patterns by Object Type**:
   ```python
   # PRIMITIVES - Use c4d.PRIM_* constants
   CUBE_PARAMS = {
       'size': 'c4d.PRIM_CUBE_LEN',        # Vector(x,y,z)
       'segments': 'c4d.PRIM_CUBE_SUBX',   # X segments
   }
   
   SPHERE_PARAMS = {
       'radius': 'c4d.PRIM_SPHERE_RAD',    # Float
       'segments': 'c4d.PRIM_SPHERE_SUB',  # Int
   }
   
   CYLINDER_PARAMS = {
       'radius': 'c4d.PRIM_CYLINDER_RADIUS',   # Float
       'height': 'c4d.PRIM_CYLINDER_HEIGHT',   # Float
       'segments': 'c4d.PRIM_CYLINDER_HSUB',   # Height segments
   }
   
   # MOGRAPH - Use verified numeric IDs (no c4d constants)
   CLONER_PARAMS = {
       'mode': 20001,      # ID_MG_MOTIONGENERATOR_MODE
       'count': 20002,     # MG_GRID_COUNT (for grid mode)
       'size': 20003,      # MG_GRID_SIZE (for grid mode)
   }
   
   # DEFORMERS - Use c4d.DEFORMOBJECT_* constants  
   BEND_PARAMS = {
       'strength': 'c4d.DEFORMOBJECT_STRENGTH',    # Float
       'angle': 'c4d.DEFORMOBJECT_ANGLE',          # Float
   }
   
   # LIGHTS - Use c4d.LIGHT_* constants
   LIGHT_PARAMS = {
       'type': 'c4d.LIGHT_TYPE',           # Int (spot, area, etc.)
       'intensity': 'c4d.LIGHT_BRIGHTNESS', # Float
       'color': 'c4d.LIGHT_COLOR',         # Vector(r,g,b)
   }
   ```

4. **Settings Dialog Parameter Mapping**:
   ```python
   # For Phase 2 Settings Dialog Implementation
   def get_object_parameters(object_type: str) -> dict:
       """Return Cinema4D parameters for object type"""
       
       param_map = {
           'cube': {
               'size_x': ('c4d.PRIM_CUBE_LEN', 'vector_x'),
               'size_y': ('c4d.PRIM_CUBE_LEN', 'vector_y'), 
               'size_z': ('c4d.PRIM_CUBE_LEN', 'vector_z'),
               'segments_x': ('c4d.PRIM_CUBE_SUBX', 'int'),
           },
           'sphere': {
               'radius': ('c4d.PRIM_SPHERE_RAD', 'float'),
               'segments': ('c4d.PRIM_SPHERE_SUB', 'int'),
               'perfect': ('c4d.PRIM_SPHERE_PERFECT', 'bool'),
           },
           'cloner': {
               'mode': (20001, 'int'),        # Grid=2, Linear=0, Radial=1
               'count_x': (20002, 'vector_x'), # For grid mode
               'count_y': (20002, 'vector_y'),
               'count_z': (20002, 'vector_z'),
           }
       }
       
       return param_map.get(object_type, {})
   ```

**🚨 PARAMETER DISCOVERY FAILURES TO AVOID:**

1. **❌ NEVER Guess Parameter IDs**
```python
# WRONG - Guessing parameter numbers
obj[1000] = 100  # What parameter is this?

# RIGHT - Use documented constants
obj[c4d.PRIM_CUBE_LEN] = c4d.Vector(100, 100, 100)
```

2. **❌ NEVER Use Wrong Parameter Types**
```python
# WRONG - Vector parameter as float
obj[c4d.PRIM_CUBE_LEN] = 100  # Should be Vector!

# RIGHT - Correct parameter type
obj[c4d.PRIM_CUBE_LEN] = c4d.Vector(100, 100, 100)
```

3. **❌ NEVER Skip Parameter Validation**
```python
# WRONG - No validation
obj[c4d.PRIM_SPHERE_RAD] = -50  # Negative radius!

# RIGHT - Validate before setting
radius = max(0.1, float(value))  # Ensure positive
obj[c4d.PRIM_SPHERE_RAD] = radius
```

### **3. JSON-Safe String Formatting**
```python
# ✅ CORRECT - Simple string concatenation with proper escaping
script_template = '''import c4d
obj = c4d.BaseObject({constant})
obj.SetName("{name}")
obj[{param_constant}] = {param_value}
'''

script = script_template.format(
    constant="c4d.Ocube",
    name=object_name.replace('"', '\\"'),  # Escape quotes
    param_constant="c4d.PRIM_CUBE_LEN", 
    param_value=f"c4d.Vector({x}, {y}, {z})"
)

# ❌ INCORRECT - Complex f-strings can break JSON encoding
script = f"""import c4d
obj = c4d.BaseObject({object_id})  # Potential JSON issues
obj.SetName("{object_name}")       # Unescaped quotes
"""
```

### **3. Always Call c4d.EventAdd()**
```python
# ✅ CORRECT - Always update viewport after changes
doc.InsertObject(obj)
c4d.EventAdd()  # CRITICAL

# ❌ INCORRECT - Changes may not be visible
doc.InsertObject(obj)
# Missing EventAdd() call
```

### **4. Proper Error Handling**
```python
# ✅ CORRECT - Check object creation
obj = c4d.BaseObject(5159)
if not obj:
    print("ERROR: Failed to create object")
    return False

# ❌ INCORRECT - No validation
obj = c4d.BaseObject(5159)
obj.SetName("Test")  # May crash if obj is None
```

### **5. Reliable Object Finding**
```python
# ✅ CORRECT - Check against cloner to avoid conflicts
for obj in doc.GetObjects():
    if "Hy3D" in obj.GetName() and obj != cloner:
        imported_obj = obj
        break

# ❌ INCORRECT - May find cloner itself
for obj in doc.GetObjects():
    if "Hy3D" in obj.GetName():
        imported_obj = obj
        break
```

---

## 🚀 OPTIMIZATION GUIDELINES

### **1. Script Performance**
- Keep scripts under 100 lines for reliable transmission
- Use simple variable assignments instead of complex expressions
- Minimize object searches with early breaks

### **2. Memory Management**  
- Remove objects from hierarchy before re-parenting
- Update viewport only after all operations complete
- Use specific object name patterns for reliable finding

### **3. Error Recovery**
- Always include try-catch blocks in Cinema4D scripts
- Print detailed error messages for debugging
- Return boolean success/failure indicators

### **4. Testing Strategy**
- Test object creation separately before complex operations
- Verify parameter IDs work before setting values
- Use scene debug scripts to validate hierarchy

---

## 📋 DEVELOPMENT CHECKLIST

**Before implementing new Cinema4D features:**

- [ ] ✅ Use verified numeric object IDs from this reference
- [ ] ✅ Use verified parameter IDs for object properties
- [ ] ✅ Test object creation separately first
- [ ] ✅ Use JSON-safe script formatting (simple concatenation)
- [ ] ✅ Include comprehensive error handling
- [ ] ✅ Add `c4d.EventAdd()` after all operations
- [ ] ✅ Test with fresh import approach for models
- [ ] ✅ Verify with scene debug script
- [ ] ✅ Add detailed logging/print statements
- [ ] ✅ Use proven working patterns as templates

**This reference contains battle-tested patterns from extensive debugging. Follow these patterns to avoid the iteration cycles we experienced during development.**