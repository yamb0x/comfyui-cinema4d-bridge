"""
Organic Growth System for Cinema4D
Apply organic growth animation to imported meshes
"""

import c4d
from c4d import documents, BaseObject, BaseTag, Vector
import math

# Target objects (will be replaced by the app)
TARGET_OBJECTS = []

def create_organic_growth(doc, obj):
    """Apply organic growth system to object"""
    
    # Create pose morph tag
    pose_tag = obj.MakeTag(c4d.Tposemorph)
    pose_tag.ExitEditMode()
    
    # Add morph target
    pose_tag.AddMorph()
    morph = pose_tag.GetMorph(0)
    morph.SetName("Growth")
    
    # Create deformers for organic effect
    
    # 1. Displacer for organic movement
    displacer = BaseObject(c4d.Odisplace)
    displacer.SetName("Organic Displacer")
    displacer[c4d.DISPLACE_STRENGTH] = Vector(50, 50, 50)
    displacer.InsertUnder(obj)
    
    # Add noise shader
    noise_shader = c4d.BaseShader(c4d.Xnoise)
    noise_shader[c4d.SLA_NOISE_SEED] = 12345
    noise_shader[c4d.SLA_NOISE_SCALE] = 0.2
    noise_shader[c4d.SLA_NOISE_ANIMATION_SPEED] = 0.5
    noise_shader[c4d.SLA_NOISE_OCTAVES] = 3
    
    displacer.InsertShader(noise_shader)
    displacer[c4d.DISPLACE_SHADING_SHADER] = noise_shader
    
    # 2. Jiggle deformer for secondary motion
    jiggle = BaseObject(c4d.Ojiggle)
    jiggle.SetName("Organic Jiggle")
    jiggle[c4d.JIGGLE_SPRING] = 30
    jiggle[c4d.JIGGLE_DRAG] = 10
    jiggle[c4d.JIGGLE_STRUCTURAL] = 0.5
    jiggle[c4d.JIGGLE_STRUCTURAL_DRAG] = 20
    jiggle.InsertUnder(obj)
    
    # 3. Spherical field for growth control
    field = BaseObject(c4d.Ospherefield)
    field.SetName("Growth Field")
    field[c4d.PRIM_SPHERE_RAD] = 100
    field[c4d.FIELD_INNER_OFFSET] = 0.8
    
    # Animate field size for growth effect
    track = field.MakeTrack(c4d.Ospherefield, c4d.PRIM_SPHERE_RAD)
    curve = track.GetCurve()
    
    # Add keyframes
    key1 = curve.AddKey(c4d.BaseTime(0))
    key1.SetValue(curve, 10)
    
    key2 = curve.AddKey(c4d.BaseTime(2))
    key2.SetValue(curve, 500)
    
    # Set interpolation
    key1.SetInterpolation(curve, c4d.CINTERPOLATION_SPLINE)
    key2.SetInterpolation(curve, c4d.CINTERPOLATION_SPLINE)
    
    doc.InsertObject(field)
    
    # Link field to displacer
    displacer[c4d.FIELDS] = c4d.InExcludeData()
    displacer[c4d.FIELDS].InsertObject(field, 0)
    
    return True

def add_growth_controller(doc, objects):
    """Add growth controller null"""
    
    controller = BaseObject(c4d.Onull)
    controller.SetName("Growth Controller")
    doc.InsertObject(controller)
    
    # Add user data for control
    bc = c4d.GetCustomDatatypeDefault(c4d.DTYPE_REAL)
    bc[c4d.DESC_NAME] = "Growth Amount"
    bc[c4d.DESC_MIN] = 0
    bc[c4d.DESC_MAX] = 100
    bc[c4d.DESC_STEP] = 1
    bc[c4d.DESC_UNIT] = c4d.DESC_UNIT_PERCENT
    controller.AddUserData(bc)
    
    # Animate growth
    track = controller.MakeTrack(c4d.ID_USERDATA, 1)
    curve = track.GetCurve()
    
    key1 = curve.AddKey(c4d.BaseTime(0))
    key1.SetValue(curve, 0)
    
    key2 = curve.AddKey(c4d.BaseTime(3))
    key2.SetValue(curve, 100)
    
    return controller

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Get target objects
    objects = TARGET_OBJECTS
    if not objects:
        # Get selected objects
        objects = []
        obj = doc.GetFirstObject()
        while obj:
            if obj.GetBit(c4d.BIT_ACTIVE):
                objects.append(obj.GetName())
            obj = obj.GetNext()
    
    if not objects:
        print("No objects selected")
        return False
    
    # Create growth controller
    controller = add_growth_controller(doc, objects)
    
    # Apply organic growth to each object
    for obj_name in objects:
        obj = doc.SearchObject(obj_name)
        if obj:
            create_organic_growth(doc, obj)
            print(f"Applied organic growth to {obj_name}")
    
    # Update scene
    c4d.EventAdd()
    
    print(f"Organic growth system applied to {len(objects)} objects")
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")