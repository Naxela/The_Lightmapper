from os.path import basename, dirname
from bpy.types import AddonPreferences
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
            print("OpenCV exists")
            row.label(text="OpenCV found")
        else:
            print("OpenCV not exists")
            row.label(text="OpenCV not found")


        # row = layout.row()
        # row.label(text="PIP")
        # row = layout.row()
        # row.label(text="OIDN / Optix")
        # row = layout.row()
        # row.label(text="UVPackmaster")
        # row = layout.row()
        # row.label(text="Texel Density")