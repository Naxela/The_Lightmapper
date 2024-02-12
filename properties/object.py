import bpy
from bpy.props import *

class TLM_ObjectProperties(bpy.types.PropertyGroup):
    tlm_mesh_lightmap_use : BoolProperty(
        name="Enable Lightmapping", 
        description="TODO", 
        default=False)
    
    tlm_mesh_lightmap_resolution : EnumProperty(
        items = [('32', '32', 'TODO'),
                 ('64', '64', 'TODO'),
                 ('128', '128', 'TODO'),
                 ('256', '256', 'TODO'),
                 ('512', '512', 'TODO'),
                 ('1024', '1024', 'TODO'),
                 ('2048', '2048', 'TODO'),
                 ('4096', '4096', 'TODO'),
                 ('8192', '8192', 'TODO')],
                name = "Lightmap Resolution", 
                description="TODO", 
                default='256')