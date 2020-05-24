from os.path import basename, dirname
from bpy.types import AddonPreferences

class TLM_AddonPreferences(AddonPreferences):

    bl_idname = "thelightmapper"

    def draw(self, context):

        layout = self.layout

        row = layout.row()
        row.label(text="OpenCV")
        row = layout.row()
        row.label(text="PIP")
        row = layout.row()
        row.label(text="OIDN / Optix")
        row = layout.row()
        row.label(text="UVPackmaster")
        row = layout.row()
        row.label(text="Texel Density")