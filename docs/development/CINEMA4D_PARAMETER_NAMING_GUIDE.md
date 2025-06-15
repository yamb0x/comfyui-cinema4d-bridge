# Cinema4D Parameter Naming Guide - CRITICAL FOR OBJECT CREATION

## 🚨 CRITICAL LESSON LEARNED (2025-01-10)

### The Problem We Just Fixed
When creating cylinder, cone, and torus primitives, the buttons stopped working due to **incorrect parameter constant names**. The root cause was **assuming parameter names** instead of verifying them against Cinema4D's actual API.

### What Went Wrong
```python
# ❌ INCORRECT - These caused AttributeError
obj[c4d.PRIM_CYLINDER_SUB]    # Does not exist
obj[c4d.PRIM_CONE_SUB]         # Does not exist  
obj[c4d.PRIM_TORUS_HSUB]       # Does not exist
obj[c4d.PRIM_TORUS_VSUB]       # Does not exist

# ✅ CORRECT - These are the actual constants
obj[c4d.PRIM_CYLINDER_SEG]     # Segments for cylinder
obj[c4d.PRIM_CONE_SEG]         # Segments for cone
obj[c4d.PRIM_TORUS_SEG]        # Ring segments for torus
obj[c4d.PRIM_TORUS_CSUB]       # Cross-section segments for torus
```

---

## 📋 Cinema4D Parameter Naming Conventions

### 1. **Abbreviation Pattern**
Cinema4D uses **abbreviated parameter names**, not full words:

| Full Word | Cinema4D Abbreviation | Example |
|-----------|----------------------|---------|
| RADIUS | RAD | `PRIM_SPHERE_RAD` |
| LENGTH | LEN | `PRIM_CUBE_LEN` |
| SEGMENTS | SEG or SUB | `PRIM_CYLINDER_SEG` |
| SUBDIVISIONS | SUB | `PRIM_SPHERE_SUB` |
| WIDTH | W | `PRIM_PLANE_SUBW` |
| HEIGHT | H | `PRIM_PLANE_SUBH` |

### 2. **Parameter Naming Structure**
```
PRIM_{OBJECT}_{PROPERTY}
```
- `PRIM` = Primitive prefix
- `{OBJECT}` = Object type (SPHERE, CUBE, etc.)
- `{PROPERTY}` = Property abbreviation (RAD, LEN, SEG, etc.)

---

## 🔍 How to Find Correct Parameter Names

### Method 1: Cinema4D Python Console (RECOMMENDED)
```python
import c4d

# Create object and inspect its parameters
obj = c4d.BaseObject(c4d.Otorus)

# List all parameters
for bc_id, bc_value in obj.GetData():
    for attr in dir(c4d):
        if attr.startswith("PRIM_TORUS_") and getattr(c4d, attr) == bc_id:
            print(f"{attr} = {bc_value}")
```

### Method 2: Check Working Examples
Look in `src/c4d/mcp_wrapper.py` for the parameter mappings:
```python
# From lines 1064-1087
'segments': 'c4d.PRIM_SPHERE_SEG',      # Sphere segments
'segments': 'c4d.PRIM_CYLINDER_SEG',    # Cylinder segments  
'cap_segments': 'c4d.PRIM_CONE_SEG',    # Cone segments
'ring_segments': 'c4d.PRIM_TORUS_SEG',  # Torus ring segments
'pipe_segments': 'c4d.PRIM_TORUS_CSEG', # Torus cross-section
```

### Method 3: Test Before Implementation
```python
# Always test parameter existence first
try:
    test = c4d.PRIM_CYLINDER_SEG
    print("Parameter exists!")
except AttributeError:
    print("Parameter does not exist - check the name")
```

---

## ✅ Verified Primitive Parameters

### **Cube**
```python
obj[c4d.PRIM_CUBE_LEN] = c4d.Vector(x, y, z)  # Size vector
obj[c4d.PRIM_CUBE_SEP] = bool                  # Separate surfaces
obj[c4d.PRIM_CUBE_DOFILLET] = bool            # Enable fillet
obj[c4d.PRIM_CUBE_FRAD] = float               # Fillet radius
obj[c4d.PRIM_CUBE_SUBX] = int                 # X subdivisions
obj[c4d.PRIM_CUBE_SUBY] = int                 # Y subdivisions  
obj[c4d.PRIM_CUBE_SUBZ] = int                 # Z subdivisions
```

