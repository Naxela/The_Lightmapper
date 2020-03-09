class Node_Types:
    output_node = 'OUTPUT_MATERIAL'
    ao_node = 'AMBIENT_OCCLUSION'
    image_texture = 'TEX_IMAGE'
    pbr_node = 'BSDF_PRINCIPLED'
    diffuse = 'BSDF_DIFFUSE'
    mapping = 'MAPPING'
    normal_map = 'NORMAL_MAP'
    bump_map = 'BUMP'
    attr_node = 'ATTRIBUTE'

class Shader_Node_Types:
    emission = "ShaderNodeEmission"
    image_texture = "ShaderNodeTexImage"
    mapping = "ShaderNodeMapping"
    normal = "ShaderNodeNormalMap"
    ao = "ShaderNodeAmbientOcclusion"
    uv = "ShaderNodeUVMap"
    mix = "ShaderNodeMixRGB"