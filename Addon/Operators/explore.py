import bpy, os, webbrowser
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

        if not bpy.data.is_saved:
            self.report({'INFO'}, "Please save your file first")
            return {"CANCELLED"}

        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.hdrlm_lightmap_savedir)

        if os.path.isdir(dirpath):
            webbrowser.open('file://' + dirpath)
        else:
            os.mkdir(dirpath)
            webbrowser.open('file://' + dirpath)

        return {'FINISHED'}