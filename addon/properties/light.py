import bpy
from bpy.props import *

class TLMLightProperties(bpy.types.PropertyGroup):

    tlm_light_lightmap_use : BoolProperty(name="Enable for Lightmapping", description="Enable the light for lightmapping", default=True)

    # tlm_light_type : EnumProperty(
    #     items = [('Static', 'Static', 'Static baked light with both indirect and direct. Hidden after baking.'),
    #              ('Stationary', 'Stationary', 'Semi dynamic light. Indirect baked, but can be moved, change intensity and color.')],
    #             name = "Light Type", description="TODO", default='Static')

    tlm_light_intensity_scale : FloatProperty(name="Intensity Scale", description="Override default intensity", default=1.0, min=0.0, max=10.0, subtype='FACTOR')

    tlm_light_casts_shadows : BoolProperty(name="Casts shadows", description="Override shadow casting for the light", default=True)

def register():
    bpy.utils.register_class(TLMLightProperties)

def unregister():
    bpy.utils.unregister_class(TLMLightProperties)