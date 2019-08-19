import bpy
from bpy.props import *

def register():

    bpy.types.Object.tlm_mesh_lightmap_use = BoolProperty(name="Enable Lightmapping", description="TODO", default=False)

    bpy.types.Object.tlm_mesh_apply_after = BoolProperty(name="Apply after build", description="TODO", default=False)
    
    bpy.types.Object.tlm_mesh_emissive = BoolProperty(name="Include emissive light", description="TODO", default=False)
    
    bpy.types.Object.tlm_mesh_emissive_shadow = BoolProperty(name="Emissive casts shadows", description="TODO", default=False)
    
    bpy.types.Object.tlm_mesh_lightmap_resolution = EnumProperty(
        items = [('32', '32', 'TODO'),
                 ('64', '64', 'TODO'),
                 ('128', '128', 'TODO'),
                 ('256', '256', 'TODO'),
                 ('512', '512', 'TODO'),
                 ('1024', '1024', 'TODO'),
                 ('2048', '2048', 'TODO'),
                 ('4096', '4096', 'TODO'),
                 ('8192', '8192', 'TODO')],
                name = "Lightmap Resolution", description="TODO", default='256')
    
    bpy.types.Object.tlm_mesh_lightmap_unwrap_mode = EnumProperty(
        items = [('Lightmap', 'Lightmap', 'TODO'),
                 ('Smart Project', 'Smart Project', 'TODO'),
                 ('Copy Existing', 'Copy Existing', 'TODO')],
                name = "Unwrap Mode", description="TODO", default='Smart Project')
    
    bpy.types.Object.tlm_mesh_unwrap_margin = FloatProperty(name="Unwrap Margin", default=0.1, min=0.0, max=1.0, subtype='FACTOR')
    
    bpy.types.Object.tlm_mesh_bake_ao = BoolProperty(name="Bake AO", description="TODO", default=False)
    
    bpy.types.Object.tlm_light_lightmap_use = BoolProperty(name="Enable for Lightmapping", description="TODO", default=True)
    
    bpy.types.Object.tlm_light_type = EnumProperty(
        items = [('Static', 'Static', 'Static baked light with both indirect and direct. Hidden after baking.'),
                 ('Stationary', 'Stationary', 'Semi dynamic light. Indirect baked, but can be moved, change intensity and color.')],
                name = "Light Type", description="TODO", default='Static')
    
    bpy.types.Object.tlm_light_intensity_scale = FloatProperty(name="Intensity Scale", default=1.0, min=0.0, max=10.0, subtype='FACTOR')
    
    bpy.types.Object.tlm_light_casts_shadows = BoolProperty(name="Casts shadows", description="TODO", default=True)