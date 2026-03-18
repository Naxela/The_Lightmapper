import bpy, os
from bpy.utils import register_class, unregister_class
from . import scene, object, distributed

classes = [
    scene.TLM_PT_Panel,
    scene.TLM_PT_Settings,
    scene.TLM_PT_Utilities,
    #distributed.TLM_PT_Distributed,
    object.TLM_PT_ObjectMenu
]

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)