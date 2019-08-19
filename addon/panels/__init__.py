import bpy, os
#from bpy.utils import register_class, unregister_class, previews
from bpy.utils import *
from . import scene, object

classes = [
    scene.TLM_PT_Panel,
    scene.TLM_PT_Settings,
    scene.TLM_PT_Denoise,
    scene.TLM_PT_Filtering,
    scene.TLM_PT_Encoding,
    scene.TLM_PT_Compression,
    scene.TLM_PT_Additional,
    object.TLM_PT_ObjectMenu
]

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)