import bpy
from bpy.props import *

class TLM_CleanLightmaps(bpy.types.Operator):
    """Cleans the lightmaps"""
    bl_idname = "tlm.clean_lightmaps"
    bl_label = "Clean Lightmaps"
    bl_description = "Clean Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #HDRLM_Build(self, context)
        print("Building Lightmaps...")
        return {'FINISHED'}