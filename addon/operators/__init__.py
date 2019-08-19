from bpy.utils import register_class, unregister_class
from . import build, clean, explore

classes = [
    build.TLM_BuildLightmaps,
    clean.TLM_CleanLightmaps,
    explore.TLM_ExploreLightmaps
]

def register():
    for cls in classes:
        register_class(cls)
        
def unregister():
    for cls in classes:
        unregister_class(cls)