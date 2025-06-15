import json
import struct

def extract_glb_info(filename):
    try:
        with open(filename, 'rb') as f:
            magic = f.read(4)
            version = struct.unpack('<I', f.read(4))[0]
            length = struct.unpack('<I', f.read(4))[0]
            
            json_chunk_length = struct.unpack('<I', f.read(4))[0]
            json_chunk_type = f.read(4)
            json_data = f.read(json_chunk_length).decode('utf-8')
            
            gltf = json.loads(json_data)
            
            info = {
                'materials_count': len(gltf.get('materials', [])),
                'textures_count': len(gltf.get('textures', [])),
                'images_count': len(gltf.get('images', [])),
                'nodes_count': len(gltf.get('nodes', [])),
            }
            
            # Check materials
            if 'materials' in gltf and gltf['materials']:
                material = gltf['materials'][0]
                info['material_name'] = material.get('name', 'unnamed')
                pbr = material.get('pbrMetallicRoughness', {})
                info['has_base_color'] = 'baseColorTexture' in pbr
                info['has_normal'] = 'normalTexture' in material
                info['has_emissive'] = 'emissiveTexture' in material
                
                # Get texture details
                if 'baseColorTexture' in pbr:
                    info['base_color_texture_index'] = pbr['baseColorTexture']['index']
                if 'normalTexture' in material:
                    info['normal_texture_index'] = material['normalTexture']['index']
            
            return info, gltf
    except Exception as e:
        return {'error': str(e)}, None

# Compare files
bridge_info, bridge_gltf = extract_glb_info('bridge_output.glb')
comfy_info, comfy_gltf = extract_glb_info('comfy_direct_output.glb')

print('=== GLB COMPARISON ===')
print('Bridge (00023):', bridge_info)
print('ComfyUI (00024):', comfy_info)

print('\n=== DIFFERENCES ===')
if 'error' not in bridge_info and 'error' not in comfy_info:
    differences = []
    for key in bridge_info:
        if bridge_info[key] != comfy_info[key]:
            differences.append(f'{key}: Bridge={bridge_info[key]} vs ComfyUI={comfy_info[key]}')
    
    if differences:
        for diff in differences:
            print(diff)
    else:
        print('No structural differences found - materials and textures are identical')
        
        # Let's check image sizes
        if bridge_gltf and comfy_gltf:
            print('\n=== TEXTURE SIZE COMPARISON ===')
            bridge_images = bridge_gltf.get('images', [])
            comfy_images = comfy_gltf.get('images', [])
            
            for i, (b_img, c_img) in enumerate(zip(bridge_images, comfy_images)):
                print(f'Image {i}:')
                print(f'  Bridge: {b_img.get("name", "unnamed")}')
                print(f'  ComfyUI: {c_img.get("name", "unnamed")}')
else:
    print('Error in analysis:', bridge_info.get('error'), comfy_info.get('error'))