import bpy

class TLM_EncodeLightmaps(bpy.types.Operator):
    """Encode the lightmaps"""
    bl_idname = "tlm.encode_lightmaps"
    bl_label = "Encode Lightmaps"
    bl_description = "Encode Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles

        return{'FINISHED'}