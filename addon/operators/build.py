import bpy

class TLM_BuildLightmaps(bpy.types.Operator):
    """Builds the lightmaps"""
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles
        sceneProperties = scene.TLM_Properties

        


        print("BUILDING LIGHTMAPS!")

        return{'FINISHED'}