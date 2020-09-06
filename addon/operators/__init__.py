import bpy
from bpy.utils import register_class, unregister_class
from . import tlm, installopencv

classes = [
    tlm.TLM_BuildLightmaps,
    tlm.TLM_CleanLightmaps,
    tlm.TLM_ExploreLightmaps,
    tlm.TLM_EnableSelection,
    tlm.TLM_DisableSelection,
    tlm.TLM_RemoveLightmapUV,
    tlm.TLM_SelectLightmapped,
    installopencv.TLM_Install_OpenCV,
    tlm.TLM_AtlasListNewItem,
    tlm.TLM_AtlastListDeleteItem,
    tlm.TLM_AtlasListMoveItem
]

def register():
    for cls in classes:
        register_class(cls)
        
def unregister():
    for cls in classes:
        unregister_class(cls)