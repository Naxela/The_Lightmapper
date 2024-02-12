import bpy
from bpy.props import *

class TLM_ObjectProperties(bpy.types.PropertyGroup):
    tlm_mesh_lightmap_use : BoolProperty(
        name="Enable Lightmapping", 
        description="TODO", 
        default=False)