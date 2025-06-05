"""
Intelligent Object Scattering for Cinema4D
Places objects from 3D/Hy3D/ with smart distribution
"""

import c4d
import random
import math
from c4d import documents, BaseObject, Vector

# Target objects to scatter (will be replaced by the app)
TARGET_OBJECTS = []

def create_scatter_system(doc, objects, count=100, radius=1000, height_variation=200):
    """Create intelligent scatter system"""
    
    # Create null to hold scattered objects
    scatter_null = BaseObject(c4d.Onull)
    scatter_null.SetName("Scattered Objects")
    doc.InsertObject(scatter_null)
    
    # Scatter parameters
    golden_angle = 137.5  # Golden angle for natural distribution
    
    for i in range(count):
        # Select random object from list
        if not objects:
            continue
            
        obj_name = random.choice(objects)
        obj = doc.SearchObject(obj_name)
        
        if not obj:
            continue
        
        # Clone object
        clone = obj.GetClone()
        
        # Calculate position using Fibonacci spiral
        angle = math.radians(i * golden_angle)
        distance = math.sqrt(i) * (radius / math.sqrt(count))
        
        x = distance * math.cos(angle)
        z = distance * math.sin(angle)
        y = random.uniform(-height_variation/2, height_variation/2)
        
        # Add some randomness
        x += random.uniform(-50, 50)
        z += random.uniform(-50, 50)
        
        # Set position
        clone.SetAbsPos(Vector(x, y, z))
        
        # Random rotation
        rot_y = random.uniform(0, math.pi * 2)
        clone.SetAbsRot(Vector(0, rot_y, 0))
        
        # Random scale variation
        scale = random.uniform(0.7, 1.3)
        clone.SetAbsScale(Vector(scale, scale, scale))
        
        # Insert under scatter null
        clone.InsertUnder(scatter_null)
    
    # Add dynamics tag to scatter null
    dynamics_tag = scatter_null.MakeTag(c4d.Tcollider)
    dynamics_tag[c4d.COLLIDER_MODE] = c4d.COLLIDER_MODE_STATIC
    
    return scatter_null

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Get target objects
    objects = TARGET_OBJECTS
    if not objects:
        # If no targets specified, get all objects starting with "Hy3D"
        objects = []
        obj = doc.GetFirstObject()
        while obj:
            if obj.GetName().startswith("Hy3D"):
                objects.append(obj.GetName())
            obj = obj.GetNext()
    
    if not objects:
        print("No objects found to scatter")
        return False
    
    # Create scatter system
    scatter_null = create_scatter_system(
        doc, 
        objects,
        count=150,
        radius=2000,
        height_variation=100
    )
    
    # Update scene
    c4d.EventAdd()
    
    print(f"Created scatter system with {len(objects)} object types")
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")