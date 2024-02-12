import bpy, os
from bpy.props import *

class TLM_SceneProperties(bpy.types.PropertyGroup):

    tlm_setting_keep_cache_files : BoolProperty(
        name="Keep cache files", 
        description="Keep cache files (non-filtered and non-denoised)", 
        default=True)