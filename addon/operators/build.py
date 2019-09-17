import bpy
from .. Utility import utility

class TLM_BuildLightmaps(bpy.types.Operator):
    """Builds the lightmaps"""
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles

        utility.bake_ordered(self, context)

        return{'FINISHED'}