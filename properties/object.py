import bpy
from bpy.props import *

class TLM_ObjectProperties(bpy.types.PropertyGroup):
    tlm_mesh_lightmap_use : BoolProperty(
        name="Enable Lightmapping", 
        description="Enable Lightmapping for this object", 
        default=False)
    
    tlm_mesh_lightmap_resolution : EnumProperty(
        items = [('32', '32', '32'),
                 ('64', '64', '64'),
                 ('128', '128', '128'),
                 ('256', '256', '256'),
                 ('512', '512', '512'),
                 ('1024', '1024', '1024'),
                 ('2048', '2048', '2048'),
                 ('4096', '4096', '4096'),
                 ('8192', '8192', '8192')],
                name = "Lightmap Resolution", 
                description="The lightmap resolution for this object", 
                default='256')
    
    unwrap_modes = [('Lightmap', 'Lightmap', 'TODO'),
                ('SmartProject', 'Smart Project', 'TODO')]
    
    tlm_mesh_lightmap_unwrap_mode : EnumProperty(
        items = unwrap_modes,
                name = "Unwrap Mode",
                description="The unwrap mode for this object", 
                default='SmartProject')
    
    tlm_mesh_unwrap_margin : FloatProperty(
        name="Unwrap Margin", 
        description="The unwrap margin for this object",
        default=0.1, 
        min=0.0, 
        max=1.0, 
        subtype='FACTOR')