import bpy

class TLM_Install_OpenCV(bpy.types.Operator):
    """Install OpenCV"""
    bl_idname = "tlm.install_opencv_lightmaps"
    bl_label = "Install OpenCV"
    bl_description = "Install OpenCV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles

        return{'FINISHED'}