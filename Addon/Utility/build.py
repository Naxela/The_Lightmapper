import bpy
from . cycles import lightmap

def prepare_build(self=0):

    if check_save():
        self.report({'INFO'}, "Please save your file first")
        return{'FINISHED'}

    if check_denoiser():
        self.report({'INFO'}, "No denoise OIDN path assigned")
        return{'FINISHED'}

    begin_build()

    #Pre-check

    #Pre-configure

def begin_build():

    #if cycles
    lightmap.bake()

    #

    pass

    manage_build()

def manage_build():

    #if cycles
    #apply materials
    

    pass














def check_save():
    if not bpy.data.is_saved:

        return 1

    else:

        return 0

def check_denoiser():

    scene = bpy.context.scene

    return 0

    # if scene.TLM_SceneProperties.tlm_denoise_use:
    #     if scene.TLM_SceneProperties.tlm_oidn_path == "":
    #         print("NO DENOISE PATH")
    #         return False
    #     else:
    #         return True
    # else:
    #     return True