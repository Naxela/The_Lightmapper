import bpy, platform
from os.path import basename, dirname
from bpy.types import AddonPreferences
from .. operators import installopencv
import importlib

class TLM_AddonPreferences(AddonPreferences):

    bl_idname = "thelightmapper"

    addon_keys = bpy.context.preferences.addons.keys()

    def draw(self, context):

        layout = self.layout

        box = layout.box()
        row = box.row()
        row.label(text="OpenCV")

        cv2 = importlib.util.find_spec("cv2")

        if cv2 is not None:
            row.label(text="OpenCV installed")
        else:
            if platform.system() == "Windows":
                row.label(text="OpenCV not found - Install as administrator!", icon_value=2)
            else:
                row.label(text="OpenCV not found - Click to install!", icon_value=2)
            row = box.row()
            row.operator("tlm.install_opencv_lightmaps", icon="PREFERENCES")

        box = layout.box()
        row = box.row()
        row.label(text="Blender Xatlas")
        if "blender_xatlas" in self.addon_keys:
            row.label(text="Blender Xatlas installed and available")
        else:
            row.label(text="Blender Xatlas not installed", icon_value=2)
        row = box.row()
        row.label(text="Github: https://github.com/mattedicksoncom/blender-xatlas")

        box = layout.box()
        row = box.row()
        row.label(text="RizomUV Bridge")
        row.label(text="Coming soon")

        box = layout.box()
        row = box.row()
        row.label(text="UVPackmaster")
        row.label(text="Coming soon")

        box = layout.box()
        row = box.row()
        row.label(text="Texel Density Checker")
        row.label(text="Coming soon")

        box = layout.box()
        row = box.row()
        row.label(text="LuxCoreRender")
        row.label(text="Coming soon")

        box = layout.box()
        row = box.row()
        row.label(text="OctaneRender")
        row.label(text="Coming soon")