"""
Smart Material Assignment for Cinema4D
Automatically assigns materials based on object names and properties
"""

import c4d
from c4d import documents, BaseObject, BaseMaterial, Vector
import re

# Target objects (will be replaced by the app)
TARGET_OBJECTS = []

def create_material_library(doc):
    """Create a library of smart materials"""
    materials = {}
    
    # 1. Glass Material
    glass = BaseMaterial(c4d.Mmaterial)
    glass.SetName("Smart Glass")
    glass[c4d.MATERIAL_USE_COLOR] = False
    glass[c4d.MATERIAL_USE_TRANSPARENCY] = True
    glass[c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS] = 0.95
    glass[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.52
    glass[c4d.MATERIAL_USE_REFLECTION] = True
    glass[c4d.MATERIAL_REFLECTION_BRIGHTNESS] = 1.0
    glass[c4d.MATERIAL_USE_SPECULAR] = True
    doc.InsertMaterial(glass)
    materials['glass'] = glass
    
    # 2. Metal Material
    metal = BaseMaterial(c4d.Mmaterial)
    metal.SetName("Smart Metal")
    metal[c4d.MATERIAL_COLOR_COLOR] = Vector(0.7, 0.7, 0.8)
    metal[c4d.MATERIAL_USE_REFLECTION] = True
    metal[c4d.MATERIAL_REFLECTION_BRIGHTNESS] = 0.9
    metal[c4d.MATERIAL_USE_SPECULAR] = True
    metal[c4d.MATERIAL_SPECULAR_WIDTH] = 0.2
    metal[c4d.MATERIAL_USE_BUMP] = True
    
    # Add noise to bump
    noise = c4d.BaseShader(c4d.Xnoise)
    noise[c4d.SLA_NOISE_SCALE] = 0.01
    metal.InsertShader(noise)
    metal[c4d.MATERIAL_BUMP_SHADER] = noise
    metal[c4d.MATERIAL_BUMP_STRENGTH] = 0.1
    
    doc.InsertMaterial(metal)
    materials['metal'] = metal
    
    # 3. Organic Material
    organic = BaseMaterial(c4d.Mmaterial)
    organic.SetName("Smart Organic")
    organic[c4d.MATERIAL_COLOR_COLOR] = Vector(0.6, 0.8, 0.5)
    organic[c4d.MATERIAL_USE_DIFFUSION] = True
    organic[c4d.MATERIAL_DIFFUSION_BRIGHTNESS] = 0.8
    organic[c4d.MATERIAL_USE_SPECULAR] = True
    organic[c4d.MATERIAL_SPECULAR_WIDTH] = 0.6
    organic[c4d.MATERIAL_SPECULAR_HEIGHT] = 0.3
    
    # Add subsurface scattering effect
    organic[c4d.MATERIAL_USE_LUMINANCE] = True
    organic[c4d.MATERIAL_LUMINANCE_COLOR] = Vector(0.9, 0.7, 0.6)
    organic[c4d.MATERIAL_LUMINANCE_BRIGHTNESS] = 0.1
    
    doc.InsertMaterial(organic)
    materials['organic'] = organic
    
    # 4. Plastic Material
    plastic = BaseMaterial(c4d.Mmaterial)
    plastic.SetName("Smart Plastic")
    plastic[c4d.MATERIAL_COLOR_COLOR] = Vector(0.9, 0.3, 0.2)
    plastic[c4d.MATERIAL_USE_SPECULAR] = True
    plastic[c4d.MATERIAL_SPECULAR_WIDTH] = 0.4
    plastic[c4d.MATERIAL_SPECULAR_HEIGHT] = 0.7
    plastic[c4d.MATERIAL_USE_REFLECTION] = True
    plastic[c4d.MATERIAL_REFLECTION_BRIGHTNESS] = 0.2
    
    doc.InsertMaterial(plastic)
    materials['plastic'] = plastic
    
    # 5. Stone Material
    stone = BaseMaterial(c4d.Mmaterial)
    stone.SetName("Smart Stone")
    stone[c4d.MATERIAL_COLOR_COLOR] = Vector(0.6, 0.6, 0.55)
    stone[c4d.MATERIAL_USE_DIFFUSION] = True
    stone[c4d.MATERIAL_USE_BUMP] = True
    
    # Add rock texture
    noise = c4d.BaseShader(c4d.Xnoise)
    noise[c4d.SLA_NOISE_SCALE] = 0.2
    noise[c4d.SLA_NOISE_OCTAVES] = 5
    noise[c4d.SLA_NOISE_SEED] = 54321
    stone.InsertShader(noise)
    stone[c4d.MATERIAL_BUMP_SHADER] = noise
    stone[c4d.MATERIAL_BUMP_STRENGTH] = 0.3
    
    doc.InsertMaterial(stone)
    materials['stone'] = stone
    
    # 6. Fabric Material
    fabric = BaseMaterial(c4d.Mmaterial)
    fabric.SetName("Smart Fabric")
    fabric[c4d.MATERIAL_COLOR_COLOR] = Vector(0.8, 0.7, 0.9)
    fabric[c4d.MATERIAL_USE_DIFFUSION] = True
    fabric[c4d.MATERIAL_DIFFUSION_BRIGHTNESS] = 1.0
    fabric[c4d.MATERIAL_USE_SPECULAR] = True
    fabric[c4d.MATERIAL_SPECULAR_WIDTH] = 0.8
    fabric[c4d.MATERIAL_SPECULAR_HEIGHT] = 0.1
    
    # Add fabric pattern
    tiles = c4d.BaseShader(c4d.Xtiles)
    tiles[c4d.SLA_TILES_GROUT_WIDTH] = 0.02
    tiles[c4d.SLA_TILES_PATTERN] = c4d.SLA_TILES_PATTERN_HEXAGONS
    fabric.InsertShader(tiles)
    fabric[c4d.MATERIAL_BUMP_SHADER] = tiles
    fabric[c4d.MATERIAL_USE_BUMP] = True
    fabric[c4d.MATERIAL_BUMP_STRENGTH] = 0.05
    
    doc.InsertMaterial(fabric)
    materials['fabric'] = fabric
    
    return materials

def analyze_object_name(name):
    """Analyze object name to determine material type"""
    name_lower = name.lower()
    
    # Keywords for different materials
    material_keywords = {
        'glass': ['glass', 'crystal', 'transparent', 'window'],
        'metal': ['metal', 'steel', 'iron', 'chrome', 'aluminum'],
        'organic': ['plant', 'leaf', 'flower', 'tree', 'creature', 'skin'],
        'plastic': ['plastic', 'rubber', 'vinyl', 'polymer'],
        'stone': ['stone', 'rock', 'concrete', 'marble', 'granite'],
        'fabric': ['cloth', 'fabric', 'textile', 'cotton', 'silk']
    }
    
    # Check keywords
    for material_type, keywords in material_keywords.items():
        for keyword in keywords:
            if keyword in name_lower:
                return material_type
    
    # Default based on patterns
    if re.search(r'(sphere|cube|box|cylinder)', name_lower):
        return 'plastic'
    elif re.search(r'(creature|character|figure)', name_lower):
        return 'organic'
    
    return 'plastic'  # Default

def apply_smart_materials(doc, obj, materials):
    """Apply materials based on object analysis"""
    obj_name = obj.GetName()
    
    # Analyze object to determine material
    material_type = analyze_object_name(obj_name)
    
    # Get material
    material = materials.get(material_type)
    if not material:
        return False
    
    # Check if object already has texture tag
    texture_tag = obj.GetTag(c4d.Ttexture)
    if not texture_tag:
        texture_tag = obj.MakeTag(c4d.Ttexture)
    
    # Apply material
    texture_tag[c4d.TEXTURETAG_MATERIAL] = material
    
    # Set projection based on object type
    obj_type = obj.GetType()
    if obj_type in [c4d.Osphere, c4d.Ocapsule]:
        texture_tag[c4d.TEXTURETAG_PROJECTION] = c4d.TEXTURETAG_PROJECTION_SPHERICAL
    elif obj_type in [c4d.Ocylinder, c4d.Otube]:
        texture_tag[c4d.TEXTURETAG_PROJECTION] = c4d.TEXTURETAG_PROJECTION_CYLINDRICAL
    elif obj_type == c4d.Ocube:
        texture_tag[c4d.TEXTURETAG_PROJECTION] = c4d.TEXTURETAG_PROJECTION_CUBIC
    else:
        texture_tag[c4d.TEXTURETAG_PROJECTION] = c4d.TEXTURETAG_PROJECTION_UVW
    
    print(f"Applied {material_type} material to {obj_name}")
    return True

def create_material_override_null(doc):
    """Create null with user data for material overrides"""
    null = BaseObject(c4d.Onull)
    null.SetName("Material Override Controller")
    
    # Add user data for each material type
    material_types = ['glass', 'metal', 'organic', 'plastic', 'stone', 'fabric']
    
    for i, mat_type in enumerate(material_types):
        bc = c4d.GetCustomDatatypeDefault(c4d.DTYPE_BOOL)
        bc[c4d.DESC_NAME] = f"Force {mat_type.capitalize()}"
        null.AddUserData(bc)
    
    doc.InsertObject(null)
    return null

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Create material library
    materials = create_material_library(doc)
    
    # Create override controller
    controller = create_material_override_null(doc)
    
    # Get target objects
    objects_to_process = []
    
    if TARGET_OBJECTS:
        # Use specified targets
        for obj_name in TARGET_OBJECTS:
            obj = doc.SearchObject(obj_name)
            if obj:
                objects_to_process.append(obj)
    else:
        # Process all polygon objects
        def collect_objects(obj):
            while obj:
                if obj.GetType() == c4d.Opolygon or obj.GetName().startswith("Hy3D"):
                    objects_to_process.append(obj)
                collect_objects(obj.GetDown())
                obj = obj.GetNext()
        
        collect_objects(doc.GetFirstObject())
    
    # Apply smart materials
    processed = 0
    for obj in objects_to_process:
        if apply_smart_materials(doc, obj, materials):
            processed += 1
    
    # Update scene
    c4d.EventAdd()
    
    print(f"Smart materials applied to {processed} objects")
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")