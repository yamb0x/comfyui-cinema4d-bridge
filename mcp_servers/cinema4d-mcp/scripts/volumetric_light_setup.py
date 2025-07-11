"""
Volumetric Light Setup for Cinema4D
Creates atmospheric lighting for the scene
"""

import c4d
from c4d import documents, BaseObject, Vector
import math

def create_volumetric_lighting(doc):
    """Create volumetric lighting setup"""
    
    # Create environment object
    environment = BaseObject(c4d.Oenvironment)
    environment.SetName("Volumetric Environment")
    doc.InsertObject(environment)
    
    # Enable volumetric lighting
    environment[c4d.ENVIRONMENT_VOLUMETRIC] = True
    environment[c4d.ENVIRONMENT_VOLUMETRIC_DENSITY] = 0.02
    environment[c4d.ENVIRONMENT_VOLUMETRIC_COLOR] = Vector(0.8, 0.9, 1.0)
    environment[c4d.ENVIRONMENT_VOLUMETRIC_BRIGHTNESS] = 0.5
    
    # Create main light sources
    lights = []
    
    # 1. Key light (warm)
    key_light = BaseObject(c4d.Olight)
    key_light.SetName("Key Light")
    key_light[c4d.LIGHT_TYPE] = c4d.LIGHT_TYPE_SPOT
    key_light[c4d.LIGHT_COLOR] = Vector(1.0, 0.95, 0.8)
    key_light[c4d.LIGHT_BRIGHTNESS] = 150
    key_light[c4d.LIGHT_DETAILS_OUTERANGLE] = math.radians(60)
    key_light[c4d.LIGHT_DETAILS_INNERANGLE] = math.radians(50)
    key_light[c4d.LIGHT_VISIBILITY_VOLUMETRIC] = True
    key_light[c4d.LIGHT_VISIBILITY_VISIBLE] = True
    key_light.SetAbsPos(Vector(500, 800, -500))
    
    # Create target
    target = BaseObject(c4d.Onull)
    target.SetName("Key Light Target")
    doc.InsertObject(target)
    
    # Add target tag
    target_tag = key_light.MakeTag(c4d.Ttargetexpression)
    target_tag[c4d.TARGETEXPRESSIONTAG_LINK] = target
    
    doc.InsertObject(key_light)
    lights.append(key_light)
    
    # 2. Fill light (cool)
    fill_light = BaseObject(c4d.Olight)
    fill_light.SetName("Fill Light")
    fill_light[c4d.LIGHT_TYPE] = c4d.LIGHT_TYPE_AREA
    fill_light[c4d.LIGHT_AREADETAILS_SHAPE] = c4d.LIGHT_AREADETAILS_SHAPE_RECTANGLE
    fill_light[c4d.LIGHT_AREADETAILS_SIZEX] = 400
    fill_light[c4d.LIGHT_AREADETAILS_SIZEY] = 600
    fill_light[c4d.LIGHT_COLOR] = Vector(0.7, 0.8, 1.0)
    fill_light[c4d.LIGHT_BRIGHTNESS] = 50
    fill_light.SetAbsPos(Vector(-800, 400, 300))
    fill_light.SetAbsRot(Vector(0, math.radians(45), 0))
    doc.InsertObject(fill_light)
    lights.append(fill_light)
    
    # 3. Rim light
    rim_light = BaseObject(c4d.Olight)
    rim_light.SetName("Rim Light")
    rim_light[c4d.LIGHT_TYPE] = c4d.LIGHT_TYPE_SPOT
    rim_light[c4d.LIGHT_COLOR] = Vector(0.9, 0.9, 1.0)
    rim_light[c4d.LIGHT_BRIGHTNESS] = 200
    rim_light[c4d.LIGHT_DETAILS_OUTERANGLE] = math.radians(45)
    rim_light[c4d.LIGHT_VISIBILITY_VOLUMETRIC] = True
    rim_light.SetAbsPos(Vector(0, 600, 800))
    
    # Add rim light target
    rim_target_tag = rim_light.MakeTag(c4d.Ttargetexpression)
    rim_target_tag[c4d.TARGETEXPRESSIONTAG_LINK] = target
    
    doc.InsertObject(rim_light)
    lights.append(rim_light)
    
    # Create light group
    light_group = BaseObject(c4d.Onull)
    light_group.SetName("Volumetric Lights")
    doc.InsertObject(light_group)
    
    # Move lights under group
    for light in lights:
        light.Remove()
        light.InsertUnder(light_group)
    
    # Add atmosphere effects
    
    # Fog
    fog = BaseObject(c4d.Ofog)
    fog.SetName("Atmospheric Fog")
    fog[c4d.FOG_DISTANCE] = 5000
    fog[c4d.FOG_COLOR] = Vector(0.8, 0.85, 0.9)
    fog[c4d.FOG_DENSITY] = 0.3
    doc.InsertObject(fog)
    
    # Create gobo (light pattern) for key light
    gobo_material = c4d.BaseMaterial(c4d.Mmaterial)
    gobo_material.SetName("Gobo Pattern")
    
    # Add noise shader for gobo
    noise = c4d.BaseShader(c4d.Xnoise)
    noise[c4d.SLA_NOISE_SCALE] = 0.5
    noise[c4d.SLA_NOISE_OCTAVES] = 2
    gobo_material.InsertShader(noise)
    gobo_material[c4d.MATERIAL_LUMINANCE_SHADER] = noise
    
    doc.InsertMaterial(gobo_material)
    
    # Apply gobo to key light
    key_light[c4d.LIGHT_DETAILS_TEXENABLED] = True
    key_light[c4d.LIGHT_DETAILS_TEX] = gobo_material
    
    return True