### **Sphere**
```python
obj[c4d.PRIM_SPHERE_RAD] = float              # Radius (NOT RADIUS!)
obj[c4d.PRIM_SPHERE_SUB] = int                # Segments
obj[c4d.PRIM_SPHERE_TYPE] = int               # 0=Standard, 4=Hemisphere
obj[c4d.PRIM_SPHERE_PERFECT] = bool           # Perfect sphere rendering
```

### **Cylinder**
```python
obj[c4d.PRIM_CYLINDER_RADIUS] = float         # Radius
obj[c4d.PRIM_CYLINDER_HEIGHT] = float         # Height
obj[c4d.PRIM_CYLINDER_SEG] = int              # Rotation segments (NOT SUB!)
obj[c4d.PRIM_CYLINDER_HSUB] = int             # Height segments
obj[c4d.PRIM_CYLINDER_CAPS] = bool            # Top/bottom caps
obj[c4d.PRIM_CYLINDER_FILLET] = bool          # Enable fillet
obj[c4d.PRIM_CYLINDER_FILLETRADIUS] = float   # Fillet radius
```

### **Cone**
```python
obj[c4d.PRIM_CONE_BRAD] = float               # Bottom radius (NOT RADIUS!)
obj[c4d.PRIM_CONE_TRAD] = float               # Top radius
obj[c4d.PRIM_CONE_HEIGHT] = float             # Height
obj[c4d.PRIM_CONE_SEG] = int                  # Segments (NOT SUB!)
obj[c4d.PRIM_CONE_HSUB] = int                 # Height segments
```

### **Torus**
```python
obj[c4d.PRIM_TORUS_OUTERRAD] = float          # Ring radius
obj[c4d.PRIM_TORUS_INNERRAD] = float          # Pipe radius
obj[c4d.PRIM_TORUS_SEG] = int                 # Ring segments (NOT HSUB!)
obj[c4d.PRIM_TORUS_CSUB] = int                # Pipe segments (NOT VSUB!)
obj[c4d.PRIM_TORUS_USE_NEW_VERSION] = bool    # Use new algorithm
```

### **Plane**
```python
obj[c4d.PRIM_PLANE_WIDTH] = float             # Width
obj[c4d.PRIM_PLANE_HEIGHT] = float            # Height  
obj[c4d.PRIM_PLANE_SUBW] = int                # Width segments
obj[c4d.PRIM_PLANE_SUBH] = int                # Height segments
```

### **Disc**
```python
obj[c4d.PRIM_DISC_ORAD] = float               # Outer radius
obj[c4d.PRIM_DISC_IRAD] = float               # Inner radius
obj[c4d.PRIM_DISC_SUB] = int                  # Segments
```

---

## 🎯 Best Practices for Future Object Creation

### 1. **NEVER Guess Parameter Names**
```python
# ❌ BAD - Guessing based on pattern
obj[c4d.PRIM_PYRAMID_RADIUS]  # Might not exist!

# ✅ GOOD - Verify first
# Check in Cinema4D console or mcp_wrapper.py
```

### 2. **Use the Reference Files**
- Primary reference: `docs/development/CINEMA4D_API_REFERENCE.md`
- Parameter mappings: `src/c4d/mcp_wrapper.py` (lines 1064-1087)
- Working examples: Test files that successfully create objects

### 3. **Test in Isolation First**
Before adding to the UI, test object creation:
```python
# Create a simple test script
script = '''
import c4d
obj = c4d.BaseObject(c4d.Opyramid)
# Test parameter
obj[c4d.PRIM_PYRAMID_LEN] = c4d.Vector(200, 200, 200)
doc.InsertObject(obj)
c4d.EventAdd()
print("SUCCESS")
'''
result = await client.execute_python(script)
```

### 4. **Document New Discoveries**
When you find a new parameter:
1. Add it to `CINEMA4D_API_REFERENCE.md`
2. Update parameter mappings in `mcp_wrapper.py`
3. Add to this guide if it's a common pattern

---

## 🚀 Next Steps for Object Creation

When implementing new object types (deformers, generators, etc.):

1. **Research Phase**
   - Check existing mappings in `mcp_wrapper.py`
   - Look for patterns in working objects
   - Test parameter names in Cinema4D console

2. **Implementation Phase**
   - Start with a minimal test script
   - Verify each parameter works
   - Add proper error handling

3. **Integration Phase**
   - Add to UI only after parameters are verified
   - Include debug logging like we did for primitives
   - Test all parameter combinations

---

## 📝 Key Takeaway

The error we fixed today teaches us: **Cinema4D's API uses specific abbreviated parameter names that must be discovered, not assumed**. When in doubt, always verify in Cinema4D's Python console or check existing working code.

This systematic approach will prevent similar issues as we implement more complex objects like deformers, generators, and MoGraph objects.