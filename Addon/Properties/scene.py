import bpy
from bpy.props import *

class TLM_SceneProperties(bpy.types.PropertyGroup):

    tlm_lightmap_engine : EnumProperty(
        items = [('Cycles', 'Cycles', 'Use Cycles for lightmapping'),
                ('LuxCoreRender', 'LuxCoreRender', 'Use LuxCoreRender for lightmapping')],
                name = "Lightmap Engine", 
                description="Select which lightmap engine to use.", 
                default='Cycles')

    #SETTINGS GROUP

    tlm_setting_clean_option : EnumProperty(
        items = [('Clean', 'Full Clean', 'Clean lightmap directory and revert all materials'),
                ('CleanMarked', 'Clean marked', 'Clean only the objects marked for lightmapping')],
                name = "Clean mode", 
                description="The cleaning mode, either full or partial clean. Be careful that you don't delete lightmaps you don't intend to delete.", 
                default='Clean')

    tlm_setting_keep_cache_files : BoolProperty(
        name="Keep cache files", 
        description="Keep cache files (non-filtered and non-denoised)", 
        default=True)

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

    tlm_setting_exposure_multiplier : FloatProperty(
        name="Exposure Multiplier", 
        default=0,
        description="0 to disable. Multiplies GI value")

    tlm_setting_apply_scale : BoolProperty(
        name="Apply scale", 
        description="Apply the scale before unwrapping.", 
        default=True)

    tlm_play_sound : BoolProperty(
        name="Play sound on finish", 
        description="Play sound on finish", 
        default=False)

    tlm_compile_statistics : BoolProperty(
        name="Compile statistics", 
        description="Compile time statistics in the lightmap folder.", 
        default=True)

    