def add_god_rays(doc):
    """Add god ray effects"""
    
    # Create cylinder for visible light beams
    light_beam = BaseObject(c4d.Ocylinder)
    light_beam.SetName("God Ray Beam")
    light_beam[c4d.PRIM_CYLINDER_RADIUS] = 100
    light_beam[c4d.PRIM_CYLINDER_HEIGHT] = 1000
    light_beam.SetAbsPos(Vector(0, 500, 0))
    light_beam.SetAbsRot(Vector(math.radians(90), 0, 0))
    
    # Create material for god rays
    ray_mat = c4d.BaseMaterial(c4d.Mmaterial)
    ray_mat.SetName("God Ray Material")
    ray_mat[c4d.MATERIAL_USE_COLOR] = False
    ray_mat[c4d.MATERIAL_USE_LUMINANCE] = True
    ray_mat[c4d.MATERIAL_LUMINANCE_COLOR] = Vector(1.0, 0.95, 0.8)
    ray_mat[c4d.MATERIAL_LUMINANCE_BRIGHTNESS] = 50
    ray_mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
    ray_mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = Vector(1, 1, 1)
    ray_mat[c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS] = 0.9
    
    # Add gradient for falloff
    gradient = c4d.BaseShader(c4d.Xgradient)
    gradient[c4d.SLA_GRADIENT_TYPE] = c4d.SLA_GRADIENT_TYPE_2D_CIRCULAR
    ray_mat.InsertShader(gradient)
    ray_mat[c4d.MATERIAL_TRANSPARENCY_SHADER] = gradient
    
    doc.InsertMaterial(ray_mat)
    doc.InsertObject(light_beam)
    
    # Apply material
    texture_tag = light_beam.MakeTag(c4d.Ttexture)
    texture_tag[c4d.TEXTURETAG_MATERIAL] = ray_mat
    
    # Make it visible only in volumetric
    light_beam[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1
    light_beam[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
    
    return light_beam

def main():
    doc = documents.GetActiveDocument()
    if not doc:
        return False
    
    # Create volumetric lighting
    create_volumetric_lighting(doc)
    
    # Add god rays
    add_god_rays(doc)
    
    # Set render settings for volumetrics
    render_data = doc.GetActiveRenderData()
    if render_data:
        # Enable volumetric rendering
        render_data[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_STANDARD
        
        # Set up post effects
        video_post = render_data.GetFirstVideoPost()
        glow_found = False
        
        while video_post:
            if video_post.GetType() == c4d.VPglow:
                glow_found = True
                break
            video_post = video_post.GetNext()
        
        if not glow_found:
            # Add glow effect
            glow = c4d.BaseList2D(c4d.VPglow)
            glow[c4d.GLOW_INTENSITY] = 0.5
            glow[c4d.GLOW_RADIUS] = 20
            render_data.InsertVideoPost(glow)
    
    # Update scene
    c4d.EventAdd()
    
    print("Volumetric lighting setup complete")
    return True

if __name__ == '__main__':
    success = main()
    print("SUCCESS" if success else "FAILED")