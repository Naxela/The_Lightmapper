import bpy
from bpy.utils import register_class, unregister_class
from . import tlm

classes = [
    tlm.TLM_BuildLightmaps,
    tlm.TLM_CleanLightmaps,
    tlm.TLM_ExploreLightmaps
]

def register():
    for cls in classes:
        register_class(cls)
        
def unregister():
    for cls in classes:
        unregister_class(cls)