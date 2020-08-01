from os.path import basename, dirname
from bpy.types import AddonPreferences
from .. operators import installopencv
import importlib

class TLM_AddonPreferences(AddonPreferences):

    bl_idname = "thelightmapper"

    def draw(self, context):

        layout = self.layout

        box = layout.box()
        row = box.row()
        row.label(text="OpenCV")

        cv2 = importlib.util.find_spec("cv2")

        if cv2 is not None:
            row.label(text="OpenCV installed")
        else:
            row.label(text="OpenCV not found - Install as administrator!", icon_value=2)
            row = box.row()
            row.operator("tlm.install_opencv_lightmaps", icon="PREFERENCES")


        # row = layout.row()
        # row.label(text="PIP")
        # row = layout.row()
        # row.label(text="OIDN / Optix")
        # row = layout.row()
        # row.label(text="UVPackmaster")
        # row = layout.row()
        # row.label(text="Texel Density")