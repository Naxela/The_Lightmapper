import bpy

class TLM_CleanLightmaps(bpy.types.Operator):
    """Cleans the lightmaps"""
    bl_idname = "tlm.clean_lightmaps"
    bl_label = "Clean Lightmaps"
    bl_description = "Clean Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles

        return{'FINISHED'}