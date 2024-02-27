import bpy, os
from bpy.props import *

class TLM_SceneProperties(bpy.types.PropertyGroup):

    tlm_setting_renderer : EnumProperty(
        items = [('CPU', 'CPU', 'Bake using the processor'),
                ('GPU', 'GPU', 'Bake using the graphics card')],
                name = "Device", 
                description="Select whether to use the CPU or the GPU", 
                default="CPU")

    tlm_setting_scale : EnumProperty(
        items = [('8', '1/8', '1/8th of set scale'),
                ('4', '1/4', '1/4th of set scale'),
                ('2', '1/2', 'Half of set scale'),
                ('1', '1/1', 'Full scale')],
                name = "Lightmap Resolution scale", 
                description="Lightmap resolution scaling. Adjust for previewing.", 
                default="1")

    tlm_setting_savedir : StringProperty(
        name="Lightmap Directory", 
        description="Your baked lightmaps will be stored here.", 
        default="Lightmaps", 
        subtype="FILE_PATH")
    
    tlm_play_sound : BoolProperty(
        name="Play sound on finish", 
        description="Play sound on finish", 
        default=False)
    
    tlm_autoApply : BoolProperty(
        name="Apply lightmaps on finish", 
        description="Automatically apply lightmaps on finish", 
        default=False)
    
    tlm_resetUV : BoolProperty(
        name="Reset lightmaps UVs", 
        description="Delete existing lightmap UVs and recalculate them", 
        default=False)
    
    tlm_quality : EnumProperty(
        items = [('0', 'Exterior Preview', 'Best for fast exterior previz'),
                    ('1', 'Interior Preview', 'Best for fast interior previz with bounces'),
                    ('2', 'Medium', 'Best for complicated interior preview and final for isometric environments'),
                    ('3', 'High', 'Best used for final baking for 3rd person games'),
                    ('4', 'Production', 'Best for first-person and Archviz'),
                    ('5', 'Custom', 'Uses the cycles sample settings provided the user')],
                name = "Quality", 
                description="Select baking quality", 
                default="0")
    
    tlm_denoise_use : BoolProperty(
        name="Enable denoising", 
        description="Enable denoising for lightmaps", 
        default=False)
    
    tlm_material_multi_user : EnumProperty(
        items = [('Ignore', 'Ignore', 'Ignore multi-user'),
                ('Unique', 'Unique', 'Every lightmapped object will get unique lightmap materials'),
                ('Shared', 'Shared', 'Objects sharing materials will also share UV space')],
                name = "Material multi-option", 
                description="Select how to handle shared materials across objects", 
                default='Unique')

    tlm_denoise_engine : EnumProperty(
        items = [('None', 'None', 'Don\'t use any denoising'),
                ('Integrated', 'Integrated', 'Use the Blender native denoiser (Compositor; Slow)'),
                ('OIDN', 'OIDN', 'Use the Intel OIDN denoiser if available')],
                name = "Denoiser", 
                description="Select which denoising engine to use.", 
                default='None')

    tlm_setting_keep_cache_files : BoolProperty(
        name="Keep cache files", 
        description="Keep cache files (non-filtered and non-denoised)", 
        default=True)