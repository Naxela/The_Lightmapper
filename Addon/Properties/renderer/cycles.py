import bpy
from bpy.props import *

class TLM_CyclesSceneProperties(bpy.types.PropertyGroup):

    tlm_mode : EnumProperty(
        items = [('CPU', 'CPU', 'Use the processor to bake textures'),
                    ('GPU', 'GPU', 'Use the graphics card to bake textures')],
                name = "Device", 
                description="Select whether to use the CPU or the GPU for baking", 
                default="CPU")

    tlm_quality : EnumProperty(
        items = [('0', 'Exterior Preview', 'Best for fast exterior previz'),
                    ('1', 'Interior Preview', 'Best for fast interior previz with bounces'),
                    ('2', 'Medium', 'Best for complicated interior preview and final for isometric environments'),
                    ('3', 'High', 'Best used for final baking for 3rd person games'),
                    ('4', 'Production', 'Best for first-person and Archviz')],
                name = "Quality", 
                description="Select baking quality", 
                default="0")

    tlm_resolution_scale : EnumProperty(
        items = [('1', '1/1', '1'),
                    ('2', '1/2', '2'),
                    ('3', '1/4', '3'),
                    ('4', '1/8', '4')],
                name = "Resolution scale", 
                description="Select resolution scale", 
                default="3")

    tlm_bake_mode : EnumProperty(
        items = [('Background', 'Background', 'More overhead; allows for network.'),
                    ('Foreground', 'Foreground', 'Direct in-session bake')],
                name = "Baking mode", 
                description="Select bake mode", 
                default="Background")

    tlm_caching_mode : EnumProperty(
        items = [('Copy', 'Copy', 'More overhead; allows for network.'),
                    ('Cache', 'Cache', 'Cache in separate blend'),
                    ('Node', 'Node restore', 'EXPERIMENTAL! Use with care')],
                name = "Caching mode",
                description="Select cache mode",
                default="Copy")

    tlm_directional_mode : EnumProperty(
        items = [('None', 'None', 'No directional information'),
                    ('Normal', 'Baked normal', 'Baked normal maps are taken into consideration')],
                name = "Directional mode", 
                description="Select directional mode", 
                default="None")

    tlm_lightmap_savedir : StringProperty(
        name="Lightmap Directory", 
        description="TODO", 
        default="Lightmaps", 
        subtype="FILE_PATH")

    tlm_dilation_margin : IntProperty(
        name="Dilation margin", 
        default=4,
        min=1, 
        max=64, 
        subtype='PIXEL')

    tlm_exposure_multiplier : FloatProperty(
        name="Exposure Multiplier", 
        default=0,
        description="0 to disable. Multiplies GI value")