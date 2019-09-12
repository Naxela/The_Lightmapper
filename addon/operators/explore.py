import bpy
from bpy.props import *

class TLM_ExploreLightmaps(bpy.types.Operator):
    """Explore the lightmaps"""
    bl_idname = "tlm.explore_lightmaps"
    bl_label = "Explore Lightmaps"
    bl_description = "Explore Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles

        return {'FINISHED'}