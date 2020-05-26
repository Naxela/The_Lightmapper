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

    tlm_mesh_lightmap_unwrap_mode : EnumProperty(
        items = [('Lightmap', 'Lightmap', 'TODO'),
                 ('SmartProject', 'Smart Project', 'TODO'),
                 ('CopyExisting', 'Copy Existing', 'TODO'),
                 ('AtlasGroup', 'Atlas Group', 'TODO')],
                name = "Unwrap Mode",
                description="TODO", 
                default='SmartProject')

    tlm_mesh_unwrap_margin : FloatProperty(
        name="Unwrap Margin", 
        default=0.1, 
        min=0.0, 
        max=1.0, 
        subtype='FACTOR')