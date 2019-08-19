import bpy
from bpy.props import *

class TLM_BuildLightmaps(bpy.types.Operator):
    """Builds the lightmaps"""
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        HDRLM_Build(self, context)
        return {'FINISHED'}

def HDRLM_Build(self, context):

    total_time = time()

    scene = context.scene
    cycles = bpy.data.scenes[scene.name].cycles

    if not bpy.data.is_saved:
        self.report({'INFO'}, "Please save your file first")
        return{'FINISHED'}

    if scene.tlm_denoise_use:
        if scene.tlm_oidn_path == "":
            scriptDir = os.path.dirname(os.path.realpath(__file__))
            if os.path.isdir(os.path.join(scriptDir,"OIDN")):
                scene.tlm_oidn_path = os.path.join(scriptDir,"OIDN")
                if scene.tlm_oidn_path == "":
                    self.report({'INFO'}, "No denoise OIDN path assigned")
                    return{'FINISHED'}

    
