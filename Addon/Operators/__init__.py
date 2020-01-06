from bpy.utils import register_class, unregister_class
from . import build, clean, explore, encode, installopencv, gui, xBake, selection

classes = [
    build.TLM_BuildLightmaps,
    clean.TLM_CleanLightmaps,
    encode.TLM_EncodeLightmaps,
    explore.TLM_ExploreLightmaps,
    installopencv.TLM_Install_OpenCV,
    selection.TLM_EnableSelection,
    selection.TLM_DisableSelection,
    #xBake.XBake
]

gui.register()

def register():
    for cls in classes:
        register_class(cls)
        
def unregister():
    for cls in classes:
        unregister_class(cls)